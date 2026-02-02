"""Small parser helpers to normalize common liquidation and bbo messages into DataFrame rows."""
from typing import Any, Dict
import pandas as pd
import json
import os
import glob

def parse_liq_msg(msg: Dict[str, Any]) -> Dict:
    """Attempt to extract fields from a liq message dict into canonical form.
    Canonical keys: timestamp, side, coin, price, usd_value, size
    """
    out = {}
    # timestamp variants
    for k in ('timestamp','time','t'):
        if k in msg:
            out['timestamp'] = msg[k]
            break
    # side
    side = msg.get('side') or msg.get('direction') or msg.get('dir')
    if side is not None:
        out['side'] = str(side).lower()
    # price
    for pk in ('price','px','p'):
        if pk in msg:
            out['price'] = msg[pk]
            break
    # usd value
    out['usd_value'] = msg.get('usd_value') or msg.get('value') or msg.get('usd') or msg.get('usdValue') or 0.0
    out['coin'] = msg.get('coin') or msg.get('market') or 'BTC'
    out['size'] = msg.get('size') or msg.get('qty') or msg.get('quantity')
    return out

def parse_bbo_msg(msg: Dict[str, Any]) -> Dict:
    out = {}
    # simple extraction
    out['timestamp'] = msg.get('timestamp') or msg.get('t')
    out['bid'] = msg.get('bid') or msg.get('bidPrice') or None
    out['ask'] = msg.get('ask') or msg.get('askPrice') or None
    return out


def read_liquidations_jsonl(path: str) -> pd.DataFrame:
    """Read a JSONL file of liquidation events and normalize into a DataFrame using `parse_liq_msg`.

    Returns empty DataFrame on error.
    """
    out = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    # some files may contain 'data' wrapper
                    try:
                        obj = json.loads(line.split('\t')[-1])
                    except Exception:
                        continue
                row = parse_liq_msg(obj if isinstance(obj, dict) else obj.get('data', {}))
                out.append(row)
        if not out:
            return pd.DataFrame()
        df = pd.DataFrame(out)
        # normalize timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        return df
    except Exception:
        return pd.DataFrame()


def read_bbo_jsonl(path: str) -> pd.DataFrame:
    """Read BBO JSONL file into DataFrame using `parse_bbo_msg`.

    If path is a directory, will glob for *.jsonl and concat.
    """
    rows = []
    try:
        paths = [path]
        if os.path.isdir(path):
            paths = glob.glob(os.path.join(path, '*.jsonl'))
        for p in paths:
            with open(p, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    rows.append(parse_bbo_msg(obj if isinstance(obj, dict) else obj.get('data', {})))
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        return df
    except Exception:
        return pd.DataFrame()


def tail_last_jsonl(path: str) -> Dict:
    """Read last non-empty JSON line from a file and return parsed dict, or {} on error.

    This implementation reads the file in text mode and returns the last non-empty line parsed as JSON.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        if not lines:
            return {}
        last = lines[-1]
        return json.loads(last)
    except Exception:
        return {}
