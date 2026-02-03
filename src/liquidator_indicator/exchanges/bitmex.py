"""BitMEX exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class BitMEXParser(BaseExchangeParser):
    """
    Parser for BitMEX exchange trade data.
    
    Supports:
    - REST API trades endpoint response
    - WebSocket trade messages
    
    Symbol formats: XBTUSD, ETHUSD
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to BitMEX format."""
        symbol = symbol.upper().replace('-', '').replace('_', '').replace('/', '')
        
        # BitMEX uses XBT for Bitcoin
        if symbol == 'BTC' or symbol.startswith('BTC'):
            symbol = 'XBT' + symbol[3:] if len(symbol) > 3 else 'XBTUSD'
        elif symbol == 'ETH':
            return 'ETHUSD'
        elif not symbol.endswith('USD'):
            symbol = symbol + 'USD'
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse BitMEX REST API trades response.
        
        BitMEX trades format:
        [
          {
            "timestamp": "2024-01-01T12:00:00.000Z",
            "symbol": "XBTUSD",
            "side": "Buy",
            "size": 1000,
            "price": 80000.5,
            "trdMatchID": "..."
          }
        ]
        """
        trades = []
        
        if isinstance(raw_data, pd.DataFrame):
            for _, row in raw_data.iterrows():
                trade = self._parse_single_trade(row.to_dict())
                if trade:
                    trades.append(trade)
        elif isinstance(raw_data, list):
            for item in raw_data:
                trade = self._parse_single_trade(item)
                if trade:
                    trades.append(trade)
        
        return trades
    
    def _parse_single_trade(self, raw_trade: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single BitMEX trade."""
        try:
            time = pd.Timestamp(raw_trade['timestamp'], tz='UTC')
            price = float(raw_trade['price'])
            # BitMEX size is in contracts, convert to BTC
            size = float(raw_trade['size']) / price
            side = 'A' if raw_trade['side'] == 'Buy' else 'B'
            
            return {
                'time': time,
                'px': price,
                'sz': size,
                'side': side
            }
        except (KeyError, ValueError, TypeError):
            return None
    
    def parse_websocket_trade(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse BitMEX WebSocket trade message."""
        if message.get('table') == 'trade' and 'data' in message:
            data = message['data']
            if isinstance(data, list) and len(data) > 0:
                return self._parse_single_trade(data[0])
        return None
