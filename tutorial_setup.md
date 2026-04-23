# 🛠️ Tutorial Lengkap: Setup Backend E-Learning AI Platform

Tutorial ini menjelaskan langkah demi langkah cara setup semua service yang dibutuhkan untuk project E-Learning AI Platform Kemenkeu.

---

## Daftar Isi

1. [Setup Google Gemini API Key (Gratis)](#1-setup-google-gemini-api-key)
2. [Setup Supabase (Database & Storage Gratis)](#2-setup-supabase-database--storage)
3. [Setup Python & Backend FastAPI](#3-setup-python-backend)
4. [Setup RAG Pipeline (Supabase pgvector)](#4-setup-rag-pipeline-supabase-pgvector)
5. [Deploy Backend ke Railway.app (Gratis)](#5-deploy-backend-ke-railway)
6. [Deploy Frontend ke GitHub Pages (Gratis)](#6-deploy-frontend)

---

## 1. Setup Google Gemini API Key

> **Biaya:** GRATIS (Free Tier: 15 request/menit, 1500 request/hari)

### Langkah-langkah:

1. **Buka** [Google AI Studio](https://aistudio.google.com/)
2. **Login** dengan akun Google Anda
3. **Klik** tombol **"Get API Key"** di sidebar kiri
4. **Klik** **"Create API Key"**
5. **Pilih** project Google Cloud (atau buat baru jika belum ada)
6. **Copy** API Key yang muncul

   ```
   Contoh: AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

7. **Simpan** API Key ke file `.env` di folder backend:
   ```
   GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### Verifikasi API Key:

Jalankan script Python berikut untuk test:

```python
import google.generativeai as genai

genai.configure(api_key="API_KEY_ANDA")
model = genai.GenerativeModel("gemini-2.0-flash")
response = model.generate_content("Halo, apa kabar?")
print(response.text)
```

> ✅ Jika muncul balasan teks, API key berhasil!

---

## 2. Setup Supabase (Database & Storage)

> **Biaya:** GRATIS (Free Tier: 500MB DB, 1GB Storage)

### 2.1. Buat Project Supabase

1. **Buka** [Supabase](https://supabase.com/) dan login dengan akun GitHub Anda.
2. **Klik** **"New Project"**
3. **Pilih** organisasi (atau buat baru)
4. **Isi konfigurasi:**
   - **Name:** `elearning-kemenkeu`
   - **Database Password:** Buat password yang kuat dan simpan.
   - **Region:** Singapore
5. **Klik** **"Create new project"**
6. Tunggu beberapa menit sampai project selesai di-provision.

### 2.2. Aktifkan Ekstensi pgvector

1. Di dashboard Supabase, **klik** menu **"Database"** (ikon database) di sidebar kiri.
2. Pilih tab **"Extensions"**.
3. Cari **`vector`** di kotak pencarian.
4. Klik ekstensi **`vector`** dan aktifkan (**Enable**).

### 2.3. Setup Storage (Untuk PDF Materi)

1. Di dashboard Supabase, **klik** menu **"Storage"** di sidebar.
2. **Klik** **"New Bucket"**
3. Masukkan nama: `materi_pdf`
4. Aktifkan toggle **"Public bucket"** (opsional, tergantung keamanan. Jika ingin private, matikan toggle ini, namun file URL harus diakses dengan bearer token).
5. **Klik** **"Save"**

### 2.4. Buat Tabel Database (SQL)

Supabase menggunakan PostgreSQL. Anda bisa menjalankan script SQL langsung dari dashboard.
1. **Klik** menu **"SQL Editor"** di sidebar kiri.
2. **Klik** **"New Query"**.
3. **Copy-paste** SQL schema berikut dan klik **Run**:

```sql
-- Tabel Users
CREATE TABLE users (
    nip VARCHAR PRIMARY KEY,
    nama VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabel Pretest
CREATE TABLE pretest (
    id SERIAL PRIMARY KEY,
    nip VARCHAR REFERENCES users(nip),
    soal JSONB,
    nilai INTEGER,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP
);

-- Tabel Learning Path
CREATE TABLE learning_path (
    id SERIAL PRIMARY KEY,
    nip VARCHAR REFERENCES users(nip),
    profil VARCHAR,
    penjabaran TEXT,
    skor_pretest INTEGER,
    bab_fokus JSONB,
    bab_opsional JSONB,
    generated_at TIMESTAMP DEFAULT NOW()
);

-- Tabel Materi Progress
CREATE TABLE materi_progress (
    id SERIAL PRIMARY KEY,
    nip VARCHAR REFERENCES users(nip),
    bab VARCHAR,
    finished BOOLEAN DEFAULT FALSE,
    time_spent_seconds INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabel Events Tracker
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    nip VARCHAR REFERENCES users(nip),
    page VARCHAR,
    action VARCHAR,
    duration_seconds INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Tabel Posttest
CREATE TABLE posttest (
    id SERIAL PRIMARY KEY,
    nip VARCHAR REFERENCES users(nip),
    soal JSONB,
    nilai INTEGER,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP
);

-- Tabel Feedback
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    nip VARCHAR REFERENCES users(nip),
    profil_akhir VARCHAR,
    analisis_perkembangan TEXT,
    evaluasi_perilaku TEXT,
    transformasi_profil TEXT,
    kesimpulan_strategis TEXT,
    generated_at TIMESTAMP DEFAULT NOW()
);

-- Tabel Vector untuk RAG
CREATE TABLE materi_chunks (
    id bigserial primary key,
    content text,
    metadata jsonb,
    embedding vector(768) -- Dimensi embedding Google Gemini
);
```

### 2.5. Dapatkan API Keys Supabase

1. **Klik** menu **"Project Settings"** (ikon gear di ujung kiri bawah).
2. Pilih tab **"API"**.
3. Copy dua nilai ini untuk backend:
   - **`Project URL`**
   - **`service_role secret`** (Penting: gunakan service_role, BUKAN anon public, karena backend butuh hak akses penuh untuk operasi DB).

4. **Tambahkan** ke `.env`:
   ```
   SUPABASE_URL=https://[PROJECT_REF_ID].supabase.co
   SUPABASE_KEY=[SERVICE_ROLE_KEY]
   ```

---

## 3. Setup Python Backend (FastAPI)

### 3.1. Install Python

1. **Download** Python 3.11+ dari [python.org](https://www.python.org/downloads/)
2. **Install** dengan mencentang ✅ **"Add Python to PATH"**
3. **Verifikasi:**
   ```bash
   python --version
   # Output: Python 3.11.x
   ```

### 3.2. Buat Project Backend

```bash
# Buat folder backend
mkdir backend
cd backend

# Buat virtual environment
python -m venv venv

# Aktivasi virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3.3. Install Dependencies

Buat file `requirements.txt`:

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
python-dotenv==1.0.1
supabase==2.3.0
google-generativeai==0.8.0
langchain==0.3.0
langchain-community==0.3.0
langchain-google-genai==2.0.0
langchain-postgres==0.0.1
psycopg2-binary==2.9.9
pymupdf==1.23.0
pydantic==2.9.0
python-multipart==0.0.9
```

Install:

```bash
pip install -r requirements.txt
```

### 3.4. Buat File `.env`

```env
# Google Gemini API
GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Supabase
SUPABASE_URL=https://[PROJECT_REF_ID].supabase.co
SUPABASE_KEY=[SERVICE_ROLE_KEY]

# CORS (tambahkan domain frontend Anda)
CORS_ORIGINS=http://localhost,http://127.0.0.1:5500,https://your-username.github.io

# Konfigurasi
RAG_COLLECTION_NAME=elearning_materi
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### 3.5. Buat `main.py` (Entry Point)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="E-Learning AI API",
    description="Backend API untuk Kemenkeu E-Learning Platform",
    version="1.0.0"
)

# Setup CORS agar frontend bisa akses
origins = os.getenv("CORS_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "E-Learning AI API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Import routers (akan dibuat nanti)
# from routers import user, pretest, posttest, learning_path, feedback, tracker
# app.include_router(user.router, prefix="/api")
# app.include_router(pretest.router, prefix="/api")
# ...
```

### 3.6. Jalankan Server Lokal

```bash
uvicorn main:app --reload --port 8000
```

Buka browser: `http://localhost:8000` → Harus muncul `{"message": "E-Learning AI API is running!"}`

Buka: `http://localhost:8000/docs` → Swagger UI otomatis dari FastAPI

---

## 4. Setup RAG Pipeline (Supabase pgvector)

### 4.1. Siapkan Folder PDF Materi

```
backend/
└── data/
    └── materi/
        ├── bab1_pengantar_keuangan_publik.pdf
        ├── bab2_manajemen_aset_negara.pdf
        ├── bab3_kebijakan_operasional.pdf
        └── bab4_analisis_ekonomi.pdf
```

### 4.2. Script Indexing PDF ke Supabase

Buat file `scripts/index_pdf.py`:

```python
"""
Script untuk mengindex PDF materi ke Supabase pgvector.
Jalankan sekali saja ketika ada materi baru.

Usage: python scripts/index_pdf.py
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from supabase import create_client, Client

# Konfigurasi
PDF_DIR = "./data/materi"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

def index_pdfs():
    print("🔄 Memulai indexing PDF...")
    
    # 1. Load semua PDF
    all_docs = []
    for filename in sorted(os.listdir(PDF_DIR)):
        if filename.endswith(".pdf"):
            filepath = os.path.join(PDF_DIR, filename)
            print(f"  📄 Loading: {filename}")
            loader = PyMuPDFLoader(filepath)
            docs = loader.load()
            # Tambahkan metadata bab
            for doc in docs:
                # Membersihkan path kosong atau newline
                doc.page_content = doc.page_content.replace('\x00', '')
                doc.metadata["source_file"] = filename
                doc.metadata["bab"] = filename.split("_")[0]  # e.g., "bab1"
            all_docs.extend(docs)
    
    print(f"  ✅ Total halaman PDF: {len(all_docs)}")
    
    # 2. Split menjadi chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = splitter.split_documents(all_docs)
    print(f"  ✅ Total chunks: {len(chunks)}")
    
    # 3. Buat embeddings dan simpan ke ChromaDB
    print("  🧠 Membuat embeddings (menggunakan Google Embedding API)...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    
    # 4. Simpan ke Supabase pgvector
    print("  🚀 Menyimpan vektor ke Supabase pgvector...")
    
    # Ambil nilai vektor untuk setiap chunk
    chunk_texts = [chunk.page_content for chunk in chunks]
    chunk_embeddings = embeddings.embed_documents(chunk_texts)
    
    # Masukkan ke database
    for idx, chunk in enumerate(chunks):
        data = {
            "content": chunk.page_content,
            "metadata": chunk.metadata,
            "embedding": chunk_embeddings[idx]
        }
        supabase.table("materi_chunks").insert(data).execute()
        
        if (idx + 1) % 50 == 0:
            print(f"  👉 Inserted {idx + 1}/{len(chunks)} chunks...")
            
    print(f"  ✅ Indexing selesai! {len(chunks)} chunks tersimpan di Supabase")

if __name__ == "__main__":
    index_pdfs()
```

### 4.3. Jalankan Indexing

```bash
# Pastikan sudah ada file PDF di data/materi/
python scripts/index_pdf.py
```

### 4.4. Service RAG Query

Buat file `services/rag_service.py`:

```python
import os
from supabase import create_client, Client
from langchain_google_genai import GoogleGenerativeAIEmbeddings

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GEMINI_API_KEY")
    )

def query_materi(query: str, k: int = 10) -> str:
    """Query materi yang relevan dari pgvector (Supabase)"""
    embedding_model = get_embeddings()
    query_vector = embedding_model.embed_query(query)
    
    # Menggunakan RPC match_materi di Supabase
    # Anda perlu membuat RPC ini di SQL editor Supabase:
    # CREATE FUNCTION match_materi (
    #  query_embedding vector(768),
    #  match_count int DEFAULT 10
    # ) RETURNS TABLE (
    #  id bigint,
    #  content text,
    #  metadata jsonb,
    #  similarity float
    # )
    # LANGUAGE plpgsql
    # AS $$
    # BEGIN
    #  RETURN QUERY
    #  SELECT
    #    materi_chunks.id,
    #    materi_chunks.content,
    #    materi_chunks.metadata,
    #    1 - (materi_chunks.embedding <=> query_embedding) AS similarity
    #  FROM materi_chunks
    #  ORDER BY materi_chunks.embedding <=> query_embedding
    #  LIMIT match_count;
    # END;
    # $$;
    
    response = supabase.rpc("match_materi", {
        "query_embedding": query_vector,
        "match_count": k
    }).execute()
    
    results = response.data
    context = "\n\n---\n\n".join([doc["content"] for doc in results])
    return context
```

---

## 5. Deploy Backend ke Railway.app

> **Biaya:** GRATIS ($5 credit/bulan)

Railway.app sangat cocok sebagai pengganti Render, dengan deploy yang lebih cepat dan tidak ada spin-down (cold start lambat) pada free tier asalkan masih ada credit bulanan.

### 5.1. Persiapan

1. **Buat akun** di [Railway.app](https://railway.app/) (free, login dengan GitHub)
2. **Push** kode backend ke **GitHub repository**

### 5.2. File yang Dibutuhkan untuk Deployment

Railway menggunakan Nixpacks secara default yang pintar di Python FastAPI, jadi tidak sangat butuh file kustom. Tapi lebih aman siapkan:

**`Procfile`** (tanpa ekstensi):
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 5.3. Deploy di Railway

1. **Login** ke [Railway Dashboard](https://railway.app/dashboard)
2. **Klik** **"New Project"** → **"Deploy from GitHub repo"**
3. **Pilih** GitHub repository backend Anda
4. **Deploy Now**.
5. Tunggu sampai deployment selesai (Railway akan otomatis mendeteksi environment Python)
6. **Buka** Dashboard Railway, pilih service backend yang baru di deploy.
7. Di bagian menu atas service, pilih menu "**Variables**"
8. **Tambahkan Environment Variables:**
   - `GEMINI_API_KEY` → Nilai API Key Anda
   - `SUPABASE_URL` → URL Supabase
   - `SUPABASE_KEY` → Service Role Supabase
   - `CORS_ORIGINS` → Domain frontend Anda (contoh: *https://your-username.github.io*)
   - (Railway akan meminta otomatis untuk auto-redeploy)
9. Di menu atas pilih "**Settings**", scroll ke bagian **Networking**
10. Di bagian **Public Networking**, klik **"Generate Domain"**
11. Anda akan mendapat URL seperti: `https://repo-name-production.up.railway.app`

URL ini adalah domain API backend yang akan anda masukkan ke `api.js` di Frontend.

---

## 6. Deploy Frontend ke GitHub Pages

> **Biaya:** GRATIS

### 6.1. Persiapan

1. **Buat repository** di GitHub (contoh: `elearning-kemenkeu`)
2. **Push** semua file HTML ke repository

### 6.2. Update API URL di Frontend

Buat file `api.js` di folder frontend:

```javascript
// Ganti dengan URL backend Railway Anda
const API_BASE_URL = 'https://repo-name-production.up.railway.app/api';

// Untuk development lokal, uncomment baris berikut:
// const API_BASE_URL = 'http://localhost:8000/api';

async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (body) options.body = JSON.stringify(body);
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    return response.json();
}
```

### 6.3. Enable GitHub Pages

1. **Buka** repository di GitHub
2. **Klik** **Settings** → **Pages** (di sidebar kiri)
3. **Source:** Deploy from a branch
4. **Branch:** `main` / `master`, folder: `/ (root)`
5. **Klik** **Save**
6. Tunggu ~2 menit, site akan live di: `https://your-username.github.io/elearning-kemenkeu/`

---

## 7. Checklist Verifikasi

Setelah semua setup selesai, verifikasi dengan checklist berikut:

- [ ] ✅ Gemini API Key bisa generate teks
- [ ] ✅ Firebase/Supabase bisa write/read data
- [ ] ✅ Backend FastAPI jalan di lokal (http://localhost:8000)
- [ ] ✅ PDF berhasil diindex ke pgvector (Supabase)
- [ ] ✅ RAG query mengembalikan konteks yang relevan
- [ ] ✅ Backend bisa diakses dari frontend (CORS OK)
- [ ] ✅ Backend deployed di Railway.app
- [ ] ✅ Frontend deployed di GitHub Pages
- [ ] ✅ End-to-end: Frontend → Backend → AI → Database → Frontend

---

## 💡 Tips & Troubleshooting

### CORS Error di Browser

Jika muncul error CORS, pastikan:
1. URL frontend ada di `CORS_ORIGINS` env var
2. Middleware CORS sudah di-setup di FastAPI
3. Gunakan `https://` bukan `http://` di production

### Supabase Limitations

Monitor DB size di Supabase Dashboard (500MB free quota). JSON text database space-nya sangat efisien, yang memakan tempat adalah vector embeddings. Jika mencapai limit, anda harus menghapus/truncate row lama di events atau upgrade pricing.

### Gemini API Rate Limit

Jika terkena rate limit:
- Implementasi exponential backoff retry
- Queue request dengan delay
- Simpan hasil AI ke database (cache) agar tidak perlu generate ulang

---

> 📧 **Butuh bantuan?** Hubungi helpdesk atau buka issue di GitHub repository project.
