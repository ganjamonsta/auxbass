import api from './core'

export const playerApi = {
  getStreamUrl: (trackId) => api.get(`/player/stream/${trackId}`),
  getBatchUrls: (trackIds) => api.post('/player/stream/batch', trackIds),
  prefetch: (trackIds) => api.post('/player/prefetch', trackIds),
  recordPlay: (trackId) => api.post(`/player/play/${trackId}`),
  download: (trackId) => api.post(`/player/download/${trackId}`),
  downloadPlaylist: (trackIds, playlistName) => api.post('/player/download-playlist', { track_ids: trackIds, playlist_name: playlistName }),
}
