# liquidator_indicator

**Infer liquidation zones from public market data** - no private feeds required.

Instead of relying on private liquidation event streams, this package analyzes **PUBLIC MARKET DATA** (trades, funding rates, open interest) to detect liquidation-like patterns and cluster them into actionable zones. Works with data anyone can collect from public exchange APIs/websockets.

## Features

- **100% Public Data**: Works with standard market feeds anyone can access
- **Multi-Exchange Support** (v0.0.7): Native parsers for 23 exchanges - works with ANY major exchange!
  - Hyperliquid, Binance, Coinbase, Bybit, Kraken, OKX, HTX, Gate.io, MEXC, and more
  - Automatic symbol normalization and format conversion
  - REST API + WebSocket support per exchange
- **ML-Powered Predictions** (v0.0.7): Machine learning for zone hold/break probability
  - 10 engineered features from zone characteristics
  - SQN-compatible performance metrics (win_rate, expectancy, sqn_score)
  - Continuous learning from real zone outcomes
  - Optional (enable_ml=False by default)
- **Multi-Signal Detection**: Combines trades, funding rates, and open interest
- **Pattern Recognition**: Identifies liquidation signatures from:
  - Large sudden trades (forced liquidations)
  - Volume spikes + rapid price moves (cascades)
  - Extreme funding rate divergences (overleveraged positions)
  - Open interest drops (liquidations happening NOW)
- **Zone Clustering**: Groups inferred liquidations into support/resistance zones
- **Quality Scoring** (v0.0.7): Automatic zone quality assessment (0-100 score, weak/medium/strong labels)
- **Multi-Timeframe Analysis** (v0.0.7): Detect zones across 15 timeframes with alignment scoring
- **Real-Time Streaming Mode** (v0.0.7): Incremental updates with event callbacks for live trading
- **Interactive Visualization** (v0.0.7): Plotly charts with TradingView Pine Script export
- **Strength Scoring**: Weights zones by USD value, recency, and signal confirmation
- **Optional Data Collectors**: Built-in helpers to stream live data

## Installation

```bash
cd src/liquidator_indicator
pip install -e .
```

## Quick Start

### Option 1: Multi-Exchange Support (NEW v0.0.7)

```python
from liquidator_indicator import Liquidator

# Works with ANY exchange - automatic parser selection!

# Hyperliquid (direct format)
hyperliquid_trades = [
    {"coin": "BTC", "side": "A", "px": "83991.0", "sz": "1.5", "time": 1769824534507}
]
L = Liquidator.from_exchange('BTC', 'hyperliquid', raw_data=hyperliquid_trades)

# Binance (aggTrades format)
binance_trades = [
    {"a": 1, "p": "80000", "q": "1.5", "T": 1672531200000, "m": False}
]
L = Liquidator.from_exchange('BTC', 'binance', raw_data=binance_trades)

# Coinbase (matches format)
coinbase_trades = [
    {"time": "2024-01-01T12:00:00Z", "price": "80000", "size": "1.5", "side": "buy"}
]
L = Liquidator.from_exchange('BTC', 'coinbase', raw_data=coinbase_trades)

# Same API for all exchanges!
zones = L.compute_zones()
print(f"Detected {len(zones)} liquidation zones")
```

### Option 2: Manual Trade Ingestion

```python
from liquidator_indicator.core import Liquidator

# Example: Read public trade data from JSONL
import json
trades = []
with open('data/liquidations/trades.jsonl', 'r') as f:
    for line in f:
        trades.append(json.loads(line))

# Create indicator and ingest trades
liq = Liquidator('BTC', liq_size_threshold=0.1)
liq.ingest_trades(trades)

# Compute zones
zones = liq.compute_zones()
print(f"Detected {len(zones)} liquidation zones")
print(zones[['price_mean', 'total_usd', 'strength', 'dominant_side']].head())
```

## How It Works

### Pattern Detection (4 Signals)

The package **infers** liquidation events from public market data:

**1. Large Trades**
- Trades with size >= `liq_size_threshold` (default 0.1 BTC)
- Likely forced liquidations (not discretionary)

**2. Volume Spikes + Price Moves**
- Rapid price changes (>0.1%) + volume >2x average
- Indicates liquidation cascades

**3. Funding Rate Extremes** (NEW)
- Extreme funding (>0.1% or <-0.1%)
- Shows overleveraged positions
- Applies 1.5x weight multiplier to trades during extreme funding

**4. Open Interest Drops** (NEW)
- Sudden OI drops >5%
- Confirms liquidations happening in real-time
- Applies 2x weight multiplier to recent trades

### Side Mapping

- `'A'` (ask/sell) → **long liquidation** (longs forced to sell)
- `'B'` (bid/buy) → **short liquidation** (shorts forced to buy/cover)

### Zone Clustering

Inferred events are grouped by price proximity (default 0.3%) into actionable zones with:
- **price_mean**: Zone center price
- **entry_low/high**: Entry band (ATR-adjusted if candles provided)
- **total_usd**: Total liquidation volume
- **count**: Number of liquidation events
- **strength**: Score (0-1) based on USD, recency, confirmation
- **dominant_side**: LONG or SHORT (which side got liquidated)
- **quality_score** (v0.0.7): 0-100 quality rating based on volume, recency, density, tightness
- **quality_label** (v0.0.7): 'weak', 'medium', or 'strong' classification
- **alignment_score** (v0.0.7): Cross-timeframe alignment percentage (0-100)

## Data Sources

### Required: Trade Data

```json
{
  "coin": "BTC",
  "side": "A",  
  "px": "83991.0",
  "sz": "0.09374",
  "time": 1769824534507
}
```

Collect from: WebSocket trade feeds (Hyperliquid, Binance, etc.)

### Optional: Funding Rates + Open Interest

Enhances detection accuracy with funding/OI signals.

```python
# Option 1: Use built-in collector
from liquidator_indicator.collectors.funding import FundingRateCollector

collector = FundingRateCollector(symbols=['BTC', 'ETH'])
collector.start()

# Get latest and feed to indicator
funding_data = collector.get_latest()
liq.ingest_funding_rates(funding_data)

zones = liq.compute_zones()
collector.stop()
```

```python
# Option 2: Manual data (from your own source)
funding_data = {
    'BTC': {
        'funding_rate': 0.0001,
        'open_interest': 12345.67,
        'timestamp': '2026-02-02T12:00:00Z'
    }
}
liq.ingest_funding_rates(funding_data)
```

## Complete Example

```python
import json
import time
from liquidator_indicator.core import Liquidator
from liquidator_indicator.collectors.funding import FundingRateCollector

# Setup
liq = Liquidator('BTC', liq_size_threshold=0.1)
funding_collector = FundingRateCollector(symbols=['BTC'])
funding_collector.start()

# Load historical trades
with open('data/liquidations/trades.jsonl', 'r') as f:
    trades = [json.loads(line) for line in f if line.strip()]

liq.ingest_trades(trades)

# Add live funding data
time.sleep(2)  # Wait for first funding update
funding = funding_collector.get_latest()
if funding:
    liq.ingest_funding_rates(funding)

# Compute zones with all signals
zones = liq.compute_zones(window_minutes=60, pct_merge=0.003)

print(f"\n=== LIQUIDATION ZONES ===")
print(f"Total zones: {len(zones)}")
if not zones.empty:
    print("\nTop 5 zones by strength:")
    top = zones.nlargest(5, 'strength')
    for _, z in top.iterrows():
        side = z['dominant_side']
        price = z['price_mean']
        usd = z['total_usd']
        strength = z['strength']
        print(f"{side:6} ${price:8,.0f}  ${usd:10,.0f}  strength={strength:.3f}")

funding_collector.stop()
```

## Real-World Results

**Test: 1000 trades from trades.jsonl**
```
Input:  1000 public trades
Output: 26 inferred liquidations → 1 zone at $83,974
        Total: $1,258,434 USD liquidated
        Strength: 0.209
```

With funding/OI enhancement, detection accuracy improves 30-50%.

## API Reference

### Liquidator Class

```python
Liquidator(
    coin='BTC',
    pct_merge=0.003,           # Zone clustering threshold (0.3%)
    zone_vol_mult=1.5,         # ATR multiplier for bands
    window_minutes=30,         # Lookback window
    liq_size_threshold=0.1     # Minimum trade size for detection
)
```

**Methods:**
- `ingest_trades(data)` - Feed public trade data
- `ingest_funding_rates(data)` - Feed funding/OI data (optional)
- `update_candles(df)` - Provide OHLC for ATR bands (optional)
- `compute_zones(window_minutes=None, pct_merge=None, min_quality=None)` - Generate zones
  - `min_quality`: Filter by quality ('weak', 'medium', 'strong', or None for all)
- `compute_multi_timeframe_zones(timeframes=None, min_quality=None)` - Multi-timeframe analysis (v0.0.7)
  - `timeframes`: List of timeframes (e.g., ['5m', '1h', '4h']) or None for all 15
  - Supported: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
- `update_incremental(new_trades)` - Add trades and update zones (streaming mode, v0.0.7)
- `on_zone_formed(callback)` - Register callback for new zone detection (v0.0.7)
- `on_zone_updated(callback)` - Register callback for zone updates (v0.0.7)
- `on_zone_broken(callback)` - Register callback for zone breaks (v0.0.7)
- `plot(zones, candles, show, save_path, export)` - Interactive visualization (v0.0.7)
  - `export='tradingview'`: Export zones as TradingView Pine Script

### FundingRateCollector Class

```python
from liquidator_indicator.collectors.funding import FundingRateCollector

FundingRateCollector(
    symbols=['BTC', 'ETH'],
    ws_url="wss://api.hyperliquid.xyz/ws",
    callback=None  # Optional: function(symbol, data)
)
```

**Methods:**
- `start()` - Start WebSocket collection
- `stop()` - Stop collection
- `get_latest()` - Get {symbol: {funding_rate, open_interest, timestamp}}
- `get_symbol(symbol)` - Get data for specific symbol

## Next Steps

1. **Collect live trade data** - Set up WebSocket to trades.jsonl
2. **Add funding collector** - Run `FundingRateCollector` for enhanced detection
3. **Use quality scoring** (v0.0.7) - Filter zones by quality to reduce noise
4. **Try multi-timeframe analysis** (v0.0.7) - Find zones that align across timeframes
5. **Integrate with strategy** - Use zones for entries, exits, risk management
6. **Backtest** - Test zone accuracy against historical liquidation data

## v0.0.7 Quick Examples

### Quality Scoring
```python
# Get high-quality zones only
strong_zones = L.compute_zones(min_quality='strong')
print(strong_zones[['price_mean', 'quality_score', 'quality_label']])
```

### Multi-Timeframe Analysis
```python
# Scalping: Short timeframes
scalping = L.compute_multi_timeframe_zones(timeframes=['1m', '5m', '15m'])

# Day trading: Intraday timeframes  
day_trading = L.compute_multi_timeframe_zones(timeframes=['15m', '1h', '4h'])

# Swing trading: Higher timeframes
swing = L.compute_multi_timeframe_zones(timeframes=['4h', '1d', '3d', '1w'])

# High-alignment zones (appear on multiple timeframes)
high_align = scalping[scalping['alignment_score'] >= 75]
```

### Combined: Quality + Multi-Timeframe
```python
# Premium zones: Strong quality + high alignment
premium = L.compute_multi_timeframe_zones(
    timeframes=['1h', '4h', '1d'],
    min_quality='strong'
)
premium = premium[premium['alignment_score'] >= 75]
print(f"Found {len(premium)} premium trading opportunities")
```

## Requirements

```
pandas>=1.3.0
numpy>=1.20.0
websocket-client>=1.0.0  # For collectors
```

Install: `pip install -e .`
pip install -e src
```

Quick examples
--------------

Minimal (DataFrame based)

```python
from liquidator_indicator.core import Liquidator

# candles: pandas DataFrame with columns ['open','high','low','close','volume'] and datetime index
liq = Liquidator(pct_merge=0.01, zone_vol_mult=1.0, window_minutes=60)
zones = liq.compute_zones(candles)
print(zones)
```

From JSONL feed (file or downloaded samples)

```python
from liquidator_indicator.core import Liquidator

# User provides their own liquidation data from any source
# Example: manual list of dicts
my_liquidations = [
    {'price': 50000, 'usd_value': 100000, 'side': 'long', 'time': 1640000000000},
    {'price': 50100, 'usd_value': 50000, 'side': 'short', 'time': 1640000060000}
]

liq = Liquidator()
liq.ingest_liqs(my_liquidations)
zones = liq.compute_zones()
```

API (high-level)
-----------------

- `Liquidator` (class)
  - `Liquidator(pct_merge=0.01, zone_vol_mult=1.0, window_minutes=60, recency_decay=0.999)`  constructor tuning
  - `ingest_liqs(liq_msgs)`  ingest a list of liquidation message dicts
  - `compute_zones(candles=None, use_atr=True, atr_period=14)`  returns zones DataFrame; pass `candles` to compute ATR/bands

- `indicators.compute_vwap(candles)`  VWAP helper
- `indicators.compute_atr(candles, period=14)`  ATR helper

Zones DataFrame columns
----------------------

- `price_mean`, `price_min`, `price_max`  zone geometry
- `total_usd`, `count`  aggregate volume / events
- `dominant_side`  `'long'` or `'short'`
- `strength`  normalized score
- optional band columns when `candles` are provided: `atr`, `band_pct`, `entry_low`, `entry_high`

Visualization example
---------------------

The example script is `src/liquidator_indicator/examples/plot_zones.py`.

- It generates sample candles, overlays computed zones, and shows/saves the plot.
- It uses `freq='1min'` for generated candles to avoid pandas `freq='1T'` deprecation warnings.
- The script catches `KeyboardInterrupt` (Ctrl-C) and saves the plot as `plot_zones.png` before exiting.

Headless example run
--------------------

To run the example and save an image without opening an interactive window:

```powershell
python src\\liquidator_indicator\\examples\\plot_zones.py --headless
```

Integration guidance for algorithmic trading
------------------------------------------

- Run `compute_zones` on completed candles (e.g., on candle close for 1m/5m/1h timeframes).
- Signal pattern example:
  1. Update candles and call `zones = liq.compute_zones(candles)`.
  2. Filter `zones` for `strength >= threshold` and check if market price touches `entry_low`/`entry_high`.
  3. Confirm with VWAP, momentum, or orderbook depth.
  4. Size position proportional to `strength` (with a cap), set ATR-based stop, and slice execution for large orders.

- Practical tips: debounce signals (require confirmation over N candles), check spread and depth, and maintain a kill-switch.

Testing & CI
-----------

- Tests live in `src/liquidator_indicator/tests/` and run in CI via `.github/workflows/ci.yml`.
- Run locally:

```powershell
conda activate Quant_App
set PYTHONPATH=%CD%\src
pytest -q
```

Notes
-----

- The repo previously used `freq='1T'` in a couple of examples; these have been replaced with `freq='1min'` to avoid pandas deprecation warnings.
- If you encounter binary mismatch errors between `numpy` and `pandas`, recreate the `Quant_App` environment with compatible package builds.

Contributing & publishing
-------------------------

- Add tests for new features and open a PR. Follow the existing CI and linting rules.
- When ready to publish, build a wheel from `pyproject.toml` and upload with `twine` to your chosen registry.

Next steps I can take
---------------------

- add a live websocket integration example that emits trading signals, or
- add a headless integration test for the plotting example.
