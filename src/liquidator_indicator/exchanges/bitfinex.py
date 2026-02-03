"""Bitfinex exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class BitfinexParser(BaseExchangeParser):
    """
    Parser for Bitfinex exchange trade data.
    
    Supports:
    - REST API trades endpoint response
    - WebSocket trade messages
    
    Symbol formats: tBTCUSD, tETHUSD (trading pairs start with 't')
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to Bitfinex format."""
        symbol = symbol.upper().replace('-', '').replace('_', '').replace('/', '')
        
        if not symbol.startswith('t'):
            symbol = 't' + symbol
        
        if not symbol.endswith('USD') and not symbol.endswith('USDT'):
            symbol = symbol + 'USD'
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse Bitfinex REST API trades response.
        
        Bitfinex trades format (array):
        [
          [
            ID,           // 0
            MTS,          // 1 - millisecond timestamp
            AMOUNT,       // 2 - positive=buy, negative=sell
            PRICE         // 3
          ]
        ]
        """
        trades = []
        
        if isinstance(raw_data, list):
            for item in raw_data:
                trade = self._parse_single_trade(item)
                if trade:
                    trades.append(trade)
        
        return trades
    
    def _parse_single_trade(self, raw_trade: Any) -> Optional[Dict[str, Any]]:
        """Parse a single Bitfinex trade."""
        try:
            # Array format: [ID, MTS, AMOUNT, PRICE]
            if isinstance(raw_trade, list) and len(raw_trade) >= 4:
                time = pd.Timestamp(int(raw_trade[1]), unit='ms', tz='UTC')
                price = float(raw_trade[3])
                amount = float(raw_trade[2])
                size = abs(amount)
                side = 'A' if amount > 0 else 'B'
                
                return {
                    'time': time,
                    'px': price,
                    'sz': size,
                    'side': side
                }
        except (ValueError, TypeError, IndexError):
            return None
        
        return None
    
    def parse_websocket_trade(self, message: Any) -> Optional[Dict[str, Any]]:
        """Parse Bitfinex WebSocket trade message."""
        if isinstance(message, list) and len(message) >= 2:
            # WebSocket format: [CHANNEL_ID, "te", [ID, MTS, AMOUNT, PRICE]]
            if message[1] == 'te' and isinstance(message[2], list):
                return self._parse_single_trade(message[2])
        return None
