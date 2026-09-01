/**
 * Player Storage utilities
 * Handles localStorage operations for player settings and state
 */

const STORAGE_KEY = 'tg_player_settings'
const STATE_STORAGE_KEY = 'tg_player_state'
export const STATE_SAVE_INTERVAL = 5000 // Save position every 5 seconds

/**
 * Load player settings from localStorage
 */
export const loadSettings = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      return {
        autoCacheEnabled: true,
        cacheMaxBytes: 1073741824, // 1 GB default
        ...parsed
      }
    }
  } catch (e) {
    console.error('Failed to load player settings:', e)
  }
  return {
    autoCacheEnabled: true,
    cacheMaxBytes: 1073741824
  }
}

/**
 * Save player settings to localStorage
 */
export const saveSettings = (settings) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch (e) {
    console.error('Failed to save player settings:', e)
  }
}

/**
 * Load player state (position, track, queue) from localStorage
 */
export const loadPlayerState = () => {
  try {
    const saved = localStorage.getItem(STATE_STORAGE_KEY)
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('Failed to load player state:', e)
  }
  return null
}

/**
 * Save player state to localStorage
 */
export const savePlayerState = (state) => {
  try {
    localStorage.setItem(STATE_STORAGE_KEY, JSON.stringify({
      ...state,
      savedAt: Date.now()
    }))
  } catch (e) {
    console.error('Failed to save player state:', e)
  }
}

/**
 * Clear saved player state
 */
export const clearPlayerState = () => {
  try {
    localStorage.removeItem(STATE_STORAGE_KEY)
  } catch (e) {
    console.error('Failed to clear player state:', e)
  }
}
