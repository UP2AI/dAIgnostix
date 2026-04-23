# Spesifikasi Teknis: Adaptive Post-Test
**Project:** Antigravity AI Engine  
**Topik:** Adaptive Learning Assessment — Posttest  
**Versi:** Final (hasil revisi diskusi)  
**Tahun:** 2026

---

## 1. Konsep Utama

Sistem asesmen ini menggunakan model **Stage-Adaptive Testing** untuk mengklasifikasikan pengguna ke dalam tiga kategori kompetensi secara otomatis dan akurat.

Fokus utama adalah memisahkan pengguna **Menengah** dan **Ahli** menggunakan tingkat kesulitan soal sebagai validator kompetensi nyata — bukan sekadar akurasi angka.

> **Prinsip desain:** Kategorisasi Ahli berbasis bukti kompetensi (Opsi A), bukan threshold skor semata. User harus membuktikan kemampuan berpikir tingkat tinggi (HOTS) untuk mencapai level Ahli.

---


## 3. Struktur Soal & Pembobotan

Total soal: **30 butir** | Nilai maksimal: **100 poin**

| Tipe Soal | Jumlah | Bobot per Soal | Total Poin |
|---|---|---|---|
| Level 2 — Normal | 25 butir | 3,2 poin | 80 poin |
| Level 3 — Sulit / Expert | 5 butir (soal 26–30) | 4,0 poin | 20 poin |

### Karakteristik soal per level

**Level 2 (Normal):**
- Fokus pada aplikasi konsep dan prosedur standar
- Pemahaman operasional materi
- Setara taksonomi Bloom: *Apply, Understand*

**Level 3 (Sulit / Expert):**
- Fokus pada sintesis multi-konsep
- Analisis kasus kritis dan penalaran tingkat tinggi (HOTS)
- Setara taksonomi Bloom: *Analyze, Evaluate, Create*

---

## 4. Logika Adaptif — The Branching Gate

AI melakukan evaluasi otomatis tepat setelah pengguna menyelesaikan **soal ke-25**.

### Checkpoint (setelah soal ke-25)

```
Skor soal 1–25 < 80?
    └── YA  → Jalur A: soal 26–30 Level 2 (Normal)
    └── TIDAK (≥ 80) → Jalur B: soal 26–30 Level 3 (Sulit/Expert)
```

| Kondisi | Jalur | Soal 26–30 |
|---|---|---|
| Skor < 80 | Jalur A | Level 2 — Normal |
| Skor ≥ 80 | Jalur B | Level 3 — Sulit/Expert |

> **Catatan:** User masuk Jalur B hanya jika menjawab benar seluruh soal Level 2 sehingga skor ≥ 80. Skor minimum di Jalur B adalah **80 poin** — tidak ada skenario skor < 80 di Jalur B.

---

## 5. Penentuan Kategori Akhir

Kategori ditentukan berdasarkan **jalur yang dilewati** dan **performa soal Level 3**, bukan semata-mata skor akhir.

| Jalur | Performa Soal 26–30 | Skor Akhir | Kategori |
|---|---|---|---|
| Jalur A | — | < 80 | **Pemula** |
| Jalur A | — | ≥ 80 | **Menengah** |
| Jalur B | Benar < 3 dari 5 soal Level 3 | 80–88 | **Menengah** |
| Jalur B | Benar ≥ 3 dari 5 soal Level 3 | ≥ 92 | **Ahli** |

### Definisi kategoris

**Pemula**
Belum menguasai konsep dasar. Disarankan mengulang learning path dari awal sebelum retake posttest.

**Menengah**
Lulus standar kompetensi (skor ≥ 80). Memahami prosedur dan aplikasi standar, namun belum mampu mensintesis konsep secara kritis. Dapat diarahkan ke materi pengayaan.

**Ahli**
Lulus standar kompetensi dan terbukti mampu mengerjakan soal HOTS. Minimal **3 dari 5 soal Level 3** dijawab benar — membuktikan pemahaman mendalam, bukan sekadar hafalan. Skor minimum kategori Ahli: **92 poin**.

---

## 6. Verifikasi Matematika Skor

### Jalur A
- Skor maksimal soal 1–25: 25 × 3,2 = **80 poin**
- Skor maksimal soal 26–30 (Level 2): 5 × 3,2 = **16 poin**
- **Skor maksimal Jalur A: 96 poin**

### Jalur B
- Skor masuk Jalur B (minimum): **80 poin**
- Benar tepat 3/5 soal Level 3: 80 + (3 × 4) = **92 poin** → threshold minimum Ahli
- Skor maksimal Jalur B: 80 + (5 × 4) = **100 poin**

---

## 7. Peran AI dalam Sistem

### 7.1 Item Calibration (sebelum deploy)
AI menganalisis teks soal untuk memberikan estimasi parameter kesulitan Level 2 / Level 3 secara otomatis berdasarkan karakteristik konten.

### 7.2 Branching Gate Otomatis
AI mengevaluasi skor setelah soal ke-25 dan secara otomatis menentukan jalur soal berikutnya tanpa intervensi manual. pastikan user jawab ujiannya tersimpan saat putus koneksi, sehingga user tidak perlu memulai ujian dari awal

---