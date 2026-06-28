---
name: reset
description: Reset progress, mastery, or quiz history for a concept, chapter, or entire book. Use when the user runs /reset and wants to start over on something.
argument-hint: "[chapter <N> | concept <name> | all]"
allowed-tools: [Bash]
---

# /reset — Reset Progress

Supported forms:
- `/reset chapter 3` — reset one chapter
- `/reset concept replication` — reset one concept
- `/reset all` — reset the entire book
- `/reset` (no argument) — ask what to reset

**Always confirm before executing. Resets are irreversible.**

## Step 1 — Identify the book

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py list
```

## Step 2 — Determine scope from argument

- `chapter <N>` → reset that chapter
- `concept <name>` → find and reset that concept
- `all` → reset the whole book
- (nothing) → ask: "What would you like to reset? A chapter, a specific concept, or the whole book?"

## Step 3 — Confirm with the user

### Reset a concept
```
⚠️  Reset concept "[name]"?

This will:
  • Clear mastery scores (U/R/A/C)
  • Remove it from your taught list
  • Delete its review schedule

This cannot be undone. Confirm? (yes / no)
```

### Reset a chapter
```
⚠️  Reset Chapter [N]: "[title]"?

This will:
  • Clear progress and mastery for [X] concepts
  • Reset chapter completion to 0%
  • Delete review schedules for those concepts
  • Quiz history is preserved

Concepts affected: [list concept names]

This cannot be undone. Confirm? (yes / no)
```

### Reset entire book
```
⛔ Reset ALL progress for "[Book Title]"?

This will permanently erase:
  • All chapter and concept progress
  • All mastery scores
  • All quiz history
  • All review schedules

Your notes files (.tex / .pdf) will NOT be deleted.

To confirm, type: yes I am sure
```

Only accept the exact phrase "yes I am sure" for the full reset. Any other response cancels.

## Step 4 — Execute if confirmed

### Concept reset
Find the concept ID by searching concepts.json, then:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py reset <slug> --concept <concept_id>
```

### Chapter reset
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py reset <slug> --chapter <N>
```

### Full reset
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py reset <slug> --all
```

## Step 5 — Confirm what happened

```
✅ Reset complete.

[For concept]: "[name]" has been cleared. It will be re-taught the next time
you reach it in the book.

[For chapter]: Chapter [N] reset. [X] concepts cleared.
Resume with /teach to start Chapter [N] fresh.

[For all]: All progress for "[Book Title]" has been cleared.
Run /teach to start from the beginning.
```

## If user cancels

```
Reset cancelled. No changes were made.
```
