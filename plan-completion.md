# Plan Completion Skill

triggers: plan complete, all steps done, close plan via template, spawn closing plan, delete plan

## Overview

Thin driver. Invoked against a specific source plan. Spawns a closing plan from `plans/templates/plan-closing.md`, registers it in queue 0, tells the user to run `/clear` then `/step --0`, and exits. All closing-workflow logic (audit, CLAUDE.md update, commit, follow-up prompt, disposition, self-delete) lives in the template's Steps 2-8.

**Input:** `SOURCE_PLAN` -- path to the plan being closed (e.g., `plans/my-feature.md`). Provided by the caller.

---

## Procedure

### 1. Completeness gate

Grep `SOURCE_PLAN` for unfinished markers at any tier:

```
Grep pattern="^### \[n\]|^\(n\)|^<n>|^### \[ \]|^\( \)|^< >|^### \[w\]|^\(w\)|^<w>|^### \[!\]|^\(!\)|^<!>" path=[SOURCE_PLAN]
```

If ANY match, abort with the list: "Source plan has unfinished steps -- cannot close. Resolve these first, then retry." `[~]` (superseded) is equivalent to `[x]` -- do NOT reject.

### 2. Derive variables

- `SOURCE_PLAN_NAME` = basename of `SOURCE_PLAN` minus `.md` (`plans/foo.md` -> `foo`)
- `SOURCE_PROJECT` = value of `project:` in `SOURCE_PLAN`'s YAML frontmatter
- `SOURCE_QUEUE` = queue file whose `active_plan` equals `SOURCE_PLAN` (grep `plans/.step*-queue.json` for the path; if not found, use empty string -- source plan was never queued, template's disposition step will no-op on queue cleanup)
- `STEP_COUNT` = count of lines matching `^### \[x\]|^### \[~\]` in `SOURCE_PLAN`
- `CLOSING_PLAN` = `plans/{SOURCE_PLAN_NAME}-closing.md`
- `CLOSING_QUEUE` = `plans/.step0-queue.json` (hardcoded literal)
- `DATE` = output of `date -u +"%Y-%m-%d"` (run the command; never guess)

### 3. Register closing plan in queue 0

Update `plans/.step0-queue.json`:
- Set `active_plan` to `CLOSING_PLAN`
- Append `CLOSING_PLAN` to the `queue` array if not already present

If `plans/.step0-queue.json` is missing, create it with `{"active_plan": CLOSING_PLAN, "queue": [CLOSING_PLAN]}`.

### 4. Dupe template, substitute variables

Copy `plans/templates/plan-closing.md` to `CLOSING_PLAN`, then run a small substitution script (sed or Python) to replace every `{{VAR}}` in `CLOSING_PLAN` with its derived value across all 8 variables. Do NOT read the template into context to substitute -- use the filesystem.

If `plans/templates/plan-closing.md` does not exist, abort: "Template not found at `plans/templates/plan-closing.md`. Place the plan-completion template from the clearstep repo into that path and retry."

After substitution, grep `CLOSING_PLAN` for any surviving occurrence of the 8 named placeholders (`{{SOURCE_PLAN}}`, `{{SOURCE_PLAN_NAME}}`, `{{SOURCE_PROJECT}}`, `{{CLOSING_PLAN}}`, `{{SOURCE_QUEUE}}`, `{{CLOSING_QUEUE}}`, `{{STEP_COUNT}}`, `{{DATE}}`). If ANY match: delete the malformed `CLOSING_PLAN` and abort -- a variable was missed. Do NOT ship a partially-substituted closing plan.

**Do NOT use a generic `\{\{[A-Z_]+\}\}` regex** -- the template intentionally contains `{{PLACEHOLDER}}` / `{{PLACEHOLDERS}}` mentions in its own explanatory prose (Step 8 template-generalization guidance, the pre-amble warning). Those are meta-references, not unsubstituted vars; a broad regex false-positives on them and aborts a valid close.

### 5. Hand off to the user

Report to the user:

```
Closing plan spawned: [CLOSING_PLAN]
Run /clear, then /step --0 to run the close ritual.
```

Then exit. Do NOT invoke `/step --0` yourself -- the user runs `/clear` first to drop the source-plan context, then kicks off `/step --0` in a fresh conversation. Everything downstream -- audit, CLAUDE.md update, commit, follow-up prompt, disposition, self-delete -- is the closing plan's job.

---

## Explicit exclusion

- **Do NOT stage `CLOSING_PLAN` or `CLOSING_QUEUE` for git.** The template's Step 8 explicitly excludes both from the source-plan commit; the thin skill must not undo that by staging them earlier.
