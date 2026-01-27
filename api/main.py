"""
TG Player API v2 - Entry Point

Uses new modular architecture with separated routers.
"""
import sys
import time
import re
from pathlib import Path
from contextlib import asynccontextmanager
from collections import defaultdict

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from shared.config import get_settings
from shared.database import init_db, close_db

from api.routers import auth
from api.routers.library import router as library_router
from api.routers.tracks import router as tracks_router
from api.routers.albums import router as albums_router
from api.routers.artists import router as artists_router
from api.routers.playlists import router as playlists_router
from api.routers.player import router as player_router, close_http_session


settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for audio streaming
        if "/api/player/audio/" in request.url.path:
            return await call_next(request)
        
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        now = time.time()
        minute_ago = now - 60
        
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > minute_ago
        ]
        
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."}
            )
        
        self.requests[client_ip].append(now)
        
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    await init_db()
    yield
    await close_http_session()
    await close_db()


app = FastAPI(
    title="TG Player API v2",
    description="API for TG Player Mini App",
    version="2.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.add_middleware(RateLimitMiddleware, requests_per_minute=600)

# CORS
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

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(library_router, prefix="/api/library", tags=["Library"])
app.include_router(tracks_router, prefix="/api/tracks", tags=["Tracks"])
app.include_router(albums_router, prefix="/api/albums", tags=["Albums"])
app.include_router(artists_router, prefix="/api/artists", tags=["Artists"])
app.include_router(playlists_router, prefix="/api/playlists", tags=["Playlists"])
app.include_router(player_router, prefix="/api/player", tags=["Player"])


# ============== Static Files & SPA Fallback ==============
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Path to webapp dist
WEBAPP_DIST = Path(__file__).parent.parent / "webapp" / "dist"

# Serve static assets (js, css, images, etc.)
if WEBAPP_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEBAPP_DIST / "assets"), name="assets")
    
    # Serve other static files from dist root
    @app.get("/manifest.json")
    async def manifest():
        return FileResponse(WEBAPP_DIST / "manifest.json")
    
    @app.get("/sw.js")
    async def service_worker():
        return FileResponse(WEBAPP_DIST / "sw.js", media_type="application/javascript")
    
    @app.get("/favicon.ico")
    async def favicon():
        favicon_path = WEBAPP_DIST / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        return {"error": "not found"}


@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "2.0.0"}


# SPA Fallback - must be LAST route
# Catches all non-API routes and serves index.html
@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    """Serve index.html for all non-API routes (SPA client-side routing)"""
    # Don't serve index.html for API routes
    if full_path.startswith("api/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    index_path = WEBAPP_DIST / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    
    return {"error": "webapp not built", "hint": "run: cd webapp && npm run build"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_v2:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
