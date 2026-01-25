<template>
  <div class="home-feed">
    <!-- Quick Access Grid -->
    <div class="quick-grid">
      <!-- Liked tracks -->
      <div 
        class="quick-item liked-quick" 
        v-if="likedCount > 0"
        @click="$emit('navigate', 'liked')"
      >
        <div class="quick-icon liked-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
          </svg>
        </div>
        <span class="quick-title">Любимое</span>
      </div>
      
      <!-- History -->
      <div 
        class="quick-item" 
        v-if="historyCount > 0"
        @click="$emit('navigate', 'history')"
      >
        <div class="quick-icon history-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M13 3a9 9 0 00-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0013 21a9 9 0 000-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
          </svg>
        </div>
        <span class="quick-title">Недавнее</span>
      </div>
      
      <!-- All playlists link -->
      <div 
        class="quick-item"
        v-if="playlistCount > 1"
        @click="$emit('navigate', 'playlists')"
      >
        <div class="quick-icon allpl-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9h-4v4h-2v-4H9V9h4V5h2v4h4v2z"/>
          </svg>
        </div>
        <span class="quick-title">Плейлисты</span>
      </div>
    </div>

    <!-- Top Artists Section -->
    <div v-if="artists.length > 0" class="feed-section">
      <h2 class="feed-section-title">Твои артисты</h2>
      <div class="horizontal-scroll artists-scroll">
        <div class="scroll-spacer"></div>
        <div 
          v-for="artist in artists.slice(0, 10)" 
          :key="artist.artist"
          class="feed-card artist-card"
          @click="$emit('filterArtist', artist.artist)"
        >
          <div class="feed-card-cover artist-cover" :style="getArtistStyle(artist.artist)">
            <img 
              v-if="artistImages[artist.artist]" 
              :src="artistImages[artist.artist]" 
              alt=""
            />
            <span v-else class="artist-initials">{{ getArtistInitials(artist.artist) }}</span>
          </div>
          <div class="feed-card-title">{{ artist.artist }}</div>
          <div class="feed-card-subtitle">{{ artist.count }} треков</div>
        </div>
        <div class="scroll-spacer"></div>
      </div>
    </div>

    <!-- Genres Section -->
    <div v-if="genres.length > 0" class="feed-section">
      <h2 class="feed-section-title">Жанры</h2>
      <div class="horizontal-scroll genres-scroll">
        <div class="scroll-spacer"></div>
        <div 
          v-for="genre in genres.slice(0, 10)" 
          :key="genre.genre"
          class="feed-card genre-card"
          @click="$emit('playGenre', genre.genre)"
        >
          <div class="feed-card-cover genre-cover" :style="getGenreStyle(genre.genre)">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor" class="genre-icon">
              <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
            </svg>
            <div class="shuffle-badge">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
              </svg>
            </div>
          </div>
          <div class="feed-card-title">{{ genre.genre }}</div>
          <div class="feed-card-subtitle">{{ genre.count }} треков</div>
        </div>
        <div class="scroll-spacer"></div>
      </div>
    </div>

    <!-- All Tracks Section -->
    <div class="feed-section">
      <h2 class="feed-section-title">Вся музыка</h2>
      <div class="feed-tracks-preview">
        <TrackItem 
          v-for="track in tracks.slice(0, 5)" 
          :key="track.id"
          :track="track"
          :isPlaying="currentTrackId === track.id && isPlaying"
          :isLiked="isTrackLiked(track.id)"
          @click="$emit('play', track)"
          @menu="$emit('menu', track)"
          @like="$emit('like', track.id)"
        />
        <button v-if="tracks.length > 5" class="see-all-btn" @click="$emit('navigate', 'tracks')">
          Смотреть все ({{ totalTracks }})
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import TrackItem from './TrackItem.vue'
import { getGenreStyle, getArtistInitials, getArtistAvatarStyle } from '@/utils/styles'

const props = defineProps({
  artists: { type: Array, default: () => [] },
  artistImages: { type: Object, default: () => ({}) },
  genres: { type: Array, default: () => [] },
  tracks: { type: Array, default: () => [] },
  totalTracks: { type: Number, default: 0 },
  likedCount: { type: Number, default: 0 },
  historyCount: { type: Number, default: 0 },
  playlistCount: { type: Number, default: 0 },
  currentTrackId: { type: [Number, String], default: null },
  isPlaying: { type: Boolean, default: false },
  isTrackLiked: { type: Function, required: true },
})

defineEmits(['navigate', 'filterArtist', 'playGenre', 'play', 'menu', 'like'])

// Use shared style utility with artist images
const getArtistStyle = (name) => {
  return getArtistAvatarStyle(name, props.artistImages[name])
}
</script>
