"""
Quiz router — end-of-chapter quiz based on bank soal.
"""
import random
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import db_service

router = APIRouter()

class QuizSubmit(BaseModel):
    jawaban: dict  # { "1": "A", "2": "C", ... }

@router.get("/quiz/{nip}/{bab_nomor}")
async def get_quiz(nip: str, bab_nomor: int):
    """
    Get quiz questions for a user + chapter.
    Pulls 5 random questions from the published bank soal for that chapter.
    Allows retake if previous attempt score < 70.
    """
    user = db_service.get_user(nip)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    # Check if quiz already completed
    existing = db_service.get_quiz_result(nip, bab_nomor)
    if existing and existing.get("completed"):
        # Ensure benar and total are available for the frontend
        soal = existing.get("soal", [])
        benar = sum(1 for s in soal if s.get("jawaban_user", "").strip().upper() == s.get("jawaban_benar", "").strip().upper())
        existing["benar"] = benar
        existing["total"] = len(soal)
        return existing

    # Pull from bank soal
    bank = db_service.get_bank_soal_by_bab(bab_nomor)
    if not bank or bank.get("status") != "published":
        raise HTTPException(
            status_code=400, 
            detail=f"Bank soal untuk Bab {bab_nomor} belum tersedia atau belum dipublish oleh admin."
        )

    all_soal = bank.get("soal", [])
    if len(all_soal) < 5:
        # Fallback if bank has fewer than 5 questions
        selected_soal = random.sample(all_soal, len(all_soal))
    else:
        selected_soal = random.sample(all_soal, 5)

    # Re-number for the quiz session
    for i, s in enumerate(selected_soal):
        s["nomor"] = i + 1

    saved = db_service.save_quiz_attempt(nip, bab_nomor, selected_soal)
    return saved

@router.post("/quiz/{nip}/{bab_nomor}/submit")
async def submit_quiz(nip: str, bab_nomor: int, body: QuizSubmit):
    """Submit quiz answers, calculate score, and mark chapter as complete."""
    quiz = db_service.get_quiz_result(nip, bab_nomor)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz belum dimulai.")

    if quiz.get("completed"):
        soal = quiz["soal"]
        # Calculate for response consistency
        benar = sum(1 for s in soal if s.get("jawaban_user", "").strip().upper() == s.get("jawaban_benar", "").strip().upper())
        return {
            "message": "Quiz sudah diselesaikan", 
            "nilai": quiz["nilai"], 
            "benar": benar,
            "total": len(soal),
            "soal": soal
        }

    soal = quiz["soal"]
    benar = 0
    total = len(soal)

    for s in soal:
        nomor = str(s["nomor"])
        jawaban_user = body.jawaban.get(nomor, "").strip().upper()
        jawaban_benar = s.get("jawaban_benar", "").strip().upper()
        
        s["jawaban_user"] = jawaban_user
        if jawaban_user == jawaban_benar:
            benar += 1

    nilai = round((benar / total) * 100) if total > 0 else 0
    
    # Submit result
    result = db_service.submit_quiz_result(nip, bab_nomor, nilai, soal)
    
    # Mark bab as complete in progress table
    db_service.mark_bab_complete(nip, f"bab{bab_nomor}")

    return {
        "message": "Quiz berhasil disubmit",
        "nilai": nilai,
        "benar": benar,
        "total": total,
        "soal": soal,
    }
