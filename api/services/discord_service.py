"""
TG Player - Discord Voice & Party Service
Zero-disk streaming via FFmpeg -> Discord Voice (Opus/PCM in memory)
Live voice state tracking, DJ roles, and collaborative queue.
"""
from typing import Optional, Dict, Any, List, Set
import asyncio
import logging
import time
import re

import discord
from discord import VoiceClient, PCMVolumeTransformer, FFmpegPCMAudio

from shared.config import get_settings
from shared.models import Track
from api.routers.player import generate_stream_token, get_telegram_file_path

logger = logging.getLogger("tg_player.discord")
settings = get_settings()


class DiscordService:
    """
    Singleton service managing the Discord bot, voice streaming,
    live voice room states, DJ permissions, and WebSocket subscriptions.
    """

    def __init__(self):
        self.bot: Optional[discord.Client] = None
        self.bot_task: Optional[asyncio.Task] = None
        self._is_ready = False
        
        # Voice connection state
        self.voice_client: Optional[VoiceClient] = None
        self.active_guild_id: Optional[int] = None
        self.active_channel_id: Optional[int] = None
        
        # Playback state
        self.current_track: Optional[Dict[str, Any]] = None
        self.current_source: Optional[PCMVolumeTransformer] = None
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.volume: int = 100  # 0 to 100%
        self.started_at: float = 0
        self.position_offset: float = 0
        
        # Collaborative Queue
        self.queue: List[Dict[str, Any]] = []
        self.queue_index: int = -1
        
        # DJ & Roles
        self.host_user: Optional[Dict[str, Any]] = None  # { id, username, display_name, discord_id }
        self.dj_lock: bool = False  # If True, only host can skip/pause/seek
        
        # Inactivity auto-leave timer
        self._inactivity_task: Optional[asyncio.Task] = None
        
        # WebSocket broadcast subscribers
        self._ws_subscribers: Set[Any] = set()
        
        # Lock for safe async playback operations
        self._play_lock = asyncio.Lock()

    @property
    def is_configured(self) -> bool:
        return bool(settings.discord_bot_token and settings.discord_bot_token.strip())

    @property
    def is_connected(self) -> bool:
        return bool(self.voice_client and self.voice_client.is_connected())

    async def start(self):
        """Start the Discord bot client as a background asyncio task"""
        if not self.is_configured:
            logger.info("ℹ️ Discord bot token not configured. Discord streaming disabled.")
            return

        intents = discord.Intents.default()
        intents.voice_states = True
        intents.guilds = True

        self.bot = discord.Client(intents=intents)

        @self.bot.event
        async def on_ready():
            self._is_ready = True
            logger.info(f"🤖 Discord Bot connected as {self.bot.user} (ID: {self.bot.user.id})")
            logger.info(f"   Available in {len(self.bot.guilds)} guilds")
            await self._update_presence()
            await self._broadcast_party_update()

        @self.bot.event
        async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
            """Listen to voice channel movements to update party member list in real-time"""
            # If the change occurred in our active channel
            if self.active_channel_id:
                if (before.channel and before.channel.id == self.active_channel_id) or \
                   (after.channel and after.channel.id == self.active_channel_id):
                    logger.debug(f"[Discord Voice] Member {member.display_name} voice state changed in party channel")
                    await self._broadcast_party_update()
                    self._check_empty_channel()

        # Start bot in background
        self.bot_task = asyncio.create_task(self._run_bot_loop())

    async def _run_bot_loop(self):
        """Bot connection loop with automatic reconnection"""
        while True:
            try:
                logger.info("🤖 Starting Discord bot gateway connection...")
                await self.bot.start(settings.discord_bot_token.strip())
            except asyncio.CancelledError:
                logger.info("🤖 Discord bot task cancelled.")
                break
            except Exception as e:
                logger.error(f"⚠️ Discord bot error: {e}. Reconnecting in 10s...")
                self._is_ready = False
                await asyncio.sleep(10)

    async def close(self):
        """Disconnect and stop bot on server shutdown"""
        logger.info("Stopping Discord Service...")
        try:
            await self.disconnect()
        except Exception:
            pass

        if self.bot and not self.bot.is_closed():
            try:
                await self.bot.close()
            except Exception:
                pass

        if self.bot_task and not self.bot_task.done():
            self.bot_task.cancel()

    # =========================================================================
    # Voice Channel Discovery & User Matching
    # =========================================================================

    def find_user_voice_channel(self, user_discord_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Check if user is currently sitting in any voice channel on servers where bot is present.
        Returns channel info dict if found, else None.
        """
        if not self.bot or not self._is_ready or not user_discord_id:
            return None

        try:
            num_id = int(user_discord_id)
        except ValueError:
            return None

        for guild in self.bot.guilds:
            voice_state = guild.voice_states.get(num_id)
            if voice_state and voice_state.channel:
                channel = voice_state.channel
                return {
                    "guild_id": str(guild.id),
                    "guild_name": guild.name,
                    "channel_id": str(channel.id),
                    "channel_name": channel.name,
                    "user_count": len([m for m in channel.members if not m.bot]),
                }
        return None

    def get_channel_members(self, channel_id: int) -> List[Dict[str, Any]]:
        """Return list of members in a voice channel with their voice states"""
        if not self.bot or not self._is_ready:
            return []

        for guild in self.bot.guilds:
            channel = guild.get_channel(channel_id)
            if channel and isinstance(channel, discord.VoiceChannel):
                members = []
                for m in channel.members:
                    is_our_bot = m.id == self.bot.user.id
                    avatar_url = str(m.display_avatar.url) if m.display_avatar else None
                    members.append({
                        "id": str(m.id),
                        "username": m.name,
                        "display_name": m.display_name,
                        "avatar_url": avatar_url,
                        "is_bot": m.bot,
                        "is_our_bot": is_our_bot,
                        "is_muted": m.voice.self_mute or m.voice.mute if m.voice else False,
                        "is_deaf": m.voice.self_deaf or m.voice.deaf if m.voice else False,
                    })
                return members
        return []

    def get_available_channels(self) -> List[Dict[str, Any]]:
        """Return all voice channels in guilds where bot has connect permissions"""
        if not self.bot or not self._is_ready:
            return []

        result = []
        for guild in self.bot.guilds:
            channels = []
            for ch in guild.voice_channels:
                perms = ch.permissions_for(guild.me)
                if perms.connect and perms.speak:
                    channels.append({
                        "id": str(ch.id),
                        "name": ch.name,
                        "user_count": len([m for m in ch.members if not m.bot]),
                    })
            if channels:
                icon_url = str(guild.icon.url) if guild.icon else None
                result.append({
                    "guild_id": str(guild.id),
                    "guild_name": guild.name,
                    "guild_icon": icon_url,
                    "channels": channels,
                })
        return result

    def get_invite_url(self) -> str:
        """Generate bot invite URL with Voice permissions"""
        if not settings.discord_client_id:
            client_id = str(self.bot.user.id) if self.bot and self.bot.user else ""
        else:
            client_id = settings.discord_client_id.strip()

        if not client_id:
            return ""

        # Permissions: Connect (1048576) + Speak (2097152) + Use Voice Activity (33554432) = 36700160
        # Plus Send Messages (2048), Embed Links (16384) = 36718592
        return f"https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions=36718592"

    # =========================================================================
    # Voice Connection & Channel Joining
    # =========================================================================

    async def connect_to_channel(self, channel_id: int, user: Dict[str, Any]) -> Dict[str, Any]:
        """Join a Discord voice channel"""
        if not self.bot or not self._is_ready:
            raise RuntimeError("Discord бот еще не подключен к сети")

        channel = self.bot.get_channel(channel_id)
        if not channel or not isinstance(channel, discord.VoiceChannel):
            raise ValueError(f"Голосовой канал ID {channel_id} не найден")

        perms = channel.permissions_for(channel.guild.me)
        if not perms.connect:
            raise PermissionError(f"У бота нет прав 'Connect' в канале '{channel.name}'")
        if not perms.speak:
            raise PermissionError(f"У бота нет прав 'Speak' в канале '{channel.name}'")

        # Set Host if no party is currently active
        if not self.is_connected or not self.host_user:
            self.host_user = user

        # Connect or move
        if self.voice_client and self.voice_client.is_connected():
            if self.voice_client.channel.id != channel_id:
                logger.info(f"Moving Discord bot to voice channel: {channel.name} ({channel.guild.name})")
                await self.voice_client.move_to(channel)
        else:
            logger.info(f"Connecting Discord bot to voice channel: {channel.name} ({channel.guild.name})")
            self.voice_client = await channel.connect(self_deaf=True)

        self.active_guild_id = channel.guild.id
        self.active_channel_id = channel.id

        await self._broadcast_party_update()
        return self.get_party_state(user)

    async def disconnect(self):
        """Stop playback and disconnect from voice channel"""
        async with self._play_lock:
            if self.voice_client:
                try:
                    if self.voice_client.is_playing() or self.voice_client.is_paused():
                        self.voice_client.stop()
                    await self.voice_client.disconnect(force=True)
                except Exception as e:
                    logger.warning(f"Error during voice client disconnect: {e}")
                finally:
                    self.voice_client = None

            self.active_guild_id = None
            self.active_channel_id = None
            self.current_track = None
            self.current_source = None
            self.is_playing = False
            self.is_paused = False
            self.queue = []
            self.queue_index = -1
            self.host_user = None
            self.dj_lock = False

            await self._update_presence()
            await self._broadcast_party_update()

    # =========================================================================
    # Playback & Audio Pipeline (Zero-Disk Stream)
    # =========================================================================

    async def play_track(
        self,
        track_dict: Dict[str, Any],
        user: Dict[str, Any],
        new_queue: Optional[List[Dict[str, Any]]] = None,
        position: float = 0,
    ) -> Dict[str, Any]:
        """
        Stream track into active Discord voice channel.
        Zero-disk streaming: generates streaming token and feeds internal proxy to FFmpegPCMAudio.
        """
        async with self._play_lock:
            if not self.is_connected:
                raise RuntimeError("Бот не подключен ни к одному голосовому каналу")

            # Check DJ Lock permissions
            if self.dj_lock and not self._can_user_control(user):
                raise PermissionError("Включен режим 'Только DJ'. Только хост может переключать треки.")

            # Update queue
            if new_queue is not None:
                self.queue = [
                    {**t, "added_by": t.get("added_by") or user}
                    for t in new_queue
                ]
                self.queue_index = next((i for i, t in enumerate(self.queue) if t.get("id") == track_dict.get("id")), 0)
            elif track_dict not in self.queue:
                self.queue.append({**track_dict, "added_by": user})
                self.queue_index = len(self.queue) - 1

            # Prepare streaming token
            track_id = track_dict.get("id")
            file_id = track_dict.get("file_id")
            if not file_id:
                raise ValueError("Трек не содержит file_id для воспроизведения")

            file_path = await get_telegram_file_path(file_id)
            if not file_path:
                raise ValueError("Файл трека временно недоступен в Telegram")

            # Generate stream proxy token
            user_id = user.get("id", 0)
            token = generate_stream_token(track_id, user_id, file_path)

            # Local internal streaming URL (loopback via FastAPI)
            stream_url = f"http://127.0.0.1:{settings.api_port}/api/player/audio/{token}"

            # Stop existing playback if active
            if self.voice_client.is_playing() or self.voice_client.is_paused():
                self.voice_client.stop()

            # Build FFmpeg audio source
            ffmpeg_before_opts = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
            ffmpeg_opts = "-vn"
            if position > 0:
                ffmpeg_opts = f"-vn -ss {int(position)}"

            source = FFmpegPCMAudio(
                stream_url,
                before_options=ffmpeg_before_opts,
                options=ffmpeg_opts
            )

            # Volume transformer
            volume_float = max(0.0, min(1.0, self.volume / 100.0))
            transformer = PCMVolumeTransformer(source, volume=volume_float)
            self.current_source = transformer

            # Callback when track finishes
            def on_finished(error):
                if error:
                    logger.error(f"[Discord Playback] Error during playback: {error}")
                asyncio.run_coroutine_threadsafe(self._on_track_ended(), self.bot.loop)

            self.voice_client.play(transformer, after=on_finished)

            # Update playback state
            self.current_track = {**track_dict, "added_by": track_dict.get("added_by") or user}
            self.is_playing = True
            self.is_paused = False
            self.started_at = time.time()
            self.position_offset = position

            logger.info(
                f"▶️ [Discord] Playing '{track_dict.get('title')}' by '{track_dict.get('artist')}' "
                f"in channel ID {self.active_channel_id} (Host: {self.host_user.get('display_name') if self.host_user else 'Unknown'})"
            )

            await self._update_presence()
            await self._broadcast_party_update()
            return self.get_party_state(user)

    async def _on_track_ended(self):
        """Auto-advance to next track in queue when current track finishes"""
        async with self._play_lock:
            if not self.is_connected:
                return

            if self.queue and self.queue_index + 1 < len(self.queue):
                self.queue_index += 1
                next_track = self.queue[self.queue_index]
                logger.info(f"⏭️ [Discord] Auto-advancing to next track in queue: {next_track.get('title')}")
                try:
                    await self._play_track_internal(next_track)
                except Exception as e:
                    logger.error(f"Failed to play next track in queue: {e}")
                    self.is_playing = False
                    await self._broadcast_party_update()
            else:
                logger.info("⏹️ [Discord] Queue finished.")
                self.is_playing = False
                self.is_paused = False
                self.current_track = None
                await self._update_presence()
                await self._broadcast_party_update()

    async def _play_track_internal(self, track_dict: Dict[str, Any]):
        """Internal playback call without altering queue index"""
        file_id = track_dict.get("file_id")
        file_path = await get_telegram_file_path(file_id)
        if not file_path:
            logger.warning(f"File path unavailable for track {track_dict.get('id')}")
            return

        token = generate_stream_token(track_dict["id"], 0, file_path)
        stream_url = f"http://127.0.0.1:{settings.api_port}/api/player/audio/{token}"

        source = FFmpegPCMAudio(
            stream_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn"
        )
        volume_float = max(0.0, min(1.0, self.volume / 100.0))
        transformer = PCMVolumeTransformer(source, volume=volume_float)
        self.current_source = transformer

        def on_finished(error):
            if error:
                logger.error(f"[Discord Playback] Error: {error}")
            asyncio.run_coroutine_threadsafe(self._on_track_ended(), self.bot.loop)

        self.voice_client.play(transformer, after=on_finished)
        self.current_track = track_dict
        self.is_playing = True
        self.is_paused = False
        self.started_at = time.time()
        self.position_offset = 0

        await self._update_presence()
        await self._broadcast_party_update()

    async def pause(self, user: Dict[str, Any]):
        """Pause playback"""
        if not self.is_connected or not self.voice_client:
            return
        if self.dj_lock and not self._can_user_control(user):
            raise PermissionError("Включен режим 'Только DJ'. Только хост может ставить на паузу.")

        if self.voice_client.is_playing():
            self.voice_client.pause()
            self.position_offset = self.get_current_position()
            self.started_at = 0
            self.is_playing = False
            self.is_paused = True
            await self._broadcast_party_update()

    async def resume(self, user: Dict[str, Any]):
        """Resume playback"""
        if not self.is_connected or not self.voice_client:
            return
        if self.dj_lock and not self._can_user_control(user):
            raise PermissionError("Включен режим 'Только DJ'. Только хост может возобновлять трек.")

        if self.voice_client.is_paused():
            self.voice_client.resume()
            self.started_at = time.time()
            self.is_playing = True
            self.is_paused = False
            await self._broadcast_party_update()

    async def stop(self, user: Dict[str, Any]):
        """Stop playback"""
        if not self.is_connected or not self.voice_client:
            return
        if self.dj_lock and not self._can_user_control(user):
            raise PermissionError("Включен режим 'Только DJ'.")

        if self.voice_client.is_playing() or self.voice_client.is_paused():
            self.voice_client.stop()
        self.is_playing = False
        self.is_paused = False
        self.current_track = None
        await self._update_presence()
        await self._broadcast_party_update()

    async def seek(self, position: float, user: Dict[str, Any]):
        """Seek to position by restarting stream with -ss offset"""
        if not self.is_connected or not self.current_track:
            return
        if self.dj_lock and not self._can_user_control(user):
            raise PermissionError("Включен режим 'Только DJ'.")

        await self.play_track(self.current_track, user, position=position)

    async def skip(self, user: Dict[str, Any]):
        """Skip to next track in queue"""
        if not self.is_connected:
            return
        if self.dj_lock and not self._can_user_control(user):
            raise PermissionError("Включен режим 'Только DJ'.")

        if self.voice_client and (self.voice_client.is_playing() or self.voice_client.is_paused()):
            self.voice_client.stop()

    async def set_volume(self, volume: int, user: Dict[str, Any]):
        """Set Discord playback volume (0 to 100)"""
        volume = max(0, min(100, volume))
        self.volume = volume
        if self.current_source:
            self.current_source.volume = volume / 100.0
        await self._broadcast_party_update()

    # =========================================================================
    # Queue Operations (Collaborative Queue)
    # =========================================================================

    async def add_to_queue(self, track_dict: Dict[str, Any], user: Dict[str, Any]) -> int:
        """Add a track to the end of the party queue (allowed for all party members)"""
        item = {
            **track_dict,
            "added_by": user,
            "added_at": time.time(),
        }
        self.queue.append(item)

        if self.is_connected and not self.is_playing and not self.is_paused:
            self.queue_index = len(self.queue) - 1
            await self.play_track(item, user)

        await self._broadcast_party_update()
        return len(self.queue)

    async def remove_from_queue(self, index: int, user: Dict[str, Any]):
        """Remove a track from queue"""
        if 0 <= index < len(self.queue):
            item = self.queue[index]
            is_adder = item.get("added_by", {}).get("id") == user.get("id")
            if not self._can_user_control(user) and not is_adder:
                raise PermissionError("Вы можете удалять только треки, добавленные вами.")

            self.queue.pop(index)
            if self.queue_index >= index:
                self.queue_index = max(0, self.queue_index - 1)
            await self._broadcast_party_update()

    # =========================================================================
    # DJ & Host Role Management
    # =========================================================================

    def _can_user_control(self, user: Dict[str, Any]) -> bool:
        """Check if user has DJ/Host permissions"""
        if not self.host_user:
            return True
        return self.host_user.get("id") == user.get("id")

    async def set_dj_lock(self, locked: bool, user: Dict[str, Any]):
        """Toggle DJ lock mode (only host can toggle)"""
        if not self._can_user_control(user):
            raise PermissionError("Только текущий DJ может менять режим блокировки.")
        self.dj_lock = locked
        await self._broadcast_party_update()

    async def transfer_dj(self, new_host_user: Dict[str, Any], user: Dict[str, Any]):
        """Transfer DJ crown to another user"""
        if not self._can_user_control(user):
            raise PermissionError("Только текущий DJ может передать управление.")
        self.host_user = new_host_user
        await self._broadcast_party_update()

    # =========================================================================
    # State Inspection & Helpers
    # =========================================================================

    def get_current_position(self) -> float:
        """Calculate elapsed playback position in seconds"""
        if not self.is_playing or self.started_at == 0:
            return self.position_offset
        return self.position_offset + (time.time() - self.started_at)

    def get_party_state(self, current_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Comprehensive state dictionary for WebApp UI and party widgets.
        Includes channel info, member list, playback status, and user-specific flags.
        """
        has_party = self.is_connected and self.active_channel_id is not None
        
        channel_name = None
        guild_name = None
        guild_icon = None
        members: List[Dict[str, Any]] = []

        if has_party and self.bot:
            for guild in self.bot.guilds:
                if guild.id == self.active_guild_id:
                    guild_name = guild.name
                    guild_icon = str(guild.icon.url) if guild.icon else None
                    ch = guild.get_channel(self.active_channel_id)
                    if ch:
                        channel_name = ch.name
                        members = self.get_channel_members(self.active_channel_id)
                    break

        is_user_in_voice = False
        user_discord_id = current_user.get("discord_id") if current_user else None
        if user_discord_id and has_party:
            is_user_in_voice = any(m.get("id") == str(user_discord_id) for m in members)

        is_host = False
        can_control = True
        if current_user and self.host_user:
            is_host = self.host_user.get("id") == current_user.get("id")
            if self.dj_lock and not is_host:
                can_control = False

        return {
            "configured": self.is_configured,
            "bot_ready": self._is_ready,
            "has_party": has_party,
            "guild_id": str(self.active_guild_id) if self.active_guild_id else None,
            "guild_name": guild_name,
            "guild_icon": guild_icon,
            "channel_id": str(self.active_channel_id) if self.active_channel_id else None,
            "channel_name": channel_name,
            "members": members,
            "member_count": len([m for m in members if not m.get("is_bot")]),
            
            # Playback
            "is_playing": self.is_playing,
            "is_paused": self.is_paused,
            "current_track": self.current_track,
            "position": round(self.get_current_position(), 1),
            "duration": self.current_track.get("duration", 0) if self.current_track else 0,
            "volume": self.volume,
            
            # Queue
            "queue": self.queue,
            "queue_index": self.queue_index,
            
            # DJ & Roles
            "host_user": self.host_user,
            "dj_lock": self.dj_lock,
            "is_host": is_host,
            "can_control": can_control,
            "is_user_in_voice": is_user_in_voice,
        }

    # =========================================================================
    # Inactivity & Presence
    # =========================================================================

    def _check_empty_channel(self):
        """Check if voice channel is empty of human members and start auto-leave countdown"""
        if not self.is_connected or not self.active_channel_id:
            return

        members = self.get_channel_members(self.active_channel_id)
        human_members = [m for m in members if not m.get("is_bot")]

        if len(human_members) == 0:
            if not self._inactivity_task or self._inactivity_task.done():
                logger.info("[Discord] Channel is empty. Starting 3-minute auto-leave timer...")
                self._inactivity_task = asyncio.create_task(self._auto_leave_countdown())
        else:
            if self._inactivity_task and not self._inactivity_task.done():
                logger.info("[Discord] Members returned to channel. Auto-leave timer cancelled.")
                self._inactivity_task.cancel()

    async def _auto_leave_countdown(self):
        """Leave voice channel after 180 seconds of emptiness"""
        try:
            await asyncio.sleep(180)
            if self.is_connected:
                logger.info("⏱️ [Discord] Channel remained empty for 3 minutes. Disconnecting...")
                await self.disconnect()
        except asyncio.CancelledError:
            pass

    async def _update_presence(self):
        """Update Discord bot rich status"""
        if not self.bot or not self._is_ready:
            return

        try:
            if self.is_playing and self.current_track:
                title = self.current_track.get("title", "Музыка")
                artist = self.current_track.get("artist", "")
                name = f"{artist} — {title}" if artist else title
                activity = discord.Activity(type=discord.ActivityType.listening, name=name)
                await self.bot.change_presence(activity=activity, status=discord.Status.online)
            else:
                activity = discord.Activity(type=discord.ActivityType.listening, name="AuxBass Player")
                await self.bot.change_presence(activity=activity, status=discord.Status.idle)
        except Exception as e:
            logger.debug(f"Failed to update Discord presence: {e}")

    # =========================================================================
    # WebSocket Event Broadcasting
    # =========================================================================

    def register_ws(self, ws):
        self._ws_subscribers.add(ws)

    def unregister_ws(self, ws):
        self._ws_subscribers.discard(ws)

    async def _broadcast_party_update(self):
        """Broadcast party state to all connected webapp clients"""
        if not self._ws_subscribers:
            return

        state = self.get_party_state(None)
        payload = {"type": "party_update", "data": state}

        dead_sockets = set()
        for ws in self._ws_subscribers:
            try:
                await ws.send_json(payload)
            except Exception:
                dead_sockets.add(ws)

        for ws in dead_sockets:
            self._ws_subscribers.discard(ws)


# Global singleton instance
discord_service = DiscordService()
