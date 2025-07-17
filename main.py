# 📦 Unified Agentic Document Extractor API
# Handles text-based and image-based PDFs, processes them, and sends to LLM for Markdown output

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pymupdf  # PyMuPDF
import pytesseract
from pdf2image import convert_from_bytes
import requests
from groq import Groq
from utils.logger import logger
from datetime import datetime

app = FastAPI()
import os
from dotenv import load_dotenv

GROQ_API_KEY=your_key_here

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
# Set OCR languages (English + Malay)
OCR_LANG = "eng+msa"

# 🔐 Helper: Check if PDF is text-based or image-based
def is_pdf_text_based(file_bytes: bytes) -> bool:
    with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            if page.get_text().strip():
                return True
    return False

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

# 🔐 Send extracted text to Groq Cloud LLM for Markdown conversion
def convert_to_markdown(text: str) -> str:
    logger.info(f"Starting Markdown conversion for text of length: {len(text)}")

    prompt = f"Convert the following legal document into structured markdown for LLM to understand:\n\n{text}"

    res = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You are a markdown document formatter."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=2048
    )

    if res.choices[0].message.content:
        logger.info(f"Markdown conversion successful for text of length: {len(text)}")
        return res.choices[0].message.content
    else:
        logger.error(f"Markdown conversion failed for text of length: {len(text)}")
        return res.json().get("choices", [{}])[0].get("message", {}).get("content", "LLM failed to return markdown.")

# 🚀 Unified Endpoint
@app.post("/extract")
async def extract_markdown_from_pdf(file: UploadFile = File(...)):
    file_bytes = await file.read()
    start_time = datetime.now()
    logger.info(f"Started processing file: {file.filename}")
    try:
        # if is_pdf_text_based(file_bytes):
        #     extracted_text = extract_text_pdf(file_bytes)
        #     method = "text"
        # logger.info(f"PDF identified as text-based: {file.filename}")
        # else:
        extracted_text = extract_text_ocr(file_bytes)
        method = "ocr"
        logger.info(f"PDF identified as image-based: {file.filename}")

        markdown = convert_to_markdown(extracted_text)
        # markdown = extracted_text
        logger.info(f"Markdown conversion successful for: {file.filename}")


        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()
        logger.info(f"Completed processing {file.filename} in {elapsed_time:.2f} seconds")

        return JSONResponse({
            "filename": file.filename,
            "method": method,
            "markdown_preview": markdown 
        })

    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
