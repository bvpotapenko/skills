# Worked example: random image rotation

Demonstrates the unit vs **property** ("quality") split on a stochastic image op.

- `src/rotation.py` — `random_rotate(img, rng)` applies a random 90° rotation; `sample_rotation_angle`
  is the stochastic core and takes an injectable RNG.
- `tests/unit/` — "a rotated image of valid shape/dtype is produced" + argument-validation error.
  Auto-marked `@pytest.mark.unit`.
- `tests/property/` — the quality tier, auto-marked `@pytest.mark.property`:
  - **metamorphic**: 360° == identity, three 90° turns compose to 270°, histogram conserved.
  - **property-based** (Hypothesis): dtype/shape preserved for any image; output is one of the four
    valid rotations.
  - **statistical**: the chosen angles are uniform (chi-square) and not constant — i.e. the rotation
    is *actually random* — plus a sanity test proving the statistical check catches a constant sampler.

Run it:

```bash
pip install numpy scipy hypothesis pytest
cd examples/property_testing_rotation
pytest                 # all tiers
pytest -m unit         # just unit
pytest -m property     # just the quality tier
```
