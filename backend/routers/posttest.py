"""
Posttest router — generate and submit posttest.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import db_service, ai_service, rag_service

router = APIRouter()


class PosttestSubmit(BaseModel):
    jawaban: dict  # { "1": "A", "2": "C", ... }


@router.get("/posttest/{nip}")
async def get_posttest(nip: str):
    """
    Get posttest questions for a user.
    If not yet generated, AI will generate them via RAG.
    Requires materi to be completed.
    """
    user = db_service.get_user(nip)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    existing = db_service.get_posttest(nip)
    if existing:
        existing["max_attempts"] = 5
        existing["attempts"] = existing.get("attempts", 1) if existing.get("attempts") is not None else 1
        return existing

    # Generate via AI + RAG
    try:
        context = rag_service.query_materi("materi audit internal keuangan negara lengkap semua bab untuk posttest", k=15)
        if not context:
            raise HTTPException(status_code=500, detail="Materi belum diindex.")

        # Get dynamic bab list for proportional question generation
        bab_list = db_service.get_all_bab()

        soal = ai_service.generate_posttest_questions(context, bab_list=bab_list if bab_list else None)
        saved = db_service.save_posttest(nip, soal)
        saved["max_attempts"] = 5
        saved["attempts"] = saved.get("attempts", 1) if saved.get("attempts") is not None else 1
        return saved
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gagal generate soal dari AI: {str(e)}")


@router.post("/posttest/{nip}/submit")
async def submit_posttest(nip: str, body: PosttestSubmit):
    """Submit posttest answers and calculate score."""
    posttest = db_service.get_posttest(nip)
    if not posttest:
        raise HTTPException(status_code=404, detail="Posttest belum ada.")

    if posttest.get("completed"):
        return {"message": "Posttest sudah diselesaikan", "nilai": posttest["nilai"], "soal": posttest["soal"]}

    soal = posttest["soal"]
    benar = 0
    total = len(soal)

    for s in soal:
        nomor = str(s["nomor"])
        jawaban_user = body.jawaban.get(nomor, "")
        s["jawaban_user"] = jawaban_user
        if jawaban_user == s["jawaban_benar"]:
            benar += 1

    nilai = round((benar / total) * 100) if total > 0 else 0
    result = db_service.submit_posttest(nip, nilai, soal)

    return {
        "message": "Posttest berhasil disubmit",
        "nilai": nilai,
        "benar": benar,
        "total": total,
        "soal": soal,
    }


@router.post("/posttest/{nip}/retake")
async def retake_posttest(nip: str):
    """Retake posttest if attempts are below max_attempts."""
    posttest = db_service.get_posttest(nip)
    if not posttest:
        raise HTTPException(status_code=404, detail="Posttest belum ada.")
    
    attempts = posttest.get("attempts", 1) if posttest.get("attempts") is not None else 1
    max_attempts = 5
    
    if attempts >= max_attempts:
        raise HTTPException(status_code=400, detail="Batas maksimal attempt (5 kali) sudah tercapai.")
    
    new_attempts = attempts + 1
    soal_bersih = posttest.get("soal", [])
    
    # Kosongkan jawaban sebelumnya saat retake
    for s in soal_bersih:
        s["jawaban_user"] = ""
    
    try:
        updated = db_service.reset_posttest_for_retake(nip, new_attempts, soal_bersih)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gagal reset posttest: {str(e)}")
        
    updated["max_attempts"] = max_attempts
    updated["attempts"] = updated.get("attempts", new_attempts) if updated.get("attempts") is not None else new_attempts
    return updated
