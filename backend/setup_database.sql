-- ============================================================
-- Supabase SQL Setup Script
-- E-Learning AI Platform - Kemenkeu Learning
-- 
-- Jalankan script ini di Supabase SQL Editor:
-- Dashboard → SQL Editor → New Query → Paste → Run
-- ============================================================

-- 1. Aktifkan ekstensi pgvector (jika belum)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Tabel Users
CREATE TABLE IF NOT EXISTS users (
    nip VARCHAR PRIMARY KEY,
    nama VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Tabel Pretest
CREATE TABLE IF NOT EXISTS pretest (
    id SERIAL PRIMARY KEY,
    nip VARCHAR REFERENCES users(nip),
    soal JSONB,
    nilai INTEGER,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP
);

-- 4. Tabel Learning Path
CREATE TABLE IF NOT EXISTS learning_path (
    id SERIAL PRIMARY KEY,
    nip VARCHAR REFERENCES users(nip),
    profil VARCHAR,
    penjabaran TEXT,
    skor_pretest INTEGER,
    bab_fokus JSONB,
    bab_opsional JSONB,
    generated_at TIMESTAMP DEFAULT NOW()
);

-- 5. Tabel Materi Progress
CREATE TABLE IF NOT EXISTS materi_progress (
    id SERIAL PRIMARY KEY,
    nip VARCHAR REFERENCES users(nip),
    bab VARCHAR,
    finished BOOLEAN DEFAULT FALSE,
    time_spent_seconds INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 6. Tabel Events Tracker
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    nip VARCHAR REFERENCES users(nip),
    page VARCHAR,
    action VARCHAR,
    duration_seconds INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- 7. Tabel Posttest
CREATE TABLE IF NOT EXISTS posttest (
    id SERIAL PRIMARY KEY,
    nip VARCHAR REFERENCES users(nip),
    soal JSONB,
    nilai INTEGER,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP
);

-- 8. Tabel Feedback
DROP TABLE IF EXISTS feedback CASCADE;
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    nip VARCHAR REFERENCES users(nip),
    profil_akhir VARCHAR,
    analisis_perkembangan TEXT,
    evaluasi_perilaku TEXT,
    transformasi_profil TEXT,
    kesimpulan_strategis TEXT,
    generated_at TIMESTAMP DEFAULT NOW()
);

-- 9. Tabel Vector untuk RAG (pgvector)
DROP TABLE IF EXISTS materi_chunks CASCADE;
CREATE TABLE IF NOT EXISTS materi_chunks (
    id BIGSERIAL PRIMARY KEY,
    content TEXT,
    metadata JSONB,
    embedding VECTOR(3072)  -- Dimensi embedding Google gemini-embedding-001
);

-- 10. Function untuk similarity search (digunakan oleh backend)
DROP FUNCTION IF EXISTS match_materi;
CREATE OR REPLACE FUNCTION match_materi (
    query_embedding VECTOR(3072),
    match_count INT DEFAULT 10
) RETURNS TABLE (
    id BIGINT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        materi_chunks.id,
        materi_chunks.content,
        materi_chunks.metadata,
        1 - (materi_chunks.embedding <=> query_embedding) AS similarity
    FROM materi_chunks
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;
