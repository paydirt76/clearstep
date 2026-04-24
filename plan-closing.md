---
project: "{{SOURCE_PROJECT}}"
status: in_progress
type: chore
description: "Plan-completion workflow for {{SOURCE_PLAN_NAME}} -- audit, CLAUDE.md update, commit, follow-up prompt, disposition"
priority: 10
created: "{{DATE}}"
---
# Plan-Completion Workflow: {{SOURCE_PLAN_NAME}}

## About This Plan

**Type:** Closing plan (ephemeral scaffold). Spawned by `/plan-completion` from the template at `plans/templates/plan-closing.md`. Executes the full closing ritual for `{{SOURCE_PLAN}}` as discrete `/step` iterations instead of one giant skill invocation.

**Lifecycle:** The skill copies the template here, substitutes variables, adds `{{CLOSING_PLAN}}` to `plans/.step0-queue.json` (the closing-plan queue -- NOT the main `.step-queue.json` where the source plan lives), marks Step 2 as `[n]`, and kicks off `/step --0`. Steps fire one at a time until **Step 8** (terminal), which runs disposition, sweep, commit, report, queue drain, and self-delete. For **template** disposition, Step 8 pauses after extraction — run `/step --0` again and Step 8 resumes at Phase C.

**Queue isolation is deliberate.** Closing plans go into queue 0 so the main queue (and any parallel queues 2-9) stay untouched while a plan is closing. A user running `/step` in a different queue mid-close won't accidentally pick up this closing plan, and this closing plan won't race with the source plan's own queue.

**Never edit this file directly.** Every instruction below operates on either `{{SOURCE_PLAN}}` (the plan being closed) or the broader repo. The closing plan is a workflow driver, not an artifact.

**Invariant:** Closing plans must not produce scratch files. If a closing-plan step ever needs scratch, fix the template — don't tag `Temp files:` in a closing plan's Results blocks. The sweep only parses the source plan.

---

## Variables (Substituted at Copy Time by the Skill)

| Variable | Meaning | Example |
|----------|---------|---------|
| `{{SOURCE_PLAN}}` | Full repo-relative path of the plan being closed | `plans/my-feature.md` |
| `{{SOURCE_PLAN_NAME}}` | Plan slug (no dir, no extension) | `my-feature` |
| `{{SOURCE_PROJECT}}` | Value of `project:` in the source plan's frontmatter | `email-filter` |
| `{{CLOSING_PLAN}}` | This file's path | `plans/my-feature-closing.md` |
| `{{SOURCE_QUEUE}}` | Queue file the source plan lives in (main or any of 2-9) | `plans/.step-queue.json` |
| `{{CLOSING_QUEUE}}` | Queue file the closing plan lives in -- always queue 0 | `plans/.step0-queue.json` |
| `{{STEP_COUNT}}` | Number of `[x]` steps in the source plan at close time | `12` |
| `{{DATE}}` | ISO date the closing plan was spawned | `2026-04-19` |

If any `{{PLACEHOLDER}}` remains uninterpolated below, the skill's copy step failed and downstream behavior will be wrong. Do not proceed until all variables are real values.

---

## Steps

### [n] Step 2: Pre-close audit -- LANDMINEs + `[w]` + `[!]` disposition

**Why this step exists:** Three classes of deferred obligation can survive to plan close. All three get orphaned silently without an audit.

- **Open LANDMINEs** -- annotations in completed-step Results blocks flagging known issues deferred for later fix. `/step` greps the live plan on every invocation, but archive plans aren't re-grepped, templated plans carry stale warnings, deleted plans lose them entirely.
- **`[w]` waiting steps** -- blocked on an external person/event. The completion gate treats only `[x]` and `[~]` as done, so `[w]` blocks plan close. The wait may have resolved silently, may no longer be needed, or may deserve a followup plan.
- **`[!]` stuck steps** -- flagged as needing intervention. Same completion-gate block. Same disposition question: fix, supersede, or defer.

**`[~]` is NOT audited** -- it equals `[x]` for completion purposes (plan pivoted, step intentionally skipped).

**Procedure:**

1. **Scan `{{SOURCE_PLAN}}` for all three categories:**

   ```
   Grep pattern="LANDMINE" path={{SOURCE_PLAN}} -n -A 1             # exclude LANDMINE[resolved]
   Grep pattern="^### \[w\]|^\(w\)|^<w>" path={{SOURCE_PLAN}} -n    # waiting (all three tiers)
   Grep pattern="^### \[!\]|^\(!\)|^<!>" path={{SOURCE_PLAN}} -n    # stuck (all three tiers)
   ```

2. **If zero items across all categories:** report "Audit clean -- no open LANDMINEs, no `[w]` waiting, no `[!]` stuck steps." and mark this step `[x]`. Skip all subsequent procedure items.

3. **Spawn one Sonnet agent per item, in parallel.** The three categories unify from here on -- same agent prompt, same output schema, same option tree. Category is a tag, not a workflow branch.

   For each audit item, main CC assembles a **context bundle** and spawns an agent. All agents fire in a single message (parallel Task calls):

   **Context bundle per item:**
   - `category`: `LANDMINE` | `w` | `!`
   - `item_text`: the LANDMINE string, or the step description for `[w]`/`[!]`
   - `results_bullet`: the full Results-block bullet the item lived in (LANDMINEs only; for `[w]`/`[!]`, the source step has no Results yet -- use step body instead)
   - `enclosing_step`: the entire source step text (from its `### [...]` header through to the next step's header)
   - `context_files`: file contents of every path named in the enclosing step's `Context:` line (main CC reads each file and passes content)
   - `plan_goal`: the Goal + Current State sections from the top of `{{SOURCE_PLAN}}`
   - `surrounding_window`: ±25 lines around the item's line number in `{{SOURCE_PLAN}}`

   **Agent prompt (verbatim, per agent):**

   *"You are synthesizing an audit item for a plan that's about to close. The user will use your output to decide Fix now / Defer / Ignore for this item. Your job: give them enough context to decide well.*

   *Read the context bundle. Produce a synthesis in this exact structured-markdown shape:*

   *```*
   *## What*
   *[One sentence: what this item is, in plain language.]*

   *## Where*
   *[One sentence: location in code or plan -- file:line if applicable, otherwise step number + what phase of work.]*

   *## Why*
   *[One sentence: why this still matters, or what ignoring it costs. Be concrete -- not "this is important" but "the rate limiter will 429 under load because the bucket size is hardcoded at 10/sec."]*

   *## Fix now preview*
   *[Two sentences: what the fix would look like in this specific context. Be concrete about files and changes. If the fix spans >1 file or requires coordinated edits, DO NOT recommend Fix now -- recommend Defer instead.]*

   *## Defer preview*
   *[Two sentences: what a deferred-plan step would contain. Title, brief scope, key files it would touch. Enough to tell the user whether deferring is sensible.]*

   *## Ignore preview*
   *[Two sentences: consequences of dismissing this item. What breaks, what drifts, what stays silently broken. For LANDMINEs, also note Step 8 disposition implications (Archive fossilizes the note, Template should strip it, Delete loses it).]*

   *## Recommended*
   *[One of: Fix now | Defer | Ignore]*

   *## Recommendation reason*
   *[One to two sentences: why this recommendation fits this specific item. Reference evidence from the bundle -- don't just assert.]*

   *Scoping rule: 'Fix now' means main CC applies the edit in this same session. If the fix would span multiple files or need coordinated changes with tests, recommend Defer instead."*

   **Failure handling:** if an agent fails to produce usable output (timeout, malformed structure, empty response), rerun it once with the same bundle. Assume one rerun is enough.

4. **After all agents complete, render a summary header and walk the cards.**

   Summary header (one line):
   ```
   Pre-close audit: N items -- LANDMINEs (M), [w] (P), [!] (Q). Walking each.
   ```

   Then render one card at a time. Each card shows: category prefix (`[LANDMINE]` / `[w]` / `[!]`), the seven synthesis sections from the agent output, and a prompt for the user's pick:

   ```
   [LANDMINE] Item 1 of N (Step 2, line 127)

   ## What
   Rate limiter bucket size hardcoded at 10/sec.

   ## Where
   _library/rate_limiter.py:42 (DualRateLimiter.__init__)

   ## Why
   Newer topics exceed 10/sec during burst fetches -- will 429 silently under production load.

   ## Fix now preview
   Change the 10 to a config-loaded value, add a default of 20 in configs/rate_limits.yaml. One-file change plus a config bump.

   ## Defer preview
   New plan step: "Refactor rate limiter to read bucket size from config." Title, scope, touches rate_limiter.py + configs/rate_limits.yaml.

   ## Ignore preview
   Burst topics will hit 429s intermittently until manually fixed later. Archive disposition fossilizes the landmine annotation; Template strips it; Delete loses it.

   ## Recommended
   Fix now

   ## Recommendation reason
   One-file change with a clear config-default path. No coordination needed.

   Pick: (F)ix now / (D)efer / (I)gnore -- default [F]
   ```

5. **Execute the user's pick item-by-item. Write back only after the action completes.**

   **Fix now:**
   - LANDMINE: main CC applies the edit. Then change source `LANDMINE:` -> `LANDMINE[resolved]: <short reason>` (or `-> see CLAUDE.md § [section]` if the fix was adding a CLAUDE.md constraint).
   - `[w]`: main CC applies fix. Convert source `[w]` -> `[x]` with `{timestamp}`, add a Results note describing how it resolved.
   - `[!]`: main CC applies fix. Convert source `[!]` -> `[x]` with `{timestamp}`, add a Results note describing the unblock.

   **Defer:**
   - Prompt once: new plan (main CC creates `plans/{{SOURCE_PLAN_NAME}}-followup.md`) or existing plan (user names which; append as new step). Hand-off payload: source plan path + step number, full Results bullet or step body, item text as step title, pre-seeded `Context:` line with files named in the origin step. For `[!]` defer, payload MUST include the full stuck-reason annotation -- the followup needs to know what's already been tried.
   - LANDMINE: change source `LANDMINE:` -> `LANDMINE[resolved]: -> see plans/<path>.md`.
   - `[w]`/`[!]`: convert source `[w]`/`[!]` -> `[~]` with `-> see plans/<path>.md` appended to step body (preserve original failure annotation below for `[!]`).

   **Ignore:**
   - LANDMINE: change source `LANDMINE:` -> `LANDMINE[resolved: dismissed by user YYYY-MM-DD during plan close]:` (keep the original text after the colon).
   - `[w]`/`[!]`: convert source `[w]`/`[!]` -> `[~]` with step body note "Ignored/dismissed by user YYYY-MM-DD during plan close." For `[!]`, preserve the original failure annotation below the note so the reason-for-stuckness isn't lost.

   Writeback is item-by-item, triggered only after the chosen action completes. Do NOT write speculatively -- if the user aborts mid-walk, already-resolved items stay resolved and the remaining walk resumes on the next `/step --0`.

6. **After the walk:** the plan file has edits (silenced LANDMINEs, `[w]`/`[!]` converted with notes, possibly fix-code diffs in other files). These will be staged in the Step 8 disposition commit. If Defer created a followup plan file, it gets staged there too. If Fix now lifted a LANDMINE to CLAUDE.md, Step 4 picks up that edit.

**Hard rule:** do not mark this step `[x]` until every item is dispositioned. The completion gate rejects the plan if any `[w]` or `[!]` marker remains -- the walk must convert them to `[x]` or `[~]`.

Context: {{SOURCE_PLAN}}
Skills: plan-creation
Mode: 1 (review)

---

### [ ] Step 4: Update CLAUDE.md

A plan's constraints and invariants are the most useful thing to document for future sessions. This step checks whether a CLAUDE.md exists and adapts accordingly -- it does not assume every project uses one.

**Phase 1: Detect the target**

1. Determine the target path. If `{{SOURCE_PLAN}}` lives inside a specific project directory (`{{SOURCE_PROJECT}}/`), the primary target is `{{SOURCE_PROJECT}}/.claude/CLAUDE.md`. If the plan is global-scope, target `.claude/CLAUDE.md`.
2. If project-scoped, check whether `{{SOURCE_PROJECT}}/` exists as a directory. If the directory is gone (renamed, merged, or deleted since the plan started), fall through: target root `.claude/CLAUDE.md` if the work has broader relevance, or proceed directly to the skip option.
3. Check whether the target CLAUDE.md file exists.

**Phase 2: Branch on result**

**If the target CLAUDE.md exists**, present two options:

- **(a) Update** -- proceed to the Execution section below
- **(b) Skip** -- mark Step 4 done with Results: "Skipped -- user chose not to update CLAUDE.md"

**If the target CLAUDE.md does NOT exist**, present three options:

- **(a) Create and populate** -- create the file, then proceed to the Execution section. Populate with what future sessions need to know: what the directory is, core invariants, sync/relationship notes, hard rules for files inside
- **(b) Skip this time** -- mark Step 4 done with Results: "Skipped -- no CLAUDE.md exists, user chose not to create"
- **(c) Skip permanently** -- mark Step 4 done, then offer: "Want me to edit the plan-completion template to remove this CLAUDE.md step for all future closes? This is reversible -- you can always re-add it later by copying the step back from the clearstep repo." If user agrees, delete this Step 4 section from `plans/templates/plan-closing.md` and confirm. If not, just skip this time

The skip-permanently option is the **self-configuring ritual** pattern: the first close surfaces the question, and the user's answer locks in their preference by editing the template itself.

**Execution (for update or create)**

**Which CLAUDE.md?** Two levels:

1. **Project-level** at `{{SOURCE_PROJECT}}/.claude/CLAUDE.md` -- default for any plan whose work lives inside a specific project
2. **Root-level** at `.claude/CLAUDE.md` -- only for changes affecting global practices or cross-project conventions

**What to update (pick all that apply):**

- **Common Commands** -- new user-facing scripts or commands
- **Status line** -- if the project's status changed meaningfully
- **Where to Look table** -- new important files or directories
- **Hard Constraints** -- new rules future sessions must not violate
- **Architecture/features sections** -- if introduced or substantially changed

**Do NOT duplicate content that already lives in a skill or plan template.** If `{{SOURCE_PLAN}}` modified a self-loading artifact (`.claude/skills/X/SKILL.md`, `plans/templates/Y.md`), that file IS the canonical home. A parallel recap in CLAUDE.md is duplication that rots. Before drafting a delta, ask: *"Is this already covered by a SKILL.md or template the plan touched?"* If yes, skip it. Only graduate to CLAUDE.md constraints that cross skill/template boundaries. Examples:

- A numbering-convention exception whose parent rule lives in CLAUDE.md -- stays in CLAUDE.md (boundary crossed)
- A mechanism summary (what the skill does, its rubric) -- stays in SKILL.md
- A step-by-step recap of a template's workflow -- stays in the template
- A hint-line convention whose canonical spec lives in a slash command or skill -- stays there
- A pointer to a reference artifact whose only consumers are workflows that already load it -- stays in the workflow

**Operational test:** *"Who is the audience for this pointer? Does their workflow already load the canonical reference?"* If yes, the pointer is duplication -- drop it.

**Execution via agent (context relief).** Drafting the delta requires reading every `[x]` step's Results block in `{{SOURCE_PLAN}}` -- don't burn main context on that.

1. **Main CC determines target path** using Phase 1 detection above.

2. **Main CC spawns a general-purpose agent** (`subagent_type: "general-purpose"`, `model: "sonnet"`) with a self-contained prompt. The agent maintains CLAUDE.md as a **router** (navigation aid for future sessions), not a changelog.

   The agent prompt must include the target path, `{{SOURCE_PLAN}}` path, the "What to update" list, the "Do NOT duplicate" rule (verbatim), the router-pattern checklist below, and this instruction:

   *"Your job: maintain the target CLAUDE.md as a router for the project, not a changelog of plan deltas.*

   *Step 1 -- survey the project's current state. List top-level files and key directories under {{SOURCE_PROJECT}}/ (or repo root if target is the root CLAUDE.md). Identify new components introduced by {{SOURCE_PLAN}} and existing components that changed.*

   *Step 2 -- read the target CLAUDE.md (or note if absent). Read every `[x]` step's Results block in {{SOURCE_PLAN}} to understand what changed.*

   *Step 3 -- ask: 'Would a future session land at this CLAUDE.md and know how to work in this project?' Identify gaps.*

   *Step 4 -- propose deltas that improve routing. Examples: add a component to the Where-to-Look table; update Common Commands; surface a new Hard Constraint; add decision rationale inline.*

   *Step 5 -- apply the 'Do NOT duplicate' rule. If content lives in a SKILL.md or template the plan touched, drop it.*

   *Step 6 -- if the target CLAUDE.md is missing, thin, or structurally weak, propose a full router-shaped skeleton using the checklist below.*

   *Router-pattern checklist:*
   *- Header orients in 3 lines: Purpose / Status / Entry point*
   *- Common Commands appear early (copy-paste actionable)*
   *- Where-to-Look table routes to sub-directory CLAUDE.mds and reference docs*
   *- Hard Constraints surfaced near the top*
   *- Architecture/How-It-Works section orients but defers details*
   *- Decision rationale inline (why X and not Y)*
   *- Directory Structure tree if non-trivial layout*
   *- Idempotency / re-run guarantees if applicable*
   *- Last-updated date at bottom*

   *Output: section-by-section delta plus <100-word justification per surviving edit. Do NOT apply edits yourself. If nothing warrants an update, say so with one-sentence reasoning."*

3. **Main CC reviews agent's proposal with the user, then applies via Edit.** Do not rubber-stamp -- the agent can miss project-specific phrasing or duplicate existing content.

Context: {{SOURCE_PLAN}}
Mode: 2 (create)

---

### [ ] Step 6: Summary + follow-up prompt

**This step fires BEFORE disposition.** The follow-up prompt is forward-looking ("what does this work enable next?") and disposition is backward-looking ("file this away"). Running forward-first lets the user's follow-up answer inform how they want the plan file treated.

**This is a two-turn step.** Do not mark `[x]` or advance `[n]` until the user answers the follow-up menu.

Step 6's "execute" phase in `/step` ends AFTER presenting the menu. The user's letter choice IS the step's required input -- without it, item 3's "Routing on selection" cannot run, and Step 8's disposition may depend on the answer. So:

- Present the summary + actionable-next-steps + follow-up menu in chat.
- **STOP.** Do not proceed to `/step` Step 5 (plan update) in the same turn.
- Do NOT mark this step `[x]`, do NOT add a `**Results:**` block, do NOT advance `[n]` to Step 8, do NOT touch `{{SOURCE_PLAN}}` or `{{CLOSING_PLAN}}`.
- Wait for the user's reply. Their answer (a/b/c/d/e/x/q or combinations) arrives as the next user turn.
- On the NEXT `/step --0` invocation (after the user's answer is in hand), execute the routing action for their letter, THEN perform the Step 5 plan update: mark `[x]` with timestamp, write Results block capturing what they chose and what routing fired, advance `[n]` to Step 8.

This is a deliberate two-turn step. Bypassing the halt (marking [x] before the user answers) is a known failure mode: the runner advances `[n]` while the menu is still unanswered in chat, defeating the "forward-first before disposition" ordering that this step exists to enforce.

---

1. **Summarize what was built** -- Table showing components created, their locations, and purpose. Pulled from every `[x]` step's `**Results:**` block in `{{SOURCE_PLAN}}`.

2. **Provide actionable next steps** -- How to use what was built:
   - Commands to run (with full syntax)
   - Files to review
   - Follow-up actions needed
   - Optional enhancements or future work

3. **Ask about follow-up work.** **Generate the menu AT CLOSE TIME** from what the plan actually produced -- do NOT paste a static template.

   **Execution via agent (context relief).** Reading every `[x]` Results block to pick plan-specific pitches burns main-context tokens for ~500 tokens of menu output. Spawn a general-purpose agent (`subagent_type: "general-purpose"`, `model: "sonnet"`) with a self-contained prompt containing `{{SOURCE_PLAN}}` path, the opener below, the generation rubric, and the category list. Instruct the agent to: *"Read {{SOURCE_PLAN}} (focus on every `[x]` step's Results blocks). Apply the rubric to pick the highest-abstraction, highest-leverage follow-up per category. Omit any category with no reasonable candidate. Return menu text ready to present verbatim -- opener + options + nothing else."* Present the agent's returned text verbatim. Routing on the user's letter choice (next `/step --0` turn) stays in main CC so /question-loop and /plan-creation invocations fire in the main conversation.

   **Opener (verbatim):**

   Plan's in the can. Before the result starts collecting dust in the corner, should we...

   **Generation rubric.** Read the Results blocks of every `[x]` step in `{{SOURCE_PLAN}}`. For each category below, pick the *highest-abstraction, highest-leverage* follow-up you can justify from what the plan built. Each option gets ONE sentence (the pitch, specific to this plan's output) + an optional second line (justification or tool/file reference). If no reasonable candidate surfaces for a category, omit that letter entirely.

   (a) New follow-up plan -- biggest unfinished thread, worthy of its own multi-step plan.
       -> /plan-creation (optionally /question-loop first if fuzzy)

   (b) Local scheduled job -- recurring script on user's machine that keeps today's work honest or extends it.
       -> Windows Task Scheduler (`schtasks`) or macOS/Linux cron

   (c) Claude Code recurring agent -- /loop (in-session) or /schedule (remote cron) that revisits the plan's output on a cadence.
       -> /loop or /schedule (ask which fits)

   (d) Parking-lot reminder -- time-delayed check ("in 2 weeks re-read X", "next month verify Y") not worth a plan slot yet.
       -> append to plans/followups-parking-lot.md (create file if missing)

   (e) Dogfood one small thing now -- <5-minute action leveraging today's work (skeleton file, quick doc tweak, running the feature once end-to-end).
       -> execute inline; no scheduling or plan creation

   (x) Brainstorm -- none of the above quite fits; open conversation.
       -> chat only, no tool invocation

   (q) Done -- clean close, file it away.
       -> exit skill normally

   **Routing on selection.** Execute the arrow action for the chosen letter. For (a) confirm whether user wants /question-loop first. For (c) ask /loop vs /schedule. For (d) confirm one-liner wording before appending. "No" / "q" / any "we're done" variant is always valid -- don't push.

   **Key principle:** the menu is generated per-plan, not pasted. Generic pitches are a smell -- if all five options read like they'd apply to any plan, re-read the Results blocks and find the plan-specific thread.

**Key principle for the whole step:** The plan created infrastructure -- now help the user extract value from it BEFORE filing the plan away.

Context: {{SOURCE_PLAN}}
Skills: plan-creation, question-loop
Mode: 1 (review)

---

### [ ] Step 8: Plan disposition + report + drain closing queue + self-delete (TERMINAL)

**This is the terminal step for all dispositions.** Sequence: choose disposition → execute → sweep → commit → report → drain → self-delete. For **template** disposition, Step 8 pauses after extraction — run `/step --0` again and it resumes at Phase C.

**/step Step 5 behavior:** This step is its own terminal action. The rm in the terminal phase deletes `{{CLOSING_PLAN}}`, so /step's normal "mark [x] and advance [n]" pass would fail. That is intentional: the terminal phase drains `active_plan` to null BEFORE the rm, so `/step --0` on next invocation sees no active plan and exits cleanly without trying to mark the deleted file.

---

**Re-entry detection (template resume).** On entry, check if `**Template extracted:**` exists in this step's body (written during a prior invocation's template extraction). If found, skip directly to Phase C — Phases A and B already ran.

---

**Phase A -- Mark plan complete.** Before disposition, flip `{{SOURCE_PLAN}}` frontmatter `status: in_progress` -> `status: complete`. This records that all steps finished regardless of what happens to the file next. Use raw-text surgery between the two `---` markers (same technique as Keep-in-place below).

---

**Phase B -- Disposition.** Ask the user what to do with `{{SOURCE_PLAN}}`. Present four options with cases for each:

**Keep in place** -- Is this plan reference material you want grep-discoverable in `plans/`?
- Flip frontmatter `status: complete` -> `status: reference` (Phase A already set `complete`). File stays at `{{SOURCE_PLAN}}`.
- Good for: recent closures you'll re-read in the next few weeks, plans whose Results blocks are still fresh operational context

**Template** -- Would this plan's step structure be useful for a different project?
- Copy to `plans/templates/` and generalize (replace project-specific details with `{{PLACEHOLDERS}}`, strip Results blocks, add inline gotcha warnings). Original removed from `plans/` during Phase C.2 (after the sweep reads it for `Temp files:` tags).
- Good for: rename migrations, cleanup sweeps, pipeline builds -- anything you'd do again with different inputs

**Archive** -- Was this hard-won architectural work worth keeping for reference but out of the live working set?
- Move to `plans/archive/`.
- Good for: complex multi-plan sagas, novel system builds where the design rationale matters

**Delete** -- Did the plan's value get fully captured elsewhere?
- Delete the file entirely.
- Good for: one-off migrations where a skill already captures the patterns, audit passes that produced a lasting artifact, mechanical bulk edits

**Process:** Present the four options with a one-sentence case for each, tailored to `{{SOURCE_PLAN}}`. Let the user decide. Execute their choice.

**If Keep in place:** Edit `{{SOURCE_PLAN}}` YAML frontmatter: change `status: complete` -> `status: reference` (Phase A already moved from `in_progress`). Preserve all other frontmatter fields verbatim; preserve the plan body exactly. Same raw-text surgery technique as Phase A.

**If Template:**

1. **Context line audit (pre-extraction).** Scan ALL `Context:` lines in `{{SOURCE_PLAN}}` -- pending, current, AND completed steps -- for plan-hygiene bugs:
   - Directory references (path ends in `/` or has no file extension)
   - Vague non-file references ("all X files", "output from Step Y", "reviewed worldbuild")
   - Single files >25K tokens with no line range or section anchor

   If any are found, surface to user with proposed fixes (move to `Script input:` / `Grep targets:`, narrow to specific files, add line ranges) BEFORE extracting. A directory bomb in a templated plan becomes a directory bomb in every plan spawned from that template. Canonical rule: `.claude/CLAUDE.md` § Step Context Hints -- "Phase C is code, not Claude."

2. **Extract template.** Copy to `plans/templates/` and generalize. Two template archetypes:
   - **Parameterized runbook** (like `project-rename.md`) -- all variables known upfront, deterministic steps
   - **Discovery-first protocol** (like `project-cleanup-post-refactor.md`) -- Step 1 discovers scope, downstream steps consume its output

   Key structural patterns for generalized templates:
   - Variable declaration header with boolean flags for conditional steps
   - Steps tagged as `[REQUIRED]`, `[CONDITIONAL: variable]`, or `[JUDGMENT-GATE]`
   - Empty schema tables (column headers, no pre-filled data)
   - Results blocks stripped; replaced with inline `(!) Gotcha:` warnings mined from the original
   - Entry/exit criteria per step

   Do NOT delete `{{SOURCE_PLAN}}` during extraction -- it stays in `plans/` until Phase C.2 removes it. The sweep in Phase C.1 needs to read it for `Temp files:` tags.

3. **Write marker and STOP.** Add to this step's body: `**Template extracted:** plans/templates/{{SOURCE_PLAN_NAME}}.md`. Tell the user: "Template extracted. Run `/step --0` to finish the close (sweep, commit, teardown)." Do NOT proceed to Phase C in this invocation.

**If Archive or Delete:** Execute immediately, proceed to Phase C.

---

**Phase C -- Sweep, commit, and teardown (all dispositions).**

For template disposition, this phase runs on the second `/step --0` invocation (after re-entry detection skips to here).

**C.1 — Temp-files sweep.**

**Scope:** source plan only. Only parse `Temp files:` lines from `[x]` steps within `{{SOURCE_PLAN}}`. Tags in other plans, sub-plans, or Context-referenced files are out of scope. Closing plans must not produce scratch — if a closing-plan template ever needs scratch, fix it at the template level, not here.

**Procedure:**

1. **Single-pass walk.** Read each `[x]` step in `{{SOURCE_PLAN}}` once. From the same read, extract every `Temp files:` line AND synthesize a one-sentence plain-English purpose for each file grounded in the step's description + Results block. Collect into a list of `(path, purpose)` pairs.

2. **Glob expansion.** Expand any glob patterns (e.g., `scratch-*.py`) against the current filesystem at sweep time. Missing files and zero-match globs are filtered from the confirmation list silently — they appear in the commit message footer under `Pre-deleted or zero-match (skipped):` instead.

3. **Path safety.** Validate each expanded path: resolve symlinks, confirm `Path.resolve().is_relative_to(repo_root)`. Reject absolute paths outside the repo, `..` escapes, and symlinks that resolve outside the repo root. On ANY rejection: **halt the close** with:

   ```
   Tag <offending path> in <source plan step> resolves outside the repo.
   Fix the tag in {{SOURCE_PLAN}} or remove it, then rerun /step --0.
   ```

   Do NOT mark Step 8 `[x]` on halt. Phases A and B are safe to repeat on rerun.

4. **Confirmation UI.** If the list has 1+ files after filtering, present:

   ```
   About to delete N temporary files only created for the purpose of this plan:

   - path/to/file.py — one-sentence purpose
   - path/to/other.md — one-sentence purpose

   Proceed? [y/n]
   ```

   If the list is empty (all files pre-deleted or zero-match), skip the UI entirely — log all paths to the commit footer and continue to C.2.

5. **Response handling:**
   - `yes` / `y` → delete all files in the list.
   - `no` / `n` with exactly 1 file in the list → skip sweep entirely, continue to C.2.
   - `no` / `n` with 2+ files → present per-file selection menu: `Select files to delete (comma-separated numbers, or "none"): 1,2,4`.
   - `no` + qualifier in same message (e.g., `no, keep the spec`) → parse qualifier, drop matched files, proceed with remainder.

6. **Delete mechanics.** For each confirmed file: `git rm -f <path>` if tracked, else `rm -f <path>`. On per-file failure (permission denied, file locked, path invalidated between confirm and delete): skip that file and continue. Append to commit message footer under `Sweep failures: <path> (<reason>)`.

7. **Commit message footer lines** (assembled from sweep, included in C.4 commit):
   - `Sweep: deleted N files` (always present if sweep ran, even if N=0)
   - `Pre-deleted or zero-match (skipped): <paths>` (only if any)
   - `Sweep failures: <path> (<reason>)` (only if any)

**C.2 — Execute disposition action:**

- **Keep in place:** the `reference` frontmatter flip from Phase B is the action (Phase A set `complete`, Phase B refined to `reference`).
- **Archive:** `git mv {{SOURCE_PLAN}} plans/archive/{{SOURCE_PLAN_NAME}}.md`
- **Delete:** `git rm {{SOURCE_PLAN}}`
- **Template:** `git rm {{SOURCE_PLAN}}` (source plan survived until now so C.1 sweep could read it for `Temp files:` tags)

**C.3 — Close the closing plan:** `git rm {{CLOSING_PLAN}}`

**C.4 — Git behavior (probe-and-configure).**

On first close, ask the user how plan-completion should handle git:

```
How should plan-completion handle git on close?

(a) Commit only — stage and commit, don't push
(b) Commit and push — stage, commit, push to remote
(c) Skip this time — leave changes in working tree, you handle git
(d) Skip always — never touch git during plan close

Choose [a/b/c/d]:
```

**If (a) commit-only or (b) commit-and-push:** build the staging list, stage, and commit.

Surgical commits only — do not use `git add -A` or `git add .`. Build the staging list explicitly:

1. Read all `**Results:**` sections in `{{SOURCE_PLAN}}` and extract every file path mentioned (created, modified, normalized, etc.).
2. Add to staging list: `{{SOURCE_PLAN}}` itself (if not already removed by disposition), any doc files updated in Step 4, and any followup plan file created in Step 2.
3. Add disposition artifacts: archive destination path (if archive), `{{SOURCE_PLAN}}` deletion (if delete or template), `plans/templates/{{SOURCE_PLAN_NAME}}.md` (if template). Add `{{CLOSING_PLAN}}` deletion from C.3.
4. Add sweep deletions from C.1 (files confirmed and deleted during sweep).
5. Do NOT stage `{{SOURCE_QUEUE}}` or `{{CLOSING_QUEUE}}` — gitignored. Queue state is per-session, never enters history.

Stage the list: `git add [file1] [file2] ...`

Run `git status --short` to verify — every staged file should trace back to a plan step, disposition action, sweep deletion, or closing-plan teardown. If anything unexpected is staged, unstage it: `git reset HEAD [file]`.

Nothing-to-commit guard: if every candidate comes back clean (nothing to stage), skip the commit entirely. Do NOT force `git commit --allow-empty`.

Commit message format: `type (feat/fix/docs/refactor/chore): scope: description`

Include sweep summary in commit message footer (details specified in C.1 sweep protocol).

`Co-Authored-By: Claude <model-version> <noreply@anthropic.com>`

If **(b)**, also push: `git push`. If push fails: `git pull --rebase && git push`. If conflicts exist, stop and ask user — do NOT force push.

**If (c) skip-this-time:** do nothing with git. Files stay in the working tree as-is. User commits manually when ready.

**If (d) skip-always:** same as (c) for this close.

**Template-edit invitation (all choices).** After executing the chosen option, offer:

```
Want me to lock this choice into the template so future closes skip the prompt?
[y/n]
```

If **yes**: edit `plans/templates/plan-closing.md` to replace this probe section (C.4) with the hardcoded behavior for their choice. Specifically:
- **(a)** → remove the probe, keep the staging/commit block, delete the push line and push error-recovery section
- **(b)** → remove the probe, keep the staging/commit/push block as-is (matches the live template)
- **(c)** → N/A — this is a one-time skip, not a permanent preference. Do not offer the template edit for (c).
- **(d)** → remove the probe and the entire staging/commit/push block, replace with: `No git actions — changes left in working tree.`

If **no** or **(c)**: leave the template unchanged. The probe fires again on the next close.

---

**Phase D -- Report completion to the user:**

```
Plan complete! All steps done.

Git: [committed only / committed and pushed / skipped (manual) / skipped (always)]
Plan disposition: [kept in place / templated / archived / deleted]
```

---

**Phase E -- Queue drain + self-delete (terminal, all dispositions).**

**Exit trap critical.** This closing plan is ephemeral scaffolding. Leaving it in `plans/` after close would cause the closing queue to pick it up on next `/step --0` invocation OR trigger auto-/plan-completion recursion (since all its steps would be `[x]`). Phase E cleans both the queue entries and the file.

1. **Drain `{{SOURCE_QUEUE}}`:** set `active_plan` to `null` (or next in queue), remove `{{SOURCE_PLAN}}` from `queue` array. Save. **Not staged — gitignored.**

2. **Drain `{{CLOSING_QUEUE}}`:** remove `{{CLOSING_PLAN}}` from the `queue` array. If `active_plan` points at `{{CLOSING_PLAN}}`, set it to `null` (or next in queue). Save. **Not staged — gitignored.**

3. **Self-delete:** `{{CLOSING_PLAN}}` was already `git rm`'d in C.3 and committed — the file is gone from the working tree. If it somehow still exists, `rm {{CLOSING_PLAN}}` as a safety net.

4. **End of workflow.** Do NOT invoke `/plan-completion` again. Do NOT continue to additional steps. Queue drains in items 1-2 set `active_plan` to null BEFORE any file deletion, so `/step --0` sees no active plan and exits cleanly. /step's own Step 5 (mark [x] / advance [n]) is SKIPPED for this step — the plan file is already gone.

Context: {{SOURCE_PLAN}}, {{SOURCE_QUEUE}}, {{CLOSING_QUEUE}}
Mode: 1 (review)

---

## Error Recovery

**If git push fails in Step 8 (only when user chose "commit and push"):**
1. Check for conflicts: `git status`
2. If behind remote: `git pull --rebase && git push`
3. If conflicts exist: Stop and ask user for guidance. Do NOT force push.

**If a source-plan step was marked done incorrectly:**
1. Edit `{{SOURCE_PLAN}}`: change `[x]` back to `[n]` and remove the `{timestamp}` suffix
2. Re-run `/step {{SOURCE_PLAN}}` to retry that step
3. After retry lands, restart this closing plan from Step 2

**If `{{SOURCE_QUEUE}}` is corrupted:**
1. Delete `{{SOURCE_QUEUE}}`
2. Run `/step {{SOURCE_PLAN}}` to reinitialize (in whichever queue slot the source was using)
3. Resume closing plan

**If `{{CLOSING_QUEUE}}` is corrupted:**
1. Delete `{{CLOSING_QUEUE}}`
2. Delete `{{CLOSING_PLAN}}`
3. Re-run `/plan-completion` on `{{SOURCE_PLAN}}` -- skill will respawn both the queue file and a fresh closing plan

**If this closing plan gets stuck mid-execution:**
- Delete `{{CLOSING_PLAN}}` manually
- Re-run `/plan-completion` on `{{SOURCE_PLAN}}` to spawn a fresh closing plan
- The template has no side effects until Step 2's audit resolutions are applied, so respawning is safe

