"""Numba-optimized functions for performance-critical operations.

These JIT-compiled functions provide 10-100x speedup for numerical loops:
- Price clustering algorithm
- Strength computation with time decay
- ATR (Average True Range) calculation
"""
import numpy as np
from numba import jit


@jit(nopython=True, cache=True)
def cluster_prices_numba(prices, usd_values, timestamps_seconds, sides_encoded, pct_merge):
    """Fast clustering of prices into zones using numba JIT.
    
    Args:
        prices: np.array of float prices (sorted)
        usd_values: np.array of float USD values
        timestamps_seconds: np.array of float timestamps (seconds since epoch)
        sides_encoded: np.array of int (0=unknown, 1=long, 2=short)
        pct_merge: float percentage threshold for merging (e.g., 0.003 for 0.3%)
    
    Returns:
        Tuple of arrays defining clusters:
        - cluster_ids: array mapping each price to its cluster ID
        - cluster_price_means: mean price per cluster
        - cluster_price_mins: min price per cluster
        - cluster_price_maxs: max price per cluster
        - cluster_usd_totals: total USD per cluster
        - cluster_counts: count per cluster
        - cluster_ts_first: first timestamp per cluster
        - cluster_ts_last: last timestamp per cluster
        - cluster_side_long: count of longs per cluster
        - cluster_side_short: count of shorts per cluster
    """
    n = len(prices)
    if n == 0:
        return (np.empty(0, dtype=np.int32), np.empty(0), np.empty(0), np.empty(0),
                np.empty(0), np.empty(0, dtype=np.int32), np.empty(0), np.empty(0),
                np.empty(0, dtype=np.int32), np.empty(0, dtype=np.int32))
    
    cluster_ids = np.zeros(n, dtype=np.int32)
    current_cluster = 0
    
    # Track cluster stats
    cluster_price_sum = prices[0]
    cluster_price_min = prices[0]
    cluster_price_max = prices[0]
    cluster_usd_sum = usd_values[0]
    cluster_count = 1
    cluster_ts_min = timestamps_seconds[0]
    cluster_ts_max = timestamps_seconds[0]
    cluster_long_count = 1 if sides_encoded[0] == 1 else 0
    cluster_short_count = 1 if sides_encoded[0] == 2 else 0
    
    cluster_ids[0] = current_cluster
    
    # Output lists (will convert to arrays)
    cluster_means = [0.0] * n  # Pre-allocate max size
    cluster_mins = [0.0] * n
    cluster_maxs = [0.0] * n
    cluster_usds = [0.0] * n
    cluster_cnts = [0] * n
    cluster_ts_firsts = [0.0] * n
    cluster_ts_lasts = [0.0] * n
    cluster_longs = [0] * n
    cluster_shorts = [0] * n
    
    for i in range(1, n):
        p = prices[i]
        cluster_mean = cluster_price_sum / cluster_count
        
        # Check if within merge threshold
        if abs(p - cluster_mean) / cluster_mean <= pct_merge:
            # Add to current cluster
            cluster_price_sum += p
            cluster_price_min = min(cluster_price_min, p)
            cluster_price_max = max(cluster_price_max, p)
            cluster_usd_sum += usd_values[i]
            cluster_count += 1
            cluster_ts_min = min(cluster_ts_min, timestamps_seconds[i])
            cluster_ts_max = max(cluster_ts_max, timestamps_seconds[i])
            if sides_encoded[i] == 1:
                cluster_long_count += 1
            elif sides_encoded[i] == 2:
                cluster_short_count += 1
            cluster_ids[i] = current_cluster
        else:
            # Save current cluster stats
            cluster_means[current_cluster] = cluster_mean
            cluster_mins[current_cluster] = cluster_price_min
            cluster_maxs[current_cluster] = cluster_price_max
            cluster_usds[current_cluster] = cluster_usd_sum
            cluster_cnts[current_cluster] = cluster_count
            cluster_ts_firsts[current_cluster] = cluster_ts_min
            cluster_ts_lasts[current_cluster] = cluster_ts_max
            cluster_longs[current_cluster] = cluster_long_count
            cluster_shorts[current_cluster] = cluster_short_count
            
            # Start new cluster
            current_cluster += 1
            cluster_price_sum = p
            cluster_price_min = p
            cluster_price_max = p
            cluster_usd_sum = usd_values[i]
            cluster_count = 1
            cluster_ts_min = timestamps_seconds[i]
            cluster_ts_max = timestamps_seconds[i]
            cluster_long_count = 1 if sides_encoded[i] == 1 else 0
            cluster_short_count = 1 if sides_encoded[i] == 2 else 0
            cluster_ids[i] = current_cluster
    
    # Save final cluster
    cluster_means[current_cluster] = cluster_price_sum / cluster_count
    cluster_mins[current_cluster] = cluster_price_min
    cluster_maxs[current_cluster] = cluster_price_max
    cluster_usds[current_cluster] = cluster_usd_sum
    cluster_cnts[current_cluster] = cluster_count
    cluster_ts_firsts[current_cluster] = cluster_ts_min
    cluster_ts_lasts[current_cluster] = cluster_ts_max
    cluster_longs[current_cluster] = cluster_long_count
    cluster_shorts[current_cluster] = cluster_short_count
    
    # Trim to actual number of clusters
    num_clusters = current_cluster + 1
    
    return (
        cluster_ids,
        np.array(cluster_means[:num_clusters]),
        np.array(cluster_mins[:num_clusters]),
        np.array(cluster_maxs[:num_clusters]),
        np.array(cluster_usds[:num_clusters]),
        np.array(cluster_cnts[:num_clusters], dtype=np.int32),
        np.array(cluster_ts_firsts[:num_clusters]),
        np.array(cluster_ts_lasts[:num_clusters]),
        np.array(cluster_longs[:num_clusters], dtype=np.int32),
        np.array(cluster_shorts[:num_clusters], dtype=np.int32)
    )


@jit(nopython=True, cache=True)
def compute_strength_batch(usd_totals, counts, last_ts_seconds, current_time_seconds):
    """Vectorized strength computation with time decay.
    
    Args:
        usd_totals: array of USD totals per zone
        counts: array of trade counts per zone
        last_ts_seconds: array of last timestamp (seconds since epoch) per zone
        current_time_seconds: current time in seconds since epoch
    
    Returns:
        Array of strength scores
    """
    n = len(usd_totals)
    strengths = np.zeros(n)
    
    for i in range(n):
        # Log-scaled components
        a = np.log1p(usd_totals[i])
        b = np.log1p(counts[i])
        
        # Time decay: recent events score higher (half-life = 1 hour = 3600 seconds)
        age_sec = current_time_seconds - last_ts_seconds[i]
        recency_weight = 1.0 / (1.0 + (age_sec / 3600.0))
        
        # Weighted combination
        strengths[i] = (a * 0.6 + b * 0.4) * recency_weight
    
    return strengths


@jit(nopython=True, cache=True)
def compute_atr_numba(high, low, close, period=14):
    """Fast ATR (Average True Range) calculation using Wilder's smoothing.
    
    Args:
        high: array of high prices
        low: array of low prices
        close: array of close prices
        period: ATR period (default 14)
    
    Returns:
        Array of ATR values (same length as input)
    """
    n = len(high)
    if n == 0:
        return np.empty(0)
    
    # Compute True Range
    tr = np.zeros(n)
    tr[0] = high[0] - low[0]  # First TR is just high-low
    
    for i in range(1, n):
        tr1 = high[i] - low[i]
        tr2 = abs(high[i] - close[i-1])
        tr3 = abs(low[i] - close[i-1])
        tr[i] = max(tr1, max(tr2, tr3))
    
    # Wilder's smoothing (exponential moving average)
    atr = np.zeros(n)
    
    # First ATR is simple average
    if n >= period:
        atr[period-1] = np.mean(tr[:period])
        
        # Subsequent values use Wilder's smoothing
        alpha = 1.0 / period
        for i in range(period, n):
            atr[i] = atr[i-1] * (1 - alpha) + tr[i] * alpha
        
        # Fill early values with first computed ATR
        for i in range(period-1):
            atr[i] = atr[period-1]
    else:
        # Not enough data for full period, use cumulative mean
        for i in range(n):
            atr[i] = np.mean(tr[:i+1])
    
    return atr


@jit(nopython=True, cache=True)
def compute_zone_bands(price_means, pct_merge, last_atr, zone_vol_mult):
    """Compute entry bands for zones using ATR and percentage thresholds.
    
    Args:
        price_means: array of zone mean prices
        pct_merge: percentage merge threshold (fallback)
        last_atr: last ATR value from candles
        zone_vol_mult: multiplier for ATR-based band
    
    Returns:
        Tuple of (band_widths, entry_lows, entry_highs, band_pcts)
    """
    n = len(price_means)
    bands = np.zeros(n)
    entry_lows = np.zeros(n)
    entry_highs = np.zeros(n)
    band_pcts = np.zeros(n)
    
    for i in range(n):
        pm = price_means[i]
        
        # Percent-based padding (fallback)
        pct_pad = max(0.001, pct_merge)
        pad_by_pct = pm * pct_pad
        
        # ATR-based padding (preferred for volatility adjustment)
        pad_by_atr = last_atr * zone_vol_mult
        
        # Take maximum
        pad = max(pad_by_pct, pad_by_atr)
        
        bands[i] = pad
        entry_lows[i] = pm - pad
        entry_highs[i] = pm + pad
        band_pcts[i] = pad / pm if pm > 0 else 0.0
    
    return bands, entry_lows, entry_highs, band_pcts


@jit(nopython=True, cache=True)
def detect_volume_spikes(sizes, threshold_multiplier=2.0, window=20):
    """Detect volume spikes using rolling mean comparison.
    
    Args:
        sizes: array of trade sizes
        threshold_multiplier: multiplier for mean (default 2.0)
        window: rolling window size
    
    Returns:
        Boolean array indicating spike locations
    """
    n = len(sizes)
    spikes = np.zeros(n, dtype=np.bool_)
    
    for i in range(n):
        start_idx = max(0, i - window + 1)
        window_mean = np.mean(sizes[start_idx:i+1])
        
        if sizes[i] > window_mean * threshold_multiplier:
            spikes[i] = True
    
    return spikes


@jit(nopython=True, cache=True)
def compute_price_changes(prices):
    """Fast percentage change calculation for prices.
    
    Args:
        prices: array of prices
    
    Returns:
        Array of absolute percentage changes
    """
    n = len(prices)
    if n < 2:
        return np.zeros(n)
    
    changes = np.zeros(n)
    changes[0] = 0.0
    
    for i in range(1, n):
        if prices[i-1] != 0:
            changes[i] = abs((prices[i] - prices[i-1]) / prices[i-1])
    
    return changes


@jit(nopython=True, cache=True)
def filter_large_trades(sizes, usd_values, threshold):
    """Filter for large trades exceeding threshold.
    
    Args:
        sizes: array of trade sizes
        usd_values: array of USD values
        threshold: minimum size threshold
    
    Returns:
        Boolean array of large trades
    """
    n = len(sizes)
    large = np.zeros(n, dtype=np.bool_)
    
    for i in range(n):
        if sizes[i] >= threshold:
            large[i] = True
    
    return large


@jit(nopython=True, cache=True)
def rolling_mean(arr, window):
    """Fast rolling mean calculation.
    
    Args:
        arr: input array
        window: window size
    
    Returns:
        Array of rolling means
    """
    n = len(arr)
    result = np.zeros(n)
    
    for i in range(n):
        start_idx = max(0, i - window + 1)
        result[i] = np.mean(arr[start_idx:i+1])
    
    return result
