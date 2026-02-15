<template>
  <aside class="sidebar">
    <!-- Logo -->
    <div class="sidebar-logo">
      <div class="logo-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
        </svg>
      </div>
      <span class="logo-text">{{ authStore.appName }}</span>
    </div>

    <!-- Main Navigation -->
    <nav class="sidebar-nav">
      <router-link to="/" class="nav-item" :class="{ active: isActiveExact('/') }">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
        </svg>
        <span>Главная</span>
      </router-link>

      <router-link to="/liked" class="nav-item" :class="{ active: isActive('/liked') }">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
        </svg>
        <span>Любимое</span>
        <span v-if="likedCount" class="nav-count">{{ formatCount(likedCount) }}</span>
      </router-link>

      <router-link to="/albums" class="nav-item" :class="{ active: isActive('/albums') }">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5zm0-5.5c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/>
        </svg>
        <span>Альбомы</span>
        <span v-if="albums.length" class="nav-count">{{ albums.length }}</span>
      </router-link>
    </nav>

    <!-- Playlists Section -->
    <div v-if="displayedPlaylists.length > 0" class="sidebar-section playlists-section">
      <div class="section-header clickable" @click="goToPersonalPlaylists">
        <span>Плейлисты</span>
        <span class="section-count">{{ userPlaylists.length }}</span>
      </div>

      <div class="playlists-list">
        <div 
          v-for="playlist in displayedPlaylists" 
          :key="playlist.id"
          class="nav-item playlist-item"
          :class="{ active: $route.params.id == playlist.id && $route.name === 'playlist-detail' }"
          @click="$router.push(`/playlist/${playlist.id}`)"
          @contextmenu.prevent="openMenu('playlist', playlist, 'sidebar', $event)"
        >
          <div class="playlist-cover" :style="getPlaylistCoverStyle(playlist)">
            <img v-if="playlist.covers?.length" :key="playlist.covers[0]" :src="getCoverUrl(playlist.covers[0], CoverSize.SMALL)" alt="" />
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
            </svg>
          </div>
          <div class="playlist-info">
            <span class="playlist-name">{{ playlist.name }}</span>
          </div>
          <span class="nav-count">{{ playlist.track_count }}</span>
        </div>
        
        <!-- Show more link -->
        <div 
          v-if="hasMorePlaylists"
          class="nav-item show-more-btn"
          @click="goToPersonalPlaylists"
        >
          <span class="show-more-text">Показать все {{ userPlaylists.length }}</span>
        </div>
      </div>
    </div>

    <!-- Friends Section -->
    <div class="sidebar-section">
      <router-link to="/friends" class="nav-item" :class="{ active: isActive('/friends') }">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
        </svg>
        <span>Кенты</span>
      </router-link>
    </div>

    <!-- Divider -->
    <div class="sidebar-divider"></div>

    <!-- Library Section -->
    <div class="sidebar-section">
      <router-link to="/collections" class="nav-item" :class="{ active: isActive('/collections') }">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
        </svg>
        <span>Коллекции</span>
      </router-link>

      <router-link to="/artists" class="nav-item" :class="{ active: isActive('/artists') }">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>
        <span>Артисты</span>
        <span v-if="artistCount" class="nav-count">{{ formatCount(artistCount) }}</span>
      </router-link>


    </div>

    <!-- User Section (bottom) -->
    <div class="sidebar-footer">
      <div class="user-info">
        <div class="user-avatar">
          {{ userInitials }}
        </div>
        <span class="user-name">{{ userName }}</span>
      </div>
      <router-link to="/settings" class="footer-btn settings-btn" title="Настройки">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
        </svg>
      </router-link>
      <button class="footer-btn logout-btn" @click="logout" title="Выйти">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/>
        </svg>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { useContextMenu } from '@/composables/useContextMenu'
import { getCoverUrl, CoverSize } from '@/utils'

const route = useRoute()
const router = useRouter()
const libraryStore = useLibraryStore()
const authStore = useAuthStore()
const uiStore = useUIStore()

// Universal context menu
const { openMenu } = useContextMenu()

// Stats
const likedCount = computed(() => libraryStore.likedTracks?.length || 0)
const artistCount = computed(() => libraryStore.artists?.length || 0)

// Playlists
const playlists = computed(() => libraryStore.playlists || [])

const albums = computed(() => {
  return playlists.value.filter(p => p.is_auto_album && p.track_count > 0)
})

const userPlaylists = computed(() => {
  return playlists.value.filter(p => !p.is_auto_album && !p.is_auto_source)
})

const displayedPlaylists = computed(() => {
  return userPlaylists.value.slice(0, 5)
})

const hasMorePlaylists = computed(() => {
  return userPlaylists.value.length > 5
})

// Navigation
const goToPersonalPlaylists = () => {
  uiStore.setLibraryTab('playlists')
  router.push('/')
}

// Format large numbers
const formatCount = (count) => {
  if (count >= 1000) {
    return (count / 1000).toFixed(1).replace('.0', '') + 'k'
  }
  return count
}

// User info
const userName = computed(() => {
  const user = authStore.user
  if (!user) return 'User'
  return user.first_name || user.username || `User ${user.id}`
})

const userInitials = computed(() => {
  const name = userName.value || 'U'
  return name.substring(0, 2).toUpperCase()
})

// Route matching
const isActive = (path) => {
  return route.path.startsWith(path)
}

const isActiveExact = (path) => {
  return route.path === path
}

// Actions
const createPlaylist = async () => {
  try {
    const name = prompt('Название плейлиста:')
    if (!name) return
    await libraryStore.createPlaylist(name)
  } catch (error) {
    console.error('Failed to create playlist:', error)
  }
}

const logout = async () => {
  if (confirm('Вы уверены, что хотите выйти?')) {
    authStore.logout()
    // Force full page reload to clear all store states
    window.location.href = '/login'
  }
}

const getPlaylistCoverStyle = (playlist) => {
  if (playlist.covers?.length) return {}
  
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
  flex-direction: row;
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
  text-decoration: none;
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

.nav-item > span:not(.nav-count) {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-count {
  margin-left: auto;
  flex-shrink: 0;
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

.add-playlist-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
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
  flex-direction: row;
  align-items: center;
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

.albums-section {
  display: flex;
  flex-direction: column;
}

.album-cover {
  border-radius: 2px;
}

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
  overflow: hidden;
}

.playlist-info .playlist-name {
  flex: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.footer-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
}

.settings-btn:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.logout-btn:hover {
  color: #ff6b6b;
  background: rgba(255, 107, 107, 0.1);
}
</style>
