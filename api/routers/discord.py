"""
TG Player API - Discord Router
Handles Discord voice control, party state, collaborative queue, and WebSocket synchronization.
"""
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.models import UserExternalAccount, utcnow
from api.routers.auth import get_current_user
from api.schemas.common import TelegramUser
from api.services.discord_service import discord_service

logger = logging.getLogger("tg_player.discord")
router = APIRouter(prefix="/discord", tags=["discord"])


# =============================================================================
# Request & Response Schemas
# =============================================================================

class ConnectRequest(BaseModel):
    channel_id: int

class PlayRequest(BaseModel):
    track: Dict[str, Any]
    queue: Optional[List[Dict[str, Any]]] = None
    position: float = 0.0

class QueueAddRequest(BaseModel):
    track: Dict[str, Any]

class VolumeRequest(BaseModel):
    volume: int = Field(..., ge=0, le=100)

class SeekRequest(BaseModel):
    position: float = Field(..., ge=0)

class DjLockRequest(BaseModel):
    locked: bool

class TransferDjRequest(BaseModel):
    target_user_id: int

class LinkDiscordRequest(BaseModel):
    discord_id: str
    username: Optional[str] = ""
    display_name: Optional[str] = ""


# =============================================================================
# Helpers
# =============================================================================

async def get_user_discord_account(user_id: int, db: AsyncSession) -> Optional[UserExternalAccount]:
    """Fetch user's linked Discord account if present"""
    stmt = (
        select(UserExternalAccount)
        .where(
            UserExternalAccount.user_id == user_id,
            UserExternalAccount.provider == "discord"
        )
    )
    return await db.scalar(stmt)


def build_user_context(user: TelegramUser, discord_acc: Optional[UserExternalAccount]) -> Dict[str, Any]:
    """Build unified user representation for party state & queue metadata"""
    return {
        "id": user.id,
        "username": user.username or f"user_{user.id}",
        "display_name": f"{user.first_name} {user.last_name or ''}".strip(),
        "avatar_url": user.photo_url,
        "discord_id": discord_acc.external_id if discord_acc else None,
        "discord_username": discord_acc.username if discord_acc else None,
    }


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/party")
async def get_party_status(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current party state. Includes active voice channel, members,
    currently playing track, queue, DJ lock status, and whether current user is in voice.
    """
    discord_acc = await get_user_discord_account(user.id, db)
    user_ctx = build_user_context(user, discord_acc)
    return discord_service.get_party_state(user_ctx)


@router.get("/user-state")
async def get_user_voice_state(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check if the current user is sitting in any voice channel on Discord.
    Used for 1-click 'Join My Voice Channel' magic connect.
    """
    discord_acc = await get_user_discord_account(user.id, db)
    if not discord_acc or not discord_acc.external_id:
        return {
            "is_linked": False,
            "in_voice": False,
            "channel": None,
        }

    detected_channel = discord_service.find_user_voice_channel(discord_acc.external_id)
    return {
        "is_linked": True,
        "in_voice": detected_channel is not None,
        "channel": detected_channel,
        "discord_username": discord_acc.username,
    }


@router.get("/channels")
async def get_available_channels(
    user: TelegramUser = Depends(get_current_user),
):
    """List all servers and voice channels where the bot is present"""
    return discord_service.get_available_channels()


@router.get("/invite")
async def get_bot_invite():
    """Get Discord bot invite URL with appropriate Voice permissions"""
    return {
        "invite_url": discord_service.get_invite_url(),
        "is_configured": discord_service.is_configured,
    }


@router.post("/connect")
async def connect_voice_channel(
    req: ConnectRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Connect bot to a specific Discord voice channel"""
    discord_acc = await get_user_discord_account(user.id, db)
    user_ctx = build_user_context(user, discord_acc)
    try:
        state = await discord_service.connect_to_channel(req.channel_id, user_ctx)
        return state
    except (PermissionError, ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/disconnect")
async def disconnect_voice_channel(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect bot from voice channel and stop playback"""
    discord_acc = await get_user_discord_account(user.id, db)
    user_ctx = build_user_context(user, discord_acc)

    if discord_service.dj_lock and not discord_service._can_user_control(user_ctx):
        raise HTTPException(status_code=403, detail="Только текущий DJ может отключить бота.")

    await discord_service.disconnect()
    return {"status": "disconnected"}


@router.post("/play")
async def play_track_in_discord(
    req: PlayRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start streaming track/queue into Discord voice channel"""
    discord_acc = await get_user_discord_account(user.id, db)
    user_ctx = build_user_context(user, discord_acc)
    try:
        state = await discord_service.play_track(
            req.track,
            user_ctx,
            new_queue=req.queue,
            position=req.position,
        )
        return state
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pause")
async def pause_playback(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pause playback in Discord"""
    discord_acc = await get_user_discord_account(user.id, db)
    user_ctx = build_user_context(user, discord_acc)
    try:
        await discord_service.pause(user_ctx)
        return {"status": "paused"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/resume")
async def resume_playback(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume playback in Discord"""
    discord_acc = await get_user_discord_account(user.id, db)
    user_ctx = build_user_context(user, discord_acc)
    try:
        await discord_service.resume(user_ctx)
        return {"status": "resumed"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/stop")
async def stop_playback(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stop playback in Discord"""
    discord_acc = await get_user_discord_account(user.id, db)
    user_ctx = build_user_context(user, discord_acc)
    try:
        await discord_service.stop(user_ctx)
        return {"status": "stopped"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/skip")
async def skip_track(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Skip to next track in Discord queue"""
    discord_acc = await get_user_discord_account(user.id, db)
    user_ctx = build_user_context(user, discord_acc)
    try:
        await discord_service.skip(user_ctx)
        return {"status": "skipped"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/seek")
async def seek_playback(
    req: SeekRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Seek position in Discord playback"""
    discord_acc = await get_user_discord_account(user.id, db)
    user_ctx = build_user_context(user, discord_acc)
    try:
        await discord_service.seek(req.position, user_ctx)
        return {"status": "seeked", "position": req.position}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/volume")
async def set_playback_volume(
    req: VolumeRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Adjust Discord playback volume (0 to 100)"""
    discord_acc = await get_user_discord_account(user.id, db)
    user_ctx = build_user_context(user, discord_acc)
    await discord_service.set_volume(req.volume, user_ctx)
    return {"status": "ok", "volume": req.volume}


# =============================================================================
# Queue Management (Collaborative Queue)
# =============================================================================

@router.post("/queue")
async def add_track_to_queue(
    req: QueueAddRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add track to party queue. Available to all members of the voice party!"""
    discord_acc = await get_user_discord_account(user.id, db)
    user_ctx = build_user_context(user, discord_acc)
    new_length = await discord_service.add_to_queue(req.track, user_ctx)
    return {"status": "added", "queue_length": new_length}


@router.delete("/queue/{index}")
async def remove_track_from_queue(
    index: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a track from party queue (Host or adder)"""
    discord_acc = await get_user_discord_account(user.id, db)
    user_ctx = build_user_context(user, discord_acc)
    try:
        await discord_service.remove_from_queue(index, user_ctx)
        return {"status": "removed"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# =============================================================================
# DJ & Role Management
# =============================================================================

@router.post("/dj/lock")
async def toggle_dj_lock(
    req: DjLockRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle DJ lock mode (only current DJ can toggle)"""
    discord_acc = await get_user_discord_account(user.id, db)
    user_ctx = build_user_context(user, discord_acc)
    try:
        await discord_service.set_dj_lock(req.locked, user_ctx)
        return {"dj_lock": req.locked}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/dj/transfer")
async def transfer_dj_role(
    req: TransferDjRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Transfer DJ role to another user in party"""
    discord_acc = await get_user_discord_account(user.id, db)
    user_ctx = build_user_context(user, discord_acc)

    # Find target user in current members
    target_user = None
    party_state = discord_service.get_party_state()
    for m in party_state.get("members", []):
        if m.get("id") == str(req.target_user_id) or str(req.target_user_id) in m.get("id", ""):
            target_user = {
                "id": req.target_user_id,
                "display_name": m.get("display_name"),
                "username": m.get("username"),
            }
            break

    if not target_user:
        target_user = {"id": req.target_user_id, "display_name": "New DJ"}

    try:
        await discord_service.transfer_dj(target_user, user_ctx)
        return {"status": "transferred", "new_dj": target_user}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# =============================================================================
# Discord Account Linking
# =============================================================================

@router.get("/account")
async def get_linked_discord_account(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's linked Discord account"""
    acc = await get_user_discord_account(user.id, db)
    if not acc:
        return {"linked": False}
    return {
        "linked": True,
        "discord_id": acc.external_id,
        "username": acc.username,
        "display_name": acc.display_name,
        "avatar_url": acc.avatar_url,
    }


@router.post("/account")
async def link_discord_account(
    req: LinkDiscordRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link user's Discord ID (for voice channel auto-detection)"""
    clean_id = req.discord_id.strip()
    if not clean_id.isdigit():
        raise HTTPException(status_code=400, detail="Discord User ID должен состоять только из цифр")

    acc = await get_user_discord_account(user.id, db)
    if not acc:
        acc = UserExternalAccount(
            user_id=user.id,
            provider="discord",
            external_id=clean_id,
            username=req.username or f"discord_{clean_id}",
            display_name=req.display_name or req.username or f"User {clean_id}",
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        db.add(acc)
    else:
        acc.external_id = clean_id
        if req.username:
            acc.username = req.username
        if req.display_name:
            acc.display_name = req.display_name
        acc.updated_at = utcnow()

    await db.commit()
    logger.info(f"User {user.id} linked Discord account ID {clean_id}")
    return {
        "status": "linked",
        "discord_id": clean_id,
        "username": acc.username,
    }


@router.delete("/account")
async def unlink_discord_account(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unlink Discord account"""
    stmt = (
        delete(UserExternalAccount)
        .where(
            UserExternalAccount.user_id == user.id,
            UserExternalAccount.provider == "discord"
        )
    )
    await db.execute(stmt)
    await db.commit()
    return {"status": "unlinked"}


# =============================================================================
# WebSocket Real-Time Sync
# =============================================================================

@router.websocket("/ws")
async def websocket_discord_party(websocket: WebSocket):
    """
    Real-time WebSocket endpoint for instant synchronization of
    playback state, party participants, and queue updates.
    """
    await websocket.accept()
    discord_service.register_ws(websocket)
    try:
        # Send initial party state immediately upon connecting
        initial_state = discord_service.get_party_state(None)
        await websocket.send_json({"type": "party_update", "data": initial_state})

        # Keep-alive ping/pong loop
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"Discord WebSocket error: {e}")
    finally:
        discord_service.unregister_ws(websocket)
