# Liquidator Indicator - Trading Guide

## What is it?
The Liquidator Indicator identifies **liquidation clusters** from public trade data (no private node feeds needed). It shows where large liquidations occurred recently, which often become **support/resistance zones**.

**New in v0.0.7:** Works with 23 major crypto exchanges (Hyperliquid, Binance, Coinbase, Bybit, Kraken, and more). Use `Liquidator.from_exchange()` for automatic format conversion.

## Visual Guide

### Zone Colors
- **BLUE zones** = Support/Demand (SHORT liquidations clustered here)
  - Shorts got liquidated → forced BUY pressure
  - Price tends to BOUNCE at these levels
  - FADE strategy: Buy near bottom of blue zone

- **ORANGE zones** = Resistance/Supply (LONG liquidations clustered here)
  - Longs got liquidated → forced SELL pressure  
  - Price tends to REJECT at these levels
  - FADE strategy: Sell/short near top of orange zone

### Zone Components
1. **Thick colored border** (3px) = Zone boundary
2. **Light fill** (8-14% opacity) = Full zone range
3. **Solid center line** (2px) = Exact liquidation cluster price
4. **Label on left** = Timeframe (10m/1h/4h LIQ)

### Multi-Timeframe Zones
- **10m zones** (8% opacity) = Short-term scalp levels (last 10 minutes of liqs)
- **1h zones** (11% opacity) = Intraday swing levels (last hour of liqs)
- **4h zones** (14% opacity) = Longer-term structural levels (last 4 hours of liqs)

**When zones align** (e.g., 1h + 4h blue zones overlap) → **STRONGER support**

---

## Trading Strategies

### 1. FADE Strategy (Counter-Trend)
**When to use:** Price approaches a zone but hasn't broken through yet

**BLUE zone (Support):**
- Enter LONG near bottom of zone
- Stop loss: Below zone (1-2% below center line)
- Target: Opposite side of zone or next resistance

**ORANGE zone (Resistance):**
- Enter SHORT near top of zone  
- Stop loss: Above zone (1-2% above center line)
- Target: Opposite side of zone or next support

**Best for:** Range-bound markets, high win rate but smaller R:R

---

### 2. JOIN Strategy (Breakout/Momentum)
**When to use:** Price breaks THROUGH a zone with high volume

**Breaking above ORANGE zone:**
- Enter LONG after close above zone + retest
- Stop loss: Back inside zone
- Target: Next zone or 2-3x zone height

**Breaking below BLUE zone:**
- Enter SHORT after close below zone + retest
- Stop loss: Back inside zone  
- Target: Next zone or 2-3x zone height

**Best for:** Trending markets, lower win rate but bigger R:R

---

### 3. SCALE Strategy (Add to Winners)
**When to use:** Already in a profitable position, price approaching next zone

**In a LONG position:**
- Add 25-50% at blue support zones (price dips to support)
- Max 3 scale-ins total
- Move stop to breakeven after 2nd add

**In a SHORT position:**
- Add 25-50% at orange resistance zones (price rallies to resistance)
- Max 3 scale-ins total
- Move stop to breakeven after 2nd add

**Best for:** Strong trends, maximizing winners

---

### 4. EXIT Strategy (Danger Zones)
**When to use:** Already in position, approaching opposite zone type

**LONG position → approaching ORANGE zone:**
- Take 50-75% profit near top of orange zone
- Trail stop on remainder

**SHORT position → approaching BLUE zone:**
- Take 50-75% profit near bottom of blue zone
- Trail stop on remainder

**Best for:** Locking in profits before reversals

---

## Zone Strength Assessment

### Strong Zones (High Confidence)
✅ Multiple timeframes overlap (1h + 4h together)
✅ Center line clearly visible (thick solid line)
✅ Recent formation (within last 2-6 hours)
✅ Large zone height (>0.5% of price)
✅ Near current price (within 2-3% distance)

### Weak Zones (Low Confidence)
❌ Only 10m zone (no higher TF confirmation)
❌ Faint/narrow zone (strength <0.2)
❌ Far from current price (>5% away)
❌ Very old data (>24h since formation)
❌ Small zone height (<0.2% of price)

---

## Real-World Examples

### Example 1: FADE at Blue Support
```
Current price: $77,000
Blue 1h + 4h zones overlap at $76,500 (center line)
Zone range: $76,200 - $76,800

TRADE:
- Wait for price to touch $76,400 (near zone bottom)
- Enter LONG with stop at $76,000 (below zone)
- Target 1: $77,000 (zone exit back to current price)
- Target 2: $77,500 (orange zone above)
- Risk: $400 | Reward: $600-1,100 | R:R = 1.5-2.75
```

### Example 2: JOIN Breakout Through Orange Resistance
```
Current price: $78,200
Orange 4h zone at $78,000 (center line)
Zone range: $77,700 - $78,300

TRADE:
- Price breaks above $78,400 on volume
- Wait for retest of $78,200-78,300 (old resistance = new support)
- Enter LONG on bounce with stop at $77,900 (back in zone)
- Target 1: $79,500 (zone height * 2)
- Target 2: Next orange zone above
- Risk: $300-400 | Reward: $1,200+ | R:R = 3+
```

### Example 3: SCALE into Blue Support (In LONG)
```
Entry: $79,000 (first long entry)
Current PnL: +$300 (+0.4%)
Blue 1h zone forming at $78,500 (pullback to support)

TRADE:
- Price dips to $78,550 (in blue zone)
- Add 50% to position (scale-in #1)
- New avg entry: $78,775
- Stop moved to $78,300 (breakeven on original)
- Allows riding trend with reduced risk
```

---

## Common Mistakes to Avoid

1. **Trading every zone** → Only trade strong multi-TF zones near current price
2. **Ignoring stop losses** → Always use stops 1-2% outside zones
3. **Fading strong breakouts** → If price closes through zone, don't fight it
4. **Over-scaling** → Max 3 adds, respect risk management
5. **Trading stale zones** → Old zones (>24h) lose relevance
6. **Fighting the trend** → Fade in ranges, join in trends

---

## Quick Decision Matrix

| Scenario | Action | Confidence |
|----------|--------|------------|
| Price at blue 4h zone, no breakout yet | FADE long | HIGH |
| Price at orange 1h zone, downtrend | FADE short | MEDIUM |
| Price breaks above orange 4h + retest | JOIN long | HIGH |
| Price breaks below blue 10m only | WAIT | LOW |
| In long, price hits orange 4h zone | EXIT 50-75% | HIGH |
| In short, price hits blue 1h+4h zones | EXIT full | HIGH |
| Multiple blue zones stack at same price | FADE long aggressively | VERY HIGH |
| 10m zone only, no higher TF confirm | SKIP | VERY LOW |

---

## Integration with Other Indicators

### With SMA20 (Simple Moving Average)
- Blue zone + price above SMA20 = **STRONG long bias**
- Orange zone + price below SMA20 = **STRONG short bias**
- Zones + SMA crossover = **High probability setup**

### With Volume
- High volume at zone = **Stronger reaction expected**
- Low volume breakout = **False breakout risk**

### With Market Structure
- Blue zones at swing lows = **Demand confirmation**
- Orange zones at swing highs = **Supply confirmation**

---

## Risk Management Rules

1. **Position size:** 1-2% risk per trade
2. **Stop loss:** Always 1-2% outside zone boundaries
3. **Max 3 simultaneous zones trades** (avoid over-exposure)
4. **Scale-in limit:** Max 3 adds per position
5. **Profit taking:** 50% at 1:1 R:R, trail remainder
6. **Daily loss limit:** Stop if -3% account balance in one day

---

## Troubleshooting

**Q: I don't see any zones**
- Check that LIQUIDATOR checkbox is enabled (top right)
- Verify trades are flowing: `Get-Content data\liquidations\trades.jsonl -Tail 5`
- Restart dashboard if indicator just enabled

**Q: Zones are too faint**
- Zones have 8-14% opacity by design to not hide candles
- Look for **thick colored borders** (3px wide) and **center lines**
- **Labels on left** show "10m LIQ" / "1h LIQ" / "4h LIQ"

**Q: Too many zones overlapping**
- Focus on **zones near current price** (within 2-3%)
- Prioritize **1h + 4h zones** over 10m-only
- Use only strongest zones (multiple TFs aligned)

**Q: Zones don't match current price**
- Old trade data: ensure WS listener running (`start_live_trading.bat`)
- Check last trade timestamp: `Get-Content data\liquidations\trades.jsonl -Tail 1`
- Zones use 48h lookback, ignore very old data

---

## Summary

**BLUE = Support → BUY near bottom (fade) or SELL if breaks below (join)**  
**ORANGE = Resistance → SELL near top (fade) or BUY if breaks above (join)**

**Strong zones = Multiple timeframes + near price + recent**  
**Weak zones = Single timeframe + far away + old**

**Always use stops. Always manage risk. Zones are probabilities, not certainties.**
