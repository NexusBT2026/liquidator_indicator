"""Binance exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class BinanceParser(BaseExchangeParser):
    """
    Parser for Binance spot and futures trade data.
    
    Supports:
    - REST API aggTrades endpoint response
    - WebSocket aggTrade stream messages
    - CSV exports from Binance
    
    Symbol formats: BTCUSDT, ETHUSDT, etc.
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol to Binance format (no separator).
        
        Examples:
            'BTC' -> 'BTCUSDT'
            'BTC-USD' -> 'BTCUSDT'
            'BTCUSDT' -> 'BTCUSDT'
        """
        # Remove separators
        symbol = symbol.replace('-', '').replace('_', '').replace('/', '').upper()
        
        # Add USDT if not present
        if not any(symbol.endswith(quote) for quote in ['USDT', 'BUSD']):
            # Convert USD to USDT
            if symbol.endswith('USD') and not symbol.endswith('USDT'):
                symbol = symbol[:-3] + 'USDT'
            elif len(symbol) <= 4:  # Just the coin symbol like 'BTC'
                symbol = symbol + 'USDT'
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse Binance REST API aggTrades response.
        
        Binance aggTrades format:
        [
          {
            "a": 26129,         // Aggregate trade ID
            "p": "0.01633102",  // Price
            "q": "4.70443515",  // Quantity
            "f": 27781,         // First trade ID
            "l": 27781,         // Last trade ID
            "T": 1498793709153, // Timestamp
            "m": true,          // Was the buyer the maker?
            "M": true           // Was the trade the best price match?
          }
        ]
        
        Args:
            raw_data: List of trade dicts from Binance API or DataFrame
        
        Returns:
            List of trades in standard format
        """
        trades = []
        
        # Handle DataFrame input
        if isinstance(raw_data, pd.DataFrame):
            for _, row in raw_data.iterrows():
                trade = self._parse_single_trade(row.to_dict())
                if trade:
                    trades.append(trade)
        # Handle list input
        elif isinstance(raw_data, list):
            for item in raw_data:
                trade = self._parse_single_trade(item)
                if trade:
                    trades.append(trade)
        else:
            raise ValueError(f"Unsupported raw_data type: {type(raw_data)}")
        
        return trades
    
    def _parse_single_trade(self, raw_trade: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single Binance trade."""
        try:
            # Binance REST API format
            if 'a' in raw_trade:
                timestamp = raw_trade['T']  # milliseconds
                price = float(raw_trade['p'])
                size = float(raw_trade['q'])
                is_buyer_maker = raw_trade['m']
                
            # WebSocket format (slightly different)
            elif 'E' in raw_trade:
                timestamp = raw_trade['T']
                price = float(raw_trade['p'])
                size = float(raw_trade['q'])
                is_buyer_maker = raw_trade['m']
                
            # CSV or simplified format
            elif 'price' in raw_trade:
                timestamp = raw_trade.get('time', raw_trade.get('timestamp'))
                price = float(raw_trade['price'])
                size_val = raw_trade.get('qty', raw_trade.get('quantity', raw_trade.get('size')))
                if size_val is None:
                    return None
                size = float(size_val)
                is_buyer_maker = raw_trade.get('isBuyerMaker', raw_trade.get('m', False))
                
            else:
                return None
            
            # Convert timestamp to pandas Timestamp
            if timestamp is None:
                return None
            if isinstance(timestamp, (int, float)):
                # Assume milliseconds if > 1e12
                if timestamp > 1e12:
                    time = pd.Timestamp(timestamp, unit='ms', tz='UTC')
                else:
                    time = pd.Timestamp(timestamp, unit='s', tz='UTC')
            else:
                time = pd.Timestamp(timestamp, tz='UTC')
            
            # Determine side (A=aggressor buy, B=aggressor sell)
            # In Binance: m=true means buyer was maker (so aggressor was seller)
            side = 'B' if is_buyer_maker else 'A'
            
            return {
                'time': time,
                'px': price,
                'sz': size,
                'side': side
            }
            
        except (KeyError, ValueError, TypeError) as e:
            # Skip malformed trades
            return None
    
    def parse_websocket_trade(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse Binance WebSocket aggTrade message.
        
        Message format:
        {
          "e": "aggTrade",  // Event type
          "E": 123456789,   // Event time
          "s": "BTCUSDT",   // Symbol
          "a": 12345,       // Aggregate trade ID
          "p": "0.001",     // Price
          "q": "100",       // Quantity
          "f": 100,         // First trade ID
          "l": 105,         // Last trade ID
          "T": 123456785,   // Trade time
          "m": true,        // Is the buyer the maker?
          "M": true         // Ignore
        }
        
        Args:
            message: Raw WebSocket message
        
        Returns:
            Single trade in standard format, or None
        """
        if message.get('e') != 'aggTrade':
            return None
        
        return self._parse_single_trade(message)
