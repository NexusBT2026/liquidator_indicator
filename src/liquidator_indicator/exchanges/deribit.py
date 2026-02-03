"""Deribit exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class DeribitParser(BaseExchangeParser):
    """
    Parser for Deribit exchange trade data.
    
    Supports:
    - REST API trades endpoint response
    - WebSocket trade messages
    
    Symbol formats: BTC-PERPETUAL, ETH-PERPETUAL
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to Deribit format."""
        symbol = symbol.upper().replace('_', '-').replace('/', '-')
        
        if '-' not in symbol:
            symbol = symbol + '-PERPETUAL'
        elif not (symbol.endswith('-PERPETUAL') or symbol.endswith('-PERP')):
            symbol = symbol + '-PERPETUAL'
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse Deribit REST API trades response.
        
        Deribit trades format:
        {
          "result": {
            "trades": [
              {
                "trade_id": "123456",
                "timestamp": 1672531200000,
                "price": 80000.5,
                "amount": 1000.0,
                "direction": "buy",
                "instrument_name": "BTC-PERPETUAL"
              }
            ]
          }
        }
        """
        trades = []
        
        if isinstance(raw_data, dict) and 'result' in raw_data:
            raw_data = raw_data['result'].get('trades', [])
        
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
        """Parse a single Deribit trade."""
        try:
            time = pd.Timestamp(int(raw_trade['timestamp']), unit='ms', tz='UTC')
            price = float(raw_trade['price'])
            # Deribit amount is in USD, convert to BTC
            size = float(raw_trade['amount']) / price
            side = 'A' if raw_trade['direction'] == 'buy' else 'B'
            
            return {
                'time': time,
                'px': price,
                'sz': size,
                'side': side
            }
        except (KeyError, ValueError, TypeError):
            return None
    
    def parse_websocket_trade(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Deribit WebSocket trade message."""
        if 'params' in message and 'data' in message['params']:
            data = message['params']['data']
            if isinstance(data, list) and len(data) > 0:
                return self._parse_single_trade(data[0])
        return None
