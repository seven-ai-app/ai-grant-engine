"""Document parser - extracts text from PDF, DOCX, PPTX, and TXT files."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def parse_uploaded_files(file_paths: list[str]) -> list[dict]:
    """Parse uploaded files and extract text content.

    Supports: .pdf, .docx, .pptx, .txt, .md
    Returns a list of dicts with keys: filename, content, type
    """
    results = []
    for path in file_paths:
        try:
            content = ""
            ext = Path(path).suffix.lower()

            if ext == ".pdf":
                import PyPDF2
                with open(path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    content = "\n".join(
                        page.extract_text() or "" for page in reader.pages
                    )

            elif ext == ".docx":
                import docx
                doc = docx.Document(path)
                content = "\n".join(
                    p.text for p in doc.paragraphs if p.text.strip()
                )

            elif ext == ".pptx":
                from pptx import Presentation
                prs = Presentation(path)
                texts = []
                for slide_num, slide in enumerate(prs.slides, 1):
                    texts.append(f"--- Slide {slide_num} ---")
                    for shape in slide.shapes:
                        if hasattr(shape, "text") and shape.text.strip():
                            texts.append(shape.text.strip())
                content = "\n".join(texts)

            elif ext in (".txt", ".md"):
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

            else:
                logger.warning(f"Unsupported file type: {ext} ({path})")
                content = ""

            results.append({
                "filename": Path(path).name,
                "content": content[:15000],
                "type": ext,
            })

        except Exception as e:
            logger.error(f"Error parsing {path}: {e}")
            results.append({
                "filename": Path(path).name,
                "content": f"Error: {e}",
                "type": "error",
            })

    return results
