import api, { cacheable } from './core'

export const artistsApi = {
  getAll: cacheable((params = {}) => api.get('/artists', { params })),
  getGlobal: cacheable((params = {}) => api.get('/artists/global', { params })),
  getOne: cacheable((artistName, params = {}) => api.get(`/artists/${encodeURIComponent(artistName)}`, { params })),
  getInfo: cacheable((artistName, params = {}) => api.get(`/artists/${encodeURIComponent(artistName)}/info`, { params })),
  getTracks: cacheable((artistName, params = {}) => api.get(`/artists/${encodeURIComponent(artistName)}/tracks`, { params })),
  getImage: cacheable((artistName) => api.get(`/artists/${encodeURIComponent(artistName)}/image`)),
}
