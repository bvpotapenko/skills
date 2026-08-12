"""Root test config: tests/conftest.py

Provides:
  - auto-marking of tests by their directory (unit / property / integration), so you never
    annotate a test with its own tier — only add cross-cutting markers (slow, gpu, enable_socket).
  - a requestable `seed` fixture for reproducible randomness in a single test.
  - a place for shared fixtures.

Copy to <project>/tests/conftest.py and extend. For ML projects, also merge conftest.ml.py.
"""
from __future__ import annotations

import random

import pytest

# --- Auto-mark tests by directory ------------------------------------------------------------
# A test in tests/unit/ gets @pytest.mark.unit automatically, etc. Keeps the dir split and the
# marker split in sync with zero per-test boilerplate. (Decision point: dirs + markers.)
_TIER_DIRS = ("unit", "property", "integration")


def pytest_collection_modifyitems(config, items):
    for item in items:
        path = str(item.fspath).replace("\\", "/")
        for tier in _TIER_DIRS:
            if f"/tests/{tier}/" in path:
                item.add_marker(getattr(pytest.mark, tier))
                break


# --- Reproducible randomness for a single test -----------------------------------------------
# Request `seed` to fix Python + numpy global RNG state for that test only. Prefer *injecting* an
# rng into the code under test where you can (see references/property-tests.md) — this fixture is
# for code that reads global RNG. NOT autouse here (it is autouse only in the ML conftest).
@pytest.fixture
def seed():
    s = 0
    random.seed(s)
    try:
        import numpy as np

        np.random.seed(s)
    except ImportError:
        pass
    return s


# --- Example shared fixtures (delete/replace) ------------------------------------------------
# @pytest.fixture
# def make_user():
#     created = []
#     def _make(name, **kw):
#         u = {"id": len(created) + 1, "name": name, **kw}
#         created.append(u)
#         return u
#     return _make
