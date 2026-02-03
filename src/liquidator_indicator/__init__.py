"""Liquidator indicator package - lightweight core API."""
from .core import Liquidator
from .indicators import compute_vwap, compute_atr
from . import exchanges

# ML predictor is optional (requires sklearn)
try:
    from .ml_predictor import ZonePredictor
    __all__ = ["Liquidator", "compute_vwap", "compute_atr", "exchanges", "ZonePredictor"]
except ImportError:
    __all__ = ["Liquidator", "compute_vwap", "compute_atr", "exchanges"]

__version__ = "0.0.7"
