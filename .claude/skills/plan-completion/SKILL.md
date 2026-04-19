# Plan Completion Skill

triggers: plan complete, all steps done, finish plan, mark done, mark complete, update queue, commit changes, push changes, delete plan

## Overview

This skill guides Claude through the proper workflow when completing plans. It ensures consistent step marking, documentation updates, git operations, and cleanup.

## !!! MANDATORY STEP CHECKLIST !!!

Every `/plan-completion` invocation MUST execute ALL of these. No exceptions.
No "this feels internal so I'll skip doc updates." No shortcuts.

- [ ] Step 2: Read current documentation
- [ ] **Step 4: LANDMINE audit** (see full rules below)
- [ ] **Step 6: Update CLAUDE.md -- MANDATORY, NEVER SKIP** (see full rules below)
- [ ] Step 8: Git commit and push
- [ ] Step 10: Run completion ritual (eulogy + status transition)
- [ ] **Step 12: Summary + follow-up prompt** (forward-looking — BEFORE disposition)
- [ ] Step 14: Plan disposition
- [ ] Step 16: Report completion

**If you find yourself thinking "the changes are internal, I'll skip Step 6" --
STOP. That rationalization is what this checklist exists to prevent. Every
plan that shipped code, config, workflows, or scripts is a candidate for
CLAUDE.md update. Default to updating. Only skip if you can explicitly
articulate why there is literally nothing a future session would want to
know about the work. Err on the side of updating.**

---

## Step Marking Format

Mark completed steps by changing `[n]` (or `[ ]`) to `[x]` and appending a timestamp:

```markdown
### [n] Step 3: Add validation                           (before)
### [x] Step 3: Add validation {2026-04-10T03:21:38}    (after)
```

**Rules:**
- Change bracket marker from `[n]` or `[ ]` to `[x]`
- Append `{YYYY-MM-DDTHH:MM:SS}` timestamp (run `date -u` — never guess)
- Never remove step content — keep the description for reference
- Add a `**Results:**` block immediately after the step content

---

## Queue File Management

The queue file `plans/.step-queue.json` (or `.stepN-queue.json` for parallel queues) tracks active plans across `/clear` sessions.

**Structure:**
```json
{
  "active_plan": "plans/current-plan.md",
  "queue": ["plans/current-plan.md"]
}
```

Per-step progress is tracked in the plan file itself (via `[x]` markers and `{timestamp}` suffixes) — the queue file only holds the active-plan pointer.

**When plan completes:**
- Set `active_plan` to `null`
- Remove from `queue` array

---

## Plan Completion Workflow

When all steps are marked `[x]`, execute this seven-step workflow:

### 2. Read Current Documentation

```bash
cat .claude/CLAUDE.md 2>/dev/null
```

Understand what's already documented before making updates.

### 4. Pre-Close Audit (LANDMINEs + open-state markers)

**Why this step exists:** Three classes of deferred obligation can survive to plan close. All three get orphaned silently without an audit:

- **Open LANDMINEs** -- annotations in completed-step Results blocks flagging known issues deferred for later fix. `/step` greps the live plan on every invocation (see `.claude/commands/step.md` Phase B), but archive plans aren't re-grepped, templated plans carry stale warnings, deleted plans lose them.
- **`[w]` waiting steps** -- blocked on an external person/event. The completion gate treats only `[x]` and `[~]` as done, so `[w]` blocks plan close. The wait may have resolved silently, may no longer be needed, or may deserve a followup plan.
- **`[!]` stuck steps** -- flagged as needing intervention. Same completion-gate block. Same disposition question: fix, supersede, or defer.

**`[~]` is NOT audited** -- it equals `[x]` for completion purposes (plan pivoted, step intentionally skipped).

**Procedure:**

1. **Scan the plan for all three categories:**

   ```
   Grep pattern="LANDMINE" path=[plan_path] -n -A 1             # exclude LANDMINE[resolved]
   Grep pattern="^### \[w\]|^\(w\)|^<w>" path=[plan_path] -n    # waiting (all three tiers)
   Grep pattern="^### \[!\]|^\(!\)|^<!>" path=[plan_path] -n    # stuck (all three tiers)
   ```

2. **If zero items across all categories:** report "Audit clean -- no open LANDMINEs, no `[w]` waiting, no `[!]` stuck steps." and proceed to Step 6.

3. **If any are found:** display a unified, categorized list:

   ```
   Pre-close audit: N items need disposition

   --- Open LANDMINEs (M) ---
   1. Step 4 (line 127): [LANDMINE text, up to ~120 chars]
   2. Step 7 (line 203): [text]

   --- Waiting steps [w] (P) ---
   3. Step 6: Wait for Teresa's schema approval

   --- Stuck steps [!] (Q) ---
   4. Step 9: Cron not firing -- needs DBA intervention
   ```

4. **Ask the user for a per-item disposition.** Options differ by category: LANDMINEs are text annotations (don't block the completion gate), while `[w]` and `[!]` are step markers (do block).

   **For LANDMINEs -- four options:**
   - **[A] Resolve via `/question-loop`** (per-item). Invoke with the LANDMINE text + full Results-block bullet it lived in + framing question. Loop ends with one of: *Fix now* (edit code, change prefix to `LANDMINE[resolved]:`) / *Silence as resolved* (prefix change + one-line reason) / *Lift to CLAUDE.md* (promote to durable constraint -- informs Step 6; mark source `LANDMINE[resolved]: -> see CLAUDE.md § [section]`).
   - **[B] Defer to NEW followup plan via `/plan-creation`** -- hand-off payload per LANDMINE: source plan path + step number, full Results bullet (origin context), LANDMINE text as step title, pre-seeded `Context:` line with files named in the Results block. Filename: `plans/[source-slug]-followup.md`. Mark source `LANDMINE[resolved]: -> see plans/[source-slug]-followup.md`.
   - **[C] Defer to EXISTING plan** -- user names which. Append as new step with same hand-off payload. Mark source `LANDMINE[resolved]:` with pointer.
   - **[D] Accept as-is** -- warn of consequence based on Step 14 disposition: *Archive* fossilizes, *Template* should strip, *Delete* loses. Require explicit acknowledgment.

   **For `[w]` waiting -- three options (no accept-as-is; `[w]` blocks the completion gate):**
   - **[A] Resolve via `/question-loop`** -- loop reads the step body (what it's waiting on) and asks whether the wait resolved. Ends with: *Wait resolved* (mark source `[x]` with `{timestamp}`, add short note to Results about how it resolved) / *No longer needed* (mark source `[~]` -- keep full step body, pivot history is the value) / *Still waiting, no ETA* (branch to [B] or [C]).
   - **[B] Defer to NEW followup plan** -- hand-off payload: source plan path + step number, full step description, original waiting-on detail, pre-seeded `Context:`. Mark source `[~]` with `-> see plans/[source-slug]-followup.md` appended to step body.
   - **[C] Defer to EXISTING plan** -- append as new step with same payload. Mark source `[~]` with pointer.

   **For `[!]` stuck -- three options (no accept-as-is; `[!]` blocks the completion gate):**
   - **[A] Resolve via `/question-loop`** -- loop surfaces the blocker, attempted approaches, and the failure annotation below the source step. Ends with: *Unblock now* (attempt fix, mark `[x]` on success) / *Redirect approach* (rewrite step text, retry, `[x]`) / *Can't be done* (mark `[~]` with failure annotation preserved).
   - **[B] Defer to NEW followup plan** -- hand-off payload MUST include the full stuck-reason annotation and attempted approaches; the followup plan needs to know what's already been tried. Mark source `[~]` with pointer.
   - **[C] Defer to EXISTING plan** -- same as above.

5. **After resolution:** the plan file has edits (silenced LANDMINEs, `[w]`/`[!]` converted to `[x]`/`[~]` with notes, possibly fix-code diffs in other files). Stage them for the Step 8 commit. If [B] created a followup plan file, stage that too. If [A] lifted a LANDMINE to CLAUDE.md, Step 6 handles the CLAUDE.md edit in the same commit.

**Hard rule:** do not proceed to Step 6 until every item is dispositioned. The completion gate rejects the plan if any `[w]` or `[!]` marker remains -- the audit must convert them to `[x]` or `[~]`.

---

### 6. Update CLAUDE.md -- MANDATORY

**THIS STEP IS MANDATORY. DO NOT SKIP IT.** Claude has historically skipped
this step under the excuse "the changes are internal." That rationalization
is forbidden. If the plan touched code, data schemas, scripts, or workflows,
there is something a future session needs to know.

**Which CLAUDE.md?** There are two levels:

1. **Project-level CLAUDE.md** at `<project>/.claude/CLAUDE.md` (e.g.,
   `<project>/.claude/CLAUDE.md`). This is the PRIMARY target for any
   plan whose work lives inside a specific project. Almost every plan
   should update its project-level CLAUDE.md.

2. **Root CLAUDE.md** at `.claude/CLAUDE.md` (the claude root). Only update
   this for changes that affect GLOBAL best practices, cross-project skills,
   or tooling conventions that apply everywhere.

**Default:** update the project-level CLAUDE.md. Only touch the root CLAUDE.md
if the work is explicitly global in scope.

**If a project-level CLAUDE.md does not exist:** CREATE one as part of this
step. Absence is NOT an escape hatch to only update the root CLAUDE.md.
Populate the new file with what future sessions working inside this project
need to know: what the directory is, core invariants, sync/relationship
notes with sibling directories, hard rules for files inside, local-only vs
shipped distinctions. This applies even when the project is gitignored
from a parent repo — the project-level CLAUDE.md is for local dev context,
not for shipping. Gitignore the new CLAUDE.md if appropriate; do not skip
creating it.

**What to update (pick all that apply):**

- **Common Commands section** — new user-facing scripts or commands
- **Status line** — if the project's status changed meaningfully
- **Where to Look table** — new important files or directories
- **Hard Constraints section** — new rules future sessions must not violate
  (e.g., "never bypass the X check without understanding Y", "always use Z
  for W", "Z function is the canonical source for X")
- **"Currently Available Skills" section** if new skill created (root CLAUDE.md)
- **"Session Workflow Commands" section** if new slash command created
- **Architecture/features sections** if any were introduced or substantially changed

**The "skip if internal only" clause is GONE.** It was being abused. If a
plan shipped work, that work taught you something. Write it down. Future
sessions will read it.

**Acceptable reasons to skip Step 6 (rare):**

- The plan produced zero new files and modified zero files (pure research
  plan that only added markdown notes)
- The plan's entire output was already documented in CLAUDE.md before the
  plan ran (e.g., a plan that "completes" an already-documented TODO)

**Unacceptable reasons to skip Step 6:**

- "The changes are internal" -- constraints and invariants are the MOST
  important thing to document for future sessions
- "The code is self-documenting" -- future you reads CLAUDE.md first
- "I'll add it to a future plan" -- that plan will never exist
- "The project doesn't have a CLAUDE.md yet" -- absence means you CREATE it
  during this step, not skip. Update-or-create, never just skip
- "The git history has it" -- nobody reads git history to learn a project

### 8. Git Commit and Push

**CRITICAL: Surgical commits only.** The working tree often has uncommitted changes from other sessions/plans. Never use `git add -A` or `git add .`.

**Build the file list from the plan's Results blocks:**
1. Read all `**Results:**` sections in the plan file
2. Extract every file path mentioned (created, modified, normalized, etc.)
3. Also include: the plan file itself, its queue file, any doc files updated in step 6, and any followup plan file created in step 4
4. Stage ONLY those files: `git add [file1] [file2] ...`
5. Run `git status --short` to verify — every staged file should trace back to a plan step
6. If anything unexpected is staged (from a prior session's `git add`), unstage it: `git reset HEAD [file]`

```bash
# Stage only files this plan touched
git add plans/[plan-name].md plans/.[queue]-queue.json [files from Results blocks]
git status --short
git commit -m "$(cat <<'EOF'
chore: complete [plan-name] plan (N/N steps)

- Key change 1
- Key change 2

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

**Commit message format:**
- Type: `feat`, `fix`, `docs`, `refactor`, `chore`
- Scope: Component or area affected
- Description: What changed and why

### 10. Run Completion Ritual (Eulogy + Status Transition)

Run the ritual inline -- no external script. Four sub-steps: verify, eulogy, status transition, queue cleanup. Then a final commit/push.

#### 10b. Verify Completion

Re-read the plan file. Confirm:
- YAML frontmatter parses (between the top `---` markers)
- Every step header's marker is `x` or `~` (top-level `[x]`/`[~]`, sub-step `(x)`/`(~)`, sub-sub-step `<x>`/`<~>`). `[~]` (superseded) counts as done -- the plan pivoted and intentionally skipped it.
- Count total vs. completed. If any step is not `[x]` or `[~]`, STOP and tell the user the plan is not complete.

#### 10d. Write the Eulogy

Claude writes the eulogy directly -- no API call, no external script, no `ANTHROPIC_API_KEY` requirement. You're already running inside Claude Code; the intelligence is already here.

Gather project context using your normal tools:
- **Project name:** from the plan's `project:` frontmatter field (fallback: plan filename without `.md`)
- **README excerpt:** read `<project>/README.md` (or `readme.md`) with `encoding='utf-8'`, first ~2000 chars; empty string if missing
- **Python file count:** Glob `<project>/**/*.py` or `len(list(Path('<project>').rglob('*.py')))`; 0 if project dir missing
- **Recent git activity:** `git log --oneline -15 -- <project>/` (empty string on error)

Then write the eulogy following the style guide below. Display the finished text in your response so the user sees it, then append it to `.claude/hall-of-heroes.md`.

**Style guide (match this tone):**

- Start with `##` heading -- the project/plan name
- Tagline in quotes under the heading (`###` subheading)
- 2-4 short paragraphs, each starting with a DIFFERENT emoji shortcode from: `:fire: :skull: :guitar: :gem: :lightning: :wrench: :bullseye: :dice: :brain: :muscle: :sparkles: :boxing_glove: :rocket: :eyes: :palette:`
- Be specific about what was actually built -- cite real features, file counts, tools used
- Humor, personality, profanity welcome -- not corporate speak
- End with a brief stats line in bold
- End the whole entry with a horizontal rule: `---`
- ASCII text only -- spell out emoji names using colon shortcodes like `:fire: :skull: :guitar:`. Do NOT emit unicode emoji characters.

Tone is CELEBRATORY: this plan actually finished, shipped, done. Be specific about what was built, acknowledge the grind, don't be a sanitized robot.

Length: 2-4 paragraphs (shorter for smaller projects, longer for big ones). Do NOT wrap the output in markdown code fences -- output raw markdown starting with the `##` heading.

**Append to `.claude/hall-of-heroes.md`:**
- If file exists: load with `encoding='utf-8'`, ensure trailing newline, append `\n\n<eulogy>\n`.
- If file missing: create `.claude/` dir if needed, then write `# Hall of Heroes\n\n---\n\n<eulogy>\n`.
- All writes: `encoding='utf-8'`.

**Escape hatch (optional, advanced):** if a user wants eulogies produced by a specific model (e.g. Sonnet 4.6 via the Anthropic SDK instead of the Claude Code runtime), they can customize this skill locally to call the API. Default behavior stays: Claude writes it inline, zero setup.

#### 10f. Transition Plan Status

Edit the plan's YAML frontmatter: change `status: in_progress` -> `status: reference`. Preserve all other frontmatter fields verbatim; preserve the plan body exactly.

Use atomic write: write new content to `<plan>.md.tmp`, then `os.replace(tmp, plan)`. Do NOT use PyYAML round-trip -- it reformats comments and reorders keys. Surgery on the raw text between the two `---` markers is safer.

#### 10h. Clear Plan From Queue Files

Scan every file matching `plans/.step*-queue.json` (including `plans/.step-queue.json`). For each: if `active_plan == "plans/<plan-filename>"` OR `"plans/<plan-filename>"` is in the `queue` array, overwrite the file with `{"active_plan": null, "queue": []}` (trailing newline, indent=2). Report which queue files were cleared.

#### 10j. Commit Ritual Changes

After the ritual succeeds, commit the affected files:

```bash
git add .claude/hall-of-heroes.md plans/[plan-name].md plans/.step*-queue.json
git commit -m "chore: Hall of Heroes eulogy for [plan-name]"
git push
```

### 12. Summary + Follow-Up Prompt

**This step fires BEFORE disposition.** The follow-up prompt is forward-looking ("what does this work enable next?") and disposition is backward-looking ("file this away"). Running forward-first lets the user's follow-up answer inform how they want the plan file treated.

1. **Summarize what was built** — Table showing components created, their locations, and purpose.

2. **Provide actionable next steps** — How to use what was built:
   - Commands to run (with full syntax)
   - Files to review
   - Follow-up actions needed
   - Optional enhancements or future work

3. **Ask about follow-up work.** **Generate the menu AT CLOSE TIME** from what the plan actually produced — do NOT paste a static template.

   **Opener (verbatim):**

   Plan's in the can. Before the result starts collecting dust in the corner, should we...

   **Generation rubric.** Read the Results blocks of every `[x]` step in the closing plan. For each category below, pick the *highest-abstraction, highest-leverage* follow-up you can justify from what the plan built. Each option gets ONE sentence (the pitch, specific to this plan's output) + an optional second line (justification or tool/file reference). If no reasonable candidate surfaces for a category, omit that letter entirely.

   (a) New follow-up plan — biggest unfinished thread, worthy of its own multi-step plan.
       → /plan-creation (optionally /question-loop first if fuzzy)

   (b) Local scheduled job — recurring script on user's machine that keeps today's work honest or extends it.
       → Windows Task Scheduler (`schtasks`) or macOS/Linux cron

   (c) Claude Code recurring agent — /loop (in-session) or /schedule (remote cron) that revisits the plan's output on a cadence.
       → /loop or /schedule (ask which fits)

   (d) Parking-lot reminder — time-delayed check ("in 2 weeks re-read X", "next month verify Y") not worth a plan slot yet.
       → append to plans/followups-parking-lot.md (create file if missing)

   (e) Dogfood one small thing now — <5-minute action leveraging today's work (skeleton file, quick doc tweak, running the feature once end-to-end).
       → execute inline; no scheduling or plan creation

   (x) Brainstorm — none of the above quite fits; open conversation.
       → chat only, no tool invocation

   (q) Done — clean close, file it away.
       → exit skill normally

   **Routing on selection.** Execute the arrow action for the chosen letter. For (a) confirm whether user wants /question-loop first. For (c) ask /loop vs /schedule. For (d) confirm one-liner wording before appending. "No" / "q" / any "we're done" variant is always valid — don't push.

   **Key principle:** the menu is generated per-plan, not pasted. Generic pitches are a smell — if all five options read like they'd apply to any plan, re-read the Results blocks and find the plan-specific thread.

**Key principle:** The plan created infrastructure — now help the user extract value from it BEFORE filing the plan away.

### 14. Plan Disposition -- Template, Archive, or Delete

**Pre-disposition Context: audit (skip only if disposition is delete).** Before templating or archiving, scan ALL `Context:` lines in the plan -- pending, current, AND completed steps -- for plan-hygiene bugs:

- Directory references (path ends in `/` or has no file extension)
- Vague non-file references ("all X files", "output from Step Y", "reviewed worldbuild")
- Single files >25K tokens with no line range or section anchor

If any are found, surface them to the user with proposed fixes (move to `Script input:` / `Grep targets:`, narrow to specific files, add line ranges) BEFORE locking the plan in for posterity. Templates and archives inherit Context: line bugs forever -- a directory bomb in a templated plan becomes a directory bomb in every plan spawned from that template. Disposition is the last line of defense. Canonical rule: CLAUDE.md § Step Context Hints "Phase C is code, not Claude."

Ask the user what to do with the plan file. Present three options with cases for each:

**Template** -- Would this plan's step structure be useful for a different project?
- Copy to `plans/templates/` and generalize (replace project-specific details with `{{PLACEHOLDERS}}`, strip Results blocks, add inline gotcha warnings)
- Good for: rename migrations, cleanup sweeps, pipeline builds -- anything you'd do again with different inputs

**Archive** -- Was this hard-won architectural work worth keeping for reference?
- Move to `plans/archive/`
- Good for: complex multi-plan sagas (like the GTD intelligence layer trilogy), novel system builds where the design rationale matters

**Delete** -- Did the plan's value get fully captured elsewhere?
- Delete the file entirely
- Good for: one-off migrations where a skill already captures the patterns, audit passes that produced a lasting artifact, mechanical bulk edits

**Process:** Present the three options with a one-sentence case for each, tailored to the specific plan. Let the user decide. Execute their choice.

**If Template:** After copying to `plans/templates/`, the plan should be generalized in a follow-up step or session. Two template archetypes exist:
- **Parameterized runbook** (like `project-rename.md`) -- all variables known upfront, deterministic steps
- **Discovery-first protocol** (like `project-cleanup-post-refactor.md`) -- Step 1 discovers scope, downstream steps consume its output

These archetypes were designed via Council deliberation (architecture triad: Aristotle, Ada, Feynman). Key structural patterns:
- Variable declaration header with boolean flags for conditional steps
- Steps tagged as `[REQUIRED]`, `[CONDITIONAL: variable]`, or `[JUDGMENT-GATE]`
- Empty schema tables (column headers, no pre-filled data)
- Results blocks stripped; replaced with inline `(!) Gotcha:` warnings mined from the original
- Entry/exit criteria per step

**If Archive or Delete:** Execute immediately and commit.

### 16. Report Completion

After successful ritual and disposition, report status:

```
Plan complete! All steps done.

Changes committed and pushed to remote.
Hall of Heroes eulogy generated and saved.
Plan disposition: [template / archive / deleted]
```

---

## Partial Completion Handling

If plan is NOT fully complete:

1. **Keep the plan file** - Don't delete or modify structure
2. **Note what's pending** - List remaining steps
3. **Stop and wait** - Don't attempt to continue without instruction
4. **Leave queue alone** - Don't clear `active_plan`; the plan is still in progress

Example response:
```
📋 Plan Status: 7/9 steps complete

Remaining:
- Step 8: Write integration tests
- Step 9: Update deployment config

To continue: /step
```

---

## Error Recovery

**If git push fails:**
1. Check for conflicts: `git status`
2. If behind remote: `git pull --rebase && git push`
3. If conflicts exist: Stop and ask user for guidance

**If step was marked done incorrectly:**
1. Edit the plan file: change `[x]` back to `[n]` and remove the `{timestamp}` suffix
2. Move the `[n]` marker back to that step (remove it from wherever it currently is)
3. Re-run `/step` to retry

**If queue file is corrupted:**
1. Delete `plans/.step-queue.json`
2. Run `/step plans/[plan-name].md` to reinitialize
