import ctypes
import logging
import os
import numpy as np
import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)
_native = None


def _try_load_native():
    global _native
    path = settings.NN_LIBRARY_PATH
    if not path or not os.path.exists(path):
        return None
    try:
        lib = ctypes.CDLL(path)
        lib.score_conversion.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_int]
        lib.score_conversion.restype = ctypes.c_float
        _native = lib
        logger.info(f"Native neural net loaded from {path}")
    except Exception as e:
        logger.warning(f"Failed to load native NN: {e}")
    return _native


def _fallback_score(features):
    w = np.array([0.9, -0.6, 1.1, 0.4, -0.3])
    z = float(np.dot(features[: len(w)], w))
    return 1.0 / (1.0 + np.exp(-z))


def score_opportunities(df):
    if df.empty:
        return df

    native = _native or _try_load_native()
    latest = df.sort_values("date").groupby(["platform", "sku"], as_index=False).tail(1).copy()

    scores = []
    for _, row in latest.iterrows():
        feats = np.array([
            float(row.get("cvr", 0.0) or 0.0),
            float(row.get("cpa", 0.0) or 0.0) / 100.0,
            float(row.get("margin_pct", 0.0) or 0.0),
            float(row.get("stockout_risk", 0.0) or 0.0),
            float(row.get("roas", 0.0) or 0.0),
        ], dtype=np.float32)

        if native is not None:
            arr = (ctypes.c_float * len(feats))(*feats)
            p = float(native.score_conversion(arr, len(feats)))
        else:
            p = _fallback_score(feats)
        scores.append(p)

    latest["conversion_probability"] = scores

    margin = latest["margin_pct"].astype(float).fillna(0)
    stock_ok = (latest["stockout_risk"].astype(float).fillna(0) >= 1.0).astype(float)
    latest["opportunity_score"] = (
        0.5 * latest["conversion_probability"]
        + 0.3 * margin.clip(0, 1)
        + 0.2 * stock_ok
    )
    latest = latest.sort_values("opportunity_score", ascending=False)
    return latest
