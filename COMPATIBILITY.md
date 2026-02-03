# Dependency Compatibility Guide

## Current Requirements

### Minimum Versions
- **Python:** >= 3.9
- **NumPy:** >= 1.20.0 (works with 1.20.x, 1.21.x, 1.22.x, 1.23.x, 1.24.x, 1.25.x, 1.26.x, 2.x)
- **Pandas:** >= 1.3.0 (works with 1.3.x, 1.4.x, 1.5.x, 2.x)
- **Numba:** >= 0.56.0 (optional - for performance boost)

### Tested Configurations
✅ Python 3.9 + NumPy 1.20 + Pandas 1.3  
✅ Python 3.10 + NumPy 1.23 + Pandas 1.5  
✅ Python 3.11 + NumPy 1.24 + Pandas 2.0  
✅ Python 3.12 + NumPy 1.26 + Pandas 2.3  

## Working with Older NumPy Versions

### If Your Project Uses NumPy < 1.20

The package uses these NumPy features:
- Basic array operations (available since NumPy 1.0)
- `to_numpy()` conversion (requires NumPy 1.16+)
- Float64 dtype operations
- Boolean indexing
- Basic statistics (mean, min, max, std)

**Likely compatible down to NumPy 1.16**, but not officially tested.

### If Your Project Uses NumPy 1.16-1.19

You have two options:

#### Option 1: Install Without Numba (Recommended)
```bash
pip install liquidator-indicator --no-deps
pip install pandas>=1.3.0 numpy>=1.16.0
```

This installs the package **without numba**, so:
- ✅ Works with your NumPy 1.16
- ✅ No dependency conflicts
- ⚠️ No JIT acceleration (uses pure Python fallback)
- ⚠️ ~3x slower on large datasets (still fast enough for most use cases)

#### Option 2: Upgrade NumPy in Virtual Environment
```bash
# Create isolated environment for liquidator-indicator
python -m venv liquidator_env
source liquidator_env/bin/activate  # Windows: liquidator_env\Scripts\activate

# Install with all optimizations
pip install liquidator-indicator
```

Keep your main project at NumPy 1.16, use this environment when you need liquidator zones.

## NumPy Version Matrix

| NumPy Version | liquidator-indicator | Numba Support | Status |
|---------------|---------------------|---------------|---------|
| 1.16.x        | ✅ Works (no numba) | ❌ No         | Manual install |
| 1.17-1.19.x   | ✅ Works (no numba) | ❌ No         | Manual install |
| 1.20-1.21.x   | ✅ Full support     | ✅ Yes        | Recommended |
| 1.22-1.24.x   | ✅ Full support     | ✅ Yes        | Recommended |
| 1.25-1.26.x   | ✅ Full support     | ✅ Yes        | Recommended |
| 2.0.x+        | ✅ Full support     | ✅ Yes        | Recommended |

## Pandas Version Matrix

| Pandas Version | liquidator-indicator | Notes |
|----------------|---------------------|-------|
| 1.0-1.2.x      | ⚠️ Untested         | May work, not guaranteed |
| 1.3.x+         | ✅ Full support     | Recommended minimum |
| 2.0.x+         | ✅ Full support     | Latest, recommended |

## Numba Compatibility

Numba has specific NumPy version requirements:

| Numba Version | NumPy Support | Python Support |
|---------------|---------------|----------------|
| 0.56.x        | 1.20-1.23     | 3.8-3.10       |
| 0.57.x        | 1.21-1.24     | 3.8-3.11       |
| 0.58.x        | 1.22-1.26     | 3.9-3.11       |
| 0.59.x+       | 1.22-1.26     | 3.9-3.12       |

**If you can't upgrade NumPy:** Skip numba, the package works fine without it!

## Installation Examples

### Standard Install (Latest Versions)
```bash
pip install liquidator-indicator
# Gets: pandas>=1.3, numpy>=1.20, numba>=0.56
```

### Install for Older NumPy Projects
```bash
# Without numba (works with NumPy 1.16+)
pip install --no-deps liquidator-indicator
pip install "pandas>=1.3.0" "numpy>=1.16.0"
```

### Install with Specific Versions
```bash
# If you need NumPy 1.20 specifically
pip install liquidator-indicator numpy==1.20.3
```

### Upgrade Existing Installation
```bash
# Upgrade everything
pip install --upgrade liquidator-indicator

# Upgrade but keep your NumPy version
pip install --upgrade --no-deps liquidator-indicator
```

## Checking Your Installation

```python
import sys
import numpy as np
import pandas as pd

print(f"Python: {sys.version}")
print(f"NumPy: {np.__version__}")
print(f"Pandas: {pd.__version__}")

try:
    import numba
    print(f"Numba: {numba.__version__} ✅")
except ImportError:
    print("Numba: Not installed (pure Python fallback) ⚠️")

# Check if liquidator-indicator works
from liquidator_indicator import Liquidator
import liquidator_indicator.core as core

print(f"Numba optimizations: {'Enabled ✅' if core.NUMBA_AVAILABLE else 'Disabled (Python fallback) ⚠️'}")

# Test it
L = Liquidator('BTC')
print("liquidator-indicator: Working! ✅")
```

## Troubleshooting

### "Cannot install liquidator-indicator due to numpy conflict"
```bash
# Install without automatic dependency resolution
pip install --no-deps liquidator-indicator
pip install pandas>=1.3.0  # Uses your existing numpy
```

### "Numba requires numpy>=1.20"
```bash
# Either upgrade numpy
pip install --upgrade numpy

# Or skip numba
pip uninstall numba
# Package still works, just slower on large datasets
```

### "Module 'numpy' has no attribute 'X'"
Your NumPy version is too old. Minimum tested is 1.20.0.

```bash
pip install --upgrade numpy>=1.20.0
```

## Performance Impact Without Numba

| Dataset Size | With Numba | Without Numba | Difference |
|--------------|------------|---------------|------------|
| 100 trades   | ~5ms       | ~15ms         | 3x slower  |
| 500 trades   | ~12ms      | ~35ms         | 3x slower  |
| 2000 trades  | ~23ms      | ~69ms         | 3x slower  |

**Still plenty fast** for most trading applications, even without numba!

## Recommendations

### For New Projects
- Use latest stable versions: `pip install liquidator-indicator`
- Get full performance benefits

### For Existing Projects with Old NumPy
1. **Best:** Create virtual environment with newer versions
2. **Good:** Install without numba using `--no-deps`
3. **Works:** Upgrade numpy in your project (if possible)

### For Production Systems
- Pin all versions after testing:
  ```bash
  pip freeze > requirements.txt
  ```
- Test thoroughly with your specific numpy version

## Future Compatibility

We aim to support:
- **NumPy:** 1.20.x through 2.x
- **Pandas:** 1.3.x through 2.x+
- **Python:** 3.9 through 3.12+

Older versions may work but are not officially tested or supported.

## Contact

If you encounter compatibility issues with specific versions, please open an issue on GitHub with:
- Your Python version
- Your NumPy version
- Your Pandas version  
- Error message/traceback

We'll work to improve compatibility where possible!
