# The property tier — property-based, metamorphic & statistical testing

This is the "quality" tier: tests that the output is **actually correct / well-behaved**, not just
the right type or shape. A unit test says *"a rotated image came back"*; a property test says *"the
rotation is actually random"*, or *"rotating then un-rotating gives back the original"*. Use this
tier whenever a function is stochastic, numeric, or has correctness properties an exact-value
assertion can't capture (most ML/AI/DL and scientific code).

Established names (use these when searching/discussing): **property-based testing**, **metamorphic
testing**, **statistical / distributional testing**; in ML, **behavioral testing** (the CheckList
taxonomy: invariance, directional expectation, minimum functionality).

These tests live in `tests/property/` (auto-marked `@pytest.mark.property`).

## Contents
1. When each sub-kind applies
2. Property-based (Hypothesis)
3. Metamorphic relations
4. Statistical / distributional (the "is it actually random" case)
5. The Hypothesis × seeding interaction (important)
6. Worked example: random image rotation (full code)

---

## 1. Which sub-kind?

- You can state an **invariant true for all inputs** → property-based (Hypothesis generates inputs).
  *"For any image, the output has the same dtype and a valid shape."*
- You have **no exact oracle** but know how outputs **relate** to transformed inputs → metamorphic.
  *"rotate by a then by b == rotate by a+b"; "scaling all features by k scales the score by k"*.
- The function is **stochastic** and correctness is about the **distribution over many runs** →
  statistical. *"random angles are uniform on [0,360) and not constant"; "the sampler's mean ≈ μ"*.

Most real components want **two or three** of these. The rotation example below uses all three.

---

## 2. Property-based testing with Hypothesis

Hypothesis generates many inputs (and *shrinks* failures to a minimal reproducer). You assert a
property that must hold for all of them.

```python
from hypothesis import given, strategies as st
import numpy as np
from hypothesis.extra import numpy as hnp

@given(hnp.arrays(dtype=np.uint8,
                  shape=hnp.array_shapes(min_dims=2, max_dims=2, min_side=1, max_side=64)))
def test_rotate_preserves_dtype_and_shape_for_any_image(img):
    out = rotate90(img)                       # rotate by a multiple of 90°
    assert out.dtype == img.dtype             # invariant: dtype preserved
    assert sorted(out.shape) == sorted(img.shape)  # 90° rotation transposes dims

@given(st.lists(st.integers()))
def test_encode_decode_roundtrip(xs):
    assert decode(encode(xs)) == xs           # classic roundtrip property
```

Tips:
- Keep examples bounded (`max_side`, `max_size`) so generation is fast.
- Use `@example(...)` to pin known tricky inputs alongside generated ones.
- Tune effort with `@settings(max_examples=200, deadline=None)` — raise `max_examples` for critical
  invariants, set `deadline=None` for code with variable runtime (ML).
- Hypothesis is the **input-space** tool; combine it with metamorphic/statistical *assertions*
  inside the test body.

---

## 3. Metamorphic relations

When you can't compute the expected output directly, assert a **relation** between related runs.
Common families:

- **Invariance**: a transformation that *shouldn't* change the result doesn't (rotating an image
  shouldn't change a rotation-invariant classifier's label; reordering a set's elements doesn't
  change `summary(set)`).
- **Equivariance / composition**: `f(g(x)) == h(f(x))` (rotate∘rotate == rotate-by-sum;
  resize-then-rotate ≈ rotate-then-resize within tolerance).
- **Directional expectation**: a change moves the output in a known direction (adding a strong
  positive word raises sentiment; increasing a feature raises a monotone model's score).
- **Conservation**: a quantity is preserved (a 90° rotation preserves the pixel histogram and sum;
  a normalization keeps the total probability at 1).

```python
import numpy as np

def test_rotate_compose(img):
    # equivariance: rotating by 90 then 180 == rotating by 270
    a = rotate90(rotate90(rotate90(img)))      # 270
    b = rotate_k(img, k=3)                      # 270 directly
    np.testing.assert_array_equal(a, b)

def test_rotate_full_turn_is_identity(img):
    np.testing.assert_array_equal(rotate_k(img, k=4), img)   # 360° == identity

def test_rotate_conserves_histogram(img):
    out = rotate90(img)
    np.testing.assert_array_equal(np.bincount(out.ravel(), minlength=256),
                                  np.bincount(img.ravel(), minlength=256))
```

For float/interpolated outputs use a tolerance: `np.testing.assert_allclose(a, b, atol=..., rtol=...)`
(or `torch.testing.assert_close`), and pick the tolerance from the operation's expected numerical
error, not by loosening until it passes.

---

## 4. Statistical / distributional — "is it *actually* random"

For a stochastic function, draw many samples and assert the **distribution** matches intent. Two
assertions you almost always want together:

1. **It matches the target distribution** (goodness-of-fit).
2. **It is not degenerate** (not constant / not collapsed to one value) — a constant function passes
   "returns a rotated image" but must fail here.

Use `scipy.stats` for the test; choose by data type:
- discrete categories (angle ∈ {0,90,180,270}) → **chi-square** vs expected counts.
- continuous (angle ∈ [0,360)) → **Kolmogorov–Smirnov** vs a uniform CDF.

```python
import numpy as np
from scipy import stats

def test_random_rotation_angles_are_uniform_discrete():
    rng = np.random.default_rng(12345)         # seed the *test* for reproducibility (see §5)
    choices = np.array([0, 90, 180, 270])
    counts = np.zeros(4, dtype=int)
    N = 4000
    for _ in range(N):
        angle = sample_rotation_angle(rng)     # the stochastic function under test
        counts[np.where(choices == angle)[0][0]] += 1

    # not degenerate: every category appears
    assert (counts > 0).all(), f"angles collapsed to a subset: {counts}"
    # uniformity: chi-square goodness-of-fit against equal expected counts
    expected = np.full(4, N / 4)
    _, p = stats.chisquare(counts, expected)
    assert p > 0.001, f"angles not uniform (chi-square p={p:.4g}, counts={counts})"
```

```python
def test_random_rotation_angles_are_uniform_continuous():
    rng = np.random.default_rng(2024)
    samples = np.array([sample_angle_continuous(rng) for _ in range(5000)])
    assert samples.std() > 1.0                 # not constant
    # KS test against Uniform(0, 360)
    _, p = stats.kstest(samples, stats.uniform(loc=0, scale=360).cdf)
    assert p > 0.001, f"angles not uniform on [0,360): KS p={p:.4g}"
```

Guidance that keeps these tests trustworthy (not flaky):
- **Use a loose significance threshold** (`p > 0.001`, not `0.05`). With a correct distribution the
  p-value is ~Uniform(0,1), so a 0.05 gate fails ~5% of the time → flaky. `0.001` keeps the
  false-failure rate ~0.1% while still catching real bias.
- **Seed the test's RNG** (the harness RNG you pass in) so a pass/fail is reproducible; you're
  testing the *function's* randomness given a stream, not betting on luck. (The function should
  accept an injected `rng` — design for it; see §5.)
- **Use enough samples** that the test has power (a few thousand for 2–8 categories). Too few → can't
  detect bias; absurdly many → slow. Mark genuinely heavy ones `@pytest.mark.slow`.
- Pair distribution-match with a **degeneracy** assertion every time — that's the half that catches
  the "constant output" bug your unit test misses.
- For "two samples come from the same distribution" (e.g. augmentation didn't shift the data) use
  `stats.ks_2samp`; for independence/correlation use the appropriate `scipy.stats` test.

---

## 5. The Hypothesis × seeding interaction (read this)

The generic `seed` fixture and ML autouse seeding (see `assets/`) fix global RNG state for
reproducibility. That interacts with this tier in two ways you must handle deliberately:

- **Hypothesis manages its own input generation.** Don't reseed global RNG *inside* a `@given` test
  expecting it to control Hypothesis — it won't, and it can fight shrinking. Let Hypothesis own
  inputs; use `@settings`/`@seed` (Hypothesis's own `from hypothesis import seed`) for
  reproducibility of generated examples.
- **Statistical tests need a stream of randomness, but a *reproducible* one.** The clean pattern is
  to **inject an RNG** into the function under test and pass a seeded `np.random.default_rng(SEED)`
  from the test (as in §4). Then the test is fully reproducible *and* genuinely exercises the
  randomness. If the function instead reads a global RNG, an autouse `seed` fixture makes the test
  deterministic — acceptable, but injection is better and is the design the unit/property tiers
  reward. **Do not** leave a statistical test reading unseeded global randomness: it'll pass/fail by
  luck.

Bottom line: **design stochastic functions to take an `rng` parameter.** It makes unit tests
trivial (pass a stub), metamorphic tests controllable, and statistical tests reproducible.

---

## 6. Worked example

A complete, runnable mini-project lives in `examples/property_testing_rotation/`. It implements a
random-rotation function and shows the full split:

- **unit** (`tests/unit/`): "a rotated array of valid shape and dtype comes back", argument
  validation errors — fast, no statistics.
- **property** (`tests/property/`):
  - metamorphic: 360° == identity; compose rotations; histogram conserved,
  - property-based (Hypothesis): dtype/shape invariant for any input,
  - statistical: the chosen angles are uniform **and** not constant (the "actually random" check).

Read those files for copy-ready patterns; run them with `pytest examples/property_testing_rotation`.
