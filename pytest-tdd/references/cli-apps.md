# CLI apps (Click / Typer / argparse)

Test command **logic** as plain functions where possible, and the **wiring** (parsing, exit codes,
stdout/stderr) via the framework's runner. Detect the framework from imports and follow that branch.

## Layering: keep logic out of the command shell
The most testable CLI separates the *command function* (parses args, calls into a library, formats
output) from the *business logic* (a plain, importable function). Unit-test the logic directly;
use the runner only to test parsing/exit-codes/output. This keeps most tests fast and the brittle
surface (argument plumbing) thin.

## Click (decision point: Click)

Use Click's `CliRunner` — invokes the command in-process and captures output/exit code:

```python
from click.testing import CliRunner
from myapp.cli import main          # a @click.command / @click.group

def test_greet_happy_path():
    result = CliRunner().invoke(main, ["greet", "--name", "Ada"])
    assert result.exit_code == 0
    assert "Hello, Ada" in result.output

def test_missing_required_option_errors():
    result = CliRunner().invoke(main, ["greet"])
    assert result.exit_code != 0
    assert "Missing option" in result.output    # parsing failure path

def test_uses_isolated_filesystem(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0
```

- Feed stdin via `invoke(main, [...], input="y\n")`; set env via `invoke(..., env={...})`.
- `result.exception` / `result.exc_info` hold uncaught errors; `catch_exceptions=False` to let them
  propagate for debugging.
- Mock the *library boundary* the command calls (`mocker.patch("myapp.cli.do_work", ...)`), not
  Click internals — assert the command parsed args and forwarded them correctly.

## Typer (decision point: Typer)

Typer ships its own runner (built on Click's):

```python
from typer.testing import CliRunner
from myapp.main import app          # a typer.Typer()

runner = CliRunner()

def test_build_command():
    result = runner.invoke(app, ["build", "--target", "prod"])
    assert result.exit_code == 0
    assert "built prod" in result.stdout
```

Same patterns as Click (Typer *is* Click underneath): parametrize argument combinations, test the
`Missing argument`/`Invalid value` failure paths, mock the boundary the command calls.

## argparse / `__main__` (decision point: argparse)

Expose a `main(argv: list[str] | None = None) -> int` that *takes argv and returns an exit code* —
this makes it directly callable, no subprocess:

```python
# myapp/cli.py
def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return run(args)              # returns 0/non-zero

# tests
import pytest
from myapp.cli import main

def test_runs_ok(capsys):
    code = main(["--name", "Ada"])
    assert code == 0
    assert "Hello, Ada" in capsys.readouterr().out

def test_bad_args_exit_2(capsys):
    with pytest.raises(SystemExit) as ei:    # argparse calls sys.exit(2) on parse error
        main(["--bogus"])
    assert ei.value.code == 2
    assert "error:" in capsys.readouterr().err   # argparse writes errors to stderr
```

If the code only has a `__main__` block, refactor the body into `main(argv)` first — testing via
`subprocess` is a last resort (slow, integration-only).

## Output and exit codes
- Capture with `capsys` (Python-level prints) or `capfd` (anything writing to fd 1/2, incl.
  subprocesses). `out, err = capsys.readouterr()`.
- Assert **exit codes** explicitly — they're the CLI's contract with the shell (`0` success, `2`
  usage error for argparse, your documented codes otherwise).
- Assert on **stable** substrings of output, not whole formatted blocks (formatting changes
  shouldn't break tests). For rich tabular/colored output consider snapshot testing (`syrupy`) in
  the property tier if exact layout is a real requirement.

## Tiers & coverage
- **unit**: command-logic functions with the boundary mocked; argument-validation errors.
- **integration**: full `invoke(...)` / `main(argv)` end-to-end with a real temp filesystem
  (`isolated_filesystem`/`tmp_path`), only true externals mocked.
- **property**: if a command transforms data, the metamorphic/property checks belong here.
- Coverage tier: **85** (argument plumbing can sit at integration level rather than padding unit %).
