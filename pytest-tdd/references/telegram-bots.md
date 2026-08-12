# Telegram bots (aiogram / python-telegram-bot)

A bot is mostly **handlers** (business logic triggered by updates) plus **I/O to Telegram's API**.
Test the handler logic with the Telegram API mocked; never hit the real servers. Detect the library
and follow that branch.

## Universal rules
- **The Telegram Bot API is a hard boundary — always mocked** in unit/property tests. The bot's
  `send_message`/`answer`/`edit_message_text` calls are *outgoing I/O*; assert you called them with
  the right chat/text/markup, don't hit the network.
- **Separate handler logic from the framework.** A handler that computes a reply by calling a plain
  service function lets you unit-test the service directly and only thinly test the handler wiring.
- Updates (messages, callback queries) are **fixtures**: build a minimal fake/`Mock` update once,
  reuse via factory fixtures.

## aiogram (decision point: aiogram — async, v3 shown)

Handlers are `async`; this pairs with the async-backend runner (`asyncio_mode="auto"`). Mock the
`Message`/`CallbackQuery` and assert on the methods the handler calls.

```python
import pytest

@pytest.fixture
def message(mocker):
    msg = mocker.AsyncMock()                 # async: .answer/.reply are awaited
    msg.text = "/start"
    msg.from_user = mocker.Mock(id=42, full_name="Ada")
    msg.chat = mocker.Mock(id=42)
    return msg

async def test_start_handler_greets(message):
    await start_handler(message)             # the aiogram handler under test
    message.answer.assert_awaited_once()
    (text,), _ = message.answer.call_args
    assert "Ada" in text                     # behavior: greeting includes the user's name

async def test_callback_answers_query(mocker):
    cb = mocker.AsyncMock()
    cb.data = "confirm:1"
    await confirm_handler(cb)
    cb.answer.assert_awaited_once()          # must acknowledge the callback
    cb.message.edit_text.assert_awaited_once()
```

- **FSM (`StateContext`/`FSMContext`)**: pass an `AsyncMock` state and assert transitions —
  `state.set_state.assert_awaited_with(Form.name)`, `state.update_data.assert_awaited_with(name="Ada")`.
  Use `state.get_data.return_value = {...}` to simulate stored data.
- aiogram also offers a `MockedBot`/test utilities in `aiogram.tests`; the `AsyncMock` approach above
  is dependency-free and usually enough. Use the official mocked bot for full
  `bot.send_message(...)`-level assertions if your handlers call `bot` directly.
- For middleware/routers, integration-test by feeding a built `Update` through the `Dispatcher` with
  the bot's session mocked.

## python-telegram-bot (decision point: PTB — `telegram.ext`, v20+ async)

Handlers take `(update, context)`. Build mock `Update`/`Context`; assert on `context.bot` /
`update.message.reply_text`.

```python
import pytest

@pytest.fixture
def update(mocker):
    upd = mocker.Mock()
    upd.effective_user = mocker.Mock(id=42, full_name="Ada")
    upd.effective_chat = mocker.Mock(id=42)
    upd.message = mocker.AsyncMock()         # reply_text is awaited
    upd.message.text = "/start"
    return upd

@pytest.fixture
def context(mocker):
    ctx = mocker.Mock()
    ctx.bot = mocker.AsyncMock()             # bot.send_message is awaited
    ctx.args = []
    ctx.user_data = {}
    return ctx

async def test_start_replies(update, context):
    await start(update, context)             # the PTB handler
    update.message.reply_text.assert_awaited_once()
    (text,), _ = update.message.reply_text.call_args
    assert "Ada" in text

from unittest.mock import ANY

async def test_command_with_args_sends_to_chat(update, context):
    context.args = ["status"]
    await handle(update, context)
    # pin chat_id (the contract), leave exact text unpinned with ANY
    context.bot.send_message.assert_awaited_once_with(chat_id=42, text=ANY)
```

(Use `unittest.mock.ANY` for arguments you don't want to pin, e.g. exact text, while still asserting
the ones that matter like `chat_id`.) PTB also provides application test helpers; the mock approach
keeps unit tests fast and offline.

## What to test
- **Command routing**: the right handler runs for `/start`, `/help`, unknown commands (failure path:
  unknown command → help/fallback).
- **Reply content/markup**: the message text and any inline keyboard are correct — assert the
  contract, a stable substring of text plus button `callback_data`, not the entire formatted string.
- **Conversation/FSM flow**: each state transitions correctly given input; invalid input keeps/loops
  state (failure path).
- **Authorization**: restricted commands reject non-allowed users (`update.effective_user.id`).
- **Outgoing API calls**: `send_message`/`edit_text`/`answer_callback` are awaited with correct
  `chat_id` and content.

## Tiers & coverage
- **unit**: handlers with mocked Message/Update/Context and mocked Bot API.
- **property**: any data transformation a handler performs (formatting, parsing) — invariants here.
- **integration**: feed an update through the real dispatcher/application with only the bot's network
  session mocked (validates routing/middleware end-to-end).
- Coverage tier: **80** (handler glue and library callbacks are I/O-heavy; cover logic, mock the API).
