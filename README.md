# Clear Step

**Context-engineered, plan-driven, step-at-a-time workflow for Claude Code.** 

Four commands. One template. Your plan survives `/clear` because state lives on disk, not in the conversation. 

If you've been burned by an autonomous AI run that changed 47 files overnight — or you keep hitting Claude Code's weekly usage caps — this is built for you.

Under the hood, this is a context engineering layer. Every step in the plan declares the files and line ranges it needs upfront. The harness loads exactly those under a 50k-token budget, runs one step, writes a `**Results:**` block, advances the `[n]` marker, then sharpens the next step's Context with what it just learned. The plan file — not the conversation — is the source of truth for what comes next. That makes adherence to the plan structural rather than willpower-based, turns `/clear` into a feature (the next `/step` re-reads the plan from disk, finds the marker, and keeps going), and lets multi-step work that would otherwise pile up 100k+ tokens of accumulated context fit in a focused 50k window per step.

---

## Install

Clone this repo, then copy the four commands/skills and the settings template into your project's `.claude/` directory.

```bash
# macOS / Linux
git clone https://github.com/<owner>/clearstep.git
cd clearstep
mkdir -p ~/your-project/.claude/{commands,skills} ~/your-project/plans

cp    .claude/commands/step.md            ~/your-project/.claude/commands/
cp -r .claude/skills/question-loop        ~/your-project/.claude/skills/
cp -r .claude/skills/plan-creation        ~/your-project/.claude/skills/
cp -r .claude/skills/plan-completion      ~/your-project/.claude/skills/
cp    .claude/settings.json.template      ~/your-project/.claude/settings.json
```

```powershell
# Windows (PowerShell)
git clone https://github.com/<owner>/clearstep.git
cd clearstep
New-Item -ItemType Directory -Force C:\your-project\.claude\commands, C:\your-project\.claude\skills, C:\your-project\plans | Out-Null

Copy-Item          .claude\commands\step.md            C:\your-project\.claude\commands\
Copy-Item -Recurse .claude\skills\question-loop        C:\your-project\.claude\skills\
Copy-Item -Recurse .claude\skills\plan-creation        C:\your-project\.claude\skills\
Copy-Item -Recurse .claude\skills\plan-completion      C:\your-project\.claude\skills\
Copy-Item          .claude\settings.json.template      C:\your-project\.claude\settings.json
```

Open `~/your-project/.claude/settings.json` and delete the `_install_instructions` key. That's the whole install.

No package manager. No server. No account. No Python. Five files on disk.

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
| `/plan-completion` (skill) | When all steps are `[x]`: writes a Hall of Heroes eulogy, transitions the plan to `reference`, archives it. |
| `settings.json.template` | Minimal permissions scaffold. Empty `allow` list. 19-entry destructive-shell `deny` blocklist. Empty `hooks` block you can fill yourself. |

Four commands. One template.

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

That's the whole onboarding. Everything else is graduated, not required:

- After `/step` clicks, try `/plan-completion` to close a plan and generate a Hall of Heroes eulogy.
- Try `/question-loop` before `/plan-creation` next time you're not sure what the plan should be.

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
| `/plan-completion` | When all steps are `[x]`: writes a Hall of Heroes eulogy, transitions the plan to `reference` status, archives it. |

Four commands. That's the whole workflow.

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
