import api, { authStorage, nonCacheable } from './core'

export { authStorage }

export const authApi = {
  validate: () => api.post('/auth/validate'),
  me: () => api.get('/auth/me'),
  status: () => api.get('/auth/status'),  // Get user status with channel info
  verifyChannel: () => api.post('/auth/channel/verify'), // Actively check channel permissions
  getConfig: () => api.get('/auth/config'),
  verifyCode: (data) => api.post('/auth/verify-code', data),
  refresh: () => api.post('/auth/refresh'),
  updateProfile: nonCacheable((data) => api.put('/auth/profile', data), 'user'),
  uploadAvatar: nonCacheable((formData) => api.post('/auth/profile/avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }), 'user'),
  deleteAvatar: nonCacheable(() => api.delete('/auth/profile/avatar'), 'user'),
  getPrivacy: () => api.get('/auth/privacy'),
  updatePrivacy: nonCacheable((data) => api.put('/auth/privacy', data), 'user'),
}
