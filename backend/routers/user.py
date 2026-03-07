"""
User router — registration and profile management.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import db_service

router = APIRouter()


class UserRegister(BaseModel):
    nip: str
    nama: str


@router.post("/user/register")
async def register_user(body: UserRegister):
    """Register a new user or return existing user."""
    existing = db_service.get_user(body.nip)
    if existing:
        return {"message": "User sudah terdaftar", "user": existing}

    user = db_service.create_user(body.nip, body.nama)

    # Initialize materi progress using dynamic bab from DB
    bab_list = db_service.get_all_bab()
    if bab_list:
        bab_names = [f"bab{b['nomor']}" for b in bab_list]
    else:
        bab_names = ["bab1", "bab2", "bab3", "bab4"]  # fallback

    db_service.init_materi_progress(body.nip, bab_names)

    return {"message": "User berhasil didaftarkan", "user": user}


@router.get("/user/{nip}")
async def get_user(nip: str):
    """Get user data by NIP."""
    user = db_service.get_user(nip)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return user


@router.get("/user/{nip}/status")
async def get_user_status(nip: str):
    """Get user progress status (0-4)."""
    user = db_service.get_user(nip)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    progress = db_service.get_user_progress(nip)
    return {"nip": nip, "nama": user["nama"], "role": user.get("role", "user"), **progress}
