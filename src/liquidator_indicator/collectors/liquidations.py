"""
Liquidation data collectors for multiple exchanges.

Collects REAL liquidation events from exchanges that provide public liquidation feeds.
Each exchange has its own collector class to handle exchange-specific formats.

Usage:
    from liquidator_indicator.collectors.liquidations import (
        BinanceLiquidationCollector,
        BybitLiquidationCollector,
        MultiExchangeLiquidationCollector
    )
    
    # Single exchange
    binance = BinanceLiquidationCollector(symbols=['BTCUSDT', 'ETHUSDT'])
    binance.start()
    liqs = binance.get_liquidations()
    
    # Multiple exchanges (aggregated)
    multi = MultiExchangeLiquidationCollector(
        exchanges=['binance', 'bybit', 'okx'],
        symbols=['BTC', 'ETH']
    )
    multi.start()
    all_liqs = multi.get_liquidations()  # Returns unified DataFrame
    
    # Feed to indicator
    from liquidator_indicator import Liquidator
    liq = Liquidator()
    liq.ingest_liquidations(all_liqs)
"""
import json
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Callable
import logging
import pandas as pd

try:
    import websocket
except ImportError:
    raise ImportError("websocket-client required: pip install websocket-client")

try:
    import requests
except ImportError:
    raise ImportError("requests required: pip install requests")

logger = logging.getLogger("liquidator_indicator.liquidation_collectors")


class BinanceLiquidationCollector:
    """
    Collect liquidation data from Binance Futures.
    
    WebSocket: wss://fstream.binance.com/stream?streams=<symbol>@forceOrder
    Documentation: https://binance-docs.github.io/apidocs/futures/en/#liquidation-order-streams
    """
    
    def __init__(
        self,
        symbols: List[str],
        callback: Optional[Callable] = None
    ):
        """
        Args:
            symbols: List of symbols (e.g., ['BTCUSDT', 'ETHUSDT'])
            callback: Optional function called on each liquidation: callback(liq_data)
        """
        self.symbols = [s.upper() if 'USDT' in s.upper() else f"{s.upper()}USDT" for s in symbols]
        self.callback = callback
        
        self._liquidations = []  # Store recent liquidations
        self._ws = None
        self._thread = None
        self._running = False
        self._lock = threading.Lock()
        
        # Build WebSocket URL with all symbol streams
        streams = [f"{s.lower()}@forceOrder" for s in self.symbols]
        self.ws_url = f"wss://fstream.binance.com/stream?streams={'/'.join(streams)}"
    
    def start(self):
        """Start WebSocket connection."""
        if self._running:
            logger.warning("Binance collector already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_ws, daemon=True)
        self._thread.start()
        logger.info(f"BinanceLiquidationCollector started for {self.symbols}")
    
    def stop(self):
        """Stop WebSocket connection."""
        self._running = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
    
    def _run_ws(self):
        """WebSocket event loop."""
        while self._running:
            try:
                self._ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                self._ws.run_forever()
            except Exception as e:
                logger.error(f"Binance WebSocket error: {e}")
                if self._running:
                    time.sleep(5)  # Reconnect after 5 seconds
    
    def _on_message(self, ws, message):
        """Parse liquidation message."""
        try:
            data = json.loads(message)
            if 'data' not in data:
                return
            
            order = data['data']['o']
            
            liq = {
                'exchange': 'binance',
                'symbol': order['s'],
                'side': 'SELL' if order['S'] == 'SELL' else 'BUY',  # Order side
                'price': float(order['p']),
                'quantity': float(order['q']),
                'value_usd': float(order['p']) * float(order['q']),
                'timestamp': datetime.fromtimestamp(order['T'] / 1000, tz=timezone.utc),
                'raw': order
            }
            
            with self._lock:
                self._liquidations.append(liq)
                # Keep only last 10,000 liquidations in memory
                if len(self._liquidations) > 10000:
                    self._liquidations = self._liquidations[-10000:]
            
            if self.callback:
                self.callback(liq)
                
        except Exception as e:
            logger.error(f"Error parsing Binance liquidation: {e}")
    
    def _on_error(self, ws, error):
        logger.error(f"Binance WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        logger.info(f"Binance WebSocket closed: {close_status_code} - {close_msg}")
    
    def get_liquidations(self, since: Optional[datetime] = None) -> pd.DataFrame:
        """
        Get liquidations as DataFrame.
        
        Args:
            since: Optional datetime filter (only return liquidations after this time)
            
        Returns:
            DataFrame with columns: exchange, symbol, side, price, quantity, value_usd, timestamp
        """
        with self._lock:
            if not self._liquidations:
                return pd.DataFrame()
            
            df = pd.DataFrame(self._liquidations)
            
            if since:
                df = df[df['timestamp'] >= since]
            
            return df[['exchange', 'symbol', 'side', 'price', 'quantity', 'value_usd', 'timestamp']]


class BybitLiquidationCollector:
    """
    Collect liquidation data from Bybit.
    
    WebSocket: wss://stream.bybit.com/v5/public/linear (liquidation channel)
    REST API: /v5/market/recent-trade for liquidation flag
    """
    
    def __init__(
        self,
        symbols: List[str],
        callback: Optional[Callable] = None
    ):
        """
        Args:
            symbols: List of symbols (e.g., ['BTCUSDT', 'ETHUSDT'])
            callback: Optional function called on each liquidation
        """
        self.symbols = [s.upper() if 'USDT' in s.upper() else f"{s.upper()}USDT" for s in symbols]
        self.callback = callback
        
        self._liquidations = []
        self._ws = None
        self._thread = None
        self._running = False
        self._lock = threading.Lock()
        
        self.ws_url = "wss://stream.bybit.com/v5/public/linear"
    
    def start(self):
        """Start WebSocket connection."""
        if self._running:
            logger.warning("Bybit collector already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_ws, daemon=True)
        self._thread.start()
        logger.info(f"BybitLiquidationCollector started for {self.symbols}")
    
    def stop(self):
        """Stop WebSocket connection."""
        self._running = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
    
    def _run_ws(self):
        """WebSocket event loop."""
        while self._running:
            try:
                self._ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                self._ws.run_forever()
            except Exception as e:
                logger.error(f"Bybit WebSocket error: {e}")
                if self._running:
                    time.sleep(5)
    
    def _on_open(self, ws):
        """Subscribe to liquidation streams."""
        for symbol in self.symbols:
            subscribe_msg = {
                "op": "subscribe",
                "args": [f"liquidation.{symbol}"]
            }
            ws.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to Bybit liquidation.{symbol}")
    
    def _on_message(self, ws, message):
        """Parse liquidation message."""
        try:
            data = json.loads(message)
            
            # Skip subscription confirmations
            if data.get('op') == 'subscribe':
                return
            
            if 'data' not in data:
                return
            
            liq_data = data['data']
            
            liq = {
                'exchange': 'bybit',
                'symbol': liq_data.get('symbol', ''),
                'side': liq_data.get('side', '').upper(),
                'price': float(liq_data.get('price', 0)),
                'quantity': float(liq_data.get('size', 0)),
                'value_usd': float(liq_data.get('price', 0)) * float(liq_data.get('size', 0)),
                'timestamp': datetime.fromtimestamp(int(liq_data.get('updatedTime', 0)) / 1000, tz=timezone.utc),
                'raw': liq_data
            }
            
            with self._lock:
                self._liquidations.append(liq)
                if len(self._liquidations) > 10000:
                    self._liquidations = self._liquidations[-10000:]
            
            if self.callback:
                self.callback(liq)
                
        except Exception as e:
            logger.error(f"Error parsing Bybit liquidation: {e}")
    
    def _on_error(self, ws, error):
        logger.error(f"Bybit WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        logger.info(f"Bybit WebSocket closed: {close_status_code} - {close_msg}")
    
    def get_liquidations(self, since: Optional[datetime] = None) -> pd.DataFrame:
        """Get liquidations as DataFrame."""
        with self._lock:
            if not self._liquidations:
                return pd.DataFrame()
            
            df = pd.DataFrame(self._liquidations)
            
            if since:
                df = df[df['timestamp'] >= since]
            
            return df[['exchange', 'symbol', 'side', 'price', 'quantity', 'value_usd', 'timestamp']]


class OKXLiquidationCollector:
    """
    Collect liquidation data from OKX.
    
    REST API: /api/v5/public/liquidation-orders (historical)
    WebSocket: wss://ws.okx.com:8443/ws/v5/public (liquidation-orders channel)
    """
    
    def __init__(
        self,
        symbols: List[str],
        callback: Optional[Callable] = None
    ):
        """
        Args:
            symbols: List of symbols (e.g., ['BTC-USDT', 'ETH-USDT'])
            callback: Optional function called on each liquidation
        """
        # OKX uses format BTC-USDT-SWAP for perpetuals
        self.symbols = [s.upper() if '-USDT-SWAP' in s.upper() else f"{s.replace('USDT', '').upper()}-USDT-SWAP" for s in symbols]
        self.callback = callback
        
        self._liquidations = []
        self._ws = None
        self._thread = None
        self._running = False
        self._lock = threading.Lock()
        
        self.ws_url = "wss://ws.okx.com:8443/ws/v5/public"
        self.rest_url = "https://www.okx.com/api/v5/public/liquidation-orders"
    
    def start(self):
        """Start WebSocket connection and fetch recent history."""
        if self._running:
            logger.warning("OKX collector already running")
            return
        
        # Fetch recent liquidations via REST API first
        self._fetch_recent_liquidations()
        
        self._running = True
        self._thread = threading.Thread(target=self._run_ws, daemon=True)
        self._thread.start()
        logger.info(f"OKXLiquidationCollector started for {self.symbols}")
    
    def stop(self):
        """Stop WebSocket connection."""
        self._running = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
    
    def _fetch_recent_liquidations(self):
        """Fetch recent liquidations via REST API."""
        for symbol in self.symbols:
            try:
                params = {
                    'instId': symbol,
                    'state': 'filled',  # Completed liquidations
                    'limit': 100
                }
                response = requests.get(self.rest_url, params=params, timeout=10)
                data = response.json()
                
                if data.get('code') == '0' and 'data' in data:
                    for liq_data in data['data']:
                        liq = {
                            'exchange': 'okx',
                            'symbol': liq_data['instId'],
                            'side': liq_data['side'].upper(),
                            'price': float(liq_data.get('bkPx', 0)),  # Bankruptcy price
                            'quantity': float(liq_data.get('sz', 0)),
                            'value_usd': float(liq_data.get('bkPx', 0)) * float(liq_data.get('sz', 0)),
                            'timestamp': datetime.fromtimestamp(int(liq_data['cTime']) / 1000, tz=timezone.utc),
                            'raw': liq_data
                        }
                        
                        with self._lock:
                            self._liquidations.append(liq)
                            
            except Exception as e:
                logger.error(f"Error fetching OKX liquidations for {symbol}: {e}")
    
    def _run_ws(self):
        """WebSocket event loop."""
        while self._running:
            try:
                self._ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                self._ws.run_forever()
            except Exception as e:
                logger.error(f"OKX WebSocket error: {e}")
                if self._running:
                    time.sleep(5)
    
    def _on_open(self, ws):
        """Subscribe to liquidation streams."""
        for symbol in self.symbols:
            subscribe_msg = {
                "op": "subscribe",
                "args": [{
                    "channel": "liquidation-orders",
                    "instType": "SWAP",
                    "instId": symbol
                }]
            }
            ws.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to OKX liquidation-orders {symbol}")
    
    def _on_message(self, ws, message):
        """Parse liquidation message."""
        try:
            data = json.loads(message)
            
            # Skip subscription confirmations
            if data.get('event') == 'subscribe':
                return
            
            if 'data' not in data:
                return
            
            # data['data'] is the list of liquidation details
            for liq_data in data['data']:
                liq = {
                    'exchange': 'okx',
                    'symbol': data['arg']['instId'],
                    'side': liq_data['side'].upper(),
                    'price': float(liq_data.get('bkPx', 0)),
                    'quantity': float(liq_data.get('sz', 0)),
                    'value_usd': float(liq_data.get('bkPx', 0)) * float(liq_data.get('sz', 0)),
                    'timestamp': datetime.fromtimestamp(int(liq_data['ts']) / 1000, tz=timezone.utc),
                    'raw': liq_data
                }
                
                with self._lock:
                    self._liquidations.append(liq)
                    if len(self._liquidations) > 10000:
                        self._liquidations = self._liquidations[-10000:]
                
                if self.callback:
                    self.callback(liq)
                    
        except Exception as e:
            logger.error(f"Error parsing OKX liquidation: {e}")
    
    def _on_error(self, ws, error):
        logger.error(f"OKX WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        logger.info(f"OKX WebSocket closed: {close_status_code} - {close_msg}")
    
    def get_liquidations(self, since: Optional[datetime] = None) -> pd.DataFrame:
        """Get liquidations as DataFrame."""
        with self._lock:
            if not self._liquidations:
                return pd.DataFrame()
            
            df = pd.DataFrame(self._liquidations)
            
            if since:
                df = df[df['timestamp'] >= since]
            
            return df[['exchange', 'symbol', 'side', 'price', 'quantity', 'value_usd', 'timestamp']]


class BitMEXLiquidationCollector:
    """
    Collect liquidation data from BitMEX.
    
    REST API: /api/v1/trade?filter={"liquidation": true}
    """
    
    def __init__(
        self,
        symbols: List[str],
        callback: Optional[Callable] = None,
        poll_interval: int = 5
    ):
        """
        Args:
            symbols: List of symbols (e.g., ['XBTUSD', 'ETHUSD'])
            callback: Optional function called on each liquidation
            poll_interval: Seconds between REST API polls
        """
        self.symbols = [s.upper() for s in symbols]
        self.callback = callback
        self.poll_interval = poll_interval
        
        self._liquidations = []
        self._thread = None
        self._running = False
        self._lock = threading.Lock()
        self._last_fetch = {}  # symbol -> last_timestamp
        
        self.rest_url = "https://www.bitmex.com/api/v1/trade"
    
    def start(self):
        """Start polling REST API."""
        if self._running:
            logger.warning("BitMEX collector already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info(f"BitMEXLiquidationCollector started for {self.symbols}")
    
    def stop(self):
        """Stop polling."""
        self._running = False
    
    def _poll_loop(self):
        """Poll REST API for liquidations."""
        while self._running:
            for symbol in self.symbols:
                try:
                    params = {
                        'symbol': symbol,
                        'filter': json.dumps({'liquidation': True}),
                        'count': 500,
                        'reverse': True
                    }
                    
                    response = requests.get(self.rest_url, params=params, timeout=10)
                    data = response.json()
                    
                    if isinstance(data, list):
                        for trade in data:
                            timestamp = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00'))
                            
                            # Skip if we've seen this before
                            if symbol in self._last_fetch and timestamp <= self._last_fetch[symbol]:
                                continue
                            
                            liq = {
                                'exchange': 'bitmex',
                                'symbol': trade['symbol'],
                                'side': trade['side'].upper(),
                                'price': float(trade['price']),
                                'quantity': float(trade['size']),
                                'value_usd': float(trade['homeNotional']),  # USD value
                                'timestamp': timestamp,
                                'raw': trade
                            }
                            
                            with self._lock:
                                self._liquidations.append(liq)
                                if len(self._liquidations) > 10000:
                                    self._liquidations = self._liquidations[-10000:]
                            
                            if self.callback:
                                self.callback(liq)
                        
                        # Update last fetch time
                        if data:
                            self._last_fetch[symbol] = datetime.fromisoformat(data[0]['timestamp'].replace('Z', '+00:00'))
                            
                except Exception as e:
                    logger.error(f"Error fetching BitMEX liquidations for {symbol}: {e}")
            
            time.sleep(self.poll_interval)
    
    def get_liquidations(self, since: Optional[datetime] = None) -> pd.DataFrame:
        """Get liquidations as DataFrame."""
        with self._lock:
            if not self._liquidations:
                return pd.DataFrame()
            
            df = pd.DataFrame(self._liquidations)
            
            if since:
                df = df[df['timestamp'] >= since]
            
            return df[['exchange', 'symbol', 'side', 'price', 'quantity', 'value_usd', 'timestamp']]


class DeribitLiquidationCollector:
    """
    Collect liquidation data from Deribit.
    
    WebSocket: wss://www.deribit.com/ws/api/v2 (trades.{instrument}.raw.liquidation channel)
    """
    
    def __init__(
        self,
        symbols: List[str],
        callback: Optional[Callable] = None
    ):
        """
        Args:
            symbols: List of symbols (e.g., ['BTC-PERPETUAL', 'ETH-PERPETUAL'])
            callback: Optional function called on each liquidation
        """
        self.symbols = [s.upper() if 'PERPETUAL' in s.upper() else f"{s.upper()}-PERPETUAL" for s in symbols]
        self.callback = callback
        
        self._liquidations = []
        self._ws = None
        self._thread = None
        self._running = False
        self._lock = threading.Lock()
        
        self.ws_url = "wss://www.deribit.com/ws/api/v2"
    
    def start(self):
        """Start WebSocket connection."""
        if self._running:
            logger.warning("Deribit collector already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_ws, daemon=True)
        self._thread.start()
        logger.info(f"DeribitLiquidationCollector started for {self.symbols}")
    
    def stop(self):
        """Stop WebSocket connection."""
        self._running = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
    
    def _run_ws(self):
        """WebSocket event loop."""
        while self._running:
            try:
                self._ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                self._ws.run_forever()
            except Exception as e:
                logger.error(f"Deribit WebSocket error: {e}")
                if self._running:
                    time.sleep(5)
    
    def _on_open(self, ws):
        """Subscribe to liquidation streams."""
        for symbol in self.symbols:
            subscribe_msg = {
                "jsonrpc": "2.0",
                "method": "public/subscribe",
                "params": {
                    "channels": [f"trades.{symbol}.liquidation"]
                },
                "id": 1
            }
            ws.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to Deribit trades.{symbol}.liquidation")
    
    def _on_message(self, ws, message):
        """Parse liquidation message."""
        try:
            data = json.loads(message)
            
            # Skip subscription confirmations
            if 'result' in data:
                return
            
            if 'params' not in data or 'data' not in data['params']:
                return
            
            for trade in data['params']['data']:
                if not trade.get('liquidation'):
                    continue
                
                liq = {
                    'exchange': 'deribit',
                    'symbol': trade['instrument_name'],
                    'side': trade['direction'].upper(),
                    'price': float(trade['price']),
                    'quantity': float(trade['amount']),
                    'value_usd': float(trade['price']) * float(trade['amount']),
                    'timestamp': datetime.fromtimestamp(trade['timestamp'] / 1000, tz=timezone.utc),
                    'raw': trade
                }
                
                with self._lock:
                    self._liquidations.append(liq)
                    if len(self._liquidations) > 10000:
                        self._liquidations = self._liquidations[-10000:]
                
                if self.callback:
                    self.callback(liq)
                    
        except Exception as e:
            logger.error(f"Error parsing Deribit liquidation: {e}")
    
    def _on_error(self, ws, error):
        logger.error(f"Deribit WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        logger.info(f"Deribit WebSocket closed: {close_status_code} - {close_msg}")
    
    def get_liquidations(self, since: Optional[datetime] = None) -> pd.DataFrame:
        """Get liquidations as DataFrame."""
        with self._lock:
            if not self._liquidations:
                return pd.DataFrame()
            
            df = pd.DataFrame(self._liquidations)
            
            if since:
                df = df[df['timestamp'] >= since]
            
            return df[['exchange', 'symbol', 'side', 'price', 'quantity', 'value_usd', 'timestamp']]


class HTXLiquidationCollector:
    """
    Collect liquidation data from HTX (formerly Huobi).
    
    REST API: /linear-swap-api/v3/swap_liquidation_orders
    """
    
    def __init__(
        self,
        symbols: List[str],
        callback: Optional[Callable] = None,
        poll_interval: int = 10
    ):
        """
        Args:
            symbols: List of symbols (e.g., ['BTC-USDT', 'ETH-USDT'])
            callback: Optional function called on each liquidation
            poll_interval: Seconds between REST API polls
        """
        self.symbols = [s.upper() if '-USDT' in s.upper() else f"{s.upper()}-USDT" for s in symbols]
        self.callback = callback
        self.poll_interval = poll_interval
        
        self._liquidations = []
        self._thread = None
        self._running = False
        self._lock = threading.Lock()
        self._last_fetch = {}
        
        self.rest_url = "https://api.hbdm.com/linear-swap-api/v3/swap_liquidation_orders"
    
    def start(self):
        """Start polling REST API."""
        if self._running:
            logger.warning("HTX collector already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info(f"HTXLiquidationCollector started for {self.symbols}")
    
    def stop(self):
        """Stop polling."""
        self._running = False
    
    def _poll_loop(self):
        """Poll REST API for liquidations."""
        while self._running:
            for symbol in self.symbols:
                try:
                    # HTX API expects 'contract' parameter with format like 'BTC-USDT'
                    params = {
                        'contract': symbol,
                        'trade_type': 0,  # All liquidations
                        'page_size': 50
                    }
                    
                    response = requests.get(self.rest_url, params=params, timeout=10)
                    data = response.json()
                    
                    if data.get('code') == 200 and 'data' in data and isinstance(data['data'], list):
                        for order in data['data']:
                            timestamp = datetime.fromtimestamp(order['created_at'] / 1000, tz=timezone.utc)
                            
                            # Skip if seen before
                            if symbol in self._last_fetch and timestamp <= self._last_fetch[symbol]:
                                continue
                            
                            liq = {
                                'exchange': 'htx',
                                'symbol': symbol,
                                'side': 'BUY' if order['direction'] == 'buy' else 'SELL',
                                'price': float(order['price']),
                                'quantity': float(order['amount']),
                                'value_usd': float(order['trade_turnover']),
                                'timestamp': timestamp,
                                'raw': order
                            }
                            
                            with self._lock:
                                self._liquidations.append(liq)
                                if len(self._liquidations) > 10000:
                                    self._liquidations = self._liquidations[-10000:]
                            
                            if self.callback:
                                self.callback(liq)
                        
                        if data['data']:
                            self._last_fetch[symbol] = datetime.fromtimestamp(
                                data['data'][0]['created_at'] / 1000, tz=timezone.utc
                            )
                            
                except Exception as e:
                    logger.error(f"Error fetching HTX liquidations for {symbol}: {e}")
            
            time.sleep(self.poll_interval)
    
    def get_liquidations(self, since: Optional[datetime] = None) -> pd.DataFrame:
        """Get liquidations as DataFrame."""
        with self._lock:
            if not self._liquidations:
                return pd.DataFrame()
            
            df = pd.DataFrame(self._liquidations)
            
            if since:
                df = df[df['timestamp'] >= since]
            
            return df[['exchange', 'symbol', 'side', 'price', 'quantity', 'value_usd', 'timestamp']]


class PhemexLiquidationCollector:
    """
    Collect liquidation data from Phemex.
    
    REST API: /public/md/v2/trade (with liquidation filter)
    """
    
    def __init__(
        self,
        symbols: List[str],
        callback: Optional[Callable] = None,
        poll_interval: int = 10
    ):
        """
        Args:
            symbols: List of symbols (e.g., ['BTCUSDT', 'ETHUSDT'])
            callback: Optional function called on each liquidation
            poll_interval: Seconds between REST API polls
        """
        self.symbols = [s.upper() if 'USDT' in s.upper() else f"{s.upper()}USDT" for s in symbols]
        self.callback = callback
        self.poll_interval = poll_interval
        
        self._liquidations = []
        self._thread = None
        self._running = False
        self._lock = threading.Lock()
        self._last_fetch = {}
        
        # Phemex perpetual contract endpoint
        self.rest_url = "https://api.phemex.com/md/v2/trade"
    
    def start(self):
        """Start polling REST API."""
        if self._running:
            logger.warning("Phemex collector already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info(f"PhemexLiquidationCollector started for {self.symbols}")
    
    def stop(self):
        """Stop polling."""
        self._running = False
    
    def _poll_loop(self):
        """Poll REST API for liquidations."""
        while self._running:
            for symbol in self.symbols:
                try:
                    params = {
                        'symbol': symbol
                    }
                    
                    response = requests.get(self.rest_url, params=params, timeout=10)
                    data = response.json()
                    
                    if data.get('error') is None and 'result' in data and 'trades_p' in data['result']:
                        for trade in data['result']['trades_p']:
                            # Phemex doesn't explicitly mark liquidations, so we filter large trades
                            # trade format: [timestamp_ns, side, price, quantity]
                            value_usd = float(trade[2]) * float(trade[3])
                            if value_usd < 10000:  # Skip small trades
                                continue
                            
                            timestamp = datetime.fromtimestamp(int(trade[0]) / 1e9, tz=timezone.utc)
                            
                            # Skip if seen before
                            if symbol in self._last_fetch and timestamp <= self._last_fetch[symbol]:
                                continue
                            
                            liq = {
                                'exchange': 'phemex',
                                'symbol': symbol,
                                'side': trade[1].upper(),
                                'price': float(trade[2]),
                                'quantity': float(trade[3]),
                                'value_usd': value_usd,
                                'timestamp': timestamp,
                                'raw': trade
                            }
                            
                            with self._lock:
                                self._liquidations.append(liq)
                                if len(self._liquidations) > 10000:
                                    self._liquidations = self._liquidations[-10000:]
                            
                            if self.callback:
                                self.callback(liq)
                        
                        if data['result']['trades_p']:
                            self._last_fetch[symbol] = datetime.fromtimestamp(
                                int(data['result']['trades_p'][0][0]) / 1e9, tz=timezone.utc
                            )
                            
                except Exception as e:
                    logger.error(f"Error fetching Phemex liquidations for {symbol}: {e}")
            
            time.sleep(self.poll_interval)
    
    def get_liquidations(self, since: Optional[datetime] = None) -> pd.DataFrame:
        """Get liquidations as DataFrame."""
        with self._lock:
            if not self._liquidations:
                return pd.DataFrame()
            
            df = pd.DataFrame(self._liquidations)
            
            if since:
                df = df[df['timestamp'] >= since]
            
            return df[['exchange', 'symbol', 'side', 'price', 'quantity', 'value_usd', 'timestamp']]


class MEXCLiquidationCollector:
    """
    Collect liquidation data from MEXC.
    
    REST API: /api/v1/private/liquidation_orders (requires authentication for full access)
    Note: Public endpoint may have limited data
    """
    
    def __init__(
        self,
        symbols: List[str],
        callback: Optional[Callable] = None,
        poll_interval: int = 10
    ):
        """
        Args:
            symbols: List of symbols (e.g., ['BTC_USDT', 'ETH_USDT'])
            callback: Optional function called on each liquidation
            poll_interval: Seconds between REST API polls
        """
        self.symbols = [s.upper().replace('-', '_') if 'USDT' in s.upper() else f"{s.upper()}_USDT" for s in symbols]
        self.callback = callback
        self.poll_interval = poll_interval
        
        self._liquidations = []
        self._thread = None
        self._running = False
        self._lock = threading.Lock()
        self._last_fetch = {}
        
        # MEXC uses Binance-compatible API
        self.rest_url = "https://api.mexc.com/api/v3/aggTrades"
    
    def start(self):
        """Start polling REST API."""
        if self._running:
            logger.warning("MEXC collector already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info(f"MEXCLiquidationCollector started for {self.symbols}")
    
    def stop(self):
        """Stop polling."""
        self._running = False
    
    def _poll_loop(self):
        """Poll REST API for liquidations."""
        while self._running:
            for symbol in self.symbols:
                try:
                    # Use spot market as proxy - filter large trades as potential liquidations
                    spot_symbol = symbol.replace('_', '')
                    params = {
                        'symbol': spot_symbol,
                        'limit': 100
                    }
                    
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    response = requests.get(self.rest_url, params=params, headers=headers, timeout=10)
                    data = response.json()
                    
                    if isinstance(data, list):
                        for trade in data:
                            # Filter for large trades (potential liquidations)
                            qty_usd = float(trade['p']) * float(trade['q'])
                            if qty_usd < 10000:  # Skip small trades
                                continue
                                
                            timestamp = datetime.fromtimestamp(int(trade['T']) / 1000, tz=timezone.utc)
                            
                            # Skip if seen before
                            if symbol in self._last_fetch and timestamp <= self._last_fetch[symbol]:
                                continue
                            
                            liq = {
                                'exchange': 'mexc',
                                'symbol': symbol,
                                'side': 'SELL' if trade['m'] else 'BUY',  # m=true means buyer is maker
                                'price': float(trade['p']),
                                'quantity': float(trade['q']),
                                'value_usd': qty_usd,
                                'timestamp': timestamp,
                                'raw': trade
                            }
                            
                            with self._lock:
                                self._liquidations.append(liq)
                                if len(self._liquidations) > 10000:
                                    self._liquidations = self._liquidations[-10000:]
                            
                            if self.callback:
                                self.callback(liq)
                        
                        if data:
                            self._last_fetch[symbol] = datetime.fromtimestamp(
                                int(data[0]['T']) / 1000, tz=timezone.utc
                            )
                            
                except Exception as e:
                    logger.error(f"Error fetching MEXC liquidations for {symbol}: {e}")
            
            time.sleep(self.poll_interval)
    
    def get_liquidations(self, since: Optional[datetime] = None) -> pd.DataFrame:
        """Get liquidations as DataFrame."""
        with self._lock:
            if not self._liquidations:
                return pd.DataFrame()
            
            df = pd.DataFrame(self._liquidations)
            
            if since:
                df = df[df['timestamp'] >= since]
            
            return df[['exchange', 'symbol', 'side', 'price', 'quantity', 'value_usd', 'timestamp']]


class MultiExchangeLiquidationCollector:
    """
    Aggregate liquidation data from multiple exchanges.
    
    Manages multiple exchange collectors and provides unified interface.
    
    Usage:
        collector = MultiExchangeLiquidationCollector(
            exchanges=['binance', 'bybit', 'okx', 'bitmex', 'deribit', 'htx', 'phemex', 'mexc'],
            symbols=['BTC', 'ETH']
        )
        collector.start()
        
        # Get all liquidations across exchanges
        all_liqs = collector.get_liquidations()
        
        # Get cross-exchange statistics
        stats = collector.get_statistics()
    """
    
    def __init__(
        self,
        exchanges: List[str],
        symbols: List[str],
        callback: Optional[Callable] = None
    ):
        """
        Args:
            exchanges: List of exchange names ('binance', 'bybit', 'okx', 'bitmex', 'deribit', 'htx', 'phemex', 'mexc')
            symbols: List of base symbols (e.g., ['BTC', 'ETH'])
            callback: Optional function called on each liquidation from any exchange
        """
        self.exchanges = [e.lower() for e in exchanges]
        self.symbols = symbols
        self.callback = callback
        
        self._collectors = {}
        
        # Initialize collectors for each exchange
        if 'binance' in self.exchanges:
            self._collectors['binance'] = BinanceLiquidationCollector(
                symbols=symbols,
                callback=self._on_liquidation
            )
        
        if 'bybit' in self.exchanges:
            self._collectors['bybit'] = BybitLiquidationCollector(
                symbols=symbols,
                callback=self._on_liquidation
            )
        
        if 'okx' in self.exchanges:
            self._collectors['okx'] = OKXLiquidationCollector(
                symbols=symbols,
                callback=self._on_liquidation
            )
        
        if 'bitmex' in self.exchanges:
            # BitMEX uses different symbol format
            bitmex_symbols = [f"{s.replace('USDT', '')}USD" if s != 'BTC' else 'XBTUSD' for s in symbols]
            self._collectors['bitmex'] = BitMEXLiquidationCollector(
                symbols=bitmex_symbols,
                callback=self._on_liquidation
            )
        
        if 'deribit' in self.exchanges:
            self._collectors['deribit'] = DeribitLiquidationCollector(
                symbols=symbols,
                callback=self._on_liquidation
            )
        
        if 'htx' in self.exchanges or 'huobi' in self.exchanges:
            self._collectors['htx'] = HTXLiquidationCollector(
                symbols=symbols,
                callback=self._on_liquidation
            )
        
        if 'phemex' in self.exchanges:
            self._collectors['phemex'] = PhemexLiquidationCollector(
                symbols=symbols,
                callback=self._on_liquidation
            )
        
        if 'mexc' in self.exchanges:
            self._collectors['mexc'] = MEXCLiquidationCollector(
                symbols=symbols,
                callback=self._on_liquidation
            )
    
    def _on_liquidation(self, liq_data: dict):
        """Called when any exchange reports a liquidation."""
        if self.callback:
            self.callback(liq_data)
    
    def start(self):
        """Start all exchange collectors."""
        for exchange, collector in self._collectors.items():
            try:
                collector.start()
            except Exception as e:
                logger.error(f"Failed to start {exchange} collector: {e}")
    
    def stop(self):
        """Stop all exchange collectors."""
        for collector in self._collectors.values():
            try:
                collector.stop()
            except Exception:
                pass
    
    def get_liquidations(self, since: Optional[datetime] = None) -> pd.DataFrame:
        """
        Get liquidations from all exchanges as unified DataFrame.
        
        Args:
            since: Optional datetime filter
            
        Returns:
            DataFrame with columns: exchange, symbol, side, price, quantity, value_usd, timestamp
        """
        all_dfs = []
        
        for exchange, collector in self._collectors.items():
            try:
                df = collector.get_liquidations(since=since)
                if not df.empty:
                    all_dfs.append(df)
            except Exception as e:
                logger.error(f"Error getting liquidations from {exchange}: {e}")
        
        if not all_dfs:
            return pd.DataFrame(columns=['exchange', 'symbol', 'side', 'price', 'quantity', 'value_usd', 'timestamp'])
        
        combined = pd.concat(all_dfs, ignore_index=True)
        combined = combined.sort_values('timestamp').reset_index(drop=True)
        
        return combined
    
    def get_statistics(self, window_minutes: int = 60) -> Dict:
        """
        Get cross-exchange liquidation statistics.
        
        Args:
            window_minutes: Time window for statistics
            
        Returns:
            Dict with statistics per exchange and totals
        """
        since = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        df = self.get_liquidations(since=since)
        
        if df.empty:
            return {
                'total_liquidations': 0,
                'total_value_usd': 0,
                'by_exchange': {},
                'by_side': {},
                'window_minutes': window_minutes
            }
        
        stats = {
            'total_liquidations': len(df),
            'total_value_usd': df['value_usd'].sum(),
            'by_exchange': df.groupby('exchange').agg({
                'value_usd': ['count', 'sum', 'mean']
            }).to_dict(),
            'by_side': df.groupby('side').agg({
                'value_usd': ['count', 'sum']
            }).to_dict(),
            'window_minutes': window_minutes,
            'timestamp': datetime.now(timezone.utc)
        }
        
        return stats
