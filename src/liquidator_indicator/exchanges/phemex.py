"""Phemex exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class PhemexParser(BaseExchangeParser):
    """
    Parser for Phemex exchange trade data.
    
    Supports:
    - REST API trades endpoint response
    - WebSocket trade messages
    
    Symbol formats: BTCUSD, ETHUSD
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to Phemex format."""
        symbol = symbol.upper().replace('-', '').replace('_', '').replace('/', '')
        
        if not symbol.endswith('USD'):
            symbol = symbol + 'USD'
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse Phemex REST API trades response.
        
        Phemex trades format:
        {
          "code": 0,
          "msg": "OK",
          "data": {
            "result": {
              "trades": [
                {
                  "timestamp": 1672531200000000000,
                  "side": "Buy",
                  "priceEp": 8000050000000,
                  "qty": 150
                }
              ]
            }
          }
        }
        """
        trades = []
        
        if isinstance(raw_data, dict):
            if 'data' in raw_data and 'result' in raw_data['data']:
                raw_data = raw_data['data']['result'].get('trades', [])
            elif 'result' in raw_data:
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
        """Parse a single Phemex trade."""
        try:
            time = pd.Timestamp(int(raw_trade['timestamp']), unit='ns', tz='UTC')
            # Phemex uses scaled prices (priceEp = price * 10^8)
            price = float(raw_trade.get('priceEp', raw_trade.get('price', 0))) / 1e8
            size = float(raw_trade.get('qty', raw_trade.get('size', 0)))
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
        """Parse Phemex WebSocket trade message."""
        if message.get('type') == 'snapshot' and 'trades' in message:
            trades = message['trades']
            if isinstance(trades, list) and len(trades) > 0:
                return self._parse_single_trade(trades[0])
        return None
