---
name: settings
description: View or change learning preferences for the current book — learning mode, pace, explanation style, background knowledge. Use when the user runs /settings or wants to change how they are being taught.
argument-hint: "[mode | pace | style | background]"
allowed-tools: [Bash]
---

# /settings — Learning Preferences

Supported forms:
- `/settings` — show current settings and offer to change any
- `/settings mode` — change learning mode
- `/settings pace` — change how many concepts before a check-in
- `/settings style` — change preferred explanation style
- `/settings background` — update what you already know

## Step 1 — Identify the book

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py list
```

## Step 2 — Load current preferences

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py context <slug>
```

Extract `preferences` from the context.

## Step 3 — Show current settings (always, even if changing one)

```
⚙️  Settings for [Book Title]

  Learning Mode:      Normal
  Session Pace:       After each concept
  Explanation Style:  Intuition-first
  Background:         "Familiar with distributed systems basics"
  Preferred Analogies: cooking, sports

Type the number of what you'd like to change, or press Enter to leave as-is:
  1. Learning Mode
  2. Session Pace
  3. Explanation Style
  4. Background / Prior Knowledge
  5. Done — no changes
```

If a specific argument was given (`/settings mode`), skip directly to that setting.

## Step 4 — Handle each setting

### Learning Mode
```
Choose your learning mode:

  1. Normal        — Thorough explanations, examples, and analogies. Well-balanced.
  2. Deep          — Extra detail, proofs, edge cases, extended examples.
  3. Fast          — Core concepts only. Minimal examples. Maximum speed.
  4. Interview Prep — Focus on tradeoffs, system design, likely interview questions.
  5. Revision      — You've seen this before. Brief recap + quiz only.

Current: [current mode]
Enter 1–5 (or Enter to keep current):
```

### Session Pace
```
How many concepts should I teach before stopping for a check-in?

  1. After every concept  (most interactive, good for hard material)
  2. After 2–3 concepts   (balanced)
  3. After a full section (faster, good when you're in a flow)

Current: [current pace]
Enter 1–3 (or Enter to keep current):
```

### Explanation Style
```
How do you prefer I explain new concepts?

  1. Intuition-first  — Start with the big picture, then details
  2. Formal-first     — Start with the precise definition, then intuition
  3. Example-first    — Start with a concrete example, then generalise
  4. Problem-first    — Start with the problem, then the solution

Current: [current style]
Enter 1–4 (or Enter to keep current):
```

### Background / Prior Knowledge
```
Tell me what you already know about this topic. I'll skip basics you're familiar with
and focus on new material.

Current: "[background_notes]"

Type your update (or Enter to keep current):
```

## Step 5 — Save updated preferences

Build the updated preferences JSON from user answers, then:

```bash
echo '<updated_preferences_json>' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py update-preferences <slug>
```

## Step 6 — Confirm

```
✅ Settings updated.

  Learning Mode:      Fast  (changed)
  Session Pace:       After 2–3 concepts  (changed)
  Explanation Style:  Intuition-first
  Background:         "Familiar with distributed systems basics"

These will apply from your next teaching session onwards.
Continue studying? Say "continue" or run /teach.
```

## Notes

- Mode and style changes apply immediately to the active session.
- The tutor should naturally adapt based on these preferences without the student needing to repeat them.
- Analogy preferences are learned automatically during teaching (not set manually here) — if the student reacts positively to a specific analogy type, the tutor should remember it.
