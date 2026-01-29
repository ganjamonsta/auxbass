import axios from 'axios'

// Use relative path for production, env variable for development
const API_URL = import.meta.env.VITE_API_URL || '/api'

// ============== Auth Token Storage ==============
const AUTH_TOKEN_KEY = 'tg_player_auth_token'
const AUTH_USER_KEY = 'tg_player_auth_user'

export const authStorage = {
  getToken: () => localStorage.getItem(AUTH_TOKEN_KEY),
  setToken: (token) => localStorage.setItem(AUTH_TOKEN_KEY, token),
  removeToken: () => localStorage.removeItem(AUTH_TOKEN_KEY),
  
  getUser: () => {
    try {
      const user = localStorage.getItem(AUTH_USER_KEY)
      return user ? JSON.parse(user) : null
    } catch {
      return null
    }
  },
  setUser: (user) => localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user)),
  removeUser: () => localStorage.removeItem(AUTH_USER_KEY),
  
  clear: () => {
    localStorage.removeItem(AUTH_TOKEN_KEY)
    localStorage.removeItem(AUTH_USER_KEY)
  },
  
  isAuthenticated: () => {
    // Check if we have Telegram WebApp auth OR JWT token
    const tg = window.Telegram?.WebApp
    return !!(tg?.initData) || !!localStorage.getItem(AUTH_TOKEN_KEY)
  },
  
  isTelegramWebApp: () => {
    const tg = window.Telegram?.WebApp
    return !!(tg?.initData)
  }
}

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
})

// Add auth headers to all requests
api.interceptors.request.use((config) => {
  const tg = window.Telegram?.WebApp
  
  // Prefer Telegram WebApp auth if available
  if (tg?.initData) {
    config.headers['X-Telegram-Init-Data'] = tg.initData
  } else {
    // Fall back to JWT token for browser auth
    const token = authStorage.getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
  }
  
  return config
})

// Handle errors (including 401 for expired tokens)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // If 401 and we're using JWT, clear the token
    if (error.response?.status === 401 && !window.Telegram?.WebApp?.initData) {
      authStorage.clear()
      // Dispatch event for UI to handle
      window.dispatchEvent(new CustomEvent('auth:logout'))
    }
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default api

// Auth
export const authApi = {
  validate: () => api.post('/auth/validate'),
  me: () => api.get('/auth/me'),
  status: () => api.get('/auth/status'),  // Get user status with channel info
  getConfig: () => api.get('/auth/config'),
  verifyCode: (data) => api.post('/auth/verify-code', data),
  refresh: () => api.post('/auth/refresh'),
}

// Tracks
export const tracksApi = {
  // My library
  getAll: (params = {}) => api.get('/tracks', { params }),
  getAllIds: (params = {}) => api.get('/tracks/ids', { params }),
  getOne: (id) => api.get(`/tracks/${id}`),
  update: (id, data) => api.put(`/tracks/${id}`, data),
  delete: (id) => api.delete(`/tracks/${id}`),
  getArtists: (scope = 'library') => api.get('/tracks/artists', { params: { scope } }),
  getArtistImage: (artistName) => api.get(`/tracks/artist-image/${encodeURIComponent(artistName)}`),
  getArtistDetail: (artistName, scope = 'library') => api.get(`/tracks/artist/${encodeURIComponent(artistName)}`, { params: { scope } }),
  getArtistIds: (artistName, params = {}) => api.get(`/tracks/artist/${encodeURIComponent(artistName)}/ids`, { params }),
  getGenres: (scope = 'library') => api.get('/tracks/genres', { params: { scope } }),
  getEnrichmentStatus: () => api.get('/tracks/enrichment/status'),
  getHistory: (limit = 50) => api.get('/tracks/history', { params: { limit } }),
  getLiked: () => api.get('/tracks/liked'),
  like: (id) => api.post(`/tracks/${id}/like`),
  unlike: (id) => api.delete(`/tracks/${id}/like`),
  markUnavailable: (id) => api.post(`/tracks/${id}/mark-unavailable`),
  getUnavailable: () => api.get('/tracks/unavailable/list'),
  deleteAllUnavailable: () => api.delete('/tracks/unavailable/all'),
  
  // Global library
  getGlobal: (params = {}) => api.get('/tracks/global', { params }),
  getRecentUploads: (limit = 20) => api.get('/tracks/global/recent', { params: { limit } }),
  getPopular: (limit = 20) => api.get('/tracks/global/popular', { params: { limit } }),
  getGlobalStats: () => api.get('/tracks/global/stats'),
  getTopUsers: (limit = 20) => api.get('/tracks/global/users', { params: { limit } }),
  getUserTracks: (userId, limit = 50) => api.get(`/tracks/global/users/${userId}/tracks`, { params: { limit } }),
  
  // Library management
  addToLibrary: (trackId) => api.post(`/tracks/${trackId}/add-to-library`),
  removeFromLibrary: (trackId) => api.delete(`/tracks/${trackId}/remove-from-library`),
}

// Playlists
export const playlistsApi = {
  getAll: () => api.get('/playlists'),
  getOne: (id) => api.get(`/playlists/${id}`),
  getIds: (id, params = {}) => api.get(`/playlists/${id}/ids`, { params }),
  create: (data) => api.post('/playlists', data),
  update: (id, data) => api.put(`/playlists/${id}`, data),
  delete: (id) => api.delete(`/playlists/${id}`),
  addTrack: (playlistId, trackId) => api.post(`/playlists/${playlistId}/tracks`, { track_id: trackId }),
  removeTrack: (playlistId, trackId) => api.delete(`/playlists/${playlistId}/tracks/${trackId}`),
}

// Artists
export const artistsApi = {
  getAll: (params = {}) => api.get('/artists', { params }),
  getGlobal: (params = {}) => api.get('/artists/global', { params }),
  getOne: (artistName) => api.get(`/artists/${encodeURIComponent(artistName)}`),
  getImage: (artistName) => api.get(`/artists/${encodeURIComponent(artistName)}/image`),
}

// Albums
export const albumsApi = {
  getAll: (params = {}) => api.get('/albums', { params }),
  getGlobal: (params = {}) => api.get('/albums/global', { params }),
  getOne: (id) => api.get(`/albums/${id}`),
  getIds: (id, params = {}) => api.get(`/albums/${id}/ids`, { params }),
}

// Player
export const playerApi = {
  getStreamUrl: (trackId) => api.get(`/player/stream/${trackId}`),
  getBatchUrls: (trackIds) => api.post('/player/stream/batch', trackIds),
  prefetch: (trackIds) => api.post('/player/prefetch', trackIds),
  recordPlay: (trackId) => api.post(`/player/play/${trackId}`),
  download: (trackId) => api.post(`/player/download/${trackId}`),
  downloadPlaylist: (trackIds, playlistName) => api.post('/player/download-playlist', { track_ids: trackIds, playlist_name: playlistName }),
}

// Social
export const socialApi = {
  searchFriends: (search, perPage = 30) => api.get('/social/friends/search', { params: { search, per_page: perPage } }),
}
