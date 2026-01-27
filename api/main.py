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
app.include_router(albums_router, prefix="/api/albums", tags=["Albums"])
app.include_router(artists_router, prefix="/api/artists", tags=["Artists"])
app.include_router(playlists_router, prefix="/api/playlists", tags=["Playlists"])
app.include_router(player_router, prefix="/api/player", tags=["Player"])


@app.get("/")
async def root():
    return {"status": "ok", "service": "TG Player API v2"}


@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_v2:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
