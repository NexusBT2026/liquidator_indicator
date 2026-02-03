"""Hyperliquid exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class HyperliquidParser(BaseExchangeParser):
    """
    Parser for Hyperliquid exchange trade data.
    
    Supports:
    - REST API trades endpoint response
    - WebSocket trade stream messages
    - Public trade data format
    
    Symbol formats: BTC, ETH (no suffix needed)
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol to Hyperliquid format (simple coin name).
        
        Examples:
            'BTC' -> 'BTC'
            'BTC-USD' -> 'BTC'
            'BTCUSDT' -> 'BTC'
            'ETH' -> 'ETH'
        """
        symbol = symbol.upper().replace('-', '').replace('_', '').replace('/', '')
        
        # Remove common suffixes
        for suffix in ['USDT', 'USD', 'PERP', 'PERPETUAL']:
            if symbol.endswith(suffix):
                symbol = symbol[:-len(suffix)]
                break
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse Hyperliquid REST API or WebSocket trade data.
        
        Hyperliquid trades format:
        [
          {
            "coin": "BTC",
            "side": "A",  // A=buy aggressor, B=sell aggressor
            "px": "83991.0",
            "sz": "0.09374",
            "time": 1769824534507,  // milliseconds
            "hash": "0x..."  // optional
          }
        ]
        
        Args:
            raw_data: List of trade dicts from Hyperliquid or DataFrame
        
        Returns:
            List of trades in standard format
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
        else:
            raise ValueError(f"Unsupported raw_data type: {type(raw_data)}")
        
        return trades
    
    def _parse_single_trade(self, raw_trade: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single Hyperliquid trade."""
        try:
            # Standard Hyperliquid format (already matches our format!)
            if 'px' in raw_trade and 'sz' in raw_trade:
                price = float(raw_trade['px'])
                size = float(raw_trade['sz'])
                side = raw_trade['side'].upper()
                
                # Time can be in different fields
                timestamp = raw_trade.get('time', raw_trade.get('timestamp', raw_trade.get('ts')))
                
            # Alternative format with full field names
            elif 'price' in raw_trade:
                price = float(raw_trade['price'])
                size_val = raw_trade.get('size')
                if size_val is None:
                    size_val = raw_trade.get('quantity')
                if size_val is None:
                    size_val = raw_trade.get('qty')
                if size_val is None:
                    return None
                size = float(size_val)
                side_str = raw_trade.get('side', 'A').upper()
                
                # Convert side if needed
                if side_str in ['BUY', 'LONG']:
                    side = 'A'
                elif side_str in ['SELL', 'SHORT']:
                    side = 'B'
                else:
                    side = side_str
                
                timestamp = raw_trade.get('time', raw_trade.get('timestamp', raw_trade.get('ts')))
                
            else:
                return None
            
            # Convert timestamp
            if isinstance(timestamp, str):
                time = pd.Timestamp(timestamp, tz='UTC')
            elif isinstance(timestamp, (int, float)):
                # Hyperliquid uses milliseconds
                if timestamp > 1e12:
                    time = pd.Timestamp(timestamp, unit='ms', tz='UTC')
                else:
                    time = pd.Timestamp(timestamp, unit='s', tz='UTC')
            else:
                time = pd.Timestamp.now(tz='UTC')
            
            # Validate side
            if side not in ('A', 'B'):
                side = 'A'
            
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
        Parse Hyperliquid WebSocket trade message.
        
        Message format (trades channel):
        {
          "channel": "trades",
          "data": [
            {
              "coin": "BTC",
              "side": "A",
              "px": "83991.0",
              "sz": "0.09374",
              "time": 1769824534507
            }
          ]
        }
        
        Args:
            message: Raw WebSocket message
        
        Returns:
            Single trade in standard format, or None
        """
        # Check if it's a trades message
        if isinstance(message, dict):
            if message.get('channel') == 'trades' and 'data' in message:
                data = message['data']
                if isinstance(data, list) and len(data) > 0:
                    return self._parse_single_trade(data[0])
            elif 'coin' in message and 'px' in message:
                # Direct trade object
                return self._parse_single_trade(message)
        
        return None
