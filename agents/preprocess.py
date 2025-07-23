import pymupdf  # PyMuPDF
import pytesseract
from pdf2image import convert_from_bytes

# Set OCR languages (English + Malay)
OCR_LANG = "eng+msa"

# 🔐 Extract text from text-based PDF
def extract_text_pdf(file_bytes: bytes) -> str:
    text = ""
    with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# 🔐 Extract text using OCR from image-based PDF (multi-language)
def extract_text_ocr(file_bytes: bytes) -> str:
    text = ""
    images = convert_from_bytes(file_bytes)
    # Log Total Pages
    print(f"Total pages to process: {len(images)}")

    for image in images:
        # Log Loop Iteration
        print(f"Processing image {images.index(image) + 1} of {len(images)}")
        text += pytesseract.image_to_string(image, lang=OCR_LANG)
    return text