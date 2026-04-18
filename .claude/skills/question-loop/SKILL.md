# Question Loop Skill

triggers: question-loop, socratic, insight, explore, question, loop, dig deeper, brainstorm, probe, discover, unpack, investigate patterns

## Overview

Structured exploration mode for discovering insights before implementation. Uses Socratic dialogue to build understanding, test hypotheses, and accumulate actionable items in a plan.

**Use when:** You need to understand a problem space, mine data for patterns, or explore options before committing to implementation.

**Don't use for:** Mid-task clarification (use AskUserQuestion), implementation planning (use EnterPlanMode), or external research (use WebSearch/Task).

---

## The Loop Structure

Each iteration follows this exact format:

### 1. NOTED (3-5 sentences)
Confirm what was just agreed or clarified:
- Acknowledge the user's input from the previous turn
- Summarize decisions made or insights confirmed
- Note any actionable items to add to the plan
- Skip this section on the first question of a loop

### 2. CONTEXT (5 sentences)
Provide background for WHY you're asking the next question:
- What aspect of the problem space are we exploring now?
- What do we already know that leads to this question?
- Why does this question matter for the overall goal?
- What would the answer unlock or enable?
- Use plain language: common words, sentences under 20 words

### 3. QUESTION (1 sentence)
Ask a specific, answerable question under 20 words.

### 4. ANSWER (5 sentences)
Answer immediately using plain language:
- Direct answer first (your best guess or hypothesis)
- Supporting evidence or reasoning
- What this means or enables
- Potential implications or follow-on considerations
- What you're uncertain about or would need to verify

### 5. Wait for Feedback
User responds with:
- **"yes"** / agreement -> Add to plan if actionable, continue to next question
- **"no"** / disagreement -> User explains why, adjust understanding, try again
- **Clarification** -> Incorporate new info, refine the question/answer
- **"call it"** -> Stop exploration, summarize findings

---

## Rules

**Plain language** -- Government/technical writing style. Applies to CONTEXT, QUESTION, and ANSWER:

- **Common words, not complex ones.** "Use" not "utilize." "Help" not "facilitate." "Start" not "commence."
- **Sentences under 20 words.** If a sentence runs long, it has two ideas. Split it.
- **Main point first.** Lead with the verdict, then the reason. Don't bury the answer under qualifiers.
- **Remove unnecessary words.** Cut "In my view," "I'd argue that," "Looking at this," and other throat-clearing.
- **Verbs, not nouns.** "Decide" not "make a decision." "Review" not "conduct a review."
- **Be direct and specific.** "Keep the current order" beats "My take is we should probably keep the existing approach."

Break every other rule before you bury the point. If your ANSWER has more commas than verbs, rewrite it.

**One question at a time** -- Never batch multiple questions.

**Always provide your answer** -- Don't ask and wait; ask, answer, then wait for feedback.

**Accumulate in the plan** -- When user agrees to an insight, add it as a step to the active plan.

**Build on previous answers** -- Each question should advance from the last, not restart.

**NOTED confirms, CONTEXT explains** -- NOTED summarizes what was just agreed; CONTEXT provides background for WHY the next question matters. Don't use CONTEXT to repeat the previous answer.

**5 sentences for CONTEXT and ANSWER** -- Keeps exploration grounded. NOTED can be 3-5 sentences. QUESTION stays at 1 sentence.

**Don't confuse with AskUserQuestion** -- That tool is for implementation choices ("which library?"), not exploration ("what patterns exist?").

---

## Example Flow

```
[First iteration - no NOTED section]

CONTEXT: We're designing a new public REST API for the analytics service.
The team hasn't decided whether to expose raw event records or pre-aggregated
metrics. This choice cascades into rate limits, caching, and how clients
build dashboards. Picking the wrong shape forces a v2 we have to deprecate.
Three early customers have draft integration specs we can read.

QUESTION: Do early customers want raw events or pre-aggregated metrics?

ANSWER: Looking at the three integration specs, two pull metrics into their
own dashboards and one wants raw events for replay. Pre-aggregated metrics
satisfy the majority and are cheaper to serve. The replay use case may not
need the public API -- a separate export endpoint could cover it. Pre-agg
also lets us cache aggressively from day one. I'd verify the third customer
truly needs raw events vs aggregated rollups before locking the design.

[User says: "yes, default to pre-aggregated. Add a step to spec the metric set."]

CLAUDE: *Adds "Spec the v1 metric set with the two metrics-first customers" to plan*

NOTED: Confirmed pre-aggregated is the default API shape. Adding a step to
spec the v1 metric set with the two metrics-first customers. The replay use
case stays out of scope for the public API for now.

CONTEXT: With pre-aggregated as the default, we need to nail down which
metrics ship in v1. The two metrics-first customers have draft specs that
list the dimensions they slice on. Aligning on a small core set is better
than shipping everything and pruning later. Versioning the metric schema
also matters -- breaking changes are expensive once dashboards exist.

QUESTION: What metrics appear in both customer specs that should be the v1
core?

[Loop continues]
```

---

## When to Add Plan Steps

Add a step when:
- User agrees an insight is actionable
- Investigation would yield concrete output (skill, doc update, code)
- Pattern suggests automation opportunity

Don't add a step when:
- Insight is interesting but not actionable
- User disagrees or needs more exploration
- It's background understanding, not a task

---

## Invoking from Plans

When writing plan steps that need Socratic exploration, use explicit invocation:

**In plan step:** `"Invoke question-loop skill to explore [topic] with user"`

**Why:** Skills trigger on user prompts, not plan file content. When executing a step, Claude reads the plan -- so "invoke question-loop skill" in the step text signals to load this skill's pattern.

| Without explicit invocation | With explicit invocation |
|-----------------------------|--------------------------|
| "Question-loop for X" -> skill doesn't trigger -> ad-hoc approach | "Invoke question-loop skill to X" -> skill triggers -> Context/Question/Answer/Feedback loop |

---

## Ending the Loop

When user says "call it" or "stop here":

1. **Summarize findings** -- Key insights discovered
2. **List new steps** -- What was agreed as actionable

Then branch on whether an active plan exists:

**Active plan exists** (check `plans/` for a relevant open plan):
3. Show plan status -- X completed, Y remaining
4. Suggest `/step` to start execution

**No active plan exists:**
3. Invoke plan-creation skill to capture findings as a new plan file in `plans/`
4. The loop output becomes the plan -- don't lose the work in a chat summary
