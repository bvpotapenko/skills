---
name: planning
description: Craft the best-fitting plan for a task before implementation, driven by explicit priorities (fast/YAGNI efficiency, calculation rigor, long-term maintainability, security) and hardened by adversarial subagent review of the draft. Use whenever the user asks to plan, design, architect, scope, estimate, or "think through" a feature, system, refactor, migration, pipeline, algorithm, or evaluation — or asks "how should we approach/build X" — even if the word "plan" never appears. Also use proactively before any multi-step implementation whose approach is not obvious. Skip only for trivial single-step tasks.
---

# Planning

Produce the best plan for the current task. "Best" is not universal — it is defined by the
active priorities. Whatever they are, a plan produced with this skill is always: traceable
to the user's actual problem, explicit about every decision and assumption, and reviewed
adversarially before the user sees the final version.

Read only the reference files the current task needs:

| File | Read when |
|---|---|
| `references/exploration.md` | Before spawning exploration subagents (step 3) |
| `references/plan-format.md` | Before writing the draft (step 6) |
| `references/review-efficiency.md` | Priority active: speed / lean code / YAGNI |
| `references/review-rigor.md` | Priority active: calculations / formulas / statistics |
| `references/review-maintainability.md` | Priority active: long-lived, growing project |
| `references/review-safety.md` | Priority active: security (see auto-rule below) |

## Priorities

Decide what the task optimizes for. Several can be active at once; all four is legal for
large systems.

- **Efficiency** — fastest useful implementation. Fewest entities (YAGNI); a trusted
  existing library beats reimplementing a solved pattern in ~9/10 cases. Signals:
  prototype, MVP, script, small tool, "keep it simple".
- **Rigor** — the calculations must be right: every relevant variable accounted for,
  methods that fit the problem. Signals: estimation, metrics, statistics, verification,
  benchmarks, formulas.
- **Maintainability** — the project will live and grow; new features must not force
  rewriting half of it. Signals: team codebase, "will scale", plugin systems, big refactor.
- **Safety** — no leaked secrets, no injections, no path for an abuser in. **Auto-activates**
  whenever the plan touches secrets, user data, network-exposed endpoints, or execution of
  external input — regardless of what the user emphasized. Safety is not opt-in.

If the active set is genuinely ambiguous and the plan would differ materially between
readings, make it the first clarifying question in step 4.

## Workflow

### 1. Extract the problem
Restate, in your own words, the problems the user actually describes and the ideas or
constraints they already voiced. Number the problems `P1..Pn`. The plan is built against
this list, not against a paraphrase of the request. Contradictions inside the request go
to step 4.

### 2. Recall context
Check what is already known before exploring: earlier decisions in this conversation,
project memory (CLAUDE.md, README, ADRs, TODOs), recent git history for in-flight
direction, and the user's standing requirements. Never silently contradict a previously
agreed decision — respect it, or raise it explicitly in step 4.

### 3. Explore
Gather the facts the plan depends on: current code state, linked pages, referenced papers
or PDFs. Delegate each to a subagent with a surgical prompt — scoped, with named
questions, named suspected issues, and a required response shape. Read
`references/exploration.md` for the templates and rules; run independent explorations in
parallel. Number the findings `E1..En`. (No subagent tool available? Do each exploration
yourself as a separate focused pass with the same structure.)

### 4. Clarify
Ask the user only at real branch points: where options significantly change the outcome
and context cannot resolve the choice. Every question offers options:

```
Q: <the decision>
  A) <option> — <effect on the plan>; + <pro> / − <con>
  B) <option> — <effect on the plan>; + <pro> / − <con>
  My take: <A or B> because <one line>.
```

Whatever is decided *without* asking is an assumption — it must appear in the
Decisions & Assumptions block, never buried in prose. If maintainability is active,
long-term expectations (features on the horizon, load growth, team size) are mandatory
clarifications unless already known.

### 5. Leverage skills
Scan the available skills twice:
- **For planning now** — anything that improves this plan (domain, analysis, reading
  skills): use it during steps 3–7.
- **For implementation later** — name the skill inside the plan step that needs it, e.g.
  "Write the test suite — *use skill `pytest-tdd`*". An implementer following the plan
  must not have to rediscover that a skill exists.

### 6. Draft the plan
Read `references/plan-format.md` and write the draft in its three-block structure:
**Decisions & Assumptions** first, then the **high-level plan**, then the **low-level
plan**, where every step traces back to `P*` and `E*` references.

### 7. Adversarial review
For each active priority, spawn a reviewer subagent over the draft:

```
Read <skill_path>/references/review-<priority>.md and act as that reviewer.
Task: <2–4 line summary>. Stack & constraints: <language, env limits, deps policy>.
Draft plan: <inline or file path>.
Return findings in the output shape that file defines. Findings only — do not rewrite the plan.
```

Run reviewers in parallel. (No subagents? Perform each active review yourself as a
separate single-priority pass — one hat at a time — after reading its file.)

Integrate the feedback. Conflicts between reviewers are resolved by the priority ranking
or escalated to the user; safety findings are never traded away silently. Every
review-driven change becomes a new entry in Decisions & Assumptions (e.g. "D4 — from
efficiency review: replaced hand-rolled config parser with OmegaConf"). If the revision
changed the plan's structure, re-run only the affected reviewers once; do not loop
further.

### 8. Finalize
Deliver the final plan in the same three blocks: Decisions & Assumptions → high-level
plan → low-level plan. Write it to a file if the project keeps plans in files or the user
asks; otherwise present it in the conversation. The plan must be executable by an
implementer who has read nothing else.
