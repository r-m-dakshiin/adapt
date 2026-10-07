"""
Reconciles ad spend, sales, GA events, inventory, and margin data
into a single unified DataFrame used by the intelligence layer.

Grain: one row per (date, platform, sku).
"""

import logging
import os
import time

import numpy as np
import pandas as pd

from app.ingestion import loader
from app.database import log_event

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Required columns per source. If a CSV is missing one, we fail loudly
# and early with a useful message instead of a pandas stack trace.
# ---------------------------------------------------------------------
REQUIRED_COLUMNS = {
    "ad_spend": {"date", "platform", "campaign_id", "sku", "spend"},
    "sales": {"date", "platform", "sku", "units_sold", "revenue"},
    "ga_events": {"date", "channel", "sku", "sessions", "add_to_cart", "purchases"},
    "inventory": {"sku", "inventory_units"},
    "sku_margins": {"sku", "margin_pct"},
}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _validate(df: pd.DataFrame, name: str) -> None:
    """Ensure a source DataFrame has the columns we expect."""
    required = REQUIRED_COLUMNS[name]
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"{name}.csv is missing required columns: {sorted(missing)}. "
            f"Found columns: {sorted(df.columns)}. "
            f"Regenerate mock data with: python scripts/generate_mock_data.py"
        )


def _safe_merge(left: pd.DataFrame, right: pd.DataFrame, on: list[str]) -> pd.DataFrame:
    """Left-merge that keeps row count identical to `left`."""
    return left.merge(right, on=on, how="left")


def _safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """
    Divide two numeric series, turning divide-by-zero into NaN and
    coercing any weird values (pd.NA, strings, None) into NaN so the
    result is always float. This is the pandas-2.x-safe replacement for
    `(a / b.replace(0, pd.NA)).astype(float)`.
    """
    num = pd.to_numeric(numerator, errors="coerce")
    den = pd.to_numeric(denominator, errors="coerce")
    den = den.replace(0, np.nan)
    result = num / den
    return pd.to_numeric(result, errors="coerce").astype(float)


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------
def build_unified_frame() -> pd.DataFrame:
    """
    Load all sources, reconcile them into a single DataFrame at
    (date, platform, sku) grain, and compute derived efficiency metrics.
    """
    t0 = time.time()

    # ---- 1. Load raw sources ----
    try:
        ads = loader.load_ad_spend().copy()
        sales = loader.load_sales().copy()
        ga = loader.load_ga_events().copy()
        inv = loader.load_inventory().copy()
        margins = loader.load_margins().copy()
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Missing source CSV: {e}. "
            f"Run `python scripts/generate_mock_data.py` from the project root first."
        ) from e

    for name, df in [
        ("ad_spend", ads),
        ("sales", sales),
        ("ga_events", ga),
        ("inventory", inv),
        ("sku_margins", margins),
    ]:
        _validate(df, name)

    logger.info(
        "Loaded sources | ads=%d sales=%d ga=%d inv=%d margins=%d",
        len(ads), len(sales), len(ga), len(inv), len(margins),
    )

    # ---- 2. Aggregate to join grain ----
    sales_agg = (
        sales.groupby(["date", "sku", "platform"], as_index=False)
        .agg(units_sold=("units_sold", "sum"), revenue=("revenue", "sum"))
    )

    ga_agg = (
        ga.groupby(["date", "sku", "channel"], as_index=False)
        .agg(
            sessions=("sessions", "sum"),
            add_to_cart=("add_to_cart", "sum"),
            purchases=("purchases", "sum"),
        )
        .rename(columns={"channel": "platform"})
    )

    # ---- 3. Reconcile ----
    unified = ads.copy()
    unified = _safe_merge(unified, sales_agg, on=["date", "sku", "platform"])
    unified = _safe_merge(unified, ga_agg, on=["date", "sku", "platform"])
    unified = _safe_merge(unified, inv, on=["sku"])
    unified = _safe_merge(unified, margins, on=["sku"])

    # ---- 4. Normalize numerics (fill missing with 0 where it makes sense) ----
    numeric_zero_fill = [
        "spend", "impressions", "clicks",
        "units_sold", "revenue",
        "sessions", "add_to_cart", "purchases",
        "inventory_units", "margin_pct",
    ]
    for col in numeric_zero_fill:
        if col in unified.columns:
            unified[col] = pd.to_numeric(unified[col], errors="coerce").fillna(0.0)

    # ---- 5. Derived metrics (safe divisions) ----
    unified["roas"] = _safe_ratio(unified["revenue"], unified["spend"])
    unified["cpa"] = _safe_ratio(unified["spend"], unified["purchases"])
    unified["cvr"] = _safe_ratio(unified["purchases"], unified["sessions"])

    unified["gross_margin"] = unified["revenue"] * unified["margin_pct"]
    unified["contribution"] = unified["gross_margin"] - unified["spend"]

    # Days-of-cover proxy: current inventory / daily units sold
    unified["stockout_risk"] = _safe_ratio(
        unified["inventory_units"], unified["units_sold"]
    )

    # ---- 6. Final cleanup — every derived column is a real float ----
    derived = [
        "roas", "cpa", "cvr",
        "gross_margin", "contribution", "stockout_risk",
    ]
    unified[derived] = (
        unified[derived]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0.0)
        .astype(float)
    )

    # Sort for deterministic downstream behavior
    unified = unified.sort_values(["date", "platform", "sku"]).reset_index(drop=True)

    duration_ms = (time.time() - t0) * 1000
    logger.info(
        "Unified frame built: %d rows in %.1f ms", len(unified), duration_ms
    )

    # ---- 7. Emit observability event (DB is optional) ----
    try:
        log_event(
            kind="ingest",
            entity_type="system",
            entity_id="reconciler",
            payload={
                "rows_ads": int(len(ads)),
                "rows_sales": int(len(sales)),
                "rows_ga": int(len(ga)),
                "rows_unified": int(len(unified)),
                "duration_ms": round(duration_ms, 2),
            },
        )
    except Exception as e:  # never let logging kill the request
        logger.warning("log_event failed: %s", e)

    return unified


def get_summary() -> dict:
    """Small JSON-safe overview of the reconciled dataset."""
    df = build_unified_frame()

    if df.empty:
        return {
            "rows": 0,
            "platforms": [],
            "skus": [],
            "date_range": [None, None],
            "columns": list(df.columns),
        }

    return {
        "rows": int(len(df)),
        "platforms": sorted(df["platform"].dropna().unique().tolist()),
        "skus": sorted(df["sku"].dropna().unique().tolist()),
        "date_range": [
            str(df["date"].min().date()) if hasattr(df["date"].min(), "date") else str(df["date"].min()),
            str(df["date"].max().date()) if hasattr(df["date"].max(), "date") else str(df["date"].max()),
        ],
        "columns": list(df.columns),
    }


# ---------------------------------------------------------------------
# Optional: quick manual test
# ---------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    summary = get_summary()
    import json
    print(json.dumps(summary, indent=2, default=str))