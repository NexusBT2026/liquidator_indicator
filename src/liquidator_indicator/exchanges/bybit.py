"""Bybit exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class BybitParser(BaseExchangeParser):
    """
    Parser for Bybit derivatives trade data.
    
    Supports:
    - REST API public trading records endpoint
    - WebSocket trade stream messages
    
    Symbol formats: BTCUSDT, ETHUSDT (perpetual contracts)
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol to Bybit format.
        
        Examples:
            'BTC' -> 'BTCUSDT'
            'BTC-USD' -> 'BTCUSDT'
            'BTCUSDT' -> 'BTCUSDT'
        """
        symbol = symbol.replace('-', '').replace('_', '').replace('/', '').upper()
        
        # Add USDT if not present
        if not any(symbol.endswith(quote) for quote in ['USDT', 'PERP']):
            # Convert USD to USDT
            if symbol.endswith('USD'):
                symbol = symbol[:-3] + 'USDT'
            elif len(symbol) <= 4:  # Just the coin symbol like 'BTC'
                symbol = symbol + 'USDT'
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse Bybit REST API trade response.
        
        Bybit trades format (v5 API):
        {
          "result": {
            "list": [
              {
                "execId": "2100000000007764263",
                "symbol": "BTCUSDT",
                "price": "16618.49",
                "size": "0.001",
                "side": "Buy",  // Taker side
                "time": "1672052955758",
                "isBlockTrade": false
              }
            ]
          }
        }
        
        Args:
            raw_data: Response dict from Bybit API, list, or DataFrame
        
        Returns:
            List of trades in standard format
        """
        trades = []
        
        # Handle nested API response
        if isinstance(raw_data, dict) and 'result' in raw_data:
            if 'list' in raw_data['result']:
                raw_data = raw_data['result']['list']
            else:
                raw_data = raw_data['result']
        
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
        """Parse a single Bybit trade."""
        try:
            # REST API format (v5)
            if 'execId' in raw_trade:
                timestamp = int(raw_trade['time'])  # milliseconds
                price = float(raw_trade['price'])
                size = float(raw_trade['size'])
                side_str = raw_trade['side'].lower()
                
            # WebSocket format
            elif 'i' in raw_trade:  # trade ID
                timestamp = int(raw_trade['T'])  # milliseconds
                price = float(raw_trade['p'])
                size = float(raw_trade['v'])
                side_str = raw_trade['S'].lower()
                
            # Legacy format
            elif 'price' in raw_trade:
                timestamp = raw_trade.get('time', raw_trade.get('timestamp', raw_trade.get('trade_time_ms')))
                price = float(raw_trade['price'])
                size_val = raw_trade.get('size')
                if size_val is None:
                    size_val = raw_trade.get('qty')
                if size_val is None:
                    size_val = raw_trade.get('volume')
                if size_val is None:
                    return None  # or raise ValueError("Trade size not found")
                size = float(size_val)
                side_str = raw_trade.get('side', 'buy').lower()
                
            else:
                return None
            
            # Convert timestamp
            if timestamp is None:
                return None
            if isinstance(timestamp, str):
                time = pd.Timestamp(timestamp, tz='UTC')
            else:
                # Bybit uses milliseconds
                time = pd.Timestamp(timestamp, unit='ms', tz='UTC')
            
            # Convert side
            # 'buy' = taker bought (aggressor buy) = 'A'
            # 'sell' = taker sold (aggressor sell) = 'B'
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
        """
        Parse Bybit WebSocket trade message.
        
        Message format (v5):
        {
          "topic": "publicTrade.BTCUSDT",
          "type": "snapshot",
          "ts": 1672304486868,
          "data": [
            {
              "T": 1672304486865,
              "s": "BTCUSDT",
              "S": "Buy",
              "v": "0.001",
              "p": "16578.50",
              "L": "PlusTick",
              "i": "20f43950-d8dd-5b31-9112-a178eb6023af",
              "BT": false
            }
          ]
        }
        
        Args:
            message: Raw WebSocket message
        
        Returns:
            Single trade in standard format, or None
        """
        if 'topic' not in message or not message['topic'].startswith('publicTrade'):
            return None
        
        # v5 API wraps trade in data array
        if 'data' in message and isinstance(message['data'], list) and len(message['data']) > 0:
            return self._parse_single_trade(message['data'][0])
        
        return None
