# Worked examples

Five refactors, chosen to show the *reasoning*, not to be copied. In each case the important part is the sentence in step 3 and the receipt in step 6 — the code shape follows from those. A different project with a different N+1 story wants a different shape.

- [1. Parallel dispatch tables — several counters, one missing record type](#1-parallel-dispatch-tables)
- [2. Cognitive complexity — splitting at the wrong seam vs the right one](#2-cognitive-complexity)
- [3. Argument count where the answer is deletion first](#3-argument-count-where-deletion-comes-first)
- [4. When the honest answer is a suppression](#4-when-the-honest-answer-is-a-suppression)
- [5. An orchestration `main()` — the seam test, then the locals audit](#5-an-orchestration-main--the-seam-test-on-a-cli-script)
- [6. "Flat by design" — the homogeneity test on a shared module](#6-flat-by-design--the-homogeneity-test-on-a-shared-module)
- [7. WPS214 on a port implementation — the fix was rung 0](#7-wps214-on-a-port-implementation--the-fix-was-rung-0)
- [5. An orchestration `main()` — the seam test on a CLI script](#5-an-orchestration-main--the-seam-test-on-a-cli-script)

---

## 1. Parallel dispatch tables

### The linter output

```
scorers.py:34: WPS226 Found string constant over-use: "deepseek"
scorers.py:88: WPS223 Found too many `elif` branches
scorers.py:91: WPS211 Found too many arguments
scorers.py:91: ARG001 Unused function argument: `processor`
scorers.py:12: WPS202 Found too many module members
```

**Step 1 tells you these are one problem, not five.** They all sit on the same axis: "which model family is this, and what does that family do?"

### Before — the half-converted state

```python
class Family(StrEnum):
    DEEPSEEK = "deepseek"
    LLAVA = "llava"
    MINICPM = "minicpm"

ENGINE_DEEPSEEK = "deepseek-ocr"

_FAMILY_LOADERS = MappingProxyType({
    Family.DEEPSEEK: _load_deepseek,
    Family.LLAVA: _load_llava,
    Family.MINICPM: _load_minicpmv,
})
_PROMPT_SCORERS = MappingProxyType({...})   # same three keys
_OUTPUT_SCORERS = MappingProxyType({...})   # same three keys


def _resolve_family(engine_name: str, model_type: str) -> Family:
    if engine_name == ENGINE_DEEPSEEK:
        return Family.DEEPSEEK
    if model_type == "llava":       # <- raw string survived the conversion
        return Family.LLAVA
    return Family.MINICPM           # <- unknown models silently become minicpm
```

Three defects the linter cannot see:

1. **Two vocabularies.** `ENGINE_DEEPSEEK` on one line, `"llava"` on the next. The enum was applied where WPS226 pointed and nowhere else.
2. **Three tables keyed by the same enum.** Whenever N tables share a key set, the key is not really a key — it is an object identity, and the tables are its fields, scattered.
3. **A silent default.** An unrecognized model becomes `MINICPM` rather than an error, so a typo in a manifest produces wrong scores instead of a stack trace.

### Step 3 — name the concept

> "A *scorer family* is the unit that knows how to recognize its own models, load them, and score prompts and outputs. Right now that unit is spread across an enum, three mappings, and an if-chain."

Note what the sentence does: it names one thing that owns four facts. The shape falls out immediately.

### Step 4 — choose the rung

Rung 4 (a frozen record) plus rung 3 (one table of them). Not rung 6: the variants differ in behavior but carry no per-variant state, so a `Protocol` would add a class hierarchy for no gain. The three parallel `MappingProxyType`s become fields on one record.

### After

```python
@dataclass(frozen=True, slots=True)
class FamilySpec:
    """Everything that varies between scorer families, in one place."""

    name: str
    engines: frozenset[str]
    model_types: frozenset[str]
    load: Callable[[ModelRef], ScorerBundle]
    score_prompt: Callable[[ScorerBundle, PromptTask], float]
    score_output: Callable[[ScorerBundle, OutputTask], float]


FAMILIES: Final = (
    FamilySpec(
        name="deepseek",
        engines=frozenset({"deepseek-ocr"}),
        model_types=frozenset(),
        load=_load_deepseek,
        score_prompt=_deepseek_score_prompt,
        score_output=_deepseek_score_output,
    ),
    FamilySpec(
        name="llava",
        engines=frozenset(),
        model_types=frozenset({"llava"}),
        load=_load_llava,
        score_prompt=_llava_score_prompt,
        score_output=_llava_score_output,
    ),
    # ... minicpm
)


def resolve_family(model: ModelRef) -> FamilySpec:
    """Find the family that claims this model, or fail loudly."""
    for spec in FAMILIES:
        if model.engine in spec.engines or model.model_type in spec.model_types:
            return spec
    raise UnknownFamilyError(engine=model.engine, model_type=model.model_type)
```

`ModelRef` is the second missing type: `engine_name` and `model_type` always travel together and are always read together, so they were already one value — undeclared. Parsing the manifest into `ModelRef` once at the boundary is what stops raw strings from spreading inward, which is the durable fix for WPS226 rather than a constant-per-literal.

### Step 5 — sweep

```bash
grep -rn '"deepseek"\|"llava"\|"minicpm"' --include="*.py" .
grep -rn "ENGINE_DEEPSEEK\|_FAMILY_LOADERS\|_PROMPT_SCORERS" --include="*.py" .
```

Passing condition: hits only inside `FAMILIES` and inside the manifest parser. Any other hit is an unconverted site.

### Step 6 — the receipt

```
N+1 receipt: adding family "qwen-vl" touches:
  1. scorers/qwen.py        — three functions (load, score_prompt, score_output)
  2. scorers/registry.py    — one FamilySpec entry
Total: 2 places, and #1 is genuinely new code, not edited code.
```

Compare with the "before": adding a family meant editing the enum, three mappings, and the if-chain — five edits to existing code, each independently forgettable, with a silent default that hid the mistake when you forgot one.

### The trade-off worth stating

Data-driven matching (`engines`/`model_types` as sets) is right when family selection is membership. If some family needs a rule that is not membership — a version comparison, a regex on the model path — do not force it into sets. Add a `matches: Callable[[ModelRef], bool]` field instead and give each family a named predicate. Choose the data-driven form when it fits because it keeps the registry declarative; do not contort real logic to preserve that.

---

## 2. Cognitive complexity

### The linter output

```
run.py:41: WPS231 Found function with too much cognitive complexity: 19 > 15
run.py:41: WPS213 Found too many expressions: 17 > 15
run.py:41: WPS210 Found too many local variables: 26 > 25
```

### The cheat

```python
def run_pass(spec, inputs, out_dir):
    bundle, tokenizer, cfg, seed, dtype, batch, limits = _run_pass_part1(spec, inputs)
    return _run_pass_part2(bundle, tokenizer, cfg, seed, dtype, batch, limits, out_dir)
```

Every counter drops. Nothing improved: seven locals now cross a function boundary, the reader makes two hops to follow one path, and neither half has a name that means anything. **A helper whose parameter list is a snapshot of another function's locals is a cut at the wrong place.**

### Finding the right seam

Read the body and mark where a *value is finished*. In a scoring pass those points are usually: inputs are loaded and validated → the model is ready → scores exist → the report is written. Each boundary carries one complete value, not a bag of intermediates.

```python
def run_pass(spec: FamilySpec, request: RunRequest) -> RunReport:
    """Load, score, and summarize one scoring pass."""
    batch = load_batch(request.inputs)          # -> InputBatch
    bundle = spec.load(request.model)           # -> ScorerBundle
    scores = score_batch(spec, bundle, batch)   # -> ScoreTable
    return summarize(scores, request.limits)    # -> RunReport
```

Each helper takes 1–3 arguments and returns one named thing. Each is independently testable and independently readable. The cognitive complexity fell because branching moved *inside* the step that owns it, not because statements were redistributed.

**The check that distinguishes the two versions:** can you describe each helper's return value in a noun phrase without mentioning the caller? `InputBatch`, `ScorerBundle`, `ScoreTable` pass. `_run_pass_part2` does not.

If no such seam exists — the function is genuinely one long linear computation with no complete intermediate values, as in some numerical kernels — that is a real finding, and a suppression with that reason is more honest than an arbitrary cut.

---

## 3. Argument count where deletion comes first

### The linter output

```
scorers/llava.py:22: WPS211 Found too many arguments: 8 > 15  (after threshold tightening)
scorers/llava.py:22: ARG001 Unused function argument: `cache_dir`
scorers/llava.py:22: ARG001 Unused function argument: `trust_remote_code`
```

### Before jumping to a dataclass, run rapier's pass

The instinct is "8 parameters → make a config object." Wrong first move. Two of them are unused *here*, and a `grep` across call sites shows `cache_dir` is passed as `None` at every caller and `trust_remote_code` is always `True`.

```
Deletion pass on score_llava():
- CUT cache_dir: every caller passes None; the loader ignores it        (~4 lines)
- CUT trust_remote_code: constant True at all 6 call sites; inline it   (~3 lines)
- KEEP dtype: differs per run and is read by the tokenizer
Net: 8 args -> 6 args, before any abstraction is introduced
```

**Then** ask whether the remaining six cluster. If `model`, `tokenizer`, and `processor` are constructed together and passed together at every call site, they are one value (`ScorerBundle`) and the signature becomes three arguments. If they do not cluster, the function is doing several jobs and splits by job.

The ordering matters: bundling dead parameters into a dataclass *preserves* them under a nicer name and makes them permanent. Delete first, then abstract what survives.

---

## 4. When the honest answer is a suppression

### The situation

```
registry.py:1: WPS202 Found too many module members: 24 > 20
```

`registry.py` contains one `FamilySpec` definition and 23 spec instances. Every member serves one concept. Splitting it into `registry_a.py` / `registry_b.py` would spread a single lookup table across files by alphabet — a WPS100-shaped move with extra steps.

### The honest fix

```python
# registry.py
# noqa comment at module level, with the forcing reason stated:
"""Family registry.

flake8: noqa: WPS202 — this module is a flat declaration of one concept
(the family table). Splitting it would spread a single lookup across files
by count rather than by meaning.
"""
```

This is one suppression for WPS202 — one module, one concept, one reason. If a third module in the same repo turns out to need the same one, that is a fact about the project, and it goes on the report's `Config notes:` line ("three flat registries each suppress WPS202; `max-module-members` may be calibrated for a different kind of project"). The owner decides what to do with it; the task does not stop to ask.

**What makes this legitimate and the cheats illegitimate:** the reason names a property of the code (one concept, flat declaration) that a reader can verify, and the alternative was concretely evaluated and is worse. "Refactoring is too hard" and a bare `# noqa: WPS202` do not meet that bar.

---

## 5. An orchestration `main()` — the seam test on a CLI script

### The linter output

```
scripts/eval.py:31: WPS210 Found too many local variables: 14 > 10
scripts/eval.py:31: WPS213 Found too many expressions: 27 > 12
scripts/eval.py:31: WPS231 Found function with too much cognitive complexity: 16 > 12
scripts/eval.py:      WPS421 Found wrong function call: print      (x14)
scripts/eval.py:      WPS226 Found string literal over-use: '.venv/bin/python' > 3
```

### The wrong turn

"`main()` is a flat 160-line orchestration script. Satisfying WPS210/213/231 in code means splitting it into `_step_a`/`_step_b` helpers passing 8 locals. WPS421 fires 14 times because these are CLI scripts. The config is miscalibrated for this project."

Every sentence describes the file. None is a finding about a fix, because no fix was attempted. The `_step_a`/`_step_b` split is the cheat from the displacement table, presented as the only code option — and "8 locals passed between them" is not an obstacle, it is rung 4's signal. And "14 times" counts lines: it is one concept.

### Step 3 — the seam test

List the complete values `main()` produces, in order, as nouns that make sense without mentioning `main()`:

1. the parsed run request (paths, container name, timeout)
2. the resolved interpreter (sibling project's venv python, or `sys.executable`)
3. the running container
4. the gathered results directory
5. the eval report

Five nouns. Seams exist; the "long and linear" sentence may not be written. The WPS226 finding — `.venv/bin/python` re-derived in four places — is noun 2 reported by a different counter.

### Step 4 — rung 4, plus one output boundary

```python
@dataclass(frozen=True)
class Run:
    """Everything every phase reads — the record that was 14 locals."""
    project: Path
    python: Path
    container: str
    results: Path
    timeout_s: int

def resolve_python(project: Path) -> Path: ...            # -> noun 2, one home for the venv rule
def deploy(run: Run) -> str: ...                          # -> noun 3, returns the container id
def gather(run: Run, container: str) -> Path: ...         # -> noun 4
def evaluate(run: Run, results: Path) -> Report: ...      # -> noun 5

def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(message)s")
    run = parse_args()
    container = deploy(run)
    try:
        results = gather(run, container)
    finally:
        stop_container(container)
    evaluate(run, results).write(sys.stdout)
    return 0
```

Each helper takes one record and at most one more argument and returns one noun. The fourteen `print` calls sorted into two kinds: twelve were status ("deploying…", "gathering…") and became `log.info`; two emitted the result table and became `Report.write(out)`. Zero suppressions. Still flat — no classes with behavior, no layers, five top-level functions and a record — which is what a flat-scripts preference was asking for.

### Step 6 — the receipt

```
N+1 receipt: adding a --quiet flag touches:
  1. main()  — level chosen from the flag
Total: 1 place            (before: 14 print sites)

N+1 receipt: adding a phase "warm the cache" between deploy and gather touches:
  1. eval.py — one new function returning `the warmed cache`, one call in main()
Total: 1 place
```

### The report line that carries the real observation

```
Config:          untouched
Config notes:    per-file-ignore for tests/*.py matches no file in this repo (copied from a library project)
```

That is a true thing the owner should hear. It is one line at the end, not a fork the task waits on.

### The residual — the second wrong turn

After the seam extraction a smaller runner in the same family lands here:

```python
def main() -> None:
    args = _build_parser().parse_args()
    _apply_num_threads(args)
    device = init_device()
    seed_everything(args.seed)
    model_info = resolve_model_info(args.model_id)
    adapter, patches, loaded = _load_adapter(args, device)
    provenance = _provenance(args, device, model_info, patches)
    captures = _run(loaded, adapter, args, device)
    out_dir = Path(args.out)
    write_outputs(out_dir, provenance, captures)
    logger.info("Wrote %d results -> %s", len(captures), out_dir)
```

```
run_ocr.py:118: WPS210 Found too many local variables: 9 > 5
```

The report says: "Every remaining local is a load-bearing phase handoff (device, adapter, loaded, args, out_dir…); bundling further is a god-namespace. Recommend raising `max-local-variables` for this package." Two claims, both checkable, both false.

**The locals audit:**

```
local        born at                consumed by
args         parse_args()           _apply_num_threads, seed, resolve, _load_adapter, _provenance, _run, Path
device       init_device()          _load_adapter, _provenance, _run
adapter  ┐
patches  ├   _load_adapter()        _run / _provenance / _provenance
loaded   ┘
model_info   resolve_model_info()   _provenance
provenance   _provenance()          write_outputs
captures     _run()                 write_outputs, log
out_dir      Path(args.out)         write_outputs, log
```

- `adapter, patches, loaded` — three names from one call. `_load_adapter` already returns a value it did not name. Add `device` to it (born one line earlier, consumed by the same three callers) and the value is "the model is ready":

```python
@dataclass(frozen=True, slots=True)
class LoadedSession:
    """Everything that exists once the model is loaded — born at one seam."""
    device: str
    adapter: ModelAdapter
    loaded: LoadedModel
    patches: tuple[str, ...]
```

- `model_info` is consumed only by `_provenance` → `_provenance(args, session)` resolves it itself.
- `provenance` is consumed only by `write_outputs` → pass the call.
- `out_dir` is used once, twice if you count the log line → inline it, and let `write_outputs` return the path it wrote so the log has it.

```python
def main() -> None:
    args = _build_parser().parse_args()
    _apply_num_threads(args)
    session = _load_session(args)                 # init_device + seed + adapter.load, one seam
    captures = _run(session, args)
    written = write_outputs(Path(args.out), _provenance(args, session), captures)
    logger.info("Wrote %d results -> %s", len(captures), written)
```

Four locals. No god-object: `LoadedSession` has four fields, all born in `_load_session`, all consumed by the same two callers. "Bundling further is a god-namespace" was an objection to an undrafted record; the drafted one is a value.

**What the audit also surfaced:** `args` sits in every consumer column, and `_run` reads five fields off an untyped `Namespace`. That is the request wanting a name (`RunRequest`, parsed once from argv). It is a package-wide decision — five runners share `add_common_args` — so it goes on the report as the next structural item, not a per-runner patch.

```
Suppressions:    none
Config:          untouched
Config notes:    none — 9 → 4 locals with one record; the "load-bearing" residual was three names from one tuple return
```

---

## 6. "Flat by design" — the homogeneity test on a shared module

### The linter output

```
runners/kit.py:1: WPS202 Found too many module members: 14 > 7
```

### The wrong turn

"`kit.py` is flat by design — its docstring says it is *exactly one shared module* for the runners. Splitting it undoes the documented design and raises WPS201 in every runner (already 3 per-file-ignores). Also, the structural fixes planned elsewhere add three members to it (14 → 17). Recommend raising `max-module-members` for this package."

Three assertions, no kind column. And the last sentence is the tell: a module that *grows* while the design is being improved is absorbing concepts, not owning one.

### The homogeneity test

```
member                 kind
add_common_args        CLI parser builder
MODE_SCORE_OUTPUT      CLI vocabulary
MODE_SCORE_PROMPT      CLI vocabulary
init_device            platform probe
device_fields          platform probe
cann_version           platform probe
seed_everything        RNG setup
resolve_model_info     provenance lookup
package_version        provenance lookup
RawCapture             result record
write_outputs          result writer
```

Five kinds. "One shared module" described where the code lives, not what it is. Split by kind:

```
runners/cli.py         add_common_args, MODE_*, (later) RunRequest + parse_request()
runners/platform.py    init_device, device_fields, cann_version, seed_everything
runners/provenance.py  resolve_model_info, package_version, ModelProvenance builder
runners/outputs.py     RawCapture, write_outputs
```

Each module has one kind and one name that is the kind. The three planned additions each have an obvious home now (a request record → `cli.py`; a provenance builder → `provenance.py`) instead of landing on the pile.

### The shape: a package, not four loose files

```
runners/kit/__init__.py    re-exports the public names from the four modules below (WPS412 allows exactly this)
runners/kit/cli.py
runners/kit/runtime.py
runners/kit/provenance.py
runners/kit/outputs.py
```

Runners keep `import kit` / `from kit import ...`; their WPS201 counts do not move; a sibling repo that does `import kit` is untouched; `--cov=kit` and isort config are untouched. If instead the four files are dropped beside the runners and `kit.py` deleted, every runner's import count rises by three and lands at the WPS201 line with no headroom, and the sibling repo needs a lockstep migration — the "price" was never the split, it was doing the split without the package.

Two things keep the package honest. First, one spelling: consumers import from `kit`, never from `kit.cli` — mixed spellings are the half-conversion failure mode, and "a façade preserves the old spelling" is a warning about *that*, not about the surface itself. Second, the kind column is re-run on the *package*: if `kit/` keeps gaining modules of new kinds, it is a dump with a directory.

The docstring gets rewritten, not obeyed.

### The receipt

```
N+1 receipt: adding a runner "run_asr.py" touches:
  1. runners/run_asr.py   — new file, imports the four concept modules it needs
Total: 1 place, and it is new code
(before: same, but every new helper it needed would have gone into kit.py)

Suppressions:    none
Config:          untouched
Config notes:    none
```

### Contrast: the module that *does* pass

`utils/device.py` in the same package has 14 members and is described as a "flat platform-probe registry". Run the same test. If the column reads `probe, probe, probe, …, PROBES table` — one kind plus the table that registers them — it is a homogeneous table and the module-level suppression from example 4 applies, with that column as the reason. If the column reads `probe, probe, dtype check, env parser, logging setup` it is example 6 again. The test is the same; only the answer differs, and it comes from the list, not from the docstring.

---

## 7. WPS214 on a port implementation — the fix was rung 0

### The linter output

```
store/reader.py:14: WPS214 Found too many methods: 8 > 7
```

### The wrong turn

"`KotStoreReader` implements the `StoreReader` port; the port owns the method set, the class is cohesive. `load_decode_prefill_floor` is a pending stub with no production callers. Options: (a) line-level `# noqa: WPS214 — implements the port`; (b) delete the stub from port, reader, writer and the fake — a contract change that removes a planned-feature marker. Recommend (a)."

The report *found* rung 0 and then chose rung 7 over it. Two errors in one paragraph:

1. **A port you own is not an external contract.** Rung 7 Part 1 asks for a constraint kind; "the port dictates the set" only qualifies when the port is somebody else's. Here the port is in the same repo, and the port is exactly the thing the counter is questioning. The same test applies to "pinned" functions: a sibling repo importing a runner's `_load_model` is not a reason to freeze `_load_model` and wrap it in `_load_session` — it is a reason to make the loader public and migrate the caller in the same change.
2. **A stub with zero callers is rung 0**, and rapier's Tripwire 2 evidence against the interface, and Tripwire 6 ("might need it later"). A "planned-feature marker" is a comment in code form; version control is where plans that are not code live.

### The receipt, written honestly

```
Suppression receipt — store/reader.py:KotStoreReader, WPS214
Constraint kind:  none — the port is owned by this repo
Rung 0 delete:    load_decode_prefill_floor has 0 production callers → delete from port, reader, writer, FakeStore
Result:           7 methods, under the line; no suppression needed
```

If the floor feature is genuinely scheduled, the alternative is to *finish* it — implement the method and its first caller — which also removes the stub. Either way the class ends with no `NotImplementedError` in it. What is not an option is a suppression that keeps the stub alive under a reason ("implements the port") that the stub itself falsifies.

```
Suppressions:    none
Config:          untouched
Behavior:        unchanged — deleted method had no callers (grep: 0 hits outside port/impls/fake)
```
