import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '@/views/HomeView.vue'

// Lazy-loaded secondary views
const LibraryView = () => import('@/views/LibraryView.vue')
const SearchView = () => import('@/views/SearchView.vue')
const FriendsView = () => import('@/views/FriendsView.vue')
const AlbumDetailView = () => import('@/views/AlbumDetailView.vue')
const ArtistDetailView = () => import('@/views/ArtistDetailView.vue')
const PlaylistDetailView = () => import('@/views/PlaylistDetailView.vue')
const DownloadedTracksView = () => import('@/views/DownloadedTracksView.vue')
const LikedTracksView = () => import('@/views/LikedTracksView.vue')
const SettingsView = () => import('@/views/SettingsView.vue')
const LoginView = () => import('@/views/LoginView.vue')
const UserProfileView = () => import('@/views/UserProfileView.vue')

import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { requiresAuth: true }
  },
  {
    path: '/library',
    name: 'library',
    component: LibraryView,
    meta: { requiresAuth: true }
  },
  {
    path: '/search',
    name: 'search',
    component: SearchView,
    meta: { requiresAuth: true }
  },
  {
    path: '/downloaded',
    name: 'downloaded',
    component: DownloadedTracksView,
    meta: { requiresAuth: true }
  },
  {
    path: '/collections',
    redirect: '/library?tab=albums'
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
    path: '/user/:id',
    name: 'user-profile',
    component: UserProfileView,
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
  {
    path: '/profile',
    name: 'my-profile',
    redirect: () => {
      const authStore = useAuthStore()
      if (authStore.user?.id) {
        return `/user/${authStore.user.id}`
      }
      return '/settings'
    }
  },
  { path: '/me', redirect: '/profile' },
  // Section shortcuts & legacy redirects
  { path: '/albums', redirect: '/library?tab=albums' },
  { path: '/playlists', redirect: '/library?tab=playlists' },
  { path: '/artists', redirect: '/library?tab=artists' },
  { path: '/tracks', redirect: '/library?tab=tracks' },
  { path: '/offline', redirect: '/downloaded' },
  { path: '/favorites', redirect: '/liked' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard - non-blocking for instant UI appearance
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // Initialize auth in background without blocking initial navigation
  if (!authStore.initialized && authStore.isAuthenticated) {
    authStore.initialize().catch((e) => {
      console.warn('[Router] Background auth init failed:', e)
    })
  }
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }
  
  if (to.name === 'login' && authStore.isAuthenticated) {
    next({ name: 'home' })
    return
  }
  
  // If user is offline and navigating to tabs that strictly require live API, redirect to downloaded
  const isOffline = typeof navigator !== 'undefined' && !navigator.onLine
  if (isOffline && authStore.isAuthenticated && (to.name === 'search' || to.name === 'friends')) {
    next({ name: 'downloaded' })
    return
  }
  
  next()
})

export default router
