"""Demo: Interactive Visualization - Plotly charts and TradingView export."""
from liquidator_indicator import Liquidator
import pandas as pd
import numpy as np

print("=" * 70)
print("INTERACTIVE VISUALIZATION DEMO")
print("=" * 70)

# Generate sample trade data
now = pd.Timestamp.now(tz='UTC')
trades = []

# Zone 1: Strong long liquidation at $80,000
for i in range(60):
    trades.append({
        'time': now - pd.Timedelta(minutes=i % 40),
        'px': 80000 + np.random.randn() * 3,
        'sz': 2.0,
        'side': 'A'
    })

# Zone 2: Medium short liquidation at $79,500
for i in range(30):
    trades.append({
        'time': now - pd.Timedelta(minutes=30 + i * 2),
        'px': 79500 + np.random.randn() * 10,
        'sz': 1.0,
        'side': 'B'
    })

# Zone 3: Weak zone at $80,500
for i in range(15):
    trades.append({
        'time': now - pd.Timedelta(hours=2 + i * 0.3),
        'px': 80500 + np.random.randn() * 20,
        'sz': 0.5,
        'side': 'A'
    })

# Generate sample candles
print("\n📊 Generating sample data...")
candles = pd.DataFrame({
    'open': [79800, 79900, 80000, 80100, 79950, 79800, 79700, 79600],
    'high': [79900, 80000, 80200, 80150, 80000, 79900, 79800, 79700],
    'low': [79700, 79850, 79950, 79950, 79800, 79600, 79500, 79400],
    'close': [79850, 79950, 80050, 79975, 79850, 79700, 79600, 79500],
}, index=pd.date_range(now - pd.Timedelta(hours=8), now, periods=8))

# Create indicator and compute zones
L = Liquidator('BTC')
L.ingest_trades(trades)
L.update_candles(candles)
zones = L.compute_zones()

print(f"✅ Generated {len(zones)} zones")
print("\nZone Summary:")
for idx, zone in zones.iterrows():
    print(f"  {idx+1}. ${zone['price_mean']:.2f} - {zone['dominant_side']:6s} - "
          f"Q:{zone['quality_score']:.0f} ({zone['quality_label']:6s}) - "
          f"${zone['total_usd']:,.0f}")

# Test 1: Interactive Plotly chart
print("\n" + "=" * 70)
print("Test 1: Interactive Plotly Chart")
print("=" * 70)

try:
    print("\n📈 Opening interactive chart in browser...")
    print("   Features:")
    print("   - Candlestick price chart")
    print("   - Shaded zone rectangles")
    print("   - Color-coded by quality (strong=green/red, medium=orange, weak=gray)")
    print("   - Hover for details")
    print("   - Zoom, pan, reset tools")
    
    fig = L.plot(zones, candles, show=False, save_path='liquidation_zones_chart.html')
    
    if fig:
        print("\n✅ Chart generated successfully!")
        print("   Saved to: liquidation_zones_chart.html")
        print("   Open in browser to interact with chart")
    
except ImportError:
    print("\n⚠️  Plotly not installed. Install with: pip install plotly")
    print("   Skipping interactive chart test")

# Test 2: TradingView Pine Script export
print("\n" + "=" * 70)
print("Test 2: TradingView Pine Script Export")
print("=" * 70)

print("\n📝 Generating TradingView Pine Script...")
try:
    fig = L.plot(zones, candles, show=False, export='tradingview')
    print("\n✅ Pine Script generated!")
    print("   Copy the script above and paste into TradingView Pine Editor")
    
except ImportError:
    print("\n⚠️  Plotly not installed. Install with: pip install plotly")

# Test 3: Programmatic access to figure
print("\n" + "=" * 70)
print("Test 3: Programmatic Figure Customization")
print("=" * 70)

try:
    fig = L.plot(zones, candles, show=False)
    
    if fig:
        # Customize figure programmatically
        fig.update_layout(
            title="Custom: BTC Liquidation Zones with Quality Scoring",
            template='plotly_white',  # Change theme
            height=600
        )
        
        # Save customized version
        fig.write_html('custom_zones_chart.html')
        print("✅ Customized chart saved to: custom_zones_chart.html")
        
except ImportError:
    print("⚠️  Plotly not installed")

# Test 4: Multi-timeframe visualization
print("\n" + "=" * 70)
print("Test 4: Multi-Timeframe Zones Visualization")
print("=" * 70)

mtf_zones = L.compute_multi_timeframe_zones(timeframes=['5m', '1h', '4h', '1d'])

if not mtf_zones.empty:
    print(f"\n📊 Generated {len(mtf_zones)} multi-timeframe zones")
    print("\nTimeframe distribution:")
    for tf in ['5m', '1h', '4h', '1d']:
        tf_zones = mtf_zones[mtf_zones['timeframe'] == tf]
        print(f"  {tf:4s}: {len(tf_zones)} zones")
    
    try:
        # Plot multi-timeframe zones
        fig_mtf = L.plot(mtf_zones, candles, show=False, save_path='mtf_zones_chart.html')
        if fig_mtf:
            print("\n✅ Multi-timeframe chart saved to: mtf_zones_chart.html")
    except ImportError:
        pass

# Usage examples
print("\n" + "=" * 70)
print("💡 USAGE EXAMPLES")
print("=" * 70)
print("""
1. Basic Visualization:
   zones = L.compute_zones()
   L.plot(zones)  # Opens in browser

2. Save Without Showing:
   L.plot(zones, show=False, save_path='zones.html')

3. With Candlestick Data:
   L.plot(zones, candles=df_candles)

4. Export to TradingView:
   L.plot(zones, export='tradingview')
   # Copy generated Pine Script to TradingView

5. Customize Programmatically:
   fig = L.plot(zones, show=False)
   fig.update_layout(template='plotly_white')
   fig.add_annotation(text="My Note", x=..., y=...)
   fig.show()

6. Multi-Timeframe Visualization:
   mtf_zones = L.compute_multi_timeframe_zones()
   L.plot(mtf_zones, candles)

Chart Features:
- Interactive zoom, pan, hover
- Color-coded zones by quality
- Candlestick overlay (optional)
- Export to HTML or TradingView
- Fully customizable Plotly figure
""")

print("\n" + "=" * 70)
print("✅ VISUALIZATION DEMO COMPLETE")
print("=" * 70)
print("\nGenerated Files:")
print("  - liquidation_zones_chart.html (interactive chart)")
print("  - custom_zones_chart.html (customized theme)")
print("  - mtf_zones_chart.html (multi-timeframe zones)")
print("\nOpen these files in your browser to interact with the charts!")
