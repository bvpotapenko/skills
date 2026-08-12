"""ML test config: merge into <project>/tests/conftest.py for ML/DL projects.

Adds full, autouse determinism (random / numpy / torch / cuda) and a couple of tiny fixtures.
See references/ml-dl.md. Note the Hypothesis / statistical-test interaction in
references/property-tests.md: let Hypothesis own generated inputs, and prefer injecting an `rng`
into stochastic code so statistical property tests stay reproducible *and* genuine.
"""
from __future__ import annotations

import os
import random

import pytest


@pytest.fixture(autouse=True)
def _seed_everything():
    """Fix all RNG state before each ML test so failures are reproducible."""
    random.seed(0)
    os.environ["PYTHONHASHSEED"] = "0"
    try:
        import numpy as np

        np.random.seed(0)
    except ImportError:
        pass
    try:
        import torch

        torch.manual_seed(0)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(0)
        # warn_only=True so ops without a deterministic impl don't hard-fail the suite.
        torch.use_deterministic_algorithms(True, warn_only=True)
    except ImportError:
        pass
    yield


# Skip marker for GPU-only tests.
def pytest_configure(config):
    config.addinivalue_line("markers", "gpu: requires CUDA; skipped when unavailable")


# --- Tiny fixtures (require torch; adapt to your framework) ----------------------------------
@pytest.fixture
def tiny_batch():
    import torch

    return torch.randn(4, 3, 8, 8)


@pytest.fixture
def tiny_model():
    import torch

    return torch.nn.Sequential(
        torch.nn.Flatten(),
        torch.nn.Linear(3 * 8 * 8, 16),
        torch.nn.ReLU(),
        torch.nn.Linear(16, 2),
    )
