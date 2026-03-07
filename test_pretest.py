import os
import sys
import traceback
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from dotenv import load_dotenv

load_dotenv('backend/.env')

from backend.services.db_service import get_user, get_pretest, save_pretest
from backend.services.rag_service import query_materi
from backend.services.ai_service import generate_pretest_questions

try:
    nip = "199503292016121001"
    
    print("Getting user...")
    user = get_user(nip)
    if not user:
        print("User not found")
        sys.exit(1)
        
    print("Getting pretest from db...")
    existing = get_pretest(nip)
    if existing:
        print("Pretest already exists")
        sys.exit(0)
        
    print("Querying materi...")
    context = query_materi("materi audit internal keuangan negara lengkap semua bab", k=15)
    print(f"Context loaded (length: {len(context)})")
    
    if not context:
        print("No context found")
        sys.exit(1)
        
    print("Generating pretest questions...")
    soal = generate_pretest_questions(context)
    print(f"Successfully generated {len(soal)} questions")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()
