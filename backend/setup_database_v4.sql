-- ============================================================
-- Supabase SQL Migration V4 — Bank Soal & Quiz System
-- E-Learning AI Platform
--
-- Jalankan script ini di Supabase SQL Editor:
-- Dashboard → SQL Editor → New Query → Paste → Run
-- ============================================================

-- 1. Tabel Bank Soal (Master Database Soal)
CREATE TABLE IF NOT EXISTS bank_soal (
    id SERIAL PRIMARY KEY,
    bab_nomor INTEGER NOT NULL,
    bab_judul VARCHAR NOT NULL,
    soal JSONB NOT NULL DEFAULT '[]',
    status VARCHAR DEFAULT 'draft',       -- 'draft' | 'published'
    generated_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Tabel Hasil Quiz (Per Bab)
CREATE TABLE IF NOT EXISTS quiz_results (
    id SERIAL PRIMARY KEY,
    nip VARCHAR REFERENCES users(nip),
    bab_nomor INTEGER NOT NULL,
    soal JSONB NOT NULL DEFAULT '[]',     -- Berisi soal yang dikerjakan + jawaban user
    nilai INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Tambahkan kolom status ke pretest/posttest jika perlu, 
-- namun struktur yang ada sudah cukup fleksibel. 
-- Pastikan tabel users sudah memiliki role 'admin'/'user'.
