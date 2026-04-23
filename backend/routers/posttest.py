"""
Posttest router — Adaptive Stage-Based Testing.

Flow:
1. GET  /posttest/{nip}              → Load soal (stage 1: 25 Level-2 questions) + session recovery
2. POST /posttest/{nip}/save-answer  → Save each answer in real-time (backend-only recovery)
3. POST /posttest/{nip}/checkpoint   → Branching gate after Q25 → returns soal 26-30
4. POST /posttest/{nip}/submit       → Final submission with weighted scoring + kategori
5. POST /posttest/{nip}/retake       → Reset for retake
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import db_service, ai_service, rag_service

router = APIRouter()

WEIGHT_LEVEL2 = 3.2  # poin per soal Level 2
WEIGHT_LEVEL3 = 4.0  # poin per soal Level 3
MAX_ATTEMPTS = 5


class PosttestSubmit(BaseModel):
    jawaban: dict  # { "1": "A", "2": "C", ... }


class SaveAnswerBody(BaseModel):
    nomor: int
    jawaban: str


def _pick_soal_from_bank(all_published: list, level: int, count: int, exclude_questions: list = None) -> list:
    """Pick questions from published bank soal by level, round-robin across chapters."""
    import random
    exclude_questions = exclude_questions or []

    pools = {}
    for b in all_published:
        soal_pool = b.get("soal", [])
        level_soal = [s for s in soal_pool if s.get("level", 2) == level]
        # Exclude already-used questions
        available = [s for s in level_soal if s.get("pertanyaan") not in exclude_questions]
        if available:
            random.shuffle(available)
            pools[b['bab_nomor']] = available

    if not pools:
        return []

    final = []
    chapter_ids = list(pools.keys())
    random.shuffle(chapter_ids)

    while len(final) < count:
        added = 0
        for b_id in chapter_ids:
            if pools.get(b_id):
                final.append(pools[b_id].pop(0))
                added += 1
                if len(final) >= count:
                    break
        if added == 0:
            break

    return final


def _calculate_score(soal: list, jawaban: dict) -> tuple:
    """Calculate weighted score. Returns (total_score, benar_count, details)."""
    total_score = 0.0
    benar = 0
    for s in soal:
        nomor = str(s["nomor"])
        jawaban_user = jawaban.get(nomor, "").strip().upper()
        s["jawaban_user"] = jawaban_user
        jawaban_benar = s.get("jawaban_benar", "").strip().upper()
        level = s.get("level", 2)
        weight = WEIGHT_LEVEL3 if level == 3 else WEIGHT_LEVEL2

        if jawaban_user == jawaban_benar:
            benar += 1
            total_score += weight

    return round(total_score), benar, soal


def _determine_kategori(jalur: str, nilai: int, soal_26_30: list, jawaban: dict) -> str:
    """Determine final category based on branching gate logic."""
    if jalur == "A":
        return "Pemula" if nilai < 80 else "Menengah"
    elif jalur == "B":
        # Count correct Level 3 answers (soal 26-30)
        benar_l3 = 0
        for s in soal_26_30:
            nomor = str(s["nomor"])
            jwb = jawaban.get(nomor, "").strip().upper()
            if jwb == s.get("jawaban_benar", "").strip().upper():
                benar_l3 += 1

        if benar_l3 >= 3:
            return "Mahir"
        else:
            return "Menengah"
    return "Menengah"


@router.get("/posttest/{nip}")
async def get_posttest(nip: str):
    """
    Get posttest for a user with session recovery support.
    Stage 1: Returns 25 Level-2 questions.
    If session exists with saved answers, returns resume data.
    """
    user = db_service.get_user(nip)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    # Mark all chapters as complete upon accessing posttest
    db_service.mark_all_bab_complete(nip)

    existing = db_service.get_posttest(nip)
    if existing:
        existing["max_attempts"] = MAX_ATTEMPTS
        existing["attempts"] = existing.get("attempts", 1) if existing.get("attempts") is not None else 1
        return existing

    # Generate new posttest from bank soal
    try:
        all_published = db_service.get_published_bank_soal()
        if not all_published:
            raise HTTPException(status_code=500, detail="Bank soal belum dipublish.")

        # Get pretest questions to avoid duplicates
        pretest = db_service.get_pretest(nip)
        pretest_questions = []
        if pretest:
            pretest_questions = [s.get("pertanyaan") for s in pretest.get("soal", [])]

        # Stage 1: Pick 25 Level 2 (Normal) questions
        soal_stage1 = _pick_soal_from_bank(all_published, level=2, count=25, exclude_questions=pretest_questions)

        if len(soal_stage1) < 25:
            # Fallback: if not enough Level 2, pick from all available
            remaining = 25 - len(soal_stage1)
            used_q = pretest_questions + [s.get("pertanyaan") for s in soal_stage1]
            extra = _pick_soal_from_bank(all_published, level=2, count=remaining, exclude_questions=[])
            soal_stage1.extend(extra[:remaining])

        if not soal_stage1:
            raise HTTPException(status_code=500, detail="Gagal mengambil soal posttest.")

        # Number questions 1-25, mark as stage1
        for i, s in enumerate(soal_stage1):
            s["nomor"] = i + 1
            s["level"] = s.get("level", 2)

        saved = db_service.save_posttest(nip, soal_stage1)
        return saved
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gagal mengambil soal posttest: {str(e)}")


@router.post("/posttest/{nip}/save-answer")
async def save_answer(nip: str, body: SaveAnswerBody):
    """Save a single answer in real-time (for lost connection recovery)."""
    posttest = db_service.get_posttest(nip)
    if not posttest:
        raise HTTPException(status_code=404, detail="Posttest belum ada.")
    if posttest.get("completed"):
        return {"message": "Posttest sudah diselesaikan"}

    result = db_service.save_answer(nip, body.nomor, body.jawaban)
    return {"message": "Jawaban tersimpan", "nomor": body.nomor}


@router.post("/posttest/{nip}/checkpoint")
async def checkpoint(nip: str):
    """
    Branching gate: evaluate score after Q25, then serve soal 26-30.
    - Score < 80 → Jalur A (Level 2 questions)
    - Score ≥ 80 → Jalur B (Level 3 HOTS questions)
    """
    posttest = db_service.get_posttest(nip)
    if not posttest:
        raise HTTPException(status_code=404, detail="Posttest belum ada.")

    if posttest.get("completed"):
        return {"message": "Posttest sudah diselesaikan", "jalur": posttest.get("jalur")}

    # Check adaptive state
    adaptive_state = posttest.get("adaptive_state") or {}
    if adaptive_state.get("checkpoint_done"):
        # Already checkpointed — return existing soal
        return {
            "message": "Checkpoint sudah dilakukan",
            "jalur": posttest.get("jalur"),
            "soal": posttest.get("soal", []),
            "checkpoint_score": adaptive_state.get("checkpoint_score", 0),
        }

    saved_jawaban = posttest.get("saved_jawaban") or {}
    soal_stage1 = posttest.get("soal", [])

    # Calculate checkpoint score (soal 1-25, all Level 2, weight 3.2)
    checkpoint_benar = 0
    for s in soal_stage1:
        nomor = str(s["nomor"])
        jawaban_user = saved_jawaban.get(nomor, "").strip().upper()
        jawaban_benar = s.get("jawaban_benar", "").strip().upper()
        if jawaban_user == jawaban_benar:
            checkpoint_benar += 1

    checkpoint_score = round(checkpoint_benar * WEIGHT_LEVEL2)

    # Determine jalur
    if checkpoint_score >= 80:
        jalur = "B"
        soal_level = 3  # Level 3 Expert/HOTS
    else:
        jalur = "A"
        soal_level = 2  # Level 2 Normal

    # Pick soal 26-30
    try:
        all_published = db_service.get_published_bank_soal()
        used_questions = [s.get("pertanyaan") for s in soal_stage1]

        soal_stage2 = _pick_soal_from_bank(
            all_published, level=soal_level, count=5, exclude_questions=used_questions
        )

        # Fallback if not enough soal of requested level
        if len(soal_stage2) < 5:
            remaining = 5 - len(soal_stage2)
            used_q = used_questions + [s.get("pertanyaan") for s in soal_stage2]
            # Try opposite level as fallback
            fallback_level = 2 if soal_level == 3 else 3
            extra = _pick_soal_from_bank(all_published, level=fallback_level, count=remaining, exclude_questions=used_q)
            soal_stage2.extend(extra[:remaining])

        # Number as 26-30
        for i, s in enumerate(soal_stage2):
            s["nomor"] = 26 + i
            s["level"] = soal_level  # Mark with the intended level

        # Combine with stage 1
        full_soal = soal_stage1 + soal_stage2

        # Update adaptive state
        new_state = {
            "phase": "stage2",
            "checkpoint_done": True,
            "checkpoint_score": checkpoint_score,
            "checkpoint_benar": checkpoint_benar,
            "jalur": jalur,
        }

        db_service.update_adaptive_state(nip, new_state)
        db_service.update_posttest_soal(nip, full_soal, jalur=jalur)

        return {
            "message": f"Checkpoint selesai. Jalur: {jalur}",
            "jalur": jalur,
            "checkpoint_score": checkpoint_score,
            "checkpoint_benar": checkpoint_benar,
            "soal_stage2": soal_stage2,
            "soal": full_soal,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gagal memproses checkpoint: {str(e)}")


@router.post("/posttest/{nip}/submit")
async def submit_posttest(nip: str, body: PosttestSubmit):
    """Submit posttest answers with weighted scoring and kategori determination."""
    posttest = db_service.get_posttest(nip)
    if not posttest:
        raise HTTPException(status_code=404, detail="Posttest belum ada.")

    if posttest.get("completed"):
        return {
            "message": "Posttest sudah diselesaikan",
            "nilai": posttest["nilai"],
            "soal": posttest["soal"],
            "kategori": posttest.get("kategori"),
            "jalur": posttest.get("jalur"),
        }

    soal = posttest["soal"]
    jalur = posttest.get("jalur") or "A"

    # Calculate weighted score
    nilai, benar, soal_updated = _calculate_score(soal, body.jawaban)

    # Determine soal 26-30 for kategori logic
    soal_26_30 = [s for s in soal if s.get("nomor", 0) >= 26]

    # Determine kategori
    kategori = _determine_kategori(jalur, nilai, soal_26_30, body.jawaban)

    # Passing grade logic
    lulus = nilai >= 80

    # Save to DB
    result = db_service.submit_posttest(nip, nilai, soal_updated, jalur=jalur, kategori=kategori)

    return {
        "message": "Posttest berhasil disubmit",
        "nilai": nilai,
        "benar": benar,
        "total": len(soal),
        "soal": soal_updated,
        "lulus": lulus,
        "jalur": jalur,
        "kategori": kategori,
    }


@router.post("/posttest/{nip}/retake")
async def retake_posttest(nip: str):
    """Retake posttest if attempts are below max_attempts."""
    posttest = db_service.get_posttest(nip)
    if not posttest:
        raise HTTPException(status_code=404, detail="Posttest belum ada.")

    attempts = posttest.get("attempts", 1) if posttest.get("attempts") is not None else 1

    if attempts >= MAX_ATTEMPTS:
        raise HTTPException(status_code=400, detail=f"Batas maksimal attempt ({MAX_ATTEMPTS} kali) sudah tercapai.")

    new_attempts = attempts + 1

    # Re-generate fresh soal from bank soal (stage 1 only)
    try:
        all_published = db_service.get_published_bank_soal()
        if not all_published:
            raise HTTPException(status_code=500, detail="Bank soal belum dipublish.")

        pretest = db_service.get_pretest(nip)
        pretest_questions = [s.get("pertanyaan") for s in pretest.get("soal", [])] if pretest else []

        soal_stage1 = _pick_soal_from_bank(all_published, level=2, count=25, exclude_questions=pretest_questions)

        if len(soal_stage1) < 25:
            extra = _pick_soal_from_bank(all_published, level=2, count=25 - len(soal_stage1), exclude_questions=[])
            soal_stage1.extend(extra[:25 - len(soal_stage1)])

        for i, s in enumerate(soal_stage1):
            s["nomor"] = i + 1
            s["jawaban_user"] = ""
            s["level"] = s.get("level", 2)

        updated = db_service.reset_posttest_for_retake(nip, new_attempts, soal_stage1)

        # Clear feedback so it can be regenerated
        db_service.delete_feedback(nip)

        updated["max_attempts"] = MAX_ATTEMPTS
        updated["attempts"] = new_attempts
        return updated
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gagal reset posttest: {str(e)}")
