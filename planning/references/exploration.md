# Exploration subagent prompts

Exploration turns unknowns into numbered findings (`E1..En`) the plan can cite. Delegate
each exploration to a subagent; run independent ones in parallel.

## Rules for every exploration prompt

A lazy prompt ("analyze the code") returns a lazy answer. Every prompt contains:

1. **Scope** — exact files, directories, URLs, or documents to examine.
2. **Questions** — the specific things the plan needs to know (how does it do A, B, C?).
3. **Suspected issues** — what to actively look for (does it have problems E, F, G?).
4. **Response shape** — the exact structure of the answer, so findings drop straight into
   the plan.
5. **Findings only** — the subagent reports; it does not fix, refactor, or editorialize.

Fill the `{placeholders}` with the specifics of the current task — that is the difference
between a surgeon's cut and a butcher's.

## Template: code state

```
Analyze {paths} in this repository.
Answer precisely:
1. How does it currently do {A}? (entry points, data flow, key functions)
2. Where is {B} implemented and what depends on it?
3. What conventions does the project use for {C}?
Actively check these suspected issues: {E}, {F}, {G} — for each: confirmed / not found /
uncertain, with file:line evidence.
Respond exactly as:
FINDINGS: numbered list, each = claim + file:line evidence
ISSUES: {E|F|G} → status + evidence
CONSTRAINTS: anything limiting the planned change (APIs, invariants, versions)
Do not modify anything. Report only.
```

### Filled example (excerpt)

```
Analyze src/metrics/aggregate.py and src/report/.
Answer precisely:
1. How does it currently aggregate per-run metrics into the summary? (entry points, data flow)
2. Where are comparison tolerances defined and what depends on them?
3. What conventions does the project use for result serialization?
Actively check these suspected issues: hard-coded tolerance values, float equality
without isclose, per-run result schemas that differ silently.
...
```

## Template: external link / docs

```
Fetch and analyze {URL(s)}.
Extract only what matters for: {one-line task statement}.
Answer: 1. {question A}  2. {question B}  3. {question C}
Note explicitly: version-specific behavior, deprecations, licensing, and anything that
contradicts the assumption "{assumption we rely on}".
Respond exactly as:
ANSWERS: numbered, paraphrased, each with a section/anchor reference
RISKS: contradictions or gaps found
```

## Template: literature / PDF

```
Read {paper/PDF path or reference}.
We need it for: {one-line purpose — e.g. choosing a statistical test for X}.
Answer:
1. What method does it propose for {A}, and under what assumptions?
2. What are the stated limitations / failure modes?
3. What parameters or thresholds does it recommend, with values?
Respond exactly as:
METHOD: …   ASSUMPTIONS: …   LIMITATIONS: …   NUMBERS: name = value (source section)
APPLICABILITY: does our case satisfy the assumptions? yes / no / uncertain + why
```

Adapt the templates freely — add questions, drop irrelevant lines — but never drop the
scope, the suspected issues, or the response shape.
