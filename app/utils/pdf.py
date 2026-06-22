from pathlib import Path
import fitz
import pytesseract
from PIL import Image



def extract_text_from_pdf(file_path: Path) -> str:
    
    text_output = ""

    with fitz.open(file_path) as doc:
        for page in doc:
            text_output += page.get_text()

    text_output = text_output.strip()

    # Normal PDF text exists
    if len(text_output) > 50:
        return text_output

    # OCR fallback
    return _ocr_pdf(file_path)


def _ocr_pdf(file_path: Path) -> str:


    result = []

    doc = fitz.open(file_path)

    for page_no, page in enumerate(doc, start=1):

        pix = page.get_pixmap(
            dpi=300
        )

        img = Image.frombytes(
            "RGB",
            [pix.width, pix.height],
            pix.samples
        )

        text = pytesseract.image_to_string(img)

        result.append(
            f"\n--- Page {page_no} ---\n{text}"
        )

    return "\n".join(result).strip()
