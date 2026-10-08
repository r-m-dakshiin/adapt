from datetime import datetime, timezone

_feedback: list[dict] = []
_fb_seq = 0


def record_outcome(execution_id, metric, pre_value, post_value,
                   window_hours=24, notes=None):
    global _fb_seq
    _fb_seq += 1
    uplift = ((post_value - pre_value) / pre_value * 100) if pre_value else 0.0
    row = {
        "id": _fb_seq,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "execution_id": execution_id,
        "metric": metric,
        "pre_value": pre_value,
        "post_value": post_value,
        "uplift": uplift,
        "window_hours": window_hours,
        "notes": notes,
    }
    _feedback.append(row)
    return row
