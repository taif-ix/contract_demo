from pathlib import Path

import fitz


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract all text from a PDF, page by page."""
    text_output = ""
    with fitz.open(file_path) as doc:
        for page_no, page in enumerate(doc, start=1):
            text_output += f"\n--- Page {page_no} ---\n{page.get_text()}"
    return text_output.strip()
