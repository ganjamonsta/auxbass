import api, { cacheable } from './core'

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
