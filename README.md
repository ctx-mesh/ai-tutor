# Teach — AI Tutor for Claude Code

A Claude Code plugin that transforms any PDF book into a personalized, interactive learning experience. Not a PDF chat tool. Not a summarizer. A world-class professor that remembers everything about your learning journey.

## What it does

- **Teaches** every concept in the book interactively — builds intuition before definitions
- **Quizzes** you after each concept and adapts difficulty to your mastery
- **Tracks progress** across sessions — picks up exactly where you left off
- **Schedules reviews** using SM-2 spaced repetition so you don't forget
- **Generates notes** as LaTeX PDFs — chapter notes, cheatsheets, interview prep
- **Remembers** your weak spots, misconceptions, preferred analogies, and learning style

Everything is stored in a `.teach/` folder inside your working directory. Each book has its own independent progress, notes, and mastery data.

---

## Requirements

- [Claude Code](https://claude.ai/code) (CLI or desktop app)
- Python 3.9+
- The following Python packages (see [Installation](#installation)):
  - `pymupdf` — PDF parsing
  - `Jinja2` — LaTeX template rendering
  - `rank-bm25` — search
  - `python-slugify` — book slug generation
- `pdflatex` *(optional)* — compiles `.tex` notes to PDF. Install via [TeX Live](https://www.tug.org/texlive/) or [MiKTeX](https://miktex.org/). Without it, `.tex` files are still generated and can be compiled manually or on [Overleaf](https://overleaf.com).

---

## Installation

### 1. Clone the repo

```bash
git clone git@github.com:ctx-mesh/ai-tutor.git
```

### 2. Install Python dependencies

```bash
cd ai-tutor
python3 -m pip install -r requirements.txt
```

### 3. Install the plugin into Claude Code

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)" ~/.claude/skills/teach
```

### 4. Reload plugins

In any active Claude Code session, run:

```
/reload-plugins
```

Or simply start a new Claude Code session. The plugin loads automatically.

### Verify installation

```bash
claude plugin list
```

You should see:

```
Skills-directory plugins (.claude/skills/*):

  ❯ teach@skills-dir
    Version: 1.0.0
    Status: ✔ loaded
```

---

## Uninstalling

```bash
rm ~/.claude/skills/teach
```

Then run `/reload-plugins` or restart Claude Code.

---

## Quick Start

Navigate to any folder containing a PDF and run:

```
/teach DDIA.pdf
```

You can also use Claude Code's `@` file picker to select a PDF:

```
/teach @                   ← opens the file picker, browse to your PDF
/teach @DDIA.pdf           ← directly references a file in the current folder
```

The tutor will parse the book, ask a few setup questions (learning mode, background), and begin teaching Chapter 1. From that point, just have a conversation.

If the folder has multiple PDFs and you run `/teach` with no argument, the tutor will list all PDFs in the current directory and ask which one to study.

---

## Commands

| Command | Description |
|---|---|
| `/teach [pdf]` | Start or resume studying a book |
| `/progress` | Full progress report — chapters, mastery, quiz stats, review schedule |
| `/quiz [chapter N \| weak \| topic]` | Adaptive quiz — current chapter, weak topics, or a specific topic |
| `/review [concept \| chapter N \| all]` | Spaced repetition — concepts due today or on demand |
| `/notes [chapter N \| cheatsheet \| interview \| book]` | Generate LaTeX notes and compile to PDF |
| `/export [notes \| progress \| quizzes \| all]` | Export artifacts — asks if unspecified |
| `/find <query>` | Search across concepts, notes, and misconceptions |
| `/reset [chapter N \| concept name \| all]` | Reset progress (always confirms before executing) |
| `/settings [mode \| pace \| style \| background]` | Change learning preferences |

During an active teaching session, you can also just talk naturally — "explain that differently", "give me an analogy", "skip this", "go deeper on X", "I already know this".

---

## Learning Modes

Set via `/settings mode` or during the initial setup:

| Mode | Description |
|---|---|
| **Normal** | Full explanations, examples, and analogies. Balanced. |
| **Deep** | Extra detail, proofs, all edge cases, extended examples |
| **Fast** | Core concepts only. Minimal examples. Maximum speed. |
| **Interview Prep** | Focus on tradeoffs, system design patterns, likely interview questions |
| **Revision** | You've seen this before — brief recap + quiz only |

---

## What gets stored

Everything lives in `.teach/` inside your working directory:

```
.teach/
└── books/
    └── designing-data-intensive-applications/
        ├── metadata.json          # book info and table of contents
        ├── concepts.json          # all extracted concepts and dependencies
        ├── progress.json          # chapter and concept completion
        ├── mastery.json           # per-concept mastery scores (SM-2)
        ├── sessions.json          # session history
        ├── misconceptions.json    # logged misconceptions
        ├── review_schedule.json   # spaced repetition schedule
        ├── preferences.json       # learning mode, style, analogies
        ├── quizzes/               # individual quiz attempt records
        └── notes/
            ├── chapter01.tex
            ├── chapter01.pdf
            ├── cheatsheet.tex
            ├── cheatsheet.pdf
            ├── interview_notes.tex
            └── book_notes.pdf
```

All files are human-readable JSON and LaTeX. No proprietary database.

---

## Running tests

```bash
python3 -m pytest tests/ -v
```

---

## How it works

The plugin is split into two layers:

**Claude** handles all reasoning: extracting concepts from chapter text, teaching interactively using a 12-step protocol, generating explanations and analogies, evaluating quiz answers, detecting misconceptions, and adapting to the student's learning style.

**Python scripts** (`scripts/teach/`) handle deterministic I/O: PDF parsing (PyMuPDF), state persistence (JSON), SM-2 scheduling, LaTeX rendering (Jinja2), PDF compilation (pdflatex), and BM25 search. All exposed via a single CLI (`scripts/teach/cli.py`) that always outputs JSON.

The `skills/teach/SKILL.md` file contains Claude's full professor protocol — about 700 lines of detailed instructions covering the teaching loop, adaptive responses, quiz engine, coverage verification, and all command handling.
