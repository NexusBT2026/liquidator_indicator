"""Plot example: show OHLC candles and overlay liquidation zones computed by Liquidator.

Run: python plot_zones.py
"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from liquidator_indicator import Liquidator


def make_sample_candles(n=120, start_price=80000):
    rng = pd.date_range(end=pd.Timestamp.utcnow(), periods=n, freq='1min')
    prices = start_price + np.cumsum(np.random.randn(n).cumsum() * 2)
    o = prices + np.random.randn(n)
    h = np.maximum(o, prices) + np.abs(np.random.rand(n) * 10)
    l = np.minimum(o, prices) - np.abs(np.random.rand(n) * 10)
    c = prices
    v = np.random.randint(10, 1000, size=n)
    return pd.DataFrame({'datetime': rng, 'open': o, 'high': h, 'low': l, 'close': c, 'volume': v})


def main():
    candles = make_sample_candles()
    # create some synthetic liquidations clustered near recent lows/highs
    last_price = float(candles['close'].iloc[-1])
    liqs = []
    for i in range(6):
        # create clusters around last_price +/- i*200
        base = last_price - (i-3) * 150
        for j in range(3):
            ts = candles['datetime'].iloc[-1] - pd.Timedelta(minutes=np.random.randint(0, 60))
            price = base + np.random.randn() * 5
            liqs.append({'timestamp': ts.isoformat(), 'side': 'long' if i%2==0 else 'short', 'price': price, 'usd_value': float(100000*(1+np.random.rand()))})

    L = Liquidator('BTC', pct_merge=0.003, zone_vol_mult=1.5, window_minutes=120)
    L.update_candles(candles.rename(columns={'datetime': 'datetime', 'open':'open','high':'high','low':'low','close':'close','volume':'volume'}))
    L.ingest_liqs(liqs)
    zones = L.compute_zones(window_minutes=120, pct_merge=0.005, use_atr=True)

    fig, ax = plt.subplots(figsize=(12,6))
    # plot candles as simple lines
    ax.plot(candles['datetime'], candles['close'], color='white')
    ax.set_facecolor('#0d1117')
    fig.patch.set_facecolor('#0d1117')
    ax.xaxis_date()
    # overlay zones
    for idx, z in zones.iterrows():
        try:
            low = z.get('entry_low', z['price_min'])
            high = z.get('entry_high', z['price_max'])
            pm = z['price_mean']
            color = '#2ecc71' if z.get('dominant_side','long') == 'long' else '#e74c3c'
            ax.fill_between(candles['datetime'].iloc[-10:], low, high, color=color, alpha=0.15)
            ax.hlines(pm, candles['datetime'].iloc[0], candles['datetime'].iloc[-1], colors=color, linestyles='dashed', linewidth=1)
        except Exception:
            continue

    ax.set_title('Sample candles with liquidation zones', color='white')
    ax.tick_params(colors='white', which='both')
    plt.tight_layout()
    try:
        plt.show()
    except KeyboardInterrupt:
        # user pressed Ctrl-C while the interactive window was open
        out_path = 'plot_zones.png'
        try:
            fig.savefig(out_path)
            print(f"Interrupted — saved current plot to {out_path}")
        except Exception:
            print("Interrupted — failed to save plot")
    finally:
        try:
            plt.close(fig)
        except Exception:
            pass


if __name__ == '__main__':
    main()
