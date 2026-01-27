<template>
  <div class="app spotify-theme" :class="{ 'has-player': playerStore.currentTrack }">
    <!-- Auth checking state -->
    <div v-if="authStore.loading && !authStore.initialized" class="auth-loading">
      <div class="auth-spinner"></div>
    </div>

    <!-- Main content with router -->
    <template v-else>
      <!-- Header for authenticated pages -->
      <PageHeader 
        v-if="showHeader"
        :title="pageTitle"
        @goBack="goBack"
      />

      <!-- Router view -->
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <keep-alive :include="['LibraryView', 'AlbumsView', 'ArtistsView', 'PlaylistsView']">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </main>

      <!-- Bottom navigation -->
      <nav v-if="showNav" class="bottom-nav">
        <router-link to="/" class="nav-item" :class="{ active: isRoute('/') }">
          <span class="nav-icon">🎵</span>
          <span class="nav-label">Библиотека</span>
        </router-link>
        <router-link to="/albums" class="nav-item" :class="{ active: isRoute('/albums') }">
          <span class="nav-icon">💿</span>
          <span class="nav-label">Альбомы</span>
        </router-link>
        <router-link to="/artists" class="nav-item" :class="{ active: isRoute('/artists') }">
          <span class="nav-icon">🎤</span>
          <span class="nav-label">Артисты</span>
        </router-link>
        <router-link to="/playlists" class="nav-item" :class="{ active: isRoute('/playlists') }">
          <span class="nav-icon">📁</span>
          <span class="nav-label">Плейлисты</span>
        </router-link>
        <router-link to="/settings" class="nav-item" :class="{ active: isRoute('/settings') }">
          <span class="nav-icon">⚙️</span>
          <span class="nav-label">Настройки</span>
        </router-link>
      </nav>

      <!-- Mini player -->
      <MiniPlayer 
        v-if="playerStore.currentTrack && showNav" 
        @click="showFullPlayer = true"
      />

      <!-- Full player modal -->
      <FullPlayer 
        v-if="showFullPlayer"
        @close="showFullPlayer = false"
      />
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import PageHeader from '@/components/PageHeader.vue'
import MiniPlayer from '@/components/MiniPlayer.vue'
import FullPlayer from '@/components/FullPlayer.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const playerStore = usePlayerStore()
const telegram = inject('telegram')

const showFullPlayer = ref(false)

// Navigation visibility
const showNav = computed(() => {
  return authStore.isAuthenticated && route.name !== 'login'
})

const showHeader = computed(() => {
  const noHeaderRoutes = ['login', 'library']
  return authStore.isAuthenticated && !noHeaderRoutes.includes(route.name)
})

const pageTitle = computed(() => {
  const titles = {
    albums: 'Альбомы',
    'album-detail': route.params?.name || 'Альбом',
    artists: 'Исполнители',
    'artist-detail': decodeURIComponent(route.params?.name || 'Артист'),
    playlists: 'Плейлисты',
    'playlist-detail': 'Плейлист',
    settings: 'Настройки',
  }
  return titles[route.name] || ''
})

const isRoute = (path) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}

// Initialize auth on mount
onMounted(async () => {
  // Initialize Telegram WebApp
  if (telegram) {
    telegram.ready()
    telegram.expand()
  }
  
  // Initialize auth
  if (authStore.isAuthenticated && !authStore.initialized) {
    await authStore.initialize()
  }
})
</script>

<style>
:root {
  --bg-primary: #121212;
  --bg-secondary: #181818;
  --bg-elevated: #242424;
  --bg-highlight: #2a2a2a;
  --text-primary: #ffffff;
  --text-secondary: #b3b3b3;
  --text-tertiary: #6a6a6a;
  --accent: #1db954;
  --accent-hover: #1ed760;
  --danger: #e91429;
  --border: #282828;
  --nav-height: 60px;
  --player-height: 64px;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100%;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.app.has-player .main-content {
  padding-bottom: calc(var(--nav-height) + var(--player-height));
}

.auth-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}

.auth-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--bg-highlight);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Bottom Navigation */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--nav-height);
  background: var(--bg-secondary);
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 100;
  padding-bottom: env(safe-area-inset-bottom);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  text-decoration: none;
  color: var(--text-tertiary);
  font-size: 10px;
  padding: 8px 12px;
  transition: color 0.2s;
}

.nav-item.active {
  color: var(--text-primary);
}

.nav-icon {
  font-size: 22px;
}

.nav-label {
  font-weight: 500;
}

/* Has mini player adjustment */
.app.has-player .bottom-nav {
  bottom: var(--player-height);
}
</style>
