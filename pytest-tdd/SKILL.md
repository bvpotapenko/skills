---
name: pytest-tdd
description: >-
  Write, structure, and run pytest test suites the TDD way across Python project types
  (asyncio backends, CLI apps, Telegram bots, standalone libraries, and ML/DL code). Use this
  skill whenever the user asks to write or add tests, "test this function", set up or fix a test
  suite, raise coverage, do TDD, work with fixtures/mocks/parametrization, test async code, write
  property/metamorphic/statistical tests for stochastic or ML behavior, or run pytest after a code
  change — even if they don't say the word "pytest". Trigger it proactively before writing new
  application code that should be test-driven, and before editing existing tested code. Always use
  pytest (never unittest), prefer fixtures over setup methods, and keep the three-tier split of
  unit / property / integration tests.
---

# pytest-tdd

A skill for test-driven development with pytest. It encodes one consistent way to structure,
write, and run tests, with per-project-type guidance loaded on demand.

Read this file fully, then read the **one** reference file matching the project type you are
working in (see *Pick the project profile* below). Read additional references only if a task spans
types (e.g. a library that also ships a CLI).

---

## Non-negotiable principles

These hold in every project, every test, every time. They are the point of the skill.

1. **pytest, not unittest.** No `unittest.TestCase`, no `self.assertEqual`. Plain functions,
   plain `assert`, pytest fixtures. (Use `unittest.mock` *objects* via the `mocker` fixture — see
   point 5 — but never the `TestCase` framework.)
2. **Fixtures over setup/teardown.** No `setup_method`/`teardown_method`/`setUp`. Shared state and
   resources come from `@pytest.fixture`. Put cross-file fixtures in `conftest.py`. Prefer the
   narrowest scope that works (`function` default; widen to `module`/`session` only for expensive,
   read-only resources).
3. **Parametrize repetition.** If two tests differ only in inputs/expected values, collapse them
   into one `@pytest.mark.parametrize` with `ids=`. Never copy-paste a test body to change a
   number. Build matrices by stacking `parametrize` decorators.
4. **Cover happy path, edge cases, and failure paths.** Every behavior gets all three where they
   exist: the normal case, the boundaries (empty, zero, one, max, unicode, None, off-by-one,
   degenerate shapes), and the error contract (`pytest.raises(Exc, match=...)`). A suite that only
   tests the happy path is incomplete.
5. **Mock at I/O boundaries, with the `mocker` fixture.** Patch the *boundary* (the HTTP client, DB
   driver, filesystem call, clock, the Telegram/3rd-party API, the subprocess), never your own
   internals. Use `pytest-mock`'s `mocker` fixture (fixture-based, auto-undone) rather than raw
   `unittest.mock.patch` context managers or decorators. Patch where the name is *looked up*, not
   where it's defined (`mocker.patch("myapp.service.httpx.get")`, not `httpx.get`). See
   `references/fixtures-and-mocking.md`.
6. **Target the coverage tier for the project type** (table below). Gate the *full* suite on it.
7. **Run pytest after every change.** See *The loop* — this is a hard step, not optional.
8. **Assert behavior, not implementation.** Assert on the public contract: return value, raised
   exception, or an observable side effect (a value written to a passed-in object, a file on disk,
   a message the mocked boundary received). Do **not** assert on private attributes, internal call
   ordering you don't care about, exact log strings, or "method X was called" unless that call *is*
   the externally-meaningful behavior. Implementation-detail assertions make refactors fail loudly
   for no reason; behavior assertions catch real regressions. When tempted to assert a call, ask
   "would a user/caller notice if this changed?" — if no, don't assert it.

Two more that make the above work in practice:

9. **Deterministic by default.** No test depends on wall-clock time, real randomness, network, or
   ambient filesystem state. Freeze time, seed or inject RNG, use `tmp_path`, block the network.
   (The exception is the *statistical* property tests, which deliberately exercise randomness — see
   the property tier.)
10. **Arrange–Act–Assert, one behavior per test.** Keep each test focused on a single behavior so a
    failure name tells you what broke. Multiple `assert`s are fine when they describe one behavior.

---

## The three test tiers

We split tests **by both directory and marker** (your chosen layout). Directories give physical
separation and let you run a tier by path; markers let you select a tier *across* directories or
combine with cross-cutting markers (`slow`, `gpu`). A `conftest.py` hook auto-applies the tier
marker from the directory, so **you never annotate a test with its own tier** — you only add
*extra* markers (`@pytest.mark.slow`, `@pytest.mark.gpu`).

```
<project>/
├── src/<package>/...
├── tests/
│   ├── conftest.py            # shared fixtures + auto-marking hook + seeding
│   ├── unit/                  # → auto @pytest.mark.unit
│   ├── property/              # → auto @pytest.mark.property
│   └── integration/           # → auto @pytest.mark.integration
└── pyproject.toml             # [tool.pytest.ini_options] + [tool.coverage.*]
```

### unit — does this one piece do what it claims, in isolation
One unit (function/method/small class) with **all collaborators and I/O mocked**. Asserts the
contract: returns the right value, raises the right error, mutates the passed object correctly.
Fast (target < ~100 ms each). For a *stochastic* function, the unit test asserts it **runs and
returns the right type/shape** — e.g. "a rotated image of the same shape comes back" — **not** that
the randomness is correct. That belongs in the next tier.

### property — does the output have the right *properties* / behavior (your "quality" tier)
This is the tier you described: beyond "it ran and returned a picture", assert the result is
*actually correct/behaved*. Established names: **property-based**, **metamorphic**, and
**statistical/distributional** testing (in ML, **behavioral** testing). Three sub-kinds, all live
here:

- **Property-based** (Hypothesis): an invariant over a generated input space — `decode(encode(x))
  == x` for all `x`; output is always a valid probability distribution; dtype preserved for any
  input.
- **Metamorphic**: a relation between inputs/outputs when there's no exact oracle —
  `rotate(rotate(img, a), b) ≈ rotate(img, a+b)`; rotate-then-unrotate ≈ identity; a 90°-multiple
  rotation preserves the pixel histogram; doubling all model inputs scales the prediction as
  expected.
- **Statistical / distributional**: for stochastic functions, the output *distribution* matches
  intent over many runs — **"the rotation is actually random"** = angles are ~uniform (chi-square /
  KS goodness-of-fit) **and not constant**; a sampler's mean/variance sit in expected bounds.

Full patterns and the worked rotation example: `references/property-tests.md` (and runnable code in
`examples/property_testing_rotation/`). *(Decision point: if you prefer the literal name `quality`,
rename the `property` dir + marker everywhere — it's purely cosmetic.)*

### integration — do several real pieces work together across a boundary
Multiple **real** components wired together: real temp DB/files, a real in-process HTTP app, the CLI
invoked end-to-end, a real event loop. Mock **only** true third-party externalities you don't own
or can't run (paid APIs, the Telegram servers, cloud SDKs). Slower, fewer, higher-level. Asserts
end-to-end behavior, not internals.

### Markers, registration, selection
Markers are registered in `pyproject.toml` with `--strict-markers` (an unregistered marker is an
error, which catches typos). Common runs:

```bash
pytest tests/unit -q                     # fast inner loop (by path)
pytest -m unit -q                        # same, by marker (works across dirs)
pytest -m "property and not gpu"         # property tier, skip GPU
pytest -m "not slow"                     # everything quick
pytest                                   # full suite + coverage gate (see config)
```

---

## The loop (TDD + run-after-change)

Follow red → green → refactor, and **run pytest after every edit to code or tests**:

1. **Red.** Write the smallest failing test that expresses the next behavior (or, when adding tests
   to existing code, the test that pins the behavior you're about to touch). Run it; confirm it
   fails *for the expected reason* (`pytest path::test -q`). A test that passes before you write the
   code is not testing what you think.
2. **Green.** Write the minimum code to pass. Run the affected tests immediately:
   `pytest tests/unit/test_x.py -q`, or `pytest --lf -x -q` to iterate on just the failures.
3. **Refactor.** Improve names/structure with the tests green. Re-run after each refactor.
4. **Before declaring the task done**, run the **full suite with the coverage gate** and make it
   green: `pytest` (the `addopts` in `pyproject.toml` apply `--cov` + `--cov-fail-under`). Inner-loop
   runs may use `--no-cov` for speed; the final run must not.

Never end a turn with a red suite, a skipped-without-reason test, or coverage below the tier. If a
test is genuinely not-yet-implementable, mark it `@pytest.mark.xfail(reason=...)` (visible) rather
than deleting or silently skipping it. If you must stop with red, say so explicitly and show the
failure.

Useful flags while working: `-q` (quiet), `-x` (stop on first failure), `--lf` / `--ff` (last-failed
first), `-k <expr>` (select by name), `-ra` (summary of skips/xfails), `--durations=10` (find slow
tests), `-p no:randomly` (disable test-order randomization to debug an order-dependent failure).

---

## Coverage tiers (per project type)

Coverage is whole-suite, so it's gated when running the **full** suite (`pytest`), typically in CI
or pre-commit — not on the fast unit-only inner loop. Because your project *types* live in separate
repos, each repo sets its own floor in `pyproject.toml` (`--cov-fail-under=<N>` + `--cov-branch`):

| Project type            | `--cov-fail-under` | Notes                                                              |
|-------------------------|--------------------|-------------------------------------------------------------------|
| Standalone library      | **95**             | Public API is the product; aim high. Branch coverage on.          |
| Async backend service   | **90**             | Exclude framework wiring/`__main__` from the denominator.         |
| CLI app                 | **85**             | Cover command logic; argument plumbing can be integration-level.  |
| Telegram bot            | **80**             | Lots of I/O glue; cover handlers/business logic, mock the API.    |
| ML / DL app             | **75**             | Line coverage is a *weak* proxy here — the **property tier and    |
|                         |                    | metric gates are the real quality bar**, not the %.               |

These are defaults — adjust per repo. Always pair the number with `--cov-branch` (branch coverage)
and `term-missing` reporting. Exclude untestable plumbing via `[tool.coverage.run] omit` and
`[tool.coverage.report] exclude_lines` rather than by lowering the floor. **For ML, do not chase the
percentage** by testing trivial getters — invest in property/metamorphic/metric tests instead.

---

## Pick the project profile

Detect the type from the repo, then read the matching reference file. Signals → profile:

- `asyncio`, `async def`, `httpx`/`aiohttp`, `fastapi`/`starlette`/`aiohttp.web`, `asyncpg`/`aiosqlite`
  → **`references/async-backend.md`** + `references/fixtures-and-mocking.md`
- `click`, `typer`, `argparse`, a `console_scripts`/`[project.scripts]` entry, a `__main__.py`
  → **`references/cli-apps.md`**
- `aiogram`, `python-telegram-bot` (`telegram.ext`), `pyrogram`/`telethon`, a bot token, handlers
  → **`references/telegram-bots.md`**
- A pure package with a public API and no app entry point, published/installable
  → **`references/libraries.md`**
- `torch`, `tensorflow`, `jax`, `sklearn`, `numpy`-heavy numeric code, training/eval loops, models,
  datasets, transforms → **`references/ml-dl.md`** (+ `references/property-tests.md` for the quality tier)
- Any stochastic or numeric function whose *correctness* (not just type) matters →
  **`references/property-tests.md`**

Always also have `references/fixtures-and-mocking.md` available — it's the shared toolbox every
profile builds on.

When unsure of the framework within a profile (Click vs Typer; aiogram vs PTB; PyTorch vs sklearn),
**detect it** from imports/`pyproject.toml` and follow that branch in the reference file. Each
reference marks its framework branches as explicit decision points.

---

## Setup (when a project has no test config yet)

If `tests/` or the pytest config is missing, scaffold from `assets/` (copy, then adapt):

- `assets/pyproject.pytest.toml` — paste `[tool.pytest.ini_options]` + `[tool.coverage.*]` into the
  project's `pyproject.toml`. Set `--cov=<package>` and the tier's `--cov-fail-under`.
- `assets/conftest.py` — root `tests/conftest.py`: the auto-marking hook, a requestable `seed`
  fixture, and shared fixture stubs.
- `assets/conftest.ml.py` — extra ML conftest (full determinism: torch/cuda seeding, a tiny-tensor
  fixture). Merge into the ML project's `tests/conftest.py`.

Then create `tests/unit/`, `tests/property/`, `tests/integration/`, each with an `__init__.py`-free
layout (pytest's `rootdir` + `src/` import mode handles discovery; prefer
`pythonpath`/`src` layout over `sys.path` hacks).

---

## Decision points (explicitly configurable)

These are choices the skill has made a default for; change them deliberately, per project. They are
called out here (and again at their point of use in the references) so the "why" is never hidden:

1. **Tier layout — dirs + markers** (chosen). Auto-marking hook keeps them in sync.
   *Alt:* markers-only (drop the dirs) or dirs-only (drop the hook).
2. **Coverage — per-type tiers** (table above), gated on the full suite with branch coverage.
   *Alt:* a single flat floor across all repos.
3. **`property` tier name** (chosen). *Alt:* `quality` — rename dir + marker if your team prefers it.
4. **Async runner — `pytest-asyncio` in `asyncio_mode = "auto"`** (no per-test decorator needed).
   *Alt:* `anyio` (`anyio_backend` fixture) if you run trio too, or `pytest-asyncio` strict mode.
   See `references/async-backend.md`.
5. **Mocking — `pytest-mock` (`mocker`)** for fixture-based, auto-undone patching.
   *Alt:* raw `unittest.mock.patch`. Discouraged: more boilerplate, easy to leak patches.
6. **Network isolation — `pytest-socket`** (`--disable-socket --allow-hosts=127.0.0.1,::1`, which
   keeps asyncio's loopback working) to enforce "mock external I/O"; integration tests re-enable via
   `@pytest.mark.enable_socket`. *Alt:* trust reviewers; drop the dependency.
7. **Warnings — `filterwarnings = ["error"]`** to turn warnings into failures.
   *Alt:* relax with targeted `ignore::` entries (ML stacks usually need a few for torch/numpy
   deprecations — see `assets/conftest.ml.py` notes).
8. **Determinism — requestable `seed` fixture** generically; **autouse** full seeding in ML.
   Note the Hypothesis/statistical-test interaction documented in `references/property-tests.md`.
9. **Property tooling — Hypothesis + `scipy.stats`** for property-based and distributional checks.
   *Alt:* hand-rolled generators / `numpy`-only stats if you can't add deps.

---

## Quick reference: which file for what

- Shared fixtures, mocking, fakes-vs-mocks, time/network/tmp control → `references/fixtures-and-mocking.md`
- The "quality" tier (property / metamorphic / statistical) + rotation example → `references/property-tests.md`
- asyncio services, async fixtures, event loop, mocking async I/O → `references/async-backend.md`
- Click / Typer / argparse, `CliRunner`, exit codes, stdout/stderr → `references/cli-apps.md`
- aiogram / python-telegram-bot handlers, FSM, mocking the Bot API → `references/telegram-bots.md`
- Pure libraries: public-API testing, doctests, packaging, high coverage → `references/libraries.md`
- PyTorch / sklearn / TF: determinism, tiny fixtures, overfit check, metric gates → `references/ml-dl.md`
- Config + conftest templates to copy → `assets/`
