import axios from 'axios'
import apiCache from '../utils/apiCache'
import { useNetworkMonitor } from '../composables/useNetworkMonitor'

// Lazy reference to network monitor (initialized on first use)
let _networkMonitor = null
const getNetworkMonitor = () => {
  if (!_networkMonitor) _networkMonitor = useNetworkMonitor()
  return _networkMonitor
}

// ============== Retry Configuration ==============
const RETRY_CONFIG = {
  maxRetries: 1,           // Одна повторная попытка
  retryDelay: 1000,        // Задержка перед retry (мс)
  retryableStatuses: [502, 503, 504, 0], // 0 = network error
  retryableMethods: ['get', 'head', 'options'], // Только идемпотентные
}

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
    
    // Notify network monitor of successful request
    try { getNetworkMonitor().recordSuccessfulRequest() } catch {}
    
    return response
  },
  async (error) => {
    const config = error.config
    
    // Notify network monitor of failed request
    try { getNetworkMonitor().recordFailedRequest(error) } catch {}
    
    // === Retry logic for transient errors ===
    if (config && !config._retried) {
      const status = error.response?.status || 0
      const isRetryable = RETRY_CONFIG.retryableStatuses.includes(status)
      const isIdempotent = RETRY_CONFIG.retryableMethods.includes(config.method)
      const isNetworkError = !error.response && error.code !== 'ERR_CANCELED'
      
      if ((isRetryable && isIdempotent) || (isNetworkError && isIdempotent)) {
        config._retried = true
        console.warn(`[API Retry] Retrying ${config.method?.toUpperCase()} ${config.url} after ${status || 'network'} error`)
        
        await new Promise(resolve => setTimeout(resolve, RETRY_CONFIG.retryDelay))
        return api(config)
      }
    }
    
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
  // Add timestamp to ensure truly random results on every call
  getAllIds: (params = {}) => api.get('/tracks/ids', { 
    params: params.sort_by === 'random' 
      ? { ...params, _t: Date.now() }  // Add timestamp to bypass any caching
      : params, 
    bypassCache: params.sort_by === 'random' 
  }),
  getOne: cacheable((id) => api.get(`/tracks/${id}`)),
  update: nonCacheable((id, data) => api.put(`/tracks/${id}`, data), 'track'),
  delete: nonCacheable((id) => api.delete(`/tracks/${id}`), 'track'),
  getArtists: cacheable((scope = 'library') => api.get('/artists', { params: { scope, limit: 500 } })),
  getArtistImage: cacheable((artistName) => api.get(`/artists/${encodeURIComponent(artistName)}/image`)),
  getArtistDetail: cacheable((artistName, scope = 'library') => api.get(`/artists/${encodeURIComponent(artistName)}`, { params: { scope } })),
  // Bypass cache when sort_by is 'random' to get fresh shuffled order each time
  // Add timestamp to ensure truly random results on every call
  getArtistIds: (artistName, params = {}) => api.get(`/artists/${encodeURIComponent(artistName)}/ids`, { 
    params: params.sort_by === 'random' 
      ? { ...params, _t: Date.now() }  // Add timestamp to bypass any caching
      : params, 
    bypassCache: params.sort_by === 'random' 
  }),
  getGenres: cacheable((scope = 'library') => api.get('/tracks/genres', { params: { scope } })),
  getTags: cacheable((scope = 'library', limit = 50) => api.get('/tracks/tags', { params: { scope, limit } })),
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

  // Tags (user-generated with voting)
  getTrackTags: (trackId) => api.get(`/tracks/${trackId}/tags`),
  addTag: nonCacheable((trackId, tag) => api.post(`/tracks/${trackId}/tags`, { tag }), 'tag'),
  voteTag: nonCacheable((trackId, tagId) => api.post(`/tracks/${trackId}/tags/${tagId}/vote`), 'tag'),
  unvoteTag: nonCacheable((trackId, tagId) => api.delete(`/tracks/${trackId}/tags/${tagId}/vote`), 'tag'),
  deleteTag: nonCacheable((trackId, tagId) => api.delete(`/tracks/${trackId}/tags/${tagId}`), 'tag'),
}

// Playlists
export const playlistsApi = {
  getAll: cacheable((params = {}) => api.get('/playlists', { params })),
  getGlobal: cacheable((params = {}) => api.get('/playlists/global', { params })),
  getManageAll: cacheable(() => api.get('/playlists/manage/all')),
  getOne: cacheable((id) => api.get(`/playlists/${id}`)),
  // Bypass cache when shuffle is requested to get fresh random order
  // Add timestamp to ensure truly random results on every call
  getIds: (id, params = {}) => api.get(`/playlists/${id}/ids`, { 
    params: params.shuffle 
      ? { ...params, _t: Date.now() }  // Add timestamp to bypass any caching
      : params, 
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
  // Add timestamp to ensure truly random results on every call
  getIds: (id, params = {}) => api.get(`/albums/${id}/ids`, { 
    params: params.shuffle 
      ? { ...params, _t: Date.now() }  // Add timestamp to bypass any caching
      : params, 
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
  getFollowing: () => api.get('/social/following'),
  getFollowers: () => api.get('/social/followers'),
  searchUsers: (query, page = 1, perPage = 30) => api.get('/social/search', { params: { query, page, per_page: perPage } }),
  follow: (userId) => api.post('/social/follow', { user_id: userId }),
  unfollow: (userId) => api.post('/social/unfollow', { user_id: userId }),
  getUserLibrary: (userId, params = {}) => api.get(`/social/user/${userId}/library`, { params }),
  getUserAlbums: (userId, params = {}) => api.get(`/social/user/${userId}/albums`, { params }),
  getUser: (userId) => api.get(`/social/user/${userId}`),
}
