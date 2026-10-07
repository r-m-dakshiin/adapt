import logging
from typing import Optional
from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)
_client: Optional[Client] = None


def get_client() -> Optional[Client]:
    global _client
    if _client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            logger.warning("Supabase not configured; running in memory-only mode.")
            return None
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client


def log_event(kind, payload, entity_type=None, entity_id=None, platform=None,
              severity="info", correlation_id=None):
    client = get_client()
    row = {
        "kind": kind, "entity_type": entity_type, "entity_id": entity_id,
        "platform": platform, "payload": payload, "severity": severity,
        "correlation_id": correlation_id,
    }
    if client is None:
        logger.info(f"[EVENT-NO-DB] {row}")
        return row
    try:
        res = client.table(settings.SUPABASE_TABLE_EVENTS).insert(row).execute()
        return res.data[0] if res.data else row
    except Exception as e:
        logger.exception(f"Failed to log event: {e}")
        return row


def insert_recommendation(rec):
    client = get_client()
    if client is None:
        logger.info(f"[REC-NO-DB] {rec}")
        return rec
    try:
        res = client.table(settings.SUPABASE_TABLE_RECOMMENDATIONS).insert(rec).execute()
        return res.data[0] if res.data else rec
    except Exception as e:
        logger.exception(f"Failed to insert recommendation: {e}")
        return rec


def update_recommendation_status(rec_id, status):
    client = get_client()
    if client is None:
        return
    client.table(settings.SUPABASE_TABLE_RECOMMENDATIONS).update({"status": status}).eq("id", rec_id).execute()


def insert_execution(exec_row):
    client = get_client()
    if client is None:
        logger.info(f"[EXEC-NO-DB] {exec_row}")
        return exec_row
    try:
        res = client.table(settings.SUPABASE_TABLE_EXECUTIONS).insert(exec_row).execute()
        return res.data[0] if res.data else exec_row
    except Exception as e:
        logger.exception(f"Failed to insert execution: {e}")
        return exec_row


def insert_feedback(fb):
    client = get_client()
    if client is None:
        logger.info(f"[FB-NO-DB] {fb}")
        return fb
    try:
        res = client.table(settings.SUPABASE_TABLE_FEEDBACK).insert(fb).execute()
        return res.data[0] if res.data else fb
    except Exception as e:
        logger.exception(f"Failed to insert feedback: {e}")
        return fb


def fetch_recent_events(limit=100):
    client = get_client()
    if client is None:
        return []
    res = (client.table(settings.SUPABASE_TABLE_EVENTS)
           .select("*").order("ts", desc=True).limit(limit).execute())
    return res.data or []


def fetch_recommendations(status=None):
    client = get_client()
    if client is None:
        return []
    q = client.table(settings.SUPABASE_TABLE_RECOMMENDATIONS).select("*")
    if status:
        q = q.eq("status", status)
    return (q.order("created_at", desc=True).execute()).data or []
