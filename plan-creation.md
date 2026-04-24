---
name: plan-creation
description: Creating implementation plans for multi-step tasks. Use when user asks to plan a feature, create a plan file, or break down a complex task into steps.
triggers:
  - create a plan
  - make a plan
  - plan this
  - implementation plan
  - break this down
  - step by step plan
  - plan file
  - plans
---

# Plan Creation Skill

Guidelines for creating structured, actionable implementation plans stored in `plans/`.

---

## Quick Reference

| Element | Format |
|---------|--------|
| Location | `plans/plan-name.md` |
| Naming | Three descriptive words: `company-research-engine.md` |
| Frontmatter | YAML block with project, status, type, description, priority, created |
| Sections | Goal, Current State, Constraints, Steps, Files to Modify, Success Criteria |
| Step format | `### [ ] Step N: Title` with inline marker |
| Completion marker | `### [x] Step N: Title` |
| Numbering | Sparse (gaps between numbers for future insertions) |

---

## File Location

**Plan files MUST live in `plans/` at the project root, as a SIBLING of `.claude/` — never inside it.**

```
your-project/
├── .claude/              <-- Claude's config
└── plans/                <-- plans go here (sibling, not child)
    └── your-plan.md
```

**Never write plans to any of these:**
- `.claude/plans/` — breaks discovery AND edits (see foot-gun below)
- `~/.claude/plans/` — user home directory, invisible to slash commands
- `C:\Users\username\.claude\plans\` — Windows form, same problem
- Any other location

**Why `.claude/plans/` is a specific foot-gun:**
1. Slash commands look for `plans/` at project root. A plan inside `.claude/` is invisible to `/step`, `/plan-creation`, and `/plan-completion`.
2. Claude Code's bypass-permissions mode explicitly excludes `.claude/` as a safety rail. Every Edit/Write to a plan inside there triggers a permission prompt — even in yolo mode.

This keeps plans version-controlled with the project, discoverable by the slash commands, and editable without permission friction.

---

## File Naming

**Use descriptive three-word names that explain the plan's purpose:**

| Good | Bad |
|------|-----|
| `company-research-engine.md` | `moonlit-drifting-zephyr.md` |
| `transcript-format-cleanup.md` | `glittery-cooking-beaver.md` |
| `sales-call-intelligence.md` | `plan-v2-final.md` |
| `history-pattern-analysis.md` | `my-plan.md` |

Names should describe what the plan does at a glance.

---

## Plan Structure

### Required Sections

```markdown
---
project: project-name
status: in_progress
type: business
description: "One-line description of what this plan does"
priority: 99
created: 2026-03-24
---
# Plan: [Descriptive Title]

## Goal

One sentence describing what this plan accomplishes.
Why are we doing this? What problem does it solve?

---

## Current State

What exists now? What's the starting point?
- Existing files, databases, or systems
- Dependencies already in place
- Constraints or limitations

---

## Implementation Steps

**Build order:** 1 -> 2 -> 3 -> ... (add when execution order differs from numbering)

### [ ] Step 2: [First action]

Description of what to do.
- Specific sub-tasks
- Expected output
- How to verify completion

Context: file.py:10-50 (relevant function), README.md:## Section
Skills: skill-name-if-needed
Mode: 2 (create)

### [ ] Step 4: [Second action]

...continue with sparse numbering (gaps for future insertions)...

---

## Files to Modify

| File | Purpose |
|------|---------|
| `path/to/file.py` | Brief description (new or modified) |
| `path/to/config.yaml` | Brief description (new or modified) |

---

## Constraints & Edge Cases

What NOT to do, and what could go wrong:
- Scope boundaries (what's explicitly out of scope)
- Platform quirks (Windows encoding, path separators, etc.)
- API limits or rate constraints
- Files/systems that must NOT be modified
- Known failure modes to handle

---

## Success Criteria

1. Measurable outcome #1
2. Measurable outcome #2
3. All findings backed by evidence
```

### Optional Sections

```markdown
## Architecture Decisions

Key technical choices and why they were made.

---

## Test Results

Document actual results as steps complete.

---

## Known Issues

Problems discovered during implementation.

---

## Next Steps

What comes after this plan completes.
```

---

## Step Format

### Writing Steps for Agent Execution

Three rules that measurably improve how agents follow plan steps:

1. **Capitalize step instructions** — "Run the experiment", not "run the experiment". Each step reads as a command, not a description. Cleaner parsing, more reliable compliance across steps.

2. **Use calm imperatives, not emphatic language** — "Run X" not "You MUST run X". Words like "MUST" and "actually" cause the agent to over-commit to that step at the expense of the broader loop. Flat, uniform tone keeps all steps at equal priority.

3. **Include exit ramps for risky steps** — "If X fails after 2-3 attempts, give up and move on." Without an explicit bail-out condition, agents thrash indefinitely on hard failures, making increasingly desperate changes that compound damage. A failed step that gets abandoned is better than a "fix" that corrupts the run.

### Context/Skills/Mode Hints

Each step can include three optional lines beneath the description to guide `/step` execution:

```markdown
### [ ] Step 5: Implement rate limiter refactor

Refactor the rate limiter to support triple-bucket throttling.

Context: rate_limiter.py:45-120 (DualRateLimiter class), README.md:## Architecture
Skills: your-skill-name
Mode: 5 (refactor)
```

- **Context:** File paths Claude Code itself needs to read and reason about. Phase C pre-loads every path here (50K token budget). Line ranges, section headers, and role annotations are encouraged.
- **Script input:** Files a script will stream to an external API (Opus bundles, training corpora, source material for LLM distillation). Listed on a separate line so Phase C doesn't pre-load them. Format: `Script input (DO NOT pre-load — stream to <API> via script): path/to/bundle.md (size)`.
- **Grep targets:** Large file sets the step searches via Glob/Grep at execution time, not via Read at Phase C. Format: `Grep targets (DO NOT pre-load — N files, ~XK tokens; use Glob/Grep): dir/ (narrowing rule)`. Use when a step touches "specific entities cited later" within a directory of dozens of files.
- **Skills:** Skill names from the routing table that this step needs. Uses "invoke [skill-name] skill" language.
- **Mode:** Suggested mode (1=review, 2=create, 3=test, 4=fix, 5=refactor).
- **Design:** Path to a design doc or section that contains the step's implementation spec. When a step requires schema decisions, mechanism trade-offs, or multi-paragraph specs, write them to a design doc in `docs/` and point to it here -- do NOT inline them in the step body. The step body should say WHAT and WHY in 3-8 lines; the design doc says HOW.

**The larger principle: Phase C is code, not Claude.** Phase C reads `Context:` paths literally — it cannot walk directories, resolve "all X files" or "output from Step Y", skip oversized files, or decide a path is for searching. Relevance is NOT the test. The test is: would `Read [path]` succeed in <10K tokens AND does Claude Code itself need to reason about it?

**Pre-flight gates before adding a path to `Context:`** (all must pass):

1. **Single file** — not a directory, glob, or "all X" reference
2. **Specific** — line range or section anchor when content >10K tokens
3. **Under budget** — the path's size + already-loaded Context wouldn't bust 50K
4. **For Claude** — Claude Code itself needs to reason about it (not a downstream script, not a Grep call)

If ANY fails, route elsewhere: API-bound files → `Script input:`; large directories searched at execution → `Grep targets:`; skill names → `Skills:`; nothing actually needed → delete. Vague references ("all canon files", "reviewed output from Step 6") always fail gates 1-2 and signal handwave thinking that hides a directory bomb. Canonical: CLAUDE.md § Step Context Hints.

### Sub-sub-steps inherit nothing — give each one its own Context

When a step has nested `<x>` / `< >` children (or `(x)` / `( )` sub-steps), Phase C reads the ACTIVE sub-sub-step's `Context:` — NOT the parent's. A parent-level kitchen-sink `Context:` is effectively dead weight once execution drops into children, because `/step` loads only the `<n>`-marked step's own Context.

**Wrong (parent-level blob, children have none):**

```markdown
( ) Step 6g: Apply minor enhancement fixes (12 sub-sub-steps)

Context: docs/review/q2.md, q3.md, q4.md, q5.md, q12.md, q13.md, q14.md (per-sub-step Phase C should narrow to the 1-2 q-files cited)
Grep targets: world_bible/ (all subdirs)
Mode: 4 (fix)

< > Step 6g4: Metaphor variation (Q4 M10)
[no Context line]

< > Step 6g6: Peripheral character grounding (Q2)
[no Context line]
```

Phase C cannot narrow 7 blob files down to "the 1-2 cited by this sub-step" — it reads paths literally (CLAUDE.md § "Phase C is code, not Claude"). When `<n>` is on 6g4, Phase C loads nothing step-specific. The executor then spends 30-60s run-time grepping for the evidence a tighter Context would have surfaced in the pre-load.

**Right (per-sub-step Contexts, shared doc stays on parent):**

```markdown
( ) Step 6g: Apply minor enhancement fixes

Context: docs/worldbuilding-best-practices.md:### 3.1 (sensory-first principle -- shared register reference)
Per-sub-step Contexts: each <x>/< > child carries its own narrowed Context. Phase C loads the active sub-sub-step's Context only; parent Context is not inherited.
Mode: 4 (fix)

<n> Step 6g4: Metaphor variation (Q4 M10)
Context: docs/review/q4_response.md:59-69 (M10 fix rec), world_bible/seeds/seed_5.md:17-21, world_bible/seeds/seed_14.md:10-21

< > Step 6g6: Peripheral character grounding (Q2)
Context: docs/review/q2_response.md:21-33 (Tarvashi), docs/review/q2_response.md:107-117 (Shidani), world_bible/seeds/seed_8.md, world_bible/hard_power_players/hpp_5.md
```

Each child's Context names the specific review-file lines + entity files IT touches. Phase C pre-loads surgically. Parent keeps only truly shared references (a schema doc, a principles file) every child would consult.

**Rule:** If you find yourself writing a parent-level `Context:` that says "narrow per sub-step" / "per-sub-step Phase C should narrow" OR lists 3+ review / audit / response files as a blob, stop. Push each file-list down into the individual child's Context. Parent keeps only what every child legitimately needs.

**Why this matters operationally.** `/step` Phase C flags this pattern at execution time and offers to author the missing child Context before running. Catching it at plan-authoring is cheaper — you know the fix for each child because you're actively decomposing the work. Catching it later means the executor has to reverse-engineer which evidence each child needs from a flat list.

**When to add hints:** For steps 1-6 (concrete, well-understood), include Context/Skills/Mode at plan-writing time. For steps 7-12 (fuzzy, exploratory), omit -- they'll be refined when you reach them. Curated context beats runtime guessing -- saves 30-60s of exploration overhead per session.

### Pending Step Size Limit

**Hard cap: 10 lines max for a pending step body** (excluding the header and Context/Skills/Mode/Design hint lines).

A pending step body should contain:
- 1-2 sentences: what this step does and why
- 1-2 sentences: key constraint or gating condition (if any)
- 0-1 sentence: what artifact it produces

If the step needs SQL schemas, mechanism options, interaction analyses, UX copy, or multi-paragraph specs, those belong in a design doc (pointed to via `Design:` line), NOT inline in the step body.

**The "independently executable" test is:** "Can a fresh `/step` session find everything it needs within the Context + Design file reads?" NOT "Can it execute without reading any other file?"

### Good Step Descriptions

```markdown
### [ ] Step 3: Build conversation flow analyzer

Create Python script to:
- Group prompts by session_id
- Identify conversation patterns (what comes after what)
- Find common session starters and enders
- Calculate session duration and prompt cadence

**Output:** `.claude/history-analysis/analyze_sessions.py`
```

### Step Granularity & Sizing

**One step = one discrete task:**
- ✅ Create ONE script and test it
- ✅ Update ONE configuration file
- ✅ Run ONE test suite
- ❌ Create 3 related scripts (should be 3 steps)
- ❌ "Finish the feature" (too vague)

### Step Markers (Three Tiers)

Steps use inline markers to track status. Three nesting tiers:

| Tier | Format | Done | Open | Next | Waiting | Stuck |
|------|--------|------|------|------|---------|-------|
| Numbered steps | `### [x] Step 2: Title` | `[x]` | `[ ]` | `[n]` | `[w]` | `[!]` |
| Lettered sub-steps | `(x) Step 2b: Title` | `(x)` | `( )` | `(n)` | `(w)` | `(!)` |
| Sub-sub-steps | `<x> Step 2b2: Title` | `<x>` | `< >` | `<n>` | `<w>` | `<!>` |

**Rules:**
- Exactly ONE `[n]`/`(n)`/`<n>` across all tiers in a plan = the single next action
- Parent flips to done when ALL children are done (e.g., Step 7 becomes `[x]` when 7a, 7b, 7c are all `(x)`)
- `[w]` = waiting on external dependency (person/event), NOT sequential task ordering
- `[!]` = stuck, needs intervention -- add failure annotation below the step

**Marking completion:** Change `[ ]` to `[x]`, strip the original description, and add a Results block:

```markdown
### [x] Step 3: Build conversation flow analyzer {2026-03-24T14:30:00}

**Results:**
- Created `analyze_sessions.py` (150 LOC)
- Processed 3,400 sessions successfully
```

**On completion, strip everything between the step header and `**Results:**`.** The Results block IS the record. The original description served its purpose -- the code and the Results block are now the source of truth. Keeping dead descriptions is the #1 cause of plan file bloat.

**Exception:** The `[~]` (superseded) marker means the step was NOT executed. Superseded steps keep their full description because the "why we pivoted" narrative IS their value.

---

## Skill Invocation in Steps

When a step requires a skill's methodology (any skill defined in your `.claude/skills/` directory), use explicit invocation language:

| Step Text (won't trigger skill) | Step Text (will trigger skill) |
|---------------------------------|--------------------------------|
| "Brainstorm X" | "Invoke brainstorm skill to explore X" |
| "Use the research skill for Y" | "Invoke research skill to gather Y" |
| "Follow the config pattern" | "Invoke api-config skill to set up API config" |

**Why this matters:** Skills trigger on user prompts, not plan file content. When `/step` executes a plan, the step text is read by Claude—so "invoke [skill-name] skill" signals to load and follow that skill's pattern.

**Rule:** Always write: `"Invoke [skill-name] skill to [action]"` when a step needs a skill's methodology.

---

## Step Count Guidelines

| Plan Complexity | Typical Steps |
|-----------------|---------------|
| Simple feature | 3-5 steps |
| Medium feature | 5-10 steps |
| Complex system | 10-15 steps |
| Major refactor | 15-25 steps |

**If a plan exceeds 25 steps**, consider splitting into multiple plans.

### Sparse Numbering

Number steps and sub-steps with gaps so new items can be inserted without renumbering everything downstream. This matters during `/step` execution when a step proves larger than expected.

**Starting points and gap sizes** — gaps leave one slot open before the first and between every adjacent pair:
- **Top-level:** start at 2, gap of 2 → (2, 4, 6)
- **Sub-steps:** start at b, gap of 2 letters → (3b, 3d, 3f)
- **Sub-sub-steps:** start at 2, gap of 2 → (3b2, 3b4, 3b6)

```markdown
### [ ] Step 2: Setup
### [ ] Step 4: Core logic
### [ ] Step 6: Integration
### [ ] Step 8: Testing
```

**Why:** Plans evolve during execution. Step 4b reveals a prep step needed before 4d. With gap-of-2 numbering, insert `( ) Step 4c:` — exactly one slot open between any two adjacent items.

### Build Order Annotation

When execution order differs from step numbering (due to insertions or dependency chains), add a build order line at the top of Implementation Steps:

```markdown
## Implementation Steps

**Build order:** 1 -> 3 -> 5 -> 4 -> 8 -> 6 -> 10
```

This makes the dependency chain explicit. Skip this for simple plans where numbering = execution order.

---

## Pre-Planning Phase

**The 4x efficiency gain comes from planning WITH the agent, not just writing a plan file.**

Before creating any plan file, spend 10-15 minutes in interactive discussion:

### 1. Read the relevant code first

Don't plan based on assumptions. Before writing a single step:
- Read the files you'll be modifying
- Check existing patterns in the codebase
- Look for related implementations you can build on
- Identify dependencies and integration points

**Rule:** If you haven't read the code, you're guessing. Plans based on guesses create intervention-heavy sessions.

### 2. Discuss the approach interactively

Discuss the approach one question at a time (invoke a question-loop-style skill if you have one, otherwise just walk the questions interactively):
- **What's the simplest path?** — Avoid over-engineering from step 1
- **What could go wrong?** — Edge cases, platform quirks, API limits
- **What should we NOT do?** — Constraints, prohibitions, scope boundaries
- **What's the testing strategy?** — How will we verify each step?

### 3. Then write the plan

Only after the conversation produces a clear approach, create the plan file. The file captures the DECISION, not the EXPLORATION.

**Why this matters:** Built-in planning mode generates a plan from a single prompt. Interactive planning surfaces constraints, edge cases, and existing code patterns that the model wouldn't discover on its own. Result: 15-minute autonomous execution vs. 60+ minutes with constant intervention.

---

## Creating a New Plan

### Step-by-Step Process

1. **Read relevant code** - Understand what exists before planning changes

2. **Discuss approach with the agent** - Interactive back-and-forth to surface constraints and edge cases

3. **Check existing plans** - Look at `plans/` for similar plans to use as templates

4. **Create the file:**
   ```bash
   # Create the plan file
   touch plans/descriptive-plan-name.md
   ```

5. **Write the structure** - Use the template above (include Constraints section)

6. **Define clear steps** - Each step should be independently executable

7. **Add success criteria** - How will we know when we're done?

8. **Prepend the auto-inserted Step 0 Gap Analysis block** — after the plan body is written but before finalizing, paste the `Step 0 template` from `## Step 0: Auto-Inserted Gap Analysis` (below) at the TOP of Implementation Steps. Step 0 carries the `[n]` marker; Step 2 onward stays `[ ]`. Step 0 fills the pre-slot the sparse-numbering convention already reserves — the "start at 2" rule leaves slot 0 open by design, so Step 0 uses it rather than breaking the rule. The author's plan still starts at Step 2. Mandatory by default; no size gate, no opt-out. Best quality when the reviewer is Opus — if you're on Sonnet or Haiku, consider `/model opus` before the first `/step` run so Step 0's review uses the strongest model.

### Example: Starting a New Plan

```markdown
---
project: my-app
status: in_progress
type: business
description: "Add user authentication with JWT tokens"
priority: 5
created: 2026-03-24
---
# Plan: User Authentication Flow

## Goal

Add secure user authentication with JWT tokens and session management.

---

## Current State

- Express.js backend running
- No authentication currently
- Database ready (PostgreSQL)

---

## Implementation Steps

### [n] Step 0: Gap Analysis — in-session review with /question-loop

Parent step. (b) generate structured review in-session, (d) walk findings via /question-loop. Auto-inserted by /plan-creation; mandatory by default. See the `## Step 0: Auto-Inserted Gap Analysis` section in the skill for the full template.

### [ ] Step 2: Add user model and database migration

Create `models/user.py` with:
- UUID primary key
- email (unique)
- password_hash
- created_at, updated_at

Run migration to create table.

Context: models/base.py (Base model class to extend), docs/development/migrations.md (migration tool conventions)
Mode: 2 (create)

### [ ] Step 4: Implement password hashing

Add bcrypt dependency and create `auth/password.py` with:
- `hash_password(plain_text) -> hash`
- `verify_password(plain_text, hash) -> bool`

### [ ] Step 6: Build registration endpoint

...and so on (sparse numbering, gaps for insertions)...
```

---

## Step 0: Auto-Inserted Gap Analysis

**After writing the plan body but before finalizing, `/plan-creation` auto-inserts a Step 0 at the top of Implementation Steps.** Step 0 runs a two-pass critique of the plan (plus the files the plan modifies, subject to a size budget), then walks the findings via `/question-loop` so accepted ones become plan edits before Step 2 executes. It is mandatory by default — not opt-in, not size-gated. The first `/step` invocation on the generated plan runs Step 0. Every plan gets this.

### Four review dimensions

Every finding is tagged with exactly one of these:

- **Missing steps** — what's assumed but not specified.
- **Underspecified steps** — where the executor would need to make judgment calls or ask clarifying questions.
- **Dependency gaps** — steps that depend on something not produced by a prior step.
- **Likely intervention points** — where a human will need to step in during autonomous execution.

### Two-pass lens coverage

Before emitting the findings list, the reviewer runs two explicit passes:

- **Prompt-craft lens:** wording clarity, option specification, subjective-text approval gates, line-range brittleness, numbering conventions, output-file routing, step-dependency checks.
- **Infrastructure lens:** state preconditions, output file locations, rollback paths, destructive-step ordering, scope-creep traps, parked-state verification.

Both run in a single reviewer session. Prompt-craft catches sloppy instructions; infrastructure catches missing state checks. The pair closes a blind-spot gap either lens alone would leave.

### Per-finding output format

```
**Finding N: <title>**
- Dimension: <Missing step | Underspecified step | Dependency gap | Likely intervention point>
- Severity: <1-10>
- Reason: <one sentence>
- What you noticed: <1-2 sentences of concrete evidence>
- Proposed fix: <one line>
```

A `TOTAL` line at the bottom summarizes severity distribution and severity-7+ count.

### Severity rubric (1-10)

| Score | Label | Action |
|-------|-------|--------|
| **10** | Reactor meltdown — plan premise wrong | **ABORT — re-plan from scratch** |
| **9** | Load-bearing design gap (cascades, needs design decision) | Edit plan pre-execution; user input likely |
| **8** | Step blocker (one step ambiguous enough to fail) | Fix the step body before that step runs |
| **7** | Done-gate gap (feature described as rationale, not bound to output) | Add explicit done-gate item |
| **6** | Pre-execution precondition (documented elsewhere, missing from step body) | Hoist into step body |
| **5** | In-flight patchable (subjective; user-in-loop can redirect at runtime) | Trust user-in-loop, optional pre-fix |
| **4** | Drive-by improvement (real value, not blocking) | Apply if <60s |
| **3** | Forward-looking nit (value lives in future template work) | Note for downstream template |
| **2** | Self-downgraded nit (formatting, line ranges, narrowing) | 10-second fix or skip |
| **1** | Cosmetic nit (zero execution impact) | Skip |

### Severity-forcing self-check (mandatory, critical in-session reviewer)

AFTER emitting the initial findings list, the reviewer re-reads its own list and asks, for every mid-band finding (severity 4-6): *"does this need to be fixed BEFORE Step 2 of the reviewed plan executes, or can it be patched inline during execution?"* Anything that must be fixed pre-execution gets upgraded to severity 7+.

This self-check matters MORE in the public variant than in an API-gated one: the reviewer is the same Claude Code session that just wrote the plan, with no model-change firewall between writer and reviewer. That self-bias shows up as severity undercalling. Treat the self-check as a forcing function with extra weight — err toward upgrade when on the fence.

### Abort threshold

Recommend rerunning `/plan-creation` from scratch (NOT patching via `/question-loop`) if either condition holds after the self-check:

- **Any finding at severity 10** (plan premise wrong), OR
- **Five or more findings at severity 7+** (accumulated blocking work).

Either condition alone aborts.

### Context bundling for Step 0

The reviewer reads the plan file AND the files the plan materially modifies (pulled from the plan's `## Files to Modify` table if present). Size cap: **≤ 400K chars bundled** (Claude Code in-session review window). If the bundle would exceed the cap, drop lowest-priority files first (reference docs before insertion targets). The plan text itself is never dropped.

### Step 0 template — auto-inserted into every generated plan

```markdown
### [n] Step 0: Gap Analysis — in-session review with /question-loop

Parent step. Two sub-steps: (b) generate the structured review in-session, (d) walk findings via /question-loop and apply accepted edits to this plan before Step 2 begins. Abort ramp: if accepted findings at severity 7+ reach 5 during the walk, stop and rerun /plan-creation from scratch.

( ) Step 0b: Generate the structured review in-session

Read this plan and the files it materially modifies (≤ 400K chars total; drop reference docs first if over cap). Review in two explicit passes: (1) prompt-craft lens — wording clarity, option specification, line-range brittleness, output-file routing, step-dependency checks; (2) infrastructure lens — state preconditions, rollback paths, destructive-step ordering, scope-creep traps. Tag each finding with one of four dimensions (Missing step / Underspecified step / Dependency gap / Likely intervention point). Score each finding 1-10 per the severity rubric in the parent skill file. After emitting the initial list, run the severity-forcing self-check on every 4-6 finding: upgrade to 7+ anything that must be fixed pre-execution. Write the findings to `plans/review_{plan-name}_step0_response.md` using the per-finding output format (Finding title, Dimension, Severity, Reason, What you noticed, Proposed fix) plus a TOTAL line. Abort threshold: severity 10 OR ≥5 findings at 7+ → stop and recommend re-running /plan-creation.

Mode: 2 (create)

( ) Step 0d: /question-loop the findings and apply accepted edits

Invoke /question-loop skill (NOT AskUserQuestion tool — different shape; /question-loop is Socratic text-based, AskUserQuestion is a constrained option-picker). Walk the findings file one finding at a time: user approves (apply as plan edit), rejects, or skips. Exit ramp: if accepted severity-7+ findings reach 5 during the walk, stop and recommend re-running /plan-creation. Do NOT mark 0d done in that case. When the walk completes without tripping the exit ramp, mark 0d (x) and advance [n] to Step 2.

Context: plans/review_{plan-name}_step0_response.md (set after 0b completes)
Skills: question-loop
Mode: 2 (create)
```

### Structural split is non-negotiable

Do NOT collapse 0b and 0d into a single step. Generation and walk are distinct activities — 0b produces an artifact, 0d consumes it. Keeping them separate lets the walk resume cleanly after `/clear` and lets the user re-run either half independently.

---

## Using /step Command

Plans integrate with the `/step` command for execution:

1. **Start a plan:**
   ```
   /step plans/my-plan.md
   ```

2. **Continue executing:**
   ```
   /step
   ```

3. **Track progress:**
   - Queue file: `.claude/.step-queue.json`
   - Persists across `/clear` commands

---

## Plan Completion Workflow

When all steps are marked `[x]`:

1. **Read current docs** - Check README.md and CLAUDE.md
2. **Update README.md** - Add section describing new feature
3. **Update CLAUDE.md** - Add new skills, commands, or workflows
4. **Git commit and push** - Commit all changes
5. **Delete plan file** - Ask user: "Plan complete. Delete `plans/[name].md`?"

---

## Common Patterns

### Research Plan

```markdown
### [ ] Step 2: Gather requirements
### [ ] Step 4: Explore existing code
### [ ] Step 6: Design solution
### [ ] Step 8: Create implementation plan (more detailed)
```

### Feature Implementation

```markdown
### [ ] Step 2: Create database schema
### [ ] Step 4: Build data models
### [ ] Step 6: Implement core logic
### [ ] Step 8: Add API endpoints
### [ ] Step 10: Write tests
### [ ] Step 12: Update documentation
```

### Refactoring Plan

```markdown
### [ ] Step 2: Document current behavior
### [ ] Step 4: Write tests for current behavior
### [ ] Step 6: Refactor [specific area]
### [ ] Step 8: Verify tests pass
### [ ] Step 10: Update documentation
```

### Survey Plan (Map-Then-Act)

For large-scale audits across many projects/files:

```markdown
### [ ] Step 2: Survey [project-A] — classify scripts
### [ ] Step 4: Survey [project-B] — classify scripts
### [ ] Step 6: Survey [project-C] — classify scripts
### [ ] Step 8: Triage — present all findings, get user decisions
### [ ] Step 10: Apply pattern to [project-A]
### [ ] Step 12: Apply pattern to [project-B]
### [ ] Step 14: Apply pattern to [project-C]
```

**Structure:**
1. **Survey phase** (Steps 1-N): Read and classify, touch NOTHING. One step per project/directory. Produce tables with verdicts (e.g., config-worthy, delete, skip). Mode: 1 (review) for all survey steps.
2. **Triage step**: Present all findings, get user decisions before any changes.
3. **Action phase** (Steps N+1 onward): Execute approved changes. The pattern established in survey makes each action step mechanical.

**Why survey-first works:** A large refactor plan (27 steps, ~380 scripts across many projects) spent ~2h surveying (Steps 1-15), then the extraction phase (Steps 17-26) was almost mechanical -- each step took 3-15 minutes because the pattern was proven. Committing to an action pattern before you've seen all the data leads to mid-plan redesigns.

**When to use:** Any task touching 5+ projects or 20+ files where you don't yet know the right pattern to apply.

---

## Avoiding Common Mistakes

| Mistake | Better Approach |
|---------|-----------------|
| Vague steps: "Do the thing" | Specific: "Create auth/password.py with hash and verify functions" |
| Giant steps | Break into 2-3 smaller steps |
| No success criteria | Add measurable outcomes |
| No current state | Document starting point |
| Whimsical name | Use descriptive three-word name |
| Plan saved inside `.claude/` | Put `plans/` at project root as sibling of `.claude/` |

