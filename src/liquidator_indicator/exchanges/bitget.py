"""Bitget exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class BitgetParser(BaseExchangeParser):
    """
    Parser for Bitget exchange trade data.
    
    Supports:
    - REST API trades endpoint response
    - WebSocket trade messages
    
    Symbol formats: BTCUSDT, ETHUSDT
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to Bitget format."""
        symbol = symbol.upper().replace('-', '').replace('_', '').replace('/', '')
        
        if not symbol.endswith('USDT'):
            symbol = symbol + 'USDT'
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse Bitget REST API trades response.
        
        Bitget trades format:
        {
          "code": "00000",
          "msg": "success",
          "data": [
            {
              "symbol": "BTCUSDT",
              "tradeId": "123456",
              "side": "buy",
              "size": "0.150",
              "price": "80000.5",
              "ts": "1672531200000"
            }
          ]
        }
        """
        trades = []
        
        if isinstance(raw_data, dict) and 'data' in raw_data:
            raw_data = raw_data['data']
        
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
        """Parse a single Bitget trade."""
        try:
            time = pd.Timestamp(int(raw_trade['ts']), unit='ms', tz='UTC')
            price = float(raw_trade['price'])
            size = float(raw_trade['size'])
            side = 'A' if raw_trade['side'] == 'buy' else 'B'
            
            return {
                'time': time,
                'px': price,
                'sz': size,
                'side': side
            }
        except (KeyError, ValueError, TypeError):
            return None
    
    def parse_websocket_trade(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Bitget WebSocket trade message."""
        if message.get('action') == 'snapshot' and 'data' in message:
            data = message['data']
            if isinstance(data, list) and len(data) > 0:
                return self._parse_single_trade(data[0])
        return None
