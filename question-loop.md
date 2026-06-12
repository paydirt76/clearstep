---
name: question-loop
description: Socratic exploration (NOTED/CONTEXT/QUESTION/ANSWER) before implementation; output is insight, not code. Use to understand a problem space or mine data for patterns before committing to a build. Not for mid-task clarification (AskUserQuestion), implementation planning (plan-creation), or external research (WebSearch).
---

# Question Loop Skill

triggers: question-loop, socratic, insight, explore, question, loop, dig deeper, brainstorm, probe, discover, unpack, investigate patterns

## Overview

Structured exploration mode for discovering insights before implementation. Uses Socratic dialogue to build understanding, test hypotheses, and accumulate actionable items in a plan.

**Use when:** You need to understand a problem space, mine data for patterns, or explore options before committing to implementation.

**Don't use for:** Mid-task clarification (use AskUserQuestion), implementation planning (use EnterPlanMode), or external research (use WebSearch/Task).

---

## The Loop File

When a loop starts (first iteration), auto-create `plans/.loop-{topic}.md` to capture the trail. The file is the source of truth -- iterations, verdicts, staged edits, and parked questions all land here. Crash-safe, grep-able later, and it makes "call it" a deterministic apply step instead of reconstructing decisions from chat.

**File header:**

```
# Loop: <topic>
Started: <UTC timestamp from `date -u`>
Status: active
tags: <comma-separated, for cross-loop grep>
```

**Sprawl defense -- signal-based meta-check.** Loops sprawl by default. Instead of a count-based Target, the meta-check ("are we converging or wandering?") fires on quality signals:
- **3 rejected verdicts in a row** -- answers aren't landing; the thread has lost grip.
- **2 clarifications on the same question** -- the question itself is wrong; reformulate or call it.

When either signal trips, append a one-line meta-check note to the file and ask the user: keep going, redirect, or call it. Iteration count alone doesn't trigger anything -- number of turns is a weak proxy for whether the loop is still earning its keep.

Append each iteration as the loop progresses. Mark `Status: complete` on "call it." File disposition at end is covered in Ending the Loop.

---

## The Loop Structure

Each iteration follows this exact format. Append the full block to the loop file as you go.

### 1. CONTEXT (5 sentences)
Background for WHY you're asking this question:
- What aspect of the problem space are we exploring now?
- What do we already know that leads to this question?
- Why does this question matter for the overall goal?
- What would the answer unlock or enable?
- Plain language: common words, sentences under 20 words

### 2. QUESTION (1 sentence)
A specific, answerable question under 20 words.

### 3. ANSWER (1-5 sentences)
Answer immediately, plain language. **5 sentences is a ceiling, not a floor.** If the direct answer fits in 1 sentence, stop there. Don't pad with qualifiers, implications, or hedges the user didn't ask for.

When more is warranted, add in this order:
- Direct answer first (your best guess or hypothesis)
- Supporting evidence or reasoning
- What this means or enables
- Potential implications or follow-on considerations
- What you're uncertain about or would need to verify

Cut every sentence that doesn't change the user's next move.

### 4. Wait for User Response
User responds with:
- **"yes"** / agreement -> VERDICT: yes
- **"no"** / disagreement -> VERDICT: rejected (capture user's reason)
- **Clarification** -> VERDICT: clarified, refine and try again
- **"call it"** -> end the loop (see Ending the Loop)

### 5. VERDICT (1 line)
Record the user's response. Format: `VERDICT: yes` / `VERDICT: rejected -- <reason>` / `VERDICT: clarified -- <what changed>`.

### 6. NOTED (3-5 sentences, conditional)
Emit only when VERDICT is `clarified` or partial agreement -- i.e., when something nuanced was settled that wouldn't be obvious from the next CONTEXT alone. **Skip on clean `yes` or `rejected` verdicts.** NOTED's job is to make the artifact accurate when the agreement is more than a one-line yes/no -- it captures the shape of disagreement and the correction the user made.

### 7. PROPOSED PLAN EDIT (conditional, 1 line)
Only when VERDICT = yes AND the insight is actionable. Format:
`PROPOSED PLAN EDIT: <path> -> <action>`

Example: `PROPOSED PLAN EDIT: plans/api-redesign.md -> add step after 4b: "Add rate-limit headers to all endpoints"`

### 8. EDIT TARGET (conditional, 1 line)
Pairs with PROPOSED PLAN EDIT. One of: `new-plan`, `existing-plan`, `claude-md`, `skill`. Makes the apply step deterministic.

---

## Rules

**Plain language** -- Government/technical writing style. Applies to CONTEXT, QUESTION, and ANSWER:

- **Common words, not complex ones.** "Use" not "utilize." "Help" not "facilitate." "Start" not "commence."
- **Sentences under 20 words.** If a sentence runs long, it has two ideas. Split it.
- **Main point first.** Lead with the verdict, then the reason. Don't bury the answer under qualifiers.
- **Remove unnecessary words.** Cut "In my view," "I'd argue that," "Looking at this," and other throat-clearing.
- **Verbs, not nouns.** "Decide" not "make a decision." "Review" not "conduct a review."
- **Be direct and specific.** "Keep the current order" beats "My take is we should probably keep the existing approach."

Break every other rule before you bury the point. If your ANSWER has more commas than verbs, rewrite it.

**One question at a time** -- Never batch multiple questions. Side-questions go to Parked.

**Always provide your answer** -- Don't ask and wait; ask, answer, then wait for feedback.

**Accumulate in the file** -- Every iteration appends to the loop file. Plan edits stage as PROPOSED PLAN EDIT lines, apply in batch at "call it."

**Build on previous answers** -- Each question advances from the last, not restarts.

**NOTED is conditional** -- emit only on `clarified` verdicts or partial agreement, where the user corrected something the next CONTEXT can't capture. Skip on clean `yes` / `rejected`. CONTEXT opens the next iteration with WHY the next question matters; don't use it to repeat NOTED.

**CONTEXT = 5 sentences. ANSWER = 1-5 sentences (ceiling, not floor -- stop when the answer's done).** NOTED, when it fires, is 3-5 sentences. QUESTION and VERDICT stay at 1 line.

**Severity-first ordering** -- When walking a pre-existing batch of items (review findings, audit results, bug lists) that have severity or priority scores, present them in descending severity order, not document order. Exit ramps (e.g. "stop at 5 accepted severity-7+") only have teeth if the critical items come first. Sorting by severity also lets the user make scope-shaping decisions early -- a rejected severity-7 finding can change how you frame the remaining items.

**Don't confuse with AskUserQuestion** -- That tool is for implementation choices ("which library?"), not exploration ("what patterns exist?").

---

## Example Flow

The loop file accumulates iterations as the loop runs. A snapshot mid-loop:

```markdown
# Loop: skill-design-question-loop-format
Started: 2026-04-26 14:32 UTC
Status: active
tags: question-loop, skill-design, file-format

## Iteration 1
CONTEXT: We're redesigning question-loop to auto-create a file at start.
The file needs to capture insights, verdicts, and staged edits. Without
structure the file becomes a wall of text. We need to lock the iteration
block format before adding sections.

QUESTION: What fields should each iteration block contain, in what order?

ANSWER: CONTEXT/QUESTION/ANSWER first (Claude's output), then VERDICT
(user's response), then NOTED (summary). PROPOSED PLAN EDIT comes last,
conditional on VERDICT being yes. NOTED moves to the end because it
summarizes the agreement, which requires the verdict to be in. Uncertain
whether EDIT TARGET should be a separate field or inline.

VERDICT: yes
NOTED: Confirmed iteration order: CONTEXT/QUESTION/ANSWER/VERDICT/NOTED/
PROPOSED PLAN EDIT. EDIT TARGET stays as a separate field for
deterministic apply.
PROPOSED PLAN EDIT: .claude/skills/question-loop/SKILL.md -> rewrite "The Loop Structure" with new order
EDIT TARGET: skill

## Iteration 2
CONTEXT: With the iteration order locked, we need to decide what else
the file captures beyond the trail itself. Side-questions surface
mid-loop and currently get lost. A parking lot section catches them
without derailing the current thread.

QUESTION: What disposition options should parked questions get at "call it"?

ANSWER: Four choices per parked question: promote (new loop file),
plan step (becomes a PROPOSED PLAN EDIT), drop (acknowledged dead end),
or leave parked (loop file persists for next session). User picks per
question. Default to leave parked if user doesn't decide.

VERDICT: yes
NOTED: Four dispositions confirmed. Bias toward parking -- cheap to park,
expensive to lose.
PROPOSED PLAN EDIT: .claude/skills/question-loop/SKILL.md -> add "Parked Questions" section
EDIT TARGET: skill

---
## Parked
- [from iteration 2] "Does the apply step need a dry-run flag?"
  why parked: implementation detail, decide after format is locked
```

At "call it," the staged PROPOSED PLAN EDIT lines apply as a batch and an Apply Log section gets appended.

---

## When to Add a PROPOSED PLAN EDIT

Emit when:
- User agrees an insight is actionable
- Investigation would yield concrete output (skill, doc update, code)
- Pattern suggests automation opportunity

Don't emit when:
- Insight is interesting but not actionable
- User disagrees or needs more exploration
- It's background understanding, not a task

---

## Parked Questions

Side-questions surface mid-loop. They're either related-but-off-thread, deeper rabbit holes, or implementation details that need the format locked first. Currently they hijack the loop or get silently dropped. Parking is the missing third option.

**When to park:**
- User answers and tacks on a tangent
- You realize mid-ANSWER there's a related thread worth noting
- CONTEXT mentions an unexplored angle but you pick a different question to lead with

**How:** Claude proposes ("parking that as a side question -- confirm?"), user can override. Append to the file's Parked section:

```
---
## Parked
- [from iteration 3] "Should NOTED be optional on iterations where nothing was agreed?"
  why parked: format question, not the skill-design thread we're on
- [from iteration 6] "Does the apply step need a dry-run flag?"
  why parked: implementation detail, decide after format is locked
```

Two fields per entry: the question and *why parked*. The "why" matters -- six iterations later you've forgotten the context.

**Bias toward parking.** Cheap to park, expensive to lose. If unsure whether to ask now or park, default to park.

---

## Invoking from Plans

When writing plan steps that need Socratic exploration, use explicit invocation:

**In plan step:** `"Invoke question-loop skill to explore [topic] with user"`

**Why:** Skills trigger on user prompts, not plan file content. When executing a step, Claude reads the plan -- so "invoke question-loop skill" in the step text signals to load this skill's pattern.

| Without explicit invocation | With explicit invocation |
|-----------------------------|--------------------------|
| "Question-loop for X" -> skill doesn't trigger -> ad-hoc approach | "Invoke question-loop skill to X" -> skill triggers -> loop file + iteration format |

---

## Requirements Scrub (pre-call-it)

A conditional closing phase applying Musk's five-step engineering process to the loop's own output. **Fires only when staged `PROPOSED PLAN EDIT` lines target a plan** (`new-plan` or `existing-plan`). Pure insight-mining loops with no staged edits skip it entirely — scrubbing requirements that don't exist is noise.

**When:** User says "call it" (or convergence is near) and staged edits exist. Offer once: "Before applying — run the requirements scrub?" User can decline ("skip scrub, call it"). Offered gate, not a hard gate.

**Format:** Each scrub step is a normal iteration — CONTEXT/QUESTION/ANSWER/VERDICT, appended to the loop file. No new machinery. Plain language throughout; if the user isn't a programmer, explain findings in plain terms.

**The four scrub iterations, in order:**

1. **Make requirements less dumb.** Challenge the staged edits themselves. Name the dumbest staged requirement and say why — especially ones Claude authored. The most valuable finds are framings everyone accepted without question (e.g. logging built AROUND a fragile mechanism instead of questioning the mechanism).

2. **Delete the part or process.** Propose cutting parts: redundant alarms, guards against failures that announce themselves, micro-decisions that batch into category decisions, steps that merge because they remove remains of the same thing. State the add-back expectation: if nothing deleted ever comes back during execution, the cut wasn't deep enough (~10% should return).

3. **Simplify and optimize what remains.** Only after deleting. Merge steps that are halves of one feature, share verification gates (one proof run at the end beats per-step proof runs), reorder so investigation outcomes shape downstream steps, extend existing infrastructure instead of adding new.

4. **Accelerate + automate (combined check).** One iteration, usually pass/fail. Ask: what cycle does this work actually shorten, and is anything worth automating? Expect "check passes, confirms the design" — these two mostly validate rather than change. Also flag what NOT to speed up (irreversible gates stay deliberate).

**Why this order is load-bearing:** deleting before simplifying prevents perfectly optimizing a step that shouldn't exist; simplifying before accelerating prevents rushing a flawed step. Don't reorder, don't skip ahead.

Each scrub iteration's verdict stages or removes plan edits like any other iteration. After iteration 4, proceed to Ending the Loop.

---

## Ending the Loop

When user says "call it" or "stop here" (if staged edits target a plan and the Requirements Scrub hasn't run, offer it first — see above):

### 1. Show staged edits
Grep the loop file for `PROPOSED PLAN EDIT:` lines. Present the batch for review. User can drop or tweak any edit before apply.

### 2. Apply confirmed edits
Run the batch. Append an Apply Log to the file with results:

```
---
## Applied (2026-04-26 15:47 UTC)
- plans/api-redesign.md: added step 4c "Add rate-limit headers to all endpoints"
- plans/api-redesign.md: revised step 4b context -- SKIPPED (user declined at apply review)
```

The Apply Log captures what actually landed -- proposed and applied can drift (user tweaks wording, plan structure changed mid-loop).

**Design-doc sync.** If a confirmed edit changes a mechanism a plan step's `Design:` line points at (a separate spec doc in `docs/`), the edit obligates BOTH surfaces: the plan step body AND the design-doc section. The design doc is the authoritative HOW every step references -- a plan-only edit silently drifts it out of sync. A PROPOSED PLAN EDIT that names only the plan still requires the matching design-doc change at apply time; widen it rather than leaving the spec stale.

### 3. Resolve parked questions
For each entry in Parked, user picks:
1. **Promote** -> spin up as a new loop file
2. **Plan step** -> becomes a PROPOSED PLAN EDIT, applied in this same batch
3. **Drop** -> acknowledged dead end, removed
4. **Leave parked** -> loop file persists, revisit next session

### 4. Mark Status: complete in the file header.

### 5. Loop file disposition

- **Edits applied to existing plan** -> loop file deleted (work landed in the plan; remaining parked questions either promoted or dropped)
- **No active plan existed** -> invoke plan-creation skill to convert the loop file into a real plan in `plans/`. The loop output becomes the plan; don't lose the work in a chat summary.
- **Loop abandoned (no edits, parked questions remain)** -> leave the file. User can resume later by reading it back.
