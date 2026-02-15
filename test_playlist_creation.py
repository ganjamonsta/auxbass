#!/usr/bin/env python3
"""
Quick test for playlist creation flow.
Run with: python test_playlist_creation.py
"""
import asyncio
import httpx
from shared.config import get_settings

settings = get_settings()
API_URL = "http://localhost:8000/api"

# Test user telegram ID (you need valid auth token)
TEST_AUTH_TOKEN = "test-token"  # Replace with actual JWT token from login

async def test_playlist_creation():
    """Test creating and fetching a playlist"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {TEST_AUTH_TOKEN}"}
        
        print("📝 Creating playlist...")
        create_response = await client.post(
            f"{API_URL}/playlists",
            json={
                "name": "Test Playlist",
                "description": "Created from test script",
                "is_public": True
            },
            headers=headers
        )
        
        if create_response.status_code != 200:
            print(f"❌ Failed to create playlist: {create_response.status_code}")
            print(create_response.json())
            return
        
        playlist = create_response.json()
        print(f"✅ Playlist created: {playlist['id']}")
        print(f"   Name: {playlist['name']}")
        print(f"   Owner: {playlist.get('owner_name', 'N/A')}")
        
        # Now fetch playlists to see if new one appears
        print("\n📚 Fetching all playlists...")
        fetch_response = await client.get(
            f"{API_URL}/playlists",
            headers=headers
        )
        
        if fetch_response.status_code != 200:
            print(f"❌ Failed to fetch playlists: {fetch_response.status_code}")
            return
        
        playlists_data = fetch_response.json()
        playlists = playlists_data.get('items', [])
        
        # Check if our new playlist is in the list
        found = next((p for p in playlists if p['id'] == playlist['id']), None)
        
        if found:
            print(f"✅ Playlist found in list!")
            print(f"   ID: {found['id']}")
            print(f"   Name: {found['name']}")
            print(f"   Is Public: {found['is_public']}")
        else:
            print(f"❌ Playlist NOT found in list!")
            print(f"   Created ID: {playlist['id']}")
            print(f"   Available playlists: {[p['id'] for p in playlists]}")

if __name__ == "__main__":
    print("🧪 Playlist Creation Test\n")
    print("⚠️  Note: You need to replace TEST_AUTH_TOKEN with a valid JWT token from login.\n")
    print("Steps to get token:")
    print("1. Login through webapp or bot")
    print("2. Check browser DevTools (Network tab) for auth token in request headers")
    print("3. Or check localStorage for auth token\n")
    
    try:
        asyncio.run(test_playlist_creation())
    except KeyboardInterrupt:
        print("\n❌ Test interrupted")
