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
          <template #actions>
            <button
              v-if="authStore.user && !isDesktop"
              class="header-profile-btn"
              :class="{ 'has-active-imports': tasksStore.hasActiveImports }"
              @click="showProfileMenu = true"
              @contextmenu.prevent="showProfileMenu = true"
              v-longpress="() => { showProfileMenu = true }"
              :title="tasksStore.hasActiveImports ? `Импорт: ${tasksStore.overallProgress}% (открыть меню профиля)` : 'Меню профиля'"
            >
              <div class="header-avatar-badge" :class="{ 'importing': tasksStore.hasActiveImports }">
                <img v-if="authStore.userAvatarUrl" :src="authStore.userAvatarUrl" class="header-avatar-img" />
                <span v-else>{{ userInitials }}</span>
                <div v-if="tasksStore.hasActiveImports" class="header-import-spinner-ring"></div>
              </div>
              <span v-if="tasksStore.hasActiveImports" class="header-import-pill">
                {{ tasksStore.overallProgress }}%
              </span>
            </button>
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
            <keep-alive :include="['HomeView', 'LibraryView', 'LikedTracksView', 'FriendsView', 'SearchView']">
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
        :isLiked="isCurrentTrackLiked"
        @expand-player="showFullPlayer = true"
        @toggle-play="playerStore.togglePlay()"
        @next-track="playerStore.next()"
        @toggle-shuffle="playerStore.toggleShuffle()"
        @toggle-repeat="playerStore.toggleRepeat()"
        @like="handleToggleLike"
      />

      <!-- Desktop: Now Playing Sidebar -->
      <NowPlayingSidebar 
        v-if="isNowPlayingActive" 
        @goToUser="handleGoToUser"
      />

      <!-- Desktop: Bottom Player -->
      <DesktopPlayer 
        v-if="isDesktop && playerStore.currentTrack && authStore.isAuthenticated"
        @expand="showFullPlayer = true"
      />

      <!-- Full player modal - Desktop version -->
      <FullPlayerDesktop
        v-if="isDesktop"
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

      <!-- Full player modal - Mobile version -->
      <Transition name="player-slide">
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
      </Transition>
      
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

      <!-- Global Ingestion Modals (accessible from any screen) -->
      <ExportifyImportModal 
        :show="tasksStore.showExportifyModal"
        @close="tasksStore.closeExportifyModal"
        @imported="libraryStore.fetchTracks({ refresh: true })"
      />

      <ImportModal
        :show="tasksStore.showImportModal"
        @close="tasksStore.closeImportModal"
        @imported="libraryStore.fetchTracks({ refresh: true })"
      />

      <!-- Share Modal -->
      <ShareModal />

      <!-- Profile Context Menu -->
      <ProfileMenu v-model="showProfileMenu" placement="header" />
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject, watch, nextTick, defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import { useTasksStore } from '@/stores/tasks'
import { useModals } from '@/composables/useModals'
import PageHeader from '@/components/PageHeader.vue'
import ToastContainer from '@/components/ToastContainer.vue'
import { MobileFooter } from '@/components/layout'
import { useNetworkMonitor } from '@/composables/useNetworkMonitor'
import { usePullToRefresh } from '@/composables/usePullToRefresh'
import { usePwaInstall } from '@/composables/usePwaInstall'
import { Music, Disc3, User, Folder, Library } from 'lucide-vue-next'
import { tracksApi } from '@/api/client'

// Heavy and conditional components loaded asynchronously on demand
const FullPlayer = defineAsyncComponent(() => import('@/components/FullPlayer.vue'))
const FullPlayerDesktop = defineAsyncComponent(() => import('@/components/desktop/FullPlayerDesktop.vue'))
const Sidebar = defineAsyncComponent(() => import('@/components/desktop/Sidebar.vue'))
const DesktopPlayer = defineAsyncComponent(() => import('@/components/desktop/DesktopPlayer.vue'))
const NowPlayingSidebar = defineAsyncComponent(() => import('@/components/desktop/NowPlayingSidebar.vue'))
const ContextMenu = defineAsyncComponent(() => import('@/components/ContextMenu.vue'))
const ProfileMenu = defineAsyncComponent(() => import('@/components/layout/ProfileMenu.vue'))
const ShareModal = defineAsyncComponent(() => import('@/components/ShareModal.vue'))
const PwaInstallModal = defineAsyncComponent(() => import('@/components/PwaInstallModal.vue'))
const PwaInstallBanner = defineAsyncComponent(() => import('@/components/PwaInstallBanner.vue'))
const ChannelBanner = defineAsyncComponent(() => import('@/components/ChannelBanner.vue'))
const MaintenanceBanner = defineAsyncComponent(() => import('@/components/MaintenanceBanner.vue'))
const NetworkBanner = defineAsyncComponent(() => import('@/components/NetworkBanner.vue'))
const ExportifyImportModal = defineAsyncComponent(() => import('@/components/ExportifyImportModal.vue'))
const ImportModal = defineAsyncComponent(() => import('@/components/ImportModal.vue'))

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const uiStore = useUIStore()
const tasksStore = useTasksStore()
const telegram = inject('telegram')
const networkMonitor = useNetworkMonitor()
const pwaInstall = usePwaInstall()
const showProfileMenu = ref(false)

// Pull-to-refresh — bound to .main-content via scrollRef
const { scrollRef, pullDistance, isPulling, isRefreshing } = usePullToRefresh(
  () => libraryStore.refresh(),
  { telegram }
)

const { showFullPlayer } = useModals(telegram)

// Scroll to top helper for tab clicks and resets
const scrollToContentTop = () => {
  if (scrollRef.value) {
    scrollRef.value.scrollTo({ top: 0, behavior: 'smooth' })
  }
  const scrollContainers = document.querySelectorAll(
    '.main-content, .main-content-wrapper, .library-view, .collections-view, .layout-content, .virtual-track-list'
  )
  scrollContainers.forEach((el) => {
    if (el && el.scrollTop > 0) {
      el.scrollTo({ top: 0, behavior: 'smooth' })
    }
  })
  window.scrollTo({ top: 0, behavior: 'smooth' })
  if (document.documentElement) {
    document.documentElement.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const handleLibraryTabClick = (tabId) => {
  uiStore.setLibraryTab(tabId)
  nextTick(() => {
    scrollToContentTop()
  })
}

// Responsive detection & auto-collapse calculation
// Desktop layout is >= 768px, Mobile layout is < 768px
const isDesktop = ref(window.innerWidth >= 768)

const updateLayoutState = () => {
  const width = window.innerWidth
  isDesktop.value = width >= 768

  if (!isDesktop.value) {
    uiStore.closeSidebarOverlay()
    return
  }

  // Right sidebar (NowPlayingSidebar) auto-hiding on narrow screens:
  // Automatically hides if window width < 1120px
  const shouldHideRight = width < 1120
  if (uiStore.userNowPlayingPreference === null) {
    uiStore.setNowPlayingSidebar(!shouldHideRight)
  } else {
    // If screen becomes very narrow (< 960px), hide right sidebar to avoid crushing center
    if (width < 960 && uiStore.isNowPlayingSidebarVisible) {
      uiStore.setNowPlayingSidebar(false)
    }
  }

  // Left sidebar auto-collapsing:
  const hasNowPlaying = !!(playerStore.currentTrack && authStore.isAuthenticated && uiStore.isNowPlayingSidebarVisible)
  const occupiedSidebars = 280 + (hasNowPlaying ? 320 : 0)
  const centerSpace = width - occupiedSidebars
  // Tight if center space < 520px or screen width < 1000px
  const isTightLeft = centerSpace < 520 || width < 1000

  uiStore.isAutoCollapsed = isTightLeft

  // If user hasn't explicitly chosen, auto-collapse based on available space
  if (uiStore.userCollapsedPreference === null) {
    uiStore.setSidebarCollapsed(isTightLeft)
  } else if (uiStore.userCollapsedPreference === false) {
    // User explicitly pinned sidebar to layout: keep it pinned in desktop mode!
    uiStore.setSidebarCollapsed(false)
  } else {
    // User had collapsed it, but when window is stretched wide, allow it to adapt!
    if (!isTightLeft) {
      uiStore.userCollapsedPreference = null
      uiStore.setSidebarCollapsed(false)
    } else {
      uiStore.setSidebarCollapsed(true)
    }
  }
}

// Watch track changes to re-evaluate center space when NowPlayingSidebar appears/disappears
watch(() => playerStore.currentTrack, () => {
  if (isDesktop.value) {
    updateLayoutState()
  }
})

// Auto-close overlay drawer on route change
watch(() => route.path, () => {
  if (uiStore.isSidebarOverlayOpen) {
    uiStore.closeSidebarOverlay()
  }
})

// Keyboard shortcuts: Esc to close overlay, Ctrl+B / Cmd+B to toggle left sidebar, Ctrl+J to toggle right sidebar
const handleGlobalKeyDown = (e) => {
  if (e.key === 'Escape' && uiStore.isSidebarOverlayOpen) {
    uiStore.closeSidebarOverlay()
  }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b' && isDesktop.value) {
    e.preventDefault()
    uiStore.toggleSidebarCollapse()
  }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'j' && isDesktop.value && playerStore.currentTrack) {
    e.preventDefault()
    uiStore.toggleNowPlayingSidebar()
  }
}

const isNowPlayingActive = computed(() => {
  return isDesktop.value && !!playerStore.currentTrack && authStore.isAuthenticated && uiStore.isNowPlayingSidebarVisible
})

// App classes for layout
const appClasses = computed(() => ({
  'has-player': !!playerStore.currentTrack,
  'desktop-layout': isDesktop.value && authStore.isAuthenticated,
  'has-now-playing': isNowPlayingActive.value,
  'sidebar-collapsed': isDesktop.value && authStore.isAuthenticated && uiStore.isSidebarCollapsed,
  'sidebar-overlay-open': isDesktop.value && authStore.isAuthenticated && uiStore.isSidebarOverlayOpen
}))

// Computed property for like state based on libraryStore.likedTracks + currentTrack
const isCurrentTrackLiked = computed(() => {
  const track = playerStore.currentTrack
  if (!track?.id) return false
  if (libraryStore.isTrackLiked(track.id)) return true
  return track.is_liked === true
})

// Navigation visibility
const showNav = computed(() => {
  return authStore.isAuthenticated && route.name !== 'login'
})

const showHeader = computed(() => {
  // On desktop, show header only for drill-down detail pages (not main navigation pages)
  if (isDesktop.value) {
    const detailRoutes = ['album-detail', 'artist-detail', 'playlist-detail']
    return authStore.isAuthenticated && detailRoutes.includes(route.name)
  }
  // On mobile, show header for all pages except login
  const noHeaderRoutes = ['login']
  return authStore.isAuthenticated && !noHeaderRoutes.includes(route.name)
})

const showBackButton = computed(() => {
  if (route.name === 'search' && (route.query.tab || route.query.mode)) {
    return true
  }
  // Main navigation tabs do not need a back button
  const mainNavRoutes = ['home', 'library', 'search', 'friends', 'liked', 'settings']
  return !mainNavRoutes.includes(route.name)
})

const pageTitle = computed(() => {
  if (route.name === 'home') {
    return 'Главная'
  }
  if (route.name === 'search') {
    if (route.query.tab === 'soundcloud') {
      return route.query.mode === 'likes' ? 'SoundCloud • Лайки' : 'SoundCloud'
    }
    if (route.query.tab === 'spotify') {
      return route.query.mode === 'likes' ? 'Spotify • Лайки' : (route.query.mode === 'exportify' ? 'Spotify • Exportify' : 'Spotify')
    }
    return 'Поиск'
  }
  // Для страницы библиотеки заголовок стабилен — «Медиатека»
  if (route.name === 'library') {
    return 'Медиатека'
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
    'user-profile': 'Профиль',
    settings: 'Настройки',
    liked: 'Любимое',
    downloaded: 'Скачанное',
    'my-profile': 'Профиль',
  }
  return titles[route.name] || ''
})

const libraryIcon = computed(() => Library)

const userInitials = computed(() => {
  const name = authStore.userDisplayName
  if (name) return name.charAt(0).toUpperCase()
  const u = authStore.user
  if (!u) return '?'
  if (u.first_name) return u.first_name.charAt(0).toUpperCase()
  if (u.username) return u.username.charAt(0).toUpperCase()
  return '?'
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
  if (route.name === 'library' && uiStore.libraryTab !== 'overview') {
    uiStore.setLibraryTab('overview')
    router.replace({ path: '/library', query: {} })
    return
  }
  if (route.name === 'search' && (route.query.tab || route.query.mode)) {
    if (window.history.length > 1) {
      router.back()
    } else {
      router.replace({ path: '/search', query: {} })
    }
    return
  }
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}

// Toggle like for current track
const handleToggleLike = async () => {
  if (playerStore.currentTrack?.id) {
    const current = isCurrentTrackLiked.value
    await libraryStore.toggleLike(playerStore.currentTrack.id, current)
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

// Apply UI scale to documentElement (root)
const applyUIScale = () => {
  const scale = Number(playerStore.uiScale) || 1.0
  // Clear any residual zoom on body
  document.body.style.zoom = ''
  // Apply zoom to documentElement for full-viewport scaling without gaps or overflow clipping
  document.documentElement.style.zoom = scale
  document.documentElement.style.setProperty('--ui-scale', String(scale))
  updateDesktopState()
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

  // Deep linking helper
  const handleStartParams = async () => {
    try {
      const urlParams = new URLSearchParams(window.location.search)
      const startParam = 
        telegram?.initDataUnsafe?.start_param || 
        window.Telegram?.WebApp?.initDataUnsafe?.start_param || 
        urlParams.get('startapp') || 
        urlParams.get('tgWebAppStartParam')
      
      if (!startParam) return

      console.log('[DeepLink] Processing start_param:', startParam)

      if (startParam.startsWith('user_')) {
        const uid = startParam.replace('user_', '')
        if (uid) {
          router.push(`/user/${uid}`)
        }
      } else if (startParam.startsWith('playlist_')) {
        const pid = startParam.replace('playlist_', '')
        if (pid) {
          router.push(`/playlist/${pid}`)
        }
      } else if (startParam.startsWith('album_')) {
        const aid = startParam.replace('album_', '')
        if (aid) {
          router.push(`/album/${aid}`)
        }
      } else if (startParam.startsWith('track_')) {
        const tid = Number(startParam.replace('track_', ''))
        if (tid) {
          try {
            const resp = await tracksApi.getOne(tid)
            if (resp.data) {
              await playerStore.play(resp.data)
            }
          } catch (e) {
            console.error('[DeepLink] Failed to load track:', e)
          }
        }
      }
    } catch (err) {
      console.error('[DeepLink] Error handling start parameter:', err)
    }
  }
  
  // Initialize Telegram WebApp
  if (telegram) {
    telegram.ready()
    telegram.expand()
  }

  // Initialize PWA installation check & banner schedule
  pwaInstall.init()
  
  // Add resize & keyboard listeners for responsive detection and shortcuts
  window.addEventListener('resize', updateLayoutState)
  window.addEventListener('keydown', handleGlobalKeyDown)
  updateLayoutState()
  
  // Listen for auth:logout events from API interceptor
  window.addEventListener('auth:logout', handleAuthLogout)
  
  // Initialize auth if not already initialized
  if (authStore.isAuthenticated && !authStore.initialized) {
    await authStore.initialize()
  }

  // Restore player state if available (persisted queue, track, position) without blocking UI
  if (playerStore.hasSavedState() && !playerStore.currentTrack && !playerStore.isPlaying) {
    playerStore.restoreState()
  }

  // Handle deep link / start_param navigation
  await handleStartParams()
  
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
  window.removeEventListener('resize', updateLayoutState)
  window.removeEventListener('keydown', handleGlobalKeyDown)
  window.removeEventListener('auth:logout', handleAuthLogout)
  window.removeEventListener('player:error', handlePlayerError)
  window.removeEventListener('player:stall-recovered', handleStallRecovered)
  window.removeEventListener('player:network-recovered', handleNetworkRecovered)
  networkMonitor.stopMonitoring()
  // Reset zoom on unmount
  document.body.style.zoom = ''
  document.documentElement.style.zoom = ''
  document.documentElement.style.removeProperty('--ui-scale')
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
  width: 100%;
  background: var(--c-bg-1);
  color: var(--c-text-1);
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow: hidden;
}

.app {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  max-height: 100%;
  min-height: 100%;
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
  height: 100%;
  min-height: 100%;
  max-height: 100%;
  width: 100%;
  overflow: hidden;
  position: relative;
  transition: grid-template-columns 0.24s cubic-bezier(0.16, 1, 0.3, 1);
}

.app.desktop-layout.sidebar-collapsed {
  --sidebar-width: var(--sidebar-collapsed-width, 72px);
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
  min-width: 0;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  min-height: 0;
  min-width: 0;
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
  height: 100%;
  min-height: 100%;
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
@media (min-width: 768px) {
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

/* Full player mobile slide transition */
.player-slide-enter-active {
  transition: transform 0.35s cubic-bezier(0.32, 0.72, 0, 1), opacity 0.25s ease;
}

.player-slide-leave-active {
  transition: transform 0.28s cubic-bezier(0.32, 0.72, 0, 1), opacity 0.2s ease;
}

.player-slide-enter-from,
.player-slide-leave-to {
  transform: translateY(100%);
  opacity: 0.6;
}

.player-slide-enter-to,
.player-slide-leave-from {
  transform: translateY(0);
  opacity: 1;
}

@media (min-width: 1440px) {
  .app.desktop-layout .main-content {
    padding: 0 40px 20px;
    max-width: 1600px;
  }
}

.header-profile-btn {
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.header-avatar-badge {
  position: relative;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--c-accent), #8b5cf6);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
  transition: transform 0.15s ease;
  overflow: hidden;
}

.header-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.header-avatar-badge.importing {
  box-shadow: 0 0 10px rgba(29, 185, 84, 0.4);
}

.header-import-spinner-ring {
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 2px solid transparent;
  border-top-color: var(--c-accent, #1db954);
  border-right-color: #38bdf8;
  animation: header-avatar-spin 1.2s linear infinite;
  pointer-events: none;
}

@keyframes header-avatar-spin {
  to { transform: rotate(360deg); }
}

.header-import-pill {
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  background: rgba(29, 185, 84, 0.2);
  border: 1px solid rgba(29, 185, 84, 0.4);
  padding: 2px 7px;
  border-radius: 10px;
  animation: pill-pulse 2s ease-in-out infinite;
}

@keyframes pill-pulse {
  0%, 100% { opacity: 0.9; }
  50% { opacity: 0.6; }
}

.header-profile-btn:hover .header-avatar-badge {
  transform: scale(1.06);
}
</style>
