"""Base parser class for exchange-specific implementations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd


class BaseExchangeParser(ABC):
    """
    Base class for exchange-specific trade data parsers.
    
    All exchange parsers must implement:
    - parse_trades(): Convert raw exchange data to standard format
    - parse_websocket_trade(): Parse single WebSocket trade message (optional)
    
    Standard trade format:
    {
        'time': pd.Timestamp (UTC),
        'px': float (price),
        'sz': float (size in base currency),
        'side': str ('A'=aggressor buy, 'B'=aggressor sell)
    }
    """
    
    def __init__(self, symbol: str):
        """
        Initialize parser for specific symbol.
        
        Args:
            symbol: Trading pair symbol (parser handles exchange-specific format)
        """
        self.symbol = symbol
        self.exchange_name = self.__class__.__name__.replace('Parser', '').upper()
    
    @abstractmethod
    def parse_trades(self, raw_data: Any) -> List[Dict[str, Any]]:
        """
        Parse exchange-specific trade data to standard format.
        
        Args:
            raw_data: Raw trade data from exchange (REST API response, CSV, etc.)
        
        Returns:
            List of trades in standard format
        """
        pass
    
    def parse_websocket_trade(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse single WebSocket trade message (optional, exchange-specific).
        
        Args:
            message: Raw WebSocket message
        
        Returns:
            Single trade in standard format, or None if not a trade message
        """
        return None
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol to exchange-specific format.
        
        Args:
            symbol: Generic symbol (e.g., 'BTC', 'BTCUSDT', 'BTC-USD')
        
        Returns:
            Exchange-specific symbol format
        """
        return symbol
    
    def validate_trade(self, trade: Dict[str, Any]) -> bool:
        """
        Validate trade has required fields in correct format.
        
        Args:
            trade: Trade dictionary
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = {'time', 'px', 'sz', 'side'}
        
        if not all(field in trade for field in required_fields):
            return False
        
        if not isinstance(trade['time'], pd.Timestamp):
            return False
        
        if trade['side'] not in ('A', 'B'):
            return False
        
        try:
            float(trade['px'])
            float(trade['sz'])
        except (ValueError, TypeError):
            return False
        
        return True
    
    def __repr__(self):
        return f"{self.exchange_name}Parser(symbol='{self.symbol}')"
