"""LaTeX note generation using Jinja2 templates."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _get_templates_dir() -> Path:
    """Locate templates relative to this file (works whether installed or run from repo)."""
    return Path(__file__).parent.parent.parent / "templates" / "teach"


def _env():
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        raise ImportError("Jinja2 is required: pip install Jinja2")

    templates_dir = _get_templates_dir()
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # Escape LaTeX special chars in values
    def latex_escape(text: str) -> str:
        specials = ["&", "%", "$", "#", "_", "{", "}", "~", "^", "\\"]
        for ch in specials:
            text = text.replace(ch, "\\" + ch)
        return text

    env.filters["le"] = latex_escape
    return env


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def generate_chapter_notes(
    book_path: Path | str,
    chapter_num: int,
    notes_data: dict,
) -> dict[str, str]:
    """
    Render chapter notes to .tex and write to notes/ directory.
    notes_data shape:
      {
        "chapter_title": str,
        "book_title": str,
        "concepts": [
          {
            "name": str,
            "definition": str,
            "intuition": str,
            "examples": [str],
            "analogies": [str],
            "warnings": [str],
            "formulas": [str],
            "connections": [str],
            "common_mistakes": [str],
          }
        ],
        "summary": str,
        "key_takeaways": [str],
        "personal_notes": str,
      }
    """
    book_path = Path(book_path)
    notes_dir = book_path / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    env = _env()
    template = env.get_template("chapter_notes.tex.j2")

    context = {
        "chapter_num": chapter_num,
        "date": _now_str(),
        **notes_data,
    }
    tex_content = template.render(**context)

    tex_path = notes_dir / f"chapter{chapter_num:02d}.tex"
    tex_path.write_text(tex_content)

    return {"tex_path": str(tex_path), "pdf_path": str(tex_path.with_suffix(".pdf"))}


def generate_book_notes(book_path: Path | str, notes_data: dict) -> dict[str, str]:
    book_path = Path(book_path)
    notes_dir = book_path / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    env = _env()
    template = env.get_template("book_notes.tex.j2")
    context = {"date": _now_str(), **notes_data}
    tex_content = template.render(**context)

    tex_path = notes_dir / "book_notes.tex"
    tex_path.write_text(tex_content)
    return {"tex_path": str(tex_path), "pdf_path": str(tex_path.with_suffix(".pdf"))}


def generate_cheatsheet(book_path: Path | str, notes_data: dict) -> dict[str, str]:
    book_path = Path(book_path)
    notes_dir = book_path / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    env = _env()
    template = env.get_template("cheatsheet.tex.j2")
    context = {"date": _now_str(), **notes_data}
    tex_content = template.render(**context)

    tex_path = notes_dir / "cheatsheet.tex"
    tex_path.write_text(tex_content)
    return {"tex_path": str(tex_path), "pdf_path": str(tex_path.with_suffix(".pdf"))}


def generate_interview_notes(book_path: Path | str, notes_data: dict) -> dict[str, str]:
    book_path = Path(book_path)
    notes_dir = book_path / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    env = _env()
    template = env.get_template("interview_notes.tex.j2")
    context = {"date": _now_str(), **notes_data}
    tex_content = template.render(**context)

    tex_path = notes_dir / "interview_notes.tex"
    tex_path.write_text(tex_content)
    return {"tex_path": str(tex_path), "pdf_path": str(tex_path.with_suffix(".pdf"))}
