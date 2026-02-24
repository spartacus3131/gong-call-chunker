import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import require_api_key
from .routers import analytics, calls, chunks, schemas

app = FastAPI(
    title="Gong Call Chunker",
    description="Extract structured intelligence from sales call transcripts",
    version="1.0.0",
)

origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All /api/v1 routes require API key when API_KEYS env var is set.
# Health endpoint is always open.
api_deps = [Depends(require_api_key)]

app.include_router(calls.router, prefix="/api/v1/calls", tags=["calls"], dependencies=api_deps)
app.include_router(chunks.router, prefix="/api/v1/chunks", tags=["chunks"], dependencies=api_deps)
app.include_router(schemas.router, prefix="/api/v1/schemas", tags=["schemas"], dependencies=api_deps)
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"], dependencies=api_deps)


@app.get("/health")
def health():
    return {"status": "ok"}
