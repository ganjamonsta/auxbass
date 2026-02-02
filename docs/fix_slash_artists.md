# Fix Artist Names with Forward Slashes

## Problem

After the recent update that added tracks where artists appear as participants in the title (not just main artist), some artist pages broke. The issue was caused by artist names containing forward slashes (`/`) in the database, such as:
- `Ecco2k/Bladee`
- `Bladee/Ecco2k`

When these artist names are used in API URLs like `/api/artists/Ecco2k/Bladee`, FastAPI's router interprets the `/` as a path separator, causing 404 errors.

## Error Logs

```
фев 02 04:57:47 ganjaland uvicorn[1742137]: INFO:     127.0.0.1:59728 - "GET /api/artists/Ecco2k/Bladee?scope=global HTTP/1.0" 404 Not Found
фев 02 04:57:48 ganjaland uvicorn[1742137]: INFO:     127.0.0.1:59732 - "GET /api/artists/Bladee/Ecco2k?scope=global HTTP/1.0" 404 Not Found
```

## Solution

### 1. Fix Existing Data (Clean Database)

Run the script to find and fix all tracks/albums with `/` in artist names:

```bash
cd /opt/tg_player
python3 scripts/fix_slash_artists.py
```

This script will:
- Find all tracks with `/` in artist field
- Find all albums with `/` in artist field  
- Show what will be changed (takes first artist before slash)
- Ask for confirmation before updating
- Update the database

Example fix:
- `Ecco2k/Bladee` → `Ecco2k`
- `Bladee/Ecco2k` → `Bladee`

### 2. Prevent Future Issues (Code Changes)

Added sanitization in `bot/services/tracks/service.py`:

**New function:**
```python
def sanitize_artist(artist: Optional[str]) -> Optional[str]:
    """Sanitize artist name to prevent URL routing issues.
    
    Removes forward slashes that would break REST API paths like /api/artists/{name}
    """
    if not artist:
        return artist
    
    # Replace forward slashes with proper separator
    # "Ecco2k/Bladee" -> "Ecco2k & Bladee"
    artist = artist.replace('/', ' & ')
    
    # Clean up multiple spaces
    artist = ' '.join(artist.split())
    
    return artist.strip()
```

**Applied to:**
- New track creation
- Track updates

This ensures that any new tracks uploaded with `/` in artist names will automatically have them replaced with ` & `.

## Files Changed

1. **Created:**
   - `scripts/fix_slash_artists.py` - Script to clean existing data
   - `docs/fix_slash_artists.md` - This documentation

2. **Modified:**
   - `bot/services/tracks/service.py` - Added artist name sanitization

## Running the Fix

```bash
# SSH to server
ssh ganja@ganjaland

# Navigate to project
cd /opt/tg_player

# Run the fix script
python3 scripts/fix_slash_artists.py

# Review what will be changed
# Type 'yes' to confirm

# Restart API if needed
sudo systemctl restart tg-player-api
```

## Verification

After running the fix:

1. Check artist pages work:
   ```bash
   curl "http://localhost:8000/api/artists/Ecco2k?scope=global"
   ```

2. Search for any remaining slashes in database:
   ```sql
   SELECT id, artist FROM tracks WHERE artist LIKE '%/%';
   SELECT id, artist FROM albums WHERE artist LIKE '%/%';
   ```

Should return 0 results.

## Prevention

The sanitization function now prevents forward slashes in artist names from:
- User uploads
- Track edits
- Any future track creation

Artist names with collaborations should use standard separators:
- `&` - Artist A & Artist B
- `,` - Artist A, Artist B
- `feat.` - Artist A feat. Artist B

These are properly handled by the normalization logic in `shared/matching.py`.
