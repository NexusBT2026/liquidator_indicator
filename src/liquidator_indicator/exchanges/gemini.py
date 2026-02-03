"""Gemini exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class GeminiParser(BaseExchangeParser):
    """
    Parser for Gemini exchange trade data.
    
    Supports:
    - REST API trades endpoint response
    - WebSocket trade messages
    
    Symbol formats: btcusd, ethusd (lowercase, no separator)
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to Gemini format."""
        symbol = symbol.lower().replace('-', '').replace('_', '').replace('/', '')
        
        if not symbol.endswith('usd'):
            symbol = symbol + 'usd'
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse Gemini REST API trades response.
        
        Gemini trades format:
        [
          {
            "timestamp": 1672531200000,
            "timestampms": 1672531200123,
            "tid": 123456,
            "price": "80000.50",
            "amount": "0.150",
            "type": "buy"
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
        """Parse a single Gemini trade."""
        try:
            timestamp = int(raw_trade['timestampms'])
            time = pd.Timestamp(timestamp, unit='ms', tz='UTC')
            price = float(raw_trade['price'])
            size = float(raw_trade['amount'])
            side = 'A' if raw_trade['type'] == 'buy' else 'B'
            
            return {
                'time': time,
                'px': price,
                'sz': size,
                'side': side
            }
        except (KeyError, ValueError, TypeError):
            return None
    
    def parse_websocket_trade(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Gemini WebSocket trade message."""
        if message.get('type') == 'trade' and 'events' in message:
            events = message['events']
            if isinstance(events, list) and len(events) > 0:
                event = events[0]
                return self._parse_single_trade(event)
        return None
