# LIQUIDATOR INDICATOR - QUICK START GUIDE

## What You Get

### 1. VISUAL ZONES ON CHART ✅
Your Dash app now shows:
- **Green shaded rectangles** = LONG liquidation zones (where longs got liquidated)
- **Red shaded rectangles** = SHORT liquidation zones (where shorts got liquidated)  
- **Price labels** = Zone center price + side
- **Top 3 strongest zones** displayed

Example from your screenshot:
```
Chart now shows: Green zone at $83,868 labeled "LONG 83,868.53"
                 (Previously: only text in left panel)
```

### 2. MULTI-SIGNAL DETECTION ✅
Package detects liquidations from **4 patterns**:

| Pattern | What It Detects | Weight Multiplier |
|---------|-----------------|-------------------|
| Large trades | Size >= 0.1 BTC (forced liquidations) | 1.0x |
| Volume spikes | >2x avg + price move >0.1% (cascades) | 1.0x |
| Funding extremes | >0.1% funding (overleveraged) | 1.5x |
| OI drops | >5% OI decrease (liquidations NOW) | 2.0x |

### 3. DATA COLLECTORS ✅
**Included in package**:
- `FundingRateCollector` - Live funding rates + open interest from WebSocket

**You provide** (from any source):
- Trade data (from public WebSocket feeds)

## Usage

### Quick Test (Your Existing Data)
```bash
cd C:\Users\Warshawski\QUANT_APP
python test_enhanced_liquidator.py
```

Output:
```
1000 trades → 26 liquidations → 1 zone at $83,975 (strength 0.209)
```

### See Visual Zones (Dash App)
```bash
python start_dash_with_liq.py
```

Open http://127.0.0.1:8059 → See green/red zones on chart

### Use In Your Code

**Option 1: Basic (trades only)**
```python
from liquidator_indicator.core import Liquidator

liq = Liquidator('BTC', liq_size_threshold=0.1)
liq.ingest_trades(trades)  # Your trade data
zones = liq.compute_zones()

# zones has: price_mean, entry_low, entry_high, total_usd, strength, dominant_side
```

**Option 2: Enhanced (trades + funding)**
```python
from liquidator_indicator.core import Liquidator
from liquidator_indicator.collectors.funding import FundingRateCollector

# Start funding collector
collector = FundingRateCollector(symbols=['BTC', 'ETH'])
collector.start()

# Create indicator
liq = Liquidator('BTC')

# Ingest trades
liq.ingest_trades(trades)

# Add funding data (enhances detection)
funding = collector.get_latest()
liq.ingest_funding_rates(funding)

# Compute zones with all signals
zones = liq.compute_zones()

# Stop collector
collector.stop()
```

## Data You Need

### Required: Trades
Collect from any exchange WebSocket (Hyperliquid, Binance, etc.)

Format:
```json
{"coin": "BTC", "side": "A", "px": "83991.0", "sz": "0.09374", "time": 1769824534507}
```

Your existing file works: `data/liquidations/trades.jsonl`

### Optional: Funding Rates (for better accuracy)
Use included collector:
```python
collector = FundingRateCollector(symbols=['BTC'])
collector.start()
# ... use collector.get_latest()
collector.stop()
```

Or provide manually:
```python
funding = {'BTC': {'funding_rate': 0.0001, 'open_interest': 12345, 'timestamp': '...'}}
liq.ingest_funding_rates(funding)
```

## What's Included in Package

```
src/liquidator_indicator/
├── core.py                      # Main Liquidator class
├── collectors/
│   ├── __init__.py
│   └── funding.py              # FundingRateCollector (WebSocket)
├── examples/
│   └── plot_zones.py           # Matplotlib visualization
├── tests/
│   └── test_core.py            # Unit tests
├── README.md                    # Full documentation
└── pyproject.toml              # Package config
```

**Install**: `pip install -e src/liquidator_indicator`

## Next Steps

### For Package Distribution
Package is **READY TO SHARE**. Users can:
1. `pip install -e .`
2. Provide trade data (from any exchange)
3. Optionally use `FundingRateCollector`
4. Get liquidation zones

### For Your Trading
1. **Set up live trade collector** - WebSocket to `data/liquidations/trades.jsonl`
2. **Run funding collector** - `FundingRateCollector(['BTC']).start()`  
3. **Run Dash app** - See live zones on chart
4. **Use zones in strategy** - Enter at zone edges, set stops at zone boundaries

## Questions Answered

**Q: Do users need to set up data streams?**  
A: Yes, they provide trade data. Package provides analysis logic + optional funding collector.

**Q: Include collectors or just document?**  
A: BOTH - Included `FundingRateCollector` + comprehensive docs.

**Q: What other data sources to include?**  
A: Analysis complete:
- ✅ Trades - Already implemented
- ✅ Funding/OI - Now included
- 📄 Orderbook - Documented approach
- 🔒 User fills - Documented but not included (private data)

**Q: Why no visual zones on chart?**  
A: FIXED - Zones now drawn as green/red shaded rectangles with labels.

---

**STATUS**: ✅ Complete & Production Ready
