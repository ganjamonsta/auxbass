<template>
  <div class="search-results">
    <!-- Loading state -->
    <div v-if="loading && !hasResults" class="skeleton-list">
      <TrackSkeleton v-for="i in 4" :key="i" />
    </div>

    <!-- No results -->
    <div v-else-if="!hasResults && hasQuery" class="empty">
      <div class="empty-icon">🔍</div>
      <p class="empty-title">Ничего не найдено</p>
      <p class="empty-hint">Попробуйте другой запрос</p>
    </div>

    <template v-else>
      <!-- Artists Section -->
      <div v-if="artists.length > 0" class="search-section">
        <h3 class="search-section-title">Артисты</h3>
        <div class="search-artists-list">
          <div
            v-for="artist in artists"
            :key="artist.artist"
            class="search-artist-item"
            @click="$emit('filterArtist', artist.artist)"
          >
            <div class="search-artist-avatar" :style="getArtistStyle(artist.artist)">
              <img 
                v-if="artistImages[artist.artist]" 
                :src="artistImages[artist.artist]" 
                alt=""
                @error="$event.target.style.display = 'none'"
              />
              <span v-else class="avatar-initials">{{ getArtistInitials(artist.artist) }}</span>
            </div>
            <div class="search-artist-info">
              <span class="search-artist-name">{{ artist.artist }}</span>
              <span class="search-artist-count">{{ artist.count }} треков</span>
            </div>
            <svg class="search-item-arrow" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
            </svg>
          </div>
        </div>
      </div>

      <!-- Albums Section -->
      <div v-if="albums.length > 0" class="search-section">
        <h3 class="search-section-title">Альбомы</h3>
        <div class="search-albums-list">
          <div
            v-for="album in albums"
            :key="album.id"
            class="search-album-item"
            @click="$emit('openPlaylist', album)"
          >
            <div class="search-album-cover">
              <img v-if="album.cover_url" :src="album.cover_url" alt="" />
              <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5zm0-5.5c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/>
              </svg>
            </div>
            <div class="search-album-info">
              <span class="search-album-name">{{ album.name }}</span>
              <span class="search-album-artist">{{ album.album_artist || 'Альбом' }} • {{ album.track_count }} треков</span>
            </div>
            <svg class="search-item-arrow" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
            </svg>
          </div>
        </div>
      </div>

      <!-- Playlists Section -->
      <div v-if="playlists.length > 0" class="search-section">
        <h3 class="search-section-title">Плейлисты</h3>
        <div class="search-playlists-list">
          <div
            v-for="playlist in playlists"
            :key="playlist.id"
            class="search-playlist-item"
            @click="$emit('openPlaylist', playlist)"
          >
            <div class="search-playlist-cover">
              <img v-if="playlist.cover_url" :src="playlist.cover_url" alt="" />
              <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
              </svg>
            </div>
            <div class="search-playlist-info">
              <span class="search-playlist-name">{{ playlist.name }}</span>
              <span class="search-playlist-count">{{ playlist.track_count }} треков</span>
            </div>
            <svg class="search-item-arrow" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
            </svg>
          </div>
        </div>
      </div>

      <!-- Tracks Section -->
      <div v-if="tracks.length > 0" class="search-section">
        <h3 class="search-section-title">Треки</h3>
        <TrackItem 
          v-for="track in tracks.slice(0, 20)" 
          :key="track.id"
          :track="track"
          :isPlaying="currentTrackId === track.id && isPlaying"
          :isLiked="isTrackLiked(track.id)"
          @click="$emit('play', track, tracks)"
          @menu="$emit('menu', track)"
          @like="$emit('like', track.id)"
        />
        <button 
          v-if="tracks.length > 20" 
          class="see-all-btn"
          @click="$emit('navigate', 'tracks')"
        >
          Показать все треки ({{ totalTracks }})
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import TrackItem from './TrackItem.vue'
import TrackSkeleton from './TrackSkeleton.vue'
import { getArtistInitials, getArtistAvatarStyle } from '@/utils/styles'

const props = defineProps({
  artists: { type: Array, default: () => [] },
  artistImages: { type: Object, default: () => ({}) },
  albums: { type: Array, default: () => [] },
  playlists: { type: Array, default: () => [] },
  tracks: { type: Array, default: () => [] },
  totalTracks: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
  hasQuery: { type: Boolean, default: false },
  currentTrackId: { type: [Number, String], default: null },
  isPlaying: { type: Boolean, default: false },
  isTrackLiked: { type: Function, required: true },
})

defineEmits(['filterArtist', 'openPlaylist', 'play', 'menu', 'like', 'navigate'])

const hasResults = computed(() => {
  return props.artists.length > 0 ||
         props.albums.length > 0 ||
         props.playlists.length > 0 ||
         props.tracks.length > 0
})

const getArtistStyle = (name) => {
  return getArtistAvatarStyle(name, props.artistImages[name])
}
</script>
