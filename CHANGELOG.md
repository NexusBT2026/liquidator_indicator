# Changelog

All notable changes to **liquidator_indicator** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.8] - 2026-02-05

### Added
- **3 New Exchange Liquidation Collectors** (verified working):
  - HTX (Huobi) - REST API polling (495 liquidations captured in live test)
  - Phemex - REST API polling (27 liquidations captured in live test)
  - MEXC - REST API polling (145 liquidations captured in live test)
- **Package Security**:
  - MANIFEST.in for controlled distribution (excludes test/debug files)
  - Clean professional package on PyPI
- **Comprehensive Testing**:
  - 12 v0.0.8 backward compatibility tests (100% passing)
  - Live integration test suite (686 liquidations captured)
  - 61 total unit tests (all passing, zero warnings)

### Removed
- **3 Non-Working Exchange Collectors**:
  - Gate.io (requires private API key authentication)
  - KuCoin (filter incompatible with liquidation data)
  - Bitfinex (symbol format/market access issues)
- **Final Working Collectors**: 8 exchanges (Binance, Bybit, OKX, BitMEX, Deribit, HTX, Phemex, MEXC)

### Fixed
- **OKX Liquidation Parsing**: Corrected data structure access (data['data'] vs data['data']['details'])
- **Pandas Deprecation Warnings**: Replaced pd.Timestamp.utcnow() with pd.Timestamp.now('UTC') (5 locations)
- **scikit-learn FutureWarning**: Removed deprecated penalty='l2' parameter from LogisticRegression
- **Test Suite**: Fixed pytest.mark.skipif decorator issue in Binance collector test

### Changed
- **Code Quality**: Zero deprecated warnings (eliminated 1454+ warnings from v0.0.7)
- **Live Verification**: All 8 working collectors validated with real liquidation data
- **Documentation**:
  - LIQUIDATION_COLLECTORS_GUIDE.md (430 lines)
  - LIQUIDATION_COLLECTORS_EXPANSION.md (technical summary)
  - Multi-exchange example scripts

### Changed
- **Code Quality Improvements** (thanks @arosstale):
  - 6 exception handling fixes (specific types + chaining)
  - 3 unused variable removals
  - 1 unused import removal
  - PyLint score: 9.79 → 9.98
- Updated `ingest_trades()` with backward compatibility for old data formats
- Improved error messages with better exception types

### Fixed
- Backward compatibility with `usd_value` column (pre-v0.0.7 format)
- Test data cutoff_hours filtering (added `cutoff_hours=None` for old test data)
- Coin column assignment logic in trade ingestion
- Callback assertions in streaming mode tests

### Security
- Added exception chaining for better error traceability
- Improved input validation with specific exception types
- Removed broad `except Exception` catches (6 instances)

## [0.0.7] - 2026-01-15

### Added
- **Machine Learning Predictions** (Priority 6 feature):
  - MLPredictor class with Random Forest + Logistic Regression
  - 8-feature zone analysis (strength, recency, volume, etc.)
  - Zone lifecycle tracking (hold/break predictions)
  - Model persistence and retraining
  - Synthetic data generation for training
- **Streaming Mode Support**:
  - Event-driven architecture with callbacks
  - Real-time zone detection (zone_formed, zone_updated, zone_broken)
  - Incremental zone tracking without recomputation
- **Advanced Visualizations**:
  - Interactive Plotly charts with quality color-coding
  - TradingView Pine Script export
  - Multi-timeframe analysis plots
- **Enhanced Quality Scoring**:
  - ML-based predictions integrated into quality scores
  - Confidence levels (0-100 scale)
  - Touch count tracking for zone validation

### Changed
- Refactored compute_zones() for ML integration
- Enhanced zone history tracking (last 20 measurements)
- Improved multi-timeframe alignment scoring

### Performance
- ML predictions: ~100ms for 50 zones
- Streaming mode: <10ms zone updates
- Model training: ~2s on 1000 zones

## [0.0.6] - 2025-12-20

### Added
- **Multi-Timeframe Analysis** (Priority 5 feature):
  - Support for 15 timeframes (1m to 1M)
  - Alignment score (0-100) based on cross-timeframe confluence
  - Configurable timeframe selection
- **Funding Rate Integration**:
  - Extreme funding detection (>0.1% = liquidation risk)
  - Open Interest drop analysis (>5% = active liquidations)
  - 1.5-2x weight multiplier for high-confidence patterns
- **Exchange Parser Expansion**:
  - Added 21 total exchanges (Hyperliquid, Binance, Coinbase, etc.)
  - Unified parser interface
  - Symbol normalization across exchanges

### Changed
- Enhanced liquidation inference with funding/OI signals
- Improved zone merging logic (3-pass algorithm)

### Fixed
- UTC timestamp handling across all parsers
- Symbol normalization edge cases

## [0.0.5] - 2025-11-10

### Added
- **ATR-Based Dynamic Bands** (Priority 4 feature):
  - Automatic band width calculation using ATR
  - Volatility-adjusted entry/exit levels
  - `use_atr=True` parameter in compute_zones()
- **Zone Quality System**:
  - 3-tier labels: strong (70-100), medium (40-70), weak (0-40)
  - 10-factor quality scoring algorithm
  - `min_quality` filtering option

### Changed
- Default band calculation now uses ATR when candles available
- Quality scores normalized to 0-100 scale

### Performance
- Numba-optimized ATR calculation: 3x faster
- Band computation: O(n) time complexity

## [0.0.4] - 2025-10-01

### Added
- **Numba Optimization** (Priority 3 feature):
  - JIT compilation for clustering algorithm
  - 3x speedup: 150k trades/sec → 454k trades/sec
  - Optional fallback to pure Python
- **Candle Data Support**:
  - `ingest_candles()` method for OHLCV data
  - ATR computation from candle data
  - Volatility-aware zone detection

### Changed
- Refactored clustering to support numba @jit
- Enhanced zone strength calculation with recency weighting

### Performance
- Clustering: 454k trades/sec with numba
- Memory: <50MB for 100k trades

## [0.0.3] - 2025-09-15

### Added
- **Enhanced Zone Detection** (Priority 2 feature):
  - Side-aware clustering (long vs short zones)
  - Volume-weighted zone strength
  - Time decay for recency scoring
- **Visual Output**:
  - ASCII visualization of zones
  - Entry/exit level display
  - Quality indicators

### Changed
- Improved merge threshold (0.3% default)
- Better handling of overlapping zones

### Fixed
- Edge case: empty trade data
- Edge case: single-trade zones

## [0.0.2] - 2025-08-20

### Added
- **Core Liquidation Inference** (Priority 1 feature):
  - Pattern 1: Large volume sell/buy clusters
  - Pattern 2: Repeated sells at same price
  - Configurable thresholds (size, merge %)
- **Zone Clustering**:
  - 3-pass merge algorithm
  - Price-based grouping (0.3% tolerance)
  - Volume aggregation

### Changed
- Renamed from `liquidation_detector` to `liquidator_indicator`
- Improved trade data ingestion

## [0.0.1] - 2025-08-01

### Added
- Initial release
- Basic trade data parser
- Simple liquidation detection
- Minimal documentation

---

## Legend

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements
- **Performance**: Performance enhancements

## Upgrade Guide

### 0.0.7 → 0.0.8
- No breaking changes
- New liquidation collectors are optional
- Old trade format (`usd_value`) still supported
- Add `cutoff_hours=None` to tests with old data

### 0.0.6 → 0.0.7
- No breaking changes
- ML predictions are opt-in (`enable_ml_predictions()`)
- Streaming mode requires callback registration

### 0.0.5 → 0.0.6
- No breaking changes
- Multi-timeframe analysis is new method (`compute_multi_timeframe_zones()`)

### 0.0.4 → 0.0.5
- `use_atr` parameter added (defaults to True when candles available)
- `min_quality` parameter added for zone filtering

### 0.0.3 → 0.0.4
- Numba is optional dependency (install: `pip install numba`)
- No breaking changes if numba unavailable

## Contributors

- @NexusBT2026 - Core development
- @arosstale - Code quality review & improvements
- Community contributors - Testing & feedback

---

**Repository:** https://github.com/NexusBT2026/liquidator_indicator  
**PyPI:** https://pypi.org/project/liquidator-indicator/  
**License:** MIT
