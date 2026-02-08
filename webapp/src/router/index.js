import { createRouter, createWebHistory } from 'vue-router'

// Lazy-loaded views
const LibraryView = () => import('@/views/LibraryView.vue')
const AlbumsView = () => import('@/views/AlbumsView.vue')
const ArtistsView = () => import('@/views/ArtistsView.vue')
const PlaylistsView = () => import('@/views/PlaylistsView.vue')
const CollectionsView = () => import('@/views/CollectionsView.vue')
const FriendsView = () => import('@/views/FriendsView.vue')
const AlbumDetailView = () => import('@/views/AlbumDetailView.vue')
const ArtistDetailView = () => import('@/views/ArtistDetailView.vue')
const PlaylistDetailView = () => import('@/views/PlaylistDetailView.vue')
const LikedTracksView = () => import('@/views/LikedTracksView.vue')
const FavoritesView = () => import('@/views/FavoritesView.vue')
const SettingsView = () => import('@/views/SettingsView.vue')
const LoginView = () => import('@/views/LoginView.vue')

import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'library',
    component: LibraryView,
    meta: { requiresAuth: true }
  },
  {
    path: '/collections',
    name: 'collections',
    component: CollectionsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/albums',
    name: 'albums',
    component: AlbumsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/album/:id',
    name: 'album-detail',
    component: AlbumDetailView,
    meta: { requiresAuth: true }
  },
  {
    path: '/artists',
    name: 'artists',
    component: ArtistsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/artist/:name',
    name: 'artist-detail',
    component: ArtistDetailView,
    meta: { requiresAuth: true }
  },
  {
    path: '/playlists',
    name: 'playlists',
    component: PlaylistsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/playlist/:id',
    name: 'playlist-detail',
    component: PlaylistDetailView,
    meta: { requiresAuth: true }
  },
  {
    path: '/friends',
    name: 'friends',
    component: FriendsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/liked',
    name: 'liked',
    component: LikedTracksView,
    meta: { requiresAuth: true }
  },
  {
    path: '/favorites',
    name: 'favorites',
    component: FavoritesView,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // Initialize auth on first navigation if we're authenticated or in Telegram Mini App
  if (!authStore.initialized && !authStore.loading) {
    const tg = window.Telegram?.WebApp
    const isTelegramMiniApp = !!(tg?.initData)
    const hasToken = !!localStorage.getItem('tg_player_auth_token')
    
    // Try to initialize if we have any auth credentials
    if (isTelegramMiniApp || hasToken) {
      try {
        console.log('[Router] Initializing auth in beforeEach guard')
        await authStore.initialize()
      } catch (e) {
        console.error('[Router] Auth initialization failed:', e.message)
        // Auth failed, continue to check
      }
    }
  }
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    console.log('[Router] Redirecting to login - not authenticated')
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }
  
  if (to.name === 'login' && authStore.isAuthenticated) {
    console.log('[Router] Redirecting from login to library - already authenticated')
    next({ name: 'library' })
    return
  }
  
  next()
})

export default router
