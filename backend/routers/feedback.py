"""
Feedback router — generate AI feedback from all user data.
"""
from fastapi import APIRouter, HTTPException
from services import db_service, ai_service

router = APIRouter()


@router.get("/feedback/{nip}")
async def get_feedback(nip: str):
    """
    Get or generate AI feedback for a user.
    Requires posttest to be completed.
    """
    user = db_service.get_user(nip)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    # Gather data anyway to enrich the response
    pretest = db_service.get_pretest(nip)
    posttest = db_service.get_posttest(nip)
    learning_path = db_service.get_learning_path(nip)

    # Check posttest is done
    if not posttest or not posttest.get("completed"):
        raise HTTPException(status_code=400, detail="Posttest belum diselesaikan")

    # Check if feedback already exists in DB
    feedback_data = db_service.get_feedback(nip)
    
    if not feedback_data:
        # Generate via AI if not exists
        materi_progress = db_service.get_materi_progress(nip)
        events = db_service.get_events(nip)
        
        # Determine if failed (score < 80)
        is_failed = posttest.get("nilai", 0) < 80
        
        # Get e-learning title for more targeted feedback
        elearning_config = db_service.get_elearning_config()
        elearning_title = elearning_config.get("judul", "E-Learning") if elearning_config else "E-Learning"

        try:
            ai_generated = ai_service.generate_feedback(
                pretest_data=pretest or {},
                posttest_data=posttest,
                learning_path_data=learning_path or {},
                materi_progress=materi_progress,
                events=events,
                is_failed_posttest=is_failed,
                elearning_title=elearning_title
            )
            feedback_data = db_service.save_feedback(nip, ai_generated)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Gagal generate feedback dari AI: {str(e)}")

    # Enrich response with scores and initial profile for frontend display
    if isinstance(feedback_data, dict):
        feedback_data["pretest_nilai"] = pretest.get("nilai") if pretest else 0
        feedback_data["posttest_nilai"] = posttest.get("nilai") if posttest else 0
        feedback_data["profil_awal"] = learning_path.get("profil") if learning_path else "N/A"
        
    return feedback_data
