# Unified Agentic Document Extractor API
# Handles text-based and image-based PDFs, processes them, and sends to LLM for Markdown output

import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from utils.logger import logger
from datetime import datetime

# Import Agents
from agents.llm_extract import extract_with_rag
from agents.preprocess import is_pdf_text_based, extract_text_pdf, extract_text_ocr

app = FastAPI()

# Extract Markdown from PDF
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
        logger.info(f"PDF identified as image-based: {file.filename}")

        query = "Find borrower_name, borrower_registration_number, law_firm_postcode, bank_name, bank_registration_number, property_address"
        targeted_variables = "borrower_name, borrower_registration_number, law_firm_postcode, bank_name, bank_registration_number, property_address"

        markdown = extract_with_rag(extracted_text, query, targeted_variables)
        logger.info(f"Markdown conversion successful for: {file.filename}")

        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()
        logger.info(f"Completed processing {file.filename} in {elapsed_time:.2f} seconds")

        return markdown

        # return JSONResponse({
        #     "filename": file.filename,
        #     "markdown_preview": markdown 
        # })

    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == '__main__':
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True, log_level="debug")