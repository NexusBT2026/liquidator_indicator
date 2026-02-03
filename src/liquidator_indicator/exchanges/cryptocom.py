"""Crypto.com exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class CryptoComParser(BaseExchangeParser):
    """
    Parser for Crypto.com exchange trade data.
    
    Supports:
    - REST API trades endpoint response
    - WebSocket trade messages
    
    Symbol formats: BTC_USDT, ETH_USDT (underscore separator)
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to Crypto.com format."""
        symbol = symbol.upper().replace('-', '_').replace('/', '_')
        
        if '_' not in symbol:
            symbol = symbol + '_USDT'
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse Crypto.com REST API trades response.
        
        Crypto.com trades format:
        {
          "code": 0,
          "method": "public/get-trades",
          "result": {
            "data": [
              {
                "dataTime": 1672531200000,
                "d": "123456",
                "s": "BUY",
                "p": 80000.5,
                "q": 0.150,
                "t": 1672531200000,
                "i": "BTC_USDT"
              }
            ]
          }
        }
        """
        trades = []
        
        if isinstance(raw_data, dict) and 'result' in raw_data:
            raw_data = raw_data['result'].get('data', [])
        
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
        """Parse a single Crypto.com trade."""
        try:
            time = pd.Timestamp(int(raw_trade.get('t', raw_trade.get('dataTime', 0))), unit='ms', tz='UTC')
            price = float(raw_trade['p'])
            size = float(raw_trade['q'])
            side = 'A' if raw_trade['s'] == 'BUY' else 'B'
            
            return {
                'time': time,
                'px': price,
                'sz': size,
                'side': side
            }
        except (KeyError, ValueError, TypeError):
            return None
    
    def parse_websocket_trade(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Crypto.com WebSocket trade message."""
        if message.get('method') == 'subscribe' and 'result' in message:
            result = message['result']
            if 'data' in result and isinstance(result['data'], list) and len(result['data']) > 0:
                return self._parse_single_trade(result['data'][0])
        return None
