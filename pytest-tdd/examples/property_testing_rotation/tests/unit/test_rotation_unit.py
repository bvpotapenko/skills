"""Unit tier: does it run and return the right *type/shape*? (No statistics here.)

This is the level your description called the plain unit test: "a picture is produced".
"""
import numpy as np
import pytest

from rotation import random_rotate, rotate_k


@pytest.fixture
def image():
    # asymmetric on purpose so the four rotations are all distinct
    return np.arange(12, dtype=np.uint8).reshape(3, 4)


def test_random_rotate_returns_an_image_of_valid_shape_and_dtype(image):
    rng = np.random.default_rng(0)
    out = random_rotate(image, rng)
    assert isinstance(out, np.ndarray)
    assert out.dtype == image.dtype
    assert sorted(out.shape) == sorted(image.shape)  # 90-deg rotation may transpose dims


@pytest.mark.parametrize("k", [0, 1, 2, 3, 4, 5], ids=lambda k: f"k={k}")
def test_rotate_k_shape_for_square_is_unchanged(k):
    sq = np.zeros((4, 4), dtype=np.uint8)
    assert rotate_k(sq, k).shape == (4, 4)


def test_rotate_k_rejects_non_2d_image():
    with pytest.raises(ValueError, match="2D image"):
        rotate_k(np.zeros((2, 3, 3)), 1)
