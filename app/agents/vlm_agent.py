import base64
import os
import json
import ollama
from app.utils.logger import logger
from app.utils.file_utils import safe_json_parse, merge_dicts
from app.agents.agent_config import get_bank_name, page_fields_mapping
from app.agents.preprocess import filter_and_rename_pages
import re

# List of fields to extract
fields = {
    "date": "",
    "borrower_name": "",
    "borrower_registration_number": "",
    "borrower_address": "",
    "bank_name": "",
    "bank_address": "",
    "bank_registration_number": "",
    "subject_of_FA": [],
    "total_loan_amount": "",
    "guarantor_name": [], 
    "guarantor_nric": [], 
    "corporate_guarantor_name": [],  
    "corporate_guarantor_registration_number": [],
    "law_firm_name": "",
    "law_firm_address": "",
    "property_title": "",
    "property_address": []
}

image_folder = "./pages/filtered"
model_name = "qwen2.5vl:7b"

# Final schema to fill
final_result = fields.copy()

system_prompt = (
    "You are a multilingual document extraction assistant. "
    "Extract structured information in English even if the document includes multiple languages like Malay. "
    "Return a JSON object with the following fields. If a value is not found, return an empty string or an empty list.\n\n"
    
    "Field Notes:\n"
    "- 'borrower_name' typically appears above 'borrower_address'.\n"
    "- 'total_loan_amount' typically is the biggest amount in subject_of_FA. Compare with other 'loan_amount' to ensure accuracy.\n"
    "- 'total_loan_amount' should not included in 'subject_of_FA'. Compare with other 'loan_amount' to ensure accuracy.\n"
    "- 'guarantor_name' and 'guarantor_nric' refer to individual people (personal guarantors). There may be more than one. Extract all as lists.\n"
    "- 'corporate_guarantor_name', 'corporate_guarantor_registration_number', and 'corporate_guarantor_address' refer to corporate entities (companies). A corporate guarantor will usually have 'Sdn Bhd' in its name. There may be more than one. Extract all as lists.\n"
    "-  'property_title' should capture all lines and details before the next section starts, preserving multiple lines.\n"
    "- 'property_address' may have multiple values. Return all as a list.\n"
    "- 'subject_of_FA' may have multiple values. It should follow the format: <Loan Type> (<Code>) - RM<amount>, e.g., 'Overdraft (OD) - RM2,000,000'.\n\n"
    
    "Important:\n"
    "- Return a valid JSON object with only the expected field names.\n"
    "- Do not return any explanations, formatting, or markdown—just the JSON output."
)


def smart_scan():
    per_page_results = []

    bank_name = get_bank_name()

    filter_and_rename_pages(bank_name)

    page_fields_map = page_fields_mapping(bank_name)

    if page_fields_map is None:
        logger.error(f"No page mapping found for bank: '{bank_name}'")
        return {}

    images = [f for f in os.listdir(image_folder) if f.lower().endswith('.png')]
    images.sort(key=lambda x: int(re.search(r'_(\d+)', x).group(1)) if re.search(r'_(\d+)', x) else 0)

    for key in page_fields_map:
        base_key = key.replace('.png', '')
        pattern = re.compile(rf'^{re.escape(base_key)}(?:_(\d+))?\.png$')
        matching_files = sorted([f for f in images if pattern.match(f)],
                                key=lambda x: int(pattern.match(x).group(1) or 0))
        
        if not matching_files:
            logger.info(f"No files found for key: {key}")
            continue
        
        fields_to_extract = page_fields_map[key]
        for img_name in matching_files:
            logger.info(f"Processing image: {img_name}")
            image_path = os.path.join(image_folder, img_name)
            if not os.path.exists(image_path):
                logger.warning(f"Image not found: {image_path}")
                continue
            with open(image_path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode("utf-8")

            user_prompt = f"""
            You are extracting structured data from a loan document.
            Extract the following fields **and return them as a valid JSON object**. Each field should match its key.
            Important Notes:
            - Fields like 'guarantor_name', 'guarantor_nric', 'corporate_guarantor_name' and 'property_address' can have multiple values. Return them as arrays.
            - If a field is missing, return an empty string for text, or an empty array for lists.
            - Do NOT just return a list. Always return a JSON object with the correct field names.
            Fields to extract:
            {json.dumps(fields_to_extract, indent=2)}
            Example valid output:
            {{
                "borrower_registration_number": "23932230923 (0931-B)",
                "law_firm_name": "Abraham Ooi & Partners",
                "law_firm_address": "28-b & 30-b, 2nd Floor, Jalan Ss 21/62, Damansara Utama Petaling Jaya, 47400 Petaling Jaya, Selangor",
                "date": "6 November 2024",
                "borrower_name": "Robert Dass",
                "borrower_address": "BL 13A-05, Zeva Residence, Persiaran Pinggiran Putra, Pinggiran Putra Permai, 43300 Seri Kembangan, Selangor, MALAYSIA",
                "bank_name": "PUBLIC BANK BERHAD",
                "bank_address": "62, 64 & 66, Jalan Tapah, Off Jalan Goh Hock Huat, 41400 Klang, Selangor.",
                "bank_registration_number": "196501000672 (6463-H)",
                "subject_of_FA": [
                    "HL/HOME10 (Redraw) (PromoUC) - RM40, 000.00",
                    "MRTA (inclusive of PB Term CI) - RM1,000,620.00"
                ],
                "total_loan_amount": "RM1,100,620.00",
                "property_title": "Individual Title ABC 0000, Lot 2, Jalan BSC 6A/2 Precinct 6A1 Type B2 Jardin Residences, 45000 Kuala Selangor",
                "property_address": [
                    "49, Jalan BSC 6A/2 Precinct 6A1 Type B2 Jardin Residences, 45000 Kuala Selangor"
                ],
                "guarantor_name": ["Ali bin Abu", "Alex Lim"],
                "guarantor_nric": ["038889384756", "9983484756431"],
                "corporate_guarantor_name": ["ABC Sdn Bhd", "DEF Sdn Bhd"],
                "corporate_guarantor_registration_number": ["20394456621", "30495563313"],
            }}
            Only return the JSON. Do not explain.
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
                raw_output = response.get("message", {}).get("content", "")
                logger.info(f"Raw LLM response from {img_name}: {raw_output}")
                if not raw_output.strip() or "nothing" in raw_output.lower() or "not found" in raw_output.lower():
                    logger.info(f"No useful data extracted from {img_name}, skipping.")
                    continue
                parsed = safe_json_parse(raw_output)
                per_page_results.append(parsed)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from {img_name}")
            except Exception as e:
                logger.error(f"Error extracting from {img_name}: {e}")

    print(per_page_results)
    final_result = merge_dicts(per_page_results)
    with open("structured_fields.json", "w") as f:
        json.dump(final_result, f, indent=2)
    logger.info("Final merged result saved to structured_fields.json")
    return final_result
