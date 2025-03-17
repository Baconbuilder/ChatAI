from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import auth, conversations, documents
from app.core.config import settings
import os

app = FastAPI(
    title="GPT Interface API",
    description="API for GPT Interface application",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# # Mount static files directory
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(conversations.router, prefix="/api", tags=["conversations"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
# app.include_router(upload.router, prefix="/api", tags=["upload"])

@app.get("/api/health")
def health_check():
    return {"status": "ok"} 