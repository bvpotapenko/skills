"""A tiny stochastic image op, used to demonstrate the unit vs property test split.

`random_rotate` takes an image and applies a random 90-degree multiple rotation.
The stochastic core (`sample_rotation_angle`) takes an injected RNG so that statistical
tests are reproducible *and* genuinely exercise the randomness (see the skill's
property-tests reference).
"""
from __future__ import annotations

import numpy as np

ANGLES: tuple[int, ...] = (0, 90, 180, 270)


def rotate_k(img, k: int):
    """Rotate a 2D image by k * 90 degrees counter-clockwise."""
    arr = np.asarray(img)
    if arr.ndim != 2:
        raise ValueError(f"expected a 2D image, got {arr.ndim}D")
    return np.rot90(arr, k % 4)


def sample_rotation_angle(rng=None) -> int:
    """Pick a rotation angle uniformly at random from ANGLES. RNG is injectable."""
    rng = np.random.default_rng() if rng is None else rng
    return int(rng.choice(ANGLES))


def random_rotate(img, rng=None):
    """Return `img` rotated by a uniformly random 90-degree multiple."""
    rng = np.random.default_rng() if rng is None else rng
    k = sample_rotation_angle(rng) // 90
    return rotate_k(img, k)
