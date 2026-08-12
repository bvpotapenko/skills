# Standalone libraries

A library's **public API is the product**, so this profile has the highest coverage bar and the
strongest case for property-based testing. Test what you export; don't test private helpers
directly.

## Test through the public API
Import the package the way a user would (`from mylib import parse`), and test the documented
contract. If a private helper needs its own test, that's often a signal it should be public or that
the public function lacks a case covering it — prefer adding a public-API test that exercises the
helper's behavior over reaching into `mylib._internal`.

```python
import pytest
from mylib import parse, ParseError

@pytest.mark.parametrize(
    ("raw", "expected"),
    [("a=1", {"a": "1"}), ("a=1;b=2", {"a": "1", "b": "2"}), ("", {})],
    ids=["single", "multiple", "empty"],
)
def test_parse_happy(raw, expected):
    assert parse(raw) == expected

@pytest.mark.parametrize("bad", ["=1", "a=", "a==1"], ids=["no-key", "no-val", "double-eq"])
def test_parse_rejects_malformed(bad):
    with pytest.raises(ParseError, match="malformed"):
        parse(bad)
```

## Lean into property-based tests
Libraries are full of laws — roundtrips, idempotence, ordering, algebraic identities — which are
exactly what Hypothesis is for (`references/property-tests.md`). A few high-value invariants
(`decode(encode(x)) == x`; `sort(sort(x)) == sort(x)`; `merge(a, empty) == a`) catch whole classes
of bugs that example-based tests miss.

## Doctests as executable documentation
If your docstrings contain examples, run them so the docs can't drift:

```toml
[tool.pytest.ini_options]
addopts = "... --doctest-modules"     # collect doctests from the package
```

Keep doctests for *illustrative* examples; put thorough edge/failure coverage in `tests/`, not in
docstrings (doctests are awkward for parametrization and error matching).

## Test the packaging contract
- Exported names: assert your `__all__` / public surface imports cleanly (a tiny
  `test_public_api_imports` that imports each public name guards accidental breakage).
- Version: `assert importlib.metadata.version("mylib")` matches `mylib.__version__` if you expose one.
- If you ship type information, run the type checker in CI (mypy/pyright) — type correctness is part
  of a library's contract (this is the "static quality gate" sense of quality, run as a separate CI
  step, not a pytest assertion).

## Compatibility matrices
If you support multiple Python or dependency versions, that's a CI concern (tox/nox/`matrix`), not
in-suite. Within the suite, use parametrized fixtures to cover behavioral variants (e.g. different
input encodings/backends) rather than environment versions.

## Tiers & coverage
- **unit**: every public function — happy/edge/failure, parametrized.
- **property**: the invariants/laws (Hypothesis) — usually a library's most valuable tests.
- **integration**: only if the library composes subsystems (e.g. a parser + an evaluator working
  together on real fixture files).
- Coverage tier: **95**, branch coverage on. Exclude genuinely unreachable defensive branches via
  `# pragma: no cover` with a comment justifying each — don't lower the floor to dodge them.
