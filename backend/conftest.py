"""Root conftest.py – adds the backend package directory to sys.path so that
all test modules can import application code without manual path manipulation.
"""

import sys
from pathlib import Path

# Insert the backend root (this file's directory) at the front of sys.path.
# This lets every test file do plain ``import main``, ``import config``, etc.
sys.path.insert(0, str(Path(__file__).parent))
