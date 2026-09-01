# Worked examples

Four refactors, chosen to show the *reasoning*, not to be copied. In each case the important part is the sentence in step 3 and the receipt in step 6 — the code shape follows from those. A different project with a different N+1 story wants a different shape.

- [1. Parallel dispatch tables — several counters, one missing record type](#1-parallel-dispatch-tables)
- [2. Cognitive complexity — splitting at the wrong seam vs the right one](#2-cognitive-complexity)
- [3. Argument count where the answer is deletion first](#3-argument-count-where-deletion-comes-first)
- [4. When the honest answer is a suppression](#4-when-the-honest-answer-is-a-suppression)

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

Then apply the escalation rule from SKILL.md: this is suppression #1 for WPS202. If a second and third appear, stop and raise it with the user — at that point `max-module-members` is miscalibrated for a project that legitimately contains registries, and changing it deliberately with a stated rationale beats scattering suppressions that each look like a small local defeat.

**What makes this legitimate and the cheats illegitimate:** the reason names a property of the code (one concept, flat declaration) that a reader can verify, and the alternative was concretely evaluated and is worse. "Refactoring is too hard" and a bare `# noqa: WPS202` do not meet that bar.
