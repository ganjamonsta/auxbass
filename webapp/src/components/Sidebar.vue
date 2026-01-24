<template>
  <aside class="sidebar">
    <!-- Logo -->
    <div class="sidebar-logo">
      <div class="logo-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
        </svg>
      </div>
      <span class="logo-text">AuxBass</span>
    </div>

    <!-- Main Navigation -->
    <nav class="sidebar-nav">
      <button 
        class="nav-item" 
        :class="{ active: activeTab === 'home' }"
        @click="$emit('navigate', 'home')"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
        </svg>
        <span>Главная</span>
      </button>

      <button 
        class="nav-item" 
        :class="{ active: activeTab === 'search' }"
        @click="$emit('navigate', 'search')"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
        </svg>
        <span>Поиск</span>
      </button>

      <button 
        class="nav-item" 
        :class="{ active: activeTab === 'global' }"
        @click="$emit('navigate', 'global')"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
        </svg>
        <span>Глобальная</span>
      </button>
    </nav>

    <!-- Divider -->
    <div class="sidebar-divider"></div>

    <!-- Library Section -->
    <div class="sidebar-section">
      <div class="section-header">
        <span>Моя музыка</span>
      </div>

      <button 
        class="nav-item" 
        :class="{ active: activeTab === 'tracks' }"
        @click="$emit('navigate', 'tracks')"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
        </svg>
        <span>Все треки</span>
        <span v-if="stats.tracks" class="nav-count">{{ stats.tracks }}</span>
      </button>

      <button 
        class="nav-item" 
        :class="{ active: activeTab === 'liked' }"
        @click="$emit('navigate', 'liked')"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
        </svg>
        <span>Любимое</span>
        <span v-if="stats.liked" class="nav-count">{{ stats.liked }}</span>
      </button>

      <button 
        class="nav-item" 
        :class="{ active: activeTab === 'history' }"
        @click="$emit('navigate', 'history')"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M13 3a9 9 0 00-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0013 21a9 9 0 000-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
        </svg>
        <span>История</span>
      </button>

      <button 
        class="nav-item" 
        :class="{ active: activeTab === 'artists' }"
        @click="$emit('navigate', 'artists')"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>
        <span>Артисты</span>
        <span v-if="stats.artists" class="nav-count">{{ stats.artists }}</span>
      </button>
    </div>

    <!-- Divider -->
    <div class="sidebar-divider"></div>

    <!-- Albums Section -->
    <div v-if="albums.length > 0" class="sidebar-section albums-section">
      <div class="section-header clickable" @click="$emit('navigate', 'albums')">
        <span>Альбомы</span>
        <span class="section-count">{{ albums.length }}</span>
      </div>

      <div class="playlists-list">
        <button 
          v-for="album in displayedAlbums" 
          :key="album.id"
          class="nav-item playlist-item"
          :class="{ active: activePlaylistId === album.id }"
          @click="$emit('openPlaylist', album)"
          @contextmenu.prevent="$emit('playlistMenu', album)"
        >
          <div class="playlist-cover album-cover" :style="getPlaylistCoverStyle(album)">
            <img v-if="album.cover_url" :src="album.cover_url" alt="" />
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5zm0-5.5c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/>
            </svg>
          </div>
          <div class="playlist-info">
            <span class="playlist-name">{{ album.name }}</span>
            <span v-if="album.album_artist" class="playlist-artist">{{ album.album_artist }}</span>
          </div>
          <span class="nav-count">{{ album.track_count }}</span>
        </button>
        
        <!-- Show more albums link -->
        <button 
          v-if="hasMoreAlbums"
          class="nav-item show-more-btn"
          @click="$emit('navigate', 'albums')"
        >
          <span class="show-more-text">Показать все {{ albums.length }} альбомов</span>
        </button>
      </div>
    </div>

    <!-- Divider -->
    <div v-if="albums.length > 0" class="sidebar-divider"></div>

    <!-- Playlists Section -->
    <div class="sidebar-section playlists-section">
      <div class="section-header">
        <span class="section-title clickable" @click="$emit('navigate', 'playlists')">Плейлисты</span>
        <button class="add-playlist-btn" @click="$emit('createPlaylist')" title="Создать плейлист">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
          </svg>
        </button>
      </div>

      <div class="playlists-list">
        <button 
          v-for="playlist in userPlaylists" 
          :key="playlist.id"
          class="nav-item playlist-item"
          :class="{ active: activePlaylistId === playlist.id }"
          @click="$emit('openPlaylist', playlist)"
          @contextmenu.prevent="$emit('playlistMenu', playlist)"
        >
          <div class="playlist-cover" :style="getPlaylistCoverStyle(playlist)">
            <img v-if="playlist.cover_url" :src="playlist.cover_url" alt="" />
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
            </svg>
          </div>
          <span class="playlist-name">{{ playlist.name }}</span>
          <span class="nav-count">{{ playlist.track_count }}</span>
        </button>

        <div v-if="userPlaylists.length === 0" class="empty-playlists">
          <span>Нет плейлистов</span>
        </div>
      </div>
    </div>

    <!-- User Section (bottom) -->
    <div class="sidebar-footer">
      <div class="user-info">
        <div class="user-avatar">
          {{ userInitials }}
        </div>
        <span class="user-name">{{ userName }}</span>
      </div>
      <button class="logout-btn" @click="$emit('logout')" title="Выйти">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/>
        </svg>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  activeTab: {
    type: String,
    default: 'home'
  },
  activePlaylistId: {
    type: Number,
    default: null
  },
  playlists: {
    type: Array,
    default: () => []
  },
  stats: {
    type: Object,
    default: () => ({ tracks: 0, liked: 0, artists: 0 })
  },
  userName: {
    type: String,
    default: 'User'
  }
})

defineEmits(['navigate', 'openPlaylist', 'createPlaylist', 'logout', 'playlistMenu'])

// Separate albums and user playlists
const albums = computed(() => {
  return props.playlists.filter(p => p.is_auto_album)
})

const displayedAlbums = computed(() => {
  return albums.value.slice(0, 5)
})

const hasMoreAlbums = computed(() => {
  return albums.value.length > 5
})

const userPlaylists = computed(() => {
  return props.playlists.filter(p => !p.is_auto_album)
})

const userInitials = computed(() => {
  const name = props.userName || 'U'
  return name.substring(0, 2).toUpperCase()
})

const getPlaylistCoverStyle = (playlist) => {
  if (playlist.cover_url) return {}
  
  // Generate gradient from playlist name
  const str = playlist.name || 'Playlist'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash % 360)
  
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 50%, 40%) 0%, hsl(${(hue + 30) % 360}, 40%, 30%) 100%)`
  }
}
</script>

<style scoped>
.sidebar {
  width: 280px;
  height: 100%;
  background: #0a0a0a;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar::-webkit-scrollbar {
  width: 6px;
}

.sidebar::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 16px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #1DB954, #1ed760);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: white;
}

.sidebar-nav {
  padding: 8px 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 16px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background: rgba(29, 185, 84, 0.2);
  color: #1DB954;
}

.nav-item.active svg {
  color: #1DB954;
}

.nav-item svg {
  flex-shrink: 0;
  opacity: 0.8;
}

.nav-count {
  margin-left: auto;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
}

.sidebar-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
  margin: 8px 16px;
}

.sidebar-section {
  padding: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-header.clickable,
.section-title.clickable {
  cursor: pointer;
  transition: color 0.15s;
}

.section-header.clickable:hover,
.section-title.clickable:hover {
  color: white;
}

.section-header.clickable:hover .section-count {
  color: rgba(255, 255, 255, 0.6);
}

.add-playlist-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.15s;
}

.add-playlist-btn:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.playlists-section {
  display: flex;
  flex-direction: column;
}

.playlists-list {
  padding-bottom: 8px;
}

.playlist-item {
  padding: 8px 16px;
}

.playlist-cover {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.7);
  flex-shrink: 0;
  overflow: hidden;
}

.playlist-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.playlist-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Album specific styles */
.albums-section {
  display: flex;
  flex-direction: column;
}

.albums-section .playlists-list {
  /* albums show limited */
}

.album-cover {
  border-radius: 2px;
}

/* Show more button */
.show-more-btn {
  justify-content: center !important;
  padding: 10px 16px !important;
  margin-top: 4px;
}

.show-more-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  transition: color 0.15s;
}

.show-more-btn:hover .show-more-text {
  color: #1DB954;
}

.playlist-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.playlist-info .playlist-name {
  flex: none;
}

.playlist-artist {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.section-count {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  font-weight: normal;
}

.empty-playlists {
  padding: 16px;
  text-align: center;
  color: rgba(255, 255, 255, 0.3);
  font-size: 13px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  gap: 12px;
  background: #0a0a0a;
  position: sticky;
  bottom: 0;
  margin-top: auto;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: white;
  flex-shrink: 0;
}

.user-name {
  font-size: 14px;
  color: white;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logout-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.15s;
}

.logout-btn:hover {
  color: #ff6b6b;
  background: rgba(255, 107, 107, 0.1);
}
</style>
