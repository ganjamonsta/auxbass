import { createRouter, createWebHistory } from 'vue-router'

// Views
import LibraryView from '@/views/LibraryView.vue'
import AlbumsView from '@/views/AlbumsView.vue'
import ArtistsView from '@/views/ArtistsView.vue'
import PlaylistsView from '@/views/PlaylistsView.vue'
import CollectionsView from '@/views/CollectionsView.vue'
import FriendsView from '@/views/FriendsView.vue'
import AlbumDetailView from '@/views/AlbumDetailView.vue'
import ArtistDetailView from '@/views/ArtistDetailView.vue'
import PlaylistDetailView from '@/views/PlaylistDetailView.vue'
import LikedTracksView from '@/views/LikedTracksView.vue'
import FavoritesView from '@/views/FavoritesView.vue'
import SettingsView from '@/views/SettingsView.vue'
import LoginView from '@/views/LoginView.vue'

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
