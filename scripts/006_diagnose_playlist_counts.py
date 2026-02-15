import asyncio
import json
from sqlalchemy import select
from shared.database import get_db_context
from shared.models import Playlist, User, PlaylistTrack
from api.routers.playlists import get_my_playlists, get_playlist_info
from api.schemas.common import TelegramUser

async def diagnose_playlist_counts():
    async with get_db_context() as db:
        # Get a user who has playlists
        user_id_result = await db.execute(select(Playlist.owner_id).limit(1))
        user_id = user_id_result.scalar()
        
        if not user_id:
            print("No playlists found in database.")
            return
            
        user = await db.get(User, user_id)
        print(f"Diagnosing for user: {user.display_name} (ID: {user.id})")
        
        # Call get_my_playlists via router logic (mocking Depends)
        # We'll simulate the user from auth
        mock_user = TelegramUser(
            id=user.id,
            first_name=user.first_name or "",
            username=user.username
        )
        
        # Test 1: get_my_playlists
        print("\n--- Test 1: get_my_playlists ---")
        response = await get_my_playlists(user=mock_user, db=db)
        for item in response.items:
            print(f"Playlist: {item.name}, ID: {item.id}, track_count (tc): {item.track_count}")
            
            # Test 2: get_playlist_info directly
            info_count, duration, _, _ = await get_playlist_info(db, item.id)
            print(f"  -> get_playlist_info count: {info_count}")

if __name__ == "__main__":
    asyncio.run(diagnose_playlist_counts())
