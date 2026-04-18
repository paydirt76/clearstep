---
description: Execute next step from active plan. Reads queue file, finds next unmarked step, executes it, updates plan, stops.
argument-hint: [--N] [plan-file-path]
---

# Step Executor

## Your Task

Execute exactly ONE step from the active plan, then stop.

## Bright-line rules

These apply at EVERY phase of /step execution — Phase C pre-loads, Step 4 edits, Step 5 plan updates, all of it.

### Banned: performative verification after edits

After Edit or Write returns "file updated successfully", the tool has ALREADY confirmed the change. Do NOT run follow-up commands whose only purpose is confirming the edit landed. Specifically banned:

- `Read`, `Grep`, `head`, `tail`, `cat`, or `wc` on a file you JUST edited in this conversation
- `git diff` on a file whose only changes are edits you just made
- Spot-checking the plan file after marking `[n]` → `[x]` in Step 5
- Re-reading a file after a multi-Edit rename to show the final state
- Any tool call framed as "let me verify the change landed" / "let me make sure it took" / "let me confirm"

**Still legitimate** (commands that tell you something *new*):
- Runtime behavior: `python script.py --dry-run`, `py_compile`, running the actual tool the step built
- Filesystem state you haven't directly checked: `ls` a directory you don't know the contents of, reading PKG-INFO
- Cross-file side effects a single tool can't report: "did the sync hook regenerate the sibling README after I edited CLAUDE.md?"
- `Grep` for REMAINING refs after a *partial* rename — surveying unchecked state, not re-checking what you wrote
- A single spot-check answering a specific uncertainty the user flagged out loud

**Bright-line test:** "Does this tool call tell me something I don't already know from the last tool's success response?" If NO → it's performative, skip it. If YES → legitimate, do it.

**When in doubt, don't verify.** The user reads the diff in their terminal. They don't need proof-of-work.

---

## Step 1: Parse Arguments and Load Queue State

**Parse `$ARGUMENTS` for queue number and plan path:**

| Argument | Queue File | Example |
|----------|-----------|---------|
| (none) | `.step-queue.json` | `/step` |
| `--0` | `.step0-queue.json` | `/step --0` |
| `--2` | `.step2-queue.json` | `/step --2` |
| `--3` | `.step3-queue.json` | `/step --3` |
| `--4` | `.step4-queue.json` | `/step --4` |
| `--5` | `.step5-queue.json` | `/step --5` |
| `--6` | `.step6-queue.json` | `/step --6` |
| `--7` | `.step7-queue.json` | `/step --7` |

**Extraction logic:**
1. Check if `$ARGUMENTS` contains `--N` pattern (e.g., `--0`, `--2`, `--3`, `--4`, `--5`, `--6`, `--7`)
2. If found: use `.stepN-queue.json` as queue file
3. If not found: use `.step-queue.json` (default)
4. Remaining argument (if any) is the plan file path

**CRITICAL: Sequential flow - do NOT parallelize:**

1. **First:** Read the queue file using the **Read tool** (not `cat`).
   - **Default queue:** `Read plans/.step-queue.json`
   - **`--N` queue:** `Read plans/.stepN-queue.json` (e.g., `plans/.step7-queue.json`)
   - Use **relative paths** and the **Read tool** — not `cat` with backslash Windows paths. **On Windows + Git Bash:** MSYS mangles backslashes, so a path like `/your/project/plans/.step7-queue.json` (passed as its Windows backslash form to `cat`) silently returns "no such file." Read tool is immune to this. (Mac/Linux users: skip — not applicable.)
   - **If Read returns "file not found":** the queue has never been used. Treat as empty: `{"active_plan": null, "queue": []}`. This is the only legitimate "no queue file" case.
   - **If Read succeeds:** parse the JSON. Look at `active_plan`. If it's a non-null string, that IS the active plan — proceed to Step 2.

2. **Sanity-check before falling through to Step 1B:**

   If you are about to go to Step 1B because the queue "looks empty," you MUST first verify with a fresh Read. The only valid triggers for Step 1B are:
   - `Read` returned a genuine "file not found" error, OR
   - The file parsed successfully AND `active_plan` is explicitly `null`, AND no plan path was passed as an argument.

   **Never go to Step 1B based on a `cat` command that returned nothing — that's the mangled-path bug, not an empty queue.** If `cat` (or any shell command) returns empty/missing, re-verify with the Read tool before proceeding.

3. **Then check:**

| Condition | Action |
|-----------|--------|
| Plan path in args | Set as active plan → **Go to Step 2** |
| `active_plan` is a non-null string | **Go to Step 2** |
| Queue file genuinely missing AND no plan arg | **STOP HERE → DO STEP 1B BELOW** |
| `active_plan` is `null` AND no plan arg | **STOP HERE → DO STEP 1B BELOW** |

### Step 1B: Plan Selection Menu — REQUIRED WHEN NO ACTIVE PLAN

**IF YOU REACHED HERE, YOU MUST:**
1. Enumerate plan files and read any existing queue files
2. Derive status/progress/next-step per plan from its own headers
3. Render the table (format below)
4. Ask user which plan to load
5. **DO NOT** continue to Step 2 until user selects

**Enumerate (parallel — run all at once):**
- `Glob pattern="plans/*.md"` — plan files
- `Glob pattern="plans/.step*-queue.json"` — existing queue files (none will match on a fresh install; that's fine)

**Read each matched queue file** (parallel Reads). For each, note `active_plan` → queue name (e.g., `.step4-queue.json` → `--4`, default queue → blank). Build a `plan_filename → queue_name` map.

**For each plan file** (parallel Grep):
- `Grep pattern="^### \[" path=[plan_path] output_mode="content" -n=true` — top-level step headers
- Count `[x]` markers (completed) and total markers (all). Progress = `completed/total`.
- Find the first `[n]` header, or failing that, first `[ ]` header → that's the "Next Step" column (trim timestamp suffixes like `{2026-...}`).
- Status: all `[x]` → `Done`; any `[x]` → `WIP`; zero `[x]` → `Ready`.

**If Glob returned zero plan files:** Tell user `No plans yet — run /plan-creation to make one.` and stop.

**Render this exact table format:**
```
Available Plans [Queue N]

| # | Plan                         | Status | Queue   | Progress | Next Step                    |
|---|------------------------------|--------|---------|----------|------------------------------|
| 1 | context-assembler-fixes      | WIP    | --4     | 4/7      | Step 5: Remove rules         |
| 2 | chapter1-accuracy-fixes      | WIP    | -       | 13/15    | Step 13 Findings             |
| 3 | arc-raiders-fanfic-research  | Ready  | -       | 0/8      | Step 1: Create Dir           |
| 4 | situation-extraction         | Done   | -       | 6/6      | --                           |

Which plan should I load into Queue N? (Enter number or filename)
```

**Sort order:** In-progress with queue → in-progress without → ready → complete.

**After user selects:** Update queue file with `active_plan`, then continue to Step 2.

---

## Step 2: Smart Context Loading

**Do NOT read the entire plan file.** Use phased reads to build surgical context.

### Phase A: Orientation (parallel — run all three at once)

1. **Read plan header** — first 80 lines (gets Goal, Current State, Constraints):
   - Use Read tool with `limit=80` on the plan file

2. **Grep for all step headers** — see progress at a glance:
   - `Grep pattern="^### \[" path=[plan_path]` (top-level steps)

3. **Grep for the [n] marker** — find the exact next action:
   - `Grep pattern="\[n\]|\(n\)|<n>" path=[plan_path]`

**After Phase A, you know:**
- What the plan is about (header)
- Progress: count `[x]` vs total from step headers
- Exact line number of the next step (`[n]` marker)

**Fallback:** If no `[n]`/`(n)`/`<n>` found, fall back to first `[ ]` step. Flag to user: "No [n] marker found — using first open step. Consider marking it [n]."

### Phase B: History (parallel — run all three at once, after Phase A)

1. **Grep for Results blocks** from completed steps:
   - `Grep pattern="\*\*Results" path=[plan_path]`

2. **Grep for Session Context** sections:
   - `Grep pattern="Session Context|Context for Next Step" path=[plan_path]`

3. **Grep for open LANDMINEs** across the full plan:
   - `Grep pattern="LANDMINE" path=[plan_path]` with `-n` and `-A 1` for context
   - Exclude lines matching `LANDMINE\[resolved\]` — those are silenced

**Then:**
- For (1) + (2): Read 15-20 lines around each Results/Context match to get the summaries. If many (10+), prioritize the 3-5 most recent (closest to current step number).
- For (3): Surface **ALL** open landmines in the Step 3 display (no 3-5 recency cap — they're short one-liners and their whole point is surviving age-decay). Each becomes a one-line bullet: step it was discovered in → the landmine text (truncate at ~120 chars).

**Why landmines get their own grep:** landmines are deferred obligations written at discovery but needing to fire at a later moment of obligation. They live in completed-step Results blocks, which Phase B's 3-5-most-recent prioritization prunes away before they fire. The separate grep bypasses the prioritization and surfaces them every run. Authoring convention: write `LANDMINE:` (or `LANDMINE for Step N:`) when you note one. When fixed or no longer applicable, delete the line or change to `LANDMINE[resolved]:` to silence future surfacing.

### Phase C: Current Step + Pre-load (after Phase A gives you the line number)

1. **Read the full current step section** — from the `[n]` line to the next step header:
   - `Read [plan_path] offset=[n_line] limit=60`
   - Adjust limit if the step is longer. Stop at the next `### [` or `### (` header.

2. **Pre-load Context hint files (with token budget)** — if the step includes a `Context:` line like:
   ```
   Context: rate_limiter.py:45-120 (DualRateLimiter class), README.md:## Architecture
   ```
   Read each referenced file/range. Use line ranges if specified — never full-read when ranges exist. For fuzzy symbol refs ("render_project_list downstream"), grep the symbol first to bound the read. Run these reads in parallel.

   **Token budget awareness:** After loading each file, estimate tokens as `len(content) // 4`. Track cumulative tokens across all Context files. If the next file would push the total past **50,000 tokens**, skip remaining files and warn:
   ```
   Token budget: 47,200/50,000 used. Skipping remaining Context files: [list]
   ```
   This prevents Phase C from flooding the context window with pre-loaded files.

   **Do NOT pre-load `Script input:` lines.** If the step lists paths under a line like `Script input (DO NOT pre-load — stream to Opus via script): path/to/bundle.md`, those files are destined for an external API call via a Python script — Claude Code should never read them. Skip them during Phase C entirely; the script in Step 4 reads the file directly and streams it to the API.

   **Do NOT pre-load `Grep targets:` lines either.** Same shape as Script input: large file sets the step touches via Glob/Grep during execution, not via Read at Phase C. Skip them entirely; the actual narrowing happens in Step 4.

   **Plan-hygiene bug detection during Phase C.** If a `Context:` entry matches ANY of the following, treat it as a plan-hygiene bug and flag it in Step 5f — DO NOT attempt to pre-load:

   - **Directory reference** — path ends in `/`, or no file extension (e.g. `world_bible/`, `docs/review/`)
   - **Vague non-file reference** — "all X files", "output from Step Y", "reviewed worldbuild", any phrase Phase C can't enumerate
   - **Single oversized file** — one path's content alone would exceed 25K tokens with no line range or section anchor

   The flag goes in Step 5f reflection with a proposed fix: move to `Script input:` (if API-bound), `Grep targets:` (if searched at execution), narrow to specific files, or add a line range. Do NOT silently swallow the path — the latent budget bomb is exactly what this guardrail catches. The "Phase C is code, not Claude" principle in CLAUDE.md § Step Context Hints is canonical.

3. **Note Skills hints** — if the step has `Skills: parallel-batch, cerebras-api`, remember to invoke those skills during execution.

4. **Note Mode hint** — if the step has a `Mode:` line, note the approach for Step 4.

5. **Sub-step Context inheritance check.** Sub-sub-steps (`<n>`) and sub-steps (`(n)`) do NOT inherit the parent's `Context:` line. Phase C loads only the active step's own Context. If the active marker is on a sub-sub-step / sub-step AND that step has NO `Context:` line of its own AND the parent step's `Context:` either (a) says "narrow per sub-step" / "per-sub-step Phase C should narrow" / similar handwave, or (b) lists 3+ review / audit / response files as a blob, FLAG in Step 3 display:

   ```
   ⚠ Phase C loaded nothing step-specific: parent Step N has kitchen-sink Context; <n> sub-step has none. Parent Context is dead weight at this depth.

   Options:
     (a) Author a Context line for this sub-step now (recommended — surgical pre-load)
     (b) Proceed and grep for specific evidence during Step 4 (slower, one-off)
   ```

   Then ask the user which they want before continuing to Step 3 / Step 4. The root-cause fix lives in `/plan-creation` (each `<x>`/`( )` child should carry its own narrowed Context when the parent's is a multi-file blob), but at execution time, offering to author the missing Context takes 30 seconds and saves minutes of run-time grep.

**Phase B and C can run in parallel** — B depends only on knowing which steps are completed (from Phase A step headers), and C depends only on the `[n]` line number (from Phase A grep).

---

## Step 3: Display Next Step

Show a structured summary before executing:

```
Active Plan [Queue N]: [plan filename]
Progress: [x_count]/[total_count] steps complete

Completed Work:
- [x] Step 1: [title] -> [1-line from Results block]
- [x] Step 3: [title] -> [1-line from Results block]
- [x] Step 5: [title] -> [1-line from Results block]

Open Landmines:
- Step 4c -> [landmine text, ~120 char]
- Step 6f2 -> [landmine text, ~120 char]

Executing: [n] Step [N]: [title] (mode: [mode label])
[Full step content from Phase C]

Pre-loaded: [list of Context files that were read]
```

**Rules:**
- Show at most 5 recent completed steps (oldest first)
- If more than 5 completed, prefix with "...(N earlier steps)"
- Omit `[Queue N]` if using default queue
- Omit `Open Landmines` section if Phase B grep (3) returned zero matches
- Omit `Pre-loaded` line if no Context hints were specified
- Each completed step summary is ONE line: step marker + title + arrow + key result
- Each landmine is ONE line: source-step marker + arrow + landmine text (truncate at ~120 char)

---

## Step 4: Execute the Step

**Mode framing:** If the step has a `Mode:` hint, use it to set your approach:

| Mode | Approach |
|------|----------|
| 1 (review) | Analyze and report. Minimize changes — only edit if explicitly asked in the step. |
| 2 (create) | Build new files and functionality. |
| 3 (test) | Run the script with `--dry-run`. Inspect output. `py_compile` for syntax. No self-written test harnesses. |
| 4 (fix) | Diagnose and fix a specific issue. Stay narrow. |
| 5 (refactor) | Restructure existing code. Preserve behavior, improve structure. |

If no Mode is specified, infer from the step description (most steps are obvious).

**Then do the work:**
- Read files mentioned (skip any already pre-loaded in Phase C)
- Make edits specified
- Run commands listed
- Create files if needed

**Skill Invocation:** If step text contains "invoke [skill-name] skill", load and follow that skill's pattern.

**Sub-step awareness:** If the `[n]` marker is on a parent step that has `( )` children, do NOT execute the parent description — execute the `(n)` child instead. If no child is marked `(n)`, mark the first `( )` child as `(n)` and execute that.

**CRITICAL:** Do ONLY this one step (or sub-step). Do not continue to subsequent steps.

---

## Step 5: Update the Plan

**CRITICAL: Read the plan file RIGHT before using Edit tool.**

### 5a: Mark Current Step Done

**First, run `date -u +"%Y-%m-%dT%H:%M:%S"` to get the real timestamp. NEVER guess.**

Mark done AND append the timestamp in the step header:

| Was | Becomes |
|-----|---------|
| `### [n] Step N: Title` | `### [x] Step N: Title {YYYY-MM-DDTHH:MM:SS}` |
| `(n) Sub-step title` | `(x) Sub-step title {YYYY-MM-DDTHH:MM:SS}` |
| `<n> Sub-sub-step title` | `<x> Sub-sub-step title {YYYY-MM-DDTHH:MM:SS}` |

**Then strip the completed step's body.** Delete everything between the step header line and the `**Results:**` block you're about to add. The step header + Results block is the complete record. Do NOT preserve the original description, Context/Skills/Mode/Design hints, or any pre-execution scaffolding.

**Exception:** If the step is being marked `[~]` (superseded, not executed), keep the full body -- the plan-revision history is the value.

### 5b: Add Results Block

Add immediately after the step header (the body was stripped in 5a):

```markdown
**Results:**
- What was created/modified (with paths)
- Key outputs or metrics
- Decisions or deviations from the plan
- Landmines the next implementer would hit
```

**Hard cap: 2-5 bullets, 100 words max.** If you're writing more, you're duplicating content that belongs in the files you just created/modified.

**Results are receipts, not design docs.** If a step created a design document, the Results block says "Created docs/foo.md (N lines, covers X/Y/Z)" -- it does NOT restate the document's contents. If a step made a schema change, Results names the columns added -- it does NOT include the CREATE TABLE statement. The artifact is the source of truth; Results is the pointer + decisions.

**The ONLY things that earn verbose treatment:** LANDMINE discoveries, plan-premise corrections, MVP deviations, and rejected alternatives. These are decisions that live nowhere else. Everything else is in the code.

**If the step wrote an artifact a future step will PARSE (bundle, manifest, JSONL, anything a downstream script will grep/slice):** add a `Markers:` line to Results listing the section-grammar regexes/literals you used (e.g. `Markers: ===== FILE: <name> =====, ### Layer N — <title>, **Delta #N — <title>**`). Phase B reads Results blocks, so this teaches future steps the file's structure for free instead of forcing them to grep-discover it.

### 5c: Advance the [n] Marker

Follow this decision tree to find and mark the next action:

**If current was a sub-sub-step `<n>`:**
- Next `< >` sibling exists → mark it `<n>`
- No more `< >` siblings → parent sub-step is done: mark parent `(x)`, then apply sub-step rule below

**If current was a sub-step `(n)`:**
- Next `( )` sibling under same parent exists → mark it `(n)`
- No more `( )` siblings → parent step is done: mark parent `[x]`, then apply top-level rule below

**If current was a top-level step `[n]`:**
- Find next `[ ]` step in plan
- If that step has `( )` children → mark first `( )` child as `(n)` (parent stays `[ ]`)
- If that step has no children → mark it `[n]`

**Blocked steps:** If the next candidate is `[w]` (waiting) or `[!]` (stuck):
- Skip it, try the one after
- Flag to user: "Skipped Step N — marked [w] waiting on external dependency" or "Skipped Step N — marked [!] stuck"
- If ALL remaining steps are `[w]` or `[!]`, report blocked status and stop

**No more steps:** Plan is complete → proceed to Step 6

### 5d: Sharpen Next Step's Context Hints

After completing a step, you know more than the plan writer did. Update the NEXT step's `Context:` line with what you learned:

- Files you created or modified that the next step needs → add to `Context:`
- Line ranges you discovered are relevant → add specific ranges
- Skills you found necessary that aren't listed → add to `Skills:`

**Example:** Step 5 created `validator.py` and the next step needs it:
```markdown
### [n] Step 7: Add validation to pipeline

Integrate the validator into the main processing loop.

Context: validator.py:20-45 (validate_record function), pipeline.py:80-110 (process loop)
Skills: parallel-batch
```

If the next step already has a `Context:` line, merge your additions into it. If it has none, add one.

### 5e: Session Context (for non-file knowledge)

**Problem:** After `/clear`, conversation memory is lost. The next `/step` only sees the plan file and queue file.

**Rule:** If you discovered or decided anything the NEXT step needs that ISN'T captured by Context hints (which point to files), persist it as text in the plan.

**When to add:**
- Research/analysis produced findings the next step depends on
- Made decisions that affect how future steps should execute
- Identified issues, blockers, or deviations from the original plan

**Format:** Add directly below the completed step's Results block:

```markdown
**Context for Next Step:**
- [Critical info the next step needs]
- [Decisions made that affect future execution]
```

**Test:** "If I `/clear` right now, would the next `/step` have everything needed to continue?" If no, add more context. If it's a file reference, put it in the `Context:` line (5d). If it's knowledge, put it here (5e).

---

## Step 5f: Reflect on Plan Direction — MANDATORY

**This step is MANDATORY. Walk the reflection visibly and echo the outcome to the user before moving to Step 6.**

The job: catch plan invalidations. Places where an upcoming step's description is now wrong, an assumption shifted, or work you did renamed/moved something a Context line points at. That's the bug this guardrail prevents. It is NOT a license to annotate downstream steps with everything you learned.

**Before walking the questions, name the work.** Write down the 3-8 concrete things this step actually produced -- functions added, files touched, schema changed, new JSON keys, behavior rewired, landmines hit. Then run each question against that list. If your reflection is `NO PLAN CHANGES NEEDED` and the only structural edit you can point at is advancing the `[n]` marker, you reviewed the marker instead of the work and did not do 5f. Go back and walk the questions against the actual diff.

### Required: walk these questions

1. Did this step make an upcoming step's description wrong (work already done, approach changed, dependency removed)?
2. Did I defer something an upcoming step assumed would already be in place (schema column, API, helper)?
3. Did I change a public API, schema, or file path that an upcoming step's Context line currently points at?
4. Did I hit a landmine the next implementer would hit too, that ISN'T visible from the code or design doc the step already references?
5. Is the overall goal still correct?

### Required: echo the outcome

**Case A — no changes needed:**
```
NO PLAN CHANGES NEEDED
```
A legitimate outcome. If upcoming descriptions still match reality and Context lines still point at the right files, say so. Don't manufacture changes to make the echo feel earned.

**Case B — targeted fixes (typically 1-3 edits):**
```
PLAN CHANGES:
- [what you changed and why]
```
Edit the plan file: fix a wrong description, mark an obsolete step `[~]`, add a missing dependency, or update a Context line to POINT at a file you moved or created. If you find yourself making 5+ edits or writing prose explanations into Context lines, **STOP** — you're duplicating info that belongs in code comments or the Results block.

Also add a `- Plan revision: [what changed and why]` bullet to the completed step's Results block.

**Case C — big changes (scope shift, new direction):**
```
PLAN CHANGES NEEDED — STOPPING FOR CONFIRMATION
[what you learned that invalidates the plan]
[what you think should change]
```
STOP. Do NOT edit the plan. Wait for user confirmation before editing.

### Guardrails

- **Context lines are pointers, not documentation.** If a Context update wants more than ~15 words of prose, it belongs in a code comment, the Results block, or the design doc -- not the Context line. The implementer will open the file; Context just tells them which one. Prose in a Context line is the tell that you're duplicating info the implementer can read from the source.
- **No duplicating the diff.** The `**Results:**` block captures what you did. Don't re-explain it in Context lines on other steps. If a future step needs to know about today's work, the Context line should point at the file or the Results block, not restate it.
- **Scope discipline applies.** Reflection is not a license to restructure downstream steps "while you're thinking about them." If a step's description is still correct, leave it alone.
- **One-minute fixes beat landmines.** If a Q4 finding is a fix you can land in <60 seconds with one or two Edits — a typo in the canonical doc, a stale marker, an inconsistent example — just do it as part of THIS step and note the drive-by in your Results block. Landmines are for genuine deferred work: multi-file changes, scope shifts, anything needing user input or a fresh decision. Logging a landmine for a one-line nit is bureaucracy that future-you has to clean up. Scope discipline forbids RESTRUCTURING — it does not forbid fixing the dent you noticed while you were in the file.
- **Refinements to the IMMEDIATE next step's Context belong in 5d, not here.** 5f is for non-adjacent steps or multiple downstream steps.
- **Echo is non-negotiable.** Even if nothing changed, print `NO PLAN CHANGES NEEDED`. Silence = reflection didn't happen.

---

## Step 6: On Plan Completion

**Skip unless all plan steps are now marked `[x]`.**

If plan is complete, tell the user:

```
Plan complete! Run /plan-completion to generate the Hall of Heroes eulogy and finalize.
```

Do NOT change plan status or remove from index — `/plan-completion` handles the full ritual (eulogy generation, status transition to `reference`, index removal).

## Step 7: Stop

**Output summary:**
```
Completed [Queue N]: Step [N] - [title]
Plan: [filename]
Progress: [x_count]/[total_count]
Next: [n] Step [N+1] - [next title] (or "Plan complete!" if no more steps)

To continue: /step [--N]
```

**Then STOP.** Do not execute the next step.

---

## Queue File Management

**Creating queue file (if plan path provided):**
```json
{
  "active_plan": "plans/[plan-name].md",
  "queue": ["plans/[plan-name].md"]
}
```

**Queue file naming:**
- Default: `.step-queue.json`
- With `--N`: `.stepN-queue.json`

---

## Error Handling

**Plan file not found:** Show error and list available plans.

**No `[n]` marker found:** Fall back to first `[ ]` step. Flag: "No [n] marker -- using first open step."

**No more steps (plan complete):**
- Follow Plan Completion Workflow from CLAUDE.md
- Then show Plan Selection Menu (Step 1B)

**Next step is `[w]` or `[!]`:** Skip and flag to user. Try next `[ ]` after it.

**All remaining steps `[w]`/`[!]`:** Report blocked status and stop.

**Step unclear:** Ask user for clarification before proceeding.
