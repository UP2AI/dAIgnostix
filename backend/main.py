"""
E-Learning AI Platform — FastAPI Backend
Entry point for the application.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import CORS_ORIGINS

app = FastAPI(
    title="E-Learning AI API",
    description="Backend API untuk Kemenkeu E-Learning Platform dengan AI & RAG",
    version="1.0.0",
)

# --- CORS ---
# Note: allow_credentials=True cannot be used with allow_origins=["*"]
origins = CORS_ORIGINS if CORS_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True if "*" not in origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static Files (PDF materi) ---
MATERI_DIR = os.path.join(os.path.dirname(__file__), "data", "materi")
os.makedirs(MATERI_DIR, exist_ok=True)
app.mount("/data/materi", StaticFiles(directory=MATERI_DIR), name="materi-files")

# --- Routers ---
from routers import user, pretest, learning_path, materi, posttest, feedback, admin

app.include_router(user.router, prefix="/api", tags=["User"])
app.include_router(pretest.router, prefix="/api", tags=["Pretest"])
app.include_router(learning_path.router, prefix="/api", tags=["Learning Path"])
app.include_router(materi.router, prefix="/api", tags=["Materi"])
app.include_router(posttest.router, prefix="/api", tags=["Posttest"])
app.include_router(feedback.router, prefix="/api", tags=["Feedback"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])


@app.get("/")
async def root():
    return {"message": "E-Learning AI API is running!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
