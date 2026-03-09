"""
Supabase Database Service — CRUD operations for all tables.
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ======================== USERS ========================

def get_user(nip: str) -> dict | None:
    """Get user by NIP. Returns None if not found."""
    res = supabase.table("users").select("*").eq("nip", nip).execute()
    return res.data[0] if res.data else None


def create_user(nip: str, nama: str) -> dict:
    """Create a new user."""
    data = {"nip": nip, "nama": nama}
    res = supabase.table("users").insert(data).execute()
    return res.data[0]


def get_user_progress(nip: str) -> dict:
    """
    Determine the user's progress state based on database data.
    Returns { progress_state: 0-4, details: {...} }
    
    States:
      0 = belum pretest
      1 = pretest done, belum semua materi
      2 = semua materi done, belum posttest
      3 = posttest done, belum feedback
      4 = feedback done (celebration)
    """
    state = 0
    details = {}

    # Check pretest
    pretest = get_pretest(nip)
    if pretest and pretest.get("completed"):
        state = 1
        details["pretest_nilai"] = pretest.get("nilai")

    # Check materi progress
    materi = get_materi_progress(nip)
    details["materi"] = materi
    if materi:
        all_done = all(m.get("finished") for m in materi)
        if all_done and state >= 1:
            state = 2

    # Check posttest
    posttest = get_posttest(nip)
    if posttest and posttest.get("completed"):
        state = 3
        details["posttest_nilai"] = posttest.get("nilai")

    # Check feedback
    fb = get_feedback(nip)
    if fb:
        state = 4

    # Check pages accessed (events tracker)
    events_res = supabase.table("events").select("page").eq("nip", nip).in_("page", ["learningpath", "feedback"]).execute()
    accessed_pages = {e.get("page") for e in events_res.data} if events_res.data else set()
    details["lp_accessed"] = "learningpath" in accessed_pages
    details["fb_accessed"] = "feedback" in accessed_pages

    details["progress_state"] = state
    return details


# ======================== PRETEST ========================

def get_pretest(nip: str) -> dict | None:
    res = supabase.table("pretest").select("*").eq("nip", nip).execute()
    return res.data[0] if res.data else None


def save_pretest(nip: str, soal: list) -> dict:
    """Save AI-generated pretest questions."""
    data = {"nip": nip, "soal": soal, "completed": False}
    res = supabase.table("pretest").insert(data).execute()
    return res.data[0]


def submit_pretest(nip: str, nilai: int, soal_updated: list) -> dict:
    """Submit pretest answers — save score and mark as completed."""
    from datetime import datetime, timezone
    res = (
        supabase.table("pretest")
        .update({
            "nilai": nilai,
            "soal": soal_updated,
            "completed": True,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        .eq("nip", nip)
        .execute()
    )
    return res.data[0] if res.data else {}


# ======================== LEARNING PATH ========================

def get_learning_path(nip: str) -> dict | None:
    res = supabase.table("learning_path").select("*").eq("nip", nip).execute()
    return res.data[0] if res.data else None


def save_learning_path(nip: str, data: dict) -> dict:
    row = {
        "nip": nip,
        "profil": data.get("profil", ""),
        "penjabaran": data.get("penjabaran_profil", ""),
        "skor_pretest": data.get("skor_pretest", 0),
        "bab_fokus": data.get("learning_path", {}).get("fokus_utama", []),
        "bab_opsional": data.get("learning_path", {}).get("opsional", []),
    }
    res = supabase.table("learning_path").insert(row).execute()
    return res.data[0] if res.data else {}


# ======================== MATERI PROGRESS ========================

def get_materi_progress(nip: str) -> list:
    res = supabase.table("materi_progress").select("*").eq("nip", nip).execute()
    return res.data


def init_materi_progress(nip: str, bab_list: list[str]) -> list:
    """Initialize materi progress rows for a user (one per bab)."""
    rows = [{"nip": nip, "bab": bab, "finished": False, "time_spent_seconds": 0} for bab in bab_list]
    res = supabase.table("materi_progress").insert(rows).execute()
    return res.data


def mark_bab_complete(nip: str, bab: str) -> dict:
    res = (
        supabase.table("materi_progress")
        .update({"finished": True})
        .eq("nip", nip)
        .eq("bab", bab)
        .execute()
    )
    return res.data[0] if res.data else {}


def mark_all_bab_complete(nip: str) -> list:
    """Mark all chapters as finished for a user."""
    res = (
        supabase.table("materi_progress")
        .update({"finished": True})
        .eq("nip", nip)
        .execute()
    )
    return res.data


def update_materi_time(nip: str, bab: str, seconds: int) -> dict:
    """Increment time_spent_seconds for a bab."""
    # Get current time first
    current = (
        supabase.table("materi_progress")
        .select("time_spent_seconds")
        .eq("nip", nip)
        .eq("bab", bab)
        .execute()
    )
    current_time = current.data[0]["time_spent_seconds"] if current.data else 0
    res = (
        supabase.table("materi_progress")
        .update({"time_spent_seconds": current_time + seconds})
        .eq("nip", nip)
        .eq("bab", bab)
        .execute()
    )
    return res.data[0] if res.data else {}


# ======================== EVENTS TRACKER ========================

def save_event(nip: str, page: str, action: str, duration_seconds: int) -> dict:
    data = {
        "nip": nip,
        "page": page,
        "action": action,
        "duration_seconds": duration_seconds,
    }
    res = supabase.table("events").insert(data).execute()
    return res.data[0] if res.data else {}


def get_events(nip: str) -> list:
    res = supabase.table("events").select("*").eq("nip", nip).execute()
    return res.data


# ======================== POSTTEST ========================

def get_posttest(nip: str) -> dict | None:
    res = supabase.table("posttest").select("*").eq("nip", nip).execute()
    return res.data[0] if res.data else None


def save_posttest(nip: str, soal: list) -> dict:
    data = {"nip": nip, "soal": soal, "completed": False}
    res = supabase.table("posttest").insert(data).execute()
    return res.data[0]


def submit_posttest(nip: str, nilai: int, soal_updated: list) -> dict:
    from datetime import datetime, timezone
    res = (
        supabase.table("posttest")
        .update({
            "nilai": nilai,
            "soal": soal_updated,
            "completed": True,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        .eq("nip", nip)
        .execute()
    )
    return res.data[0] if res.data else {}


def reset_posttest_for_retake(nip: str, new_attempts: int, soal_bersih: list) -> dict:
    try:
        res = (
            supabase.table("posttest")
            .update({
                "completed": False,
                "nilai": 0,
                "soal": soal_bersih,
                "attempts": new_attempts
            })
            .eq("nip", nip)
            .execute()
        )
        return res.data[0] if res.data else {}
    except Exception as e:
        # Fallback if `attempts` column does not exist in DB yet
        print(f"Warning: 'attempts' column may not exist. {e}")
        res = (
            supabase.table("posttest")
            .update({
                "completed": False,
                "nilai": 0,
                "soal": soal_bersih
            })
            .eq("nip", nip)
            .execute()
        )
        return res.data[0] if res.data else {}


# ======================== FEEDBACK ========================

def get_feedback(nip: str) -> dict | None:
    res = supabase.table("feedback").select("*").eq("nip", nip).execute()
    return res.data[0] if res.data else None


def save_feedback(nip: str, data: dict) -> dict:
    row = {
        "nip": nip,
        "profil_akhir": data.get("profil_akhir", ""),
        "analisis_perkembangan": data.get("analisis_perkembangan", ""),
        "evaluasi_perilaku": data.get("evaluasi_perilaku", ""),
        "transformasi_profil": data.get("transformasi_profil", ""),
        "kesimpulan_strategis": data.get("kesimpulan_strategis", ""),
    }
    res = supabase.table("feedback").insert(row).execute()
    return res.data[0] if res.data else {}


# ======================== MATERI CHUNKS (pgvector) ========================

def insert_chunk(content: str, metadata: dict, embedding: list) -> dict:
    data = {
        "content": content,
        "metadata": metadata,
        "embedding": embedding,
    }
    res = supabase.table("materi_chunks").insert(data).execute()
    return res.data[0] if res.data else {}


def search_chunks(query_embedding: list, match_count: int = 10) -> list:
    """Similarity search via Supabase RPC (match_materi function)."""
    res = supabase.rpc("match_materi", {
        "query_embedding": query_embedding,
        "match_count": match_count,
    }).execute()
    return res.data


def clear_all_chunks() -> int:
    """Delete all materi_chunks (for re-indexing)."""
    res = supabase.table("materi_chunks").select("id").execute()
    count = len(res.data)
    if count > 0:
        supabase.table("materi_chunks").delete().neq("id", 0).execute()
    return count


# ======================== ADMIN — USERS ========================

def get_all_users() -> list:
    """List all users."""
    res = supabase.table("users").select("*").order("created_at", desc=True).execute()
    return res.data


def update_user_role(nip: str, role: str) -> dict:
    """Update user role (admin/user)."""
    res = (
        supabase.table("users")
        .update({"role": role})
        .eq("nip", nip)
        .execute()
    )
    return res.data[0] if res.data else {}


def delete_user_cascade(nip: str) -> dict:
    """Delete user and all related data."""
    tables = ["events", "materi_progress", "pretest", "posttest",
              "learning_path", "feedback"]
    for t in tables:
        try:
            supabase.table(t).delete().eq("nip", nip).execute()
        except Exception:
            pass
    res = supabase.table("users").delete().eq("nip", nip).execute()
    return res.data[0] if res.data else {}


# ======================== ADMIN — E-LEARNING CONFIG ========================

def get_elearning_config() -> dict | None:
    """Get the single elearning_config row."""
    res = supabase.table("elearning_config").select("*").limit(1).execute()
    return res.data[0] if res.data else None


def save_elearning_config(judul: str, deskripsi: str) -> dict:
    """Upsert elearning config."""
    existing = get_elearning_config()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    if existing:
        res = (
            supabase.table("elearning_config")
            .update({"judul": judul, "deskripsi": deskripsi, "updated_at": now})
            .eq("id", existing["id"])
            .execute()
        )
    else:
        res = (
            supabase.table("elearning_config")
            .insert({"judul": judul, "deskripsi": deskripsi, "updated_at": now})
            .execute()
        )
    return res.data[0] if res.data else {}


# ======================== ADMIN — DYNAMIC BAB ========================

def get_all_bab() -> list:
    """List all bab ordered by nomor."""
    res = supabase.table("elearning_bab").select("*").order("nomor").execute()
    return res.data


def add_bab(nomor: int, judul: str, deskripsi: str = "") -> dict:
    """Add a new bab."""
    data = {"nomor": nomor, "judul": judul, "deskripsi": deskripsi}
    res = supabase.table("elearning_bab").insert(data).execute()
    return res.data[0] if res.data else {}


def update_bab(bab_id: int, nomor: int, judul: str, deskripsi: str = "") -> dict:
    """Update an existing bab."""
    data = {"nomor": nomor, "judul": judul, "deskripsi": deskripsi}
    res = (
        supabase.table("elearning_bab")
        .update(data)
        .eq("id", bab_id)
        .execute()
    )
    return res.data[0] if res.data else {}


def delete_bab(bab_id: int) -> dict:
    """Delete a bab."""
    res = supabase.table("elearning_bab").delete().eq("id", bab_id).execute()
    return res.data[0] if res.data else {}


def update_bab_pdf(bab_id: int, pdf_filename: str, indexed: bool = False) -> dict:
    """Update PDF filename and indexed status for a bab."""
    res = (
        supabase.table("elearning_bab")
        .update({"pdf_filename": pdf_filename, "indexed": indexed})
        .eq("id", bab_id)
        .execute()
    )
    return res.data[0] if res.data else {}


def update_bab_materi_pdf(bab_id: int, pdf_materi_filename: str) -> dict:
    """Update materi PDF filename for a bab (user-facing, not indexed)."""
    res = (
        supabase.table("elearning_bab")
        .update({"pdf_materi_filename": pdf_materi_filename})
        .eq("id", bab_id)
        .execute()
    )
    return res.data[0] if res.data else {}


def mark_bab_indexed(bab_id: int) -> dict:
    """Mark a bab as indexed (vector DB populated)."""
    res = (
        supabase.table("elearning_bab")
        .update({"indexed": True})
        .eq("id", bab_id)
        .execute()
    )
    return res.data[0] if res.data else {}


def get_bab_by_id(bab_id: int) -> dict | None:
    """Get a single bab by ID."""
    res = supabase.table("elearning_bab").select("*").eq("id", bab_id).execute()
    return res.data[0] if res.data else None


# ======================== BANK SOAL ========================

def get_all_bank_soal() -> list:
    """Get all bank soal entries."""
    res = supabase.table("bank_soal").select("*").order("bab_nomor").execute()
    return res.data

def get_bank_soal_by_bab(bab_nomor: int) -> dict | None:
    """Get bank soal for a specific chapter."""
    res = supabase.table("bank_soal").select("*").eq("bab_nomor", bab_nomor).execute()
    return res.data[0] if res.data else None

def get_published_bank_soal() -> list:
    """Get all published bank soal entries."""
    res = supabase.table("bank_soal").select("*").eq("status", "published").order("bab_nomor").execute()
    return res.data

def save_bank_soal(bab_nomor: int, bab_judul: str, soal: list, status: str = "draft") -> dict:
    """Upsert bank soal for a chapter."""
    existing = get_bank_soal_by_bab(bab_nomor)
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    
    data = {
        "bab_nomor": bab_nomor,
        "bab_judul": bab_judul,
        "soal": soal,
        "status": status,
        "updated_at": now
    }
    
    if existing:
        res = supabase.table("bank_soal").update(data).eq("id", existing["id"]).execute()
    else:
        res = supabase.table("bank_soal").insert(data).execute()
    return res.data[0] if res.data else {}

def update_bank_soal_status(bank_id: int, status: str) -> dict:
    """Update bank soal status (draft/published)."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    res = supabase.table("bank_soal").update({"status": status, "updated_at": now}).eq("id", bank_id).execute()
    return res.data[0] if res.data else {}

# ======================== QUIZ RESULTS ========================

def get_quiz_result(nip: str, bab_nomor: int) -> dict | None:
    """Get quiz result for a user and chapter."""
    res = (
        supabase.table("quiz_results")
        .select("*")
        .eq("nip", nip)
        .eq("bab_nomor", bab_nomor)
        .execute()
    )
    return res.data[0] if res.data else None

def save_quiz_attempt(nip: str, bab_nomor: int, soal: list) -> dict:
    """Save an initial quiz attempt."""
    existing = get_quiz_result(nip, bab_nomor)
    if existing and existing.get("completed"):
        return existing
        
    data = {
        "nip": nip,
        "bab_nomor": bab_nomor,
        "soal": soal,
        "completed": False,
        "nilai": 0
    }
    
    if existing:
        res = supabase.table("quiz_results").update(data).eq("id", existing["id"]).execute()
    else:
        res = supabase.table("quiz_results").insert(data).execute()
    return res.data[0] if res.data else {}

def submit_quiz_result(nip: str, bab_nomor: int, nilai: int, soal_updated: list) -> dict:
    """Submit quiz answers and mark as completed."""
    from datetime import datetime, timezone
    res = (
        supabase.table("quiz_results")
        .update({
            "nilai": nilai,
            "soal": soal_updated,
            "completed": True,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        .eq("nip", nip)
        .eq("bab_nomor", bab_nomor)
        .execute()
    )
    return res.data[0] if res.data else {}

# ======================== ADMIN — DB OVERVIEW ========================

def get_db_overview() -> dict:
    """Get row counts for key tables."""
    tables = ["users", "pretest", "posttest", "learning_path",
              "materi_progress", "feedback", "events", "materi_chunks",
              "elearning_config", "elearning_bab", "bank_soal", "quiz_results"]
    overview = {}
    for t in tables:
        try:
            res = supabase.table(t).select("id", count="exact").execute()
            overview[t] = res.count if res.count is not None else len(res.data)
        except Exception:
            overview[t] = "error"
    return overview
