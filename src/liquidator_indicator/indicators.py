"""Common indicator helpers: VWAP and ATR that are useful for zone banding."""
from typing import Optional
import pandas as pd


def compute_vwap(candles: pd.DataFrame, period: Optional[int] = None, price_col: str = 'close', vol_col: str = 'volume') -> pd.Series:
    """Compute VWAP series from candles.

    If `period` is None returns cumulative VWAP, otherwise a rolling-window VWAP of given length.
    Candles must contain price and volume columns.
    """
    if candles is None or candles.empty:
        return pd.Series(dtype=float)
    df = candles.copy()
    # normalize column names
    if price_col not in df.columns:
        if 'close' in df.columns:
            price_col = 'close'
        elif 'px' in df.columns:
            price_col = 'px'
    if vol_col not in df.columns:
        if 'volume' in df.columns:
            vol_col = 'volume'
    df[price_col] = pd.to_numeric(df[price_col], errors='coerce')
    df[vol_col] = pd.to_numeric(df[vol_col], errors='coerce').fillna(0.0)
    tp_vol = df[price_col] * df[vol_col]
    if period is None:
        cum_tp_vol = tp_vol.cumsum()
        cum_vol = df[vol_col].cumsum()
        vwap = cum_tp_vol / cum_vol.replace({0: pd.NA})
        return vwap.ffill().fillna(0.0)
    else:
        tp_vol_r = tp_vol.rolling(window=period, min_periods=1).sum()
        vol_r = df[vol_col].rolling(window=period, min_periods=1).sum()
        vwap = tp_vol_r / vol_r.replace({0: pd.NA})
        return vwap.ffill().fillna(0.0)


def compute_atr(candles: pd.DataFrame, per: int = 14) -> pd.Series:
    """Public ATR computation (Wilder-style) from candles with high/low/close columns."""
    if candles is None or candles.empty:
        return pd.Series(dtype=float)
    df = candles.copy()
    df['high'] = pd.to_numeric(df['high'], errors='coerce')
    df['low'] = pd.to_numeric(df['low'], errors='coerce')
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - df['close'].shift(1)).abs()
    tr3 = (df['low'] - df['close'].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).dropna()
    atr = tr.ewm(alpha=1.0/per, adjust=False).mean()
    return atr
