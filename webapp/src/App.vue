<template>
  <div class="app spotify-theme" :class="appClasses">
    <!-- Auth checking state -->
    <div v-if="authStore.loading && !authStore.initialized" class="auth-loading">
      <div class="auth-spinner"></div>
    </div>

    <!-- Main content with router -->
    <template v-else>
      <!-- Desktop Sidebar -->
      <Sidebar v-if="isDesktop && authStore.isAuthenticated" />

      <!-- Main Content Wrapper -->
      <div class="main-content-wrapper">
        <!-- Header for authenticated pages (mobile + desktop detail pages) -->
        <PageHeader 
          v-if="showHeader"
          :title="pageTitle"
          :showBack="showBackButton"
          @goBack="goBack"
        >
          <template v-if="route.name === 'library'" #icon>
            <component :is="libraryIcon" :size="20" />
          </template>
          <template v-if="route.name === 'library'" #toggle>
            <div class="neu-tab-bar header-tabs">
              <button 
                v-for="tab in [{ id: 'tracks', label: 'Треки' }, { id: 'albums', label: 'Альбомы' }, { id: 'artists', label: 'Артисты' }, { id: 'playlists', label: 'Плейлисты' }]"
                :key="tab.id"
                class="neu-tab" 
                :class="{ active: uiStore.libraryTab === tab.id }"
                @click="uiStore.setLibraryTab(tab.id)"
              >
                <span class="neu-tab-content" :data-text="tab.label">{{ tab.label }}</span>
              </button>
            </div>
          </template>
          <template v-if="route.name === 'collections'" #toggle>
            <div class="neu-tab-bar header-tabs">
              <button 
                class="neu-tab" 
                :class="{ active: uiStore.collectionsTab === 'albums' }"
                @click="uiStore.setCollectionsTab('albums')"
              >
                <span class="neu-tab-content" data-text="Альбомы">Альбомы</span>
              </button>
              <button 
                class="neu-tab" 
                :class="{ active: uiStore.collectionsTab === 'playlists' }"
                @click="uiStore.setCollectionsTab('playlists')"
              >
                <span class="neu-tab-content" data-text="Плейлисты">Плейлисты</span>
              </button>
            </div>
          </template>
        </PageHeader>

        <!-- Router view -->
        <main ref="scrollRef" class="main-content">
          <!-- Pull-to-refresh indicator -->
          <div
            v-if="pullDistance > 0 || isRefreshing"
            class="pull-to-refresh-indicator"
            :style="{ transform: `translateY(${isRefreshing ? 60 : pullDistance}px)` }"
          >
            <div class="ptr-spinner" :class="{ active: isRefreshing, ready: isPulling }">
              <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
              </svg>
            </div>
            <span class="ptr-text">{{ isRefreshing ? 'Обновление…' : isPulling ? 'Отпустите' : 'Потяните вниз' }}</span>
          </div>

          <router-view v-slot="{ Component }">
            <keep-alive :include="['LibraryView', 'CollectionsView', 'LikedTracksView', 'FriendsView']">
              <component :is="Component" />
            </keep-alive>
          </router-view>
        </main>

      </div>

      <!-- Mobile Footer (Player + Navigation) -->
      <MobileFooter
        v-if="showNav && !isDesktop"
        :showPlayer="!!playerStore.currentTrack"
        :currentTrack="playerStore.currentTrack"
        :isPlaying="playerStore.isPlaying"
        :loading="playerStore.loading"
        :progress="playerStore.progress"
        :duration="playerStore.duration"
        :buffered="playerStore.buffered"
        @expand-player="showFullPlayer = true"
        @toggle-play="playerStore.togglePlay()"
        @next-track="playerStore.next()"
        @toggle-shuffle="playerStore.toggleShuffle()"
        @toggle-repeat="playerStore.toggleRepeat()"
      />

      <!-- Desktop: Now Playing Sidebar -->
      <NowPlayingSidebar 
        v-if="isDesktop && playerStore.currentTrack && authStore.isAuthenticated"
        @goToUser="handleGoToUser"
      />

      <!-- Desktop: Bottom Player -->
      <DesktopPlayer 
        v-if="isDesktop && playerStore.currentTrack && authStore.isAuthenticated"
        @expand="showFullPlayer = true"
      />

      <!-- Full player modal - Desktop version -->
      <FullPlayerDesktop
        v-if="showFullPlayer && isDesktop"
        :show="showFullPlayer"
        :track="playerStore.currentTrack"
        :is-playing="playerStore.isPlaying"
        :loading="playerStore.loading"
        :progress="playerStore.progress"
        :duration="playerStore.duration"
        :buffered="playerStore.buffered"
        :volume="playerStore.volume"
        :is-muted="playerStore.isMuted"
        :shuffle="playerStore.shuffle"
        :repeat="playerStore.repeat"
        :is-liked="isCurrentTrackLiked"
        :upcoming-queue="upcomingTracks"
        :queue-length="playerStore.queue.length"
        :history-tracks="historyTracks"
        :hd-track-info="playerStore.hdTrackInfo"
        :lazy-shuffle-mode="playerStore.isLazyShuffleMode()"
        :lazy-shuffle-total="playerStore.lazyShuffleIds?.length || 0"
        :lazy-shuffle-index="playerStore.lazyShuffleIndex"
        :context-info="playerStore.lazyShuffleContext"
        @close="showFullPlayer = false"
        @toggle="playerStore.togglePlay()"
        @next="playerStore.next()"
        @prev="playerStore.prev()"
        @seek="playerStore.seek($event)"
        @setVolume="playerStore.setVolume($event)"
        @toggleMute="playerStore.toggleMute()"
        @toggleShuffle="playerStore.toggleShuffle()"
        @toggleRepeat="playerStore.toggleRepeat()"
        @playFromQueue="playerStore.playFromQueue($event)"
        @like="handleToggleLike"
      />

      <!-- Full player modal - Mobile version (original) -->
      <FullPlayer 
        v-if="showFullPlayer && !isDesktop"
        :track="playerStore.currentTrack"
        :is-playing="playerStore.isPlaying"
        :loading="playerStore.loading"
        :progress="playerStore.progress"
        :duration="playerStore.duration"
        :buffered="playerStore.buffered"
        :volume="playerStore.volume"
        :is-muted="playerStore.isMuted"
        :shuffle="playerStore.shuffle"
        :repeat="playerStore.repeat"
        :queue="playerStore.queue"
        :queue-index="playerStore.queueIndex"
        :shuffle-order="playerStore.shuffleOrder"
        :shuffle-index="playerStore.shuffleIndex"
        :is-liked="isCurrentTrackLiked"
        :lazy-shuffle-mode="playerStore.isLazyShuffleMode()"
        :lazy-shuffle-total="playerStore.lazyShuffleIds?.length || 0"
        :lazy-shuffle-index="playerStore.lazyShuffleIndex"
        @close="showFullPlayer = false"
        @toggle="playerStore.togglePlay()"
        @next="playerStore.next()"
        @prev="playerStore.prev()"
        @seek="playerStore.seek($event)"
        @setVolume="playerStore.setVolume($event)"
        @toggleMute="playerStore.toggleMute()"
        @toggleShuffle="playerStore.toggleShuffle()"
        @toggleRepeat="playerStore.toggleRepeat()"
        @removeFromQueue="playerStore.removeFromQueue($event)"
        @moveInQueue="playerStore.moveInQueue($event.from, $event.to)"
        @playFromQueue="playerStore.playFromQueue($event)"
        @like="handleToggleLike"
      />
      
      <!-- Channel setup banner -->
      <ChannelBanner />
      
      <!-- Global context menu (universal for all element types) -->
      <ContextMenu />
      
      <!-- Maintenance status banner -->
      <MaintenanceBanner />

      <!-- Network status banner -->
      <NetworkBanner />
      
      <!-- PWA install banner & guide modal -->
      <PwaInstallBanner />
      <PwaInstallModal />

      <!-- Global toast notifications -->
      <ToastContainer />
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import { useModals } from '@/composables/useModals'
import PageHeader from '@/components/PageHeader.vue'
import FullPlayer from '@/components/FullPlayer.vue'
import ChannelBanner from '@/components/ChannelBanner.vue'
import ToastContainer from '@/components/ToastContainer.vue'
import ContextMenu from '@/components/ContextMenu.vue'
import NetworkBanner from '@/components/NetworkBanner.vue'
import MaintenanceBanner from '@/components/MaintenanceBanner.vue'
import PwaInstallBanner from '@/components/PwaInstallBanner.vue'
import PwaInstallModal from '@/components/PwaInstallModal.vue'
import { useNetworkMonitor } from '@/composables/useNetworkMonitor'
import { usePullToRefresh } from '@/composables/usePullToRefresh'
import { usePwaInstall } from '@/composables/usePwaInstall'
import { MobileFooter } from '@/components/layout'
import { Music, Disc3, User, Folder } from 'lucide-vue-next'
// Desktop components
import Sidebar from '@/components/desktop/Sidebar.vue'
import DesktopPlayer from '@/components/desktop/DesktopPlayer.vue'
import NowPlayingSidebar from '@/components/desktop/NowPlayingSidebar.vue'
import FullPlayerDesktop from '@/components/desktop/FullPlayerDesktop.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const uiStore = useUIStore()
const telegram = inject('telegram')
const networkMonitor = useNetworkMonitor()
const pwaInstall = usePwaInstall()

// Pull-to-refresh — bound to .main-content via scrollRef
const { scrollRef, pullDistance, isPulling, isRefreshing } = usePullToRefresh(
  () => libraryStore.refresh(),
  { telegram }
)

const { showFullPlayer } = useModals(telegram)

// Responsive detection
const isDesktop = ref(window.innerWidth >= 1024)
const updateDesktopState = () => {
  isDesktop.value = window.innerWidth >= 1024
}

// App classes for layout
const appClasses = computed(() => ({
  'has-player': playerStore.currentTrack,
  'desktop-layout': isDesktop.value && authStore.isAuthenticated,
  'has-now-playing': isDesktop.value && playerStore.currentTrack && authStore.isAuthenticated
}))

// Computed property for like state based on libraryStore.likedTracks
const isCurrentTrackLiked = computed(() => {
  const trackId = playerStore.currentTrack?.id
  if (!trackId) return false
  return libraryStore.isTrackLiked(trackId)
})

// Navigation visibility
const showNav = computed(() => {
  return authStore.isAuthenticated && route.name !== 'login'
})

const showHeader = computed(() => {
  // On desktop, show header only for detail pages (not main navigation pages)
  if (isDesktop.value) {
    const detailRoutes = ['album-detail', 'artist-detail', 'playlist-detail', 'liked', 'settings']
    return authStore.isAuthenticated && detailRoutes.includes(route.name)
  }
  // On mobile, show header for all pages except login
  const noHeaderRoutes = ['login']
  return authStore.isAuthenticated && !noHeaderRoutes.includes(route.name)
})

const showBackButton = computed(() => {
  // Only the main library page (home) doesn't need back button
  return route.name !== 'library'
})

const pageTitle = computed(() => {
  // Для главной страницы библиотеки показываем название текущего раздела
  if (route.name === 'library') {
    const libraryTitles = {
      tracks: 'Треки',
      albums: 'Альбомы',
      artists: 'Артисты',
      playlists: 'Плейлисты'
    }
    return libraryTitles[uiStore.libraryTab] || 'Библиотека'
  }
  
  const titles = {
    collections: 'Коллекции',
    albums: 'Альбомы',
    'album-detail': route.params?.name || 'Альбом',
    artists: 'Исполнители',
    'artist-detail': decodeURIComponent(route.params?.name || 'Артист'),
    playlists: 'Плейлисты',
    'playlist-detail': 'Плейлист',
    friends: 'Кенты',
    settings: 'Настройки',
  }
  return titles[route.name] || ''
})

const libraryIcon = computed(() => {
  const icons = {
    tracks: Music,
    albums: Disc3,
    artists: User,
    playlists: Folder
  }
  return icons[uiStore.libraryTab] || Music
})

// Queue computeds for desktop player
const upcomingTracks = computed(() => {
  if (playerStore.shuffle) {
    // In shuffle mode, use shuffle order
    const currentShuffleIdx = playerStore.shuffleIndex
    return playerStore.shuffleOrder
      .slice(currentShuffleIdx + 1)
      .map(idx => playerStore.queue[idx])
      .filter(t => t)
  } else {
    // In normal mode, use queue order
    return playerStore.queue.slice(playerStore.queueIndex + 1)
  }
})

const historyTracks = computed(() => {
  if (playerStore.shuffle) {
    // In shuffle mode, get previous tracks from shuffle order
    const currentShuffleIdx = playerStore.shuffleIndex
    return playerStore.shuffleOrder
      .slice(0, currentShuffleIdx)
      .map(idx => playerStore.queue[idx])
      .filter(t => t)
      .reverse()
  } else {
    // In normal mode, get previous tracks
    return playerStore.queue.slice(0, playerStore.queueIndex).reverse()
  }
})

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}

// Toggle like for current track
const handleToggleLike = async () => {
  if (playerStore.currentTrack?.id) {
    await libraryStore.toggleLike(playerStore.currentTrack.id)
  }
}

// Handle navigation to user profile
const handleGoToUser = (user) => {
  if (!user?.id) return
  showFullPlayer.value = false
  // Navigate to friends page and pass user info via query
  router.push({ 
    name: 'friends',
    query: { viewUser: user.id }
  })
}

// Handle auth:logout event (triggered by API interceptor on 401)
const handleAuthLogout = () => {
  authStore.logout()
  playerStore.stop()
  // Force full page reload to clear all store states
  window.location.href = '/login'
}

// Apply UI scale to body
const applyUIScale = () => {
  document.body.style.zoom = playerStore.uiScale
}

// Watch for scale changes
watch(
  () => playerStore.uiScale,
  () => applyUIScale(),
  { immediate: true }
)

// === Player error toast handlers (hoisted for cleanup in onUnmounted) ===
const handlePlayerError = (e) => {
  const { type, track, message, errorCode } = e.detail || {}
  const trackTitle = track?.title || 'Трек'
  
  switch (type) {
    case 'cascade_error':
      uiStore.toast.error('Воспроизведение остановлено', 'Слишком много ошибок подряд. Попробуйте позже.')
      break
    case 'audio_error':
      if (errorCode === 2) {
        uiStore.toast.warning('Ошибка сети', `Не удалось загрузить «${trackTitle}», переключаем...`)
      } else if (errorCode === 3) {
        uiStore.toast.warning('Ошибка декодирования', `Не удалось декодировать «${trackTitle}»`)
      } else {
        uiStore.toast.warning('Ошибка аудио', `Проблема с «${trackTitle}», переключаем...`)
      }
      break
    case 'stall_timeout':
      uiStore.toast.warning('Медленная загрузка', `Трек «${trackTitle}» не загружается — проблемы с сетью`)
      break
    case 'not_found':
      uiStore.toast.error('Трек не найден', `«${trackTitle}» больше недоступен`)
      break
    case 'playback_error':
      uiStore.toast.warning('Ошибка воспроизведения', message || `Проблема с «${trackTitle}»`)
      break
    case 'auth_expired':
      // Silent — will auto-skip, not worth showing toast
      break
  }
}

const handleStallRecovered = (e) => {
  const { track, attempt } = e.detail || {}
  if (attempt > 1) {
    uiStore.toast.info('Восстановлено', `Воспроизведение «${track?.title || 'Трек'}» восстановлено`)
  }
}

const handleNetworkRecovered = () => {
  uiStore.toast.success('Сеть восстановлена', 'Соединение восстановлено')
}

// Initialize auth on mount
onMounted(async () => {
  // Apply initial scale
  applyUIScale()
  
  // Initialize Telegram WebApp
  if (telegram) {
    telegram.ready()
    telegram.expand()
  }

  // Initialize PWA installation check & banner schedule
  pwaInstall.init()
  
  // Add resize listener for responsive detection
  window.addEventListener('resize', updateDesktopState)
  
  // Listen for auth:logout events from API interceptor
  window.addEventListener('auth:logout', handleAuthLogout)
  
  // Initialize auth
  if (authStore.isAuthenticated && !authStore.initialized) {
    await authStore.initialize()
    
    // Initialize library after auth
    await libraryStore.init()
    
    // Restore player state if available (persisted queue, track, position)
    if (playerStore.hasSavedState()) {
      await playerStore.restoreState()
    }
  }
  
  // === Start network monitoring ===
  networkMonitor.startMonitoring()
  
  // === Player event listeners ===
  window.addEventListener('player:error', handlePlayerError)
  window.addEventListener('player:stall-recovered', handleStallRecovered)
  window.addEventListener('player:network-recovered', handleNetworkRecovered)
  
  // Handle unavailable tracks - show notification with helpful message
  playerStore.setOnTrackUnavailable((track, message, isLargeFile) => {
    if (isLargeFile) {
      const sizeMB = track.file_size ? (track.file_size / 1024 / 1024).toFixed(1) : '20+'
      console.warn(`[Player] Track too large for streaming: ${sizeMB} MB`)
      uiStore.toast.warning(
        'Большой файл',
        `Трек (${sizeMB} MB) слишком большой для стриминга. Используйте кнопку скачивания.`
      )
    } else {
      console.warn('[Player] Track unavailable:', message)
      // Check if it's HD format error
      if (message && (message.includes('HD') || message.includes('FLAC') || message.includes('WAV') || message.includes('высокого качества'))) {
        uiStore.toast.warning(
          'Только HD',
          'Этот трек доступен только в HD качестве. Используйте кнопку скачивания.'
        )
      } else {
        uiStore.toast.error(
          'Трек недоступен',
          message || 'Не удалось воспроизвести трек'
        )
      }
    }
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', updateDesktopState)
  window.removeEventListener('auth:logout', handleAuthLogout)
  window.removeEventListener('player:error', handlePlayerError)
  window.removeEventListener('player:stall-recovered', handleStallRecovered)
  window.removeEventListener('player:network-recovered', handleNetworkRecovered)
  networkMonitor.stopMonitoring()
  // Reset zoom on unmount
  document.body.style.zoom = '1'
})
</script>

<style>
/* App.vue layout styles — tokens are in design-system.css */

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100%;
  background: var(--c-bg-1);
  color: var(--c-text-1);
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  max-height: 100vh;
  max-height: 100dvh;
  overflow: hidden;
}

/* Desktop Layout - CSS Grid */
.app.desktop-layout {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  grid-template-rows: 1fr auto;
  grid-template-areas:
    "sidebar main"
    "player player";
  min-height: 100vh;
  height: 100vh;
  max-height: 100vh;
  overflow: hidden;
  position: relative;
}

.app.desktop-layout.has-now-playing {
  grid-template-columns: var(--sidebar-width) 1fr var(--now-playing-width);
  grid-template-areas:
    "sidebar main nowplaying"
    "player player player";
}

.app.desktop-layout :deep(.sidebar) {
  grid-area: sidebar;
  height: 100%;
}

.app.desktop-layout .main-content-wrapper {
  grid-area: main;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  min-height: 0;
}

.app.desktop-layout :deep(.now-playing-sidebar) {
  grid-area: nowplaying;
  height: 100%;
  overflow-x: hidden;
  overflow-y: auto;
}

.app.desktop-layout :deep(.desktop-player) {
  grid-area: player;
  width: 100%;
  flex-shrink: 0;
  position: sticky;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 200;
}

/* Mobile layout wrapper */
.main-content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  min-height: 0;
  position: relative;
}

/* Pull-to-refresh indicator */
.pull-to-refresh-indicator {
  position: absolute;
  top: -60px;
  left: 0;
  right: 0;
  height: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: var(--c-text-2);
  font-size: 12px;
  z-index: 10;
  pointer-events: none;
  transition: none;
  will-change: transform;
}

.ptr-spinner {
  width: 24px;
  height: 24px;
  color: var(--c-text-2);
  transition: color 0.15s;
}

.ptr-spinner.ready {
  color: var(--c-accent);
}

.ptr-spinner.active {
  color: var(--c-accent);
  animation: spin 0.8s linear infinite;
}

.ptr-text {
  font-size: 11px;
  opacity: 0.7;
}

/* Desktop: content padding */
.app.desktop-layout .main-content {
  padding-bottom: 20px;
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
  border: 3px solid var(--c-bg-4);
  border-top-color: var(--c-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Desktop adjustments */
@media (min-width: 1024px) {
  .app.desktop-layout .main-content {
    padding: 0 24px 20px;
  }
  
  .app.desktop-layout :deep(.track-item) {
    border-radius: 8px;
    margin-bottom: 2px;
  }
  
  .app.desktop-layout :deep(.track-item:hover) {
    background: rgba(255, 255, 255, 0.1);
  }
}

@media (min-width: 1440px) {
  .app.desktop-layout .main-content {
    padding: 0 40px 20px;
    max-width: 1600px;
  }
}
</style>
