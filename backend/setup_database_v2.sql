-- ============================================================
-- Supabase SQL Migration V2 — Admin System & Dynamic Bab
-- E-Learning AI Platform
--
-- Jalankan script ini di Supabase SQL Editor:
-- Dashboard → SQL Editor → New Query → Paste → Run
-- ============================================================

-- 1. Add role column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'user';

-- 2. E-learning configuration (singleton row)
CREATE TABLE IF NOT EXISTS elearning_config (
    id SERIAL PRIMARY KEY,
    judul VARCHAR NOT NULL DEFAULT 'E-Learning',
    deskripsi TEXT DEFAULT '',
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. Dynamic bab/chapters
CREATE TABLE IF NOT EXISTS elearning_bab (
    id SERIAL PRIMARY KEY,
    nomor INTEGER NOT NULL,
    judul VARCHAR NOT NULL,
    deskripsi TEXT DEFAULT '',
    pdf_filename VARCHAR DEFAULT '',
    indexed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert default config if not exists
INSERT INTO elearning_config (judul, deskripsi)
SELECT 'E-Learning Audit Internal Keuangan Negara', 'Platform pembelajaran berbasis AI untuk Audit Internal Keuangan Negara'
WHERE NOT EXISTS (SELECT 1 FROM elearning_config LIMIT 1);
