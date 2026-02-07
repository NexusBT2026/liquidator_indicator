# Release Notes — v0.0.8

Released: 2026-02-05

Summary
-------
Version 0.0.8 contains the real-liquidation data validation feature, integration of multiple new collectors, important bug fixes, and packaging/security improvements. This release focuses on production readiness, test coverage, and ensuring we do not ship development artifacts to PyPI.

Highlights
----------
- 8 verified, working liquidation collectors: Binance, Bybit, OKX, BitMEX, Deribit, HTX (Huobi), Phemex, MEXC.
- Removed 3 non-working collectors from the package: Gate.io, KuCoin, Bitfinex.
- Live verification: 686 liquidations captured in a 60-second live test (approx. $12.9M USD total liquidation value).
- Cross-exchange cascade detection and validation: zones validated across exchanges receive a quality score boost (up to +30%).
- OKX parsing bug fixed (data['data'] vs data['data']['details']).
- Replaced deprecated pandas calls (pd.Timestamp.utcnow() → pd.Timestamp.now('UTC')) in multiple locations.
- Removed a deprecated scikit-learn parameter to eliminate FutureWarning.
- Created a v0.0.8 compatibility test suite (12 tests) to confirm backward compatibility with v0.0.7 features.
- Added `MANIFEST.in` to control package distribution; test/debug files and internal docs are excluded from PyPI.

Testing & Quality
-----------------
- Unit tests: 61/61 passing locally.
- v0.0.8 compatibility tests: 12/12 passing.
- Zero deprecation warnings in test output (previously ~1454 warnings).
- PyLint score: 9.98/10.

Packaging & Distribution
------------------------
- Package published to PyPI: `liquidator-indicator` v0.0.8
- `MANIFEST.in` added to ensure only user-facing files are included in releases.

Notes on Removed Collectors
---------------------------
- Gate.io: requires private API key authentication — removed from default distribution.
- KuCoin: filter logic incompatible with live liquidation data — removed to avoid false positives.
- Bitfinex: symbol format/market access issues — removed until corrected.

Migration & Upgrade
-------------------
- Users upgrading from v0.0.7 to v0.0.8 should expect the package to behave the same for core `Liquidator` functionality; additional real-liquidation validation features are optional and require running the `MultiExchangeLiquidationCollector` or individual collectors.

Credits
-------
Thanks to contributors who assisted with live testing, debugging, and packaging improvements.

---

For full details and usage examples, see the documentation and examples directory in the repository on GitHub.