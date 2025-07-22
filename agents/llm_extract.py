from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import ollama
import json
import logging
import time

logger = logging.getLogger(__name__)

def create_vector_store(text: str) -> FAISS:
    start_time = time.time()
    # Split text into small chunks for faster retrieval
    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=80)
    # chunks = text_splitter.split_text(text)

    # Use lightweight multilingual embeddings for speed
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    # embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/stsb-xlm-r-multilingual")
    chunker = SemanticChunker(embeddings, breakpoint_threshold_type="percentile", breakpoint_threshold_amount=0.95)
    chunks = chunker.split_text(text)
    # Create FAISS index
    vector_store = FAISS.from_texts(chunks, embeddings)
    logger.info(f"Vector store created in {time.time() - start_time:.2f} seconds")
    return vector_store

def extract_with_rag(text: str, query: str, targeted_variables: str) -> dict:
    logger.info(f"Starting RAG extraction for text of length: {len(text)}")
    start_time = time.time()
    # Create vector store
    vector_store = create_vector_store(text)
    # Retrieve relevant chunks
    relevant_chunks = vector_store.similarity_search(query, k=10)
    context = "\n".join([chunk.page_content for chunk in relevant_chunks])
    logger.info(f"Context retrieved in {time.time() - start_time:.2f} seconds")
    logger.info(f"Retrieved context: {context[:50000]}...")  # Log first 500 chars

    prompt = f"""
        You are a financial analyst AI tasked with extracting specific financial variables from a document. The document content will be provided to you, which may include text, images, or a combination of both. Your task is to carefully analyze this content and extract the requested information.

        {context}

        Please include the value, and the targeted variable's name.
        {{
        "targeted_variable_name": "value",
        }}

        Format your answer as an array of JSON objects. If you don't know the answer, add N/A as your response. Please don't include anything else in your response.

        What are the values for the following?

        {targeted_variables}
    """

    try:
        response = ollama.chat(
            model="qwen3:8b",  # Qwen for precise JSON generation
            messages=[
                {"role": "system", "content": "You are a precise data extraction tool for legal documents. Return only JSON, no other text."},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.2, "max_tokens": 2048}
        )
        raw_content = response.get("message", {}).get("content", "")
        logger.info(f"Raw LLM response: {raw_content}")

        if raw_content.strip():
            logger.info(f"RAG extraction completed in {time.time() - start_time:.2f} seconds")
            return json.loads(raw_content)
        else:
            logger.error(f"RAG extraction failed: empty response")
            return {"inference_result": {}}
    except Exception as e:
        logger.error(f"RAG extraction failed: {str(e)}")
        return {"inference_result": {}, "error": str(e)}