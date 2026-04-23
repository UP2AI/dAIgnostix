"""
Materi router — progress tracking, event logging, and public bab/config access.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import db_service

router = APIRouter()


@router.get("/materi/config")
async def get_public_config():
    """Public: Get e-learning config and bab list for frontend."""
    config = db_service.get_elearning_config()
    bab_list = db_service.get_all_bab()
    return {
        "config": config or {"judul": "E-Learning", "deskripsi": ""},
        "bab": bab_list,
        "total_bab": len(bab_list),
    }


@router.get("/materi/bab-list")
async def get_public_bab_list():
    """Public: Get all bab info for the frontend."""
    bab_list = db_service.get_all_bab()
    return {"bab": bab_list, "total": len(bab_list)}


class TrackEvent(BaseModel):
    page: str
    action: str
    duration_seconds: int = 0


class TrackTime(BaseModel):
    bab: str
    seconds: int


@router.get("/materi/{nip}/progress")
async def get_progress(nip: str):
    """Get materi progress for a user."""
    user = db_service.get_user(nip)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    progress = db_service.get_materi_progress(nip)
    return {"nip": nip, "progress": progress}


@router.post("/materi/{nip}/track")
async def track_event(nip: str, body: TrackEvent):
    """Log a user event (page visit, time tracking heartbeat)."""
    db_service.save_event(nip, body.page, body.action, body.duration_seconds)
    return {"message": "Event tracked"}


@router.post("/materi/{nip}/time")
async def track_time(nip: str, body: TrackTime):
    """Update time spent on a specific bab."""
    db_service.update_materi_time(nip, body.bab, body.seconds)
    return {"message": "Time updated"}


@router.post("/materi/{nip}/complete/{bab}")
async def complete_bab(nip: str, bab: str):
    """Mark a bab as completed."""
    user = db_service.get_user(nip)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    db_service.mark_bab_complete(nip, bab)
    return {"message": f"{bab} marked as complete"}
