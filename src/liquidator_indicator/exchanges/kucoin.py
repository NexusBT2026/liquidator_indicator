"""KuCoin exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class KuCoinParser(BaseExchangeParser):
    """
    Parser for KuCoin exchange trade data.
    
    Supports:
    - REST API trades endpoint response
    - WebSocket trade messages
    
    Symbol formats: BTC-USDT, ETH-USDT (dash separator)
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to KuCoin format."""
        symbol = symbol.upper().replace('_', '-').replace('/', '-')
        
        if '-' not in symbol:
            symbol = symbol + '-USDT'
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse KuCoin REST API trades response.
        
        KuCoin trades format:
        {
          "code": "200000",
          "data": [
            {
              "sequence": "123456",
              "price": "80000.5",
              "size": "0.150",
              "side": "buy",
              "time": 1672531200000000000
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
        """Parse a single KuCoin trade."""
        try:
            # KuCoin uses nanoseconds
            time = pd.Timestamp(int(raw_trade['time']), unit='ns', tz='UTC')
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
        """Parse KuCoin WebSocket trade message."""
        if message.get('type') == 'message' and message.get('topic', '').startswith('/market/match'):
            data = message.get('data', {})
            if data:
                return self._parse_single_trade(data)
        return None
