---
name: progress
description: Show a thorough progress report for the book currently being studied. Use when the user runs /progress, asks "how am I doing?", "show my progress", "what's my mastery?", or wants a progress breakdown.
argument-hint: "[book-slug]"
allowed-tools: [Bash]
---

# /progress — Thorough Progress Report

## Step 1 — Identify the book

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py list
```

- If one book: use it automatically.
- If multiple: use the most recently accessed (`last_accessed`). If the user passed a slug as argument, use that.
- If no books: tell the user to run `/teach <pdf>` first.

## Step 2 — Load full context

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py context <slug>
```

## Step 3 — Render the report

Present every section below. Do not skip any section even if it has no data — show "None yet" for empty sections.

---

### Header

```
📚 [Book Title] by [Author]
Last studied: [last_accessed, human-readable: "2 days ago" / "today" / "June 28"]
Total study time: [X hours Y minutes]
```

---

### Overall Progress

Show a visual progress bar (use █ and ░, 20 chars wide):

```
Overall  ████████████░░░░░░░░  60%   [completed chapters] / [total chapters] chapters
```

Then per-chapter breakdown. For each chapter show:
- ✅ if complete, 🔵 if in progress (current chapter), ⬜ if not started
- Title and completion %

```
Chapter Breakdown:
  ✅  1. Reliable, Scalable Systems          100%
  ✅  2. Data Models and Query Languages     100%
  🔵  3. Storage and Retrieval               45%   ← you are here
  ⬜  4. Encoding and Evolution                0%
  ⬜  5. Replication                           0%
  ...
```

---

### Mastery Breakdown

Show the 4-dimension mastery table for all **taught concepts**, grouped by chapter.
Use the mastery.json data. Format:

```
Mastery by Concept:

Chapter 1 — Reliable, Scalable Systems
  Concept                   U     R     A     C     Overall
  ─────────────────────────────────────────────────────────
  Reliability              90%   85%   80%   90%    87%  ✅
  Scalability              75%   70%   65%   80%    73%  🔵
  Maintainability          60%   55%   50%   60%    57%  ⚠️

Chapter 2 — Data Models
  ...
```

Legend: ✅ ≥80% mastery · 🔵 60–79% · ⚠️ <60%

U=Understanding · R=Recall · A=Application · C=Confidence

---

### Strong & Weak Topics

```
💪 Strong Topics (≥80% mastery):
  • Reliability (87%)
  • B-Trees (83%)

⚠️  Weak Topics (<60% mastery):
  • Consensus Algorithms (34%)
  • LSM-Trees (48%)
  • [if none: "No weak topics yet — great work!"]
```

---

### Quiz Performance

```
📊 Quiz Stats:
  Total quizzes taken:   12
  Questions answered:    48
  Accuracy:              73%

  By type:
    Multiple Choice      80%  (24 questions)
    Explain in own words 65%  (12 questions)
    Scenario             70%  (12 questions)
```

If no quizzes: "No quizzes taken yet. Run /quiz to test your knowledge."

---

### Spaced Repetition

```
📅 Review Schedule:
  Due today:      3 concepts  → run /review to go through them
  Due this week:  7 concepts

  Next up:
    • Replication (due today, 45% mastery)
    • Write-ahead Log (due today, 52% mastery)
    • LSM-Trees (due in 2 days, 48% mastery)
```

If nothing due: "No reviews due. Keep studying and they'll appear here."

---

### Misconceptions

```
🧠 Unresolved Misconceptions:
  • [concept]: [what was misunderstood]
  • ...
  [if none: "No misconceptions logged — well done!"]
```

---

### Session History

Show the 3 most recent sessions:

```
📖 Recent Sessions:
  Jun 28  Chapter 3 · 45 min · 4 concepts · quiz: 3/4 correct
  Jun 26  Chapter 2 · 60 min · 6 concepts · quiz: 5/6 correct
  Jun 24  Chapter 1 · 90 min · 8 concepts · quiz: 7/8 correct
```

---

### Time Estimate

```
⏱ Estimated time remaining: ~6 hours
  (based on [N] chapters × avg 30 min/chapter + review queue)
```

---

### Footer suggestion

End with one actionable recommendation based on the data:
- If weak topics exist: "I'd recommend reviewing [weakest topic] before moving on."
- If due reviews exist: "You have reviews due — run /review to clear them."
- If on track: "You're making great progress! Continue with Chapter N."
