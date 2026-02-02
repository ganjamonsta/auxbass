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

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from shared.config import get_settings
from shared.database import init_db, close_db

from bot.services.channels import init_channel_service, get_channel_service, start_channel_service, stop_channel_service

from api.routers import auth
from api.routers.library import router as library_router
from api.routers.tracks import router as tracks_router
from api.routers.albums import router as albums_router
from api.routers.artists import router as artists_router
from api.routers.playlists import router as playlists_router
from api.routers.images import router as images_router
from api.routers.player import router as player_router, close_http_session
from api.routers.social import router as social_router


settings = get_settings()

# Global bot instance for API
api_bot: Bot = None


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


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add cache-control headers to GET requests for cacheable resources"""
    
    # Cache durations for different endpoints (in seconds)
    CACHE_RULES = {
        r'/api/tracks/liked': 60,              # 1 minute - liked tracks change frequently
        r'/api/tracks/global/stats': 120,      # 2 minutes - statistics
        r'/api/library/stats': 120,            # 2 minutes - statistics  
        r'/api/tracks/genres': 1800,           # 30 minutes - genres
        r'/api/tracks/artists': 1800,          # 30 minutes - artists list
        r'/api/artists/.+/info': 900,          # 15 minutes - artist details
        r'/api/artists/.+/tracks': 900,        # 15 minutes - artist tracks
        r'/api/artists/global': 600,           # 10 minutes - global artists
        r'/api/artists': 600,                  # 10 minutes - artists
        r'/api/albums/global': 600,            # 10 minutes - global albums
        r'/api/albums': 600,                   # 10 minutes - albums
        r'/api/playlists': 300,                # 5 minutes - playlists
        r'/api/tracks': 180,                   # 3 minutes - tracks
    }
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only add cache headers to successful GET requests
        if request.method == "GET" and response.status_code == 200:
            path = request.url.path
            
            # Skip cache headers for streaming and images
            if "/api/player/audio/" in path or "/api/images/" in path:
                return response
            
            # Find matching cache rule
            max_age = None
            for pattern, duration in self.CACHE_RULES.items():
                if re.match(pattern, path):
                    max_age = duration
                    break
            
            if max_age:
                # Add cache-control header
                # - private: only client can cache (not CDN/proxy)
                # - max-age: how long to cache
                # - must-revalidate: check with server when stale
                response.headers["Cache-Control"] = f"private, max-age={max_age}, must-revalidate"
                response.headers["X-Cache-TTL"] = str(max_age)
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global api_bot
    
    await init_db()
    
    # Initialize bot for channel service
    api_bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    init_channel_service(api_bot)
    
    # Start channel service queue worker for auto-forwarding liked tracks
    await start_channel_service()
    
    yield
    
    # Cleanup
    await stop_channel_service()
    if api_bot:
        await api_bot.session.close()
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

# Cache control
app.add_middleware(CacheControlMiddleware)

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
app.include_router(images_router, prefix="/api", tags=["Images"])
app.include_router(player_router, prefix="/api/player", tags=["Player"])
app.include_router(social_router, prefix="/api", tags=["Social"])


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
        # Read into memory to avoid BaseHTTPMiddleware conflict with FileResponse
        from fastapi.responses import Response
        content = index_path.read_bytes()
        return Response(content=content, media_type="text/html")
    
    return {"error": "webapp not built", "hint": "run: cd webapp && npm run build"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_v2:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
