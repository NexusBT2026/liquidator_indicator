"""
FundingRateCollector - Collect live funding rates and open interest from Hyperliquid WebSocket.

Based on src/data/funding_ws_connection.py pattern but simplified for package distribution.

Usage:
    from liquidator_indicator.collectors.funding import FundingRateCollector
    
    collector = FundingRateCollector(symbols=['BTC', 'ETH'])
    collector.start()
    
    # Get latest data
    data = collector.get_latest()
    print(data)
    # {'BTC': {'funding_rate': 0.0001, 'open_interest': 12345.67, 'timestamp': '2026-02-02T...'}}
    
    # Feed to indicator
    liq.ingest_funding_rates(data)
    
    collector.stop()
"""
import json
import time
import threading
from datetime import datetime, timezone
from typing import List, Dict, Optional, Callable
import logging

try:
    import websocket
except ImportError:
    raise ImportError("websocket-client required: pip install websocket-client")

logger = logging.getLogger("liquidator_indicator.funding_collector")


class FundingRateCollector:
    """Collect live funding rates and open interest from Hyperliquid WebSocket."""
    
    def __init__(
        self,
        symbols: List[str],
        ws_url: str = "wss://api.hyperliquid.xyz/ws",
        callback: Optional[Callable] = None
    ):
        """
        Args:
            symbols: List of coin symbols to track (e.g. ['BTC', 'ETH'])
            ws_url: WebSocket endpoint URL
            callback: Optional function called on each update: callback(symbol, data)
        """
        self.symbols = [s.upper() for s in symbols]
        self.ws_url = ws_url
        self.callback = callback
        
        self._data = {}  # {symbol: {funding_rate, open_interest, timestamp}}
        self._ws = None
        self._thread = None
        self._running = False
        self._lock = threading.Lock()
    
    def start(self):
        """Start WebSocket connection in background thread."""
        if self._running:
            logger.warning("Collector already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_ws, daemon=True)
        self._thread.start()
        logger.info(f"FundingRateCollector started for {self.symbols}")
    
    def stop(self):
        """Stop WebSocket connection."""
        self._running = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("FundingRateCollector stopped")
    
    def get_latest(self) -> Dict[str, Dict]:
        """Get latest funding data for all symbols.
        
        Returns:
            {symbol: {funding_rate, open_interest, timestamp}}
        """
        with self._lock:
            return self._data.copy()
    
    def get_symbol(self, symbol: str) -> Optional[Dict]:
        """Get latest data for specific symbol."""
        with self._lock:
            return self._data.get(symbol.upper())
    
    def _run_ws(self):
        """WebSocket main loop (runs in background thread)."""
        while self._running:
            try:
                self._ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                    on_open=self._on_open
                )
                self._ws.run_forever()
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            
            if self._running:
                logger.info("Reconnecting in 5s...")
                time.sleep(5)
    
    def _on_open(self, ws):
        """Subscribe to activeAssetCtx channel for funding rates."""
        logger.info("WebSocket connected")
        for symbol in self.symbols:
            sub_msg = json.dumps({
                "method": "subscribe",
                "subscription": {
                    "type": "activeAssetCtx",
                    "coin": symbol
                }
            })
            ws.send(sub_msg)
            logger.info(f"Subscribed to {symbol} funding/OI")
    
    def _on_message(self, ws, message):
        """Process funding rate updates."""
        try:
            if message == '{"channel":"pong"}':
                return
            
            data = json.loads(message)
            channel = data.get('channel', '')
            
            if channel == 'activeAssetCtx':
                asset_data = data.get('data', {})
                coin = asset_data.get('coin', '')
                ctx = asset_data.get('ctx', {})
                
                if coin and ctx and coin in self.symbols:
                    funding_rate = float(ctx.get('funding', 0))
                    open_interest = float(ctx.get('openInterest', 0))
                    timestamp = datetime.now(timezone.utc).isoformat()
                    
                    update = {
                        'funding_rate': funding_rate,
                        'open_interest': open_interest,
                        'timestamp': timestamp
                    }
                    
                    with self._lock:
                        self._data[coin] = update
                    
                    logger.debug(f"{coin}: funding={funding_rate:.6f}, oi={open_interest:.2f}")
                    
                    # Call user callback if provided
                    if self.callback:
                        try:
                            self.callback(coin, update)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")
        
        except Exception as e:
            logger.error(f"Message parse error: {e}")
    
    def _on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        logger.info(f"WebSocket closed: {close_status_code} {close_msg}")


# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    def on_update(symbol, data):
        print(f"UPDATE: {symbol} @ {data['timestamp']}")
        print(f"  Funding: {data['funding_rate']:.6f}")
        print(f"  OI: {data['open_interest']:.2f}")
    
    collector = FundingRateCollector(
        symbols=['BTC', 'ETH', 'SOL'],
        callback=on_update
    )
    
    collector.start()
    
    try:
        while True:
            time.sleep(10)
            latest = collector.get_latest()
            print(f"\nLatest data: {len(latest)} symbols")
    except KeyboardInterrupt:
        print("\nStopping...")
        collector.stop()
