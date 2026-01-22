"""
TG Player API - Entry Point
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import get_settings
from shared.database import init_db, close_db

from api.routers import tracks, playlists, player, auth


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="TG Player API",
    description="API for TG Player Mini App",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.webapp_url,
        "https://telegram.org",
        "https://*.telegram.org",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(tracks.router, prefix="/api/tracks", tags=["Tracks"])
app.include_router(playlists.router, prefix="/api/playlists", tags=["Playlists"])
app.include_router(player.router, prefix="/api/player", tags=["Player"])


@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "service": "TG Player API"}


@app.get("/api/health")
async def health():
    """API health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
