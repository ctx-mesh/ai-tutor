"""PDF parsing using PyMuPDF — extracts TOC, chapter text, section headings."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _import_fitz():
    try:
        import fitz
        return fitz
    except ImportError:
        raise ImportError(
            "pymupdf is required: pip install pymupdf"
        )


# Patterns for chapter heading detection (fallback when PDF has no embedded TOC)
_CHAPTER_PATTERNS = [
    re.compile(r"^chapter\s+(\d+)[:\s\.\-—]*(.*)$", re.IGNORECASE),
    re.compile(r"^(\d+)\.\s+([A-Z][A-Za-z\s]{3,60})$"),
    re.compile(r"^CHAPTER\s+([IVXLCDM]+)[:\s\.\-—]*(.*)$", re.IGNORECASE),
]

_SECTION_PATTERNS = [
    re.compile(r"^(\d+\.\d+)\s+(.+)$"),
    re.compile(r"^(\d+\.\d+\.\d+)\s+(.+)$"),
]


def _roman_to_int(s: str) -> int:
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    result, prev = 0, 0
    for ch in reversed(s.upper()):
        v = vals.get(ch, 0)
        result += v if v >= prev else -v
        prev = v
    return result


def get_pdf_metadata(pdf_path: str) -> dict[str, Any]:
    """Extract title, author, page count."""
    fitz = _import_fitz()
    doc = fitz.open(pdf_path)
    meta = doc.metadata or {}
    return {
        "title": meta.get("title", "").strip() or Path(pdf_path).stem,
        "author": meta.get("author", "").strip(),
        "total_pages": doc.page_count,
        "pdf_path": str(Path(pdf_path).resolve()),
    }


def extract_toc(pdf_path: str) -> list[dict[str, Any]]:
    """
    Extract table of contents. Uses PyMuPDF's built-in TOC first;
    falls back to heuristic chapter detection if TOC is empty.
    """
    fitz = _import_fitz()
    doc = fitz.open(pdf_path)
    total_pages = doc.page_count

    # Try embedded TOC
    raw_toc = doc.get_toc(simple=False)
    if raw_toc:
        return _parse_embedded_toc(raw_toc, total_pages)

    # Heuristic fallback: scan pages for chapter headings
    return _detect_chapters_heuristically(doc)


def _parse_embedded_toc(raw_toc: list, total_pages: int) -> list[dict]:
    """Convert PyMuPDF TOC entries to chapter list (top-level entries only)."""
    chapters = []
    chapter_num = 0

    # Collect level-1 entries (chapters)
    top_level = [(level, title, page) for level, title, page, *_ in raw_toc if level == 1]

    for i, (level, title, start_page) in enumerate(top_level):
        chapter_num += 1
        end_page = top_level[i + 1][2] - 1 if i + 1 < len(top_level) else total_pages
        # Collect sections within this chapter (level 2)
        sections = []
        for slevel, stitle, spage, *_ in raw_toc:
            if slevel == 2 and start_page <= spage <= end_page:
                sections.append({"title": stitle.strip(), "page": spage})

        chapters.append({
            "chapter_num": chapter_num,
            "title": title.strip(),
            "start_page": start_page,
            "end_page": end_page,
            "page_count": max(1, end_page - start_page + 1),
            "sections": sections,
            "has_figures": False,  # updated during text extraction
        })

    return chapters


def _detect_chapters_heuristically(doc) -> list[dict]:
    """Scan PDF pages for large/bold text that looks like chapter headings."""
    chapters = []
    chapter_num = 0
    total_pages = doc.page_count

    for page_num in range(total_pages):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block["type"] != 0:  # text block
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    flags = span.get("flags", 0)
                    size = span.get("size", 0)
                    is_bold = bool(flags & 2**4)  # bold flag

                    if not text or len(text) < 3:
                        continue

                    # Large font + bold = likely chapter heading
                    if size >= 14 and is_bold:
                        for pattern in _CHAPTER_PATTERNS:
                            m = pattern.match(text)
                            if m:
                                chapter_num += 1
                                title = m.group(2).strip() if len(m.groups()) >= 2 else text
                                chapters.append({
                                    "chapter_num": chapter_num,
                                    "title": title or f"Chapter {chapter_num}",
                                    "start_page": page_num + 1,
                                    "end_page": None,  # filled in below
                                    "page_count": None,
                                    "sections": [],
                                    "has_figures": False,
                                })
                                break

    # Fill in end pages
    for i, ch in enumerate(chapters):
        next_start = chapters[i + 1]["start_page"] - 1 if i + 1 < len(chapters) else total_pages
        ch["end_page"] = next_start
        ch["page_count"] = max(1, next_start - ch["start_page"] + 1)

    # If no chapters detected, treat entire book as one chapter
    if not chapters:
        chapters = [{
            "chapter_num": 1,
            "title": "Full Book",
            "start_page": 1,
            "end_page": total_pages,
            "page_count": total_pages,
            "sections": [],
            "has_figures": False,
        }]

    return chapters


def extract_chapter_text(pdf_path: str, start_page: int, end_page: int) -> dict[str, Any]:
    """
    Extract text from a chapter (1-indexed pages).
    Returns structured content: full text, sections, pages with figures.
    """
    fitz = _import_fitz()
    doc = fitz.open(pdf_path)

    # Convert to 0-indexed
    p_start = max(0, start_page - 1)
    p_end = min(doc.page_count - 1, end_page - 1)

    full_text_parts = []
    sections = []
    pages_with_figures = []
    current_section = None

    for page_idx in range(p_start, p_end + 1):
        page = doc[page_idx]
        page_num = page_idx + 1

        # Check for images/figures
        image_list = page.get_images()
        if image_list:
            pages_with_figures.append(page_num)

        blocks = page.get_text("dict")["blocks"]
        page_texts = []

        for block in blocks:
            if block["type"] == 0:  # text block
                for line in block.get("lines", []):
                    line_text = ""
                    is_section_heading = False
                    for span in line.get("spans", []):
                        text = span["text"]
                        flags = span.get("flags", 0)
                        size = span.get("size", 0)
                        is_bold = bool(flags & 2**4)
                        if size >= 12 and is_bold and len(text.strip()) > 3:
                            is_section_heading = True
                        line_text += text

                    line_text = line_text.strip()
                    if not line_text:
                        continue

                    if is_section_heading:
                        # Check if it's a section pattern
                        for pattern in _SECTION_PATTERNS:
                            m = pattern.match(line_text)
                            if m:
                                current_section = {"number": m.group(1), "title": m.group(2).strip(), "page": page_num}
                                sections.append(current_section)
                                break

                    page_texts.append(line_text)

            elif block["type"] == 1:  # image block
                page_texts.append(f"[FIGURE on page {page_num}]")

        full_text_parts.append(f"\n--- Page {page_num} ---\n" + "\n".join(page_texts))

    return {
        "full_text": "\n".join(full_text_parts),
        "sections": sections,
        "pages_with_figures": pages_with_figures,
        "start_page": start_page,
        "end_page": end_page,
        "page_count": p_end - p_start + 1,
    }
