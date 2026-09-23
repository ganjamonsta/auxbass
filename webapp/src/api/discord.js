import api from './core'

// Normalize track object for Discord API — backend expects file_id field
function normalizeTrack(track) {
  if (!track) return track
  return {
    ...track,
    // Map telegram_file_id → file_id if needed
    file_id: track.file_id || track.telegram_file_id || null,
  }
}

export const discordApi = {
  getParty: () => api.get('/discord/party'),
  getUserState: () => api.get('/discord/user-state'),
  getChannels: () => api.get('/discord/channels'),
  getInvite: () => api.get('/discord/invite'),
  connect: (channelId) => api.post('/discord/connect', { channel_id: Number(channelId) }),
  disconnect: () => api.post('/discord/disconnect'),
  play: (track, queue = null, position = 0) => api.post('/discord/play', {
    track: normalizeTrack(track),
    queue: queue ? queue.map(normalizeTrack) : null,
    position,
  }),
  pause: () => api.post('/discord/pause'),
  resume: () => api.post('/discord/resume'),
  stop: () => api.post('/discord/stop'),
  skip: () => api.post('/discord/skip'),
  seek: (position) => api.post('/discord/seek', { position }),
  setVolume: (volume) => api.post('/discord/volume', { volume }),
  addToQueue: (track) => api.post('/discord/queue', { track: normalizeTrack(track) }),
  removeFromQueue: (index) => api.delete(`/discord/queue/${index}`),
  setDjLock: (locked) => api.post('/discord/dj/lock', { locked }),
  transferDj: (targetUserId) => api.post('/discord/dj/transfer', { target_user_id: targetUserId }),
  getAccount: () => api.get('/discord/account'),
  getOAuthUrl: () => api.get('/discord/oauth/url'),
  linkAccount: (discordId, username = '', displayName = '') =>
    api.post('/discord/account', { discord_id: discordId, username, display_name: displayName }),
  unlinkAccount: () => api.delete('/discord/account'),
}
