"""BM25 keyword search across concepts, notes, misconceptions, and quiz history."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from scripts.teach.concepts import get_all_concepts
from scripts.teach.misconceptions import get_misconceptions
from scripts.teach.quiz import get_quiz_history


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _read_notes_text(book_path: Path) -> list[dict]:
    """Load all .tex note files as searchable documents."""
    notes_dir = book_path / "notes"
    docs = []
    if not notes_dir.exists():
        return docs
    for f in notes_dir.glob("*.tex"):
        try:
            content = f.read_text()
            docs.append({"source": f"notes/{f.name}", "text": content})
        except OSError:
            pass
    return docs


def search(book_path: Path | str, query: str, limit: int = 10) -> list[dict]:
    """BM25 search across the knowledge base. Returns ranked results."""
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        return [{"error": "rank-bm25 not installed: pip install rank-bm25"}]

    book_path = Path(book_path)

    # Build corpus
    documents: list[dict] = []

    # Concepts
    for cid, concept in get_all_concepts(book_path).items():
        text = " ".join([
            concept.get("name", ""),
            concept.get("definition", ""),
            concept.get("intuition", ""),
            " ".join(concept.get("examples", [])),
            " ".join(concept.get("keywords", [])),
        ])
        documents.append({"source": f"concept:{cid}", "title": concept.get("name", cid), "text": text})

    # Notes files
    documents.extend(_read_notes_text(book_path))

    # Misconceptions
    for m in get_misconceptions(book_path):
        documents.append({"source": f"misconception:{m['id']}", "title": "Misconception", "text": m["text"]})

    if not documents:
        return []

    corpus = [_tokenize(d["text"]) for d in documents]
    bm25 = BM25Okapi(corpus)

    query_tokens = _tokenize(query)
    scores = bm25.get_scores(query_tokens)

    ranked = sorted(zip(scores, documents), key=lambda x: x[0], reverse=True)

    results = []
    for score, doc in ranked[:limit]:
        if score > 0:
            results.append({
                "source": doc.get("source"),
                "title": doc.get("title", doc.get("source", "")),
                "score": round(float(score), 4),
                "snippet": doc["text"][:300].replace("\n", " "),
            })

    return results
