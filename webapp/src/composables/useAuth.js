/**
 * Authentication composable
 * Handles Telegram and browser authentication
 */
import { ref, computed } from 'vue'
import { authStorage } from '@/api/client'

export function useAuth(telegram = null) {
  const isAuthenticated = ref(false)
  const currentUser = ref(null)
  const authChecking = ref(true)

  /**
   * Check authentication status
   * Supports Telegram WebApp and JWT browser auth
   */
  const checkAuth = () => {
    // If in Telegram WebApp, we're always authenticated via initData
    if (telegram?.initData) {
      isAuthenticated.value = true
      currentUser.value = telegram.initDataUnsafe?.user || null
      authChecking.value = false
      return true
    }
    
    // Check for JWT token in browser
    if (authStorage.getToken()) {
      isAuthenticated.value = true
      currentUser.value = authStorage.getUser()
      authChecking.value = false
      return true
    }
    
    authChecking.value = false
    return false
  }

  /**
   * Handle successful login
   */
  const handleLogin = async (user, libraryStore, playerStore) => {
    isAuthenticated.value = true
    currentUser.value = user
    
    // Initialize the library after successful login
    await libraryStore.init()
    
    // Restore player state if available
    if (playerStore.hasSavedState()) {
      await playerStore.restoreState()
    }
  }

  /**
   * Handle logout (browser auth only)
   */
  const handleLogout = () => {
    authStorage.clear()
    isAuthenticated.value = false
    currentUser.value = null
  }

  /**
   * Get display name for current user
   */
  const userDisplayName = computed(() => {
    // First try Telegram WebApp
    const tgUser = telegram?.initDataUnsafe?.user
    if (tgUser?.username) {
      return `@${tgUser.username}`
    }
    if (tgUser?.first_name) {
      return tgUser.first_name
    }
    
    // Fall back to JWT user
    if (currentUser.value?.username) {
      return `@${currentUser.value.username}`
    }
    if (currentUser.value?.first_name) {
      return currentUser.value.first_name
    }
    
    return 'Musiq'
  })

  /**
   * Get current user ID
   */
  const currentUserId = computed(() => {
    return telegram?.initDataUnsafe?.user?.id || currentUser.value?.id || null
  })

  return {
    // State
    isAuthenticated,
    currentUser,
    authChecking,
    
    // Computed
    userDisplayName,
    currentUserId,
    
    // Methods
    checkAuth,
    handleLogin,
    handleLogout,
  }
}
