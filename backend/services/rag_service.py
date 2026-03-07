"""
RAG Service — PDF parsing, text chunking, embedding, and pgvector search.
Uses Google Embedding API + Supabase pgvector.
"""
import os
import google.generativeai as genai
from config import GEMINI_API_KEY
from services.db_service import insert_chunk, search_chunks

genai.configure(api_key=GEMINI_API_KEY)


def _get_embedding(text: str) -> list:
    """Get embedding vector for a single text using Google Embedding API."""
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]


def _get_query_embedding(text: str) -> list:
    """Get embedding for a query (retrieval_query task type)."""
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_query",
    )
    return result["embedding"]


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks


def index_pdf(filepath: str, bab: str = "") -> int:
    """
    Parse a PDF file, chunk the text, embed each chunk,
    and store in Supabase pgvector.
    Returns the number of chunks indexed.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(filepath)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()

    # Clean text
    full_text = full_text.replace("\x00", "")

    # Chunk
    from config import CHUNK_SIZE, CHUNK_OVERLAP
    chunks = _chunk_text(full_text, CHUNK_SIZE, CHUNK_OVERLAP)

    # Embed and store
    filename = os.path.basename(filepath)
    for i, chunk_text in enumerate(chunks):
        embedding = _get_embedding(chunk_text)
        metadata = {
            "source_file": filename,
            "bab": bab or filename.split("_")[0],
            "chunk_index": i,
        }
        insert_chunk(content=chunk_text, metadata=metadata, embedding=embedding)

    return len(chunks)


def index_all_pdfs(pdf_dir: str = "./data/materi") -> dict:
    """Index all PDFs in a directory. Returns summary of chunks per file."""
    results = {}
    if not os.path.exists(pdf_dir):
        return {"error": f"Directory {pdf_dir} does not exist"}

    for filename in sorted(os.listdir(pdf_dir)):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(pdf_dir, filename)
            bab = filename.split("_")[0]  # e.g., "bab1"
            count = index_pdf(filepath, bab)
            results[filename] = count

    return results


def query_materi(query: str, k: int = 10) -> str:
    """
    Query relevant materi chunks from pgvector.
    Returns concatenated context string.
    """
    query_vector = _get_query_embedding(query)
    results = search_chunks(query_vector, k)
    if not results:
        return ""
    context = "\n\n---\n\n".join([doc["content"] for doc in results])
    return context
