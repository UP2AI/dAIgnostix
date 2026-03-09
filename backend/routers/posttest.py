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

    # Mark all chapters as complete upon accessing posttest
    db_service.mark_all_bab_complete(nip)

    existing = db_service.get_posttest(nip)
    if existing:
        existing["max_attempts"] = 5
        existing["attempts"] = existing.get("attempts", 1) if existing.get("attempts") is not None else 1
        return existing

    # Pull from Bank Soal instead of AI generation
    try:
        all_published = db_service.get_published_bank_soal()
        if not all_published:
            raise HTTPException(status_code=500, detail="Bank soal belum dipublish.")

        pretest = db_service.get_pretest(nip)
        pretest_questions = []
        if pretest:
            # Gather questions already seen in pretest to avoid duplicates if possible
            pretest_questions = [s.get("pertanyaan") for s in pretest.get("soal", [])]

        import random
        total_target = 30
        chapters = [b for b in all_published if b.get("soal")]
        
        if not chapters:
             raise HTTPException(status_code=500, detail="Bank soal kosong.")

        final_soal = []
        # Prepare pools, prioritizing questions NOT in pretest
        pools = {}
        for b in chapters:
            soal_pool = b.get("soal", [])
            new_questions = [s for s in soal_pool if s.get("pertanyaan") not in pretest_questions]
            seen_questions = [s for s in soal_pool if s.get("pertanyaan") in pretest_questions]
            
            random.shuffle(new_questions)
            random.shuffle(seen_questions)
            # Combine: new questions first, then seen questions as fallback
            pools[b['bab_nomor']] = new_questions + seen_questions

        # Round-robin selection to ensure proportionality
        chapter_ids = list(pools.keys())
        random.shuffle(chapter_ids)
        
        while len(final_soal) < total_target:
            added_this_round = 0
            for b_id in chapter_ids:
                if pools[b_id]:
                    question = pools[b_id].pop(0)
                    final_soal.append(question)
                    added_this_round += 1
                    if len(final_soal) >= total_target:
                        break
            if added_this_round == 0:
                break

        if not final_soal:
            raise HTTPException(status_code=500, detail="Gagal mengambil soal posttest.")

        # Re-number for the session
        for i, s in enumerate(final_soal):
            s["nomor"] = i + 1

        saved = db_service.save_posttest(nip, final_soal)
        return saved
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gagal mengambil soal posttest: {str(e)}")


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
        jawaban_user = body.jawaban.get(nomor, "").strip().upper()
        s["jawaban_user"] = jawaban_user
        jawaban_benar = s["jawaban_benar"].strip().upper()
        if jawaban_user == jawaban_benar:
            benar += 1

    nilai = round((benar / total) * 100) if total > 0 else 0
    result = db_service.submit_posttest(nip, nilai, soal)

    # passing grade logic
    lulus = nilai >= 80

    return {
        "message": "Posttest berhasil disubmit",
        "nilai": nilai,
        "benar": benar,
        "total": total,
        "soal": soal,
        "lulus": lulus
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
        # Clear feedback so it can be regenerated with new results
        db_service.delete_feedback(nip)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gagal reset posttest: {str(e)}")
        
    updated["max_attempts"] = max_attempts
    updated["attempts"] = updated.get("attempts", new_attempts) if updated.get("attempts") is not None else new_attempts
    return updated
