import axios from 'axios'

// Use relative path for production, env variable for development
const API_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
})

// Add Telegram init data to all requests
api.interceptors.request.use((config) => {
  const tg = window.Telegram?.WebApp
  if (tg?.initData) {
    config.headers['X-Telegram-Init-Data'] = tg.initData
  }
  return config
})

// Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default api

// Auth
export const authApi = {
  validate: () => api.post('/auth/validate'),
  me: () => api.get('/auth/me'),
}

// Tracks
export const tracksApi = {
  // My library
  getAll: (params = {}) => api.get('/tracks', { params }),
  getOne: (id) => api.get(`/tracks/${id}`),
  update: (id, data) => api.put(`/tracks/${id}`, data),
  delete: (id) => api.delete(`/tracks/${id}`),
  getArtists: (scope = 'library') => api.get('/tracks/artists', { params: { scope } }),
  getArtistImage: (artistName) => api.get(`/tracks/artist-image/${encodeURIComponent(artistName)}`),
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
  create: (data) => api.post('/playlists', data),
  update: (id, data) => api.put(`/playlists/${id}`, data),
  delete: (id) => api.delete(`/playlists/${id}`),
  addTrack: (playlistId, trackId) => api.post(`/playlists/${playlistId}/tracks`, { track_id: trackId }),
  removeTrack: (playlistId, trackId) => api.delete(`/playlists/${playlistId}/tracks/${trackId}`),
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
