"""Exchange-specific parsers for liquidator_indicator."""

from .base import BaseExchangeParser
from .hyperliquid import HyperliquidParser
from .binance import BinanceParser
from .coinbase import CoinbaseParser
from .bybit import BybitParser
from .kraken import KrakenParser
from .okx import OKXParser
from .htx import HTXParser
from .gateio import GateIOParser
from .mexc import MEXCParser
from .bitmex import BitMEXParser
from .deribit import DeribitParser
from .bitfinex import BitfinexParser
from .kucoin import KuCoinParser
from .phemex import PhemexParser
from .bitget import BitgetParser
from .cryptocom import CryptoComParser
from .bingx import BingXParser
from .bitstamp import BitstampParser
from .gemini import GeminiParser
from .poloniex import PoloniexParser

__all__ = [
    'BaseExchangeParser',
    'HyperliquidParser',  # User's primary exchange!
    'BinanceParser',
    'CoinbaseParser',
    'BybitParser',
    'KrakenParser',
    'OKXParser',
    'HTXParser',
    'GateIOParser',
    'MEXCParser',
    'BitMEXParser',
    'DeribitParser',
    'BitfinexParser',
    'KuCoinParser',
    'PhemexParser',
    'BitgetParser',
    'CryptoComParser',
    'BingXParser',
    'BitstampParser',
    'GeminiParser',
    'PoloniexParser',
]
