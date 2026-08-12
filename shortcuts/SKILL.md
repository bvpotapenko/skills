---
name: shortcuts
description: "Capture and reuse hard-won debugging and setup knowledge as per-project shortcut files, so solved problems are never paid for twice. Use this skill at three moments: (1) BEFORE starting any non-trivial task — check the project's shortcuts/ directory for a matching file and read it first; (2) the MOMENT an approach is abandoned or an error has cost more than ~15 minutes — log the dead end immediately; (3) when the problem is solved — append the exact working fix. Trigger whenever debugging, environment setup, dependency or driver issues, deployment, or any previously-seen task family comes up; and whenever the user says 'we did this before', 'save this for next time', 'shortcuts', 'lessons learned', or complains about time wasted on a repeated problem."
---

# Shortcuts — never pay for the same problem twice

Hours burned on a dead end are only wasted if they're forgotten. A shortcut file converts them into a permanent asset: the next encounter with the same wall costs minutes, not hours. The file's reader is a future agent with zero memory of today — write for grep, not for narrative.

The shortcuts root (e.g. `~/.kerminal/projects/{project}/shortcuts/`) is defined in the project's AGENTS.md; use that path.

## The three moments

**1. Read before work.** Before starting any non-trivial task, list the project's `shortcuts/` directory. If a file matches the task family, read it before touching anything — 30 seconds of reading beats rediscovering a known trap. If a listed fix applies, say so explicitly: "shortcuts/cuda_server_deployment.md covers this — applying the known fix."

**2. Log the dead end at the moment of abandonment.** The instant you give up on an approach — or an error has eaten ~15 minutes — append a dead-end line to the matching shortcut file (create it if missing). Immediately, not at session end: sessions get cut off, context gets compacted, and the lesson dies with them. This is also a natural stop-and-ask point: logging the dead end forces you to name it, which is when grinding becomes visible.

**3. Log the fix at the moment of solution.** When it works, append the fix to the same entry: exact commands, exact versions, and the one-sentence reason it works. Copy-pasteable — the future agent should be able to run it, not re-derive it.

## Entry format

Header = the literal error text or observable symptom, because that's what will be grepped for later. One entry per problem, appended chronologically:

```markdown
## ImportError: flash_attn — pip build fails: missing CUDA headers
date: 2026-07-24 | env: Ascend NPU, torch 2.4, no CUDA toolkit
Dead ends:
- pip install flash-attn — needs nvcc, box has none (NPU host)
- building from source — same wall, 30 min wasted
Fix:
export ATTN_IMPL=eager   # engine flag; flash_attn is CUDA-only, N/A on NPU
Cost: ~45 min wasted -> next time ~2 min
```

Rules that keep entries useful:

- **Symptom-keyed headers.** The header is what a stuck agent would paste into grep — error text beats a summary like "attention problems".
- **One line per dead end, with the why.** "Tried X — failed because Y." The *why* is what prevents a future agent from retrying a near-variant of X. No essays, no reflection, no apology — this is a lookup table, not a diary.
- **Fixes carry their versions.** A fix is only trusted for the env it was proven on; on a different version, it's a hypothesis to check first, not a truth. That's why `env:` is mandatory.
- **The cost line is the advertisement.** "~2h -> 5 min" is what convinces the next reader (or you) that checking the file is worth it.

## File layout

One file per **recurring task family**, not per incident — `cuda_server_deployment.md`, `ocr_eval_env.md` — so retrieval doesn't fragment across dozens of session-named files. New incident in a known family → append to the existing file. Genuinely new family → new file, named by the task, snake_case.

## Hygiene

- **Promotion rule.** When the same lesson appears in shortcut files of 2+ projects, it has outgrown "shortcut" and become a principle — propose moving it to the global AGENTS.md (that's how "change the environment, not the code" earned its place). Shortcut files hold project-specific facts; AGENTS.md holds cross-project rules.
- **Staleness.** When a shortcut's fix no longer applies (env upgraded, tool replaced), don't delete the entry — add one line: `superseded 2026-08: on X 5.x use <new fix>`. History of what changed is itself a shortcut.
- **No duplicates.** Before adding an entry, grep the file for the symptom. If it exists, extend that entry rather than writing a sibling.

## Example — bad vs good dead-end line

Bad (narrative, no grep value, no why):
> Today I struggled a lot with the transformers version and eventually realized after much effort that patching wasn't the way.

Good:
> - patched model code for transformers 5.x compat (try/except imports, cache API, RoPE) — spiral: each patch exposed the next break; root cause was env, not code
