<template>
  <div class="playlist-section">
    <!-- System playlists -->
    <div class="playlist-category">
      <h3 class="category-title">Быстрый доступ</h3>
      <div class="system-playlists-grid">
        <!-- Liked -->
        <div 
          v-if="likedCount > 0" 
          class="system-playlist-item"
          @click="$emit('navigate', 'liked')"
        >
          <div class="system-playlist-icon liked-gradient">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
          </div>
          <div class="system-playlist-info">
            <span class="system-playlist-title">Любимое</span>
            <span class="system-playlist-count">{{ likedCount }} треков</span>
          </div>
        </div>
        
        <!-- History -->
        <div 
          v-if="historyCount > 0" 
          class="system-playlist-item"
          @click="$emit('navigate', 'history')"
        >
          <div class="system-playlist-icon history-gradient">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
            </svg>
          </div>
          <div class="system-playlist-info">
            <span class="system-playlist-title">История</span>
            <span class="system-playlist-count">{{ historyCount }} треков</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Source playlists -->
    <div v-if="sourcePlaylists.length > 0" class="playlist-category">
      <h3 class="category-title clickable" @click="$emit('openSection', 'sources')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 6px; opacity: 0.7;">
          <path d="M21 3H3c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H3V5h18v14zM9.41 15.95L12 13.36l2.59 2.59L16 14.54l-4-4-4 4z"/>
        </svg>
        Источники
        <svg class="section-arrow" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
        </svg>
      </h3>
      <div class="playlists-compact-list">
        <PlaylistItem
          v-for="playlist in sourcePlaylists"
          :key="playlist.id"
          :playlist="playlist"
          @click="$emit('openPlaylist', playlist)"
        />
      </div>
    </div>

    <!-- Album playlists -->
    <div v-if="albumPlaylists.length > 0" class="playlist-category">
      <h3 class="category-title clickable" @click="$emit('openSection', 'albums')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 6px; opacity: 0.7;">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5zm0-5.5c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/>
        </svg>
        Альбомы
        <svg class="section-arrow" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
        </svg>
      </h3>
      <div class="playlists-compact-list">
        <PlaylistItem
          v-for="playlist in albumPlaylists"
          :key="playlist.id"
          :playlist="playlist"
          @click="$emit('openPlaylist', playlist)"
        />
      </div>
    </div>

    <!-- User playlists -->
    <div class="playlist-category">
      <div class="category-header">
        <h3 class="category-title clickable" @click="$emit('openSection', 'playlists')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 6px; opacity: 0.7;">
            <path d="M4 10h12v2H4zm0-4h12v2H4zm0 8h8v2H4zm10 0v6l5-3z"/>
          </svg>
          Мои плейлисты
          <svg class="section-arrow" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
          </svg>
        </h3>
        <button @click.stop="$emit('createPlaylist')" class="create-btn-small">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
          </svg>
        </button>
      </div>
      <div v-if="userPlaylists.length === 0" class="empty-small">
        <p>Нет плейлистов</p>
        <button @click="$emit('createPlaylist')" class="create-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
          </svg>
          <span>Создать плейлист</span>
        </button>
      </div>
      <div v-else class="playlists-compact-list">
        <PlaylistItem
          v-for="playlist in userPlaylists"
          :key="playlist.id"
          :playlist="playlist"
          @click="$emit('openPlaylist', playlist)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import PlaylistItem from './PlaylistItem.vue'

defineProps({
  likedCount: { type: Number, default: 0 },
  historyCount: { type: Number, default: 0 },
  sourcePlaylists: { type: Array, default: () => [] },
  albumPlaylists: { type: Array, default: () => [] },
  userPlaylists: { type: Array, default: () => [] },
})

defineEmits(['navigate', 'openSection', 'openPlaylist', 'createPlaylist'])
</script>
