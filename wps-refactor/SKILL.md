---
name: wps-refactor
description: "Fix flake8 wemake-python-styleguide (WPS) and ruff violations by repairing the design the violation points at, instead of silencing the counter. Use whenever a WPS or ruff violation is reported or pasted, on 'make the linter pass', 'fix flake8/ruff', 'clean up lint', 'WPS is complaining', when lint fixes made code worse, and before editing any file in a repo whose setup.cfg or pyproject.toml enables wemake-python-styleguide. Use it the moment you are tempted to add a noqa, raise a max-* threshold, add a per-file-ignore, create utils.py/helpers.py, introduce **kwargs or Any, dodge a rule with an underscore, split a function at an arbitrary line, or call the config miscalibrated — and when writing or aggregating a lint-cleanup plan, listing 'options' for residual violations, or deciding how tests are linted: a suppression proposed in a plan is a suppression. Takes precedence over rapier's tripwire against linter fixes that add structure."
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

## The four failure modes — recognize these in your own edits

### 1. Silencing — the counter is disabled rather than satisfied

`# noqa: WPS226`, bumping `max-arguments`, adding a rule to `per-file-ignores`, renaming `data` to `data_`. The code is unchanged; only the observer changed. There is a legitimate version of this (see "Rung 7") but it is rare, it carries a receipt, and it is argued for out loud, never slipped in.

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

### 4. Respelling — the logic is unchanged, only the AST is

A tuple of two outcomes indexed by `bool(choices)` so that no ternary appears. `''.join(choices[:1])` to spell "the first element or empty". `sys.stdout.write(...)` in place of a banned `print`. An `and`/`or` chain that reproduces an `if`. A ternary moved into a call argument "to see whether WPS509 still fires". Every one of these keeps the same operands and the same branches and changes only the syntax the rule's visitor looks for. The counter goes green, the reader now has to decode an idiom, and the reason the rule exists is untouched. This is the failure mode that is *harder* to catch than a `noqa`, because a `noqa` is visible in the diff and a `tuple[bool(x)]` is not — so it gets its own test.

**The reason test, run before every edit.** Each rule protects one design property; the catalog names it, and for a rule the catalog does not cover, the WPS docstring does (`python -c "from wemake_python_styleguide.violations import *; help(...)"` or the docs). Write the reason in one clause, then ask of the change you are about to make: *does it satisfy the reason, or the mechanism?* "WPS421 forbids `print` because output belongs to one declared channel" → routing through `sys.stdout.write` satisfies nothing; routing through a logger, or declaring this module *is* the output channel (a role policy, below), satisfies the reason. "WPS509 forbids nested ternaries because a reader cannot hold two conditions in one expression" → naming the intermediate value satisfies it; a tuple index does not. If the honest answer is "mechanism", stop; the change is a respelling.

Two corollaries. **Never edit to find out whether a rule fires** — "let the linter tell me" is legitimate for confirming a structural fix landed, not for searching the space of syntaxes a visitor misses. **Shaving a local is not a fix** — "drop `bound` by changing how the loop unpacks", "fold `plan_path` into the `Path(...)` call" are respellings of WPS210; the locals audit (below) is the fix, and if it leaves the count over the line the function is doing two jobs.

## Not every rule needs architecture

Do not philosophize about import order. Classify the violation first — this takes seconds and prevents the opposite failure, where every trivial fix turns into a redesign.

**Mechanical fix is correct and sufficient** — apply it and move on: ruff `I` (import sorting), `UP` (pyupgrade), `E`/`W` (whitespace, formatting), `C4` (comprehensions), `F401` (unused import → delete it), `RET504`/`RET505` (redundant assignment or `else` after `return`), WPS336 (implicit string concat), WPS339/WPS358 (number formatting), WPS420 (`pass` → docstring or removal), WPS504 (negated condition → invert it), WPS453 / ruff `EXE001`/`EXE002` (shebang and executable bit disagree → `chmod +x`, or drop the shebang if the file is only imported; a fact about the file's mode is not something to ignore in config).

**Structural — the violation is a symptom; read the rest of this skill**: every WPS rule that counts things (WPS2xx family), every naming rule (WPS110/111/118), WPS226, WPS432, WPS437, WPS219, WPS430, WPS421, and ruff `ARG`, `PLR09xx`, `B006`/`B008`.

**A rule that fires N times on one file is one structural finding, not N.** Fourteen `print` calls in a script are one missing output boundary (catalog, WPS421). Six `WPS111` short names in one loop body are one unnamed thing being indexed. Group by concept before you count anything — the count decides whether the linter is wrong, and counting lines instead of concepts is how a single fix gets mistaken for a miscalibrated config.

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

If you cannot write this sentence, you have not read enough. Go back to step 2.

**The seam test — run it before you may write "no missing concept, this function is just long and linear."** That sentence is a claim about the code, and it is checkable, so check it. List, in execution order, the complete values the function produces — each as a noun phrase that makes sense without mentioning the caller: `the parsed run request`, `the running container`, `the gathered results directory`, `the eval report`. Intermediates that only mean something mid-computation (`the partially reduced accumulator`, `the loop index`) do not count.

- **Two or more nouns → seams exist.** Each noun is a function that returns it; the locals every phase reads are one frozen record (rung 4). Go to step 4. This is the normal case for any orchestration `main()` — deploy, gather, evaluate, report — because the script already names its phases. A flat-scripts preference (no layers, no classes) is satisfied by four top-level functions and one record; it is not a requirement that one function hold every local.
- **Fewer than two → the finding is earned.** Go to "Rung 7" with the list as your evidence.
- **Two or more, extracted, and still over the line → run the locals audit** (next section) before writing "the rest are load-bearing".

"These are CLI scripts" and "it is a 160-line orchestration function" describe the file. They are not seam-test results, and they do not open the escape valve.

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
Suppressions:    none | <rule> at <scope> — <one-line reason>   (one entry per concept, not per line; each has a Rung-7 receipt below the report)
Config:          untouched
Config notes:    none | <observation for the owner, e.g. "per-file-ignore for tests/*.py matches no file">
Behavior:        unchanged | <what changed and why it was required>
```

`Config: untouched` is a constant, not a status. `setup.cfg` and `pyproject.toml` are not edited by this skill and are not offered as a path: a threshold or ignore changed there weakens the rule for files you have not read, and it is the one silencing move that leaves no trace at the site it excuses. `Config notes:` is where a real observation goes — a stale ignore copied from another project, a third module in the repo needing the same suppression — stated once, for the owner to act on. It is a line in the report, not a branch the user must choose before the task can finish.

The report is the deliverable whether the request was "check" or "fix"; the only difference is whether the `Violations:` line has an `after`. For a check, every structural finding still carries its step-3 sentence, and the one next step to offer is applying it.

---

## Anti-cheat checklist

Run this against your own diff before reporting. Each item is grep-able. Any hit needs a written justification or a redo.

1. `# noqa` added anywhere
2. A `max-*` value raised in `setup.cfg` / `pyproject.toml` — redo; there is no justification path (see "Rung 7")
3. A rule added to `per-file-ignores` — redo; same
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
16. More `# noqa` entries for one rule in one file than the number of step-3 sentences written for that rule (suppressions scattered per line instead of placed once per concept)
17. A suppression reason built on "by design", "flat", "cohesive", "load-bearing", "one over", "documented", or an effort estimate, with no constraint kind from Rung 7 Part 1
18. A structural option marked "rejected" in a report or plan with no drafted shape next to it (no field list, no kind column, no locals table)
19. A `NotImplementedError`, `pass`-body, or zero-caller method still present in a class that received a WPS214 suppression
20. A helper returning a tuple of three or more values that was not given a name (the record rung 4 was for)
21. A config change, threshold value, or per-file-ignore appearing as an *option* or *recommendation* in a plan — it belongs on `Config notes:` as an observation with a named domain property, or nowhere
22. An expression restructured with the same operands and branches to change its AST shape — `tuple[bool(...)]`, `and`/`or` chains standing in for `if`, `''.join(x[:1])`, a ternary relocated into an argument — with the rule's reason unaddressed
23. `sys.stdout.write` / `sys.stderr.write` / `os.write` appearing where `print` was flagged
24. An edit whose purpose, stated or evident, was to find out whether a rule fires

Items 11 and 15 are the ones that cause bugs rather than ugliness. Treat them as blocking. Items 17–19 and 21 are the ones that turn a refactor task into a config negotiation; treat them as a redo of the rung ladder. Items 22–24 are invisible in a diff review; they are caught only by running the reason test on your own change before you make it.

---

## The residual after extraction — the locals audit

The seam test gets `main()` from 14 locals to 7. Then the second failure arrives: "every remaining local is a load-bearing phase handoff; bundling further would be a god-object." That sentence is also a claim, and it is also checkable. For each surviving local write **where it is born** and **who consumes it**:

```
local        born at                consumed by
args         parse_args()           _load(), _run(), Path(args.out)
device       init_device()          _load(), _provenance(), _run()
adapter  ┐
patches  ├   _load_adapter()        _run() / _provenance() / _provenance()
loaded   ┘
model_info   resolve_model_info()   _provenance()
provenance   _provenance()          write_outputs()
captures     _run()                 write_outputs(), log
out_dir      Path(args.out)         write_outputs(), log
```

Two rules read straight off the table:

- **Several locals born from one call are one value.** A helper that returns a 3-tuple has a return type it did not name. Name it (a frozen record) and three locals become one. This is a *type*, not a god-object: the fields were produced together at one seam and describe one state — "the model is ready".
- **A local consumed by exactly one later call folds into that call.** `model_info` feeds only `_provenance` → compute it inside `_provenance`. `provenance` feeds only `write_outputs` → pass the call directly, or let the writer build it. `out_dir` used once → inline it.

What survives is the honest count, and in a linear runner it is 3–4: the parsed request, one prepared-state record, the result. Only if it is *still* over the line after the audit is the function doing more than one job — and the seams are the rows where the consumer set changes.

The discriminator the displacement table relies on, stated so it can be applied: **a record is a value when its fields are born at the same seam and consumed together; it is a bag when it collects whatever happened to be in scope.** `config: dict`, a `ctx` every function reads two keys from, `**kwargs` — bags. `LoadedSession(device, adapter, loaded, patches)` returned by the one function that produces all four — a value. "Would be a god-object" is not an objection to a drafted record with its fields listed; it is an objection to an undrafted one.

A companion signal in the same table: if `args` (an untyped namespace) appears in every consumer column and helpers read four or five fields off it, the request itself is an unnamed record. Parsing argv into a typed request at the boundary is the WPS226 "parse at the boundary" move applied to the CLI; decide it once for the package, not per runner.

---

## Module and class counters — the homogeneity test

WPS202 (module members) and WPS214 (methods) get the same assertion: "it is one concept", "flat by design", "the docstring says this is the single shared module". Test it instead of accepting it. List the members and write the *kind* of each next to it:

```
add_common_args      CLI parser builder
init_device          platform probe
seed_everything      RNG setup
resolve_model_info   provenance lookup
package_version      provenance lookup
write_outputs        result writer
RawCapture           result record
MODE_SCORE_*         CLI vocabulary
```

Four or five kinds in one module is four or five concepts sharing a filename. Split by *kind*: each new module is named after its kind (`provenance.py`, `outputs.py`, `cli.py`), depends one way on the others, and receives no member because of its size. This is the opposite of `helpers.py`, which is a split by count; anti-cheat item 4 stays in force.

A module passes the test — and earns a suppression — when every member is *the same kind of thing* and reading it top to bottom is reading one list: one spec type plus N instances; N probe functions and the table that registers them; a contract module of zero-logic types. Then the flat shape is the concept, not a habit.

Two things the counter cannot tell you but the member list can:

- **Growth under refactor is the tell.** If the design work you are doing *adds* members to a module already over the line, that module is absorbing concepts rather than owning one. A registry gains entries; a dump gains kinds.
- **A split-by-kind of a shared module is a package, not a scattering.** The concept modules go under the old name as a package (`kit/cli.py`, `kit/provenance.py`, ...) and `kit/__init__.py` re-exports them; that is the one kind of logic WPS412 allows there. Consumers keep importing from the package surface, so their WPS201 count does not move, and external callers of the old name keep working. The concept modules are the package's internal organization — each stays under WPS202, which was the point. Two rules make this honest rather than a hiding place: consumers import from the surface only (a repo where some files do `from kit import X` and others `from kit.cli import X` has two spellings of one dependency — that *is* the half-conversion failure mode, and it is what "a façade preserves the old spelling" actually warns about); and a package that keeps growing kinds under one surface is still a dump, just with a directory. If a split is rejected on the grounds that consumer import counts would rise, the split was being done without the package, not with it. Rapier's "flatten if tracing one path crosses more than ~3 files" is about *call chains*; the call graph is unchanged by this.
- **A caller outside the module that reaches an underscore name is an undeclared contract.** The fix is to declare it — a public name, the caller migrated — never to freeze the private one and wrap it. "Pinned because another repo imports it" is a reason to make it public in the same change, not a reason for two spellings of the same operation.

For WPS214 the kind column is *which attributes the method reads* (catalog entry). And for both counters, a Protocol or port that dictates the member set is an external contract only if it is external: a port you own whose method is a stub with zero callers is rung 0 evidence against the port, not a reason to suppress the class that implements it.

---

## Role policies — tests, CLI modules, scripts

Some files have a *job* that is the very thing a style rule forbids. A test asserts and uses literal data; a CLI entry module prints; a standalone script has a shebang and a `main` that talks to the user. For such a file the rule's reason is satisfied by the file's role, and the honest form is a **role policy**: a per-file-ignore keyed to the role (`tests/**`, `**/cli.py`, `scripts/*.py`), decided once by the owner, with a two-line rationale in the config. It is a policy, not a suppression, and it is not this skill's to write — the agent names it on `Config notes:` and, until it exists, fixes the code in front of it the honest way (a logger, or one declared output function that the module calls, never `sys.stdout.write` in place of `print`). Three things keep role policies from becoming the miscalibration they replace: the role is a *file kind*, not a file that happened to be hard; the relaxed rules are the ones whose reason the role satisfies, nothing more; and the same policy is spelled identically across sibling packages.

Tests are the role where this matters most, because the rules that carry design signal split into two groups there and agents disagree unless the split is stated.

**Rules that lose most of their signal in tests — relaxed once, repo-wide, for `tests/**`, with a two-line rationale, by the owner:** WPS202 and WPS201 (a test module is legitimately a flat list of scenarios with many imports), WPS226 and WPS432 (test data is literals; naming every one hides the scenario), WPS118 (test names are sentences), WPS437 and WPS442 (tests reach into internals and shadow fixtures by design). Relaxing these per file, or differently in sibling packages, is the miscalibration; relaxing them once for the test tree is a policy, and this skill's job is to name the policy on the `Config notes:` line, not to edit it in.

**Rules that keep their signal in tests — treated exactly as in production:** WPS210, WPS213, WPS231, WPS220, WPS222, WPS204. A test with seven locals has an arrange block that wants a fixture or a builder; a nested loop over cases wants `parametrize`; an idiom repeated twelve times across a module wants one helper with a domain name. These are the same missing concepts this skill hunts everywhere, and they matter *more* in tests, because the suite is the document a maintainer reads first. Fix them structurally and report them with the same receipt as production code.

---

## Rung 7 — suppression, and what it costs

Sometimes the linter is wrong. A registry that is genuinely a flat list of same-kind facts will trip WPS202, and splitting it makes things worse. A numerical kernel will trip WPS210 and WPS221 for real mathematical reasons. A zero-exception policy would force the bad refactor, so an honest exit must exist.

But the exit is where this skill fails most often, and it fails one way: **the agent reaches it by assertion.** "The class is cohesive", "flat by design", "every local is load-bearing", "it is only one over", "the docstring calls it the one shared module", "the structural option is half a day" — each sounds like a finding and none is checkable. An exit reachable with a sentence will be reached with a sentence. So the exit is a rung with a receipt, and the receipt has three parts a reader can verify.

### Part 1 — the forcing constraint is one of three falsifiable kinds

| Kind | Qualifies | Verify by |
|---|---|---|
| **External contract** | The file is copied into a container as a single artifact; a third-party API fixes the method set; a wire format fixes the field names | Point at the deployment line, the upstream signature, the spec |
| **Homogeneous table** | One record type plus N instances; N same-kind functions in one registry; a contract module of zero-logic types | The kind column above has one entry |
| **Mathematical necessity** | A kernel whose intermediates have no domain names because they are steps of one derivation | Try to name the two halves; if you cannot, the seam does not exist |

What never qualifies: a docstring or a past decision ("flat by design", "the only shared module") — these record a *location* and a *history*, and rapier's encounter check already says age is not a forcing requirement; a comment is age written down. Cohesion asserted without the kind column. "Load-bearing" asserted without the locals audit. The size of the overage — a threshold is where the signal starts, not a tolerance band, and "one over" in a module you expect to grow is "three over" next quarter. The cost of the alternative — cost is reported to the user, never used to decide.

### Part 2 — every lower rung has a written verdict

You may not reject a shape you have not drafted. "Deeper bundling — rejected: displacement" is a claim; the evidence is the drafted record with its fields listed and the born-at column showing they come from different seams. Write this next to every suppression in the report:

```
Suppression receipt — <file:symbol>, <rule>
Constraint kind:  external contract | homogeneous table | mathematical necessity
Constraint:       <the checkable fact, with its location>
Rung 0 delete:    nothing — all N members have live callers: <list> | <what was deleted>
Rung 1–2:         n/a because <...> | tried: <...>
Rung 3–4:         drafted <Table/Record>(fields=[...]); rejected because <born at different seams / consumed by different callers>
Rung 5–6:         n/a — variants differ in one behavior | drafted: <...>
Scope:            line | module        (narrowest that works)
```

A rung line reading "not tried" makes the receipt incomplete and the suppression unearned. Rung 0 in particular: a stub, a `NotImplementedError`, a hook with zero callers, a "planned feature" marker inside a class that trips WPS214 — these are rung 0, and deleting one (version control remembers) or implementing it usually drops the count below the line by itself. Choosing a suppression while a stub is still in the class is the clearest failure this skill produces.

### Part 3 — scope, and what counting suppressions means

The ladder of scope stops at the module:

1. **Line-level** `# noqa: WPS226 — <reason>` for a single site.
2. **Module-level**, in the module docstring (`flake8: noqa: WPS202 — <reason>`), when the whole file is one homogeneous concept. One home, one reason, visible in the file it governs. Also the right scope when one rule fires many times on one concept in one file: one suppression, not fourteen.
3. There is no rung 3. Config is not a fix and is not offered as one. A change that belongs in config is a decision about the project, made by its owner outside this task; if the code in front of you seems to need it, that is a `Config notes:` observation.

When the same rule earns a *receipted* suppression in a third module of the repo, that pattern goes on `Config notes:` as an observation — "three registries in this package trip WPS202; if the package is declarative by nature the owner may want a package-level value" — never as a recommendation. Two things are routinely misread here:

- **Only receipted suppressions count.** Five proposed `noqa`s with no Part-2 receipts are five unfinished refactors, not five strikes. Counting your own untried suppressions and concluding the threshold is wrong is circular.
- **A threshold is calibrated to a property of the domain**, never to how many times a refactor felt hard. The observation names the property ("numerical kernels", "declarative registries", "test scenario lists"); if you cannot name one, there is no observation, only unfinished work.

---

## Precedence with rapier

Rapier's Tripwire 7 says: *a linter fix that adds structure → stop and ask*. This skill supersedes that tripwire, but not the rest of rapier. The resolution:

1. **Deletion outranks everything.** Rapier's deletion pass runs first. Code that should not exist cannot be linted into shape, and a WPS violation on dead code is a signal to delete, not to refactor. Rung 0 of the shape menu is rapier's rung.
2. **Once code has earned its place, this skill governs its shape.** Rapier's "don't add abstraction" instinct does *not* veto naming a concept that a violation exposed, because rungs 3–5 (table, dataclass, enum) reduce total complexity — they make the N+1 edit smaller. Rapier's ladder measures *layers*; this skill measures *places you must edit*. When a change lowers the second while raising the first slightly, take it.
3. **Rapier still vetoes speculation.** WPS223 firing on a three-branch chain is a reason for a three-entry table, not for a plugin system, an entry-point registry, or a config schema. Rapier's Tripwire 2 (an abstraction with exactly one user) and Tripwire 6 (building for an unstated requirement) remain in force. If the shape you chose has one member, it is a rename, not a concept.
4. **Tool choice still precedes style conformance.** If the right answer was a 20-line shell script, do not build a Python class hierarchy because the Python linter is the one that ran.
5. **Rapier's flatness is about hops, not files.** Its ladder and its "flatten past ~3 files" question measure how far a reader travels to follow one execution path. Turning a shared module into a package with a re-exporting surface changes where names live, not how many calls deep a path goes nor where consumers import from; it is not a ladder climb and rapier does not veto it. What rapier does veto is the *class* that a split might tempt you into when three functions would do.
6. **"Documented" is not a forcing requirement in either skill.** Rapier's encounter check strips existing structure of the authority of a past decision; this skill strips existing *flatness* of the same authority. A docstring saying "the one shared module" or "flat by design" is a statement of history that both skills read and neither obeys. The forcing requirement has to be nameable today, in one sentence, of one of the three kinds in Rung 7.
7. **Stubs are rapier's evidence and this skill's rung 0.** A method that raises `NotImplementedError` or has no caller is Tripwire 2 evidence against its interface for rapier and a deletion for this skill. Neither skill lets it hide under a `noqa`.

---

## Reference files

- `references/catalog.md` (section I covers the style rules whose fixes are most often respelled) — 40+ WPS and ruff rules with the typical cheat and the structural fix for each. **Read this whenever a violation code appears that you have not just handled.** Look up the specific code rather than reasoning from the rule name; several WPS names are misleading about what they are actually measuring.
- `references/worked-examples.md` — seven before/after cases at different rungs: parallel dispatch tables, a complexity split, deletion before abstraction, the one honest suppression, an orchestration `main()` through the seam test *and* the locals audit, a "flat by design" shared module through the homogeneity test, and a WPS214 class whose real fix was rung 0. Read example 5 before deciding a `main()` cannot be decomposed; read 6 before writing "one concept, flat by design"; read 7 before suppressing on a class that has a stub in it.

**These examples are directional, not templates.** They show what "the concept got a home" looks like in one domain. Adapt the reasoning — the sentence in step 3 and the receipt in step 6 — to the code in front of you. An example copied structurally into a project where it does not fit is itself a WPS-refactor failure: it is displacement with extra steps.
