# Changelog

All notable changes to Clear Step will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.69.420] - 2026-06-12 — "The Save File Update"

The brainstorming system got a ground-up rework, the plan reviewer
got a long-overdue balance pass, and the end-of-plan flow got some
quality-of-life love.

### New Features

- **Question Loop now has a save file.** Every brainstorming session
  writes to `plans/.loop-{topic}.md` as it goes — questions, answers,
  verdicts, and staged plan edits all persist. Crash, `/clear`, or
  walk away mid-loop and your progress is still there when you get
  back. No more losing a 40-minute session to a context wipe.
  - *Dev note: this was the #1 way good ideas died. The chat was the
    only record, and the chat doesn't survive. Now the file is the
    source of truth and the conversation is just the UI.*
- **Side quests no longer interrupt the main quest.** Questions that
  surface mid-loop go to a new Parked section instead of derailing
  the current thread. At the end of the loop, each parked question
  gets a disposition: promote it, turn it into a plan step, drop it,
  or leave it parked for next time.
- **Plan edits now apply in one batch.** Agreed insights stage up as
  `PROPOSED PLAN EDIT` lines during the loop and apply all at once
  when you call it — instead of live-editing the plan mid-conversation
  and hoping every edit landed.

### Balance Changes

- **Plan reviewer severity ratings rebalanced.** The built-in plan
  reviewer was rating minor issues as critical, tripping the abort
  threshold on plans that were fine to run.
  - "Plan doesn't list every call site": severity 7 → 4-5
  - "Line range off by a few lines": severity 7 → 5
  - "Vague step with an obvious answer": severity 7 → 5
  - A new down-check forces the question: *could a competent executor
    resolve this in under 5 minutes with a grep or one question?* If
    yes, it's not critical.
  - *Dev note: the reviewer is the same session that wrote the plan,
    so it tends to over-flag to look thorough and under-flag to
    protect its own work. The check now runs in both directions.*
- **Loop sprawl detection reworked.** The "are we still converging?"
  check no longer counts turns — it fires on quality signals instead:
  3 rejected answers in a row, or 2 clarifications on the same
  question. Long productive loops are no longer punished for being
  long.
- **NOTED section nerfed (in a good way).** The recap that opened
  every loop iteration now only appears when something nuanced was
  actually settled. Clean yes/no verdicts skip it. Less ritual, same
  record.

### Quality of Life

- **Clearer end-of-plan handoff.** When a plan finishes, `/step` now
  gives you the exact command to copy, tells you to `/clear` first,
  and fills in your actual plan filename — instead of a vague "run
  /plan-completion to finalize."
- **Design docs and plan steps stay in sync.** New rule: when a
  review finding changes a mechanism that lives in a design doc, the
  edit applies to both the plan step and the doc — no more silent
  drift between the two.
- Plan names can be four words now. Three was a hard cap; some plans
  need the fourth word.
- `question-loop` and `plan-completion` got proper description
  headers, so the skill router knows when to summon them.

## [0.69.42] - 2026-04-23

### Added
- Mandatory Step 0 Gap Analysis — every generated plan now gets a pre-flight review that scores findings by severity and walks them via `/question-loop` before execution begins.
- Follow-up prompt menu fires before plan disposition, offering next-action suggestions based on what the plan built.
- `/plan-completion` offers to create a project CLAUDE.md if none exists, instead of failing.
- `plans/templates/plan-closing.md` — new shipped file; the closing template the thin driver spawns.

### Changed
- `/plan-completion` rewritten from monolithic ~400-line skill to ~60-line thin driver that spawns a closing plan from `plans/templates/plan-closing.md`. Each closing step runs through `/step --0`, making the close inspectable and interruptible.
- Git commit+push behavior is now self-configuring — asks preference on first close (commit-only, commit-and-push, skip-this-time, skip-always).
- `suggest_beep.py` hook replaced with paste-ready beep snippets in the README for macOS, Linux, and Windows.
- `settings.json.template` simplified — empty hooks block, no `{{PROJECT_ROOT}}` placeholder.
- Plan-creation `Files to Create` section renamed to `Files to Modify`.
- Plan-creation location warning expanded with bypass-permissions explanation.

### Removed
- Hall of Heroes eulogy generation from plan-completion closing ritual.
- `suggest_beep.py` hook file.

## [0.1.0] - 2026-04-18

Initial public release.

### Added
- `/step` command — execute one plan step at a time with Phase A/B/C context loading, `[n]` marker advancement, and mandatory Step 5f reflection.
- `/plan-creation` skill — build numbered-step plans with sparse gap-of-2 numbering, Context/Skills/Mode hints, and sub-step markers.
- `/plan-completion` skill — close out a finished plan with a structured closing ritual, status transition, and index removal.
- `/question-loop` skill — Socratic NOTED/CONTEXT/QUESTION/ANSWER exploration for design decisions before implementation.
- `settings.json.template` — minimal starter settings with an empty `hooks` block and a 19-entry destructive-shell deny list. README includes paste-ready Stop-hook beep snippets for macOS, Linux, and Windows.
