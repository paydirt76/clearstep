# Changelog

All notable changes to Clear Step will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-18

Initial public release.

### Added
- `/step` command — execute one plan step at a time with Phase A/B/C context loading, `[n]` marker advancement, and mandatory Step 5f reflection.
- `/plan-creation` skill — build numbered-step plans with sparse gap-of-2 numbering, Context/Skills/Mode hints, and sub-step markers.
- `/plan-completion` skill — close out a finished plan with Hall of Heroes eulogy generation, status transition, and index removal.
- `/question-loop` skill — Socratic NOTED/CONTEXT/QUESTION/ANSWER exploration for design decisions before implementation.
- `suggest_beep.py` hook — Stop-hook nudge that tells users how to self-install a terminal beep for their platform.
- `settings.json.template` — minimal starter settings with the Stop hook wired and a 19-entry destructive-shell deny list.
