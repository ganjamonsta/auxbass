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
  getAll: (params = {}) => api.get('/tracks', { params }),
  getOne: (id) => api.get(`/tracks/${id}`),
  update: (id, data) => api.put(`/tracks/${id}`, data),
  delete: (id) => api.delete(`/tracks/${id}`),
  getArtists: () => api.get('/tracks/artists'),
  getArtistImage: (artistName) => api.get(`/tracks/artist-image/${encodeURIComponent(artistName)}`),
  getGenres: () => api.get('/tracks/genres'),
  getEnrichmentStatus: () => api.get('/tracks/enrichment/status'),
  getHistory: (limit = 50) => api.get('/tracks/history', { params: { limit } }),
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
  recordPlay: (trackId) => api.post(`/player/play/${trackId}`),
}
