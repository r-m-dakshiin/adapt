import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def meta_adjust_budget(campaign_id, new_budget, dry_run=False):
    payload = {"campaign_id": campaign_id, "daily_budget": int(new_budget * 100)}
    if dry_run:
        return {"dry_run": True, "platform": "meta",
                "request": payload, "response": {"status": "simulated"}}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{settings.META_API_BASE}/{campaign_id}",
                data={**payload, "access_token": settings.META_ACCESS_TOKEN},
            )
            return {"platform": "meta", "request": payload,
                    "response": r.json(), "status_code": r.status_code}
    except Exception as e:
        logger.exception("Meta call failed")
        return {"platform": "meta", "request": payload,
                "response": {"error": str(e)}, "status_code": 500}


async def google_adjust_budget(campaign_id, new_budget, dry_run=False):
    payload = {"campaignId": campaign_id, "dailyBudgetMicros": int(new_budget * 1_000_000)}
    if dry_run:
        return {"dry_run": True, "platform": "google",
                "request": payload, "response": {"status": "simulated"}}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{settings.GOOGLE_ADS_API_BASE}/campaigns:mutate",
                json=payload,
                headers={"Authorization": f"Bearer {settings.GOOGLE_ADS_TOKEN}"},
            )
            return {"platform": "google", "request": payload,
                    "response": r.json(), "status_code": r.status_code}
    except Exception as e:
        logger.exception("Google call failed")
        return {"platform": "google", "request": payload,
                "response": {"error": str(e)}, "status_code": 500}


async def dispatch(platform, campaign_id, new_budget, dry_run=False):
    if platform.lower() == "meta":
        return await meta_adjust_budget(campaign_id, new_budget, dry_run)
    if platform.lower() in ("google", "google_ads"):
        return await google_adjust_budget(campaign_id, new_budget, dry_run)
    return {"platform": platform,
            "response": {"error": "unsupported platform"}, "status_code": 400}
