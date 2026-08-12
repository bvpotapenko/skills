"""Auto-mark tests by their directory (unit / property / integration).

A test in tests/unit/ gets @pytest.mark.unit automatically; tests/property/ -> property; etc.
You never tag a test with its own tier — only cross-cutting markers (slow, gpu).
"""
import pytest

_TIER_DIRS = ("unit", "property", "integration")


def pytest_collection_modifyitems(config, items):
    for item in items:
        path = str(item.fspath).replace("\\", "/")
        for tier in _TIER_DIRS:
            if f"/tests/{tier}/" in path:
                item.add_marker(getattr(pytest.mark, tier))
                break
