"""
Data stream collectors for liquidator_indicator package.

These are OPTIONAL utilities that help users collect public data feeds.
Users can either:
1. Use these collectors to automate data gathering
2. Implement their own collectors
3. Feed data from existing sources (files, APIs, etc.)

The indicator package itself is data-source agnostic.
"""

from .funding import FundingRateCollector
from .liquidations import (
    BinanceLiquidationCollector,
    BybitLiquidationCollector,
    OKXLiquidationCollector,
    BitMEXLiquidationCollector,
    DeribitLiquidationCollector,
    HTXLiquidationCollector,
    PhemexLiquidationCollector,
    MEXCLiquidationCollector,
    MultiExchangeLiquidationCollector
)

__all__ = [
    'FundingRateCollector',
    'BinanceLiquidationCollector',
    'BybitLiquidationCollector',
    'OKXLiquidationCollector',
    'BitMEXLiquidationCollector',
    'DeribitLiquidationCollector',
    'HTXLiquidationCollector',
    'PhemexLiquidationCollector',
    'MEXCLiquidationCollector',
    'MultiExchangeLiquidationCollector'
]
