import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the reasoning core of an autonomous D2C advertising decision engine.
Given structured signals (anomalies, causal drivers, opportunity scores), produce:
1. A concise plain-text diagnostic narrative.
2. A ranked list of actionable recommendations with confidence and rationale.
Return ONLY valid JSON with keys: narrative (string), recommendations (list of objects with keys:
entity_type, entity_id, action, from_entity, to_entity, delta_budget, confidence, rationale).
"""


def _build_user_prompt(context):
    return "Signals:\n" + json.dumps(context, default=str, indent=2)


def _call_gemini(prompt):
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.LLM_MODEL)
    resp = model.generate_content(
        [{"role": "user", "parts": [SYSTEM_PROMPT + "\n\n" + prompt]}]
    )
    return resp.text


def _call_openrouter(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
        default_headers={
            "HTTP-Referer": settings.OPENROUTER_SITE_URL,
            "X-Title": settings.OPENROUTER_SITE_NAME,
        },
    )
    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content

def _call_openai(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
        default_headers={
            "HTTP-Referer": settings.OPENROUTER_SITE_URL,
            "X-Title": settings.OPENROUTER_SITE_NAME,
        },
    )
    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content

def _extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return {"narrative": text, "recommendations": []}
    try:
        return json.loads(text[start : end + 1])
    except Exception as e:
        logger.warning(f"JSON parse failed: {e}")
        return {"narrative": text, "recommendations": []}


def _fallback_reason(context):
    anomalies = context.get("anomalies", [])
    opps = context.get("top_opportunities", [])
    if not anomalies:
        return {
            "narrative": "No significant anomalies detected across active campaigns.",
            "recommendations": [],
        }
    top = anomalies[0]
    drivers = context.get("drivers", [])
    driver_name = drivers[0].get("driver", "n/a") if drivers else "n/a"
    narrative = (
        f"Anomaly detected on {top['entity_id']} ({top['metric']} "
        f"{top['delta_pct']:.1f}% vs baseline, z={top['z_score']:.2f}). "
        f"Likely driver: {driver_name}."
    )
    recs = []
    if opps:
        dst = opps[0]
        recs.append({
            "entity_type": "sku_campaign",
            "entity_id": top["entity_id"],
            "action": "reallocate",
            "from_entity": top["entity_id"],
            "to_entity": f"{dst.get('platform')}|{dst.get('sku')}",
            "delta_budget": -abs(top.get("delta_pct", 10)) * 5,
            "confidence": 0.62,
            "rationale": f"Shift budget from {top['entity_id']} to {dst.get('sku')}.",
        })
    return {"narrative": narrative, "recommendations": recs}


def reason(context):
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "openrouter" and not settings.OPENROUTER_API_KEY:
        return _fallback_reason(context)
    if provider == "gemini" and not settings.GEMINI_API_KEY:
        return _fallback_reason(context)
    if provider == "openai" and not settings.OPENAI_API_KEY:
        return _fallback_reason(context)

    prompt = _build_user_prompt(context)
    try:
        if provider == "openrouter":
            text = _call_openrouter(prompt)
        elif provider == "gemini":
            text = _call_gemini(prompt)
        else:
            text = _call_openai(prompt)
        return _extract_json(text)
    except Exception as e:
        logger.exception(f"LLM reasoning failed: {e}")
        return _fallback_reason(context)
