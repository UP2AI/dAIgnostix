-- ============================================================
-- Supabase SQL Migration V5 — Adaptive Post-Test System
-- E-Learning AI Platform - dAIgnostix
--
-- Jalankan script ini di Supabase SQL Editor:
-- Dashboard → SQL Editor → New Query → Paste → Run
-- ============================================================

-- 1. Tambahkan kolom adaptive test ke tabel posttest
ALTER TABLE posttest 
  ADD COLUMN IF NOT EXISTS jalur VARCHAR DEFAULT NULL,           -- 'A' atau 'B'
  ADD COLUMN IF NOT EXISTS saved_jawaban JSONB DEFAULT '{}',     -- jawaban real-time per soal (recovery)
  ADD COLUMN IF NOT EXISTS kategori VARCHAR DEFAULT NULL,        -- 'Pemula', 'Menengah', 'Mahir'
  ADD COLUMN IF NOT EXISTS adaptive_state JSONB DEFAULT '{}';    -- state checkpoint: phase, checkpoint_score, etc.

-- 2. Tambahkan kolom attempts jika belum ada
ALTER TABLE posttest 
  ADD COLUMN IF NOT EXISTS attempts INTEGER DEFAULT 1;

-- 3. (Opsional) Index untuk performa query
CREATE INDEX IF NOT EXISTS idx_posttest_nip ON posttest(nip);
CREATE INDEX IF NOT EXISTS idx_bank_soal_status ON bank_soal(status);
