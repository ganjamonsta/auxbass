import { createRouter, createWebHistory } from 'vue-router'

// Lazy-loaded views
const LibraryView = () => import('@/views/LibraryView.vue')
const CollectionsView = () => import('@/views/CollectionsView.vue')
const FriendsView = () => import('@/views/FriendsView.vue')
const AlbumDetailView = () => import('@/views/AlbumDetailView.vue')
const ArtistDetailView = () => import('@/views/ArtistDetailView.vue')
const PlaylistDetailView = () => import('@/views/PlaylistDetailView.vue')
const LikedTracksView = () => import('@/views/LikedTracksView.vue')
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
    path: '/album/:id',
    name: 'album-detail',
    component: AlbumDetailView,
    meta: { requiresAuth: true }
  },
  {
    path: '/artist/:name',
    name: 'artist-detail',
    component: ArtistDetailView,
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
    path: '/settings',
    name: 'settings',
    component: SettingsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView
  },
  // Legacy redirects
  { path: '/favorites', redirect: '/liked' },
  { path: '/albums', redirect: '/collections' },
  { path: '/playlists', redirect: '/collections' },
  { path: '/artists', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // Initialize auth on first navigation
  if (!authStore.initialized && authStore.isAuthenticated) {
    try {
      await authStore.initialize()
    } catch (e) {
      // Auth failed, continue to check
    }
  }
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }
  
  if (to.name === 'login' && authStore.isAuthenticated) {
    next({ name: 'library' })
    return
  }
  
  next()
})

export default router
