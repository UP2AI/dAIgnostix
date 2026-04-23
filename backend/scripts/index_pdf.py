"""
Standalone script for batch indexing PDFs into Supabase pgvector.

Usage:
    cd backend
    python scripts/index_pdf.py
"""
import os
import sys

# Add parent dir to path so imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from services.rag_service import index_all_pdfs


def main():
    pdf_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "materi")

    print("🔄 Memulai indexing PDF ke Supabase pgvector...")
    print(f"📁 Folder: {pdf_dir}")

    if not os.path.exists(pdf_dir):
        print(f"❌ Folder {pdf_dir} tidak ditemukan!")
        print("   Buat folder dan taruh file PDF materi di dalamnya.")
        return

    results = index_all_pdfs(pdf_dir)

    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return

    total = sum(results.values())
    print(f"\n✅ Indexing selesai!")
    print(f"📊 Total: {total} chunks dari {len(results)} file")
    for filename, count in results.items():
        print(f"   📄 {filename}: {count} chunks")


if __name__ == "__main__":
    main()
