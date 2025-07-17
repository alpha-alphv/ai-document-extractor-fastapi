import requests
from typing import Dict, List
from pydantic import BaseModel

# Define input and expected schema
class ExtractionRequest(BaseModel):
    text: str
    fields: List[str]  # e.g., ["Effective Date", "Party A", "Party B"]

class ExtractionResponse(BaseModel):
    status: str
    extracted: Dict[str, str]
    raw_output: str

# Build the prompt
def build_prompt(text: str, fields: List[str]) -> str:
    field_list = "\n".join([f"- {f}" for f in fields])
    return f"""You are a legal document analyzer.
Extract the following fields from the document below:
{field_list}

Document:
\"\"\"
{text}
\"\"\"

Return ONLY the following JSON format:
{{
{", ".join([f'"{f}": "..."' for f in fields])}
}}"""

# Query local LLM (Ollama here, modify URL if needed)
def call_local_llm(prompt: str) -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
        }
    )
    return response.json()["response"]
