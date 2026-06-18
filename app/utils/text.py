import re


def split_into_paragraphs(text: str) -> list[str]:
    """Split raw text into non-trivial paragraphs."""
    chunks = re.split(r"\n\s*\n|(?<=\.)\s+(?=[A-Z])", text)
    return [chunk.strip() for chunk in chunks if len(chunk.strip()) > 20]


def find_best_paragraph(text: str, keyword: str) -> str:
    """Return the first paragraph containing *keyword* (case-insensitive)."""
    keyword_lower = keyword.lower()
    for para in split_into_paragraphs(text):
        if keyword_lower in para.lower():
            return para[:1000]
    return ""
