import pytest
import pandas as pd
from liquidator_indicator import Liquidator


def test_cluster_basic():
    L = Liquidator('BTC')
    sample = [
        {'timestamp':'2026-01-31T12:00:00Z','side':'long','price':80000,'usd_value':500000},
        {'timestamp':'2026-01-31T12:01:00Z','side':'long','price':79960,'usd_value':300000},
        {'timestamp':'2026-01-31T12:05:00Z','side':'short','price':78000,'usd_value':200000},
    ]
    L.ingest_liqs(sample)
    z = L.compute_zones(window_minutes=120, pct_merge=0.005)
    assert not z.empty
    assert 'strength' in z.columns
