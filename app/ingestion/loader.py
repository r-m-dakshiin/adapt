import os
import logging
from functools import lru_cache
import pandas as pd

logger = logging.getLogger(__name__)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _path(name):
    return os.path.join(DATA_DIR, name)


@lru_cache(maxsize=1)
def load_ad_spend():
    return pd.read_csv(_path("ad_spend.csv"), parse_dates=["date"])


@lru_cache(maxsize=1)
def load_sales():
    return pd.read_csv(_path("sales.csv"), parse_dates=["date"])


@lru_cache(maxsize=1)
def load_ga_events():
    return pd.read_csv(_path("ga_events.csv"), parse_dates=["date"])


@lru_cache(maxsize=1)
def load_inventory():
    return pd.read_csv(_path("inventory.csv"))


@lru_cache(maxsize=1)
def load_margins():
    return pd.read_csv(_path("sku_margins.csv"))


def reload_all():
    load_ad_spend.cache_clear()
    load_sales.cache_clear()
    load_ga_events.cache_clear()
    load_inventory.cache_clear()
    load_margins.cache_clear()
