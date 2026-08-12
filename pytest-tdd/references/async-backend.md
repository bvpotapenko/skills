# Async backends (asyncio)

For services built on `asyncio` — FastAPI/Starlette, aiohttp, raw asyncio workers, with async DB
drivers (`asyncpg`, `aiosqlite`, `motor`) and async HTTP clients (`httpx.AsyncClient`, `aiohttp`).

## Runner: pytest-asyncio in `auto` mode (decision point)

Default config (in `assets/pyproject.pytest.toml`):

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"     # any `async def test_*` just runs — no per-test decorator
```

So you write:

```python
async def test_handler_returns_user():
    result = await get_user(1)
    assert result.name == "Ada"
```

*Alternatives:* `pytest-asyncio` **strict** mode (decorate each async test with
`@pytest.mark.asyncio`) if you want explicitness; or **anyio** (`@pytest.mark.anyio` + an
`anyio_backend` fixture) if you also target trio. Pick one per project; don't mix.

## Async fixtures

Fixtures can be async too (yield works for teardown):

```python
import pytest_asyncio

@pytest_asyncio.fixture
async def client():
    async with httpx.AsyncClient(base_url="http://test") as c:
        yield c            # torn down after the test
```

(In `auto` mode `@pytest.fixture` on an async function also works; `pytest_asyncio.fixture` is the
explicit form.) Keep an event-loop-bound resource at `function` scope unless you deliberately manage
a wider-scoped loop.

## Mocking async I/O

Use `mocker` with an **async** return. `unittest.mock`/`pytest-mock` give `AsyncMock` automatically
when patching a coroutine function with `autospec`, or use `mocker.AsyncMock` directly:

```python
async def test_fetch_user_calls_repo(mocker):
    repo = mocker.AsyncMock()
    repo.get.return_value = User(id=1, name="Ada")     # awaited call returns this
    svc = UserService(repo)

    user = await svc.fetch(1)

    assert user.name == "Ada"
    repo.get.assert_awaited_once_with(1)               # note: assert_awaited*, not assert_called*
```

- Patch async boundaries with `autospec=True` so the mock is an `AsyncMock` matching the signature:
  `mocker.patch("myapp.svc.httpx.AsyncClient.get", autospec=True, return_value=resp)`.
- `side_effect` works the same (sequence, or an exception to simulate timeouts:
  `repo.get.side_effect = asyncio.TimeoutError`).
- Assert with the await-aware methods: `assert_awaited`, `assert_awaited_once_with`, `await_count`.

## Prefer a fake over mocking the whole DB

For repository/service logic, an in-memory async fake beats patching the driver — exercises real
logic, no event-loop-bound mock gymnastics:

```python
class FakeUserRepo:
    def __init__(self): self._db = {}
    async def add(self, u): self._db[u.id] = u
    async def get(self, i): return self._db.get(i)
```

## HTTP app integration (FastAPI/Starlette example)

Drive the **real** app in-process with `httpx.ASGITransport` (or `TestClient`); this is an
integration test (`tests/integration/`, real routing/serialization, only true externals mocked):

```python
import httpx, pytest

@pytest.fixture
async def app_client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        yield c

async def test_create_user_endpoint(app_client):
    r = await app_client.post("/users", json={"name": "Ada"})
    assert r.status_code == 201
    assert r.json()["name"] == "Ada"
```

For aiohttp, use `aiohttp.test_utils` / `pytest-aiohttp`'s `aiohttp_client` fixture analogously.

## Async-specific gotchas

- **Never `time.sleep`** to wait for tasks; `await` them, or use `asyncio.wait_for`/an event. Use
  `freezegun`/`time-machine` for time, and for scheduled-delay logic patch the sleep
  (`mocker.patch("asyncio.sleep", new=mocker.AsyncMock())`) so the test is instant.
- **Test cancellation/timeout paths** — they're real failure paths:
  `with pytest.raises(asyncio.TimeoutError): await asyncio.wait_for(slow(), 0.01)`.
- **Concurrency**: assert correct behavior under `asyncio.gather(...)` (no shared-state corruption,
  expected ordering/aggregation).
- The network-isolation policy uses `--allow-hosts=127.0.0.1,::1` specifically so asyncio's loopback
  self-pipe keeps working while external connections are blocked. Don't drop the loopback allowance.
- Coverage tier: **90** (exclude `__main__`/server bootstrap from the denominator via
  `[tool.coverage.report] omit`).
