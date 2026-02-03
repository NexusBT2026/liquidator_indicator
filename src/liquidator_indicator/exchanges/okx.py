"""OKX exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class OKXParser(BaseExchangeParser):
    """
    Parser for OKX exchange trade data.
    
    Supports:
    - REST API trades endpoint response
    - WebSocket trades channel messages
    
    Symbol formats: BTC-USDT, BTC-USDT-SWAP, BTC-USD-SWAP
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol to OKX format.
        
        Examples:
            'BTC' -> 'BTC-USDT-SWAP'
            'BTCUSDT' -> 'BTC-USDT-SWAP'
            'BTC-USDT' -> 'BTC-USDT-SWAP'
        """
        symbol = symbol.upper().replace('_', '-').replace('/', '-')
        
        # Add -USDT-SWAP if not present
        if '-' not in symbol:
            if symbol.endswith('USDT'):
                symbol = symbol[:-4] + '-USDT-SWAP'
            else:
                symbol = symbol + '-USDT-SWAP'
        elif not symbol.endswith('-SWAP') and not symbol.endswith('-FUTURES'):
            symbol = symbol + '-SWAP'
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse OKX REST API trades response.
        
        OKX trades format:
        {
          "code": "0",
          "msg": "",
          "data": [
            {
              "instId": "BTC-USDT-SWAP",
              "tradeId": "123456",
              "px": "80000.5",
              "sz": "10",  // contracts
              "side": "buy",
              "ts": "1672531200000"
            }
          ]
        }
        """
        trades = []
        
        # Handle nested API response
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
        else:
            raise ValueError(f"Unsupported raw_data type: {type(raw_data)}")
        
        return trades
    
    def _parse_single_trade(self, raw_trade: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single OKX trade."""
        try:
            price = float(raw_trade['px'])
            size = float(raw_trade['sz'])
            side_str = raw_trade['side'].lower()
            timestamp = int(raw_trade['ts'])
            
            time = pd.Timestamp(timestamp, unit='ms', tz='UTC')
            side = 'A' if side_str == 'buy' else 'B'
            
            return {
                'time': time,
                'px': price,
                'sz': size,
                'side': side
            }
        except (KeyError, ValueError, TypeError):
            return None
    
    def parse_websocket_trade(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse OKX WebSocket trades message."""
        if message.get('arg', {}).get('channel') != 'trades':
            return None
        
        if 'data' in message and isinstance(message['data'], list) and len(message['data']) > 0:
            return self._parse_single_trade(message['data'][0])
        
        return None
