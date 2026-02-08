# TG Player — Copilot Instructions

## Architecture

Three-service monorepo for a Telegram music player: **bot** (aiogram 3), **api** (FastAPI), and **webapp** (Vue 3 + Vite). All Python services share code via the `shared/` package.

```
bot/        → Telegram bot (aiogram 3 Dispatcher + Routers)
api/        → REST API (FastAPI, mounted at /api)
webapp/     → Telegram Mini App (Vue 3, Pinia, Tailwind, Vite)
shared/     → Config, DB engine, SQLAlchemy models, matching utils
database/   → init.sql schema + numbered migration .sql files
```

**Data flow:** Users send audio files to the **bot** → bot saves `Track` (keyed by `file_unique_id`) and `UserLibrary` entry → background `enrichment_worker` enriches metadata from Deezer/Last.fm → **api** serves tracks/albums/playlists to the **webapp** which streams audio via Telegram Bot API proxy (`/api/player/audio/`).

## Key Conventions

### Python (bot + api + shared)
- **Async everywhere**: SQLAlchemy async sessions (`asyncpg` for Postgres, `aiosqlite` for local dev). Use `async with get_session() as session:` for DB access.
- **Models in `shared/models.py`**: SQLAlchemy 2.0 declarative style with `Mapped[]` / `mapped_column()`. Enums use the `enum_column()` helper to store lowercase `.value` strings.
- **Track ownership model**: `Track` is global (one per `file_unique_id`). `UserLibrary` is the join table connecting users to tracks. Never query tracks without joining `UserLibrary` when showing a user's library.
- **Services pattern** (bot): Singleton service instances in `bot/services/` — `track_service`, `album_service`, `channel_service`, `deduplication_service`, `enrichment_worker`. Import from `bot.services` package.
- **API auth**: JWT-based. Use `get_current_user` dependency for required auth, `get_optional_user` for optional. Auth schema is `TelegramUser` from `api/schemas/common.py`.
- **API routers** map to `api/routers/*.py` with matching Pydantic schemas in `api/schemas/*.py`.
- **Cross-layer dependency**: The API imports `bot.services.channels` for channel forwarding — this is intentional (see `api/routers/tracks.py` note).
- **Text matching**: Use functions from `shared/matching.py` (`normalize_artist`, `fuzzy_match_title`, etc.) — never hand-roll normalization. `shared/utils.py` re-exports these for backward compatibility.
- **Settings**: `shared/config.py` with `pydantic-settings`. Access via `get_settings()` (cached). All config from env vars / `.env` file.

### Webapp (Vue 3)
- **State management**: Pinia stores in `webapp/src/stores/` — `player.js` (large, ~2600 lines), `library.js`, `auth.js`, `ui.js`.
- **Composables**: Reusable logic in `webapp/src/composables/` (e.g., `useContextMenu`, `useVirtualScroll`, `usePullToRefresh`).
- **API client**: `webapp/src/api/client.js` — axios instance with auth interceptor. API URL defaults to `/api` in production.
- **Styling**: Scoped `<style scoped>` per component. CSS variables for theming (`--accent`, `--text-primary`, `--bg-elevated`, etc.) defined in `webapp/src/styles/design-system.css`. Tailwind is available but components primarily use custom CSS.
- **Cover images**: Use `getCoverUrl(url, CoverSize)` from `@/utils` — never construct cover URLs directly.
- **Icons**: `lucide-vue-next` — import individual icons, don't import the whole library.
- **Router**: Lazy-loaded views. All authenticated routes use `meta: { requiresAuth: true }`.
- **UI language**: Russian for user-facing text in bot messages and webapp UI labels.

## Development

```bash
# Local dev: DB in Docker, services run natively
docker compose -f docker-compose.dev.yml up -d          # PostgreSQL on :5432
python -m uvicorn api.main:app --reload --port 8000     # API on :8000
python bot/main.py                                       # Bot
cd webapp && npm run dev                                  # Webapp on :5173

# Or use run_dev.bat (Windows interactive launcher)
```

- Requires `.env.local` (copied to `.env` at runtime) with `BOT_TOKEN`, `DATABASE_URL`, etc.
- `DATABASE_URL=postgresql://postgres:postgres@localhost/tg_player_dev` for local Postgres.
- Tests: `pytest` — uses `pytest-asyncio`, fixtures in `tests/conftest.py`. Mocks for Telegram objects.

## Database

- **PostgreSQL 16** in production, SQLite for quick local testing.
- Schema defined both in `database/init.sql` (DDL) and `shared/models.py` (ORM). Keep both in sync.
- Migrations: numbered SQL files in `database/migrations/` (e.g., `003_add_normalized_artist.sql`). Applied manually.
- Production deploys via `docker-compose.prod.yml` + `deploy/` scripts.

## Audio Streaming

The API proxies audio from Telegram Bot API to avoid exposing the bot token. The player router (`api/routers/player.py`) uses a global `aiohttp.ClientSession` pool for efficient streaming. HD formats (FLAC, WAV, ALAC) are detected by mime type and flagged `is_streamable=false` — the webapp handles this by offering MP3 alternatives via `streamable_id`.

## Enrichment Pipeline

Background worker (`bot/services/enrichment/`) processes tracks with status `pending`:
1. Last.fm API → album name, tags, genre
2. Deezer API → covers, track numbers, album IDs
3. On completion → auto-assigns to `Album` entity, updates channel messages

Status flow: `pending` → `processing` → `completed`/`failed`. Check `enrichment_status` on `TrackEnrichment` model.
