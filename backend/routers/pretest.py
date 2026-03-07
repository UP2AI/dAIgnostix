"""
Pretest router — generate and submit pretest.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import db_service, ai_service, rag_service

router = APIRouter()


class PretestSubmit(BaseModel):
    jawaban: dict  # { "1": "A", "2": "C", ... }


@router.get("/pretest/{nip}")
async def get_pretest(nip: str):
    """
    Get pretest questions for a user.
    If not yet generated, AI will generate them via RAG.
    """
    user = db_service.get_user(nip)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    existing = db_service.get_pretest(nip)
    if existing:
        return existing

    # Generate via AI + RAG
    try:
        # Reduce k to 1 to drastically minimize token usage
        context = rag_service.query_materi("materi audit internal keuangan negara lengkap semua bab", k=1)
        if not context:
            raise HTTPException(status_code=500, detail="Materi belum diindex. Admin perlu menjalankan indexing PDF terlebih dahulu.")

        # Get dynamic bab list for proportional question generation
        bab_list = db_service.get_all_bab()

        soal = ai_service.generate_pretest_questions(context, bab_list=bab_list if bab_list else None)
        saved = db_service.save_pretest(nip, soal)
        return saved
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gagal generate soal dari AI: {str(e)}")


@router.post("/pretest/{nip}/submit")
async def submit_pretest(nip: str, body: PretestSubmit):
    """Submit pretest answers and calculate score."""
    pretest = db_service.get_pretest(nip)
    if not pretest:
        raise HTTPException(status_code=404, detail="Pretest belum ada. Ambil soal terlebih dahulu.")

    if pretest.get("completed"):
        return {"message": "Pretest sudah diselesaikan", "nilai": pretest["nilai"], "soal": pretest["soal"]}

    soal = pretest["soal"]
    benar = 0
    total = len(soal)

    for s in soal:
        nomor = str(s["nomor"])
        jawaban_user = body.jawaban.get(nomor, "")
        s["jawaban_user"] = jawaban_user
        if jawaban_user == s["jawaban_benar"]:
            benar += 1

    nilai = round((benar / total) * 100) if total > 0 else 0
    result = db_service.submit_pretest(nip, nilai, soal)

    return {
        "message": "Pretest berhasil disubmit",
        "nilai": nilai,
        "benar": benar,
        "total": total,
        "soal": soal,
    }
