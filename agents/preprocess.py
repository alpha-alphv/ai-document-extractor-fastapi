import pymupdf  # PyMuPDF
import pytesseract
from pdf2image import convert_from_bytes
import os

# Set OCR languages (English + Malay)
OCR_LANG = "eng+msa"

# Extract text from text-based PDF
def extract_text_pdf(file_bytes: bytes) -> str:
    text = ""
    with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# Extract text using OCR from image-based PDF (multi-language)
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

# Convert each pages into images and store in directory ./pages
def pdf_to_images(file_bytes: bytes, output_dir='./pages'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    num_images = 0

    # Use Matrix for zoom (increasing DPI)
    zoom_matrix = pymupdf.Matrix(4.0, 4.0)
    for page_num in range(len(doc)):
        print(f"Processing page {num_images + 1} of {len(doc)}")
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=zoom_matrix)
        pix.save(f"{output_dir}/page_{page_num + 1}.png")
        num_images += 1
    doc.close()
    return num_images