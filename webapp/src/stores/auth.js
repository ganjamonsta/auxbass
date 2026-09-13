import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api, { authStorage, authApi } from '@/api/client'
import apiCache from '@/utils/apiCache'

const CHANNEL_STATUS_KEY = 'tg_player_channel_status'

const loadCachedChannelStatus = () => {
  try {
    const raw = localStorage.getItem(CHANNEL_STATUS_KEY)
    if (raw) return JSON.parse(raw)
  } catch (_) {}
  return { hasChannel: false, canSave: false, channelInfo: null }
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(authStorage.getUser())
  const loading = ref(false)
  const initialized = ref(false)
  const error = ref(null)
  
  // Channel/Premium status
  const cachedStatus = loadCachedChannelStatus()
  const hasChannel = ref(cachedStatus.hasChannel)
  const canSave = ref(cachedStatus.canSave)
  const channelInfo = ref(cachedStatus.channelInfo)
  const showChannelBanner = ref(false)  // Show banner when user tries premium action
  
  // App config
  const appName = ref('TG Player')  // Default, will be overridden by bot_username
  const botUsername = ref('')

  // Getters
  const isAuthenticated = computed(() => authStorage.isAuthenticated())
  const isTelegramWebApp = computed(() => authStorage.isTelegramWebApp())

  // Actions
  async function initialize() {
    if (initialized.value || loading.value) return
    
    loading.value = true
    error.value = null
    
    try {
      // Validate existing auth
      const prevUser = authStorage.getUser()
      const response = await authApi.validate()
      if (response.data?.user) {
        if (prevUser && prevUser.id !== response.data.user.id) {
          // Different user logged in - wipe stale cache
          try {
            apiCache.clear()
            for (let i = localStorage.length - 1; i >= 0; i--) {
              const k = localStorage.key(i)
              if (k && (k.startsWith('tg_player_cached_') || k.startsWith('library-') || k.startsWith('global-'))) {
                localStorage.removeItem(k)
              }
            }
          } catch (_) {}
        }
        user.value = response.data.user
        authStorage.setUser(response.data.user)
      }
      initialized.value = true
      
      // Fetch channel status and config in background without blocking initial navigation
      fetchStatus().catch(err => console.warn('[Auth] Background status fetch error:', err))
      fetchConfig().catch(err => console.warn('[Auth] Background config fetch error:', err))
    } catch (err) {
      // If network is offline or request failed due to connection error, keep existing session!
      const isOfflineError = (typeof navigator !== 'undefined' && !navigator.onLine) || !err.response || err.code === 'ERR_NETWORK' || err.code === 'ECONNABORTED'
      const savedUser = authStorage.getUser()
      if (isOfflineError && savedUser) {
        console.log('[Auth] Network offline, preserving existing session for offline use')
        user.value = savedUser
        initialized.value = true
      } else {
        // Auth explicitly failed (401/403) - clear storage
        authStorage.clear()
        localStorage.removeItem(CHANNEL_STATUS_KEY)
        user.value = null
        error.value = 'Authentication failed'
        initialized.value = true
      }
    } finally {
      loading.value = false
    }
  }
  
  async function fetchStatus() {
    try {
      const response = await authApi.status()
      hasChannel.value = response.data.has_channel || false
      canSave.value = response.data.can_save || false
      channelInfo.value = response.data.channel_info || null
      try {
        localStorage.setItem(CHANNEL_STATUS_KEY, JSON.stringify({
          hasChannel: hasChannel.value,
          canSave: canSave.value,
          channelInfo: channelInfo.value
        }))
      } catch (_) {}
    } catch (err) {
      console.error('Failed to fetch status:', err)
      // Don't fail initialization for status fetch, keep cached status
    }
  }
  
  async function fetchConfig() {
    try {
      const response = await authApi.getConfig()
      if (response.data?.bot_username) {
        appName.value = response.data.bot_username
        botUsername.value = response.data.bot_username
      }
    } catch (err) {
      console.error('Failed to fetch config:', err)
    }
  }
  
  function promptChannelSetup(actionTitle = '') {
    showChannelBanner.value = true
    import('./ui').then(({ useUIStore }) => {
      const uiStore = useUIStore()
      if (uiStore?.toast) {
        uiStore.toast.info(
          'Требуется Telegram-канал',
          actionTitle ? `Для ${actionTitle} подключите канал в настройках` : 'Подключите Telegram-канал для сохранения треков и плейлистов'
        )
      }
    }).catch(() => {})
  }

  function requireChannel(actionTitle = '') {
    if (!hasChannel.value) {
      promptChannelSetup(actionTitle)
      return false
    }
    return true
  }
  
  function dismissChannelBanner() {
    showChannelBanner.value = false
  }

  async function loginWithCode(code) {
    loading.value = true
    error.value = null
    
    try {
      const response = await authApi.verifyCode({ code })
      
      if (response.data?.token) {
        authStorage.setToken(response.data.token)
      }
      if (response.data?.user) {
        const prevUser = authStorage.getUser()
        if (prevUser && prevUser.id !== response.data.user.id) {
          try {
            apiCache.clear()
            for (let i = localStorage.length - 1; i >= 0; i--) {
              const k = localStorage.key(i)
              if (k && (k.startsWith('tg_player_cached_') || k.startsWith('library-') || k.startsWith('global-'))) {
                localStorage.removeItem(k)
              }
            }
          } catch (_) {}
        }
        user.value = response.data.user
        authStorage.setUser(response.data.user)
      }
      
      // Fetch channel status and config in background
      fetchStatus().catch(() => {})
      fetchConfig().catch(() => {})
      
      initialized.value = true
      return response.data
    } catch (err) {
      error.value = 'Invalid or expired code'
      throw err
    } finally {
      loading.value = false
    }
  }

  function logout() {
    authStorage.clear()
    user.value = null
    initialized.value = false
    error.value = null
    try {
      localStorage.removeItem(CHANNEL_STATUS_KEY)
      apiCache.clear()
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const k = localStorage.key(i)
        if (k && (k.startsWith('tg_player_cached_') || k.startsWith('library-') || k.startsWith('global-'))) {
          localStorage.removeItem(k)
        }
      }
    } catch (_) {}
  }

  async function refreshUser() {
    try {
      const response = await authApi.me()
      user.value = response.data
      authStorage.setUser(response.data)
    } catch (err) {
      if (err.response?.status === 401) {
        logout()
      }
    }
  }

  async function updateProfile(data) {
    const response = await authApi.updateProfile(data)
    user.value = response.data
    authStorage.setUser(response.data)
    apiCache.invalidateRelated('user', user.value?.id)
    return response.data
  }

  async function uploadAvatar(file) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await authApi.uploadAvatar(formData)
    if (response.data?.user) {
      user.value = response.data.user
      authStorage.setUser(response.data.user)
    } else if (response.data?.avatar_url) {
      user.value = { ...user.value, custom_avatar_url: response.data.avatar_url }
      authStorage.setUser(user.value)
    }
    apiCache.invalidateRelated('user', user.value?.id)
    return response.data
  }

  async function deleteAvatar() {
    const response = await authApi.deleteAvatar()
    user.value = response.data
    authStorage.setUser(response.data)
    apiCache.invalidateRelated('user', user.value?.id)
    return response.data
  }

  const userDisplayName = computed(() => {
    const u = user.value
    if (!u) return ''
    if (u.custom_nickname && u.custom_nickname.trim()) return u.custom_nickname.trim()
    if (u.first_name) {
      return (u.first_name + (u.last_name ? ' ' + u.last_name : '')).trim()
    }
    return u.username || `Пользователь #${u.id}`
  })

  const userAvatarUrl = computed(() => user.value?.custom_avatar_url || user.value?.photo_url || null)

  return {
    // State
    user,
    loading,
    initialized,
    error,
    hasChannel,
    canSave,
    channelInfo,
    showChannelBanner,
    appName,
    botUsername,
    // Getters
    isAuthenticated,
    isTelegramWebApp,
    userDisplayName,
    userAvatarUrl,
    // Actions
    initialize,
    loginWithCode,
    logout,
    refreshUser,
    updateProfile,
    uploadAvatar,
    deleteAvatar,
    fetchStatus,
    fetchConfig,
    promptChannelSetup,
    requireChannel,
    dismissChannelBanner
  }
})
