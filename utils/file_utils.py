import pymupdf

def is_pdf_text_based(filepath: str) -> bool:
    doc = pymupdf.open(filepath)
    for page in doc:
        if page.get_text().strip():
            print(page.get_text())
            return True
    return False