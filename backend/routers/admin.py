"""
Admin router — E-Learning management, user management, PDF upload & indexing.
"""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from services import db_service, rag_service, ai_service

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

class BankSoalUpdate(BaseModel):
    soal: list
    status: str = "draft"


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

@router.post("/admin/bab/{bab_id}/upload-materi-pdf")
async def upload_bab_materi_pdf(bab_id: int, file: UploadFile = File(...)):
    """Upload user-facing materi PDF for a specific bab (NOT indexed to vector DB)."""
    existing = db_service.get_bab_by_id(bab_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Bab tidak ditemukan")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Hanya file PDF yang diizinkan")

    os.makedirs(PDF_DIR, exist_ok=True)

    safe_filename = f"bab{existing['nomor']}_materi_{file.filename}"
    filepath = os.path.join(PDF_DIR, safe_filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    db_service.update_bab_materi_pdf(bab_id, safe_filename)
    return {
        "message": f"PDF Materi berhasil diupload",
        "filename": safe_filename,
    }


@router.get("/admin/bab/{bab_id}/serve-materi-pdf")
async def serve_materi_pdf(bab_id: int):
    """Serve the user-facing materi PDF file for display in frontend."""
    bab = db_service.get_bab_by_id(bab_id)
    if not bab:
        raise HTTPException(status_code=404, detail="Bab tidak ditemukan")

    filename = bab.get("pdf_materi_filename", "")
    if not filename:
        # Fallback to RAG PDF if no separate materi PDF
        filename = bab.get("pdf_filename", "")
    if not filename:
        raise HTTPException(status_code=404, detail="Bab ini belum memiliki PDF materi")

    filepath = os.path.join(PDF_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File PDF tidak ditemukan di server")

    return FileResponse(
        filepath,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=\"{filename}\""},
    )


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


# ======================== BANK SOAL MANAGEMENT ========================

@router.post("/admin/bank-soal/generate")
async def generate_all_bank_soal(bab_id: int = None):
    """
    Generate bank soal for all bab or a specific bab using AI.
    """
    if bab_id:
        babs = [db_service.get_bab_by_id(bab_id)]
        if not babs[0]:
            raise HTTPException(status_code=404, detail="Bab tidak ditemukan")
    else:
        babs = db_service.get_all_bab()

    results = []
    for b in babs:
        try:
            # Query context for this bab
            context = rag_service.query_materi(f"materi lengkap {b['judul']} bab {b['nomor']}", k=10)
            if not context:
                results.append({"bab": b["nomor"], "status": "error", "message": "Context RAG kosong"})
                continue
            
            soal = ai_service.generate_bank_soal_questions(context, b["nomor"], b["judul"])
            saved = db_service.save_bank_soal(b["nomor"], b["judul"], soal)
            results.append({"bab": b["nomor"], "status": "success", "id": saved.get("id")})
        except Exception as e:
            results.append({"bab": b["nomor"], "status": "error", "message": str(e)})

    return {"message": "Proses generate selesai", "results": results}

@router.get("/admin/bank-soal")
async def list_bank_soal():
    """List all bank soal entries."""
    bank = db_service.get_all_bank_soal()
    return {"bank_soal": bank}

@router.get("/admin/bank-soal/{bab_nomor}")
async def get_bank_soal(bab_nomor: int):
    """Get bank soal for a chapter."""
    bank = db_service.get_bank_soal_by_bab(bab_nomor)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank soal belum dibuat")
    return bank

@router.put("/admin/bank-soal/{bank_id}")
async def update_bank_soal(bank_id: int, body: BankSoalUpdate):
    """Update bank soal questions or status."""
    result = db_service.update_bank_soal_status(bank_id, body.status)
    # Also update questions
    from services.db_service import supabase
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    res = supabase.table("bank_soal").update({
        "soal": body.soal, 
        "status": body.status,
        "updated_at": now
    }).eq("id", bank_id).execute()
    
    return {"message": "Bank soal berhasil diupdate", "bank": res.data[0] if res.data else {}}

@router.post("/admin/bank-soal/{bank_id}/publish")
async def publish_bank_soal(bank_id: int):
    """Mark bank soal as published."""
    result = db_service.update_bank_soal_status(bank_id, "published")
    return {"message": "Bank soal berhasil dipublish", "bank": result}

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
