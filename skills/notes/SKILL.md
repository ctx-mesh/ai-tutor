---
name: notes
description: Generate LaTeX notes and compile to PDF. Use when the user runs /notes, asks to "generate notes", "create notes", "make a cheatsheet", or "generate interview notes".
argument-hint: "[chapter <N> | cheatsheet | interview | book]"
allowed-tools: [Bash]
---

# /notes — Generate LaTeX Notes

Supported types:
- `/notes` — notes for the current chapter (default)
- `/notes chapter 3` — notes for a specific chapter
- `/notes cheatsheet` — condensed cheatsheet for the whole book
- `/notes interview` — interview-prep notes
- `/notes book` — complete book notes

## Step 1 — Identify the book

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py list
```

Use the most recently accessed book. If multiple books and no slug in the argument, use the one with `current_chapter` in progress.

## Step 2 — Determine note type from argument

Parse the argument:
- `chapter <N>` or `chapter<N>` → chapter notes for chapter N
- `cheatsheet` → cheatsheet
- `interview` → interview notes
- `book` → full book notes
- (nothing) → chapter notes for `current_chapter` from context

## Step 3 — Load context

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py context <slug>
```

Get: current chapter, book title, concepts taught, weak topics, misconceptions.

## Step 4 — Build the notes data

### For chapter notes

Load the concepts taught in that chapter from context. For each concept, synthesize:

```json
{
  "book_title": "<title>",
  "chapter_title": "<chapter title from metadata>",
  "summary": "<2-3 sentence summary of the chapter>",
  "concepts": [
    {
      "name": "...",
      "definition": "...",
      "intuition": "one-sentence intuition",
      "examples": ["...", "..."],
      "analogies": ["..."],
      "formulas": ["LaTeX math string if applicable, else empty"],
      "warnings": ["..."],
      "common_mistakes": ["..."],
      "connections": ["connects to X because...", "contrast with Y"]
    }
  ],
  "key_takeaways": ["takeaway 1", "takeaway 2", "takeaway 3"],
  "personal_notes": "<any misconceptions or struggles the student had with this chapter>"
}
```

Write the notes from your knowledge of the concepts taught — do NOT copy text verbatim. Write from understanding.

Generate:
```bash
echo '<notes_json>' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py generate-notes <slug> <chapter_num>
```

Compile:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py compile-notes <slug> chapter<N>
```

### For cheatsheet

Condense every taught concept to: name, one-liner, key formula (if any), one key insight. Maximum density.

```bash
echo '<cheatsheet_json>' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py generate-cheatsheet <slug>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py compile-notes <slug> cheatsheet
```

### For interview notes

Focus on: why-it-matters, likely interview questions, trade-offs, pitfalls. Include weak topics and misconceptions.

```bash
echo '<interview_json>' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py generate-interview-notes <slug>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py compile-notes <slug> interview_notes
```

### For book notes

Collect all chapters and their concepts. Synthesize a coherent book-level summary.

```bash
echo '<book_notes_json>' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py generate-book-notes <slug>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teach/cli.py compile-notes <slug> book_notes
```

## Step 5 — Report result

If PDF compiled successfully:
```
✅ Notes generated: .teach/books/<slug>/notes/chapter03.pdf

Chapter 3 — Storage and Retrieval
  • 4 concepts covered
  • 2 warnings
  • 3 key takeaways

Open the PDF at the path above, or compile the .tex manually if you prefer.
```

If pdflatex not available:
```
✅ LaTeX notes written: .teach/books/<slug>/notes/chapter03.tex

pdflatex is not installed so the PDF wasn't compiled automatically.
To compile: pdflatex chapter03.tex
Or install TeX Live: https://www.tug.org/texlive/
```

If an error occurred, show the error and the .tex path so the user can recover.
