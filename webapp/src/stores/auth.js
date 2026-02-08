import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api, { authStorage, authApi } from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(authStorage.getUser())
  const loading = ref(false)
  const initialized = ref(false)
  const error = ref(null)
  
  // Channel/Premium status
  const hasChannel = ref(false)
  const canSave = ref(false)
  const channelInfo = ref(null)
  const showChannelBanner = ref(false)  // Show banner when user tries premium action
  
  // App config
  const appName = ref('TG Player')  // Default, will be overridden by bot_username

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
      const response = await authApi.validate()
      if (response.data?.user) {
        user.value = response.data.user
        authStorage.setUser(response.data.user)
      }
      initialized.value = true
      
      // Fetch channel status and config after auth
      await Promise.all([fetchStatus(), fetchConfig()])
    } catch (err) {
      // Auth failed - clear storage
      authStorage.clear()
      user.value = null
      error.value = 'Authentication failed'
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
    } catch (err) {
      console.error('Failed to fetch status:', err)
      // Don't fail initialization for status fetch
    }
  }
  
  async function fetchConfig() {
    try {
      const response = await authApi.getConfig()
      if (response.data?.bot_username) {
        appName.value = response.data.bot_username
      }
    } catch (err) {
      console.error('Failed to fetch config:', err)
    }
  }
  
  function promptChannelSetup() {
    showChannelBanner.value = true
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
        user.value = response.data.user
        authStorage.setUser(response.data.user)
      }
      
      // Fetch channel status and config after successful login
      await Promise.all([fetchStatus(), fetchConfig()])
      
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
    // Getters
    isAuthenticated,
    isTelegramWebApp,
    // Actions
    initialize,
    loginWithCode,
    logout,
    refreshUser,
    fetchStatus,
    fetchConfig,
    promptChannelSetup,
    dismissChannelBanner
  }
})
