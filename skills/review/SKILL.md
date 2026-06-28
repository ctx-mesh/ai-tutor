---
name: review
description: Run spaced repetition reviews for concepts that are due. Use when the user runs /review, asks "what's due for review?", "review my weak topics", "do my reviews", or wants to go through spaced repetition.
argument-hint: "[<concept-name> | chapter <N> | all]"
allowed-tools: [Bash]
---

# /review — Spaced Repetition Review

Supported forms:
- `/review` — go through all SM-2 concepts due today
- `/review replication` — review a specific concept
- `/review chapter 3` — review all concepts from chapter 3
- `/review all` — review every taught concept (full refresh)

## Step 1 — Identify the book

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py list
```

Use the most recently accessed book.

## Step 2 — Get due reviews

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py due-reviews <slug>
```

Also load context for weak topics and taught concepts:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py context <slug>
```

## Step 3 — Determine scope

- `/review` (no argument) → `due_today` from CLI output
- `/review <concept-name>` → find that concept in mastery data, review it regardless of schedule
- `/review chapter N` → all taught concepts from chapter N
- `/review all` → all concepts in `mastery.json`

If nothing is due and no argument given:
```
✅ No reviews due today! Your spaced repetition schedule is clear.

Next reviews coming up:
  • Replication (in 2 days)
  • B-Trees (in 4 days)
  • LSM-Trees (in 5 days)

Come back then, or run /quiz to practice now.
```

## Step 4 — Announce the review session

```
📅 Review Session — [N] concepts due today

I'll ask you to recall each concept. This is retrieval practice — don't look anything up.
Ready? Let's go.
```

## Step 5 — For each concept, run a retrieval check

**Do NOT re-explain the concept from scratch.** This is a recall test, not a lesson.

Ask a short recall prompt:
```
[Concept name]

Quick — in 2-3 sentences: what is it, what problem does it solve, and what's the key tradeoff?
```

Wait for the student's response.

**If they remember well (accurate, complete):**
- Brief confirmation: "Exactly right. [One-sentence reinforcement]."
- Update mastery upward (recall +0.1, understanding stays, confidence +0.1)
- SM-2 interval extends → next review date pushed out

**If they partially remember:**
- Acknowledge what they got right
- Fill in the specific gap: "You got the what, but the key tradeoff you missed is..."
- Update mastery: modest improvement

**If they've forgotten:**
- Give a concise 3-4 sentence recap: intuition → definition → example → key tradeoff
- Do NOT run the full 12-step teaching protocol — this is a refresher
- Update mastery downward (recall -0.15, reset SM-2 interval to 1 day)
- Optionally ask a simple follow-up question to verify the recap landed

After each review:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py update-mastery <slug> <concept_id> <u> <r> <a> <c>
```

## Step 6 — Review session summary

```
Review Complete ✅

Reviewed: 5 concepts
  ✅ Remembered well:    Replication, B-Trees, ACID
  ⚠️  Partially recalled: Write-ahead Log
  ❌ Forgot:             Consensus Algorithms

Next reviews scheduled:
  • Replication       → in 12 days
  • B-Trees           → in 8 days
  • Consensus Alg.    → tomorrow

[If any forgotten]: Want to re-study Consensus Algorithms now? Say "teach consensus algorithms"
or pick it up in your next session.
```

## Key review principles

- Keep it short and fast — 2–3 minutes per concept maximum
- Never re-explain unless the student genuinely forgot — then give the short version only
- The goal is retrieval practice, not re-teaching
- Trust the SM-2 schedule — concepts the student knows well will naturally space out
