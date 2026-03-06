import os
import sys

print("Python Executable:", sys.executable)
print("Python Version:", sys.version)
print("Current Working Directory:", os.getcwd())
print("Python Path:", sys.path)

# Detailed import diagnostics
try:
    import yaml
    print("✅ PyYAML imported successfully")
    print("PyYAML version:", yaml.__version__)
    print("PyYAML file location:", yaml.__file__)
except ImportError:
    print("❌ Standard import failed")
