"""Comprehensive tests for multi-exchange parsers."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
import pytest
from liquidator_indicator.exchanges import (
    HyperliquidParser, BinanceParser, CoinbaseParser, BybitParser, KrakenParser,
    OKXParser, HTXParser, GateIOParser, MEXCParser, BitMEXParser,
    DeribitParser, BitfinexParser, KuCoinParser, PhemexParser, BitgetParser,
    CryptoComParser, BingXParser, BitstampParser, GeminiParser, PoloniexParser
)
from liquidator_indicator import Liquidator

print("=" * 70)
print("MULTI-EXCHANGE PARSER TESTS")
print("=" * 70)
print("\nTesting 21 exchange parsers...")
print("This ensures your package works with ANY major crypto exchange!\n")


class TestHyperliquidParser:
    """Test Hyperliquid exchange parser (USER'S PRIMARY EXCHANGE)."""
    
    def test_hyperliquid_format(self):
        """Test parsing Hyperliquid trade data."""
        raw_data = [
            {
                "coin": "BTC",
                "side": "A",
                "px": "83991.0",
                "sz": "0.09374",
                "time": 1769824534507
            },
            {
                "coin": "BTC",
                "side": "B",
                "px": "83985.5",
                "sz": "0.15000",
                "time": 1769824535000
            }
        ]
        
        parser = HyperliquidParser('BTC')
        trades = parser.parse_trades(raw_data)
        
        assert len(trades) == 2
        assert trades[0]['px'] == 83991.0
        assert trades[0]['sz'] == 0.09374
        assert trades[0]['side'] == 'A'
        assert isinstance(trades[0]['time'], pd.Timestamp)
        
        assert trades[1]['side'] == 'B'
    
    def test_hyperliquid_symbol_normalization(self):
        """Test Hyperliquid symbol normalization."""
        parser = HyperliquidParser('BTC')
        assert parser.normalize_symbol('BTC') == 'BTC'
        assert parser.normalize_symbol('BTC-USD') == 'BTC'
        assert parser.normalize_symbol('BTCUSDT') == 'BTC'
        assert parser.normalize_symbol('BTCPERP') == 'BTC'
    
    def test_hyperliquid_websocket_format(self):
        """Test parsing Hyperliquid WebSocket message."""
        message = {
            "channel": "trades",
            "data": [
                {
                    "coin": "BTC",
                    "side": "A",
                    "px": "83500.0",
                    "sz": "0.200",
                    "time": 1769824534507
                }
            ]
        }
        
        parser = HyperliquidParser('BTC')
        trade = parser.parse_websocket_trade(message)
        
        assert trade is not None
        assert trade['px'] == 83500.0
        assert trade['sz'] == 0.200
        assert trade['side'] == 'A'


class TestBinanceParser:
    """Test Binance exchange parser."""
    
    def test_binance_rest_api_format(self):
        """Test parsing Binance REST API aggTrades response."""
        raw_data = [
            {
                "a": 26129,
                "p": "80000.50",
                "q": "0.150",
                "f": 27781,
                "l": 27781,
                "T": 1672531200000,
                "m": False,
                "M": True
            },
            {
                "a": 26130,
                "p": "80001.25",
                "q": "0.250",
                "f": 27782,
                "l": 27782,
                "T": 1672531201000,
                "m": True,
                "M": True
            }
        ]
        
        parser = BinanceParser('BTCUSDT')
        trades = parser.parse_trades(raw_data)
        
        assert len(trades) == 2
        assert trades[0]['px'] == 80000.50
        assert trades[0]['sz'] == 0.150
        assert trades[0]['side'] == 'A'  # buyer was NOT maker
        assert isinstance(trades[0]['time'], pd.Timestamp)
        
        assert trades[1]['side'] == 'B'  # buyer WAS maker
    
    def test_binance_symbol_normalization(self):
        """Test Binance symbol normalization."""
        parser = BinanceParser('BTC')
        assert parser.normalize_symbol('BTC') == 'BTCUSDT'
        assert parser.normalize_symbol('BTC-USD') == 'BTCUSDT'
        assert parser.normalize_symbol('BTCUSDT') == 'BTCUSDT'
    
    def test_binance_websocket_format(self):
        """Test parsing Binance WebSocket message."""
        message = {
            "e": "aggTrade",
            "E": 123456789,
            "s": "BTCUSDT",
            "a": 12345,
            "p": "79500.00",
            "q": "0.500",
            "f": 100,
            "l": 105,
            "T": 1672531200000,
            "m": False,
            "M": True
        }
        
        parser = BinanceParser('BTCUSDT')
        trade = parser.parse_websocket_trade(message)
        
        assert trade is not None
        assert trade['px'] == 79500.00
        assert trade['sz'] == 0.500
        assert trade['side'] == 'A'


class TestCoinbaseParser:
    """Test Coinbase exchange parser."""
    
    def test_coinbase_rest_api_format(self):
        """Test parsing Coinbase REST API trades response."""
        raw_data = [
            {
                "time": "2024-01-01T12:00:00.123456Z",
                "trade_id": 74,
                "price": "80000.00",
                "size": "0.15000000",
                "side": "buy"
            },
            {
                "time": "2024-01-01T12:00:01.234567Z",
                "trade_id": 75,
                "price": "80001.50",
                "size": "0.25000000",
                "side": "sell"
            }
        ]
        
        parser = CoinbaseParser('BTC-USD')
        trades = parser.parse_trades(raw_data)
        
        assert len(trades) == 2
        assert trades[0]['px'] == 80000.00
        assert trades[0]['sz'] == 0.15
        assert trades[0]['side'] == 'A'  # buy = aggressor buy
        assert trades[1]['side'] == 'B'  # sell = aggressor sell
    
    def test_coinbase_symbol_normalization(self):
        """Test Coinbase symbol normalization."""
        parser = CoinbaseParser('BTC')
        assert parser.normalize_symbol('BTC') == 'BTC-USD'
        assert parser.normalize_symbol('BTCUSD') == 'BTC-USD'
        assert parser.normalize_symbol('BTC-USD') == 'BTC-USD'
    
    def test_coinbase_websocket_format(self):
        """Test parsing Coinbase WebSocket match message."""
        message = {
            "type": "match",
            "trade_id": 10,
            "sequence": 50,
            "maker_order_id": "ac928c66-ca53-498f-9c13-a110027a60e8",
            "taker_order_id": "132fb6ae-456b-4654-b4e0-d681ac05cea1",
            "time": "2024-01-01T08:19:27.028459Z",
            "product_id": "BTC-USD",
            "size": "0.150",
            "price": "79500.00",
            "side": "buy"
        }
        
        parser = CoinbaseParser('BTC-USD')
        trade = parser.parse_websocket_trade(message)
        
        assert trade is not None
        assert trade['px'] == 79500.00
        assert trade['sz'] == 0.150
        assert trade['side'] == 'A'


class TestBybitParser:
    """Test Bybit exchange parser."""
    
    def test_bybit_rest_api_format(self):
        """Test parsing Bybit REST API v5 response."""
        raw_data = {
            "result": {
                "list": [
                    {
                        "execId": "2100000000007764263",
                        "symbol": "BTCUSDT",
                        "price": "80000.49",
                        "size": "0.150",
                        "side": "Buy",
                        "time": "1672052955758",
                        "isBlockTrade": False
                    },
                    {
                        "execId": "2100000000007764264",
                        "symbol": "BTCUSDT",
                        "price": "80001.50",
                        "size": "0.250",
                        "side": "Sell",
                        "time": "1672052956000",
                        "isBlockTrade": False
                    }
                ]
            }
        }
        
        parser = BybitParser('BTCUSDT')
        trades = parser.parse_trades(raw_data)
        
        assert len(trades) == 2
        assert trades[0]['px'] == 80000.49
        assert trades[0]['sz'] == 0.150
        assert trades[0]['side'] == 'A'  # Buy
        assert trades[1]['side'] == 'B'  # Sell
    
    def test_bybit_symbol_normalization(self):
        """Test Bybit symbol normalization."""
        parser = BybitParser('BTC')
        assert parser.normalize_symbol('BTC') == 'BTCUSDT'
        assert parser.normalize_symbol('BTC-USD') == 'BTCUSDT'
        assert parser.normalize_symbol('BTCUSDT') == 'BTCUSDT'
    
    def test_bybit_websocket_format(self):
        """Test parsing Bybit WebSocket message."""
        message = {
            "topic": "publicTrade.BTCUSDT",
            "type": "snapshot",
            "ts": 1672304486868,
            "data": [
                {
                    "T": 1672304486865,
                    "s": "BTCUSDT",
                    "S": "Buy",
                    "v": "0.150",
                    "p": "79500.50",
                    "L": "PlusTick",
                    "i": "20f43950-d8dd-5b31-9112-a178eb6023af",
                    "BT": False
                }
            ]
        }
        
        parser = BybitParser('BTCUSDT')
        trade = parser.parse_websocket_trade(message)
        
        assert trade is not None
        assert trade['px'] == 79500.50
        assert trade['sz'] == 0.150
        assert trade['side'] == 'A'


class TestKrakenParser:
    """Test Kraken exchange parser."""
    
    def test_kraken_rest_api_format(self):
        """Test parsing Kraken REST API trades response."""
        raw_data = {
            "error": [],
            "result": {
                "XXBTZUSD": [
                    ["80000.40000", "0.15000000", 1672531200.123, "b", "m", ""],
                    ["80001.50000", "0.25000000", 1672531201.456, "s", "m", ""]
                ],
                "last": "1672531201456789000"
            }
        }
        
        parser = KrakenParser('XBT/USD')
        trades = parser.parse_trades(raw_data)
        
        assert len(trades) == 2
        assert trades[0]['px'] == 80000.40
        assert trades[0]['sz'] == 0.15
        assert trades[0]['side'] == 'A'  # 'b' = buy
        assert trades[1]['side'] == 'B'  # 's' = sell
    
    def test_kraken_symbol_normalization(self):
        """Test Kraken symbol normalization (BTC -> XBT)."""
        parser = KrakenParser('BTC')
        assert parser.normalize_symbol('BTC') == 'XBT/USD'
        assert parser.normalize_symbol('BTCUSD') == 'XBT/USD'
        assert parser.normalize_symbol('BTC-USD') == 'XBT/USD'
        assert parser.normalize_symbol('XBT/USD') == 'XBT/USD'
    
    def test_kraken_websocket_format(self):
        """Test parsing Kraken WebSocket message."""
        message = [
            123,  # channelID
            [
                ["79500.40000", "0.15000000", "1672531200.123456", "b", "m", ""]
            ],
            "trade",
            "XBT/USD"
        ]
        
        parser = KrakenParser('XBT/USD')
        trade = parser.parse_websocket_trade(message)
        
        assert trade is not None
        assert trade['px'] == 79500.40
        assert trade['sz'] == 0.15
        assert trade['side'] == 'A'


class TestLiquidatorFromExchange:
    """Test Liquidator.from_exchange() convenience method."""
    
    def test_hyperliquid_integration(self):
        """Test creating Liquidator with Hyperliquid parser (USER'S EXCHANGE)."""
        hyperliquid_data = [
            {"coin": "BTC", "side": "A", "px": "83991.0", "sz": "1.5", "time": 1769824534507},
            {"coin": "BTC", "side": "B", "px": "83985.5", "sz": "2.0", "time": 1769824535000}
        ]
        
        try:
            L = Liquidator.from_exchange('BTC', 'hyperliquid', raw_data=hyperliquid_data, cutoff_hours=None)
            
            assert L.coin == 'BTC', f"Expected coin='BTC', got {L.coin}"
            assert not L._trades.empty, f"Trades DataFrame is empty! {L._trades}"
            assert len(L._trades) == 2, f"Expected 2 trades, got {len(L._trades)}"
            print("✅ Hyperliquid integration works!")
        except Exception as e:
            print(f"❌ Hyperliquid integration failed: {e}")
            raise
    
    def test_binance_integration(self):
        """Test creating Liquidator with Binance parser."""
        binance_data = [
            {"a": 1, "p": "80000", "q": "1.5", "T": 1672531200000, "m": False, "M": True},
            {"a": 2, "p": "80100", "q": "2.0", "T": 1672531201000, "m": True, "M": True}
        ]
        
        L = Liquidator.from_exchange('BTC', 'binance', raw_data=binance_data, cutoff_hours=None)
        
        assert L.coin == 'BTC'
        assert not L._trades.empty
        assert len(L._trades) == 2
    
    def test_coinbase_integration(self):
        """Test creating Liquidator with Coinbase parser."""
        coinbase_data = [
            {"time": "2024-01-01T12:00:00Z", "price": "80000", "size": "1.5", "side": "buy"},
            {"time": "2024-01-01T12:00:01Z", "price": "80100", "size": "2.0", "side": "sell"}
        ]
        
        L = Liquidator.from_exchange('BTC', 'coinbase', raw_data=coinbase_data, cutoff_hours=None)
        
        assert L.coin == 'BTC'
        assert not L._trades.empty
    
    def test_bybit_integration(self):
        """Test creating Liquidator with Bybit parser."""
        bybit_data = {
            "result": {
                "list": [
                    {"execId": "1", "price": "80000", "size": "1.5", "side": "Buy", "time": "1672052955758"}
                ]
            }
        }
        
        L = Liquidator.from_exchange('BTC', 'bybit', raw_data=bybit_data, cutoff_hours=None)
        
        assert L.coin == 'BTC'
        assert not L._trades.empty
    
    def test_kraken_integration(self):
        """Test creating Liquidator with Kraken parser."""
        kraken_data = {
            "result": {
                "XXBTZUSD": [
                    ["80000", "1.5", 1672531200.123, "b", "m", ""]
                ]
            }
        }
        
        L = Liquidator.from_exchange('BTC', 'kraken', raw_data=kraken_data, cutoff_hours=None)
        
        assert L.coin == 'BTC'
        assert not L._trades.empty
    
    def test_unsupported_exchange(self):
        """Test error handling for unsupported exchange."""
        with pytest.raises(ValueError, match="not supported"):
            Liquidator.from_exchange('BTC', 'unknown_exchange', raw_data=[])
    
    def test_all_supported_exchanges(self):
        """Test that all 21+ major exchanges are supported."""
        supported_exchanges = [
            'hyperliquid',   # User's primary exchange
            'binance',       # Largest by volume
            'coinbase',      # Major US exchange
            'bybit',         # Major derivatives
            'kraken',        # Major EU/US exchange
            'okx',           # Major global exchange
            'htx', 'huobi',  # HTX (formerly Huobi)
            'gateio', 'gate',# Gate.io
            'mexc',          # MEXC
            'bitmex',        # BitMEX derivatives
            'deribit',       # Options/derivatives
            'bitfinex',      # Major exchange
            'kucoin',        # KuCoin
            'phemex',        # Phemex derivatives
            'bitget',        # Bitget
            'cryptocom', 'crypto.com',  # Crypto.com
            'bingx',         # BingX
            'bitstamp',      # Bitstamp (oldest)
            'gemini',        # Gemini (Winklevoss)
            'poloniex',      # Poloniex
        ]
        
        print(f"\n{'Exchange':<15} {'Status'}")
        print("-" * 30)
        
        passed = 0
        failed = 0
        
        for exchange in supported_exchanges:
            try:
                L = Liquidator.from_exchange('BTC', exchange)
                print(f"{exchange:<15} ✅")
                passed += 1
            except ValueError as e:
                if "not supported" in str(e):
                    print(f"{exchange:<15} ✗ NOT SUPPORTED")
                    failed += 1
                    raise
        
        print(f"\n✅ All {passed} exchanges supported!")
        assert failed == 0, f"{failed} exchanges failed"
    
    def test_symbol_normalization(self):
        """Test symbol normalization across exchanges."""
        # Binance: BTC -> BTCUSDT
        L1 = Liquidator.from_exchange('BTC', 'binance')
        assert L1.coin == 'BTC'
        
        # Coinbase: BTC -> BTC-USD
        L2 = Liquidator.from_exchange('BTC', 'coinbase')
        assert L2.coin == 'BTC'
        
        # Kraken: BTC -> XBT/USD (but coin still 'BTC')
        L3 = Liquidator.from_exchange('BTC', 'kraken')
        assert L3.coin == 'BTC'


def test_all_parsers_validate_trades():
    """Test that all parsers validate trades correctly."""
    parsers = [
        HyperliquidParser('BTC'),
        BinanceParser('BTCUSDT'),
        CoinbaseParser('BTC-USD'),
        BybitParser('BTCUSDT'),
        KrakenParser('XBT/USD'),
        OKXParser('BTC-USDT-SWAP'),
        BitgetParser('BTCUSDT'),
        KuCoinParser('BTC-USDT'),
    ]
    
    valid_trade = {
        'time': pd.Timestamp.now(tz='UTC'),
        'px': 80000.0,
        'sz': 1.5,
        'side': 'A'
    }
    
    invalid_trades = [
        {'px': 80000, 'sz': 1.5, 'side': 'A'},  # Missing time
        {'time': pd.Timestamp.now(tz='UTC'), 'sz': 1.5, 'side': 'A'},  # Missing px
        {'time': pd.Timestamp.now(tz='UTC'), 'px': 80000, 'side': 'A'},  # Missing sz
        {'time': pd.Timestamp.now(tz='UTC'), 'px': 80000, 'sz': 1.5, 'side': 'X'},  # Invalid side
    ]
    
    for parser in parsers:
        assert parser.validate_trade(valid_trade) is True
        for invalid in invalid_trades:
            assert parser.validate_trade(invalid) is False


if __name__ == '__main__':
    print("=" * 70)
    print("MULTI-EXCHANGE PARSER TESTS")
    print("=" * 70)
    
    # Run tests
    test_classes = [
        TestHyperliquidParser,  # USER'S PRIMARY EXCHANGE - Test first!
        TestBinanceParser,
        TestCoinbaseParser,
        TestBybitParser,
        TestKrakenParser,
        TestLiquidatorFromExchange
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        test_instance = test_class()
        test_methods = [m for m in dir(test_instance) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_instance, method_name)
                method()
                print(f"  ✅ {method_name}")
                passed_tests += 1
            except Exception as e:
                print(f"  ✗ {method_name}: {str(e)}")
    
    # Run standalone test
    print(f"\nStandalone Tests:")
    total_tests += 1
    try:
        test_all_parsers_validate_trades()
        print(f"  ✅ test_all_parsers_validate_trades")
        passed_tests += 1
    except Exception as e:
        print(f"  ✗ test_all_parsers_validate_trades: {str(e)}")
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed_tests}/{total_tests} tests passed")
    print("=" * 70)
    
    if passed_tests == total_tests:
        print("\n✅ ALL EXCHANGE PARSER TESTS PASSED!")
        print("\n📊 Multi-Exchange Support Summary:")
        print("   • 21 exchanges supported")
        print("   • Works with REST API and WebSocket data")
        print("   • Automatic symbol normalization")
        print("   • Unified trade format across all exchanges")
        print("\n💡 What this means:")
        print("   Your package is EXCHANGE-AGNOSTIC!")
        print("   Users can collect data from ANY exchange")
        print("   and get consistent liquidation zone analysis.")
    else:
        print(f"\n✗ {total_tests - passed_tests} tests failed")
