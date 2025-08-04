from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
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
    # Split text into small chunks for faster retrieval (Traditional Chunking)
    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=80)
    # chunks = text_splitter.split_text(text)

    # multilingual embeddings
    # embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    # embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/stsb-xlm-r-multilingual", model_kwargs={"device": "cuda"})
    embeddings = HuggingFaceEmbeddings(model_name="Qwen/Qwen3-Embedding-4B", model_kwargs={"device": "cuda"})   

    # embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3", model_kwargs={"device": "cuda"}) 
    chunker = SemanticChunker(embeddings, breakpoint_threshold_type="percentile", breakpoint_threshold_amount=0.85)
    
    chunks = chunker.split_text(text)
    # Create FAISS index
    vector_store = FAISS.from_texts(chunks, embeddings)
    logger.info(f"Vector store created in {time.time() - start_time:.2f} seconds")
    return vector_store, chunks

def extract_with_rag(text: str, query: str, targeted_variables: str) -> dict:
    logger.info(f"Starting RAG extraction for text of length: {len(text)}")
    start_time = time.time()
    # Create vector store
    dense_store, chunks = create_vector_store(text)
    dense_retriever = dense_store.as_retriever(search_kwargs={"k": 12})

    # Sparse retriever
    sparse_retriever = BM25Retriever.from_texts(chunks, k=12)

    # Hybrid Search Retriever
    hybrid_retriever = EnsembleRetriever(retrievers=[dense_retriever, sparse_retriever], weights=[0.3, 0.7])

    # Retrieve relevant chunks using hybrid
    relevant_chunks = hybrid_retriever.get_relevant_documents(query)

    # Retrieve relevant chunks
    # relevant_chunks = vector_store.similarity_search(query, k=10)
    context = "\n".join([chunk.page_content for chunk in relevant_chunks])
    logger.info(f"Context retrieved in {time.time() - start_time:.2f} seconds")
    logger.info(f"Retrieved context: {context[:50000]}...")  # Log first 500 chars

# Put example in prompt
    prompt = f"""
        You are a law firm analyst AI tasked with extracting specific law variables from a document. The document content will be provided to you, 
        which may include text, images, or a combination of both. Your task is to carefully analyze this content and extract the requested information. 
        Here is the tips:

        a. Corporate Gurantor is Company Based. For example, 'company SDN BHD'
        b. Gurantor is people, it can be multiple of it.
        c. Date normally included in bank's notice section
        d. Total_loan_amount normally taken from The FA (Facility Agreement) in bank's notice section
        e. The bank details can be taken in bank's notice section
        f. The bank registration number should be in this format: "129821989233 (139421-P)". Do not rephrase and split it by ",".
        g. Subject of FA (Facility Agreement) must include price limit, it can be multiple of it and must follow the specific format. For example, Overdraft(OD)-RM2,000,000.00

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
            model="qwen3:8b",  
            messages=[
                {"role": "system", "content": "You are a precise data extraction tool for legal documents. Return only JSON, no other text."},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.3, "max_tokens": 2048}
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