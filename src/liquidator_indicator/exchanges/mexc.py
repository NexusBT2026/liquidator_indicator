"""MEXC exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class MEXCParser(BaseExchangeParser):
    """
    Parser for MEXC exchange trade data.
    
    Supports:
    - REST API trades endpoint response
    - WebSocket trade messages
    
    Symbol formats: BTCUSDT, ETHUSDT (no separator)
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to MEXC format (uppercase, no separator)."""
        symbol = symbol.upper().replace('-', '').replace('_', '').replace('/', '')
        if not symbol.endswith('USDT'):
            symbol = symbol + 'USDT'
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse MEXC REST API trades response.
        
        MEXC trades format:
        [
          {
            "id": 123456,
            "price": "80000.5",
            "qty": "0.150",
            "time": 1672531200000,
            "isBuyerMaker": false
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
        """Parse a single MEXC trade."""
        try:
            time = pd.Timestamp(int(raw_trade['time']), unit='ms', tz='UTC')
            price = float(raw_trade['price'])
            size = float(raw_trade['qty'])
            side = 'B' if raw_trade['isBuyerMaker'] else 'A'
            
            return {
                'time': time,
                'px': price,
                'sz': size,
                'side': side
            }
        except (KeyError, ValueError, TypeError):
            return None
    
    def parse_websocket_trade(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse MEXC WebSocket trade message."""
        if 'd' in message and 'deals' in message['d']:
            deals = message['d']['deals']
            if isinstance(deals, list) and len(deals) > 0:
                return self._parse_single_trade(deals[0])
        return None
