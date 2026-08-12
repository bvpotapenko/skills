# Fixtures & mocking — the shared toolbox

Every profile builds on this. Read it once; the domain references assume it.

## Contents
1. Fixture patterns (scope, factory, yield-teardown, composition)
2. Built-in fixtures you should reach for first
3. Mocking with `mocker`: where to patch, what to assert
4. Fakes vs mocks vs stubs — pick the lightest that proves the behavior
5. Time, randomness, network, filesystem isolation
6. Parametrization patterns
7. Anti-patterns to avoid

---

## 1. Fixture patterns

**Plain fixture** — a value or object the test requests by name:

```python
import pytest

@pytest.fixture
def user():
    return User(id=1, name="Ada")
```

**Yield fixture for setup + teardown** (this is how you replace `tearDown`):

```python
@pytest.fixture
def db_conn(tmp_path):
    conn = sqlite3.connect(tmp_path / "t.db")
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    yield conn                      # test runs here
    conn.close()                    # always runs, even on failure
```

**Factory fixture** — when a test needs *several* configured instances. Return a function:

```python
@pytest.fixture
def make_user():
    created = []
    def _make(name, **kw):
        u = User(id=len(created) + 1, name=name, **kw)
        created.append(u)
        return u
    return _make

def test_two_users(make_user):
    a, b = make_user("Ada"), make_user("Bo")
    assert a.id != b.id
```

**Scope** — default `function` (fresh per test = isolation). Widen only for expensive, read-only
resources, and prefer `session` for things like a loaded model or a started container:

```python
@pytest.fixture(scope="session")
def embedding_model():            # loaded once for the whole run
    return load_model("tiny")
```

A `function`-scoped fixture can depend on a `session`-scoped one, never the reverse.

**Composition** — fixtures depend on fixtures; build small ones and combine:

```python
@pytest.fixture
def admin(make_user):
    return make_user("root", role="admin")
```

**`conftest.py`** — fixtures defined there are available to all tests in that directory tree with no
import. Put shared fixtures at the level that needs them (root `tests/conftest.py` for global,
`tests/integration/conftest.py` for integration-only).

**Parametrized fixtures** — run every dependent test once per param (good for "same behavior across
backends"):

```python
@pytest.fixture(params=["memory", "sqlite"])
def store(request, tmp_path):
    return make_store(request.param, tmp_path)
```

---

## 2. Built-ins to reach for first

| Fixture        | Use                                                                 |
|----------------|---------------------------------------------------------------------|
| `tmp_path`     | A unique `pathlib.Path` temp dir per test — **never** write to cwd. |
| `tmp_path_factory` | Session-scoped temp dirs.                                       |
| `monkeypatch`  | Patch attrs/env/dict/syspath with auto-undo (`setattr`, `setenv`, `chdir`, `delitem`). |
| `capsys`/`capfd` | Capture `stdout`/`stderr` (`capsys` for Python-level, `capfd` for fd-level/subprocess). |
| `caplog`       | Assert on log *records* (level, message) — see the implementation-detail caveat below. |
| `recwarn`      | Capture warnings.                                                    |
| `request`      | Introspect the running test (markers, params, `request.node`).      |

`monkeypatch.setenv("API_KEY", "x")` and `monkeypatch.chdir(tmp_path)` are the clean ways to control
environment and cwd — they undo themselves after the test.

---

## 3. Mocking with `mocker`

Use `pytest-mock`'s `mocker` fixture. It wraps `unittest.mock` and **auto-reverts** every patch at
test end (no `with`/decorator nesting, no leaks).

**Patch where the name is looked up, not where it's defined.** If `myapp/service.py` does
`import httpx` then calls `httpx.get(...)`, patch `myapp.service.httpx.get`:

```python
def test_fetch_returns_payload(mocker):
    resp = mocker.Mock(status_code=200)
    resp.json.return_value = {"ok": True}
    get = mocker.patch("myapp.service.httpx.get", return_value=resp)

    result = myapp.service.fetch("/u")

    assert result == {"ok": True}          # behavior: the returned value
    get.assert_called_once_with("/u")      # boundary contract: we called the API correctly
```

**`mocker.patch.object`** to patch a method on a class/instance; **`side_effect`** for sequences or
exceptions:

```python
mocker.patch.object(Client, "send", side_effect=[ok, ok, TimeoutError])
mocker.patch("myapp.svc.now", side_effect=ConnectionError("boom"))
```

**`autospec=True`** (or `mocker.create_autospec`) makes the mock reject calls with the wrong
signature — prefer it so a refactor of the real function's signature fails the test instead of
silently passing:

```python
mocker.patch("myapp.service.charge", autospec=True, return_value=Receipt(ok=True))
```

**`spy`** wraps the *real* function but records calls — use when you want real behavior **and**
assertion that it ran:

```python
spy = mocker.spy(myapp.cache, "store")
do_work()
spy.assert_called_once()
```

### What to assert on a mock (and what not to)
Assert the boundary **contract** — that you called the external dependency with the right arguments
(`assert_called_once_with(...)`), because that *is* observable behavior. Do **not** assert internal
call counts/order that no caller cares about, or `assert_called` on your own helper functions —
that's testing implementation. Rule of thumb: assert mock calls only for *boundaries you own the
contract with* (the HTTP request you send, the message you publish, the row you insert).

`caplog` caveat: asserting an *exact* log string is brittle. Assert the level and a stable substring
(`"payment failed" in caplog.text`, `caplog.records[0].levelno == logging.ERROR`) only when the log
is a real, contracted output (e.g. an audit log). Otherwise skip it.

---

## 4. Fakes vs mocks vs stubs

Pick the lightest tool that proves the behavior:

- **Stub**: returns canned data, no assertions. Good for "the code under test needs *something* back".
- **Mock**: records calls so you can assert the interaction. Use when the *interaction* is the
  behavior (you must call `charge()` exactly once).
- **Fake**: a working lightweight implementation (in-memory dict as a repository, `aiosqlite`
  in-memory DB, a fake clock object). **Often the best choice** — it exercises real logic without
  real I/O, and doesn't couple the test to call sequences. Prefer a fake repository over five
  `mocker.patch` calls.

```python
class FakeRepo:                      # a fake — real behavior, no DB
    def __init__(self): self._rows = {}
    def add(self, u): self._rows[u.id] = u
    def get(self, i): return self._rows.get(i)

def test_service_persists(make_user):
    repo = FakeRepo()
    svc = UserService(repo)
    svc.register(make_user("Ada"))
    assert repo.get(1).name == "Ada"   # behavior via the fake, no mock-call asserts
```

Injecting collaborators (constructor params, like `UserService(repo)`) makes fakes trivial and is
the single biggest lever for testable, non-brittle code. Design for it.

---

## 5. Isolating time, randomness, network, filesystem

- **Time**: inject a clock (`UserService(now=lambda: fixed_dt)`) or use `freezegun`
  (`@freeze_time("2025-01-01")`) / `time-machine`. Never assert on `datetime.now()` directly.
- **Randomness**: inject the RNG (`def shuffle(xs, rng=random.Random()): ...`) so tests pass a
  seeded `random.Random(0)`; or use the `seed` fixture. For *checking that something is random*, see
  `references/property-tests.md` — that's the one place you don't pin the seed.
- **Network**: the `--disable-socket --allow-hosts=127.0.0.1,::1` policy (pytest-socket) fails any
  unmocked external connection in unit/property tests while leaving asyncio's loopback intact;
  integration tests opt back in with `@pytest.mark.enable_socket`. Either way, mock the *client*, not
  the socket, in unit tests.
- **Filesystem**: always `tmp_path`. To control cwd, `monkeypatch.chdir(tmp_path)`.

---

## 6. Parametrization patterns

**Basic, with readable ids:**

```python
@pytest.mark.parametrize(
    ("text", "expected"),
    [("", 0), ("a", 1), ("héllo", 5)],
    ids=["empty", "single", "unicode"],
)
def test_length(text, expected):
    assert length(text) == expected
```

**Stack decorators for a matrix** (cartesian product):

```python
@pytest.mark.parametrize("a", [0, 1, -1])
@pytest.mark.parametrize("b", [10, 100])
def test_add(a, b):
    assert add(a, b) == a + b
```

**Error cases in the same table** with `pytest.raises` via `pytest.param`:

```python
ok = lambda v: v
@pytest.mark.parametrize(
    ("value", "expectation"),
    [
        (5, does_not_raise := __import__("contextlib").nullcontext()),
        (-1, pytest.raises(ValueError, match="negative")),
    ],
)
def test_validate(value, expectation):
    with expectation:
        validate(value)
```

(Cleaner: keep happy-path and error-path as two parametrized tests if the mixed table hurts
readability.) Use `pytest.param(..., marks=pytest.mark.slow, id="big")` to mark individual cases.

---

## 7. Anti-patterns (don't)

- `setup_method`/`teardown_method`/`setUp`/`tearDown` → use fixtures.
- `unittest.TestCase` subclasses / `self.assert*` → plain functions + `assert`.
- Patching deep internals or asserting private attributes → patch boundaries, assert contracts.
- One giant test asserting ten unrelated things → split by behavior.
- Order-dependent tests / shared mutable module state → isolate via fixtures; `-p no:randomly` only
  to *debug*, then fix the coupling.
- `time.sleep` to "wait for" async/threads → await/poll/synchronize instead.
- Copy-pasted near-identical tests → parametrize.
- Tests that pass before the implementation exists → you're not testing what you think.
