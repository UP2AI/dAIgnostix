"""
AI Service — Google Gemini API integration.
Generates pretest/posttest questions, learning paths, and feedback.
"""
import time
import json
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, RetryError
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
# Using the exact preview identifier for 3.1 flash lite
model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")

def _generate_with_retry(prompt: str, max_retries: int = 3) -> str:
    """Helper to generate content with retries for rate limits."""
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except ResourceExhausted as e:
            if attempt == max_retries - 1:
                raise e
            # Google sometimes asks to wait 30-40s on free tier
            time.sleep(20 * (attempt + 1))
    return "{}"


def _parse_json(text: str) -> dict | list:
    """Extract JSON from AI response text (handles markdown code blocks)."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (code block markers)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return json.loads(text)


def generate_pretest_questions(context: str, bab_list: list = None) -> list:
    """
    Generate pretest MCQ questions based on RAG context.
    5 questions per bab, total = 5 × number of babs.
    """
    if bab_list and len(bab_list) > 0:
        jumlah_per_bab = 5
        total_soal = jumlah_per_bab * len(bab_list)
        bab_detail = "\n".join([f"  - {b['judul']} (Bab {b['nomor']}): {jumlah_per_bab} soal" for b in bab_list])
        distribusi = f"""
Distribusikan soal secara PROPORSIONAL per bab, masing-masing {jumlah_per_bab} soal:
{bab_detail}

Total: {total_soal} soal.
Gunakan field "bab_referensi" sesuai nama bab di atas (contoh: "Bab 1", "Bab 2", dst).
"""
    else:
        total_soal = 10
        distribusi = "Distribusikan soal secara merata dari semua bab materi.\nTotal: 10 soal."

    prompt = f"""Gunakan kemampuan terhebat kamu. Kamu adalah Dosen pembuat soal ujian pre test yang sangat handal dan profesional untuk materi pembelajaran saya.

Berdasarkan konteks materi berikut:
---
{context}
---

Buatkan {total_soal} soal pilihan ganda untuk pretest. soal harus bersifat teknis dan bukan konseptual. soal harus menggunakan materi materi inti dan jangan asal membuat soal dengan menggunakan materi tidak inti. 
buatlah soal yang jawabannya tersurat pada materi yang telah diberikan sehingga mempermudah user dalam menjawab secara teori.
{distribusi}
Tingkat kesulitan: campuran mudah (30%), sedang (50%), sulit (20%).

contoh soal yang jelek untuk pre test. 
1. Apa nama program atau konsep yang diusung Kementerian Keuangan dalam materi tersebut?
2. Berdasarkan materi, apa yang menjadi kekuatan organisasi Kementerian Keuangan untuk mengantisipasi ketidakpastian?
3. Dalam konteks materi, apa yang harus diantisipasi oleh Learning Organization di lingkungan Kementerian Keuangan?
4. Berdasarkan materi yang diberikan, dokumen hukum mana yang mengatur tentang Manajemen Pengetahuan?

jangan menggunakan "Berdasarkan materi" , karena saat pre test materi belum diberikan.

contoh soal yang bagus
1. Pembelajaran Terintegrasi mengkombinasikan model belajar apa saja?
2. Dalam tahapan pengelolaan prosesnya, Pembelajaran Terintegrasi harus diawali dengan?
3. Apa yang dimaksud dengan pembelajaran terintegrasi menurut KMK Nomor 350/KMK.011/2022?
4. Di bawah ini yang BUKAN merupakan salah satu model pembelajaran terintegrasi menurut KMK Nomor 350/KMK.011/2022
5. Dalam implementasi dukungan manajemen pengetahuan, pendekatan intervensi pembelajaran di mana belajar tidak perlu meninggalkan tempat kerja disebut dengan
6. Yang BUKAN merupakan tujuan dari pelaksanaan pembelajaran terintegrasi adalah

FORMAT OUTPUT (JSON array saja, tanpa text lain):
[
  {{
    "nomor": 1,
    "pertanyaan": "...",
    "opsi": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "jawaban_benar": "A",
    "bab_referensi": "Bab 1"
  }}
]

PENTING:
- Soal HARUS berdasarkan konteks materi yang diberikan.
- Jangan membuat soal di luar konteks.
- Output HANYA JSON array, tanpa penjelasan tambahan.
"""
    response_text = _generate_with_retry(prompt)
    return _parse_json(response_text)


def generate_posttest_questions(context: str, bab_list: list = None) -> list:
    """
    Generate posttest MCQ questions (different from pretest).
    5 questions per bab, total = 5 × number of babs.
    """
    if bab_list and len(bab_list) > 0:
        jumlah_per_bab = 5
        total_soal = jumlah_per_bab * len(bab_list)
        bab_detail = "\n".join([f"  - {b['judul']} (Bab {b['nomor']}): {jumlah_per_bab} soal" for b in bab_list])
        distribusi = f"""
Distribusikan soal secara PROPORSIONAL per bab, masing-masing {jumlah_per_bab} soal:
{bab_detail}

Total: {total_soal} soal.
Gunakan field "bab_referensi" sesuai nama bab di atas (contoh: "Bab 1", "Bab 2", dst).
"""
    else:
        total_soal = 10
        distribusi = "Distribusikan soal secara merata dari semua bab materi.\nTotal: 10 soal."

    prompt = f"""Gunakan kemampuan terhebat kamu. Kamu adalah Dosen pembuat soal ujian post test.

Berdasarkan konteks materi berikut:
---
{context}
---

Buatkan {total_soal} soal pilihan ganda untuk POSTTEST.
Soal ini HARUS BERBEDA dari soal pretest, tapi tetap berdasarkan materi yang sama. soal harus teknis dan bukan konseptual. soal harus menggunakan materi materi inti. 
jangan asal membuat soal dengan menggunakan materi tidak inti. 
jawaban harus tersurat pada materi yang telah diberikan sehingga mempermudah user dalam menjawab secara teori.
{distribusi}
Tingkat kesulitan: campuran mudah (20%), sedang (50%), sulit (30%).

contoh soal yang jelek untuk pre test. 
1. Apa nama program atau konsep yang diusung Kementerian Keuangan dalam materi tersebut?
2. Berdasarkan materi, apa yang menjadi kekuatan organisasi Kementerian Keuangan untuk mengantisipasi ketidakpastian?
3. Dalam konteks materi, apa yang harus diantisipasi oleh Learning Organization di lingkungan Kementerian Keuangan?
4. Berdasarkan materi yang diberikan, dokumen hukum mana yang mengatur tentang Manajemen Pengetahuan?

jangan menggunakan "Berdasarkan materi"

contoh soal yang bagus
1. Pembelajaran Terintegrasi mengkombinasikan model belajar apa saja?
2. Dalam tahapan pengelolaan prosesnya, Pembelajaran Terintegrasi harus diawali dengan?
3. Apa yang dimaksud dengan pembelajaran terintegrasi menurut KMK Nomor 350/KMK.011/2022?
4. Di bawah ini yang BUKAN merupakan salah satu model pembelajaran terintegrasi menurut KMK Nomor 350/KMK.011/2022
5. Dalam implementasi dukungan manajemen pengetahuan, pendekatan intervensi pembelajaran di mana belajar tidak perlu meninggalkan tempat kerja disebut dengan
6. Yang BUKAN merupakan tujuan dari pelaksanaan pembelajaran terintegrasi adalah


FORMAT OUTPUT (JSON array saja, tanpa text lain):
[
  {{
    "nomor": 1,
    "pertanyaan": "...",
    "opsi": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "jawaban_benar": "C",
    "bab_referensi": "Bab 2"
  }}
]

PENTING:
- Soal HARUS berdasarkan konteks materi.
- Output HANYA JSON array, tanpa penjelasan tambahan.
"""
    response_text = _generate_with_retry(prompt)
    return _parse_json(response_text)


def generate_learning_path(pretest_data: dict) -> dict:
    """Generate personalized learning path based on pretest results."""
    nilai = pretest_data.get("nilai", 0)
    soal = pretest_data.get("soal", [])

    # Calculate score per bab
    bab_stats = {}
    for s in soal:
        bab = s.get("bab_referensi", "Unknown")
        if bab not in bab_stats:
            bab_stats[bab] = {"benar": 0, "total": 0}
        bab_stats[bab]["total"] += 1
        if s.get("jawaban_user") == s.get("jawaban_benar"):
            bab_stats[bab]["benar"] += 1

    detail_bab = ""
    for bab, stat in sorted(bab_stats.items()):
        detail_bab += f"  - {bab}: {stat['benar']}/{stat['total']} soal benar\n"

    prompt = f"""Kamu adalah sistem AI untuk platform e-learning Kemenkeu.

Data User:
- Nilai Pretest: {nilai}/100
- Detail per Bab:
{detail_bab}

Instruksi Penentuan Status Bab:
1. "fokus_utama": Masukkan HANYA bab-bab di mana user menjawab BENAR di bawah 60% dari total soal pada bab tersebut. Jika nilai Pretest < 60 secara keseluruhan, bab 1, 2, dan 3 otomatis harus masuk ke fokus_utama sebagai pemahaman dasar.
2. "opsional": Masukkan bab-bab yang mana user menjawab benar dengan sangat baik (di atas 80%).

Buatkan learning path personal dengan format JSON.

FORMAT OUTPUT (JSON object saja, tanpa text lain):
{{
  "profil": "Pemula|Menengah|Mahir",
  "syarat pembagian profil": "Pemula: 0-60, Menengah: 61-80, Mahir: 81-100",
  "penjabaran_profil": "Deskripsi analisis kemampuan user berdasarkan data pretest... jangan menggunakan kata user tetapi gunakan kata 'Anda' sebagai sapaan",
  "skor_pretest": {nilai},
  "learning_path": {{
    "fokus_utama": ["Bab X", "Bab Y"],
    "wajib": ["Bab A", "Bab B"],
    "opsional": ["Bab C"],
    "urutan_rekomendasi": ["Bab ...", "Bab ...", "..."]
  }},
  "rekomendasi": "Saran singkat untuk user..."
}}

PENTING: Output HANYA JSON object, tanpa penjelasan tambahan.
"""
    response_text = _generate_with_retry(prompt)
    return _parse_json(response_text)


def generate_feedback(
    pretest_data: dict,
    posttest_data: dict,
    learning_path_data: dict,
    materi_progress: list,
    events: list,
    is_failed_posttest: bool = False,
    elearning_title: str = "E-Learning",
    kategori: str = "Menengah",
    jalur: str = None,
    quiz_results: list = None,
    user_nama: str = None,
) -> dict:
    """Generate comprehensive, personalized AI feedback from all user data.
    
    kategori is determined by the branching gate system (Pemula/Menengah/Mahir).
    jalur is 'A' or 'B' from the adaptive test checkpoint.
    quiz_results is a list of quiz_result dicts {bab_nomor, nilai, soal}.
    """
    pretest_nilai = pretest_data.get("nilai", 0)
    posttest_nilai = posttest_data.get("nilai", 0)
    profil_awal = learning_path_data.get("profil", "N/A")
    profil_awal_penjabaran = learning_path_data.get("penjabaran", "")
    quiz_results = quiz_results or []
    attempts = posttest_data.get("attempts", 1) or 1

    # Clean the title for certificates/job suggestions (remove variations of 'elearning')
    cleaned_title = elearning_title.lower()
    for word in ["elearning", "e-learning", "pembelajaran digital"]:
        cleaned_title = cleaned_title.replace(word, "")
    cleaned_title = cleaned_title.strip().title()

    # ---- PER-BAB ACCURACY ANALYSIS from posttest soal ----
    # Group soal by bab_referensi and calculate accuracy
    posttest_soal = posttest_data.get("soal", [])
    bab_stats = {}  # { bab_referensi: {benar, total, salah_topik: [pertanyaan]} }
    for s in posttest_soal:
        bab = s.get("bab_referensi", "Tidak Diketahui")
        if bab not in bab_stats:
            bab_stats[bab] = {"benar": 0, "total": 0, "salah_soal": []}
        bab_stats[bab]["total"] += 1
        jawaban_user = s.get("jawaban_user", "").strip().upper()
        jawaban_benar = s.get("jawaban_benar", "").strip().upper()
        if jawaban_user == jawaban_benar:
            bab_stats[bab]["benar"] += 1
        else:
            # Save the question text for context (truncated)
            bab_stats[bab]["salah_soal"].append(s.get("pertanyaan", "")[:100])

    bab_performance_lines = []
    weakest_bab = None
    weakest_pct = 100
    for bab, stats in sorted(bab_stats.items()):
        pct = round((stats["benar"] / stats["total"]) * 100) if stats["total"] > 0 else 0
        status = "✓ Baik" if pct >= 70 else ("⚠ Perlu Perhatian" if pct >= 50 else "✗ Lemah")
        wrong_preview = "; ".join(stats["salah_soal"][:3])  # max 3 wrong Qs preview
        bab_performance_lines.append(
            f"  - {bab}: {stats['benar']}/{stats['total']} benar ({pct}%) [{status}]"
            + (f'\n      Contoh pertanyaan yang salah: "{wrong_preview}"' if wrong_preview else "")
        )
        if pct < weakest_pct:
            weakest_pct = pct
            weakest_bab = bab
    bab_performance_text = "\n".join(bab_performance_lines) if bab_performance_lines else "  (data soal tidak tersedia)"

    # ---- PRETEST vs POSTTEST BAB COMPARISON ----
    pretest_soal = pretest_data.get("soal", [])
    pretest_bab_stats = {}
    for s in pretest_soal:
        bab = s.get("bab_referensi", "Tidak Diketahui")
        if bab not in pretest_bab_stats:
            pretest_bab_stats[bab] = {"benar": 0, "total": 0}
        pretest_bab_stats[bab]["total"] += 1
        if s.get("jawaban_user", "").strip().upper() == s.get("jawaban_benar", "").strip().upper():
            pretest_bab_stats[bab]["benar"] += 1

    bab_delta_lines = []
    for bab in bab_stats:
        post_pct = round((bab_stats[bab]["benar"] / bab_stats[bab]["total"]) * 100) if bab_stats[bab]["total"] > 0 else 0
        if bab in pretest_bab_stats and pretest_bab_stats[bab]["total"] > 0:
            pre_pct = round((pretest_bab_stats[bab]["benar"] / pretest_bab_stats[bab]["total"]) * 100)
            delta = post_pct - pre_pct
            arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
            bab_delta_lines.append(f"  - {bab}: Pre={pre_pct}% → Post={post_pct}% ({arrow}{abs(delta)}%)")
        else:
            bab_delta_lines.append(f"  - {bab}: Pre=N/A → Post={post_pct}%")
    bab_delta_text = "\n".join(bab_delta_lines) if bab_delta_lines else "  (perbandingan tidak tersedia)"

    # ---- QUIZ RESULTS PER BAB ----
    quiz_summary = ""
    if quiz_results:
        quiz_lines = []
        for qr in quiz_results:
            bab_no = qr.get("bab_nomor", "?")
            nilai_quiz = qr.get("nilai", 0)
            status_q = "Lulus" if nilai_quiz >= 70 else "Belum Lulus"
            quiz_lines.append(f"  - Bab {bab_no}: {nilai_quiz}/100 [{status_q}]")
        quiz_summary = "\n".join(quiz_lines)
    else:
        quiz_summary = "  (tidak ada data kuis bab)"

    # ---- TIME ANALYSIS ----
    time_per_bab = ""
    total_study_minutes = 0
    for m in materi_progress:
        minutes = round(m.get("time_spent_seconds", 0) / 60, 1)
        total_study_minutes += minutes
        time_per_bab += f"  - {m.get('bab', 'N/A')}: {minutes} menit\n"

    events_summary = json.dumps(events[:50], default=str, ensure_ascii=False)

    # Adaptive test context
    jalur_desc = ""
    if jalur == "B":
        jalur_desc = "User memasuki Jalur B (Expert Path) — artinya user berhasil menjawab dengan sangat baik pada soal standar dan diberikan soal tingkat tinggi (HOTS) untuk menguji kemampuan analisis dan sintesis."
    elif jalur == "A":
        jalur_desc = "User memasuki Jalur A (Standard Path) — user mengerjakan soal tambahan dengan tingkat kesulitan standar."

    kategori_desc = ""
    if kategori == "Mahir":
        kategori_desc = "User dikategorikan MAHIR — terbukti mampu menjawab soal HOTS dengan baik (minimal 3 dari 5 soal expert benar). Ini menunjukkan pemahaman mendalam, bukan sekadar hafalan."
    elif kategori == "Menengah":
        kategori_desc = "User dikategorikan MENENGAH — lulus standar kompetensi (skor >= 80), memahami prosedur dan aplikasi standar, namun belum sepenuhnya menguasai penalaran tingkat tinggi."
    elif kategori == "Pemula":
        kategori_desc = "User dikategorikan PEMULA — belum mencapai standar kompetensi minimum. Perlu mengulang materi dan memperkuat pemahaman dasar."

    # Determine focus based on pass/fail
    if is_failed_posttest:
        focus_instruction = f"""Tugas Khusus: User BELUM LULUS post-test (nilai < 80) pada pelatihan "{elearning_title}".
Kategori kompetensi akhir (ditentukan oleh sistem): {kategori}. {kategori_desc}
{jalur_desc}
Fokus analisis Anda harus pada:
1. Identifikasi TEPAT bab mana yang paling lemah berdasarkan data akurasi per-bab di bawah.
2. Sebutkan KONKRET topik/soal yang salah dijawab.
3. Jika ini percobaan ke-{attempts} (bukan percobaan pertama), tunjukkan pola kesalahan yang berulang.
4. Berikan langkah belajar ulang yang sangat spesifik dan realistis."""
    else:
        focus_instruction = f"""Tugas: User telah menyelesaikan pelatihan "{elearning_title}" dengan baik (percobaan ke-{attempts}).
Kategori kompetensi akhir (ditentukan oleh sistem): {kategori}. {kategori_desc}
{jalur_desc}
Fokus analisis Anda:
1. Sebutkan bab mana yang menjadi kekuatan dan mana yang masih perlu diperkuat menggunakan DATA AKURASI PER-BAB.
2. {'Karena user mencapai level Mahir (Expert via Jalur B), tekankan bukti kemampuan berpikir tingkat tinggi.' if kategori == 'Mahir' else 'Apresiasi peningkatan dari pre-test ke post-test berdasarkan data delta per-bab.'}
3. Rekomendasi pengembangan karir dan sertifikasi yang relevan dengan tema pelatihan."""

    prompt = f"""Role: Anda adalah seorang Spesialis Pengembangan SDM berbasis data di Kementerian Keuangan. Anda SANGAT DILARANG memberikan feedback generik. Seluruh feedback harus bersumber dari DATA SPESIFIK USER di bawah ini.

{focus_instruction}

Ketentuan Penulisan:
- Gaya Bahasa: Motivasional namun berbasis fakta dan data. Profesional sebagai ASN.
- Panjang Konten: Setiap paragraf mendalam (minimal 4-6 kalimat), mengutip angka dan fakta spesifik dari data.
- Larangan: JANGAN membuat pernyataan umum seperti "Anda perlu belajar lebih keras". Selalu sebut BAB SPESIFIK, TOPIK SPESIFIK, dan ANGKA SPESIFIK.
- Sapaan: Selalu gunakan kata "Anda".
- Larangan 2: Jangan memberikan saran untuk mengubah tipe atau format materi e-learning yang diberikan penyelenggara.
- PENTING: Nilai profil_akhir di output JSON HARUS sama persis dengan kategori yang ditentukan oleh sistem: "{kategori}".

=== DATA SPESIFIK USER ===
[Profil Dasar]
- Nama: {user_nama or 'Peserta'}
- Judul Pelatihan: {elearning_title}
- Percobaan Post-test ke: {attempts} kali
- Profil Awal (dari Pretest): {profil_awal} — {profil_awal_penjabaran}
- Kategori Akhir (dari sistem): {kategori}
- Jalur Adaptive Test: {jalur or 'N/A'}
- Learning Path yang diberikan: fokus di {learning_path_data.get('bab_fokus', [])}

[Nilai]
- Nilai Pretest: {pretest_nilai}/100
- Nilai Posttest: {posttest_nilai}/100 {'(TIDAK LULUS, nilai minimum 80)' if is_failed_posttest else '(LULUS)'}

[Akurasi Per-Bab di Post-test — INI UTAMA]
{bab_performance_text}
{f'>> Bab paling lemah: {weakest_bab} ({weakest_pct}% benar)' if weakest_bab else ''}

[Perbandingan Pre-test vs Post-test per Bab]
{bab_delta_text}

[Nilai Kuis Bab]
{quiz_summary}

[Waktu Belajar per Bab]
{time_per_bab}Total waktu belajar: {round(total_study_minutes, 1)} menit

[Event Tracking (50 events terakhir)]
{events_summary}

FORMAT OUTPUT (JSON object saja, tanpa text lain):
{{
  "profil_akhir": "{kategori}",
  "analisis_perkembangan": "Tulis paragraf mendalam tentang nilai pretest vs posttest, delta per-bab, bab terkuat dan terlemah.",
  "evaluasi_perilaku": "Klasifikasikan pola belajar user (Big Eater/Nibbler/Picky Eater/Gulper) berdasarkan data waktu belajar per bab. Sebutkan angka menit per bab dan jelaskan alasan klasifikasi. 1. Pemelajar Big Eater: Mengalokasikan sejumlah besar waktu untuk belajar secara intensif dengan sedikit atau tanpa jeda belajar. 2. Pemelajar Nibbler: Menggabungkan komitmen waktu yang substansial dengan jeda yang konsisten antar sesi. 3. Pemelajar Picky Eater: Mengalokasikan waktu keseluruhan yang lebih sedikit tetapi dengan jeda yang teratur. 4. Pemelajar Gulper: Mengalokasikan waktu minimal tanpa jeda.",
  "transformasi_profil": "Tulis paragraf perubahan profil dari {profil_awal} ke {kategori}. Gabungkan deskripsi profil awal, perubahan setelah post-test, dan bukti konkret dari data akurasi.",
  "kesimpulan_strategis": "Tulis rekomendasi konkret yang bisa LANGSUNG dilakukan oleh user sendiri tanpa memerlukan bantuan admin atau pihak lain: (1) bab/topik spesifik yang perlu dipelajari ulang berdasarkan data akurasi, (2) sertifikasi publik terkait {cleaned_title} yang bisa diikuti secara mandiri di internet beserta nama platform dan link-nya, (3) profesi yang relevan di instansi pemerintah dan swasta/internasional. DILARANG merekomendasikan hal-hal yang membutuhkan persetujuan/bantuan admin, atasan, atau HRIS seperti meminta akses modul atau meminta admin memberikan sesuatu.",
  "rekomendasi_ai_courses": [
    {{
      "title": "Nama Spesifik Sertifikasi / Course (maks 60 char)",
      "platform": "Platform (contoh: Coursera, edX, KLC, Google, Microsoft, AWS)",
      "provider": "Penyelenggara (Universitas / Instansi)",
      "level": "Pilih salah satu: Advanced / Intermediate / Beginner menyesuaikan level profil {kategori}",
      "link": "URL valid ke kursus/sertifikasi tersebut atau URL google search keywordnya",
      "description": "Alasan 1 kalimat MENGAPA AI merekomendasikan ini berdasarkan data analisis user.",
      "harga": "Perkiraan harga (contoh: Berbayar, Gratis, dsb)",
      "relevansi_pilar": "Pilar Pembelajaran terkait"
    }},
    "...maksimal buatkan 2 rekomendasi saja..."
  ]
}}

PENTING: Output HANYA JSON object, tanpa penjelasan tambahan.
"""
    response_text = _generate_with_retry(prompt)
    result = _parse_json(response_text)
    # Enforce system-determined kategori
    result["profil_akhir"] = kategori
    return result


def generate_bank_soal_questions(context: str, bab_nomor: int, bab_judul: str, jumlah_level2: int = 15, jumlah_level3: int = 5) -> list:
    """
    Generate a bank of MCQ questions for a specific chapter.
    Produces two levels:
      - Level 2 (Normal): Apply/Understand — standard competency questions
      - Level 3 (Expert/HOTS): Analyze/Evaluate/Create — higher-order thinking
    Each question includes a 'level' field (2 or 3).
    """
    total = jumlah_level2 + jumlah_level3
    prompt = f"""Gunakan kemampuan terhebat kamu. Kamu adalah Dosen pembuat soal ujian profesional.
    
Tugas Anda adalah membuat DATABASE SOAL (Bank Soal) untuk materi pembelajaran berikut:
Bab {bab_nomor}: {bab_judul}

KONTEKS MATERI:
---
{context}
---

Buatkan total {total} soal pilihan ganda yang BERVARIASI, dibagi menjadi 2 LEVEL:

== LEVEL 2 (Normal) — {jumlah_level2} soal ==
Kriteria:
- Fokus pada aplikasi konsep dan prosedur standar
- Pemahaman operasional materi
- Setara taksonomi Bloom: Apply, Understand
- Soal bersifat teknis, jawaban tersurat di materi
- Distribusi: Mudah (30%), Sedang (70%)

== LEVEL 3 (Expert / HOTS) — {jumlah_level3} soal ==
Kriteria:
- Fokus pada sintesis multi-konsep dari materi ini
- Analisis kasus kritis dan penalaran tingkat tinggi (HOTS)
- Setara taksonomi Bloom: Analyze, Evaluate, Create
- Soal berbentuk skenario, studi kasus, atau perbandingan konsep
- Jawaban memerlukan pemahaman mendalam (bukan sekadar hafalan)
- Tingkat kesulitan: Sulit semua

Gunakan variasi narasi: "Apa yang dimaksud...", "Jika terjadi X maka...", "Manakah yang paling tepat...", skenario kasus, dan dasar hukum/peraturan jika ada.

FORMAT OUTPUT (JSON array saja, tanpa text lain, tanpa penjelasan):
[
  {{
    "nomor": 1,
    "pertanyaan": "...",
    "opsi": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "jawaban_benar": "A",
    "bab_referensi": "Bab {bab_nomor}",
    "level": 2
  }},
  {{
    "nomor": {jumlah_level2 + 1},
    "pertanyaan": "[Soal HOTS/Expert]...",
    "opsi": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "jawaban_benar": "C",
    "bab_referensi": "Bab {bab_nomor}",
    "level": 3
  }}
]

PENTING: 
- HANYA output JSON array.
- Soal nomor 1-{jumlah_level2} HARUS memiliki "level": 2
- Soal nomor {jumlah_level2 + 1}-{total} HARUS memiliki "level": 3
- Pastikan semua {total} soal benar-benar berasal dari konteks materi di atas.
- Setiap soal WAJIB memiliki field "level" (integer: 2 atau 3).
"""
    response_text = _generate_with_retry(prompt)
    questions = _parse_json(response_text)
    # Enforce level field in case AI didn't set it properly
    for i, q in enumerate(questions):
        if "level" not in q:
            q["level"] = 2 if i < jumlah_level2 else 3
    return questions
