from typing import Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routes import users

app = FastAPI(title="FlavorNet API")

# Allow the local development frontend(s) to call the API without CORS errors.
allowed_origins: Sequence[str] = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)


@app.get("/")
def root():
    return {"message": "FlavorNet backend is running!"}


# Serve the static frontend for convenience (optional) when available (e.g. local dev).
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount(
        "/frontend",
        StaticFiles(directory=frontend_dir, html=True),
        name="frontend",
    )
