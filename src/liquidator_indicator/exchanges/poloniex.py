"""Poloniex exchange parser for trade data."""

from typing import List, Dict, Any, Optional
import pandas as pd
from .base import BaseExchangeParser


class PoloniexParser(BaseExchangeParser):
    """
    Parser for Poloniex exchange trade data.
    
    Supports:
    - REST API trades endpoint response
    - WebSocket trade messages
    
    Symbol formats: USDT_BTC, USDT_ETH (quote first, underscore separator)
    """
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to Poloniex format."""
        symbol = symbol.upper().replace('-', '_').replace('/', '_')
        
        # Poloniex uses QUOTE_BASE format (opposite of most exchanges)
        if '_' not in symbol:
            symbol = 'USDT_' + symbol
        elif not symbol.startswith('USDT_'):
            # Swap if needed: BTC_USDT -> USDT_BTC
            parts = symbol.split('_')
            if len(parts) == 2 and parts[1] in ['USDT', 'USD']:
                symbol = parts[1] + '_' + parts[0]
        
        return symbol
    
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse Poloniex REST API trades response.
        
        Poloniex trades format:
        [
          {
            "date": "2024-01-01 12:00:00",
            "type": "buy",
            "rate": "80000.50",
            "amount": "0.150",
            "total": "12000.075",
            "tradeID": "123456",
            "globalTradeID": 123456
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
        """Parse a single Poloniex trade."""
        try:
            time = pd.Timestamp(raw_trade['date'], tz='UTC')
            price = float(raw_trade['rate'])
            size = float(raw_trade['amount'])
            side = 'A' if raw_trade['type'] == 'buy' else 'B'
            
            return {
                'time': time,
                'px': price,
                'sz': size,
                'side': side
            }
        except (KeyError, ValueError, TypeError):
            return None
    
    def parse_websocket_trade(self, message: Any) -> Optional[Dict[str, Any]]:
        """Parse Poloniex WebSocket trade message."""
        if isinstance(message, list) and len(message) >= 3:
            # Poloniex WS format: [channelId, null, [tradeId, type, rate, amount, timestamp]]
            if isinstance(message[2], list):
                for item in message[2]:
                    if isinstance(item, list) and len(item) >= 5:
                        try:
                            trade = {
                                'date': pd.Timestamp(float(item[4]), unit='s'),
                                'type': 'buy' if item[1] == 1 else 'sell',
                                'rate': item[2],
                                'amount': item[3]
                            }
                            return self._parse_single_trade(trade)
                        except (IndexError, ValueError):
                            continue
        return None
