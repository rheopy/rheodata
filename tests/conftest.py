"""Shared fixtures: headless matplotlib, fixture registry, real-datasets root."""
import matplotlib

matplotlib.use("Agg")

from pathlib import Path

import pytest

import rheodata.registry as reg

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixture_registry():
    """Validated registry built from tests/fixtures (dev fixtures)."""
    return reg.load_registry(FIXTURES_DIR)


@pytest.fixture(scope="session")
def real_registry():
    """Validated registry from the packaged datasets dir, or None if unpopulated."""
    root = reg._default_root()
    if root is None:
        return None
    if not any(d.is_dir() and not d.name.startswith((".", "_")) for d in root.iterdir()):
        return None
    return reg.load_registry(root)


@pytest.fixture(scope="session", params=["fixtures", "real"])
def any_registry(request, fixture_registry, real_registry):
    """Each populated registry: fixtures always, real datasets when present."""
    if request.param == "real" and real_registry is None:
        pytest.skip("no curated datasets in rheodata/datasets yet")
    return fixture_registry if request.param == "fixtures" else real_registry
