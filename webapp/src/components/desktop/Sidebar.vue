<template>
  <aside class="sidebar">
    <!-- Logo -->
    <div class="sidebar-logo">
      <div class="logo-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
        </svg>
      </div>
      <span class="logo-text">{{ authStore.appName || 'auxbassbot' }}</span>
      <div 
        v-if="authStore.user" 
        class="header-avatar clickable" 
        @click="goToMyProfile"
        title="Мой профиль"
      >
        <span class="header-avatar-badge">{{ userInitials }}</span>
      </div>
    </div>

    <!-- Main Navigation -->
    <nav class="sidebar-nav">
      <router-link to="/" class="nav-item" :class="{ active: isActiveExact('/') }">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
        </svg>
        <span>Главная</span>
      </router-link>

      <!-- Library Root -->
      <div 
        class="nav-item clickable" 
        :class="{ active: route.name === 'library' && (!route.query.tab || route.query.tab === 'overview') }"
        @click="goToLibraryTab('overview')"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="m16 6 4 14M12 6v14M8 8v12M4 4v16"></path>
        </svg>
        <span>Библиотека</span>
      </div>

      <!-- Library Sub-links -->
      <div class="sidebar-subnav">
        <div 
          class="nav-subitem clickable" 
          :class="{ active: route.name === 'library' && route.query.tab === 'tracks' }"
          @click="goToLibraryTab('tracks')"
          title="Все треки медиатеки"
        >
          <Music :size="15" />
          <span>Все треки</span>
          <span v-if="libraryStore.tracks?.length" class="sub-count">{{ libraryStore.tracks.length }}</span>
        </div>

        <div 
          class="nav-subitem clickable" 
          :class="{ active: route.name === 'library' && route.query.tab === 'playlists' }"
          @click="goToLibraryTab('playlists')"
          title="Мои плейлисты"
        >
          <ListMusic :size="15" />
          <span>Плейлисты</span>
          <span v-if="userPlaylists.length" class="sub-count">{{ userPlaylists.length }}</span>
        </div>

        <div 
          class="nav-subitem clickable" 
          :class="{ active: route.name === 'library' && route.query.tab === 'artists' }"
          @click="goToLibraryTab('artists')"
          title="Исполнители"
        >
          <Mic2 :size="15" />
          <span>Артисты</span>
        </div>

        <div 
          class="nav-subitem clickable" 
          :class="{ active: route.name === 'library' && route.query.tab === 'albums' }"
          @click="goToLibraryTab('albums')"
          title="Альбомы"
        >
          <Disc3 :size="15" />
          <span>Альбомы</span>
        </div>
      </div>

      <router-link to="/friends" class="nav-item" :class="{ active: isActive('/friends') }">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
          <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
        </svg>
        <span>Друзья (Кенты)</span>
      </router-link>

      <!-- Offline / Cached tracks standout card -->
      <router-link 
        to="/downloaded" 
        class="nav-item offline-highlight-item" 
        :class="{ active: isActive('/downloaded') }"
        title="Кэшированные и скачанные треки"
      >
        <FolderDown :size="20" class="offline-icon" />
        <span>Offline</span>
        <span v-if="cachedTracksCount > 0" class="nav-count offline-count">{{ cachedTracksCount }}</span>
      </router-link>

      <!-- Import Section link -->
      <router-link 
        to="/settings?section=import" 
        class="nav-item import-highlight-item" 
        :class="{ active: route.path === '/settings' && (route.query.section === 'import' || route.hash === '#import') }"
        title="Импорт музыки из Spotify и SoundCloud"
      >
        <Upload :size="20" class="import-icon" />
        <span>Импорт</span>
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

    <!-- User Section (bottom) -->
    <div class="sidebar-footer">
      <div 
        class="user-info clickable" 
        :class="{ active: showProfileMenu }"
        @click="showProfileMenu = !showProfileMenu" 
        @contextmenu.prevent="showProfileMenu = true"
        v-longpress="() => { showProfileMenu = true }"
        title="Меню профиля"
      >
        <div class="user-avatar">
          {{ userInitials }}
        </div>
        <span class="user-name">{{ userName }}</span>
      </div>
      <button 
        v-if="!pwaInstall.isInstalled" 
        class="footer-btn install-btn" 
        @click="pwaInstall.promptInstall()" 
        title="Установить приложение"
      >
        <Download :size="20" />
      </button>
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

    <!-- Context Menu for Profile -->
    <ProfileMenu v-model="showProfileMenu" placement="sidebar" />
  </aside>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { useContextMenu } from '@/composables/useContextMenu'
import { usePwaInstall } from '@/composables/usePwaInstall'
import { getCoverUrl, CoverSize, getPlaylistCoverStyle } from '@/utils'
import { Download, FolderDown, Upload, Music, ListMusic, Mic2, Disc3 } from 'lucide-vue-next'
import { getCacheStats } from '@/utils/audioCacheDb'
import ProfileMenu from '@/components/layout/ProfileMenu.vue'

const route = useRoute()
const router = useRouter()
const libraryStore = useLibraryStore()
const authStore = useAuthStore()
const uiStore = useUIStore()
const pwaInstall = usePwaInstall()
const showProfileMenu = ref(false)
const cachedTracksCount = ref(0)

const updateCachedStats = async () => {
  try {
    const stats = await getCacheStats()
    cachedTracksCount.value = stats?.trackCount || 0
  } catch (_) {}
}

// Universal context menu
const { openMenu } = useContextMenu()

// Stats
const likedCount = computed(() => libraryStore.likedTracks?.length || 0)

// Playlists
const playlists = computed(() => libraryStore.playlists || [])

const userPlaylists = computed(() => playlists.value)

const displayedPlaylists = computed(() => {
  return userPlaylists.value.slice(0, 5)
})

const hasMorePlaylists = computed(() => {
  return userPlaylists.value.length > 5
})

// Navigation
const goToLibraryTab = (tab) => {
  uiStore.setLibraryTab(tab)
  if (tab === 'overview') {
    router.push('/library')
  } else {
    router.push({ path: '/library', query: { tab } })
  }
}

const goToPersonalPlaylists = () => {
  goToLibraryTab('playlists')
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

const goToMyProfile = () => {
  if (authStore.user?.id) {
    router.push(`/user/${authStore.user.id}`)
  }
}

const onPlaylistChanged = () => {
  libraryStore.fetchPlaylists()
}

onMounted(() => {
  window.addEventListener('playlist:changed', onPlaylistChanged)
  window.addEventListener('cache-updated', updateCachedStats)
  updateCachedStats()
})

onUnmounted(() => {
  window.removeEventListener('playlist:changed', onPlaylistChanged)
  window.removeEventListener('cache-updated', updateCachedStats)
})
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
  padding: 20px 16px 16px;
}

.header-avatar {
  margin-left: auto;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #333 0%, #222 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.15);
  cursor: pointer;
  transition: transform 0.15s ease, border-color 0.15s ease;
}

.header-avatar:hover {
  transform: scale(1.06);
  border-color: rgba(255, 255, 255, 0.4);
}

.header-avatar-badge {
  font-size: 12px;
  font-weight: 700;
  color: #fff;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--c-accent, #1db954), var(--c-accent-light, #1ed760));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #000;
}

.logo-text {
  font-size: 18px;
  font-weight: 800;
  color: white;
  letter-spacing: -0.02em;
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
  padding: 10px 14px;
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
  background: rgba(255, 255, 255, 0.08);
  color: white;
}

.nav-item.active {
  background: rgba(29, 185, 84, 0.12);
  color: var(--c-accent, #1db954);
  font-weight: 600;
}

.nav-item.active svg {
  color: var(--c-accent, #1db954);
  opacity: 1;
}

/* Sidebar Subnav (Under Library) */
.sidebar-subnav {
  margin: 3px 0 6px 16px;
  padding-left: 10px;
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-subitem {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 12px;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.65);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}

.nav-subitem:hover {
  background: rgba(255, 255, 255, 0.07);
  color: white;
}

.nav-subitem.active {
  background: rgba(29, 185, 84, 0.12);
  color: var(--c-accent, #1db954);
  font-weight: 600;
}

.nav-subitem.active svg {
  color: var(--c-accent, #1db954);
}

.sub-count {
  margin-left: auto;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 6px;
  border-radius: 8px;
}

.offline-highlight-item {
  margin-top: 8px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 11px 14px;
}

.offline-highlight-item:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.18);
  transform: translateY(-1px);
}

.offline-highlight-item.active {
  background: rgba(29, 185, 84, 0.15);
  border-color: rgba(29, 185, 84, 0.4);
  color: var(--c-accent, #1db954);
}

.offline-highlight-item .offline-count {
  background: rgba(255, 255, 255, 0.14);
  color: rgba(255, 255, 255, 0.85);
  font-weight: 600;
}

.import-highlight-item {
  margin-top: 4px;
}

.import-highlight-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: white;
}

.import-highlight-item.active {
  background: rgba(29, 185, 84, 0.12);
  color: var(--c-accent, #1db954);
  font-weight: 600;
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
  color: var(--c-accent);
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

.user-info.clickable {
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--r-md);
  transition: background 0.15s ease;
}

.user-info.clickable:hover,
.user-info.clickable.active {
  background: rgba(255, 255, 255, 0.12);
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

.install-btn:hover {
  color: var(--c-accent, #1db954);
  background: rgba(29, 185, 84, 0.15);
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
