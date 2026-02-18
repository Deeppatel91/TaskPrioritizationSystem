
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router #router paths TASK PERFORMANCE/app/api/routes.py
from app.services.db_service import init_db

init_db()

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

# #Browser → Middleware → API Route → Middleware → Response
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#for creting database tables if they don't exist yet
@app.on_event("startup")
def on_startup():
    """Create database tables if they don't exist yet."""
    init_db()



app.include_router(router)

#redirect root to docs
@app.get("/", include_in_schema=False)
def root():
    return {"message": "Task Prioritization API — visit /docs for interactive documentation."}





#interactive docs links /docs and OPEN API /openapi.json