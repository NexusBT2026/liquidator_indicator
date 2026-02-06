import pandas as pd
from liquidator_indicator import Liquidator


def test_compute_zones_includes_bands():
    L = Liquidator('BTC', pct_merge=0.003, zone_vol_mult=1.5, window_minutes=120, cutoff_hours=None)
    # create simple candles
    candles = pd.DataFrame({'high':[10,11,12,13],'low':[8,9,10,11],'close':[9,10,11,12]})
    L.update_candles(candles)
    # inject liqs
    sample = [
        {'timestamp':'2026-01-31T12:00:00Z','side':'long','price':11,'usd_value':100000},
        {'timestamp':'2026-01-31T12:01:00Z','side':'short','price':12,'usd_value':200000}
    ]
    L.ingest_liqs(sample)
    z = L.compute_zones()
    assert not z.empty
    # bands/atr fields should be present when candles provided
    assert 'atr' in z.columns and 'band' in z.columns and 'entry_low' in z.columns and 'entry_high' in z.columns
