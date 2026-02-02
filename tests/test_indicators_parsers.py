import json
import tempfile
import os
import pandas as pd

from liquidator_indicator import compute_vwap, compute_atr
from liquidator_indicator.parsers import read_liquidations_jsonl, read_bbo_jsonl, tail_last_jsonl


def test_compute_vwap_cumulative():
    df = pd.DataFrame({
        'close': [10, 12, 11],
        'volume': [100, 200, 100]
    })
    vwap = compute_vwap(df)
    assert len(vwap) == 3
    # cumulative VWAP after first = 10, after second = (10*100 + 12*200)/300 = 11.333...
    assert abs(vwap.iloc[0] - 10.0) < 1e-6
    assert abs(vwap.iloc[1] - ((10*100 + 12*200) / 300)) < 1e-6


def test_compute_vwap_rolling():
    df = pd.DataFrame({
        'close': [10, 12, 11, 13],
        'volume': [100, 200, 100, 100]
    })
    vwap = compute_vwap(df, period=2)
    assert len(vwap) == 4
    # last two bars vwap = (11*100 + 13*100)/200 = 12
    assert abs(vwap.iloc[-1] - 12.0) < 1e-6


def test_compute_atr_basic():
    df = pd.DataFrame({
        'high': [12, 13, 14, 15],
        'low': [9, 10, 11, 12],
        'close': [11, 12, 13, 14]
    })
    atr = compute_atr(df, per=3)
    assert len(atr) == 4
    assert (atr > 0).any()


def test_read_liquidations_jsonl_and_tail_last():
    lines = [
        {'timestamp': '2026-01-31T12:00:00Z', 'side': 'long', 'price': 80000, 'usd_value': 500000},
        {'timestamp': '2026-01-31T12:01:00Z', 'side': 'short', 'price': 79000, 'usd_value': 200000}
    ]
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as tf:
        path = tf.name
        for l in lines:
            tf.write(json.dumps(l) + "\n")
    try:
        df = read_liquidations_jsonl(path)
        assert not df.empty
        assert 'price' in df.columns
        last = tail_last_jsonl(path)
        assert isinstance(last, dict)
        assert last.get('price') == 79000
    finally:
        os.remove(path)


def test_read_bbo_jsonl():
    msgs = [
        {'timestamp': '2026-01-31T12:00:00Z', 'bid': 79900, 'ask': 80100},
        {'timestamp': '2026-01-31T12:01:00Z', 'bid': 79800, 'ask': 80200}
    ]
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as tf:
        path = tf.name
        for m in msgs:
            tf.write(json.dumps(m) + "\n")
    try:
        df = read_bbo_jsonl(path)
        assert not df.empty
        assert 'bid' in df.columns and 'ask' in df.columns
    finally:
        os.remove(path)
