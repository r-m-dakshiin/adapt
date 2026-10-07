from fastapi import APIRouter, HTTPException

from app.database import (
    fetch_recommendations,
    insert_execution,
    log_event,
    update_recommendation_status,
)
from app.execution.ad_apis import dispatch
from app.schemas import ExecuteRequest, ExecuteResponse

router = APIRouter(prefix="/execute", tags=["execute"])


@router.get("/recommendations")
def list_recommendations(status: str | None = None):
    return fetch_recommendations(status=status)


@router.post("/run", response_model=ExecuteResponse)
async def execute(req: ExecuteRequest):
    recs = fetch_recommendations()
    rec = next((r for r in recs if r["id"] == req.recommendation_id), None)
    if not rec:
        raise HTTPException(status_code=404, detail="recommendation not found")

    platform = rec.get("metadata", {}).get("platform") or "meta"
    target = rec.get("to_entity") or rec.get("entity_id") or ""
    campaign_id = target.split("|")[-1] if "|" in target else target
    new_budget = abs(float(rec.get("delta_budget") or 100.0))

    result = await dispatch(platform, campaign_id, new_budget, dry_run=req.dry_run)

    exec_row = {
        "recommendation_id": req.recommendation_id,
        "platform": platform,
        "request": result.get("request", {}),
        "response": result.get("response", {}),
        "success": result.get("status_code", 200) < 400,
        "error": result.get("response", {}).get("error"),
    }
    saved = insert_execution(exec_row)
    update_recommendation_status(
        req.recommendation_id,
        "executed" if exec_row["success"] else "rejected",
    )
    log_event(
        kind="execution",
        entity_type="recommendation",
        entity_id=str(req.recommendation_id),
        platform=platform,
        payload=saved or exec_row,
        severity="info" if exec_row["success"] else "warning",
    )

    return ExecuteResponse(
        success=exec_row["success"],
        platform=platform,
        request=exec_row["request"],
        response=exec_row["response"],
        message="executed" if exec_row["success"] else "failed",
    )
