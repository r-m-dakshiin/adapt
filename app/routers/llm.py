from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

from app.intelligence.llm_agent import reason

router = APIRouter(prefix="/llm", tags=["llm"])


class AnalyseRequest(BaseModel):
    anomalies: list[dict[str, Any]] = []
    drivers: list[dict[str, Any]] = []
    executions: list[dict[str, Any]] = []


@router.post("/analyse")
def analyse(req: AnalyseRequest):
    """Proxy LLM reasoning — key stays server-side."""
    context = {
        "anomalies": req.anomalies,
        "drivers": req.drivers,
        "executions": req.executions,
    }
    return reason(context)
