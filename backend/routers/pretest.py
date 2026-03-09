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

    # Pull from Bank Soal instead of generating on the fly
    try:
        all_published = db_service.get_published_bank_soal()
        if not all_published:
            raise HTTPException(status_code=500, detail="Bank soal belum dipublish oleh admin. Silakan hubungi admin.")

        final_soal = []
        import random
        
        for bank in all_published:
            soal_pool = bank.get("soal", [])
            if not soal_pool:
                continue
            
            # Select 5 random questions from this bab
            selected = random.sample(soal_pool, min(5, len(soal_pool)))
            final_soal.extend(selected)

        if not final_soal:
            raise HTTPException(status_code=500, detail="Gagal mengambil soal dari bank soal.")

        # Re-number for the session
        for i, s in enumerate(final_soal):
            s["nomor"] = i + 1

        saved = db_service.save_pretest(nip, final_soal)
        return saved
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gagal mengambil soal dari database: {str(e)}")


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
