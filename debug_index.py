import os
import sys
import traceback

sys.path.append(os.path.join(os.getcwd(), "backend"))

from dotenv import load_dotenv
load_dotenv('backend/.env')

from services.rag_service import index_pdf

pdf_path = "backend/data/materi/keupublik.pdf"
print(f"Indexing {pdf_path}...")
try:
    count = index_pdf(pdf_path, "bab1")
    print(f"Success! Indexed {count} chunks.")
except Exception as e:
    print(f"FAILED with error: {e}")
    if hasattr(e, 'message'):
        print(f"Error Message: {e.message}")
    else:
        print(f"Error Args: {e.args}")
