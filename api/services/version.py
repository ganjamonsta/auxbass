"""
TG Player - Version & Build Tracking Service
Отслеживает версию, хэш бандла фронтенда, git commit и время старта сервера,
чтобы клиент мог достоверно определить факт обновления приложения на сервере.
"""
import os
import json
import time
import hashlib
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

# Время старта процесса бэкенда (Unix timestamp в секундах)
SERVER_START_TIME = int(time.time())

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
WEBAPP_DIST = ROOT_DIR / "webapp" / "dist"

_git_commit_cache: Optional[str] = None
_version_cache: Optional[Dict[str, Any]] = None
_last_check: float = 0.0
_CACHE_TTL = 3.0  # Кэшируем вычисление на 3 секунды для высокой производительности


def get_git_commit() -> str:
    """Получить хэш текущего коммита Git"""
    global _git_commit_cache
    if _git_commit_cache:
        return _git_commit_cache

    env_commit = os.environ.get("GIT_COMMIT") or os.environ.get("COMMIT_SHA")
    if env_commit:
        _git_commit_cache = env_commit[:8]
        return _git_commit_cache

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT_DIR,
            stderr=subprocess.DEVNULL,
            timeout=2.0
        ).decode().strip()
        if commit:
            _git_commit_cache = commit
            return commit
    except Exception:
        pass

    _git_commit_cache = "unknown"
    return _git_commit_cache


def get_dist_index_hash() -> str:
    """Вычислить SHA256 хэш файла webapp/dist/index.html (первые 12 символов)"""
    index_file = WEBAPP_DIST / "index.html"
    if not index_file.exists():
        return "none"
    try:
        content = index_file.read_bytes()
        return hashlib.sha256(content).hexdigest()[:12]
    except Exception:
        return "none"


def get_version_info() -> Dict[str, Any]:
    """
    Возвращает актуальную информацию о версии приложения и бандле:
    - version: строковая версия (e.g. '2.0.0')
    - build_id: уникальный идентификатор сборки
    - git_commit: короткий хэш коммита
    - dist_hash: хэш index.html
    - server_start_time: timestamp старта процесса сервера
    """
    global _version_cache, _last_check
    now = time.time()
    if _version_cache and (now - _last_check) < _CACHE_TTL:
        return _version_cache

    git_commit = get_git_commit()
    dist_hash = get_dist_index_hash()
    version = "2.0.0"
    build_id = None
    build_time = None

    # Попытка прочитать version.json из собранного webapp/dist
    version_file = WEBAPP_DIST / "version.json"
    if version_file.exists():
        try:
            data = json.loads(version_file.read_text(encoding="utf-8"))
            version = data.get("version", version)
            build_id = data.get("buildId")
            build_time = data.get("buildTime")
            if not git_commit or git_commit == "unknown":
                git_commit = data.get("gitCommit", git_commit)
        except Exception:
            pass

    # Если build_id не задан явно в version.json, формируем надежный составной хэш
    if not build_id:
        build_id = f"{git_commit}:{dist_hash}"

    _version_cache = {
        "version": version,
        "build_id": build_id,
        "git_commit": git_commit,
        "dist_hash": dist_hash,
        "build_time": build_time,
        "server_start_time": SERVER_START_TIME,
    }
    _last_check = now
    return _version_cache
