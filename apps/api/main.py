from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Argus Financial Document Intelligence API",
    description="Evidence-first financial document extraction, verification, and audit platform.",
    version="1.0.0",
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from apps.api.routers import documents_router
app.include_router(documents_router)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness probe verifying API health."""
    return HealthResponse(
        status="healthy",
        service="argus-api",
        version="1.0.0",
    )


@app.get("/")
async def root():
    return {
        "message": "Argus Financial Intelligence Engine",
        "docs_url": "/docs",
        "status": "operational",
    }
