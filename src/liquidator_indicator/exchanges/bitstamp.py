"""Bitstamp exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class BitstampParser(BaseExchangeParser):
    """
    Parser for Bitstamp exchange trade data.
    
    Supports:
    - REST API trades endpoint response
    - WebSocket trade messages
    
    Symbol formats: btcusd, ethusd (lowercase, no separator)
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to Bitstamp format."""
        symbol = symbol.lower().replace('-', '').replace('_', '').replace('/', '')
        
        if not symbol.endswith('usd'):
            symbol = symbol + 'usd'
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse Bitstamp REST API trades response.
        
        Bitstamp trades format:
        [
          {
            "date": "1672531200",
            "tid": "123456",
            "price": "80000.50",
            "type": "0",
            "amount": "0.15000000"
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
        """Parse a single Bitstamp trade."""
        try:
            timestamp = int(raw_trade.get('timestamp', raw_trade.get('date', 0)))
            time = pd.Timestamp(timestamp, unit='s', tz='UTC')
            price = float(raw_trade['price'])
            size = float(raw_trade['amount'])
            # Bitstamp: type "0" = buy, "1" = sell
            side = 'A' if raw_trade['type'] == '0' else 'B'
            
            return {
                'time': time,
                'px': price,
                'sz': size,
                'side': side
            }
        except (KeyError, ValueError, TypeError):
            return None
    
    def parse_websocket_trade(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Bitstamp WebSocket trade message."""
        if message.get('event') == 'trade' and 'data' in message:
            return self._parse_single_trade(message['data'])
        return None
