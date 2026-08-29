# Long-Form Formats: Textbook Parts and Workbooks

Two document types. Both are markdown files delivered to the user (not chat text). Both exist to be *returned to* between distractions, so structure is navigation, not bureaucracy.

## Shared machinery (both document types)

**The box taxonomy** — visual anchors the learner learns to trust:

- `💡 LINK #N:` — a checkpoint that SEALS a connection the preceding text already built; never the delivery vehicle. The box test: it must read as a one-line *summary of what the reader just understood*, not as news — if you cannot point at the exact preceding paragraphs that set the question and resolved it, the box is unearned: build the ladder or cut the box. Because it's a seal, it doubles as self-diagnosis; instruct the learner in the preamble: "a 💡 box should feel obvious by the time you reach it — if one reads as new information, re-read the section above it before moving on." Each box earns its number by connecting at least two previously-separate things, or reframing one thing so a later result becomes obvious. Numbered consecutively, and numbering CONTINUES across documents in the same course (Part II starts where Part I stopped).
- `📓 NOTEBOOK:` — the load-bearing results as *generative prompts*: a question the learner answers in their own words, never a ready-made line to transcribe. Give the check, not the sentence — "📓 In your own words: why does squaring rescue the average deviation? (then check yourself against §2.1)". Quality bar: if the learner answered ONLY the notebook prompts, their answers would form a working summary of the document. Tell them to actually write, not nod.
- `🎛 KNOBS:` — term-by-term dissection of a formula just presented: effect of each term growing/shrinking, behavior at edge cases, which knob the practitioner actually turns.

**ASCII graphics**: keep to ~64 characters wide (mobile-safe). Rough is fine; *labeled* is mandatory — every axis, region, and threshold named. Draw the picture that carries the argument (overlapping curves for power, quadrants for covariance), never decoration. A picture the learner can redraw from memory is a proof they own the idea — say so under the important ones.

**Numbers**: every worked number recomputed and verified before it ships. Prefer values that come out clean. When two different roads should give the same number (a direct formula and a decomposition), USE that as a planted cross-check across chapters — "matching to the digit" moments build enormous trust.

**Answers quarantine**: all task answers in a single section at the very end, after everything, with one-line reasoning each — never adjacent to the tasks. State the law: honest attempt first; a fought-for wrong answer beats a peeked-at right one.

## Format A — Textbook Part

```
# <COURSE TITLE>
## Part <N> — <subtitle>
   how-to-use preamble: sitting size (10–15 min per sub-chapter), notebook
   instructions, box taxonomy, answers location, invitation to bring
   solutions back for checking

## CHAPTER Ω — THE ONE IDEA          ← the spine, stated first, before any content
   the single organizing principle; instruct the learner to write it on
   page one and return to it whenever lost

# CHAPTER 0 — THE REPAIR SHOP        ← only if learner stated current beliefs
   audit table (claim / verdict), rebuild broken concepts from the failure point

# CHAPTERS 1..K — the content
   each chapter = 2–4 sub-chapters, each sized to one sitting and labeled
   with minutes; each sub-chapter: ladder-built theory → 💡/📓/🎛 boxes →
   2–3 worked examples ("Worked example N-A") → chapter ends with 2–3 tasks
   ("Tasks for Chapter N", IDs like T3.1)

# FINAL CHAPTER — THE MAP
   one big ASCII concept map of everything; then compress the whole part to
   its N core ideas (N ≤ 5 per part) — this chapter converts facts to
   knowledge; then a menu of possible next parts (let the user choose)

# ANSWERS — all of them, at the very end
```

Pacing rules that matter: escalate difficulty *within* each chapter and *across* the document; plant ideas early and pay them off with explicit callbacks ("Ch.0's Pythagorean link, cashing in again"); when a chapter's concept will be someone's day-job tool, include one example set in the learner's actual domain. End the document with a short, warm sign-off in the teacher's voice that invites returning with solutions.

## Format B — Workbook (exercise book)

No theory — problems only, plus the answers quarantine. The workbook's secret second function is diagnosis: every task carries a chapter tag `[Ch.N]` so a stumble tells the learner exactly what to re-read. Say this in the preamble.

```
# <COURSE TITLE> — The Workbook
   preamble: difficulty legend, standing equipment, cast of characters

   Difficulty legend:
   ●    solvable in the head (no paper allowed — that's the point)
   ●●   paper + basic calculator
   ●●●  stretch: multi-step, or one inch past the textbook

## SET per chapter — 3–6 tasks, ramping ● → ●●●, IDs like W3.2
## BOSS BATTLES — 3–4 integrative problems spanning several chapters,
   ideally staged as one realistic scenario from the learner's domain
## ANSWERS
```

Workbook craft:

- **Standing equipment**: list the constants/rules the learner should know *from memory* (announce that using them unaided is deliberate spaced retrieval).
- **Recurring cast** (Perelman's device): 2–4 characters who carry the playful tasks — a dragon with measurable heads, an absent-minded professor who loses umbrellas at fixed probability. Fun carries numbers; every playful task still has exact arithmetic and a real point.
- **Tasks that secretly teach**: some ●●● tasks should lead the learner to *discover* a result the textbook never stated, which the answer then names ("you've just derived the computational formula for variance"). Nothing cements understanding like discovery under one's own power.
- **Self-verifying tasks**: where possible, design tasks whose answer the learner can check independently (invert the operation, compare two roads). These teach the checking habit for free.
- **Mix of flavors**: pure-math drills, playful narratives, and the learner's real domains (work + research), roughly balanced; a domain task should be one they could genuinely meet on the job.
- **Boss battles** end the ramp: multi-chapter, realistic, and at least one should contain a *trap* the textbook warned about (an approximation that fails in the tail, a selection bias, a tempting-but-wrong baseline) so the answer can spring it pedagogically.
- **Answers** include brief reasoning and, where a task hides a named concept or classic story, the reveal belongs there — the answer section is the workbook's second textbook.

## Multi-part continuity

Chapter numbers, link numbers, and task ID schemes continue across parts of the same course. Later parts open by restating where the previous part left the learner (its N core ideas) and close by extending the map. Cross-check numbers across parts on purpose (compute the same quantity by a new road and match it) — continuity is the physical evidence that this is one body of knowledge.
