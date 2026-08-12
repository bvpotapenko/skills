# ML / DL / AI algorithms

ML code has properties that break naive testing: stochasticity, no exact oracle, expensive runs,
hardware (GPU) dependence, and "it ran" ≠ "it's correct". Line coverage is a **weak** signal here —
the **property tier** (`references/property-tests.md`) and **metric gates** are the real quality bar.
Default framework branch: **PyTorch**; scikit-learn and TF/JAX notes inline.

## Contents
1. Determinism (seed everything)
2. Tiny fixtures (small data, small models — keep tests in milliseconds)
3. Numerical assertions & tolerances
4. The canonical sanity tests (overfit a tiny batch; shapes/dtypes/devices; gradients)
5. Behavioral / metamorphic tests for models
6. Data-pipeline tests (transforms, datasets, loaders) + mocking heavy I/O
7. Metric gates (the "quality" sense for models)
8. sklearn / TF / JAX deltas

---

## 1. Determinism
Use the **autouse** seeding fixture from `assets/conftest.ml.py` so every ML test starts from a
fixed RNG state across `random`, `numpy`, and `torch` (+ cuda). It also sets deterministic algorithm
flags. This makes failures reproducible. (Recall the interaction with Hypothesis and *statistical*
property tests from `references/property-tests.md`: design stochastic functions to take an injected
`rng`; let Hypothesis own generated inputs.)

```python
# core of assets/conftest.ml.py
@pytest.fixture(autouse=True)
def _seed_everything():
    import os, random, numpy as np
    random.seed(0); np.random.seed(0); os.environ["PYTHONHASHSEED"] = "0"
    try:
        import torch
        torch.manual_seed(0)
        if torch.cuda.is_available(): torch.cuda.manual_seed_all(0)
        torch.use_deterministic_algorithms(True, warn_only=True)
    except ImportError:
        pass
    yield
```

## 2. Tiny fixtures — keep ML tests fast and CPU-only
Tests must run in milliseconds on CPU. Use **tiny** tensors and **tiny** models; never load real
checkpoints or full datasets in unit/property tests.

```python
import pytest, torch

@pytest.fixture
def batch():
    return torch.randn(4, 3, 8, 8)            # 4 tiny "images"

@pytest.fixture
def model():
    return torch.nn.Sequential(               # 2-layer toy net
        torch.nn.Flatten(), torch.nn.Linear(3*8*8, 16),
        torch.nn.ReLU(), torch.nn.Linear(16, 2),
    )
```

Mark anything that truly needs a GPU `@pytest.mark.gpu` and skip when unavailable:

```python
gpu = pytest.mark.skipif(not torch.cuda.is_available(), reason="no CUDA")
```

## 3. Numerical assertions & tolerances
Floats are never exactly equal — assert closeness with an explicit, justified tolerance:

```python
import torch
torch.testing.assert_close(out, expected, rtol=1e-4, atol=1e-6)
# numpy / sklearn:
import numpy as np
np.testing.assert_allclose(pred, expected, rtol=1e-5, atol=1e-8)
```

Pick tolerances from the operation's expected numerical error and dtype (fp16 needs looser than
fp64), not by loosening until green. For exact-by-construction quantities (counts, integer labels,
argmax indices) use exact equality.

## 4. Canonical sanity tests
These three catch the majority of "model code is wrong" bugs and belong in every model's suite:

**Shapes / dtypes / devices** (unit tier) — the contract of a forward pass:

```python
def test_forward_shape_dtype(model, batch):
    out = model(batch)
    assert out.shape == (4, 2)
    assert out.dtype == torch.float32
    assert not torch.isnan(out).any()         # no NaNs/Infs
```

**Overfit a tiny batch** (property tier) — a correct, trainable model can memorize a handful of
examples; if it can't, wiring/loss/optimizer is broken:

```python
def test_can_overfit_tiny_batch(model):
    x = torch.randn(8, 3, 8, 8)
    y = torch.randint(0, 2, (8,))
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    loss_fn = torch.nn.CrossEntropyLoss()
    losses = []
    for _ in range(200):
        opt.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward(); opt.step()
        losses.append(loss.item())
    assert losses[-1] < 0.05                   # learned the tiny set
    assert losses[-1] < losses[0]              # and loss actually went down
```

**Gradients flow** (unit/property tier) — every trainable parameter gets a finite, non-zero-by-bug
gradient:

```python
def test_all_params_get_gradients(model, batch):
    out = model(batch).sum()
    out.backward()
    for name, p in model.named_parameters():
        assert p.grad is not None, f"{name} has no grad (detached?)"
        assert torch.isfinite(p.grad).all(), f"{name} grad has NaN/Inf"
```

(For custom autograd functions, use `torch.autograd.gradcheck` against numerical gradients.)
A **single-train-step** test (loss decreases after one `opt.step()`) is a good fast smoke test too.

## 5. Behavioral / metamorphic tests for models
This is the property tier applied to models — assert relations you expect, with no exact oracle:

- **Invariance**: an augmentation that shouldn't change the prediction doesn't (within tolerance) —
  e.g. a normalization-invariant model gives the same logits for `x` and `x` after an
  identity-preserving transform; flipping inputs the model is meant to be invariant to.
- **Equivariance**: transforming the input transforms the output predictably (rotate the input →
  segmentation mask rotates the same way).
- **Directional expectation**: increasing a feature a monotone model depends on doesn't *decrease*
  the score; adding signal increases confidence.
- **Determinism in eval**: `model.eval()` + same input → identical output across two calls (catches
  stray dropout/BN-in-train bugs):

```python
def test_eval_is_deterministic(model, batch):
    model.eval()
    with torch.no_grad():
        a, b = model(batch), model(batch)
    torch.testing.assert_close(a, b)
```

## 6. Data pipeline: transforms, datasets, loaders
The pipeline is ordinary code with real correctness properties — test it hard, mock the heavy I/O.

- **Transforms** (unit + property): output shape/dtype/range correct; a `Normalize` actually yields
  ~zero mean/unit std on known input; augmentations are **stochastic but bounded** (use the
  statistical sub-tier: over many calls a random crop covers the image roughly uniformly and never
  goes out of bounds — exactly the "is it actually random" pattern).
- **Dataset** (unit): `__len__` correct; `__getitem__` returns the right tuple/types; index bounds
  raise; **mock disk reads** — patch the file/image loader (`mocker.patch("pkg.data.read_image",
  return_value=fake_array)`) so no real files are touched. Use `tmp_path` to lay down tiny fixture
  files when you must read real ones.
- **DataLoader** (integration): batching/collation shape is right; with a seeded generator,
  shuffling is reproducible; a custom `collate_fn` handles ragged inputs. Keep `num_workers=0` in
  tests for determinism and speed.
- **Splits/leakage** (property): train/val/test are disjoint (assert empty index intersection) — a
  cheap test that prevents a catastrophic bug.

## 7. Metric gates (the "quality" sense for trained models)
For pipelines that train/evaluate, gate on a **metric threshold** on a fixed tiny eval set, and/or a
**no-regression** check vs a stored baseline. This is the model-quality analogue of a coverage gate.

```python
def test_meets_accuracy_floor(trained_tiny_model, eval_set):
    acc = evaluate(trained_tiny_model, eval_set)
    assert acc >= 0.80, f"accuracy regressed to {acc:.3f}"

def test_no_metric_regression(metrics, baseline):           # baseline loaded from a committed json
    assert metrics["f1"] >= baseline["f1"] - 0.01           # small tolerance band
```

Keep these on a **tiny, fixed** dataset so they're fast and deterministic; run full-scale evals
separately (not in the unit suite). Mark slow/full evals `@pytest.mark.slow` and exclude from the
inner loop. Because coverage % is a weak proxy for model code, **these metric and behavioral tests —
not the coverage number — are what "quality" means for ML**; the tier floor (75) is a safety net,
not the goal.

## 8. sklearn / TF / JAX deltas
- **scikit-learn**: pass `random_state=0` to every estimator/split; assert `fit`→`predict` shapes,
  that `predict_proba` rows sum to 1 (property), that a pipeline overfits a tiny separable set, and
  metric floors via `sklearn.metrics`. No autograd; the overfit/metric/behavioral tests still apply.
- **TensorFlow/Keras**: seed with `tf.keras.utils.set_random_seed(0)` and
  `tf.config.experimental.enable_op_determinism()`; test `model(x)` shapes/dtypes, a one-step
  `train_on_batch` loss decrease, and `model.evaluate` floors. Use `assert_allclose` on `.numpy()`.
- **JAX**: thread an explicit `key = jax.random.PRNGKey(0)` (JAX has no global RNG — injection is
  mandatory, which suits this skill); test `jax.numpy` outputs with `np.testing.assert_allclose`;
  for gradients, `jax.test_util.check_grads`. `jit` a function and assert it matches the un-jitted
  result (a built-in metamorphic check).

## Tiers & coverage summary
- **unit**: shapes/dtypes/devices, gradient existence, transform/dataset contracts (I/O mocked).
- **property**: overfit-tiny-batch, eval determinism, invariance/equivariance/directional,
  augmentation distribution (statistical), split disjointness, jit-vs-eager.
- **integration**: dataloader→model→loss wired end-to-end on tiny data; a full mini training step.
- Coverage tier: **75** line floor as a safety net — invest effort in the property/metric tests, not
  in chasing the percentage.
