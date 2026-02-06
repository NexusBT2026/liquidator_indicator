"""
Quick fix for using liquidator-indicator with older NumPy versions.

If your project uses NumPy 1.16-1.19, you have 2 options:
"""

print("=" * 70)
print("SOLUTION 1: Install Without Numba (Simplest)")
print("=" * 70)
print("""
In your terminal:

    pip install --no-deps liquidator-indicator
    pip install "pandas>=1.3.0"
    # Keep your existing numpy 1.16

This installs liquidator-indicator without touching your NumPy version.
- Works perfectly with NumPy 1.16+
- Pure Python mode (no JIT compilation)
- Still fast enough for most use cases
- 3x slower than with numba, but stable and reliable
""")

print("=" * 70)
print("SOLUTION 2: Virtual Environment (Best Performance)")
print("=" * 70)
print("""
Create an isolated environment:

    # Create new environment
    python -m venv liquidator_env
    
    # Activate it
    # Windows:
    liquidator_env\\Scripts\\activate
    # Linux/Mac:
    source liquidator_env/bin/activate
    
    # Install with all optimizations
    pip install liquidator-indicator
    
    # Use this environment when you need zones
    python your_liquidator_script.py

Your main project stays at NumPy 1.16, this environment uses NumPy 1.20+
""")

print("=" * 70)
print("SOLUTION 3: Hybrid Approach (Programmatic)")
print("=" * 70)
print("""
Call liquidator-indicator as subprocess from your main app:

    # In your NumPy 1.16 project:
    import subprocess
    import json
    
    # Prepare data
    trades_json = json.dumps(your_trades_data)
    
    # Call liquidator in separate environment
    result = subprocess.run(
        ['path/to/liquidator_env/python', 'compute_zones.py'],
        input=trades_json,
        capture_output=True,
        text=True
    )
    
    # Get zones back
    zones = json.loads(result.stdout)

Keeps dependencies completely isolated!
""")

print("=" * 70)
print("TEST YOUR CURRENT SETUP")
print("=" * 70)

try:
    import numpy as np
    import pandas as pd
    
    print(f"✅ NumPy version: {np.__version__}")
    print(f"✅ Pandas version: {pd.__version__}")
    
    # Try importing liquidator
    try:
        from liquidator_indicator import Liquidator
        import liquidator_indicator.core as core
        
        print(f"✅ liquidator-indicator: Installed")
        print(f"   Numba optimizations: {'Enabled' if core.NUMBA_AVAILABLE else 'Disabled (Pure Python)'}")
        
        # Quick test
        import pandas as pd
        now = pd.Timestamp.now(tz='UTC')
        test_trades = [
            {'time': now, 'px': 80000, 'sz': 1.0, 'side': 'A'},
            {'time': now, 'px': 80010, 'sz': 0.5, 'side': 'B'},
        ]
        
        L = Liquidator('BTC')
        L.ingest_trades(test_trades)
        zones = L.compute_zones()
        
        print(f"✅ Test successful: Found {len(zones)} zones")
        print("\n👍 Your setup is working! No changes needed.")
        
    except ImportError as e:
        print(f"❌ liquidator-indicator: Not installed")
        print(f"   Error: {e}")
        print("\n💡 Use SOLUTION 1 above to install")
        
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")

print("\n" + "=" * 70)
print("RECOMMENDATION")
print("=" * 70)

import sys
try:
    import numpy as np
    np_version = tuple(map(int, np.__version__.split('.')[:2]))
    
    if np_version < (1, 20):
        print(f"Your NumPy {np.__version__} is older than 1.20")
        print("👉 Use SOLUTION 1 (--no-deps) or SOLUTION 2 (venv)")
        print("   Both work perfectly with your version!")
    else:
        print(f"Your NumPy {np.__version__} is compatible!")
        print("👉 Standard install works: pip install liquidator-indicator")
except:
    print("Unable to detect NumPy version")
    print("👉 Try SOLUTION 1 for maximum compatibility")
