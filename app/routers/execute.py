from fastapi import APIRouter, HTTPException

from app.execution.decision_engine import (
    get_recommendations,
    set_recommendation_status,
)
from app.execution.ad_apis import dispatch
from app.schemas import ExecuteRequest, ExecuteResponse

router = APIRouter(prefix="/execute", tags=["execute"])


@router.get("/recommendations")
def list_recommendations(status: str | None = None):
    return get_recommendations(status=status)


@router.post("/run", response_model=ExecuteResponse)
async def execute(req: ExecuteRequest):
    recs = get_recommendations()
    rec = next((r for r in recs if r["id"] == req.recommendation_id), None)
    if not rec:
        raise HTTPException(status_code=404, detail="recommendation not found")

    platform = rec.get("metadata", {}).get("platform") or "meta"
    target = rec.get("to_entity") or rec.get("entity_id") or ""
    campaign_id = target.split("|")[-1] if "|" in target else target
    new_budget = abs(float(rec.get("delta_budget") or 100.0))

    result = await dispatch(platform, campaign_id, new_budget, dry_run=req.dry_run)

    success = result.get("status_code", 200) < 400
    set_recommendation_status(req.recommendation_id, "executed" if success else "rejected")

    return ExecuteResponse(
        success=success,
        platform=platform,
        request=result.get("request", {}),
        response=result.get("response", {}),
        message="executed" if success else "failed",
    )
