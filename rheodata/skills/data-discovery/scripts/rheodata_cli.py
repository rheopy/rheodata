#!/usr/bin/env python3
"""Fallback CLI wrapper for the rheodata data-discovery skill.

Use this when `rheodata` is not pip-installed: it adds the repository's package
directory to ``sys.path`` and forwards to the same CLI, so the flags are
identical to `rheodata <args>`.

    python scripts/rheodata_cli.py list
    python scripts/rheodata_cli.py search --material Carbopol
    python scripts/rheodata_cli.py info carbopol_940_1pct

Assumes this script lives in <repo>/rheodata/skills/data-discovery/scripts/.
"""

import os
import sys

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
# <repo>/rheodata/skills/data-discovery/scripts -> <repo>
REPO_ROOT = os.path.abspath(os.path.join(SKILL_DIR, "..", "..", "..", ".."))
if os.path.isdir(os.path.join(REPO_ROOT, "rheodata")):
    sys.path.insert(0, REPO_ROOT)

import rheodata.__main__  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(rheodata.__main__.main())
