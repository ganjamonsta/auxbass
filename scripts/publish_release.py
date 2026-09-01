"""
TG Player - WebApp Release Publisher
Скрипт для сборки и загрузки WebApp релиза напрямую в GitHub Releases:
https://github.com/ganjamonsta/auxbass/releases
"""
import os
import re
import sys
import subprocess
import tarfile
from pathlib import Path
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "webapp" / "dist"
ARCHIVE_PATH = ROOT_DIR / "webapp-dist.tar.gz"
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(ENV_PATH)


def get_git_repo() -> tuple[str, str]:
    """Получить owner и repo из git remote origin"""
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=ROOT_DIR
        ).decode().strip()
        match = re.search(r"github\.com[:/]([^/]+)/([^/\.]+)", url)
        if match:
            return match.group(1), match.group(2)
    except Exception:
        pass
    return "ganjamonsta", "auxbass"


def ensure_archive() -> bool:
    """Проверяет наличие архива webapp-dist.tar.gz или создает его из webapp/dist"""
    if not (DIST_DIR / "index.html").exists():
        print("❌ Ошибка: webapp/dist/index.html не найден. Сначала соберите фронтенд (npm run build).")
        return False

    print("📦 Упаковка webapp/dist в webapp-dist.tar.gz...")
    with tarfile.open(ARCHIVE_PATH, "w:gz") as tar:
        tar.add(DIST_DIR, arcname="webapp/dist")
    
    size_kb = ARCHIVE_PATH.stat().st_size / 1024
    print(f"✅ Архив создан: webapp-dist.tar.gz ({size_kb:.1f} KB)")
    return True


def upload_to_github_releases(token: str, owner: str, repo: str) -> bool:
    """Загружает webapp-dist.tar.gz в GitHub Releases 'latest' через REST API"""
    print(f"\n🚀 Загрузка в GitHub Releases (https://github.com/{owner}/{repo}/releases)...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    
    with httpx.Client(headers=headers, timeout=60.0) as client:
        # 1. Проверяем или создаем release latest
        rel_resp = client.get(f"https://api.github.com/repos/{owner}/{repo}/releases/tags/latest")
        if rel_resp.status_code == 200:
            release = rel_resp.json()
        elif rel_resp.status_code == 404:
            print("📝 Создание релиза 'latest'...")
            create_resp = client.post(
                f"https://api.github.com/repos/{owner}/{repo}/releases",
                json={
                    "tag_name": "latest",
                    "name": "Latest WebApp Build",
                    "body": "Production build of TG Player WebApp.",
                    "draft": False,
                    "prerelease": False,
                }
            )
            if create_resp.status_code not in (200, 201):
                print(f"❌ Ошибка создания релиза: {create_resp.status_code} {create_resp.text}")
                return False
            release = create_resp.json()
        else:
            print(f"❌ Ошибка проверки релиза: {rel_resp.status_code} {rel_resp.text}")
            return False

        release_id = release["id"]

        # 2. Удаляем старый ассет webapp-dist.tar.gz, если есть
        for asset in release.get("assets", []):
            if asset["name"] == "webapp-dist.tar.gz":
                print(f"🗑️ Удаление старого ассета webapp-dist.tar.gz (id={asset['id']})...")
                client.delete(f"https://api.github.com/repos/{owner}/{repo}/releases/assets/{asset['id']}")

        # 3. Загружаем новый ассет
        upload_url = f"https://uploads.github.com/repos/{owner}/{repo}/releases/{release_id}/assets?name=webapp-dist.tar.gz"
        print("⬆️ Загрузка файла webapp-dist.tar.gz на GitHub...")
        
        with open(ARCHIVE_PATH, "rb") as f:
            file_data = f.read()

        upload_headers = {
            **headers,
            "Content-Type": "application/gzip",
            "Content-Length": str(len(file_data)),
        }
        
        up_resp = client.post(upload_url, headers=upload_headers, content=file_data)
        if up_resp.status_code in (200, 201):
            print("✅ webapp-dist.tar.gz успешно загружен в GitHub Releases!")
            return True
        else:
            print(f"❌ Ошибка загрузки ассета: {up_resp.status_code} {up_resp.text}")
            return False


def save_token_to_env(token: str):
    """Сохраняет GITHUB_TOKEN в .env файл"""
    try:
        content = ""
        if ENV_PATH.exists():
            content = ENV_PATH.read_text(encoding="utf-8")
        
        if "GITHUB_TOKEN=" in content:
            content = re.sub(r"GITHUB_TOKEN=.*", f"GITHUB_TOKEN={token}", content)
        else:
            content += f"\n# GitHub Releases Token\nGITHUB_TOKEN={token}\n"
        
        ENV_PATH.write_text(content, encoding="utf-8")
        print("💾 GITHUB_TOKEN сохранен в .env (больше вводить не потребуется)!")
    except Exception as e:
        print(f"⚠️ Не удалось сохранить токен в .env: {e}")


def main():
    print("========================================================")
    print("       🎵 TG Player - WebApp Release Publisher          ")
    print("========================================================")

    if not ensure_archive():
        sys.exit(1)

    owner, repo = get_git_repo()
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or os.getenv("GIT_TOKEN")

    if not token:
        print(f"\n🔑 Для загрузки в https://github.com/{owner}/{repo}/releases")
        print("   нужен GitHub Personal Access Token (с правами 'repo').")
        print("   Создать можно тут (15 сек): https://github.com/settings/tokens/new")
        print("   (срок: 'No expiration', галочка: 'repo')\n")
        try:
            user_token = input("👉 Вставьте ваш токен (ghp_...): ").strip()
            if user_token:
                token = user_token
                save_token_to_env(token)
            else:
                print("❌ Токен не введен. Отмена.")
                sys.exit(1)
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Отменено.")
            sys.exit(1)

    try:
        ok = upload_to_github_releases(token, owner, repo)
        if ok:
            print("\n========================================================")
            print(f"  🎉 УСПЕШНО ЗАЛИТО В РЕЛИЗЫ:")
            print(f"  🔗 https://github.com/{owner}/{repo}/releases/tag/latest")
            print("========================================================")
            sys.exit(0)
        else:
            print("\n❌ Не удалось загрузить в Releases.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
