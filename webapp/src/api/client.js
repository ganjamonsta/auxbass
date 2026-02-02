import axios from 'axios'
import apiCache from '../utils/apiCache'

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
  
  // Check cache for GET requests (unless explicitly bypassed)
  if (config.method === 'get' && !config.bypassCache) {
    const cacheKey = apiCache.generateKey(config.url, config.params)
    const cachedResponse = apiCache.get(cacheKey)
    
    if (cachedResponse) {
      // Return cached response (cancel actual request)
      config.adapter = () => Promise.resolve({
        data: cachedResponse,
        status: 200,
        statusText: 'OK (cached)',
        headers: {},
        config,
        request: {}
      })
    }
  }
  
  return config
})

// Handle errors (including 401 for expired tokens)
api.interceptors.response.use(
  (response) => {
    // Cache successful GET responses (unless explicitly bypassed)
    if (response.config.method === 'get' && !response.config.bypassCache && response.status === 200) {
      const cacheKey = apiCache.generateKey(response.config.url, response.config.params)
      apiCache.set(cacheKey, response.data)
    }
    
    return response
  },
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

// Helper to create cacheable API method
const cacheable = (method) => method

// Helper to create non-cacheable API method (mutations)
const nonCacheable = (method, invalidateType) => {
  return (...args) => {
    return method(...args).then(response => {
      // Invalidate related caches after mutation
      if (invalidateType) {
        apiCache.invalidateRelated(invalidateType, args[0])
      }
      return response
    })
  }
}

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
  // My library (cached)
  getAll: cacheable((params = {}) => api.get('/tracks', { params })),
  // Bypass cache when sort_by is 'random' to get fresh shuffled order each time
  getAllIds: (params = {}) => api.get('/tracks/ids', { 
    params, 
    bypassCache: params.sort_by === 'random' 
  }),
  getOne: cacheable((id) => api.get(`/tracks/${id}`)),
  update: nonCacheable((id, data) => api.put(`/tracks/${id}`, data), 'track'),
  delete: nonCacheable((id) => api.delete(`/tracks/${id}`), 'track'),
  getArtists: cacheable((scope = 'library') => api.get('/tracks/artists', { params: { scope } })),
  getArtistImage: cacheable((artistName) => api.get(`/tracks/artist-image/${encodeURIComponent(artistName)}`)),
  getArtistDetail: cacheable((artistName, scope = 'library') => api.get(`/tracks/artist/${encodeURIComponent(artistName)}`, { params: { scope } })),
  // Bypass cache when sort_by is 'random' to get fresh shuffled order each time
  getArtistIds: (artistName, params = {}) => api.get(`/tracks/artist/${encodeURIComponent(artistName)}/ids`, { 
    params, 
    bypassCache: params.sort_by === 'random' 
  }),
  getGenres: cacheable((scope = 'library') => api.get('/tracks/genres', { params: { scope } })),
  getEnrichmentStatus: cacheable(() => api.get('/tracks/enrichment/status')),
  getHistory: cacheable((limit = 50) => api.get('/tracks/history', { params: { limit } })),
  getLiked: cacheable(() => api.get('/tracks/liked')),
  like: nonCacheable((id) => api.post(`/tracks/${id}/like`), 'like'),
  unlike: nonCacheable((id) => api.delete(`/tracks/${id}/like`), 'like'),
  markUnavailable: nonCacheable((id) => api.post(`/tracks/${id}/mark-unavailable`), 'track'),
  getUnavailable: cacheable(() => api.get('/tracks/unavailable/list')),
  deleteAllUnavailable: nonCacheable(() => api.delete('/tracks/unavailable/all'), 'track'),
  
  // Global library (cached)
  getGlobal: cacheable((params = {}) => api.get('/tracks/global', { params })),
  getRecentUploads: cacheable((limit = 20) => api.get('/tracks/global/recent', { params: { limit } })),
  getPopular: cacheable((limit = 20) => api.get('/tracks/global/popular', { params: { limit } })),
  getGlobalStats: cacheable(() => api.get('/tracks/global/stats')),
  getTopUsers: cacheable((limit = 20) => api.get('/tracks/global/users', { params: { limit } })),
  getUserTracks: cacheable((userId, limit = 50) => api.get(`/tracks/global/users/${userId}/tracks`, { params: { limit } })),
  
  // Library management (mutations)
  addToLibrary: nonCacheable((trackId) => api.post(`/tracks/${trackId}/add-to-library`), 'track'),
  removeFromLibrary: nonCacheable((trackId) => api.delete(`/tracks/${trackId}/remove-from-library`), 'track'),
}

// Playlists
export const playlistsApi = {
  getAll: cacheable(() => api.get('/playlists')),
  getOne: cacheable((id) => api.get(`/playlists/${id}`)),
  // Bypass cache when shuffle is requested to get fresh random order
  getIds: (id, params = {}) => api.get(`/playlists/${id}/ids`, { 
    params, 
    bypassCache: params.shuffle === true 
  }),
  create: nonCacheable((data) => api.post('/playlists', data), 'playlist'),
  update: nonCacheable((id, data) => api.put(`/playlists/${id}`, data), 'playlist'),
  delete: nonCacheable((id) => api.delete(`/playlists/${id}`), 'playlist'),
  addTrack: nonCacheable((playlistId, trackId) => api.post(`/playlists/${playlistId}/tracks`, { track_id: trackId }), 'playlist'),
  removeTrack: nonCacheable((playlistId, trackId) => api.delete(`/playlists/${playlistId}/tracks/${trackId}`), 'playlist'),
}

// Artists
export const artistsApi = {
  getAll: cacheable((params = {}) => api.get('/artists', { params })),
  getGlobal: cacheable((params = {}) => api.get('/artists/global', { params })),
  getOne: cacheable((artistName, params = {}) => api.get(`/artists/${encodeURIComponent(artistName)}`, { params })),
  getInfo: cacheable((artistName, params = {}) => api.get(`/artists/${encodeURIComponent(artistName)}/info`, { params })),
  getTracks: cacheable((artistName, params = {}) => api.get(`/artists/${encodeURIComponent(artistName)}/tracks`, { params })),
  getImage: cacheable((artistName) => api.get(`/artists/${encodeURIComponent(artistName)}/image`)),
}

// Albums
export const albumsApi = {
  getAll: cacheable((params = {}) => api.get('/albums', { params })),
  getGlobal: cacheable((params = {}) => api.get('/albums/global', { params })),
  getOne: cacheable((id) => api.get(`/albums/${id}`)),
  // Bypass cache when shuffle is requested to get fresh random order
  getIds: (id, params = {}) => api.get(`/albums/${id}/ids`, { 
    params, 
    bypassCache: params.shuffle === true 
  }),
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
