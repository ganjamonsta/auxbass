<template>
  <div class="artist-card">
    <!-- Artist Header -->
    <div class="artist-header">
      <div class="artist-avatar" :style="avatarStyle">
        <img 
          v-if="artist.image_url" 
          :src="artist.image_url" 
          alt=""
          @error="$event.target.style.display = 'none'"
        />
        <span v-else class="avatar-initials">{{ initials }}</span>
      </div>
      <div class="artist-info">
        <h1 class="artist-name">{{ artist.name }}</h1>
        <p class="artist-stats">
          {{ artist.track_count }} треков • {{ formatPlays(artist.total_plays) }}
        </p>
      </div>
      <button class="play-all-btn" @click="playAll" v-if="artist.tracks?.length">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z"/>
        </svg>
      </button>
    </div>

    <!-- Albums Section -->
    <div v-if="artist.albums?.length > 0" class="section">
      <h2 class="section-title">Альбомы</h2>
      <div class="horizontal-scroll">
        <div class="scroll-spacer"></div>
        <div 
          v-for="album in artist.albums" 
          :key="album.id"
          class="album-card"
          @click="$emit('openAlbum', album)"
        >
          <div class="album-cover">
            <img v-if="album.cover_url" :src="album.cover_url" alt="" />
            <svg v-else width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5zm0-5.5c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/>
            </svg>
          </div>
          <div class="album-name">{{ album.name }}</div>
          <div class="album-count">{{ album.track_count }} треков</div>
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
            <img v-if="playlist.cover_url" :src="playlist.cover_url" alt="" />
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
import { computed } from 'vue'
import TrackItem from './TrackItem.vue'

const props = defineProps({
  artist: {
    type: Object,
    required: true
  },
  currentTrackId: Number,
  isPlaying: Boolean
})

const emit = defineEmits(['play', 'menu', 'like', 'openAlbum', 'openPlaylist', 'playAll'])

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

const formatPlays = (count) => {
  if (!count) return '0 прослушиваний'
  if (count === 1) return '1 прослушивание'
  if (count < 5) return `${count} прослушивания`
  return `${count} прослушиваний`
}

const playAll = () => {
  if (props.artist.tracks?.length) {
    emit('play', props.artist.tracks[0], props.artist.tracks)
  }
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

.play-all-btn {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--spotify-green);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(29, 185, 84, 0.4);
  transition: transform 0.15s ease;
}

.play-all-btn:active {
  transform: scale(0.92);
}

.play-all-btn svg {
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

.album-count {
  font-size: 12px;
  color: var(--spotify-text-muted);
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
