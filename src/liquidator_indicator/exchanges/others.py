"""Additional exchange parsers (HTX, Gate.io, MEXC, BitMEX, Deribit, Bitfinex, KuCoin)."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class HTXParser(BaseExchangeParser):
    """Parser for HTX (Huobi) exchange."""
    
    def normalize_symbol(self, symbol: str) -> str:
        symbol = symbol.lower().replace('-', '').replace('_', '')
        if not symbol.endswith('usdt'):
            symbol = symbol + 'usdt'
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        trades = []
        if isinstance(raw_data, dict) and 'data' in raw_data:
            raw_data = raw_data['data']
        
        if isinstance(raw_data, list):
            for item in raw_data:
                try:
                    trade = {
                        'time': pd.Timestamp(item['ts'], unit='ms', tz='UTC'),
                        'px': float(item['price']),
                        'sz': float(item['amount']),
                        'side': 'A' if item['direction'] == 'buy' else 'B'
                    }
                    trades.append(trade)
                except (KeyError, ValueError, TypeError):
                    continue
        return trades


class GateIOParser(BaseExchangeParser):
    """Parser for Gate.io exchange."""
    
    def normalize_symbol(self, symbol: str) -> str:
        symbol = symbol.upper().replace('-', '_').replace('/', '_')
        if '_' not in symbol:
            symbol = symbol + '_USDT'
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        trades = []
        if isinstance(raw_data, list):
            for item in raw_data:
                try:
                    trade = {
                        'time': pd.Timestamp(int(item['create_time']), unit='s', tz='UTC'),
                        'px': float(item['price']),
                        'sz': float(item['amount']),
                        'side': 'A' if item['side'] == 'buy' else 'B'
                    }
                    trades.append(trade)
                except (KeyError, ValueError, TypeError):
                    continue
        return trades


class MEXCParser(BaseExchangeParser):
    """Parser for MEXC exchange."""
    
    def normalize_symbol(self, symbol: str) -> str:
        symbol = symbol.upper().replace('-', '').replace('_', '')
        if not symbol.endswith('USDT'):
            symbol = symbol + 'USDT'
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        trades = []
        if isinstance(raw_data, list):
            for item in raw_data:
                try:
                    trade = {
                        'time': pd.Timestamp(int(item['time']), unit='ms', tz='UTC'),
                        'px': float(item['price']),
                        'sz': float(item['qty']),
                        'side': 'B' if item['isBuyerMaker'] else 'A'
                    }
                    trades.append(trade)
                except (KeyError, ValueError, TypeError):
                    continue
        return trades


class BitMEXParser(BaseExchangeParser):
    """Parser for BitMEX exchange."""
    
    def normalize_symbol(self, symbol: str) -> str:
        symbol = symbol.upper().replace('-', '').replace('_', '')
        if symbol == 'BTC':
            return 'XBTUSD'
        elif symbol == 'ETH':
            return 'ETHUSD'
        return symbol + 'USD'
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        trades = []
        if isinstance(raw_data, list):
            for item in raw_data:
                try:
                    trade = {
                        'time': pd.Timestamp(item['timestamp'], tz='UTC'),
                        'px': float(item['price']),
                        'sz': float(item['size']) / float(item['price']),  # Convert contracts to BTC
                        'side': 'A' if item['side'] == 'Buy' else 'B'
                    }
                    trades.append(trade)
                except (KeyError, ValueError, TypeError):
                    continue
        return trades


class DeribitParser(BaseExchangeParser):
    """Parser for Deribit exchange."""
    
    def normalize_symbol(self, symbol: str) -> str:
        symbol = symbol.upper().replace('-', '_').replace('/', '_')
        if '_' not in symbol:
            symbol = symbol + '-PERPETUAL'
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        trades = []
        if isinstance(raw_data, dict) and 'result' in raw_data:
            raw_data = raw_data['result'].get('trades', [])
        
        if isinstance(raw_data, list):
            for item in raw_data:
                try:
                    trade = {
                        'time': pd.Timestamp(item['timestamp'], unit='ms', tz='UTC'),
                        'px': float(item['price']),
                        'sz': float(item['amount']) / float(item['price']),  # Convert USD to BTC
                        'side': 'A' if item['direction'] == 'buy' else 'B'
                    }
                    trades.append(trade)
                except (KeyError, ValueError, TypeError):
                    continue
        return trades


class BitfinexParser(BaseExchangeParser):
    """Parser for Bitfinex exchange."""
    
    def normalize_symbol(self, symbol: str) -> str:
        symbol = symbol.upper().replace('-', '').replace('_', '')
        if not symbol.startswith('t'):
            symbol = 't' + symbol
        if not symbol.endswith('USD'):
            symbol = symbol + 'USD'
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        trades = []
        if isinstance(raw_data, list):
            for item in raw_data:
                try:
                    # Bitfinex array format: [ID, MTS, AMOUNT, PRICE]
                    if isinstance(item, list) and len(item) >= 4:
                        trade = {
                            'time': pd.Timestamp(int(item[1]), unit='ms', tz='UTC'),
                            'px': float(item[3]),
                            'sz': abs(float(item[2])),
                            'side': 'A' if float(item[2]) > 0 else 'B'
                        }
                        trades.append(trade)
                except (ValueError, TypeError, IndexError):
                    continue
        return trades


class KuCoinParser(BaseExchangeParser):
    """Parser for KuCoin exchange."""
    
    def normalize_symbol(self, symbol: str) -> str:
        symbol = symbol.upper().replace('_', '-').replace('/', '-')
        if '-' not in symbol:
            symbol = symbol + '-USDT'
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        trades = []
        if isinstance(raw_data, dict) and 'data' in raw_data:
            raw_data = raw_data['data']
        
        if isinstance(raw_data, list):
            for item in raw_data:
                try:
                    trade = {
                        'time': pd.Timestamp(int(item['time']), unit='ns', tz='UTC'),
                        'px': float(item['price']),
                        'sz': float(item['size']),
                        'side': 'A' if item['side'] == 'buy' else 'B'
                    }
                    trades.append(trade)
                except (KeyError, ValueError, TypeError):
                    continue
        return trades


class PhemexParser(BaseExchangeParser):
    """Parser for Phemex exchange."""
    
    def normalize_symbol(self, symbol: str) -> str:
        symbol = symbol.upper().replace('-', '').replace('_', '')
        if not symbol.endswith('USD'):
            symbol = symbol + 'USD'
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        trades = []
        if isinstance(raw_data, dict) and 'result' in raw_data:
            raw_data = raw_data['result'].get('trades', [])
        
        if isinstance(raw_data, list):
            for item in raw_data:
                try:
                    trade = {
                        'time': pd.Timestamp(int(item['timestamp']), unit='ns', tz='UTC'),
                        'px': float(item['price']),
                        'sz': float(item['size']),
                        'side': 'A' if item['side'] == 'Buy' else 'B'
                    }
                    trades.append(trade)
                except (KeyError, ValueError, TypeError):
                    continue
        return trades


class BitgetParser(BaseExchangeParser):
    """Parser for Bitget exchange."""
    
    def normalize_symbol(self, symbol: str) -> str:
        symbol = symbol.upper().replace('-', '').replace('_', '')
        if not symbol.endswith('USDT'):
            symbol = symbol + 'USDT'
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        trades = []
        if isinstance(raw_data, dict) and 'data' in raw_data:
            raw_data = raw_data['data']
        
        if isinstance(raw_data, list):
            for item in raw_data:
                try:
                    trade = {
                        'time': pd.Timestamp(int(item['ts']), unit='ms', tz='UTC'),
                        'px': float(item['price']),
                        'sz': float(item['size']),
                        'side': 'A' if item['side'] == 'buy' else 'B'
                    }
                    trades.append(trade)
                except (KeyError, ValueError, TypeError):
                    continue
        return trades


class CryptoComParser(BaseExchangeParser):
    """Parser for Crypto.com exchange."""
    
    def normalize_symbol(self, symbol: str) -> str:
        symbol = symbol.upper().replace('-', '_').replace('/', '_')
        if '_' not in symbol:
            symbol = symbol + '_USDT'
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        trades = []
        if isinstance(raw_data, dict) and 'result' in raw_data:
            raw_data = raw_data['result'].get('data', [])
        
        if isinstance(raw_data, list):
            for item in raw_data:
                try:
                    trade = {
                        'time': pd.Timestamp(int(item['t']), unit='ms', tz='UTC'),
                        'px': float(item['p']),
                        'sz': float(item['q']),
                        'side': 'A' if item['s'] == 'BUY' else 'B'
                    }
                    trades.append(trade)
                except (KeyError, ValueError, TypeError):
                    continue
        return trades


class BingXParser(BaseExchangeParser):
    """Parser for BingX exchange."""
    
    def normalize_symbol(self, symbol: str) -> str:
        symbol = symbol.upper().replace('_', '-').replace('/', '-')
        if '-' not in symbol:
            symbol = symbol + '-USDT'
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        trades = []
        if isinstance(raw_data, dict) and 'data' in raw_data:
            raw_data = raw_data['data']
        
        if isinstance(raw_data, list):
            for item in raw_data:
                try:
                    trade = {
                        'time': pd.Timestamp(int(item['time']), unit='ms', tz='UTC'),
                        'px': float(item['price']),
                        'sz': float(item['qty']),
                        'side': 'B' if item['isBuyerMaker'] else 'A'
                    }
                    trades.append(trade)
                except (KeyError, ValueError, TypeError):
                    continue
        return trades


class BitstampParser(BaseExchangeParser):
    """Parser for Bitstamp exchange."""
    
    def normalize_symbol(self, symbol: str) -> str:
        symbol = symbol.lower().replace('-', '').replace('_', '')
        if not symbol.endswith('usd'):
            symbol = symbol + 'usd'
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        trades = []
        if isinstance(raw_data, list):
            for item in raw_data:
                try:
                    trade = {
                        'time': pd.Timestamp(int(item['timestamp']), unit='s', tz='UTC'),
                        'px': float(item['price']),
                        'sz': float(item['amount']),
                        'side': 'A' if item['type'] == '0' else 'B'
                    }
                    trades.append(trade)
                except (KeyError, ValueError, TypeError):
                    continue
        return trades


class GeminiParser(BaseExchangeParser):
    """Parser for Gemini exchange."""
    
    def normalize_symbol(self, symbol: str) -> str:
        symbol = symbol.lower().replace('-', '').replace('_', '')
        if not symbol.endswith('usd'):
            symbol = symbol + 'usd'
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        trades = []
        if isinstance(raw_data, list):
            for item in raw_data:
                try:
                    trade = {
                        'time': pd.Timestamp(int(item['timestampms']), unit='ms', tz='UTC'),
                        'px': float(item['price']),
                        'sz': float(item['amount']),
                        'side': 'A' if item['type'] == 'buy' else 'B'
                    }
                    trades.append(trade)
                except (KeyError, ValueError, TypeError):
                    continue
        return trades


class PoloniexParser(BaseExchangeParser):
    """Parser for Poloniex exchange."""
    
    def normalize_symbol(self, symbol: str) -> str:
        symbol = symbol.upper().replace('-', '_').replace('/', '_')
        if '_' not in symbol:
            symbol = 'USDT_' + symbol
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        trades = []
        if isinstance(raw_data, list):
            for item in raw_data:
                try:
                    trade = {
                        'time': pd.Timestamp(item['date'], tz='UTC'),
                        'px': float(item['rate']),
                        'sz': float(item['amount']),
                        'side': 'A' if item['type'] == 'buy' else 'B'
                    }
                    trades.append(trade)
                except (KeyError, ValueError, TypeError):
                    continue
        return trades

