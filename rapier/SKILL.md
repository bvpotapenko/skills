---
name: rapier
description: "Enforce minimal, simplest-thing-that-works implementations and catch over-engineering before it compounds. Use this skill at three moments: (1) BEFORE writing any code, plan, or architecture — to pick the simplest viable shape and declare a complexity budget; (2) AFTER producing code, a plan, or a design — to run a deletion pass and cut what isn't earning its place; (3) WHILE READING existing code — to give encountered abstractions the same scrutiny as new ones and flag those that don't earn their keep, even unasked. Trigger whenever the user asks to build, implement, design, plan, refactor, review, or explore anything; whenever your working files contain interfaces, base classes, factories, registries, or NotImplementedError stubs; whenever new work is routed around an existing abstraction; whenever a solution grows past its estimate; whenever you're patching around environment mismatches; and whenever the user mentions simplicity, over-engineering, bloat, MVP, 'keep it simple', or 'is this too much'."
---

# Rapier — the simplest thing that works

One precise hit beats a heavy swing. Small working iterations shipped today are worth more than architecture shipped next week, because every layer, dependency, and abstraction is a future failure point that someone (probably the user) pays for in debugging hours. This skill exists because "don't over-engineer" is a vibe that agents rationalize away mid-task. Vibes don't stop you at line 400; tripwires do. Everything below is phrased as a check you either pass or fail.

Apply the skill in three passes: the **design gate** before you build, the **deletion pass** after, and the **encounter check** whenever you read code you didn't write. The third exists because the first two share a blind spot: they only see what this session produces, and most of the complexity you'll ever meet was produced by somebody else.

---

## Pass 1 — The design gate (before building)

### 1a. State the budget out loud

Before writing anything, declare in one or two sentences: what you'll build, its rough size, and what you will NOT build.

> "Plan: one ~60-line script, no new dependencies, no config file. Not building: retry logic, parallelism, a CLI framework."

The budget isn't a formality — it's the anchor that makes drift *visible*. Without a stated estimate, "just one more helper class" never registers as a violation. With it, blowing 2x past the budget is an objective event that triggers a stop (see Tripwire 4).

When the user *explicitly asks* for extensibility, robustness, or future-proofing, that's a stated-but-future requirement: answer it with the cheap path — show in one sentence how the simple design accommodates it later ("a new channel = one 15-line function added the day you pick it") — and build only what's needed today. Don't build the machinery, and don't ignore the ask.

### 1b. Start at the bottom of the ladder

Each rung of complexity must be *forced* onto you by a requirement you can name in one sentence. If you can't name it, stay on the lower rung.

```
inline command / one-liner
  └─> single flat script (.sh or .py)
        └─> a few scripts composed via stdio/files
              └─> module with functions
                    └─> package with classes
                          └─> service / framework / daemon
```

### 1c. Default answers

When a design decision comes up, these are the defaults. Deviating requires a stated reason, not a feeling:

| Decision | Default | Climb only when... |
|---|---|---|
| Function vs class | Function | State genuinely persists across many calls |
| Script vs framework | One script per task family | Scripts start duplicating >30 lines of shared logic |
| Config file vs constants | Constants at top of file | A non-developer must edit values |
| New dependency vs stdlib/shell | stdlib/shell | Reimplementing would take >20 focused lines |
| Abstraction vs copy-paste | Copy-paste twice; abstract on the 3rd use | The third concrete use actually exists — and all three use the *whole* interface (a use that stubs methods doesn't count) |
| Concurrent vs sequential | Sequential | Measured (not imagined) runtime is unacceptable |
| Generic vs hardcoded | Hardcoded for the current case | A second real caller needs the variation today |

---

## Tripwires — stop and ask

These fire mid-work. When one fires, stop, state which tripwire fired, and ask the user before continuing. The whole point is that they fire *early* — by the time a human notices the grind, the hours are already gone.

1. **Second workaround for the same root cause.** One workaround is pragmatic; two means you're patching code to fit a broken context. The default fix is to change the environment, not the code: align the version, install the driver, use the tool the code was written for. Stop and say: "The root cause is X; I can fix X directly, or keep patching around it — which do you want?"
2. **An abstraction without genuine users.** A base class, interface, plugin hook, or config schema serving a single concrete case is speculation — inline it. And count users *honestly*: an implementation that stubs interface methods (`NotImplementedError`, `pass`, "unsupported" mixins) is evidence against the interface, not a use of it; a caller that still branches on concrete type is telling you the interface bought no polymorphism; a factory or registry enumerating ≤3 fixed entries for one call site is an if/elif with extra steps. Three implementations can still add up to zero genuine users.
3. **A dependency for a 20-line job.** If stdlib, shell, or a short function covers it, don't import a package for it.
4. **2x past the declared budget.** Size or file count doubled past your Pass-1 estimate → the estimate was wrong or the approach is. Stop and re-scope; don't quietly absorb it.
5. **A part that can't run alone.** If a step can't be executed and debugged in isolation, the design is too coupled. Decouple before adding more.
6. **Building for an unstated requirement.** "Might need it later" is not a requirement. If nobody asked for it, cut it — it can be added the day someone does.
7. **A linter fix that adds structure.** If silencing a style/complexity warning requires a new class, layer, or file, stop — see "Linters" below. A warning is a signal, not a requirement.
8. **New work routed around an existing abstraction.** If the natural way to add a feature is to bypass the interface/factory/framework that was supposed to host it, the abstraction has failed at its one job — being general. This is the architectural twin of Tripwire 1: the bypass is a workaround, and by the second bypass the problem is provably the structure, not the cases. Don't leave it standing as a false map of the codebase (the next reader will assume everything routes through it); flag it for deletion alongside the new work. This fires whether the bypass is yours or already sitting in the repo when you arrive.

---

## Linters and complexity metrics

Linters (flake8/WPS, ruff, pylint, cognitive-complexity checkers) measure *local* complexity: branches per function, variable and argument counts, expression depth. They are blind to *structural* complexity: layers, indirection, hops needed to trace one execution path — the kind this skill fights. Satisfying a local metric by adding indirection is a complexity transfer, not a reduction: the counters go green while the code gets harder to follow. Coordinate the two like this:

- **Tool choice precedes style conformance.** The ladder decision comes first. If the right rung is a flat shell script, the Python linter never applies — never choose a class-heavy Python design because the toolchain happens to lint Python.
- **Fix-preference order for a violation** (best to worst): delete the offending code → simplify inline (early returns, clearer decomposition, better names) → extract a flat function in the same file → extract a module → extract a class. The last two are ladder climbs and need a named forcing requirement; the warning alone is never one.
- **A justified suppression beats an unneeded abstraction.** When nothing above "extract module" resolves it, a targeted `noqa`-style suppression with a one-line reason is the honest fix — same spirit as a KEEP line. Keep suppressions rare: if they multiply, the linter config is miscalibrated for the project (fix it config-level, e.g. relaxed rules for a scripts directory), and that's worth flagging to the user.

---

## Pass 2 — The deletion pass (after building)

Run this on whatever is in front of you — code just produced, a plan, an architecture sketch, someone else's draft, or existing code you're reading (Pass 3 governs what to *do* with findings there). Answer each question concretely; "looks fine" is not an answer.

0. **Is this the right rung at all?** Before trimming within the design, re-check the ladder: could the whole thing be a lower rung (a script, a shell pipeline, a cron line)? The biggest simplifications come from re-rung, not from trimming.
1. **What deletes with zero behavior change?** Unused parameters, dead branches, hooks with no caller, defensive checks for impossible states.
2. **Which two layers merge?** Any wrapper that only forwards to the thing it wraps collapses into it.
3. **What is hardcodable?** Every knob nobody turns becomes a constant; every config entry with one-ever value gets inlined.
4. **Can each step run in isolation?** If not, that's the next simplification target.
5. **Would a new reader trace the main path in one sitting?** If tracing one request/run requires jumping through more than ~3 files, flatten.

Then report in this shape before applying anything:

```
Deletion pass on <artifact>:
- CUT <thing>: <why behavior is unchanged>       (~N lines)
- MERGE <A> into <B>: <why the layer adds nothing>
- KEEP <thing>: <the one-sentence requirement that forces it>
Net: <before> -> <after> lines, <D> deps -> <D'> deps
```

The KEEP lines matter as much as the cuts — this skill is a bias, not a ban. Real requirements (correctness that must be proven, measured scale, external contracts, safety-critical checks) legitimately force rungs up the ladder, and they survive every pass because their forcing requirement is *present and nameable in one sentence* — and that sentence gets written next to the complexity it justifies. "We'll probably need it" never qualifies; "the client's interface requires it" always does.

---

## Pass 3 — The encounter check (reading code you didn't write)

The blind spot this pass exists for: an agent that would never *build* a factory for three fixed cases will happily *conform* to one it finds, because existing code arrives wearing the authority of a decision already made. It has none. Age is not a forcing requirement, and neither is looking like textbook clean code — Protocol + factory + DI reads as professional precisely because it's the pattern, which is how it survives session after session while the tracing hours pile up inside it. Existing structure must name its forcing requirement under exactly the same rules as new structure.

So whenever the files you're reading or touching for the current task contain an abstraction — interface/Protocol/ABC, base class, factory, registry, plugin hook, mixin, config schema — run deletion-pass questions 0–2 on it mentally and check it against Tripwires 2 and 8. This is an observation pass over your working set, not an audit of the whole repo.

What you do with a hit differs from Pass 2, because nobody asked you to rewrite this code, and an uninvited refactor is its own kind of budget blowout. Flag it in 2–3 lines — the evidence plus the collapsed shape — offer it as a follow-up, and continue the task you were given:

> "Flag: `engines/` is a Protocol whose three implementations each stub half the methods, and the only caller still branches on type — an if/elif wearing an interface. Collapses to one flat script per family plus a small shared-functions file (~9 files → 4). Want that as a follow-up, or leave it?"

Calibration: **silence is the default.** A structure that passes — implementations that fill the whole interface, a caller that never type-checks, a registry that's genuinely open-ended — gets a mental KEEP and no comment. One flag per structure per conversation; if the user declines, it stays declined.

---

## Few-shot examples

**1 — Version mismatch (environment vs code)**
Task: model code written for library X 4.x is running against X 5.x; imports and APIs break.
Over-engineered: a chain of try/except imports, config shims, and API wrappers to make the code 5.x-compatible.
Rapier: flag the mismatch immediately, pin X to 4.x, run. One line in a requirements file instead of six fragile patches. Ask before ever choosing the patch path.

**2 — Evaluation harness (system design)**
Task: run several families of evaluations against a system regularly.
Over-engineered: a Python framework — runner base class, plugin registry, YAML config schema, results ORM.
Rapier: one flat shell script per eval family, sharing a small common env file; each independently runnable; a container wraps the working scripts for reproducibility, it doesn't justify deeper architecture.

**3 — One-time data pull (code)**
Task: fetch ~200 records from an API and save them.
Over-engineered: an async client class with retry/backoff decorators, a caching layer, and a CLI.
Rapier: a plain loop with a request and a sleep, writing to one file. If it fails, rerun it.

**4 — Internal tool (architecture)**
Task: a tool used by five people, a few times a day.
Over-engineered: three services, a message queue, a deployment pipeline.
Rapier: one process, a cron entry, and SQLite. Revisit when a measured load, not an imagined one, breaks it.

**5 — Two variants (refactoring)**
Task: a function needs slightly different behavior in a second context.
Over-engineered: extract an abstract base class and a strategy pattern.
Rapier: an if-branch or a parameter. The pattern earns its place at the third variant — if it ever arrives.

**6 — Encountered "clean" architecture (existing code, not yours)**
Situation: while adding an unrelated feature, you read a package with an interface, three implementing classes, mixins that stub the methods each class doesn't support, a registry mapping three names to the three classes — and a single caller that still branches on which *kind* of class it got. A newer feature in the repo already bypassed the whole thing with a flat script.
Looks like: textbook structure. Three implementations, shared interface, a factory — the "abstract on the 3rd use" rule appears satisfied, so nothing fires and you conform to the pattern.
Rapier: count honestly — three implementations each stubbing half the interface are not three users (Tripwire 2); the type-branching caller got no polymorphism from the Protocol; the existing bypass is the field verdict (Tripwire 8). Flag in two lines with the collapsed shape, offer it as a follow-up, and keep doing the task you were actually asked to do.
