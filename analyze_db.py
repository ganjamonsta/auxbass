#!/usr/bin/env python3
"""Analyze existing database structure and data"""
import sqlite3

conn = sqlite3.connect('tg_player.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
print('=== TABLES ===')
for t in tables:
    print(f'  {t[0]}')

print()

# Get row counts and schema for each table
for table in tables:
    table_name = table[0]
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = cursor.fetchone()[0]
    print(f'=== {table_name} ({count} rows) ===')
    
    cursor.execute(f'PRAGMA table_info({table_name})')
    columns = cursor.fetchall()
    for col in columns:
        pk_str = "PK" if col[5] else ""
        nn_str = "NOT NULL" if col[3] else ""
        print(f'  {col[1]:30} {col[2]:15} {nn_str:10} {pk_str}')
    print()

# Sample data from key tables
print('=== SAMPLE DATA ===')
print()

# Users
cursor.execute('SELECT id, username, first_name FROM users LIMIT 5')
users = cursor.fetchall()
print('Users:')
for u in users:
    print(f'  ID={u[0]}, username={u[1]}, name={u[2]}')
print()

# Tracks stats
cursor.execute('SELECT COUNT(*), COUNT(DISTINCT artist), COUNT(DISTINCT album) FROM tracks')
track_stats = cursor.fetchone()
print(f'Tracks: {track_stats[0]} total, {track_stats[1]} artists, {track_stats[2]} albums')

cursor.execute('SELECT enrichment_status, COUNT(*) FROM tracks GROUP BY enrichment_status')
enrichment = cursor.fetchall()
print('Enrichment status:')
for e in enrichment:
    print(f'  {e[0] or "NULL"}: {e[1]}')
print()

# Playlists breakdown
cursor.execute('''
SELECT 
    CASE 
        WHEN is_auto_album = 1 THEN 'auto_album'
        WHEN is_auto_source = 1 THEN 'auto_source'
        ELSE 'user_playlist'
    END as type,
    COUNT(*)
FROM playlists 
GROUP BY type
''')
playlist_types = cursor.fetchall()
print('Playlists by type:')
for p in playlist_types:
    print(f'  {p[0]}: {p[1]}')
print()

# User library
cursor.execute('SELECT COUNT(*), COUNT(DISTINCT user_id), COUNT(DISTINCT track_id) FROM user_library')
lib_stats = cursor.fetchone()
print(f'UserLibrary: {lib_stats[0]} entries, {lib_stats[1]} users, {lib_stats[2]} unique tracks')

cursor.execute('SELECT source, COUNT(*) FROM user_library GROUP BY source')
sources = cursor.fetchall()
print('Library sources:')
for s in sources:
    print(f'  {s[0]}: {s[1]}')
print()

# Forward sources in tracks
cursor.execute('SELECT forward_from_type, COUNT(*) FROM tracks WHERE forward_from_type IS NOT NULL GROUP BY forward_from_type')
forwards = cursor.fetchall()
print('Forward sources:')
for f in forwards:
    print(f'  {f[0]}: {f[1]}')

conn.close()
