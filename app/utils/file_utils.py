import pymupdf
import json
import re

def parse_and_sanitize(content):
    try:
        parsed = json.loads(content)
        return "[]" if isinstance(parsed, list) else ""
    except json.JSONDecodeError:
        return ""

def safe_json_parse(raw_content):
    try:
        # Step 1: Remove Markdown like ```json or ```
        clean = re.sub(r"```(json)?", "", raw_content).strip()

        # Step 2: Try parsing
        return json.loads(clean)
    except json.JSONDecodeError as e:
        print("JSON parsing failed:", e)
        print("Original content:", raw_content[:500])
        return None

def merge_dicts(list_of_dicts):
    merged = {}

    # Step 1: Collect all values
    for d in list_of_dicts:
        for k, v in d.items():
            if k not in merged:
                # Initialize as list
                merged[k] = []

            if isinstance(v, list):
                new_items = [item.strip() for item in v if isinstance(item, str) and item.strip()]
            elif isinstance(v, str) and v.strip():
                new_items = [v.strip()]
            else:
                new_items = []

            for item in new_items:
                if item not in merged[k]:
                    merged[k].append(item)

    # Step 2: Post-process: convert single-item lists to string, else keep list
    for k, v in merged.items():
        if isinstance(v, list):
            if len(v) == 1:
                merged[k] = v[0]  # Convert to string
            elif len(v) == 0:
                merged[k] = []  # Keep as empty list

    return merged

