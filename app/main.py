# Unified Agentic Document Extractor API
# Handles text-based and image-based PDFs, processes them, and sends to LLM for Markdown output

import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from app.utils.logger import logger
from datetime import datetime
import shutil
import json

# Import Agents
from app.agents.llm_extract import extract_with_rag
from app.agents.preprocess import extract_text_ocr, pdf_to_images, filter_bank_copy
from app.agents.vlm_agent import smart_scan

app = FastAPI()

# Extract Markdown from PDF using RAG
# @app.post("/extract")
# async def extract_markdown_from_pdf(file: UploadFile = File(...)):
#     file_bytes = await file.read()
#     start_time = datetime.now()
#     logger.info(f"Started processing file: {file.filename}")
#     try:
#         extracted_text = extract_text_ocr(file_bytes)
#         logger.info(f"PDF identified as image-based: {file.filename}")

#         fields = [
#             "date",
#             "borrower_name",
#             "borrower_registration_number",
#             "borrower_address",
#             "bank_name",
#             "bank_address",
#             "bank_registration_number",
#             "subject of FA",
#             "total_loan_amount",
#             "gurantor_name",
#             "gurantor_nric",
#             "coporate_gurantor_name",
#             "coporate_gurantor_registration_number",
#             "coporate_gurantor_address",
#             "law_firm_name",
#             "law_firm_address",
#         ]

#         query = "Extract " + ", ".join(fields)
#         targeted_variables = ", ".join(fields)

#         markdown = extract_with_rag(extracted_text, query, targeted_variables)
#         logger.info(f"Markdown conversion successful for: {file.filename}")

#         end_time = datetime.now()
#         elapsed_time = (end_time - start_time).total_seconds()
#         logger.info(f"Completed processing {file.filename} in {elapsed_time:.2f} seconds")

#         return markdown

#     except Exception as e:
#         logger.error(f"Error processing file {file.filename}: {e}")
#         return JSONResponse(status_code=500, content={"error": str(e)})

# Extract Markdown from PDF using VLM
@app.post("/extract-vlm")
async def extract_markdown_VLM(file: UploadFile = File(...)):
    image_path='./pages'
    file_bytes = await file.read()
    start_time = datetime.now()
    logger.info(f"Started processing file: {file.filename}")
    try:
        # Convert PDFs to Images
        num_images = pdf_to_images(file_bytes, image_path)
        logger.info(f"Number of Images Converted: {num_images}")

        # Filter bank copy
        filter_bank_copy(image_path)

        # VLM Processing
        extracted_info = smart_scan()

        #  Delete image after processing
        try:
            shutil.rmtree('./pages')
            logger.info(f"Deleted of Images Path: {image_path}")
        except Exception as e:
            print(f"Error deleting {image_path}: {e}")


        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()
        logger.info(f"Completed processing {file.filename} in {elapsed_time:.2f} seconds")

        # Format the extracted information
        formatted_info = {
            "ref_no": extracted_info.get("ref_no", ""),
            "date": extracted_info.get("date", ""),
            "open_date": extracted_info.get("open_date", ""),
            "close_date": extracted_info.get("close_date", ""),
            "borrower_name": extracted_info.get("borrower_name", ""),
            "borrower_registration_number": extracted_info.get("borrower_registration_number", ""),
            "borrower_address": extracted_info.get("borrower_address", ""),
            "bank_name": extracted_info.get("bank_name", ""),
            "bank_address": extracted_info.get("bank_address", ""),
            "bank_registration_number": extracted_info.get("bank_registration_number", ""),
            "subject_matter": extracted_info.get("subject_of_FA", ""),
            "total_loan_amount": extracted_info.get("total_loan_amount", ""),
            "gurantor_name": extracted_info.get("gurantor_name", ""),
            "gurantor_nric": extracted_info.get("gurantor_nric", ""),
            "coporate_gurantor_name": extracted_info.get("coporate_gurantor_name", ""),
            "coporate_gurantor_registration_number": extracted_info.get("coporate_gurantor_registration_number", ""),
            "law_firm_name": extracted_info.get("law_firm_name", ""),
            "law_firm_address": extracted_info.get("law_firm_address", ""),
            "property_description": extracted_info.get("property_title", ""),
            "property_address": extracted_info.get("property_address", ""),
            "property_price": extracted_info.get("property_price", "")
        }

        with open("structured_fields.json", "w") as f:
            json.dump(formatted_info, f, indent=2)
        logger.info("Final merged result saved to structured_fields.json")
        return json.dumps(formatted_info, indent=2)

    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == '__main__':
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True, log_level="debug")