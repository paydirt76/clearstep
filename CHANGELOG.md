# Changelog

All notable changes to Clear Step will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.69.42] - 2026-04-23

### Added
- Mandatory Step 0 Gap Analysis — every generated plan now gets a pre-flight review that scores findings by severity and walks them via `/question-loop` before execution begins.
- Follow-up prompt menu fires before plan disposition, offering next-action suggestions based on what the plan built.
- `/plan-completion` offers to create a project CLAUDE.md if none exists, instead of failing.
- `plans/templates/plan-completion.md` — new shipped file; the closing template the thin driver spawns.

### Changed
- `/plan-completion` rewritten from monolithic ~400-line skill to ~60-line thin driver that spawns a closing plan from `plans/templates/plan-completion.md`. Each closing step runs through `/step --0`, making the close inspectable and interruptible.
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
