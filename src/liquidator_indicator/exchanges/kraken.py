"""Kraken exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class KrakenParser(BaseExchangeParser):
    """
    Parser for Kraken exchange trade data.
    
    Supports:
    - REST API Trades endpoint response
    - WebSocket trade channel messages
    
    Symbol formats: XBT/USD, ETH/USD (Kraken uses XBT for Bitcoin)
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol to Kraken format.
        
        Examples:
            'BTC' -> 'XBT/USD'
            'BTC-USD' -> 'XBT/USD'
            'BTCUSD' -> 'XBT/USD'
            'ETH' -> 'ETH/USD'
        
        Note: Kraken uses XBT (not BTC) for Bitcoin.
        """
        symbol = symbol.upper().replace('-', '/').replace('_', '/')
        
        # Replace BTC with XBT
        if symbol.startswith('BTC'):
            symbol = 'XBT' + symbol[3:]
        
        # Add /USD if not present
        if '/' not in symbol:
            if symbol == 'XBT' or symbol == 'BTC':
                symbol = 'XBT/USD'
            elif symbol.endswith('USD'):
                # XBTUSD -> XBT/USD
                if symbol.startswith('XBT'):
                    symbol = 'XBT/USD'
                elif len(symbol) > 3:
                    symbol = symbol[:-3] + '/USD'
            else:
                symbol = symbol + '/USD'
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse Kraken REST API trades response.
        
        Kraken trades format:
        {
          "error": [],
          "result": {
            "XXBTZUSD": [
              [
                "16837.40000",  // price
                "0.00200000",   // volume
                1672531200.123, // time
                "b",            // buy/sell (b=buy, s=sell is aggressor)
                "m",            // market/limit (m=market, l=limit)
                "",             // miscellaneous
                12345           // trade ID (optional)
              ]
            ],
            "last": "1672531200123456789"
          }
        }
        
        Args:
            raw_data: Response dict from Kraken API, list, or DataFrame
        
        Returns:
            List of trades in standard format
        """
        trades = []
        
        # Handle nested API response
        if isinstance(raw_data, dict) and 'result' in raw_data:
            # Find the symbol key (e.g., "XXBTZUSD")
            result = raw_data['result']
            for key, value in result.items():
                if key != 'last' and isinstance(value, list):
                    raw_data = value
                    break
        
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
    
    def _parse_single_trade(self, raw_trade: Any) -> Optional[Dict[str, Any]]:
        """Parse a single Kraken trade."""
        try:
            # REST API array format: [price, volume, time, buy/sell, market/limit, misc]
            if isinstance(raw_trade, (list, tuple)) and len(raw_trade) >= 4:
                price = float(raw_trade[0])
                size = float(raw_trade[1])
                timestamp = float(raw_trade[2])
                side_str = raw_trade[3].lower()
                
            # WebSocket or dict format
            elif isinstance(raw_trade, dict):
                price = float(raw_trade.get('price', raw_trade.get('p', 0)))
                size = float(raw_trade.get('volume', raw_trade.get('v', raw_trade.get('sz', 0))))
                timestamp = float(raw_trade.get('time', raw_trade.get('timestamp', raw_trade.get('t', 0))))
                side_str = raw_trade.get('side', raw_trade.get('s', 'b')).lower()
                
            else:
                return None
            
            # Convert timestamp (Kraken uses seconds with decimals)
            time = pd.Timestamp(timestamp, unit='s', tz='UTC')
            
            # Convert side
            # Kraken: 'b' = buy (aggressor bought) = 'A'
            #         's' = sell (aggressor sold) = 'B'
            side = 'A' if side_str == 'b' else 'B'
            
            return {
                'time': time,
                'px': price,
                'sz': size,
                'side': side
            }
            
        except (KeyError, ValueError, TypeError, IndexError):
            return None
    
    def parse_websocket_trade(self, message: Any) -> Optional[Dict[str, Any]]:
        """
        Parse Kraken WebSocket trade message.
        
        Message format:
        [
          channelID,
          [
            [
              "16837.40000",
              "0.00200000",
              "1672531200.123456",
              "b",
              "m",
              ""
            ]
          ],
          "trade",
          "XBT/USD"
        ]
        
        Args:
            message: Raw WebSocket message
        
        Returns:
            Single trade in standard format, or None
        """
        if not isinstance(message, list) or len(message) < 4:
            return None
        
        if message[2] != 'trade':
            return None
        
        # Extract trade data (second element, first trade in array)
        if isinstance(message[1], list) and len(message[1]) > 0:
            trade_data = message[1][0]
            return self._parse_single_trade(trade_data)
        
        return None
