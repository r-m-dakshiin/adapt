import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.execution.decision_engine import diagnose
from app.ingestion.reconciler import build_unified_frame
from app.routers import ingest, diagnose as diagnose_router, execute, feed, llm as llm_router

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _scheduled_ingest():
    try:
        build_unified_frame()
    except Exception:
        logger.exception("Scheduled ingest failed")


def _scheduled_diagnose():
    try:
        df = build_unified_frame()
        diagnose(df)
    except Exception:
        logger.exception("Scheduled diagnose failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(_scheduled_ingest, "interval",
                      minutes=settings.INGEST_INTERVAL_MINUTES, id="ingest")
    scheduler.add_job(_scheduled_diagnose, "interval",
                      minutes=settings.DIAGNOSE_INTERVAL_MINUTES, id="diagnose")
    scheduler.start()
    logger.info("%s starting up", settings.APP_NAME)
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(diagnose_router.router)
app.include_router(execute.router)
app.include_router(feed.router)
app.include_router(llm_router.router)


@app.post("/simulate/loop")
async def simulate_loop():
    """Full pipeline: ingest → diagnose → execute top rec → feedback."""
    from app.learning.feedback import record_outcome

    df = build_unified_frame()
    result = diagnose(df)

    recs = result.get("recommendations", [])
    executed = []
    for r in recs[:1]:
        platform = (r.get("to_entity") or r.get("entity_id") or "meta").split("|")[0]
        executed.append({
            "platform": platform,
            "action": r.get("action"),
            "from": r.get("from_entity"),
            "to": r.get("to_entity"),
            "delta_budget": r.get("delta_budget"),
            "confidence": r.get("confidence"),
        })
        try:
            record_outcome(execution_id=0, metric="roas",
                           pre_value=1.4, post_value=2.1,
                           window_hours=24, notes="simulated loop")
        except Exception:
            pass

    return {
        "anomalies": result["anomalies"],
        "drivers": result["drivers"],
        "narrative": result["narrative"],
        "recommendations": recs,
        "executed": executed,
        "top_opportunities": result["top_opportunities"],
    }


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


@app.get("/config/client")
def client_config():
    """Frontend config — serves OR key so it never needs to be hardcoded in HTML."""
    return {
        "or_key": settings.OPENROUTER_API_KEY,
        "or_model": settings.LLM_MODEL,
    }
