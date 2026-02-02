"""Example showing basic usage of the Liquidator package."""
from liquidator_indicator import Liquidator

sample = [
    {'timestamp':'2026-01-31T12:00:00Z','side':'long','price':80000,'usd_value':500000},
    {'timestamp':'2026-01-31T12:01:00Z','side':'long','price':79920,'usd_value':300000},
    {'timestamp':'2026-01-31T12:05:00Z','side':'short','price':78000,'usd_value':200000},
]

L = Liquidator('BTC')
L.ingest_liqs(sample)
z = L.compute_zones(window_minutes=60)
print(z)
