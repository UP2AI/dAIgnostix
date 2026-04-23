"""
Learning Path router — generate AI learning path from pretest results.
"""
from fastapi import APIRouter, HTTPException
from services import db_service, ai_service

router = APIRouter()


@router.get("/learning-path/{nip}")
async def get_learning_path(nip: str):
    """
    Get or generate learning path for a user.
    Requires pretest to be completed first.
    """
    user = db_service.get_user(nip)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    # Check if already exists
    existing = db_service.get_learning_path(nip)
    if existing:
        return existing

    # Check pretest is done
    pretest = db_service.get_pretest(nip)
    if not pretest or not pretest.get("completed"):
        raise HTTPException(status_code=400, detail="Pretest belum diselesaikan")

    # Generate via AI
    try:
        lp_data = ai_service.generate_learning_path(pretest)
        saved = db_service.save_learning_path(nip, lp_data)
        return saved
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gagal generate learning path dari AI: {str(e)}")
