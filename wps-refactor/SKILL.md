---
name: wps-refactor
description: "Fix flake8 wemake-python-styleguide (WPS) and ruff violations by repairing the design the violation points at, instead of silencing the counter. Use this skill whenever a WPS or ruff violation is reported or pasted, whenever the user says 'make the linter pass', 'fix flake8', 'fix ruff', 'clean up lint', 'WPS is complaining', or reports that lint fixes made the code worse or harder to extend; and before editing any file in a repo whose setup.cfg or pyproject.toml enables wemake-python-styleguide. Use it especially the moment you are tempted to add a noqa, raise a max-* threshold, add a per-file-ignore, create utils.py or helpers.py, introduce **kwargs or Any, prefix a name with an underscore to dodge a rule, or split a function at an arbitrary line to get a count down — this skill governs every one of those moves. It takes precedence over rapier's tripwire against linter fixes that add structure."
---

# WPS-refactor — fix the design, not the counter

## The core claim

**A WPS violation is a measurement, not an instruction.** It reports that a number crossed a threshold. It does not tell you which concept is missing, and it cannot tell whether you removed complexity or just moved it somewhere the counter does not look.

This matters because the counter can be satisfied in two ways, and only one of them is a fix:

- The number drops **because a concept got a name and a single home**. Real fix.
- The number drops **because the same tangle now spans more names, files, or dict keys**. Damage. The linter goes green and the code gets worse.

Both look identical to flake8. Only the second one is common, because it is faster. Assume you are about to do the second one.

The reliable test is not "does it lint?" It is: **after the fix, how many places must change to add the next case?** If the answer went up, or stayed above one, the refactor failed regardless of the exit code.

---

## The three failure modes — recognize these in your own edits

### 1. Silencing — the counter is disabled rather than satisfied

`# noqa: WPS226`, bumping `max-arguments`, adding a rule to `per-file-ignores`, renaming `data` to `data_`. The code is unchanged; only the observer changed. There is a legitimate version of this (see "When the linter is wrong") but it is rare and must be argued for out loud, never slipped in.

### 2. Displacement — the complexity moves to where nothing counts it

The classic moves, all of which lower a WPS number while raising real complexity:

| Move | Counter satisfied | What actually happened |
|---|---|---|
| Bundle 9 parameters into `config: dict` | WPS211 | Types lost, callers now guess keys |
| Add `**kwargs` | WPS211 | Signature no longer documents anything |
| Split a 70-line function at line 35 into `_step_a`/`_step_b` | WPS213, WPS231 | Two functions passing 8 locals between them; one path, two hops |
| Move half a module to `helpers.py` | WPS202 | Concept split across files by size, not meaning |
| Hoist a subexpression to `tmp` | WPS221 | A meaningless name now sits on the hot path |
| `import module` instead of `from module import a, b` | WPS201 | Dependency count unchanged, call sites longer |
| Annotate as `Any` | WPS234 | Type checker disabled at that boundary |
| `del unused_arg` or `_ = unused_arg` | ruff ARG | Wrong signature preserved and now advertised |

Displacement is the default agent behavior because it is a local edit. Every entry above should read as an alarm, not a technique.

### 3. Half-conversion — the concept is introduced but applied only at the flagged line

The most damaging mode, and the hardest to see, because the diff looks like good work. An enum, constant, or registry is introduced; the flagged occurrence is converted; the other twelve occurrences keep the old vocabulary. Now one idea has two spellings, and every future reader has to learn both.

```python
# Half-converted: linter is quiet, code is worse than before
class Family(StrEnum):
    DEEPSEEK = "deepseek"
    LLAVA = "llava"

ENGINE_DEEPSEEK = "deepseek-ocr"

def _resolve_family(engine_name: str, model_type: str) -> Family:
    if engine_name == ENGINE_DEEPSEEK:      # constant vocabulary
        return Family.DEEPSEEK
    if model_type == "llava":               # raw-string vocabulary  <-- survivor
        return Family.LLAVA
    return Family.MINICPM                    # implicit default, unnamed
```

Two vocabularies for one concept, plus a silent fallback that hides unknown models. **The rule: a concept is not introduced until the old spelling has zero occurrences outside its new home.** Step 5 of the procedure enforces this mechanically.

---

## Not every rule needs architecture

Do not philosophize about import order. Classify the violation first — this takes seconds and prevents the opposite failure, where every trivial fix turns into a redesign.

**Mechanical fix is correct and sufficient** — apply it and move on: ruff `I` (import sorting), `UP` (pyupgrade), `E`/`W` (whitespace, formatting), `C4` (comprehensions), `F401` (unused import → delete it), `RET504`/`RET505` (redundant assignment or `else` after `return`), WPS336 (implicit string concat), WPS339/WPS358 (number formatting), WPS420 (`pass` → docstring or removal), WPS504 (negated condition → invert it).

**Structural — the violation is a symptom; read the rest of this skill**: every WPS rule that counts things (WPS2xx family), every naming rule (WPS110/111/118), WPS226, WPS432, WPS437, WPS219, WPS430, and ruff `ARG`, `PLR09xx`, `B006`/`B008`.

**Ambiguous — decide by reading the code**: WPS110 on a genuinely generic utility, WPS111 on a mathematical index in a tight loop, SIM102/SIM108 where the "simplified" form is less readable than the original. If mechanical is genuinely better here, take it and say why in one line.

---

## The procedure

Follow this in order. Steps 5 and 6 are the ones that catch the failure modes above; do not skip them because the linter already went quiet.

### 1. Widen the scope before reading anything

Never work from a single reported line. Run the linter over the whole module and group the output:

```bash
flake8 path/to/module.py
ruff check path/to/module.py
```

Multiple violations in one module are usually **one** underlying problem reported by several counters. WPS211 (too many arguments) + ruff ARG (unused arguments) + WPS223 (too many elifs) in the same file is not three tasks. It is one missing type, reported three ways. Fixing them separately produces three bad patches.

### 2. Read the module and its callers, not the function

```bash
grep -rn "name_of_thing" --include="*.py" .
```

You cannot tell whether an argument cluster deserves a type without seeing whether callers already build it together. You cannot tell whether an elif-chain deserves a table without seeing whether the same branching exists in two other functions.

### 3. Name the concept in one sentence

Write it down explicitly, in domain language, before touching code. The sentence must be about the problem domain, not about Python:

- Good: "The thing this module keeps re-deriving is *which loader/prompt-scorer/output-scorer triple serves a given model*."
- Good: "Every scorer receives the union of every family's inputs and ignores the ones it does not need."
- Bad: "This function is too complex." (that is the linter's sentence, not yours)
- Bad: "We need a strategy pattern." (a shape, chosen before the concept was named)

If you cannot write this sentence, you have not read enough. Go back to step 2. If the honest sentence is "there is no missing concept, this function is just long and linear," that is a valid finding — see "When the linter is wrong."

### 4. Choose the home from the shape menu

The concept needs exactly one place to live. Pick the **cheapest shape that makes the N+1 case a single-place edit** — the shapes are ordered from cheapest to most expensive, and each rung needs a reason you can state:

| # | Shape | Use when | Typical rules it resolves |
|---|---|---|---|
| 0 | **Delete it** | The branch, parameter, or hook has no live caller | any |
| 1 | **Guard clauses / early return** | Nesting encodes preconditions, not variation | WPS220, WPS231, WPS222 |
| 2 | **A named predicate or a named intermediate value** | A boolean expression or subexpression carries meaning | WPS221, WPS222, WPS204 |
| 3 | **A table (dict / `MappingProxyType` registry)** | Branching selects a *value or callable* by a key; the branches differ only in what they return | WPS223, WPS226, WPS212, WPS231 |
| 4 | **A frozen dataclass / `NamedTuple`** | Parameters or locals always travel together, or a function returns several related values | WPS211, WPS210, WPS213, ARG, PLR0913 |
| 5 | **Enum + one mapping keyed by it** | The key set is closed and the same key drives several lookups | WPS226, WPS432, WPS223 |
| 6 | **A `Protocol` (or ABC) with one class per variant** | Variants differ in **more than one behavior** *and* each carries its own state | WPS214, WPS202, WPS231 |

**The rung-6 rule.** A Protocol earns its place when the number of behaviors that vary is greater than one. If variants differ in exactly one function, that is a table (rung 3), not a class hierarchy. If they differ in three functions keyed by the same enum — as in three parallel dicts all keyed by `Family` — **the three parallel tables are the tell that the variants want to be one object.** Collapsing N parallel dicts keyed by the same enum into one dict of records (rung 4) or one Protocol (rung 6) is almost always the right call, because it makes "add a family" a single-place edit.

**Do not skip rungs.** Rungs 3 and 4 resolve the large majority of real WPS violations and cost almost nothing. Reaching for rung 6 first is the over-engineering that rapier exists to stop.

### 5. Convert everything, then sweep for survivors

Apply the concept across the whole module — not only the flagged line. Then prove the old vocabulary is gone:

```bash
# for every raw literal, constant, or branch condition the concept replaced
grep -rn '"deepseek"' --include="*.py" .
grep -rn "ENGINE_DEEPSEEK" --include="*.py" .
```

**Every hit outside the new home is an unfinished conversion.** Zero hits, or hits only inside the single definition site, is the passing condition. Duplicate definitions of the same constant (the same name assigned twice in one module) are a specific signal that the file was edited without being read — check for them explicitly.

### 6. Write the N+1 receipt

Before claiming the fix is done, write out concretely what adding the next case requires:

```
N+1 receipt: adding model family "qwen-vl" requires editing:
  1. registry.py  — one new FamilySpec entry
Total: 1 place
```

If the list has more than one entry (two is tolerable only when the second is a genuinely separate concern, like a test fixture), **the concept is not in one home yet — return to step 4.** This receipt is the actual definition of success for this skill. The linter's exit code is not.

### 7. Re-run both linters over the whole module and the tests

The refactor must not push violations into neighbouring files or into the test suite. If the tests now need rewriting, that is information: check whether the tests were asserting on the old vocabulary (fine, update them) or on behavior that changed (not fine, you broke something).

### 8. Report in this shape

```
WPS fix — <module>
Violations:      <before, by code> -> <after, by code>
Concept:         <the one sentence from step 3>
Home:            <file:symbol>
Shape:           <rung number + name from the menu>
Sweep:           grep '<old spelling>' -> <N> hits outside home   (must be 0)
N+1 receipt:     adding <concrete new case> touches <M> place(s): <list>
Suppressions:    none | <rule> — <one-line reason>
Thresholds:      unchanged
Behavior:        unchanged | <what changed and why it was required>
```

The `Thresholds: unchanged` line exists because raising a `max-*` value is the least visible and most damaging form of silencing — it weakens the rule for the entire codebase to fix one function. If you changed one, say so explicitly and justify it as a config decision, not as a fix.

---

## Anti-cheat checklist

Run this against your own diff before reporting. Each item is grep-able. Any hit needs a written justification or a redo.

1. `# noqa` added anywhere
2. A `max-*` value raised in `setup.cfg`
3. A rule added to `per-file-ignores`
4. New file named `utils.py`, `helpers.py`, `common.py`, `misc.py`, `base.py`, `core.py` (WPS100/WPS102 exist precisely to catch this)
5. New function named `_part2`, `_step_b`, `_process_impl`, `_do_work`, `_handle` — split-by-line-count signatures
6. A name gained a trailing underscore or a numeric suffix (`data_`, `value2`)
7. `**kwargs` or `*args` appeared in a signature that previously listed parameters
8. `Any`, `object`, or `dict[str, Any]` appeared where a concrete type was
9. A constant is referenced exactly once (it is a rename, not a concept)
10. The same constant or literal is defined twice in one module
11. `del arg` / `_ = arg` / `noqa: ARG` used on an unused parameter
12. Two helper functions pass more than 4 locals between them
13. The raw literal an enum replaced still appears elsewhere in the repo
14. A new `if` chain was created that duplicates a branch that already exists elsewhere
15. Behavior changed silently — a `try` body was narrowed, a default branch was added, an exception type widened

Items 11 and 15 are the ones that cause bugs rather than ugliness. Treat them as blocking.

---

## When the linter is wrong

Sometimes it is. A registry module that is genuinely a flat list of facts will trip WPS202 (too many module members), and splitting it makes things worse. A numerical kernel will trip WPS210 and WPS221 for real mathematical reasons. **A zero-exception policy is not a virtue here — it is what causes linter-driven architecture damage**, because it leaves an agent no honest exit and forces the bad refactor.

The escape valve must be narrow and expensive:

1. Suppress the **narrowest scope that works**: a line-level `# noqa: WPS226 — <reason>` beats a file-level ignore, which beats a config change.
2. Every suppression carries a one-line reason naming the forcing constraint — the same standard as a KEEP line in a rapier deletion pass. "Too hard to fix" is not a reason. "This module is a flat registry; splitting it would spread one concept across files" is.
3. If suppressions for the same rule reach three, stop and tell the user: **the config is miscalibrated for this project**, and fixing it at config level (with a stated rationale) is more honest than scattering suppressions. That is a conversation to have, not a change to make unilaterally.

---

## Precedence with rapier

Rapier's Tripwire 7 says: *a linter fix that adds structure → stop and ask*. This skill supersedes that tripwire, but not the rest of rapier. The resolution:

1. **Deletion outranks everything.** Rapier's deletion pass runs first. Code that should not exist cannot be linted into shape, and a WPS violation on dead code is a signal to delete, not to refactor. Rung 0 of the shape menu is rapier's rung.
2. **Once code has earned its place, this skill governs its shape.** Rapier's "don't add abstraction" instinct does *not* veto naming a concept that a violation exposed, because rungs 3–5 (table, dataclass, enum) reduce total complexity — they make the N+1 edit smaller. Rapier's ladder measures *layers*; this skill measures *places you must edit*. When a change lowers the second while raising the first slightly, take it.
3. **Rapier still vetoes speculation.** WPS223 firing on a three-branch chain is a reason for a three-entry table, not for a plugin system, an entry-point registry, or a config schema. Rapier's Tripwire 2 (an abstraction with exactly one user) and Tripwire 6 (building for an unstated requirement) remain in force. If the shape you chose has one member, it is a rename, not a concept.
4. **Tool choice still precedes style conformance.** If the right answer was a 20-line shell script, do not build a Python class hierarchy because the Python linter is the one that ran.

---

## Reference files

- `references/catalog.md` — 40+ WPS and ruff rules with the typical cheat and the structural fix for each. **Read this whenever a violation code appears that you have not just handled.** Look up the specific code rather than reasoning from the rule name; several WPS names are misleading about what they are actually measuring.
- `references/worked-examples.md` — three full before/after refactors at different rungs, including the parallel-dispatch-tables case and a complexity-splitting case. Read when the shape choice in step 4 is not obvious.

**These examples are directional, not templates.** They show what "the concept got a home" looks like in one domain. Adapt the reasoning — the sentence in step 3 and the receipt in step 6 — to the code in front of you. An example copied structurally into a project where it does not fit is itself a WPS-refactor failure: it is displacement with extra steps.
