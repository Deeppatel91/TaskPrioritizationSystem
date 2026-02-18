"""
main.py
═══════
FastAPI application entry point.

Run locally:
    uvicorn main:app --reload

Interactive docs:
    http://localhost:8000/docs
    http://localhost:8000/redoc
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Change this in main.py

from app.api.routes import router
from app.services.db_service import init_db
# Somewhere in your startup logic:
init_db()
# ── Application factory ────────────────────────────────────────────────────────

app = FastAPI(
    title="Task Prioritization System",
    description=(
        "A deterministic task prioritization engine. "
        "Submit tasks with deadline, effort, and importance attributes "
        "and receive a priority score (0–100) and category (High / Medium / Low)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow all origins for development; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup event ──────────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    """Create database tables if they don't exist yet."""
    init_db()


# ── Register routes ────────────────────────────────────────────────────────────

app.include_router(router)


# ── Root redirect ──────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root():
    return {"message": "Task Prioritization API — visit /docs for interactive documentation."}