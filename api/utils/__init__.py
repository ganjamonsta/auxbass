"""
TG Player API - Shared Utility Functions

Re-exports from sub-modules for convenience.
"""
from fastapi import HTTPException

from api.utils.responses import (
    track_to_response,
    album_to_response,
    build_track_search_filter,
    streamable_track_filter,
    is_streamable,
    is_hd_format,
    STREAMABLE_MIME_TYPES,
    HD_MIME_TYPES,
    MAX_STREAMABLE_SIZE_BYTES,
)
from api.utils.bot_helpers import (
    get_bot,
    close_bot,
    get_http_session,
    close_http_session,
)

# Legacy alias — original function was named with underscore
_get_bot = get_bot


def raise_not_found(detail: str = "Not found"):
    raise HTTPException(status_code=404, detail=detail)
