<script setup>
import { computed } from 'vue'
import TrackItem from './TrackItem.vue'
import { formatDurationLong } from '@/utils/formatters'

const props = defineProps({
  playlist: { type: Object, default: null },
  currentTrackId: { type: Number, default: null },
  isPlaying: { type: Boolean, default: false },
})

const emit = defineEmits(['play', 'playAll', 'download', 'menu'])

// Get up to 4 unique cover images for playlist collage
const collageCovers = computed(() => {
  if (!props.playlist?.tracks) return []
  
  const covers = []
  const seen = new Set()
  
  for (const track of props.playlist.tracks) {
    if (track.cover_url && !seen.has(track.cover_url)) {
      seen.add(track.cover_url)
      covers.push(track.cover_url)
      if (covers.length >= 4) break
    }
  }
  
  return covers.length > 0 ? covers : []
})

const formatDuration = (seconds) => {
  if (!seconds) return ''
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours} ч ${mins} мин`
  }
  return `${mins} мин`
}
</script>

<template>
  <div class="playlist-view">
    <div class="playlist-header-section">
      <!-- Album cover or track collage -->
      <div class="playlist-cover" :class="{ 'has-cover': playlist?.cover_url || collageCovers.length > 0 }">
        <!-- Single album cover -->
        <img v-if="playlist?.cover_url" :src="playlist.cover_url" alt="" class="cover-image" />
        <!-- 4-track collage for regular playlists -->
        <div v-else-if="collageCovers.length > 0" class="cover-collage">
          <img v-for="(cover, i) in collageCovers" :key="i" :src="cover" alt="" class="collage-img" />
        </div>
        <!-- Fallback icon -->
        <svg v-else width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
          <path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
        </svg>
      </div>
      <div class="playlist-meta">
        <span v-if="playlist?.album_artist" class="playlist-artist">{{ playlist.album_artist }}</span>
        <h2>{{ playlist?.name }}</h2>
        <p>{{ playlist?.track_count }} треков • {{ formatDuration(playlist?.total_duration) }}</p>
      </div>
      <button class="download-playlist-btn" @click="$emit('download')" title="Скачать все треки">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
        </svg>
      </button>
      <button class="play-all-btn" @click="$emit('playAll')">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z"/>
        </svg>
      </button>
    </div>
    <TrackItem 
      v-for="track in playlist?.tracks" 
      :key="track.id"
      :track="track"
      :isPlaying="currentTrackId === track.id && isPlaying"
      @click="$emit('play', track, playlist?.tracks)"
      @menu="$emit('menu', track)"
    />
  </div>
</template>

<style scoped>
.playlist-view {
  padding: 16px;
}

.playlist-header-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.playlist-cover {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--spotify-gray) 0%, var(--spotify-gray-dark) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--spotify-text-secondary);
  overflow: hidden;
  flex-shrink: 0;
}

.playlist-cover.has-cover {
  background: transparent;
}

.playlist-cover .cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-collage {
  width: 100%;
  height: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 1px;
}

.cover-collage .collage-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-collage .collage-img:only-child {
  grid-column: 1 / -1;
  grid-row: 1 / -1;
}

.playlist-meta {
  flex: 1;
  min-width: 0;
}

.playlist-artist {
  font-size: 12px;
  color: var(--spotify-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: block;
  margin-bottom: 2px;
}

.playlist-meta h2 {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.playlist-meta p {
  font-size: 13px;
  color: var(--spotify-text-muted);
}

.play-all-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--spotify-green);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: black;
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
  transition: transform 0.2s, box-shadow 0.2s;
  flex-shrink: 0;
}

.play-all-btn svg {
  width: 22px;
  height: 22px;
}

.play-all-btn:active {
  transform: scale(0.95);
}

.download-playlist-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--spotify-gray);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--spotify-text-secondary);
  transition: transform 0.15s, background 0.15s;
  flex-shrink: 0;
}

.download-playlist-btn svg {
  width: 18px;
  height: 18px;
}

.download-playlist-btn:active {
  transform: scale(0.95);
  background: var(--spotify-gray-light);
}
</style>
