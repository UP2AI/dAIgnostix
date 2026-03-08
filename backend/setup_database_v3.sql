-- ============================================================
-- Supabase SQL Migration V3 — Dual PDF per Bab
-- E-Learning AI Platform
--
-- Adds separate column for user-facing materi PDF
-- (pdf_filename = RAG database, pdf_materi_filename = user display)
--
-- Jalankan script ini di Supabase SQL Editor:
-- Dashboard → SQL Editor → New Query → Paste → Run
-- ============================================================

-- 1. Add materi PDF column to elearning_bab table
ALTER TABLE elearning_bab ADD COLUMN IF NOT EXISTS pdf_materi_filename VARCHAR DEFAULT '';
