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
    elearning_title: str = "E-Learning"
) -> dict:
    """Generate comprehensive AI feedback based on all user data."""
    pretest_nilai = pretest_data.get("nilai", 0)
    posttest_nilai = posttest_data.get("nilai", 0)
    profil_awal = learning_path_data.get("profil", "N/A")

    # Clean the title for certificates/job suggestions (remove variations of 'elearning')
    cleaned_title = elearning_title.lower()
    for word in ["elearning", "e-learning", "pembelajaran digital"]:
        cleaned_title = cleaned_title.replace(word, "")
    cleaned_title = cleaned_title.strip().title()

    time_per_bab = ""
    for m in materi_progress:
        minutes = round(m.get("time_spent_seconds", 0) / 60, 1)
        time_per_bab += f"  - {m.get('bab', 'N/A')}: {minutes} menit\n"

    events_summary = json.dumps(events[:50], default=str, ensure_ascii=False)

    # Determine focus based on pass/fail
    if is_failed_posttest:
        focus_instruction = f"""
Tugas Khusus: User BELUM LULUS post-test (nilai < 80) pada pelatihan "{elearning_title}". 
Fokus analisis Anda harus pada:
1. Identifikasi bab mana yang paling lemah berdasarkan hasil post-test.
2. Memberikan saran perbaikan yang sangat spesifik dan langkah-langkah konkret untuk dipelajari kembali agar LULUS di percobaan berikutnya.
3. Memberikan motivasi yang kuat namun jujur bahwa kegagalan ini adalah bagian dari proses menuju kompetensi yang lebih tinggi.
4. Fokus pada penguasaan materi saat ini.
"""
    else:
        focus_instruction = f"""
Tugas: User telah menyelesaikan pelatihan "{elearning_title}" dengan baik.
Fokus analisis Anda adalah pada:
1. Apresiasi atas capaian nilai dan perkembangan kompetensi dari pre-test ke post-test.
2. Memberikan saran pengembangan karir yang strategis (tidak harus di lingkungan Kemenkeu).
3. Rekomendasi sertifikasi atau langkah lanjutan untuk menjaga momentum keahlian ini.
"""

    prompt = f"""Role: Anda adalah seorang Spesialis Pengembangan SDM dan analis hasil Pembelajaran Digital di lingkungan Kementerian Keuangan.

{focus_instruction}

Ketentuan Penulisan:

Gaya Bahasa: Gunakan pendekatan motivasional. Hindari bahasa yang terlalu kaku, namun tetap jaga profesionalitas ASN.

Panjang Konten: Setiap nilai dalam JSON harus berupa paragraf yang tidak bertele tele, mendalam, dan deskriptif (minimal 4-6 kalimat per paragraf).

Konteks Organisasi: Hubungkan {"perlu-nya perbaikan" if is_failed_posttest else "keberhasilan"} belajar dengan kontribusi terhadap organisasi, peningkatan kredibilitas di unit kerja, dan pemanfaatan fasilitas pengembangan kompetensi.

Sapaan: Selalu gunakan kata "Anda".

Larangan: Jangan memberikan saran untuk mengubah tipe atau format materi e-learning yang diberikan penyelenggara. Fokus pada pengembangan diri user, jangan lebay atau berlebih-lebihan dalam memotivasi user.


DATA PEMBELAJARAN:
- Judul Pelatihan: {elearning_title}
- Nilai Pretest: {pretest_nilai}/100
- Nilai Posttest: {posttest_nilai}/100
- Profil Awal: {profil_awal}
- Learning Path yang diberikan: fokus di {learning_path_data.get('bab_fokus', [])}
- Waktu belajar per bab:
{time_per_bab}
- Event Tracking (sample): {events_summary}

FORMAT OUTPUT (JSON object saja, tanpa text lain):
{{
  "profil_akhir": "Pemula|Menengah|Mahir",
  "analisis_perkembangan": "[Tulis paragraf tentang perbandingan skor pre-test dan post-test.{' Jika nilai masih di bawah 80, jelaskan area mana yang perlu diperkuat.' if is_failed_posttest else ' Jika ada lompatan nilai yang signifikan, tekankan pada bukti ketajaman berpikir.'}]",
  "evaluasi_perilaku": "[Klasifikasikan pola belajar user ke dalam salah satu dari 4 kategori berikut (masukkan juga penjelasan kategori tersebut) berdasarkan data waktu dan jeda belajar, lalu jelaskan dalam 1 paragraf. jangan men jugje negatif user jika user belum lolos, karena user memiliki preferensi/kategori belajar masing-masing:
    1. Pemelajar Big Eater: Mengalokasikan sejumlah besar waktu untuk belajar secara intensif dengan sedikit atau tanpa jeda belajar.
    2. Pemelajar Nibbler: Menggabungkan komitmen waktu yang substansial dengan jeda yang konsisten antar sesi. Memungkinkan pemahaman komprehensif melalui kedalaman dan pengulangan. (Kategori ini digambarkan dengan warna hijau pada pojok kanan atas).
    3. Pemelajar Picky Eater: Mengalokasikan waktu keseluruhan yang lebih sedikit tetapi dengan jeda yang teratur. Fokus berinteraksi pada materi tertentu untuk merefleksikan, meninjau, dan memperkuat bahasan yang menarik/penting bagi mereka.
    4. Pemelajar Gulper: Mengalokasikan waktu minimal untuk belajar dan mengonsumsi konten dengan cepat tanpa jeda. Mengutamakan efisiensi daripada kedalaman untuk mendapatkan gambaran umum dengan cepat.
  ]",
  "transformasi_profil": "[Tulis paragraf tentang perubahan status dari user. {'Karena user belum lulus, berikan feedback yang sangat membangun dan instruksi belajar kembali agar siap ujian ulang.' if is_failed_posttest else 'Gambarkan bagaimana pemahaman baru ini menjadi modal kuat untuk menjadi ahli di bidangnya.'}]",
  "kesimpulan_strategis": "[Tulis paragraf berisi saran {'belajar ulang dan persiapan ujian' if is_failed_posttest else 'pengembangan karir'}. {'Sebutkan bab materi mana saja yang harus dibaca ulang secara mendalam.' if is_failed_posttest else f'Sertakan rekomendasi sertifikasi (hilangkan kata elearning dalam judul/subjek sertifikasinya) terkait tema {cleaned_title} yang ada di internet beserta link nya yang bisa diikuti user. Sarankan untuk memperbarui portofolio di HRIS dan dapat menjadi (sebutkan pekerjaan yang cocok dengan tema {cleaned_title} untuk pengembangan karir baik di instansi pemerintah maupun di industri swasta/internasional).'}]"
}}

PENTING: Output HANYA JSON object, tanpa penjelasan tambahan.
"""
    response_text = _generate_with_retry(prompt)
    return _parse_json(response_text)


def generate_bank_soal_questions(context: str, bab_nomor: int, bab_judul: str, jumlah: int = 10) -> list:
    """
    Generate a bank of MCQ questions for a specific chapter.
    Requires RAG context.
    """
    prompt = f"""Gunakan kemampuan terhebat kamu. Kamu adalah Dosen pembuat soal ujian profesional.
    
Tugas Anda adalah membuat DATABASE SOAL (Bank Soal) untuk materi pembelajaran berikut:
Bab {bab_nomor}: {bab_judul}

KONTEKS MATERI:
---
{context}
---

Buatkan {jumlah} soal pilihan ganda yang BERVARIASI. 
Kriteria soal:
1. Soal harus bersifat teknis (berdasarkan fakta/isi materi) dan bukan sekadar konseptual umum.
2. Gunakan variasi narasi: ada yang langsung "Apa yang dimaksud...", ada yang skenario "Jika terjadi X maka...", ada yang menanyakan dasar hukum/peraturan jika ada.
3. Jawaban harus tersurat (ada) di dalam materi yang diberikan.
4. Distribusi tingkat kesulitan: Mudah (30%), Sedang (50%), Sulit (20%).

FORMAT OUTPUT (JSON array saja, tanpa text lain, tanpa penjelasan):
[
  {{
    "nomor": 1,
    "pertanyaan": "...",
    "opsi": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "jawaban_benar": "A",
    "bab_referensi": "Bab {bab_nomor}"
  }}
]

PENTING: 
- HANYA output JSON array.
- Pastikan semua {jumlah} soal benar-benar berasal dari konteks materi di atas.
"""
    response_text = _generate_with_retry(prompt)
    return _parse_json(response_text)
