<template>
  <div class="artist-card">
    <!-- Artist Header -->
    <div class="artist-header">
      <div class="artist-avatar" :style="avatarStyle">
        <img 
          v-if="artist.image_url" 
          :src="getCoverUrl(artist.image_url, CoverSize.LARGE)" 
          alt=""
          @error="$event.target.style.display = 'none'"
        />
        <span v-else class="avatar-initials">{{ initials }}</span>
      </div>
      <div class="artist-info">
        <h1 class="artist-name">{{ artist.name }}</h1>
        <p class="artist-stats">
          {{ artist.track_count }} треков • {{ formatPlayCount(artist.total_plays) }}
        </p>
      </div>
      <div class="action-buttons" v-if="artist.tracks?.length">
        <button class="action-btn play-btn" @click="playAll">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </button>
        <button class="action-btn shuffle-btn" @click="shufflePlay" :disabled="isShuffling">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Albums Section -->
    <div v-if="artist.albums?.length > 0" class="section">
      <h2 class="section-title">Альбомы</h2>
      <div class="horizontal-scroll">
        <div class="scroll-spacer"></div>
        <div 
          v-for="album in sortedAlbums" 
          :key="album.id"
          class="album-card"
          @click="$emit('openAlbum', album)"
          @contextmenu.prevent="$emit('albumContextmenu', { album, event: $event })"
        >
          <div class="album-cover">
            <img v-if="album.cover_url" :src="getCoverUrl(album.cover_url, CoverSize.SMALL)" alt="" />
            <svg v-else width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5zm0-5.5c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/>
            </svg>
          </div>
          <div class="album-name">{{ album.name }}</div>
          <div class="album-meta">
            <span class="album-count">{{ album.track_count }} треков</span>
            <span v-if="album.release_date" class="album-year">{{ formatReleaseYear(album.release_date) }}</span>
          </div>
        </div>
        <div class="scroll-spacer"></div>
      </div>
    </div>

    <!-- Playlists containing artist -->
    <div v-if="artist.playlists?.length > 0" class="section">
      <h2 class="section-title">В плейлистах</h2>
      <div class="horizontal-scroll">
        <div class="scroll-spacer"></div>
        <div 
          v-for="playlist in artist.playlists" 
          :key="playlist.id"
          class="playlist-card"
          @click="$emit('openPlaylist', playlist)"
        >
          <div class="playlist-cover">
            <img v-if="playlist.cover_url" :src="getCoverUrl(playlist.cover_url, CoverSize.SMALL)" alt="" />
            <svg v-else width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
            </svg>
          </div>
          <div class="playlist-name">{{ playlist.name }}</div>
          <div class="playlist-count">{{ playlist.track_count }} треков</div>
        </div>
        <div class="scroll-spacer"></div>
      </div>
    </div>

    <!-- Tracks Section -->
    <div class="section tracks-section">
      <h2 class="section-title">Все треки</h2>
      <div class="tracks-list">
        <TrackItem 
          v-for="track in artist.tracks" 
          :key="track.id"
          :track="track"
          :isPlaying="currentTrackId === track.id && isPlaying"
          :isLiked="track.is_liked"
          @click="$emit('play', track, artist.tracks)"
          @menu="$emit('menu', track)"
          @like="$emit('like', track.id)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import TrackItem from './TrackItem.vue'
import { formatPlayCount, getCoverUrl, CoverSize } from '@/utils'

const props = defineProps({
  artist: {
    type: Object,
    required: true
  },
  currentTrackId: Number,
  isPlaying: Boolean,
  isShuffling: Boolean
})

const emit = defineEmits(['play', 'menu', 'like', 'openAlbum', 'openPlaylist', 'playAll', 'shuffleAll', 'albumContextmenu'])

const initials = computed(() => {
  const name = props.artist.name || '?'
  const words = name.split(' ').filter(w => w.length > 0)
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
})

const avatarStyle = computed(() => {
  if (props.artist.image_url) return {}
  
  // Generate gradient based on name
  const name = props.artist.name || ''
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue1 = Math.abs(hash % 360)
  const hue2 = (hue1 + 40) % 360
  
  return {
    background: `linear-gradient(135deg, hsl(${hue1}, 60%, 45%) 0%, hsl(${hue2}, 50%, 35%) 100%)`
  }
})

// Sort albums by release date (newest first)
const sortedAlbums = computed(() => {
  if (!props.artist.albums) return []
  
  return [...props.artist.albums].sort((a, b) => {
    // Albums with release_date come first, sorted newest to oldest
    if (a.release_date && b.release_date) {
      return b.release_date.localeCompare(a.release_date)
    }
    if (a.release_date) return -1
    if (b.release_date) return 1
    return 0
  })
})

// Format release date to just year
const formatReleaseYear = (dateStr) => {
  if (!dateStr) return ''
  // dateStr is in YYYY-MM-DD format
  return dateStr.split('-')[0]
}

const playAll = () => {
  if (props.artist.tracks?.length) {
    emit('play', props.artist.tracks[0], props.artist.tracks)
  }
}

// Emit shuffleAll event - parent should call playerStore.playShuffleAll('artist', artistName)
const shufflePlay = () => {
  emit('shuffleAll', props.artist.name)
}
</script>

<style scoped>
.artist-card {
  padding-bottom: 100px;
}

/* ─── Header ─── */
.artist-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 16px;
  background: linear-gradient(180deg, var(--spotify-gray-dark) 0%, transparent 100%);
}

.artist-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-shadow: 
    6px 6px 12px var(--neu-shadow-dark),
    -4px -4px 8px var(--neu-shadow-light);
}

.artist-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-initials {
  font-size: 32px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.artist-info {
  flex: 1;
  min-width: 0;
}

.artist-name {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.artist-stats {
  font-size: 14px;
  color: var(--spotify-text-muted);
  margin: 0;
}

/* ─── Neumorphic Action Buttons ─── */
.action-buttons {
  display: flex;
  flex-shrink: 0;
  border-radius: 28px;
  background: var(--spotify-green);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.3),
    -3px -3px 8px rgba(255, 255, 255, 0.1),
    inset 0 1px 1px rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.action-btn {
  width: 48px;
  height: 48px;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
}

.action-btn::after {
  content: '';
  position: absolute;
  top: 8px;
  bottom: 8px;
  width: 1px;
  background: rgba(255, 255, 255, 0.2);
}

.action-btn.play-btn::after {
  right: 0;
}

.action-btn.shuffle-btn::after {
  display: none;
}

.action-btn:active {
  background: rgba(0, 0, 0, 0.15);
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.action-btn.play-btn svg {
  margin-left: 2px;
}

/* ─── Sections ─── */
.section {
  margin-top: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 12px;
  padding: 0 16px;
}

/* ─── Horizontal Scroll ─── */
.horizontal-scroll {
  display: flex;
  overflow-x: auto;
  gap: 12px;
  scrollbar-width: none;
  -ms-overflow-style: none;
  scroll-snap-type: x mandatory;
}

.horizontal-scroll::-webkit-scrollbar {
  display: none;
}

.scroll-spacer {
  flex-shrink: 0;
  width: 16px;
  scroll-snap-align: start;
}

/* ─── Album Cards ─── */
.album-card {
  flex-shrink: 0;
  width: 130px;
  cursor: pointer;
  scroll-snap-align: start;
}

.album-card:active {
  opacity: 0.7;
}

.album-cover {
  width: 130px;
  height: 130px;
  border-radius: var(--neu-radius-md);
  background: var(--xm-bg-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light);
}

.album-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.album-cover svg {
  color: var(--spotify-text-muted);
}

.album-name {
  margin-top: 8px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.album-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--spotify-text-muted);
}

.album-count {
  /* inherits from .album-meta */
}

.album-year {
  opacity: 0.7;
}

.album-year::before {
  content: "•";
  margin-right: 6px;
}

/* ─── Playlist Cards ─── */
.playlist-card {
  flex-shrink: 0;
  width: 130px;
  cursor: pointer;
  scroll-snap-align: start;
}

.playlist-card:active {
  opacity: 0.7;
}

.playlist-cover {
  width: 130px;
  height: 130px;
  border-radius: var(--neu-radius-md);
  background: var(--xm-bg-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light);
}

.playlist-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.playlist-cover svg {
  color: var(--spotify-text-muted);
}

.playlist-name {
  margin-top: 8px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.playlist-count {
  font-size: 12px;
  color: var(--spotify-text-muted);
}

/* ─── Tracks Section ─── */
.tracks-section {
  padding: 0;
}

.tracks-section .section-title {
  padding: 0 16px;
}

.tracks-list {
  margin-top: 8px;
}
</style>
