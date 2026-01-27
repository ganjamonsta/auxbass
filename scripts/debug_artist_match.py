#!/usr/bin/env python3
"""Debug artist matching"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.services.metadata import metadata_service

# Test artist matching
source = "Глюк'oZa"
deezer = "Глюк'oza"

print(f"Source: {source}")
print(f"Deezer: {deezer}")
print()

# Normalize
norm_source = metadata_service._normalize_artist(source)
norm_deezer = metadata_service._normalize_artist(deezer)

print(f"Normalized source: '{norm_source}'")
print(f"Normalized deezer: '{norm_deezer}'")
print()

# Match
matches = metadata_service._artist_matches(source, deezer)
print(f"_artist_matches: {matches}")
