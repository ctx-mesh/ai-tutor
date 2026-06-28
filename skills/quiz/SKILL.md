---
name: quiz
description: Run an adaptive quiz on the book being studied. Use when the user runs /quiz, says "quiz me", "test me", "give me questions", or wants to be tested on specific topics or chapters.
argument-hint: "[chapter <N> | weak | <topic-name>]"
allowed-tools: [Bash]
---

# /quiz — Adaptive Quiz Engine

Supported forms:
- `/quiz` — adaptive quiz on current chapter
- `/quiz chapter 3` — quiz a specific chapter
- `/quiz weak` — quiz the student's weakest topics
- `/quiz replication` — quiz a specific concept or topic by name

## Step 1 — Identify the book

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py list
```

Use the most recently accessed book.

## Step 2 — Determine scope from argument

- `chapter <N>` → quiz concepts from chapter N
- `weak` → quiz weak topics (composite < 0.6)
- `<topic-name>` → find the concept by name and quiz it
- (nothing) → quiz current chapter from context

## Step 3 — Load context

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py context <slug>
```

Get: current chapter, weak topics, taught concepts, mastery scores.

## Step 4 — Select concepts to quiz

- **Current chapter / specific chapter**: use the taught concepts for that chapter
- **Weak**: use `weak_topics` from context (composite < 0.6), up to 10
- **Topic name**: search for matching concept, quiz that one

If no concepts have been taught yet in the requested scope:
> "No concepts have been taught in [scope] yet. Study first with /teach, then come back to quiz."

## Step 5 — Set difficulty per concept

For each concept, look up its mastery composite:
- composite ≥ 0.8 → **hard** questions (edge cases, compare/contrast, scenario, application)
- composite 0.5–0.8 → **medium** questions (explain tradeoffs, apply to scenario)
- composite < 0.5 → **easy** questions (define, basic recall, true/false)

## Step 6 — Run the quiz

Generate 5–8 questions (fewer for a single-concept quiz, more for chapter/weak scope).
Vary question types — never ask the same type back-to-back.

**Question types to use:**

**Multiple Choice** — for factual/definitional concepts:
```
Q: [Question text]

A) [option]
B) [option]
C) [option]
D) [option]

Your answer:
```
Wait for answer. Reveal correct answer and explain why the others are wrong.

**True / False** — for common misconceptions:
```
True or False: [statement]
```
Always explain the reasoning after.

**Fill in the Blank:**
```
Complete this: "In [context], when [condition], the system ___________"
```

**Explain in Your Own Words** — for deep concepts:
```
Explain [concept] as if you're teaching it to a colleague who hasn't read this book.
[Grade: accuracy, completeness, clarity, example used]
```
Rubric: Full credit = correct + complete + clear example. Partial = mostly right but missing key nuance. No credit = wrong.

**Scenario:**
```
You're designing a system that [requirement]. Your team suggests [concept].
Walk me through: Would you use it? What are the risks? What alternatives exist?
```

**Compare Concepts:**
```
Compare [A] vs [B]. When would you choose each? What's the key tradeoff?
```

**Application/Reasoning:**
```
Given: [specific situation with numbers/constraints]
Question: What happens when [event]? Walk through step by step.
```

## Step 7 — Evaluate and respond

**Correct answer:**
- Acknowledge specifically what was right (not just "correct!")
- Add one interesting extension or real-world example
- Update mastery upward

**Partially correct:**
- Acknowledge what was right
- Correct the specific gap
- Re-ask the exact same question phrased differently before moving on

**Wrong answer:**
- Do not repeat the same explanation that was already taught
- Try a different angle: analogy, visual, simpler breakdown
- Log misconception if this is the second time:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py log-misconception <slug> <concept_id> "<what they got wrong>"
```

## Step 8 — Update mastery after each answer

Score 0.0–1.0 on each dimension based on the answer quality:
- **understanding**: did they get the concept right?
- **recall**: did they recall it accurately under pressure?
- **application**: could they apply it to the scenario?
- **confidence**: how confident did they seem in the answer?

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py update-mastery <slug> <concept_id> <u> <r> <a> <c>
```

## Step 9 — Quiz summary

After all questions, log the session and show results:

```bash
echo '{"concept_id": "<id>", "quiz_type": "mixed", "total_questions": N, "correct_answers": N, "questions": [...]}' \
  | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py log-quiz <slug>
```

Show:
```
Quiz Complete! 📊

Score: 6/8 correct (75%)

✅ Strong answers:   Replication, B-Trees
⚠️  Needs more work:  LSM-Trees, Consensus

[If ≥80%]: Great work. These concepts are solidly in memory.
[If 60–79%]: Good progress. I'd recommend reviewing [weakest concept] once more.
[If <60%]: Let's revisit these before moving on. Run /review to go through them at your pace.
```

Then suggest next action:
- High score + new chapter coming → "Ready to continue? Say 'continue' or run /teach."
- Low score → "Want to review the weak ones now? Run /review."
