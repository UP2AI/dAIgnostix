"""
Admin router — E-Learning management, user management, PDF upload & indexing.
"""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from services import db_service, rag_service

router = APIRouter()

PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "materi")


# ======================== MODELS ========================

class ConfigBody(BaseModel):
    judul: str
    deskripsi: str = ""


class BabBody(BaseModel):
    nomor: int
    judul: str
    deskripsi: str = ""


class RoleBody(BaseModel):
    role: str  # "admin" or "user"


# ======================== E-LEARNING CONFIG ========================

@router.get("/admin/config")
async def get_config():
    """Get e-learning configuration."""
    config = db_service.get_elearning_config()
    if not config:
        return {"judul": "E-Learning", "deskripsi": ""}
    return config


@router.post("/admin/config")
async def save_config(body: ConfigBody):
    """Save/update e-learning configuration."""
    result = db_service.save_elearning_config(body.judul, body.deskripsi)
    return {"message": "Konfigurasi berhasil disimpan", "config": result}


# ======================== BAB MANAGEMENT ========================

@router.get("/admin/bab")
async def list_bab():
    """List all bab."""
    babs = db_service.get_all_bab()
    return {"bab": babs, "total": len(babs)}


@router.post("/admin/bab")
async def create_bab(body: BabBody):
    """Create a new bab."""
    result = db_service.add_bab(body.nomor, body.judul, body.deskripsi)
    return {"message": f"Bab {body.nomor} berhasil ditambahkan", "bab": result}


@router.put("/admin/bab/{bab_id}")
async def update_bab(bab_id: int, body: BabBody):
    """Update an existing bab."""
    existing = db_service.get_bab_by_id(bab_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Bab tidak ditemukan")
    result = db_service.update_bab(bab_id, body.nomor, body.judul, body.deskripsi)
    return {"message": f"Bab {body.nomor} berhasil diupdate", "bab": result}


@router.delete("/admin/bab/{bab_id}")
async def remove_bab(bab_id: int):
    """Delete a bab."""
    existing = db_service.get_bab_by_id(bab_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Bab tidak ditemukan")
    db_service.delete_bab(bab_id)
    return {"message": f"Bab berhasil dihapus"}


# ======================== PDF UPLOAD & INDEXING ========================

@router.post("/admin/bab/{bab_id}/upload-pdf")
async def upload_bab_pdf(bab_id: int, file: UploadFile = File(...)):
    """Upload PDF for a specific bab and auto-index to vector DB."""
    existing = db_service.get_bab_by_id(bab_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Bab tidak ditemukan")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Hanya file PDF yang diizinkan")

    os.makedirs(PDF_DIR, exist_ok=True)

    # Use bab identifier in filename
    safe_filename = f"bab{existing['nomor']}_{file.filename}"
    filepath = os.path.join(PDF_DIR, safe_filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Update DB with filename
    db_service.update_bab_pdf(bab_id, safe_filename, indexed=False)

    # Auto-index to vector DB
    try:
        bab_label = f"Bab {existing['nomor']}"
        chunk_count = rag_service.index_pdf(filepath, bab_label)
        db_service.mark_bab_indexed(bab_id)
        return {
            "message": f"PDF berhasil diupload dan diindex ({chunk_count} chunks)",
            "filename": safe_filename,
            "chunks": chunk_count,
            "indexed": True,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "message": f"PDF berhasil diupload, tapi gagal index: {str(e)}",
            "filename": safe_filename,
            "chunks": 0,
            "indexed": False,
        }


@router.post("/admin/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Legacy: Upload a PDF file to the server."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Hanya file PDF yang diizinkan")

    os.makedirs(PDF_DIR, exist_ok=True)
    filepath = os.path.join(PDF_DIR, file.filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    return {"message": f"File {file.filename} berhasil diupload", "path": filepath}


@router.post("/admin/index-pdf")
async def index_pdf(filename: str = ""):
    """
    Index PDF(s) into pgvector.
    If filename is provided, index only that file.
    If empty, index all PDFs in data/materi/.
    """
    if filename:
        filepath = os.path.join(PDF_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"File {filename} tidak ditemukan")

        bab = filename.split("_")[0]
        count = rag_service.index_pdf(filepath, bab)
        return {"message": f"{filename} berhasil diindex", "chunks": count}
    else:
        results = rag_service.index_all_pdfs(PDF_DIR)
        total = sum(results.values()) if isinstance(results, dict) and "error" not in results else 0
        return {"message": "Indexing selesai", "results": results, "total_chunks": total}


@router.post("/admin/reindex-bab/{bab_id}")
async def reindex_bab(bab_id: int):
    """Re-index a specific bab's PDF into vector DB."""
    bab = db_service.get_bab_by_id(bab_id)
    if not bab:
        raise HTTPException(status_code=404, detail="Bab tidak ditemukan")
    if not bab.get("pdf_filename"):
        raise HTTPException(status_code=400, detail="Bab ini belum memiliki PDF")

    filepath = os.path.join(PDF_DIR, bab["pdf_filename"])
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"File PDF tidak ditemukan di server")

    try:
        bab_label = f"Bab {bab['nomor']}"
        count = rag_service.index_pdf(filepath, bab_label)
        db_service.mark_bab_indexed(bab_id)
        return {"message": f"Re-index berhasil ({count} chunks)", "chunks": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal re-index: {str(e)}")


# ======================== USER MANAGEMENT ========================

@router.get("/admin/users")
async def list_users():
    """List all users with their basic info."""
    users = db_service.get_all_users()
    return {"users": users, "total": len(users)}


@router.get("/admin/users/{nip}/detail")
async def user_detail(nip: str):
    """Get detailed user info including progress."""
    user = db_service.get_user(nip)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    progress = db_service.get_user_progress(nip)
    return {"user": user, "progress": progress}


@router.put("/admin/users/{nip}/role")
async def change_user_role(nip: str, body: RoleBody):
    """Update a user's role."""
    if body.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Role harus 'admin' atau 'user'")
    user = db_service.get_user(nip)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    result = db_service.update_user_role(nip, body.role)
    return {"message": f"Role user {nip} diubah menjadi {body.role}", "user": result}


@router.delete("/admin/users/{nip}")
async def remove_user(nip: str):
    """Delete a user and all related data."""
    user = db_service.get_user(nip)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    db_service.delete_user_cascade(nip)
    return {"message": f"User {nip} dan semua data terkait berhasil dihapus"}


# ======================== DATABASE OVERVIEW ========================

@router.get("/admin/db-overview")
async def db_overview():
    """Get overview of all database tables."""
    overview = db_service.get_db_overview()
    return {"tables": overview}


@router.delete("/admin/vectors")
async def clear_vectors():
    """Clear all vector data (materi_chunks) for re-indexing."""
    count = db_service.clear_all_chunks()
    # Reset all bab indexed status
    babs = db_service.get_all_bab()
    for b in babs:
        db_service.update_bab_pdf(b["id"], b.get("pdf_filename", ""), indexed=False)
    return {"message": f"Berhasil menghapus {count} chunks. Semua bab perlu di-index ulang."}
