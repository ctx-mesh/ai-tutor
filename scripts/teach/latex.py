"""pdflatex compilation — wraps the system pdflatex command."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def is_pdflatex_available() -> bool:
    return shutil.which("pdflatex") is not None


def compile_latex(tex_path: str | Path) -> dict:
    """
    Compile a .tex file to .pdf using pdflatex.
    Runs twice to resolve cross-references.
    Returns {"pdf_path": str} on success or {"error": str} on failure.
    """
    tex_path = Path(tex_path)
    if not tex_path.exists():
        return {"error": f"File not found: {tex_path}"}

    if not is_pdflatex_available():
        return {
            "error": "pdflatex not found. Install TeX Live or MiKTeX to compile PDFs.",
            "tex_path": str(tex_path),
            "note": "The .tex file was generated successfully and can be compiled manually.",
        }

    output_dir = tex_path.parent
    cmd = [
        "pdflatex",
        "-interaction=nonstopmode",
        "-output-directory", str(output_dir),
        str(tex_path),
    ]

    try:
        # Run twice for cross-references
        for _ in range(2):
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

        pdf_path = tex_path.with_suffix(".pdf")
        if pdf_path.exists():
            return {"pdf_path": str(pdf_path), "tex_path": str(tex_path)}
        else:
            return {
                "error": "pdflatex ran but PDF was not produced.",
                "stdout": result.stdout[-2000:] if result.stdout else "",
                "stderr": result.stderr[-1000:] if result.stderr else "",
            }

    except subprocess.TimeoutExpired:
        return {"error": "pdflatex timed out after 60 seconds."}
    except Exception as e:
        return {"error": f"Compilation failed: {e}"}
