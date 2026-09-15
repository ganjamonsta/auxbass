import api, { cacheable, nonCacheable } from './core'

export const tracksApi = {
  // My library (cached by default, bypasses cache when refresh/bypassCache requested)
  getAll: (params = {}, options = {}) => {
    const bypassCache = !!params.refresh || !!params.bypassCache || !!options.bypassCache
    return api.get('/tracks', {
      params,
      bypassCache,
      ...options
    })
  },
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
  getCoverSuggestions: (id, query = null) => api.get(`/tracks/${id}/cover-suggestions`, { params: query ? { query } : {} }),
  setCover: nonCacheable((id, coverUrl) => api.post(`/tracks/${id}/set-cover`, { cover_url: coverUrl }), 'track'),
  uploadCover: nonCacheable((id, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/tracks/${id}/cover`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }, 'track'),
  deleteCover: nonCacheable((id) => api.delete(`/tracks/${id}/cover`), 'track'),
  getArtists: cacheable((scope = 'library') => api.get('/artists', { params: { scope, limit: 500 } })),
  getArtistImage: cacheable((artistName) => api.get(`/artists/${encodeURIComponent(artistName)}/image`)),
  getArtistDetail: cacheable((artistName, scope = 'library') => api.get(`/artists/${encodeURIComponent(artistName)}`, { params: { scope } })),
  // Bypass cache when shuffle is requested to get fresh shuffled order each time
  // Add timestamp to ensure truly random results on every call
  getArtistIds: (artistName, params = {}) => api.get(`/artists/${encodeURIComponent(artistName)}/ids`, { 
    params: params.shuffle 
      ? { ...params, _t: Date.now() }  // Add timestamp to bypass any caching
      : params, 
    bypassCache: !!params.shuffle 
  }),
  getGenres: cacheable((scope = 'library') => api.get('/tracks/genres', { params: { scope } })),
  getTags: cacheable((scope = 'library', limit = 50) => api.get('/tracks/tags', { params: { scope, limit } })),
  getHistory: cacheable((limit = 50) => api.get('/tracks/history', { params: { limit } })),
  getLiked: cacheable(() => api.get('/tracks/liked')),
  like: nonCacheable((id) => api.post(`/tracks/${id}/like`), 'like'),
  unlike: nonCacheable((id) => api.delete(`/tracks/${id}/like`), 'like'),
  dislike: nonCacheable((id) => api.post(`/tracks/${id}/dislike`), 'like'),
  undislike: nonCacheable((id) => api.delete(`/tracks/${id}/dislike`), 'like'),
  markUnavailable: nonCacheable((id) => api.post(`/tracks/${id}/mark-unavailable`), 'track'),
  normalizeMetadata: nonCacheable((id) => api.post(`/tracks/${id}/normalize-metadata`), 'track'),
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
  reSource: nonCacheable((id, customUrl = null) => api.post(`/tracks/${id}/re-source`, null, { params: customUrl ? { custom_url: customUrl } : {} }), 'track'),

  // Tags (user-generated with voting)
  getTrackTags: (trackId) => api.get(`/tracks/${trackId}/tags`),
  addTag: nonCacheable((trackId, tag) => api.post(`/tracks/${trackId}/tags`, { tag }), 'tag'),
  voteTag: nonCacheable((trackId, tagId) => api.post(`/tracks/${trackId}/tags/${tagId}/vote`), 'tag'),
  unvoteTag: nonCacheable((trackId, tagId) => api.delete(`/tracks/${trackId}/tags/${tagId}/vote`), 'tag'),
  deleteTag: nonCacheable((trackId, tagId) => api.delete(`/tracks/${trackId}/tags/${tagId}`), 'tag'),

  // Lyrics
  getLyrics: (trackId, forceRefresh = false) => api.get(`/tracks/${trackId}/lyrics`, { params: { force_refresh: forceRefresh } }),
  updateLyrics: nonCacheable((trackId, data) => api.put(`/tracks/${trackId}/lyrics`, data), 'track'),
  updateLyricsOffset: nonCacheable((trackId, offsetMs) => api.post(`/tracks/${trackId}/lyrics/offset`, { offset_ms: offsetMs }), 'track'),
  searchLyrics: (trackId, query) => api.post(`/tracks/${trackId}/lyrics/search`, null, { params: { query } }),
}
