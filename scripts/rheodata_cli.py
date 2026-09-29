"""Fallback CLI wrapper: uses the repo's rheodata package when it is not installed.

Same flags as the installed ``rheodata`` console script.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rheodata.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
