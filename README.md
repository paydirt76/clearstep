# Clear Step

**Context-engineered, plan-driven, step-at-a-time workflow for Claude Code.** 

Four commands. Two templates. Your plan survives `/clear` because state lives on disk, not in the conversation. 

If you've been burned by an autonomous AI run that changed 47 files overnight — or you keep hitting Claude Code's weekly usage caps — this is built for you.

Under the hood, this is a context engineering layer. Every step in the plan declares the files and line ranges it needs upfront. The harness loads exactly those under a 50k-token budget, runs one step, writes a `**Results:**` block, advances the `[n]` marker, then sharpens the next step's Context with what it just learned. The plan file — not the conversation — is the source of truth for what comes next. That makes adherence to the plan structural rather than willpower-based, turns `/clear` into a feature (the next `/step` re-reads the plan from disk, finds the marker, and keeps going), and lets multi-step work that would otherwise pile up 100k+ tokens of accumulated context fit in a focused 50k window per step.

---

## Setup

Clone this repo, then let Claude Code install it -- or copy the files manually. All five files are at the repo root. Each gets renamed and placed into the right directory in your project.

```
git clone https://github.com/paydirt76/clearstep.git
```

**Easiest:** Open Claude Code in your project directory and say:

> Read the README in ../clearstep (or wherever you cloned it) and install Clear Step in this project.

**Manual install:** Copy each file to its destination, creating directories as needed.

| Repo file | Install to | What it is |
|-----------|-----------|------------|
| `step.md` | `.claude/commands/step.md` | The `/step` slash command |
| `question-loop.md` | `.claude/skills/question-loop/SKILL.md` | Socratic exploration skill |
| `plan-creation.md` | `.claude/skills/plan-creation/SKILL.md` | Plan authoring skill |
| `plan-completion.md` | `.claude/skills/plan-completion/SKILL.md` | Plan closing skill |
| `plan-closing.md` | `plans/templates/plan-closing.md` | Closing template used by `/plan-completion` |
| `settings.json.template` | *(reference only)* | Review it, then adapt your own `.claude/settings.json` by hand |

```bash
# macOS / Linux
cd clearstep
PROJECT=~/your-project

mkdir -p "$PROJECT/.claude/commands" \
         "$PROJECT/.claude/skills/question-loop" \
         "$PROJECT/.claude/skills/plan-creation" \
         "$PROJECT/.claude/skills/plan-completion" \
         "$PROJECT/plans/templates"

cp step.md              "$PROJECT/.claude/commands/step.md"
cp question-loop.md     "$PROJECT/.claude/skills/question-loop/SKILL.md"
cp plan-creation.md     "$PROJECT/.claude/skills/plan-creation/SKILL.md"
cp plan-completion.md   "$PROJECT/.claude/skills/plan-completion/SKILL.md"
cp plan-closing.md      "$PROJECT/plans/templates/plan-closing.md"
```

```powershell
# Windows (PowerShell)
cd clearstep
$Project = "C:\your-project"

New-Item -ItemType Directory -Force `
    "$Project\.claude\commands", `
    "$Project\.claude\skills\question-loop", `
    "$Project\.claude\skills\plan-creation", `
    "$Project\.claude\skills\plan-completion", `
    "$Project\plans\templates" | Out-Null

Copy-Item step.md            "$Project\.claude\commands\step.md"
Copy-Item question-loop.md   "$Project\.claude\skills\question-loop\SKILL.md"
Copy-Item plan-creation.md   "$Project\.claude\skills\plan-creation\SKILL.md"
Copy-Item plan-completion.md "$Project\.claude\skills\plan-completion\SKILL.md"
Copy-Item plan-closing.md    "$Project\plans\templates\plan-closing.md"
```

No package manager. No server. No account. No Python. Five files on disk, one template to review.

---

## Project Layout

**One required convention: `plans/` MUST be a sibling of `.claude/`, NOT inside it.** The slash commands are hardcoded to look for `plans/` at your project root. Plan files saved anywhere else will be invisible to `/step`, `/plan-creation`, and `/plan-completion`.

**Common foot-gun: do not put plans inside `.claude/`.** Two things break. (1) The slash commands won't find them — `/step` lists nothing, `/plan-creation` writes to the wrong place. (2) Claude Code's bypass-permissions mode explicitly excludes `.claude/` as a safety rail, so every Edit/Write to a plan inside there triggers a permission prompt even in yolo mode. Keep `plans/` as its own top-level folder.

```
your-project/                    <-- your project root
├── .claude/                     <-- Claude's config (commands, skills, settings)
│   ├── commands/step.md
│   ├── skills/{question-loop,plan-creation,plan-completion}/
│   └── settings.json
└── plans/                       <-- SIBLING of .claude/, NOT inside it
    ├── templates/
    │   └── plan-closing.md      <-- closing template for /plan-completion
    ├── hello-clear-step.md      <-- your plan files live here
    └── .step-queue.json         <-- auto-created on first /step
```

You only create the `plans/` directory itself. State files inside it auto-create:

- `.step-queue.json` — the default queue, written when you run `/step`.
- `.stepN-queue.json` — parallel work slots (e.g. `/step --3` writes `.step3-queue.json`). Useful when you want to run multiple plans without them stepping on each other.

The slash commands resolve `plans/` relative to the current working directory, so always run Claude Code from your project root. If `/step` opens the plan-selection menu when you expected an active queue, check that you're at the project root and not inside a subdirectory.

---

## What Ships

| File | Purpose |
|------|---------|
| `/question-loop` (skill) | Socratic exploration before you commit to a plan. NOTED -> CONTEXT -> QUESTION -> ANSWER, one beat at a time. |
| `/plan-creation` (skill) | Turns exploration into a numbered plan file with `[n]` marker and per-step Context hints. |
| `/step` (command) | Executes ONE step from the active plan. Three-phase context load (orient -> history -> step + Context files under 50k tokens). Writes a timestamped `**Results:**` block, advances `[n]`, sharpens the next step's Context, stops. |
| `/plan-completion` (skill) | When all steps are `[x]`: spawns a closing plan from the template -- audit, CLAUDE.md update, commit, disposition. |
| `plan-closing.md` (template) | Closing template spawned by `/plan-completion`. Controls what happens during close -- reorder steps, skip ones you don't need, add your own. |
| `settings.json.template` | Minimal permissions scaffold. Empty `allow` list. 19-entry destructive-shell `deny` blocklist. Empty `hooks` block you can fill yourself. Reference-only — review and adapt by hand. |

Four commands. Two templates.

---

## Quickstart -- /clear Survival Demo

The unfakeable proof: Clear Step picks up where it left off after you wipe the conversation.

### 1. Drop in an example plan

Save this to `plans/hello-clear-step.md`:

```markdown
---
project: demo
status: in_progress
priority: 5
created: 2026-04-17
---
# Plan: Hello Clear Step

## Goal
Prove `/step` survives `/clear`.

## Implementation Steps

### [n] Step 2: Create greeting.txt
Create `greeting.txt` containing the words "hello from step 2".
Mode: 2 (create)

### [ ] Step 4: Append a second line
Append "this line was added after /clear" to `greeting.txt`.
Mode: 2 (create)

### [ ] Step 6: Read and summarize
Read `greeting.txt` and summarize its contents.
Mode: 1 (review)
```

### 2. Run, wipe, re-run

In Claude Code:

```
/step plans/hello-clear-step.md
```

Clear Step executes Step 2, writes a `**Results:**` block with a real timestamp (it shells out to `date -u`), advances `[n]` to Step 4, and stops.

Now wipe the conversation:

```
/clear
```

Then run, with no arguments:

```
/step
```

The plan file is still on disk. The `[n]` marker still points at Step 4. Clear Step reads the plan, executes the next step, advances the marker. Same conversation-clearing ritual, same forward progress.

That's the core loop. Steps 1-2 used a hand-written plan to prove the mechanism. In practice, you generate plans and explore ideas with the other commands:

### 3. Writing your own plans with /plan-creation

When you have a real task, don't hand-write the plan file. Tell Claude Code what you want to build, then:

```
/plan-creation
```

It asks a few clarifying questions (goal, constraints, what files are involved), then writes a numbered plan to `plans/your-plan-name.md` with `[n]` markers, Context hints per step, and gap-of-2 numbering so you can insert steps later without renumbering. A mandatory Step 0 (Gap Analysis) reviews the plan before execution begins -- it scores findings by severity and walks them with you so you can accept or reject edits before Step 2 fires.

Once the plan exists, run `/step` to execute it one step at a time.

### 4. Exploring before you plan with /question-loop

When you're not sure what the plan should be yet -- you have a vague goal but haven't decided the approach:

```
/question-loop
```

This runs a Socratic exploration loop. Each turn follows a NOTED -> CONTEXT -> QUESTION -> ANSWER rhythm: it acknowledges what you said, adds relevant context, asks one focused question, and waits. No code gets written. The output is clarity, not artifacts. When the shape of the work is clear, exit the loop and run `/plan-creation`.

### 5. Closing a finished plan with /plan-completion

When all steps in a plan are marked `[x]`:

```
/plan-completion
```

This spawns a closing plan from the `plan-closing.md` template. The closing ritual runs as discrete `/step` iterations -- audit what changed, update your project's CLAUDE.md, commit, choose what to do with the plan file (archive, delete, or keep). Each closing step is inspectable and interruptible, same as any other step.

---

## Honest Limits

**You give up set-and-forget AI coding.** Clear Step beeps every few minutes and waits for you to say go. You pay 30 seconds every five minutes so you don't pay 30 minutes of cleanup every hour.

**The main failure mode is plan-premise drift.** If Step 2 was built on a misread of the codebase, everything downstream is contaminated. Two recovery paths:

- **Cheap:** A mandatory five-question reflection pass after every step (`5f` in `/step`) catches most drift. Affected downstream steps get marked `[~]` superseded; corrections get inserted.
- **Expensive:** A step gets marked `[!]` stuck. Execution halts. You talk to the model and either rewrite the plan tail or start fresh informed by what was learned.

The tool bounds execution, not judgment. A bad premise all the way down is still on you.

**Not good for:**

- **Greenfield prototyping.** Use chat mode. Come back when the idea is concrete enough to plan.
- **Solo scripts under ~100 lines.** The plan file IS the overhead. Don't ceremony-check a one-liner.
- **Paired team work on a shared plan.** Clear Step is single-user state.

The threshold isn't plan length -- it's whether the work is multi-step or may require over 100,000 tokens of context.

---

## Platform Notes

**Tested daily on Windows 11.** The commands and skills are plain markdown, so they work identically on macOS, Linux, and anywhere Claude Code runs.

- **Windows-specific advice lives inline** in the command and skill prose (MSYS path mangling on Git Bash, `encoding='utf-8'` on `open()` calls, ASCII-only prints in background scripts). The advice fires when the model sees it matters.
- **macOS:** untested by the author at launch. On the roadmap. The author runs Windows daily but owns a Mac. Mac testing is the builder's job.
- **Linux:** the explicit contributor gap. If you run Linux and hit a problem, file it. That's the contribution that matters most at launch.

### Wiring up a beep (optional)

Claude Code doesn't make noise when it finishes a turn. A Stop hook can play a sound. Pick your OS and paste the matching snippet into the `hooks` block of `.claude/settings.json`:

**macOS:**
```json
"Stop": [
  { "hooks": [ { "type": "command", "command": "afplay /System/Library/Sounds/Glass.aiff" } ] }
]
```

**Linux:**
```json
"Stop": [
  { "hooks": [ { "type": "command", "command": "paplay /usr/share/sounds/freedesktop/stereo/bell.oga" } ] }
]
```

**Windows:**
```json
"Stop": [
  { "hooks": [ { "type": "command", "command": "powershell -c \"[console]::beep(400,500)\"" } ] }
]
```

Restart Claude Code for the hook to take effect. Swap in any sound file you prefer.

---

## Command Reference

| Command | What it does |
|---------|--------------|
| `/question-loop` | Structured Socratic exploration. NOTED -> CONTEXT -> QUESTION -> ANSWER per turn. Use before you know what the plan should be. |
| `/plan-creation` | Short Socratic exchange -> writes a numbered plan with `[n]` marker and per-step Context hints to `plans/your-plan-name.md`. Enforces descriptive 3-4 word plan names. |
| `/step` | Executes exactly ONE step from the active plan. Three-phase context load, timestamped `**Results:**` block, `[n]` advances, next step's Context gets sharpened, stops. |
| `/plan-completion` | When all steps are `[x]`: spawns a closing plan from the template. Audit, CLAUDE.md update, commit, disposition -- each as its own step. |

Four commands. That's the whole workflow.

---

## Patch Notes -- v0.69.42

This update breaks the biggest bottleneck in the closing workflow and adds pre-flight plan review.

### Plan Completion -- Reworked

**Why.** The old plan-completion skill was a single monolithic block -- roughly 400 lines executing in one shot. On complex plans, this ate context window budget and gave you no way to inspect or interrupt the closing process. If something went wrong halfway through, you started over.

**What.** Plan completion is now a thin driver (~60 lines) that spawns a multi-step closing plan from the `plan-closing.md` template. Each closing step -- audit, CLAUDE.md update, commit, disposition -- runs individually through `/step --0`. The Hall of Heroes eulogy is retired (this shortened the closing process with negligible loss).

**How.** The setup copies `plan-closing.md` to `plans/templates/plan-closing.md` in your project. The template controls what happens during close -- reorder steps, skip ones you don't need, add your own. Git push behavior is self-configuring: on first close, it asks your preference (commit-only, commit-and-push, skip) and remembers it.

### Step 0 -- Mandatory Gap Analysis

Every generated plan now gets a mandatory pre-flight review before Step 2 fires. Step 0 generates findings scored by severity across four dimensions, then walks you through each one via `/question-loop` so you can accept or reject edits. Catches missing steps, dependency gaps, and underspecified work before they blow up mid-execution. Plans that survive Step 0 hit fewer surprises.

### Minor Changes

- `suggest_beep.py` hook removed. Beep setup is now paste-ready JSON snippets in the README -- pick your OS, copy one block.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Contributing

**File issues for:**
- Linux friction (the explicit contributor gap).
- macOS friction (author's backlog, but reports welcome).
- Places where the command or skill prose gave confusing guidance.
- Plan-structure ideas that survive the "does this fit four commands and a hook?" test.

**Not for:**
- Feature requests that require a server, an account, or a package manager.
- Requests to port to a non-Claude-Code stack. Clear Step is a Claude Code discipline layer, not a universal workflow framework.

The repo is plain-markdown, so a good issue is usually a good PR.

---

For the longer-form pitch (the bet, the four architectural fixes, the compounding-value argument), see `ANNOUNCEMENT.md`.
