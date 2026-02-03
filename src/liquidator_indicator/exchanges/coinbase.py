"""Coinbase exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class CoinbaseParser(BaseExchangeParser):
    """
    Parser for Coinbase Advanced Trade (formerly Coinbase Pro) trade data.
    
    Supports:
    - REST API trades endpoint response
    - WebSocket match channel messages
    
    Symbol formats: BTC-USD, ETH-USD, etc.
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol to Coinbase format (dash separator).
        
        Examples:
            'BTC' -> 'BTC-USD'
            'BTCUSD' -> 'BTC-USD'
            'BTC-USD' -> 'BTC-USD'
        """
        symbol = symbol.upper().replace('_', '-').replace('/', '-')
        
        # Add -USD if not present
        if '-' not in symbol:
            # Common pairs
            if symbol.startswith('BTC') and len(symbol) > 3:
                symbol = 'BTC-' + symbol[3:]
            elif symbol.startswith('ETH') and len(symbol) > 3:
                symbol = 'ETH-' + symbol[3:]
            elif symbol.endswith('USD'):
                symbol = symbol[:-3] + '-USD'
            elif symbol.endswith('USDT'):
                symbol = symbol[:-4] + '-USD'
            else:
                symbol = symbol + '-USD'
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse Coinbase REST API trades response.
        
        Coinbase trades format:
        [
          {
            "time": "2014-11-07T22:19:28.578544Z",
            "trade_id": 74,
            "price": "10.00000000",
            "size": "0.01000000",
            "side": "buy"  // taker side
          }
        ]
        
        Args:
            raw_data: List of trade dicts from Coinbase API or DataFrame
        
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
        """Parse a single Coinbase trade."""
        try:
            # REST API format
            if 'time' in raw_trade:
                time = pd.Timestamp(raw_trade['time'], tz='UTC')
                price = float(raw_trade['price'])
                size = float(raw_trade['size'])
                side_str = raw_trade.get('side', 'buy').lower()
                
            # WebSocket match format
            elif 'type' in raw_trade and raw_trade['type'] == 'match':
                time = pd.Timestamp(raw_trade['time'], tz='UTC')
                price = float(raw_trade['price'])
                size = float(raw_trade['size'])
                side_str = raw_trade.get('side', 'buy').lower()
                
            else:
                return None
            
            # Convert side (Coinbase uses taker side)
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
        Parse Coinbase WebSocket match message.
        
        Message format:
        {
          "type": "match",
          "trade_id": 10,
          "sequence": 50,
          "maker_order_id": "ac928c66-ca53-498f-9c13-a110027a60e8",
          "taker_order_id": "132fb6ae-456b-4654-b4e0-d681ac05cea1",
          "time": "2014-11-07T08:19:27.028459Z",
          "product_id": "BTC-USD",
          "size": "5.23512",
          "price": "400.23",
          "side": "sell"  // taker side
        }
        
        Args:
            message: Raw WebSocket message
        
        Returns:
            Single trade in standard format, or None
        """
        if message.get('type') != 'match':
            return None
        
        return self._parse_single_trade(message)
