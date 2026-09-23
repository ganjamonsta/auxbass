"""
TG Player API - Discord Router
Handles Discord voice control, party state, collaborative queue, and WebSocket synchronization.
"""
from typing import Optional, List, Dict, Any
import logging
import time
from datetime import datetime
from urllib.parse import urlencode

import aiohttp
import jwt
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import get_settings
from shared.database import get_db
from shared.models import UserExternalAccount, utcnow
from api.routers.auth import get_current_user
from api.schemas.common import TelegramUser
from api.services.discord_service import discord_service

logger = logging.getLogger("tg_player.discord")
settings = get_settings()
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
    import traceback
    try:
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
            "discord_id": discord_acc.external_id,
            "discord_username": discord_acc.username,
            "discord_display_name": discord_acc.display_name,
            "discord_avatar_url": discord_acc.avatar_url,
        }
    except Exception as e:
        logger.exception(f"Error in get_user_voice_state: {e}")
        return {
            "is_linked": False,
            "in_voice": False,
            "channel": None,
            "error": str(e),
            "trace": traceback.format_exc(),
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
# Discord Account Linking & OAuth2 Flow
# =============================================================================

@router.get("/oauth/url")
async def get_discord_oauth_url(
    user: TelegramUser = Depends(get_current_user),
):
    """
    Generate Discord OAuth2 authorization URL for 1-click account linking.
    Requires discord_client_id (or connected bot user ID) and discord_client_secret.
    """
    client_id = settings.discord_client_id.strip()
    if not client_id and discord_service.bot and discord_service.bot.user:
        client_id = str(discord_service.bot.user.id)

    if not client_id:
        return {
            "configured": False,
            "url": None,
            "message": "DISCORD_CLIENT_ID не настроен на сервере",
        }

    if not settings.discord_client_secret or not settings.discord_client_secret.strip():
        return {
            "configured": False,
            "url": None,
            "message": "DISCORD_CLIENT_SECRET не настроен в .env",
        }

    # State contains signed JWT to prevent CSRF and bind to Telegram user
    payload = {
        "sub": str(user.id),
        "purpose": "discord_oauth",
        "exp": int(time.time()) + 600,
    }
    state = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    redirect_uri = settings.effective_discord_redirect_uri

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": "identify",
        "state": state,
        "prompt": "consent",
    }
    oauth_url = f"https://discord.com/oauth2/authorize?{urlencode(params)}"
    return {
        "configured": True,
        "url": oauth_url,
        "redirect_uri": redirect_uri,
    }


@router.get("/oauth/callback", response_class=HTMLResponse)
async def discord_oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Discord OAuth2 redirect callback.
    Exchanges code for access token, fetches Discord profile,
    and updates/creates UserExternalAccount.
    """
    def render_result_html(is_success: bool, title: str, message: str, user_data: Optional[Dict[str, Any]] = None) -> HTMLResponse:
        theme_accent = "#1db954" if is_success else "#f44336"
        badge_bg = "rgba(29, 185, 84, 0.15)" if is_success else "rgba(244, 67, 54, 0.15)"
        badge_text = "Подключено" if is_success else "Ошибка"
        
        avatar_html = ""
        if user_data and user_data.get("avatar_url"):
            avatar_html = f'<img src="{user_data["avatar_url"]}" style="width: 72px; height: 72px; border-radius: 50%; margin-bottom: 16px; box-shadow: 0 4px 16px rgba(88,101,242,0.4);" alt="Avatar" />'

        import json
        json_payload = {
            "type": "discord_oauth_success" if is_success else "discord_oauth_error",
            **(user_data or {}),
            "error": message if not is_success else None,
        }
        payload_str = json.dumps(json_payload)

        html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — AuxBass</title>
  <style>
    body {{
      margin: 0;
      padding: 20px;
      box-sizing: border-box;
      background: #0d0d0d;
      color: #fff;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
    }}
    .card {{
      background: #1a1a1a;
      padding: 32px;
      border-radius: 20px;
      box-shadow: 8px 8px 20px rgba(0,0,0,0.6), -4px -4px 12px rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.05);
      text-align: center;
      max-width: 400px;
      width: 100%;
    }}
    h2 {{
      margin: 0 0 10px 0;
      font-size: 20px;
      color: #5865f2;
    }}
    p {{
      margin: 0 0 20px 0;
      color: #b0b0b0;
      font-size: 14px;
      line-height: 1.5;
    }}
    .badge {{
      display: inline-block;
      padding: 6px 16px;
      background: {badge_bg};
      color: {theme_accent};
      border-radius: 20px;
      font-weight: 600;
      font-size: 13px;
      border: 1px solid {theme_accent};
      margin-bottom: 12px;
    }}
    .closing-note {{
      font-size: 12px;
      color: #666;
      margin-top: 16px;
    }}
  </style>
</head>
<body>
  <div class="card">
    {avatar_html}
    <div class="badge">{badge_text}</div>
    <h2>{title}</h2>
    <p>{message}</p>
    <div class="closing-note">Это окно закроется автоматически...</div>
  </div>
  <script>
    const data = {payload_str};
    try {{
      if (window.opener) {{
        window.opener.postMessage(data, '*');
      }}
    }} catch (e) {{}}

    try {{
      if (typeof BroadcastChannel !== 'undefined') {{
        const bc = new BroadcastChannel('auxbass_discord_auth');
        bc.postMessage(data);
        bc.close();
      }}
    }} catch (e) {{}}

    setTimeout(() => {{
      try {{
        window.close();
      }} catch (e) {{}}
      setTimeout(() => {{
        window.location.href = '{settings.webapp_url}/#/settings';
      }}, 500);
    }}, 1200);
  </script>
</body>
</html>"""
        return HTMLResponse(content=html_content, status_code=200 if is_success else 400)

    # 1. Check for Discord-level error
    if error:
        msg = error_description or error
        logger.warning(f"Discord OAuth denied by user: {msg}")
        return render_result_html(False, "Авторизация отменена", f"Discord вернул ошибку: {msg}")

    if not code or not state:
        return render_result_html(False, "Неверный запрос", "Отсутствуют обязательные параметры code или state.")

    # 2. Verify state token
    try:
        payload = jwt.decode(state, settings.secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("purpose") != "discord_oauth":
            raise ValueError("Invalid purpose")
        user_id = int(payload["sub"])
    except Exception as e:
        logger.warning(f"Discord OAuth invalid state: {e}")
        return render_result_html(False, "Ошибка безопасности", "Сессия авторизации истекла или недействительна. Попробуйте снова.")

    # 3. Exchange code for access token
    client_id = settings.discord_client_id.strip()
    if not client_id and discord_service.bot and discord_service.bot.user:
        client_id = str(discord_service.bot.user.id)
    client_secret = settings.discord_client_secret.strip()
    redirect_uri = settings.effective_discord_redirect_uri

    if not client_id or not client_secret:
        return render_result_html(False, "Ошибка конфигурации", "CLIENT_ID или CLIENT_SECRET не настроены на сервере.")

    token_url = "https://discord.com/api/v10/oauth2/token"
    token_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=token_payload, headers=headers) as resp:
                if resp.status != 200:
                    err_body = await resp.text()
                    logger.error(f"Discord token exchange failed ({resp.status}): {err_body}")
                    return render_result_html(False, "Ошибка авторизации", "Не удалось получить токен от Discord. Попробуйте снова.")
                token_data = await resp.json()
                access_token = token_data.get("access_token")

            # Fetch user profile
            profile_url = "https://discord.com/api/v10/users/@me"
            auth_headers = {"Authorization": f"Bearer {access_token}"}
            async with session.get(profile_url, headers=auth_headers) as resp:
                if resp.status != 200:
                    logger.error(f"Discord user profile fetch failed ({resp.status})")
                    return render_result_html(False, "Ошибка профиля", "Не удалось загрузить данные пользователя Discord.")
                discord_user = await resp.json()
    except Exception as e:
        logger.error(f"Discord OAuth request exception: {e}")
        return render_result_html(False, "Ошибка сети", f"Сетевая ошибка при связи с Discord: {str(e)}")

    discord_id = str(discord_user["id"])
    username = discord_user.get("username", "")
    global_name = discord_user.get("global_name") or username
    avatar_hash = discord_user.get("avatar")

    if avatar_hash:
        ext = "gif" if avatar_hash.startswith("a_") else "png"
        avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.{ext}?size=128"
    else:
        try:
            def_idx = (int(discord_id) >> 22) % 6
        except Exception:
            def_idx = 0
        avatar_url = f"https://cdn.discordapp.com/embed/avatars/{def_idx}.png"

    # 4. Save to UserExternalAccount
    stmt = select(UserExternalAccount).where(
        UserExternalAccount.user_id == user_id,
        UserExternalAccount.provider == "discord"
    )
    acc = await db.scalar(stmt)
    if not acc:
        acc = UserExternalAccount(
            user_id=user_id,
            provider="discord",
            external_id=discord_id,
            username=username,
            display_name=global_name,
            avatar_url=avatar_url,
            auth_token=access_token,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        db.add(acc)
    else:
        acc.external_id = discord_id
        acc.username = username
        acc.display_name = global_name
        acc.avatar_url = avatar_url
        acc.auth_token = access_token
        acc.updated_at = utcnow()

    await db.commit()
    logger.info(f"User {user_id} linked Discord account {username} ({discord_id}) via OAuth2")

    return render_result_html(
        is_success=True,
        title="Discord успешно подключен!",
        message=f"Аккаунт <b>@{username}</b> ({global_name}) успешно привязан. Бот теперь видит ваш голосовой канал.",
        user_data={
            "discord_id": discord_id,
            "username": username,
            "display_name": global_name,
            "avatar_url": avatar_url,
        }
    )

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
        "display_name": acc.display_name,
        "avatar_url": acc.avatar_url,
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
