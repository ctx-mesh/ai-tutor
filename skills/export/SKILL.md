---
name: export
description: Export notes, progress data, or quiz history. Defaults to exporting notes. Use when the user runs /export or wants to get their notes, progress report, or learning data out of the tool.
argument-hint: "[notes | progress | quizzes | all]"
allowed-tools: [Bash]
---

# /export — Export Learning Artifacts

**Default behavior (no argument): export notes.** If the type of notes is ambiguous, ask.

Supported forms:
- `/export` — export notes (ask which type if unspecified)
- `/export notes` — export notes (ask which type)
- `/export notes chapter 3` — export chapter 3 notes as PDF
- `/export notes cheatsheet` — export cheatsheet
- `/export notes interview` — export interview notes
- `/export notes book` — export full book notes
- `/export progress` — export progress as a formatted text/markdown file
- `/export quizzes` — export quiz history as JSON
- `/export all` — export everything

## Step 1 — Identify the book

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py list
```

## Step 2 — Parse argument and resolve ambiguity

If the argument is `notes` or empty → **ask the user which notes to export** (unless a sub-type is already specified):

```
What would you like to export?

1. Chapter notes (PDF per chapter)
2. Full book notes (single PDF)
3. Cheatsheet
4. Interview prep notes
5. All of the above
```

Wait for their answer before proceeding.

If the argument already includes a sub-type (`notes chapter 3`, `notes cheatsheet`, etc.) → proceed directly without asking.

## Step 3 — Execute the export

### Notes export

First generate (or regenerate) the notes, then compile:

For chapter notes — iterate through all completed chapters:
```bash
echo '<chapter_notes_json>' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py generate-notes <slug> <N>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py compile-notes <slug> chapter<N>
```

For cheatsheet:
```bash
echo '<cheatsheet_json>' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py generate-cheatsheet <slug>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py compile-notes <slug> cheatsheet
```

For interview notes:
```bash
echo '<interview_json>' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py generate-interview-notes <slug>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py compile-notes <slug> interview_notes
```

For book notes:
```bash
echo '<book_notes_json>' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py generate-book-notes <slug>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py compile-notes <slug> book_notes
```

### Progress export

Load context and write a formatted markdown progress report to `.teach/books/<slug>/exports/progress_<date>.md`.

Use the Bash `Write` equivalent: write the file directly using the Write tool or by piping to a file.

### Quiz history export

The quiz JSON files are already in `.teach/books/<slug>/quizzes/`. Just tell the user where they are.
Optionally, if user wants a single file: compile them into `.teach/books/<slug>/exports/quiz_history.json`.

## Step 4 — Report results

```
📦 Export Complete

Notes exported to .teach/books/<slug>/notes/:
  ✅ chapter01.pdf   (12 pages)
  ✅ chapter02.pdf   (9 pages)
  ✅ chapter03.pdf   (15 pages)
  ✅ cheatsheet.pdf  (2 pages)
  ⚠️  chapter04.tex  (pdflatex not available — compile manually)

All files are in: .teach/books/designing-data-intensive-applications/notes/
```

If pdflatex is not available for any file, explain:
```
pdflatex is not installed — .tex files were generated but not compiled to PDF.
Install TeX Live to compile: https://www.tug.org/texlive/
Or open the .tex files in Overleaf (overleaf.com) for free online compilation.
```

## Step 5 — Offer next action

```
Want me to open the notes folder? Or is there anything else you'd like exported?
```
