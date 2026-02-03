"""Gate.io exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class GateIOParser(BaseExchangeParser):
    """
    Parser for Gate.io exchange trade data.
    
    Supports:
    - REST API trades endpoint response
    - WebSocket trade messages
    
    Symbol formats: BTC_USDT, ETH_USDT (underscore separator)
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to Gate.io format (uppercase with underscore)."""
        symbol = symbol.upper().replace('-', '_').replace('/', '_')
        if '_' not in symbol:
            symbol = symbol + '_USDT'
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse Gate.io REST API trades response.
        
        Gate.io trades format:
        [
          {
            "id": "123456",
            "create_time": "1672531200",
            "create_time_ms": "1672531200000",
            "side": "buy",
            "currency_pair": "BTC_USDT",
            "amount": "0.150",
            "price": "80000.5"
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
        """Parse a single Gate.io trade."""
        try:
            timestamp = int(raw_trade.get('create_time_ms', raw_trade.get('create_time', 0)))
            if timestamp < 1e12:  # seconds
                timestamp = timestamp * 1000
            
            time = pd.Timestamp(timestamp, unit='ms', tz='UTC')
            price = float(raw_trade['price'])
            size = float(raw_trade['amount'])
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
        """Parse Gate.io WebSocket trade message."""
        if message.get('channel') == 'spot.trades' and 'result' in message:
            result = message['result']
            if isinstance(result, list) and len(result) > 0:
                return self._parse_single_trade(result[0])
        return None
