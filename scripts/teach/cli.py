#!/usr/bin/env python3
"""
Teach CLI — unified entrypoint for all plugin operations.
All output is JSON to stdout. Errors: {"error": "<message>"}.

Usage: python3 cli.py <command> [args...]
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Allow running from any directory by adding the repo root to sys.path
_REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from scripts.teach import workspace as ws
from scripts.teach import pdf_parser, concepts, progress, mastery, sessions
from scripts.teach import misconceptions, quiz, review, notes, latex, search


def _out(data: object) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _err(msg: str, **kwargs) -> None:
    _out({"error": msg, **kwargs})


def _book_path(slug: str) -> Path:
    return ws.get_book_path(slug)


def cmd_init(args: list[str]) -> None:
    """init <pdf_path>"""
    if not args:
        _err("Usage: init <pdf_path>")
        return

    pdf_path = args[0]
    if not Path(pdf_path).exists():
        _err(f"PDF not found: {pdf_path}")
        return

    try:
        meta = pdf_parser.get_pdf_metadata(pdf_path)
        toc = pdf_parser.extract_toc(pdf_path)
        slug = ws.init_book(pdf_path, toc, meta)
        _out({
            "slug": slug,
            "title": meta["title"],
            "author": meta["author"],
            "total_pages": meta["total_pages"],
            "total_chapters": len(toc),
            "chapters": toc,
            "book_path": str(ws.get_book_path(slug)),
        })
    except Exception as e:
        _err(str(e))


def cmd_list(_args: list[str]) -> None:
    """list"""
    books = ws.list_books()
    _out({"books": books, "count": len(books)})


def cmd_context(args: list[str]) -> None:
    """context <slug>"""
    if not args:
        _err("Usage: context <slug>")
        return
    slug = args[0]
    book_path = _book_path(slug)

    if not book_path.exists():
        _err(f"Book not found: {slug}")
        return

    try:
        meta = json.loads((book_path / "metadata.json").read_text())
        prog = progress.get_progress(book_path)
        mast = mastery.get_mastery(book_path)
        recent = sessions.get_recent_sessions(book_path, limit=3)
        due = review.get_due_reviews(book_path)
        upcoming = review.get_upcoming_reviews(book_path, days_ahead=7)
        weak = mastery.get_weak_topics(book_path)
        strong = mastery.get_strong_topics(book_path)
        unresolved = misconceptions.get_unresolved_misconceptions(book_path)
        prefs = json.loads((book_path / "preferences.json").read_text()) if (book_path / "preferences.json").exists() else {}
        study_time = sessions.get_total_study_time_minutes(book_path)
        quiz_stats = quiz.get_quiz_stats(book_path)

        # Estimate time remaining (rough: 30 min per chapter not yet completed)
        total_ch = prog.get("total_chapters", 1)
        completed_ch = len(prog.get("completed_chapters", []))
        remaining_ch = max(0, total_ch - completed_ch)
        est_minutes_remaining = remaining_ch * 30

        ws.touch_last_accessed(slug)

        _out({
            "slug": slug,
            "title": meta.get("title"),
            "author": meta.get("author"),
            "total_chapters": total_ch,
            "progress": prog,
            "weak_topics": weak[:10],
            "strong_topics": strong[:10],
            "due_reviews": due,
            "upcoming_reviews": upcoming[:5],
            "recent_sessions": recent,
            "unresolved_misconceptions": unresolved[:5],
            "preferences": prefs,
            "study_time_minutes": study_time,
            "est_minutes_remaining": est_minutes_remaining,
            "quiz_stats": quiz_stats,
            "mastery_summary": {
                "total_concepts": len(mast["concept_mastery"]),
                "avg_composite": round(
                    sum(m["composite"] for m in mast["concept_mastery"].values()) / max(1, len(mast["concept_mastery"])),
                    3,
                ) if mast["concept_mastery"] else 0.0,
            },
        })
    except Exception as e:
        _err(str(e))


def cmd_extract(args: list[str]) -> None:
    """extract <slug> <chapter_num>"""
    if len(args) < 2:
        _err("Usage: extract <slug> <chapter_num>")
        return
    slug, chapter_str = args[0], args[1]
    try:
        chapter_num = int(chapter_str)
    except ValueError:
        _err(f"Invalid chapter number: {chapter_str}")
        return

    book_path = _book_path(slug)
    if not book_path.exists():
        _err(f"Book not found: {slug}")
        return

    try:
        meta = json.loads((book_path / "metadata.json").read_text())
        chapters = meta.get("chapters", [])
        ch = next((c for c in chapters if c["chapter_num"] == chapter_num), None)
        if not ch:
            _err(f"Chapter {chapter_num} not found in metadata")
            return

        pdf_path = meta["pdf_path"]
        result = pdf_parser.extract_chapter_text(pdf_path, ch["start_page"], ch["end_page"])
        result["chapter_num"] = chapter_num
        result["chapter_title"] = ch["title"]
        result["sections_from_toc"] = ch.get("sections", [])
        _out(result)
    except Exception as e:
        _err(str(e))


def cmd_update_progress(args: list[str]) -> None:
    """update-progress <slug> <chapter_num> <concept_id>"""
    if len(args) < 3:
        _err("Usage: update-progress <slug> <chapter_num> <concept_id>")
        return
    slug, chapter_str, concept_id = args[0], args[1], args[2]
    try:
        chapter_num = int(chapter_str)
    except ValueError:
        _err(f"Invalid chapter number: {chapter_str}")
        return

    book_path = _book_path(slug)
    try:
        prog = progress.mark_concept_taught(book_path, chapter_num, concept_id)
        _out(prog)
    except Exception as e:
        _err(str(e))


def cmd_update_mastery(args: list[str]) -> None:
    """update-mastery <slug> <concept_id> <u> <r> <a> <c>"""
    if len(args) < 6:
        _err("Usage: update-mastery <slug> <concept_id> <understanding> <recall> <application> <confidence>")
        return
    slug, concept_id = args[0], args[1]
    try:
        u, r, a, c = float(args[2]), float(args[3]), float(args[4]), float(args[5])
    except ValueError:
        _err("Scores must be floats between 0 and 1")
        return

    book_path = _book_path(slug)
    try:
        record = mastery.update_mastery(book_path, concept_id, u, r, a, c)
        _out(record)
    except Exception as e:
        _err(str(e))


def cmd_log_concept(args: list[str]) -> None:
    """log-concept <slug>  (concept JSON on stdin)"""
    if not args:
        _err("Usage: log-concept <slug>  (concept JSON on stdin)")
        return
    slug = args[0]
    book_path = _book_path(slug)
    try:
        concept_data = json.loads(sys.stdin.read())
        saved = concepts.save_concept(book_path, concept_data)
        _out(saved)
    except json.JSONDecodeError as e:
        _err(f"Invalid JSON on stdin: {e}")
    except Exception as e:
        _err(str(e))


def cmd_log_session(args: list[str]) -> None:
    """log-session <slug>  (session JSON on stdin)"""
    if not args:
        _err("Usage: log-session <slug>  (session JSON on stdin)")
        return
    slug = args[0]
    book_path = _book_path(slug)
    try:
        session_data = json.loads(sys.stdin.read())
        saved = sessions.log_session(book_path, session_data)
        _out(saved)
    except json.JSONDecodeError as e:
        _err(f"Invalid JSON on stdin: {e}")
    except Exception as e:
        _err(str(e))


def cmd_log_misconception(args: list[str]) -> None:
    """log-misconception <slug> <concept_id> <text...>"""
    if len(args) < 3:
        _err("Usage: log-misconception <slug> <concept_id> <text>")
        return
    slug, concept_id = args[0], args[1]
    text = " ".join(args[2:])
    book_path = _book_path(slug)
    try:
        record = misconceptions.log_misconception(book_path, concept_id, text)
        _out(record)
    except Exception as e:
        _err(str(e))


def cmd_log_quiz(args: list[str]) -> None:
    """log-quiz <slug>  (quiz JSON on stdin)"""
    if not args:
        _err("Usage: log-quiz <slug>  (quiz JSON on stdin)")
        return
    slug = args[0]
    book_path = _book_path(slug)
    try:
        quiz_data = json.loads(sys.stdin.read())
        saved = quiz.log_quiz(book_path, quiz_data)
        _out(saved)
    except json.JSONDecodeError as e:
        _err(f"Invalid JSON on stdin: {e}")
    except Exception as e:
        _err(str(e))


def cmd_due_reviews(args: list[str]) -> None:
    """due-reviews <slug>"""
    if not args:
        _err("Usage: due-reviews <slug>")
        return
    slug = args[0]
    book_path = _book_path(slug)
    try:
        due = review.get_due_reviews(book_path)
        upcoming = review.get_upcoming_reviews(book_path, days_ahead=7)
        _out({"due_today": due, "upcoming_7_days": upcoming})
    except Exception as e:
        _err(str(e))


def cmd_generate_notes(args: list[str]) -> None:
    """generate-notes <slug> <chapter_num>  (notes JSON on stdin)"""
    if len(args) < 2:
        _err("Usage: generate-notes <slug> <chapter_num>  (notes JSON on stdin)")
        return
    slug, chapter_str = args[0], args[1]
    try:
        chapter_num = int(chapter_str)
    except ValueError:
        _err(f"Invalid chapter number: {chapter_str}")
        return

    book_path = _book_path(slug)
    try:
        notes_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        _err(f"Invalid JSON on stdin: {e}")
        return

    try:
        result = notes.generate_chapter_notes(book_path, chapter_num, notes_data)
        _out(result)
    except Exception as e:
        _err(str(e))


def cmd_compile_notes(args: list[str]) -> None:
    """compile-notes <slug> <type>  (type: chapter<N>|book_notes|cheatsheet|interview_notes)"""
    if len(args) < 2:
        _err("Usage: compile-notes <slug> <type>")
        return
    slug, note_type = args[0], args[1]
    book_path = _book_path(slug)
    notes_dir = book_path / "notes"

    # Resolve file
    if note_type == "book_notes":
        tex_path = notes_dir / "book_notes.tex"
    elif note_type == "cheatsheet":
        tex_path = notes_dir / "cheatsheet.tex"
    elif note_type == "interview_notes":
        tex_path = notes_dir / "interview_notes.tex"
    elif note_type.startswith("chapter"):
        # e.g. "chapter3" or "chapter03"
        num_str = note_type.replace("chapter", "").strip()
        try:
            ch_num = int(num_str)
        except ValueError:
            _err(f"Invalid chapter type: {note_type}")
            return
        tex_path = notes_dir / f"chapter{ch_num:02d}.tex"
    else:
        _err(f"Unknown note type: {note_type}. Use: chapter<N>, book_notes, cheatsheet, interview_notes")
        return

    result = latex.compile_latex(tex_path)
    _out(result)


def cmd_search(args: list[str]) -> None:
    """search <slug> <query...>"""
    if len(args) < 2:
        _err("Usage: search <slug> <query>")
        return
    slug = args[0]
    query = " ".join(args[1:])
    book_path = _book_path(slug)
    try:
        results = search.search(book_path, query)
        _out({"query": query, "results": results, "count": len(results)})
    except Exception as e:
        _err(str(e))


def cmd_reset(args: list[str]) -> None:
    """reset <slug> [--chapter N | --concept ID | --all]"""
    if not args:
        _err("Usage: reset <slug> [--chapter N | --concept ID | --all]")
        return
    slug = args[0]
    book_path = _book_path(slug)

    if not book_path.exists():
        _err(f"Book not found: {slug}")
        return

    flags = args[1:]

    try:
        if "--all" in flags:
            meta = json.loads((book_path / "metadata.json").read_text())
            total_chapters = len(meta.get("chapters", []))
            prog = progress.reset_all(book_path, total_chapters)
            mastery.reset_all_mastery(book_path)
            # Clear quizzes
            for f in (book_path / "quizzes").glob("*.json"):
                f.unlink()
            _out({"reset": "all", "slug": slug, "progress": prog})

        elif "--chapter" in flags:
            idx = flags.index("--chapter")
            if idx + 1 >= len(flags):
                _err("--chapter requires a number")
                return
            chapter_num = int(flags[idx + 1])
            ch_concepts = concepts.get_chapter_concepts(book_path, chapter_num)
            concept_ids = [c["id"] for c in ch_concepts]
            prog = progress.reset_chapter(book_path, chapter_num, concept_ids)
            for cid in concept_ids:
                mastery.reset_concept_mastery(book_path, cid)
            _out({"reset": "chapter", "chapter_num": chapter_num, "concepts_reset": concept_ids, "progress": prog})

        elif "--concept" in flags:
            idx = flags.index("--concept")
            if idx + 1 >= len(flags):
                _err("--concept requires an ID")
                return
            concept_id = flags[idx + 1]
            mastery.reset_concept_mastery(book_path, concept_id)
            # Remove from taught list
            prog = progress.get_progress(book_path)
            taught = [c for c in prog.get("taught_concepts", []) if c != concept_id]
            prog["taught_concepts"] = taught
            from scripts.teach.workspace import _write_json
            _write_json(book_path / "progress.json", prog)
            _out({"reset": "concept", "concept_id": concept_id})

        else:
            _err("Specify --all, --chapter N, or --concept ID")

    except Exception as e:
        _err(str(e))


def cmd_mark_chapter_complete(args: list[str]) -> None:
    """mark-chapter-complete <slug> <chapter_num>"""
    if len(args) < 2:
        _err("Usage: mark-chapter-complete <slug> <chapter_num>")
        return
    slug, chapter_str = args[0], args[1]
    try:
        chapter_num = int(chapter_str)
    except ValueError:
        _err(f"Invalid chapter number: {chapter_str}")
        return
    book_path = _book_path(slug)
    try:
        prog = progress.mark_chapter_complete(book_path, chapter_num)
        _out(prog)
    except Exception as e:
        _err(str(e))


def cmd_update_preferences(args: list[str]) -> None:
    """update-preferences <slug>  (preferences JSON on stdin)"""
    if not args:
        _err("Usage: update-preferences <slug>  (preferences JSON on stdin)")
        return
    slug = args[0]
    book_path = _book_path(slug)
    try:
        new_prefs = json.loads(sys.stdin.read())
        prefs_path = book_path / "preferences.json"
        existing = json.loads(prefs_path.read_text()) if prefs_path.exists() else {}
        existing.update(new_prefs)
        prefs_path.write_text(json.dumps(existing, indent=2))
        _out(existing)
    except json.JSONDecodeError as e:
        _err(f"Invalid JSON on stdin: {e}")
    except Exception as e:
        _err(str(e))


def cmd_generate_book_notes(args: list[str]) -> None:
    """generate-book-notes <slug>  (notes JSON on stdin)"""
    if not args:
        _err("Usage: generate-book-notes <slug>  (notes JSON on stdin)")
        return
    slug = args[0]
    book_path = _book_path(slug)
    try:
        notes_data = json.loads(sys.stdin.read())
        result = notes.generate_book_notes(book_path, notes_data)
        _out(result)
    except json.JSONDecodeError as e:
        _err(f"Invalid JSON on stdin: {e}")
    except Exception as e:
        _err(str(e))


def cmd_generate_cheatsheet(args: list[str]) -> None:
    """generate-cheatsheet <slug>  (notes JSON on stdin)"""
    if not args:
        _err("Usage: generate-cheatsheet <slug>  (notes JSON on stdin)")
        return
    slug = args[0]
    book_path = _book_path(slug)
    try:
        notes_data = json.loads(sys.stdin.read())
        result = notes.generate_cheatsheet(book_path, notes_data)
        _out(result)
    except json.JSONDecodeError as e:
        _err(f"Invalid JSON on stdin: {e}")
    except Exception as e:
        _err(str(e))


def cmd_generate_interview_notes(args: list[str]) -> None:
    """generate-interview-notes <slug>  (notes JSON on stdin)"""
    if not args:
        _err("Usage: generate-interview-notes <slug>  (notes JSON on stdin)")
        return
    slug = args[0]
    book_path = _book_path(slug)
    try:
        notes_data = json.loads(sys.stdin.read())
        result = notes.generate_interview_notes(book_path, notes_data)
        _out(result)
    except json.JSONDecodeError as e:
        _err(f"Invalid JSON on stdin: {e}")
    except Exception as e:
        _err(str(e))


COMMANDS = {
    "init": cmd_init,
    "list": cmd_list,
    "context": cmd_context,
    "extract": cmd_extract,
    "update-progress": cmd_update_progress,
    "update-mastery": cmd_update_mastery,
    "log-concept": cmd_log_concept,
    "log-session": cmd_log_session,
    "log-misconception": cmd_log_misconception,
    "log-quiz": cmd_log_quiz,
    "due-reviews": cmd_due_reviews,
    "generate-notes": cmd_generate_notes,
    "generate-book-notes": cmd_generate_book_notes,
    "generate-cheatsheet": cmd_generate_cheatsheet,
    "generate-interview-notes": cmd_generate_interview_notes,
    "compile-notes": cmd_compile_notes,
    "search": cmd_search,
    "reset": cmd_reset,
    "mark-chapter-complete": cmd_mark_chapter_complete,
    "update-preferences": cmd_update_preferences,
}


def main() -> None:
    args = sys.argv[1:]
    if not args:
        _out({"commands": sorted(COMMANDS.keys()), "usage": "python3 cli.py <command> [args...]"})
        return

    command = args[0]
    rest = args[1:]

    handler = COMMANDS.get(command)
    if handler is None:
        _err(f"Unknown command: {command}", available=sorted(COMMANDS.keys()))
        sys.exit(1)

    handler(rest)


if __name__ == "__main__":
    main()
