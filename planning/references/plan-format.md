# Plan format

The draft (step 6) and the final plan (step 8) use the same three blocks, in this order.
The blocks exist so that wrong assumptions are visible before the steps, and every step is
traceable to the problem it solves.

## Block 1 — Decisions & Assumptions

Everything chosen or presumed, stated before any steps:

```
D1 (decision, user-confirmed): <what was chosen> — chose option B in Q1: <one-line why>.
A1 (assumption, not asked): <what is presumed> — why reasonable: <…> — if wrong: <what breaks / changes>.
D4 (from <priority> review): <change made after review> — <why>.
```

Rules:
- Every branch taken without asking the user is an `A*` entry. No buried assumptions.
- "If wrong" is mandatory for assumptions — it tells the reader what to re-check first.
- Review-driven changes get their own `D*` entries during step 7.

## Block 2 — High-level plan

Numbered steps, one line each, in execution order. Mark dependencies and parallelizable
steps. A reader must grasp the whole shape of the work in under a minute.

```
1. <verb + object>            (depends on: —)
2. <verb + object>            (depends on: 1)
3. <verb + object>            (parallel with 2)
```

## Block 3 — Low-level plan

One subsection per high-level step. Include the fields that carry content; omit empty
ones.

```
### Step N — <title>
Addresses: P2, P3            ← problems extracted in workflow step 1
Informed by: E1, E4          ← exploration findings
Implementation notes: <how; key modules/functions; order of operations>
Design decisions: <local choices + one-line rationale each>
Formulas: <every variable defined, units stated, edge cases noted>      (if any)
Watch out: <important things easy to get wrong here>
Use skill/tool: <exact skill name for this step, e.g. pytest-tdd>       (if one exists)
Done when: <verifiable completion criterion>
```

Rules:
- Every `P*` from the problem extraction is claimed by at least one step. An unclaimed
  problem means the plan does not solve the request.
- Formulas define *all* variables; anything deliberately omitted is stated with its
  justification ("term X dropped: contributes < 1% because …").
- If a skill exists for a step's job, naming it in `Use skill/tool` is not optional — the
  implementer must not have to rediscover it.
