from app.utils.logger import logger
import ollama
import base64
import os

image_folder = "./pages/filtered"
model_name = "qwen2.5vl:7b"

def get_bank_name(page_name="bank_copy"):
    logger.info(f"Extracting bank name from {page_name}...")
    image_path = os.path.join("./pages", f"{page_name}.png")
    if not os.path.exists(image_path):
        logger.warning(f"Image not found: {image_path}")
        return ""
    
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    system_prompt = """
    You are a document analysis assistant tasked with extracting the bank name from an official loan document.
    Return only the bank name as a plain string, with no labels, formatting, or explanations.
    Examples: CIMB Bank Berhad, Maybank Berhad, RHB Bank, Public Bank Berhad
    If no bank name is found, return an empty string.
    """
    
    user_prompt = """
    Extract the bank name from the provided loan document page. Output ONLY the bank name as plain text.
    """
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt, "images": [image_b64]}
            ],
            options={"temperature": 0.3, "max_tokens": 2048}
        )
        content = response.get("message", {}).get("content", "").strip()
        if content:
            return content
        logger.warning("No bank name found.")
        return ""
    except Exception as e:
        logger.warning(f"Error extracting bank name from {page_name}: {e}")
        return ""

def page_fields_mapping(bank_name: str):
    bank_field_mappings = {
        "CIMB BANK BERHAD": {
            "page_fields_map": {
                "bank_copy": ["date", "borrower_name", "borrower_registration_number", "borrower_address",
                              "bank_name", "bank_address", "bank_registration_number"],
                "law_firm_details": ["law_firm_name", "law_firm_address"],
                "subject_of_fa": ["subject_of_FA", "total_loan_amount"],
                "guarantor_details": ["guarantor_name", "guarantor_nric",
                                      "corporate_guarantor_name", "corporate_guarantor_registration_number"],
                "property_details": ["property_title", "property_address"]
            },
            "stamp_required": False
        },
        "CIMB ISLAMIC BANK BERHAD": {
            "page_fields_map": {
                "bank_copy": ["date", "borrower_name", "borrower_registration_number", "borrower_address",
                              "bank_name", "bank_address", "bank_registration_number"],
                "law_firm_details": ["law_firm_name", "law_firm_address"],
                "subject_of_fa": ["subject_of_FA", "total_loan_amount"],
                "guarantor_details": ["guarantor_name", "guarantor_nric",
                                      "corporate_guarantor_name", "corporate_guarantor_registration_number"],
                "property_details": ["property_title", "property_address"]
            },
            "stamp_required": False
        },
        "MAYBANK BERHAD": {
            "page_fields_map": {
                "bank_copy": ["date", "borrower_name", "borrower_registration_number", "borrower_address",
                              "bank_name", "bank_address", "bank_registration_number"],
                "law_firm_details": ["law_firm_name", "law_firm_address"],
                "subject_of_fa": ["subject_of_FA", "total_loan_amount"],
                "guarantor_details": ["guarantor_name", "guarantor_nric",
                                      "corporate_guarantor_name", "corporate_guarantor_registration_number"],
                "property_details": ["property_title", "property_address"]
            },
            "stamp_required": False
        },
        "RHB BANK BERHAD": {
            "page_fields_map": {
                "bank_copy": ["date", "borrower_name", "borrower_registration_number", "borrower_address",
                              "bank_name", "bank_address", "bank_registration_number"],
                "law_firm_details": ["law_firm_name", "law_firm_address"],
                "subject_of_fa": ["subject_of_FA", "total_loan_amount"],
                "guarantor_details": ["guarantor_name", "guarantor_nric",
                                      "corporate_guarantor_name", "corporate_guarantor_registration_number"],
                "property_details": ["property_title", "property_address"]
            },
            "stamp_required": False
        },
        "PUBLIC BANK BERHAD": {
            "page_fields_map": {
                "bank_copy": ["date", "borrower_name", "borrower_registration_number", "borrower_address",
                              "bank_name", "bank_address", "bank_registration_number"],
                "law_firm_details": ["law_firm_name", "law_firm_address"],
                "subject_of_fa": ["subject_of_FA", "total_loan_amount"],
                "guarantor_details": ["guarantor_name", "guarantor_nric",
                                      "corporate_guarantor_name", "corporate_guarantor_registration_number"],
                "property_details": ["property_title", "property_address"]
            },
            "stamp_required": False
        }
    }
    targeted_bank = bank_field_mappings.get(bank_name.upper())
    if targeted_bank:
        return targeted_bank["page_fields_map"]
    return None