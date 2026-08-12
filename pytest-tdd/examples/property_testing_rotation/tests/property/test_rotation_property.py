"""Property tier ("quality"): is the output *actually correct / behaved*?

Three sub-kinds, all here:
  - metamorphic  : relations that must hold (360 == identity, compose, histogram conserved)
  - property-based (Hypothesis): invariants over any input (dtype/shape preserved; valid rotation)
  - statistical  : the rotation is *actually random* (uniform angles, and not constant)
"""
import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp
from scipy import stats

from rotation import ANGLES, random_rotate, rotate_k, sample_rotation_angle


@pytest.fixture
def image():
    return np.arange(12, dtype=np.uint8).reshape(3, 4)


# --- metamorphic -----------------------------------------------------------------------------
def test_full_turn_is_identity(image):
    np.testing.assert_array_equal(rotate_k(image, 4), image)  # 360 deg == identity


def test_three_quarter_turns_compose(image):
    composed = rotate_k(rotate_k(rotate_k(image, 1), 1), 1)   # 90 + 90 + 90
    np.testing.assert_array_equal(composed, rotate_k(image, 3))  # == 270 directly


@pytest.mark.parametrize("k", [0, 1, 2, 3], ids=lambda k: f"k={k}")
def test_rotation_conserves_pixel_histogram(image, k):
    out = rotate_k(image, k)
    np.testing.assert_array_equal(
        np.bincount(out.ravel(), minlength=256),
        np.bincount(image.ravel(), minlength=256),
    )


# --- property-based (Hypothesis) -------------------------------------------------------------
_any_image = hnp.arrays(
    dtype=np.uint8,
    shape=hnp.array_shapes(min_dims=2, max_dims=2, min_side=1, max_side=16),
)


@settings(max_examples=150, deadline=None)
@given(img=_any_image, k=st.integers(min_value=0, max_value=8))
def test_rotate_k_preserves_dtype_and_shape_for_any_image(img, k):
    out = rotate_k(img, k)
    assert out.dtype == img.dtype
    assert sorted(out.shape) == sorted(img.shape)


@settings(max_examples=150, deadline=None)
@given(img=_any_image, seed=st.integers(min_value=0, max_value=2**32 - 1))
def test_random_rotate_output_is_one_of_the_four_rotations(img, seed):
    out = random_rotate(img, np.random.default_rng(seed))
    candidates = [rotate_k(img, k) for k in range(4)]
    assert any(out.shape == c.shape and np.array_equal(out, c) for c in candidates)


# --- statistical: "is the rotation ACTUALLY random?" -----------------------------------------
def test_sampled_angles_are_uniform_and_not_constant():
    rng = np.random.default_rng(12345)          # seed the harness -> reproducible pass/fail
    n = 4000
    counts = {a: 0 for a in ANGLES}
    for _ in range(n):
        counts[sample_rotation_angle(rng)] += 1

    observed = np.array([counts[a] for a in ANGLES])
    assert (observed > 0).all(), f"angles collapsed to a subset: {counts}"   # not degenerate
    _, p = stats.chisquare(observed, np.full(len(ANGLES), n / len(ANGLES)))
    assert p > 0.001, f"angles not uniform (chi-square p={p:.4g}, counts={counts})"


def test_statistical_test_has_power_to_catch_a_constant_sampler():
    """Sanity check on the test itself: a biased (constant) sampler must fail uniformity."""
    n = 4000
    observed = np.array([n, 0, 0, 0])           # a broken sampler that always returns 0 deg
    assert not (observed > 0).all()             # degeneracy check fires
    _, p = stats.chisquare(observed, np.full(4, n / 4))
    assert p < 0.001                            # uniformity check fires
