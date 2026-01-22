"""
TG Player API - Entry Point
"""
import sys
import time
import re
from pathlib import Path
from contextlib import asynccontextmanager
from collections import defaultdict

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from shared.config import get_settings
from shared.database import init_db, close_db

from api.routers import tracks, playlists, player, auth


settings = get_settings()


# ============== Rate Limiting ==============
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
        
        # Get client IP (consider X-Forwarded-For for reverse proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > minute_ago
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down."
            )
        
        # Record this request
        self.requests[client_ip].append(now)
        
        return await call_next(request)


# ============== Input Sanitization ==============
def sanitize_search_input(query: str) -> str:
    """Sanitize search input to prevent SQL injection and XSS"""
    if not query:
        return ""
    # Remove SQL special characters
    query = re.sub(r'[;\'"\\%_]', '', query)
    # Limit length
    return query[:100].strip()


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

# Add rate limiting (60 requests per minute per IP)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

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
