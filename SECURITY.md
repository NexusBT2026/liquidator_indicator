# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.0.8   | :white_check_mark: |
| 0.0.7   | :white_check_mark: |
| 0.0.6   | :x:                |
| < 0.0.6 | :x:                |

## Security Considerations

**liquidator_indicator** is a trading analysis tool that processes market data and generates trading signals. While it does **not** handle private keys, API keys, or execute trades directly, security is critical when integrating with trading systems.

### Key Security Practices

1. **API Key Management**
   - Never hardcode API keys in your code
   - Use environment variables or secure vaults
   - Restrict API permissions (read-only when possible)

2. **Data Validation**
   - All exchange data is validated before processing
   - Malformed data is rejected with specific exceptions
   - Input sanitization prevents injection attacks

3. **Dependencies**
   - All dependencies are well-maintained packages
   - Regular security audits of dependency versions
   - Numba optimization is optional (safe fallback available)

4. **Network Security**
   - WebSocket connections use WSS (secure)
   - REST API calls use HTTPS only
   - No credential transmission in liquidation collectors

## Reporting a Vulnerability

**DO NOT** open public issues for security vulnerabilities.

### How to Report

**Email:** security@nexusbt2026.com (or open a private security advisory on GitHub)

**Include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested fix (if available)

### Response Timeline

- **24 hours:** Initial acknowledgment
- **72 hours:** Severity assessment and action plan
- **7-14 days:** Patch development and testing
- **Release:** Security fix published with CVE (if applicable)

### Disclosure Policy

- Reporters receive credit in release notes (if desired)
- Public disclosure after patch is released
- Coordinated disclosure with affected users

## Security Best Practices for Users

### 1. Production Deployment
```python
# ✅ GOOD: Use environment variables
import os
api_key = os.getenv('EXCHANGE_API_KEY')

# ❌ BAD: Hardcoded credentials
api_key = "sk_live_abc123..."  # NEVER DO THIS
```

### 2. Data Validation
```python
# ✅ GOOD: Validate external data
try:
    liq.ingest_trades(exchange_data)
except ValueError as e:
    logger.error(f"Invalid data: {e}")
    # Handle gracefully
```

### 3. Rate Limiting
```python
# ✅ GOOD: Respect exchange rate limits
collector = BinanceLiquidationCollector(
    symbols=['BTCUSDT'],
    poll_interval=10  # Don't hammer APIs
)
```

### 4. Error Handling
```python
# ✅ GOOD: Catch specific exceptions
try:
    zones = liq.compute_zones()
except (KeyError, ValueError) as e:
    # Handle expected errors
    pass
except Exception as e:
    # Log unexpected errors
    logger.exception("Unexpected error")
```

### 5. Network Isolation
- Run liquidation collectors in isolated environments
- Use firewalls to restrict outbound connections
- Monitor network traffic for anomalies

## Known Limitations

1. **Real-time Data Dependency**
   - Relies on public exchange APIs (availability not guaranteed)
   - WebSocket disconnections require reconnection logic
   - Historical data may have gaps

2. **Market Data Accuracy**
   - Inferred liquidations are estimates, not guaranteed
   - Cross-exchange timing differences exist
   - Volume calculations may vary by exchange

3. **Performance Constraints**
   - Large datasets require sufficient memory
   - Numba compilation may take time on first run
   - Multi-exchange collection increases CPU usage

## Security Audit History

| Date       | Auditor      | Scope                          | Status |
|------------|--------------|--------------------------------|--------|
| 2026-02-05 | @arosstale   | Code quality review (PyLint)   | ✅ Pass |
| 2026-01-15 | Internal     | Dependency audit               | ✅ Pass |
| 2025-12-20 | Internal     | Exception handling review      | ✅ Pass |

## Responsible Use

**liquidator_indicator** is a research and analysis tool. Users are responsible for:
- Compliance with local trading regulations
- Risk management in live trading
- Proper position sizing and stop losses
- Understanding leverage risks (40x+ is high risk)

**WARNING:** Cryptocurrency trading involves substantial risk of loss. Never trade with money you cannot afford to lose.

## Contact

- **General Questions:** GitHub Issues
- **Security Issues:** security@nexusbt2026.com (private)
- **Commercial Support:** support@nexusbt2026.com

---

**Last Updated:** February 5, 2026  
**Version:** 1.0
