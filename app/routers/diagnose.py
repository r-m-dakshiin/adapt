from fastapi import APIRouter

from app.ingestion.reconciler import build_unified_frame
from app.execution.decision_engine import diagnose
from app.schemas import DiagnoseResponse

router = APIRouter(prefix="/diagnose", tags=["diagnose"])


@router.post("/run", response_model=DiagnoseResponse)
def run_diagnose():
    df = build_unified_frame()
    result = diagnose(df)
    return DiagnoseResponse(
        anomalies=result["anomalies"],
        narrative=result["narrative"],
        drivers=result["drivers"],
    )


@router.post("/full")
def run_full_diagnose():
    df = build_unified_frame()
    return diagnose(df)
