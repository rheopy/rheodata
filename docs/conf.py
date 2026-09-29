# Sphinx configuration for the rheodata documentation.
#
# Standard Read the Docs setup: Sphinx + MyST (Markdown) + autodoc.
# Build locally with:  sphinx-build -b html docs docs/_build/html
#
# The dataset catalog pages (docs/datasets/*.md) are generated from the
# registry at the top of this file, so Read the Docs needs no extra build
# steps: `sphinx-build` alone is enough.
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# --- Generate dataset pages before the build ---------------------------------
# Non-fatal: if the package or registry is unavailable the docs still build.
try:
    import generate_dataset_pages  # noqa: E402

    _docs_dir = os.path.abspath(os.path.dirname(__file__))
    generate_dataset_pages.main(
        repo_root=os.path.dirname(_docs_dir),
        docs_dir=_docs_dir,
    )
except Exception as exc:  # noqa: BLE001
    print(f"[rheodata] dataset page generation skipped: {exc!r}")

# --- Project -------------------------------------------------------------------
project = "rheodata"
copyright = "2026, rheopy"
author = "rheopy"
release = "0.1.0"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# MyST: allow $...$ / $$...$$ math and ::: colon fences.
myst_enable_extensions = [
    "dollarmath",
    "colon_fence",
]

suppress_warnings = ["misc.highlighting_failure"]

# Don't document inherited / private members; keep API pages tight.
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "private-members": False,
    "show-inheritance": False,
}
