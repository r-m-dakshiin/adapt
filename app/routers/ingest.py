import time
from fastapi import APIRouter

from app.ingestion.reconciler import build_unified_frame, get_summary
from app.schemas import IngestResponse

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/run", response_model=IngestResponse)
def run_ingest():
    t0 = time.time()
    df = build_unified_frame()
    return IngestResponse(
        rows_ingested=len(df),
        unified_rows=len(df),
        duration_ms=(time.time() - t0) * 1000,
    )


@router.get("/summary")
def summary():
    return get_summary()
