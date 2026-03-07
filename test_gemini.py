import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv('backend/.env')
api_key = os.getenv('GEMINI_API_KEY')
print(f"Testing API Key: {api_key[:10]}...")

genai.configure(api_key=api_key)
try:
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content="Hello world",
        task_type="retrieval_document",
    )
    print(f"Embedding successful! Vector length: {len(result['embedding'])}")
except Exception as e:
    print(f"Error: {e}")
