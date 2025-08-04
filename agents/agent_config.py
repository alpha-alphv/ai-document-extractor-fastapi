from utils.logger import logger
import ollama
import base64
import os

image_folder = "./pages"
model_name = "qwen2.5vl:7b"

def get_bank_name():
    logger.info("Define which bank is this ...")

    for i in range(4, 5):  # Typically on page 4
        logger.info(f"Go to page {i}...")
        image_path = os.path.join(image_folder, f"page_{i}.png")

        if not os.path.exists(image_path):
            logger.warning(f"Image not found: {image_path}")
            continue

        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        user_prompt = f"""
        You are an AI assistant helping to extract the bank name from a loan document.
        Your task is to output ONLY the bank name as plain text. Example answers: CIMB Bank Berhad, Maybank, RHB Bank, etc.
        """

        system_prompt = """
        You are a document analysis assistant. Your task is to extract only the bank name from an official loan document. 
        The document may contain multiple entities and legal language, but your goal is to find and return only the bank name mentioned.

        Output format:
        Just return the bank name as a plain string, with no labels, no extra formatting, and no explanations.

        Examples of valid outputs:
        - CIMB Bank Berhad
        - Maybank Berhad
        - RHB Bank
        - Public Bank Berhad

        If no bank name is found on the page, return an empty string.
        """

        try:
            response = ollama.chat(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": user_prompt,
                        "images": [image_b64]
                    }
                ],
                options={"temperature": 0.3, "max_tokens": 2048}
            )
            # Assume response is plain text or dict with field
            content = response.get("message", {}).get("content")
            if content:
                content = content.strip()
                return content
            else:
                logger.warning("No content returned from model.")
                return ""

        except Exception as e:
            logger.warning(f"Failed to extract bank name from page {i}: {e}")

    return ""

def page_fields_mapping(bank_name: str):
    bank_field_mappings = {
        "PUBLIC BANK BERHAD": {
            "page_fields_map": {
                1: ["borrower_registration_number"],
                3: ["law_firm_name", "law_firm_address"],
                4: [
                    "date", "borrower_name", "borrower_address",
                    "bank_name", "bank_address", "bank_registration_number"
                ],
                7: [
                    "subject_of_FA", "total_loan_amount"
                ],
                9: [
                    "property_title", "property_address"
                ]
            },
            "stamp_required": False
        },
        "CIMB BANK BERHAD": {
            "page_fields_map": {
                2: ["date"],
                3: ["law_firm_name", "law_firm_address"],
                4: [
                    "borrower_name", "borrower_registration_number", "borrower_address",
                    "bank_name", "bank_address", "bank_registration_number",
                    "subject_of_FA", "total_loan_amount"
                ],
                8: [
                    "guarantor_name", "guarantor_nric",
                    "corporate_guarantor_name", "corporate_guarantor_registration_number"
                ]
            },
            "stamp_required": False
        },
        "MAYBANK ISLAMIC BERHAD": {
            "page_fields_map": {
                1: ["borrower_registration_number"],
                2: ["borrower_name", "borrower_address"],
                3: ["law_firm_name", "law_firm_address"],
                4: [
                    "date",
                    "bank_name", "bank_address", "bank_registration_number",
                    "subject_of_FA", "total_loan_amount"
                ],
                5: [
                    "property_title","property_address"
                ]
            },
            "stamp_required": False
        },
        "MALAYAN BANKING BERHAD": {
            "page_fields_map": {
                1: ["borrower_registration_number"],
                2: ["borrower_name", "borrower_address"],
                3: ["law_firm_name", "law_firm_address"],
                4: [
                    "date", "bank_name", "bank_address", "bank_registration_number",
                    "subject_of_FA", "total_loan_amount"
                ],
                5: [
                    "guarantor_name", "guarantor_nric",
                    "corporate_guarantor_name", "corporate_guarantor_registration_number",
                    "corporate_guarantor_address"
                ]
            },
            "stamp_required": False
        },
    }
    targeted_bank = bank_field_mappings.get(bank_name.upper())
    if targeted_bank:
        return targeted_bank["page_fields_map"]
    return None