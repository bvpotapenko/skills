# Violation catalog — what each rule is actually measuring, how agents cheat it, what the real fix is

Look up the code you were given. Do not reason from the rule's *name* — several WPS names describe the symptom rather than the measurement, and the fix follows from the measurement.

Rule numbers shift slightly between wemake-python-styleguide major versions. Trust the message text in the flake8 output over the number in this file; if they disagree, the output wins.

**Contents**
- [A. Magic values and vocabulary](#a-magic-values-and-vocabulary)
- [B. Function size and complexity](#b-function-size-and-complexity)
- [C. Control flow shape](#c-control-flow-shape)
- [D. Module and class shape](#d-module-and-class-shape)
- [E. Naming](#e-naming)
- [F. Coupling and access](#f-coupling-and-access)
- [G. Ruff rules that carry design signal](#g-ruff-rules-that-carry-design-signal)
- [H. Rules where the mechanical fix is correct](#h-rules-where-the-mechanical-fix-is-correct)

---

## A. Magic values and vocabulary

**WPS226 — OverusedStringConstant**
- Measures: the same string literal appears more than N times in one module.
- Cheat: define a constant with the identical value, substitute it at the flagged sites only, leave the rest as raw strings.
- Fix: a string repeated across a module is almost always a **key into an implicit registry**. Make both explicit — a closed key set (enum) and a single mapping keyed by it. Then ask where the string comes from: if it crosses a boundary (JSON field, CLI flag, filename, HTTP header) it belongs to an external contract, so parse it into the internal type once at the boundary and never let the wire spelling travel inward.
- Sweep: `grep -rn '"<the literal>"'` must return hits only at the definition site and the boundary parser.

**WPS432 — MagicNumber**
- Measures: a numeric literal other than a small allowed set appears in an expression.
- Cheat: `TWO = 2`, `THRESHOLD_095 = 0.95` — renaming the value rather than naming its meaning.
- Fix: name what the number *means in the domain*, not what it *is*: `RGB_CHANNELS = 3`, `KL_ALERT_THRESHOLD = 0.05`. Then check whether it is a *tuning knob* rather than a fact — knobs belong in a config dataclass field with a default, not as a module constant, because a knob will eventually need to differ per run and a constant makes that a rewrite.

**WPS407 — MutableModuleConstant**
- Measures: a module-level `dict`/`list`/`set` bound to an uppercase name.
- Cheat: convert to a tuple of pairs, losing O(1) lookup and readability.
- Fix: `MappingProxyType(...)` for a genuine lookup table is the correct answer and should be used freely. But treat the violation as a prompt to ask whether the table is the *single* home for its concept, or one of several parallel tables keyed by the same thing — parallel tables are the strongest signal in this entire catalog that a record type is missing (see worked example 1).

**WPS115 — UpperCaseAttribute**
- Measures: a class body assigns an uppercase name.
- Cheat: lowercase the name, hiding that it is a constant.
- Fix: if it varies per instance it is a field (dataclass or `__init__`); if it is shared and constant it belongs at module level or on an enum. The rule is asking you to decide which, because uppercase-in-class-body is ambiguous to readers.

**WPS204 / WPS203 — OverusedExpression (function / module scope)**
- Measures: the same non-trivial expression (`self.config.model.dtype`, `len(items) - 1`) appears N+ times.
- Cheat: assign it to `tmp` or `val` at the top of the function.
- Fix: a repeated expression is an unnamed concept. If it derives from one object, it is a `@property` or a method on that object. If it derives from several, it is a small function whose name states the derivation. Naming it locally with a meaningful name is acceptable; naming it `tmp` converts one problem into two (see WPS110).

---

## B. Function size and complexity

**WPS211 — TooManyArguments** (also ruff `PLR0913`)
- Measures: parameter count.
- Cheat: `**kwargs`, or `config: dict[str, Any]`, or bundling unrelated parameters into a tuple.
- Fix: look for **clusters that always travel together at every call site** — that cluster is a missing frozen dataclass, and its name is a domain noun (`ModelBundle`, `RunSpec`, `SamplingConfig`). Verify by checking callers: if callers already construct the same three values in the same order everywhere, the type exists already, undeclared. If no cluster exists and the parameters are genuinely independent, the function is doing several jobs — split by *job*, not by parameter count.
- Companion signal: if some parameters are unused by some code paths (ruff `ARG`), the signature is a union of several different signatures. That is a dispatch problem, not an argument-count problem.

**WPS210 — TooManyLocalVariables**
- Measures: count of local names.
- Cheat: reuse one variable for several purposes, or inline expressions to avoid naming them — both make the function harder to read while the counter drops.
- Fix: group the locals. They almost always fall into 2–3 clusters that are each computed together and used together; each cluster is either a returned record type or a separate function whose return value is that cluster. Split at the point where a *value is complete*, not at a line number.

**WPS213 — TooManyExpressions** and **WPS231 / PLR0915 — CognitiveComplexity**
- Measures: statement count and branch-nesting-weighted complexity.
- Cheat: cut the function in half at an arbitrary line into `_step_a`/`_step_b` that pass 8 locals between them.
- Fix: find the **seams** — the points where the function finishes producing one thing and starts producing the next. A good extraction has a narrow interface (1–3 arguments, one return value) and a name that is a noun phrase or a verb on a domain object. If your extraction needs 6 parameters, it was cut at the wrong place; put it back and look for the real seam. Frequently the true fix is upstream: the function branches on a type code, and once dispatch moves to a table the body becomes linear.

**WPS212 / PLR0911 — TooManyReturns**
- Measures: return statement count.
- Cheat: a single `result` variable mutated through the function and returned at the end. This is worse — it converts explicit exits into implicit state.
- Fix: many returns means many outcomes. Either the outcomes are a closed set (make them an enum or a small result type) or the function is a dispatcher (make it a table lookup). Early-return guard clauses are *not* the problem and should survive; the rule is aimed at scattered exits from deep inside nested blocks.

**WPS238 — TooManyRaises**
- Measures: distinct `raise` statements in one function.
- Cheat: raise one generic exception with a formatted message, discarding the type distinction callers depend on.
- Fix: separate validation from execution. A validation function that checks preconditions and raises, followed by a body that assumes them, reads better and localizes the raises. If callers genuinely need to distinguish the failures, keep the types and split the function.

**WPS229 — TooLongTryBody**
- Measures: statements inside `try`.
- Cheat: shrink the `try` by moving statements after it — which silently changes which failures are caught.
- Fix: the `try` should wrap exactly the operation that can raise the exception being handled. Everything else moves *out*, before or after, deliberately. This is the rule most likely to introduce a real bug when fixed carelessly — verify behavior, not just the counter.

**WPS217 / WPS216 / WPS225 — TooManyAwaits / Decorators / ExceptCases**
- Measures: counts within a function.
- Cheat: merge except branches into `except Exception`, stack decorators onto a wrapper.
- Fix: many excepts means the body spans several failure domains — split by domain. Many awaits often means sequential I/O that wants `asyncio.gather`, or a function coordinating too many collaborators.

---

## C. Control flow shape

**WPS223 — TooManyElifs**
- Measures: length of an `elif` chain.
- Cheat: convert to nested `if`s (trips WPS220 instead), or to `match` with the same branch bodies, or split the chain across two functions.
- Fix: an elif-chain whose branches differ only in the *value or callable they produce* is a table. Replace it with one mapping from key to value, plus one explicit failure for unknown keys. An elif-chain whose branches genuinely *do different things with different data* is polymorphism — but only reach for that when more than one behavior varies (SKILL.md rung 6). `match` is not a fix; it is the same branching with newer syntax.
- Do not silently default. `return Family.MINICPM` as a fallback hides unknown inputs; `raise ValueError(f"unknown engine: {engine}")` surfaces them at the boundary where they can be fixed.

**WPS222 — TooManyConditions**
- Measures: boolean operators in one condition.
- Cheat: split into nested `if`s, moving the complexity into nesting depth.
- Fix: the compound condition is an unnamed predicate. Extract it as a function or property whose name states the *business meaning* (`is_eligible_for_scoring`), not its structure (`check_a_and_b`). If the predicate is checking membership in a set of values, it is a table lookup.

**WPS220 — TooDeepNesting**
- Measures: indentation depth.
- Cheat: extract the innermost block into `_inner()` taking 7 parameters.
- Fix in this order: (1) guard clauses — invert the conditions and return/continue early, which usually removes two levels for free; (2) if the nesting is loops over a cross-product, flatten with `itertools.product` or by iterating a pre-built list of cases; (3) only then extract, and extract the *whole* inner loop as a function over one domain object.

**WPS228 — TooLongCompare** and **WPS505 — NestedTernary**
- Cheat: assign parts to temporaries with meaningless names.
- Fix: same as WPS222 — the comparison chain is a predicate wanting a name, or a range check wanting a small value object.

**WPS430 — NestedFunction**
- Measures: a `def` inside a `def`.
- Cheat: move it to module level with an underscore prefix and pass all the closed-over state as parameters — which usually produces a 6-parameter private helper nobody else can use.
- Fix: ask what the closure was capturing. If it captured state, that state plus the function is a small class or a `functools.partial`. If it captured nothing, it is a plain module-level function and moving it is correct. If it was a one-line callback, a lambda in a table entry or a comprehension often removes the need entirely.

**WPS426 — LambdaInsideLoop**
- Measures: a lambda defined in a loop body (late-binding hazard).
- Cheat: `lambda x, _bound=value: ...` default-argument trick.
- Fix: the loop is building a collection of callables — that is a registry. Build it as a dict/tuple of named functions or `functools.partial` objects, which also fixes the readability problem the default-arg trick creates.

**WPS440 / WPS441 — BlockAndLocalOverlap / ControlVarUsedAfterBlock**
- Measures: a loop or `with` variable shadowing or leaking outside its block.
- Cheat: rename to `item2`.
- Fix: the loop is computing a value that outlives it. Extract the loop into a function that *returns* that value; the variable then has an explicit name and lifetime. This is one of the highest-value fixes in the catalog because leaked loop variables are a real bug class.

---

## D. Module and class shape

**WPS202 — TooManyModuleMembers**
- Measures: top-level definitions in a module.
- Cheat: move the overflow into `helpers.py` — splitting by *count*, so one concept ends up in two files and the import graph gets worse.
- Fix: split by **concept**, not by size. Read the member names and group them: if the module contains "things that define the model families" and "things that run a scoring pass", those are two modules with a one-directional dependency. If every member genuinely belongs to one concept and the module is just large (a registry, a protocol definition), that is a legitimate suppression case — say so.

**WPS201 — TooManyImports** and **WPS235 — TooManyImportedModuleNames**
- Measures: import count.
- Cheat: `import package` instead of `from package import a, b, c` — the dependency is identical, only the counter changed.
- Fix: a module importing 20 things is coordinating too much. Usually a cluster of imports serves one job that should be its own module; move the job and the imports with it. Look at which imports are used by which functions — the grouping is usually obvious and matches the WPS202 split.

**WPS214 — TooManyMethods**
- Measures: method count on a class.
- Cheat: move methods to module-level functions taking the instance as the first argument.
- Fix: the class has more than one responsibility. Group methods by *which attributes they touch* — clusters that touch disjoint attribute sets are separate classes. If all methods touch all attributes, the class is cohesive and this is a suppression candidate.

**WPS230 — TooManyPublicAttributes**
- Fix: same clustering analysis as WPS214, applied to fields. Frequently a subset of fields is a nested value object (`ModelPaths`, `RunLimits`), which also fixes the WPS211 in the constructor.

**WPS232 — CognitiveModuleComplexity**
- Fix: this fires when many functions are individually acceptable but the module as a whole branches heavily. Usually one dispatch decision is being re-made in several functions — centralize it once (a table) and the module-level number falls without any splitting.

**WPS100 / WPS102 — WrongModuleName**
- Measures: module named `utils`, `helpers`, `common`, `misc`, `base`, `tools`, or non-conforming.
- This rule exists to catch the WPS202 cheat. If you just created the file to relieve a count, that is the confession — go back and split by concept.
- Fix: name the module after the concept it owns. If you cannot, it does not own one.

**WPS412 — InitModuleHasLogic**
- Fix: `__init__.py` re-exports; behavior lives in named modules. Move the logic to a module named after what it does and import it.

**WPS600 / WPS601 / WPS602 / WPS605 / WPS615**
- `WPS600` subclassing a builtin: use composition or `UserDict`/`UserList`, or accept that you wanted a dataclass with one field.
- `WPS615` unpythonic getter/setter: `get_x()`/`set_x()` become an attribute or a `@property`. The cheat is renaming to `x_value()`; the fix is removing the accessor layer.
- `WPS602` staticmethod: a static method with no relationship to class state is a module function; move it out rather than converting to `classmethod`.

---

## E. Naming

**WPS110 — WrongVariableName** (`data`, `result`, `item`, `value`, `handle`, `content`, `info`, `params`, `obj`, `temp`)
- Cheat: `data` → `data_`, `data2`, `my_data`, `input_data`. All of these trip WPS120 or convey nothing.
- Fix: name what it *is in this domain*: `manifest`, `logits`, `token_ids`, `family_spec`. If you cannot name it specifically, the variable is holding several unrelated things — that is the real finding, and it usually means a missing type. This rule is much more valuable than it looks: it is a cheap detector for undeclared types.

**WPS111 — TooShortName**
- Cheat: `x` → `xx`.
- Fix: domain name. Legitimate exceptions exist (mathematical indices in a tight numerical loop, `i`/`j` in a matrix kernel) — those are honest suppression candidates with a one-line reason.

**WPS118 — TooLongName**
- Cheat: truncate to an abbreviation nobody can read.
- Fix: a very long name is usually describing a compound concept (`deepseek_prompt_scorer_batch_size`). The compound is a type; once `DeepseekScorer` has a `batch_size` field, the name is short because the context carries the rest.

**WPS120 — TrailingUnderscore** and **WPS114 — UnderscoredNumberName**
- These exist to catch the WPS110/WPS111 cheats. Their appearance in a diff is direct evidence of a dodge.

**WPS125 — BuiltinShadowing** (`id`, `type`, `input`, `list`, `filter`)
- Cheat: `type` → `type_`.
- Fix: qualify with the domain: `model_type`, `record_id`, `raw_input`. The name is under-specified, not merely colliding.

**WPS122 — UnusedVariableIsDefined**
- Fix: delete it. If it exists to document a tuple unpacking, `_` (or `_unused_name`) is fine — but check first whether the value is genuinely unused or whether you dropped a return value you needed.

---

## F. Coupling and access

**WPS219 — TooDeepAccess** (`a.b.c.d.e`) and **WPS233 — long call chain**
- Cheat: assign the chain to an intermediate variable, hiding the coupling without reducing it.
- Fix: this is a Law of Demeter violation — your code knows too much about a structure it does not own. Either the owning object should expose what you need directly (add a property there), or you should be passed the leaf rather than the root. Ask: "why does this function receive the whole config when it only needs the dtype?" Frequently the answer collapses a WPS211 at the same time.

**WPS437 — ProtectedAttributeUsage**
- Cheat: `getattr(obj, "_thing")` — same coupling, now invisible to the linter *and* to the type checker.
- Fix: either the attribute should be public (the underscore was wrong), or the accessing code belongs inside the owning class, or you need a real accessor. If the object is third-party and there is no supported path, that is a legitimate suppression with a reason naming the upstream gap.

**WPS234 — OverlyComplexAnnotation**
- Cheat: `Any`, `object`, or dropping the annotation.
- Fix: a nested annotation like `dict[str, list[tuple[str, float]]]` is a type wanting a name. Introduce a type alias at minimum, a dataclass or `NamedTuple` if it has behavior or if the tuple positions are meaningful. The annotation's complexity is a direct measurement of missing domain vocabulary.

**WPS425 — Boolean non-keyword argument**
- Cheat: rename the parameter.
- Fix: make it keyword-only (`*, strict: bool`), or — better when the flag selects between two behaviors — split into two named functions. A boolean parameter at a call site (`score(model, True, False)`) is unreadable regardless of what the linter says.

**WPS442 — OuterScopeShadowing**
- Fix: rename the *inner* name to something more specific, or recognize that the function is reaching for module state it should receive as a parameter.

**WPS421 — WrongFunctionCall** (`print`, `eval`, `exec`, `breakpoint`, `globals`)
- Cheat: `getattr(builtins, "print")`, or wrapping `print` in a function named something else.
- Fix: `print` → a `logging` call at the right level, or an explicit write to a stream the caller passes. `eval`/`exec` → a dispatch table (again). Debug leftovers → delete.

**WPS402 — TooManyNoqaComments**
- If this fires, the previous pass cheated. Treat it as an audit finding: revisit the suppressed sites and fix them properly, or make the config decision explicitly.

---

## G. Ruff rules that carry design signal

**ARG001 / ARG002 / ARG005 — unused argument**
- Cheat: `del unused`, `_ = unused`, prefix with `_`, or `# noqa: ARG001`.
- Fix: **this is the single most under-rated design signal in the list.** An unused parameter means the signature is the union of several different signatures forced into one shape. If three functions share a signature and each ignores a different subset, they do not want a uniform interface — they want either per-variant constructors, or one context object each reads what it needs from. A comment saying "ignores the arguments its model family does not use" is a bug report about the design, written by the person who wrote the design.

**PLR0912 — too many branches**, **PLR0915 — too many statements**
- Ruff twins of WPS231/WPS213; same treatment.

**B006 — mutable default argument**
- Cheat: `= None` plus `if x is None: x = []` is the standard correct fix and is fine. The cheat is `= ()` when the function then mutates it.
- Fix: default to `None` and construct inside, or make the parameter required.

**B008 — function call in default argument**
- Fix: same pattern; a call in a default is evaluated once at import time, which is almost always a latent bug rather than a style issue.

**F841 — unused local variable**
- Fix: delete — but first check whether the assignment was capturing a return value the code should be using. Unused locals sometimes mark a dropped error path.

**SIM102 / SIM114 / SIM117 — collapsible if / with**
- Usually correct to apply mechanically. Push back when the collapsed form pushes the line past readability or hides a meaningful staging of conditions; in that case the honest fix is naming the predicate (WPS222 treatment), not the collapse.

**SIM108 — if-else to ternary**
- Apply when both branches are short expressions. When the branches are non-trivial, a ternary is a readability regression; extract a named predicate or keep the if-else and suppress with a reason.

**TRY300 / TRY301 — return/raise inside try**
- Related to WPS229; the fix is the same narrowing of the `try` body, with the same warning about changing which failures are caught.

---

## H. Rules where the mechanical fix is correct

Apply and move on. Spending design thought here is the opposite failure — it wastes time and often makes the change riskier.

`I001` import sorting · `UP` pyupgrade rewrites · `E`/`W` whitespace and formatting · `C4xx` comprehension simplification · `F401` unused import (delete it) · `RET504` redundant assignment before return · `RET505` `else` after `return` · `WPS336` implicit string concatenation · `WPS339`/`WPS358` number literal formatting · `WPS420` stray `pass` · `WPS503` useless returning `else` · `WPS504` negated condition (invert it) · `WPS507` useless `len()` compare · `WPS510` `in` against a list (use a set or tuple) · `WPS513` implicit `elif` · `WPS529` `if k in d: d[k]` (use `d.get`) · `PTH` pathlib migrations.

The one caution: apply these *after* the structural work, not before. Mechanical fixes on code you are about to restructure are wasted diff and make the real change harder to review.
