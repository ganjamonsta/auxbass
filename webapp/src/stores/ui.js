import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUIStore = defineStore('ui', () => {
  // Library tab state: 'overview', 'tracks', 'albums', 'artists', or 'playlists'
  const libraryTab = ref(localStorage.getItem('library_active_tab') || 'overview')

  const setLibraryTab = (tab) => {
    libraryTab.value = tab
    localStorage.setItem('library_active_tab', tab)
  }

  // Toast notifications
  const toasts = ref([])
  let toastId = 0

  const showToast = (options) => {
    // Support both object and string arguments
    const toast = typeof options === 'string' 
      ? { title: options, type: 'info' }
      : options
    
    const id = ++toastId
    const newToast = {
      id,
      type: toast.type || 'info',
      title: toast.title,
      message: toast.message,
      duration: toast.duration || 4000,
    }
    
    toasts.value.push(newToast)
    
    if (newToast.duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, newToast.duration)
    }
    
    return id
  }

  const removeToast = (id) => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index !== -1) {
      toasts.value.splice(index, 1)
    }
  }

  // Shorthand methods
  const toast = {
    success: (title, message) => showToast({ type: 'success', title, message }),
    error: (title, message) => showToast({ type: 'error', title, message }),
    warning: (title, message) => showToast({ type: 'warning', title, message }),
    info: (title, message) => showToast({ type: 'info', title, message }),
  }

  // Persistent sidebar keys
  const SIDEBAR_COLLAPSED_KEY = 'tg_player_sidebar_collapsed'
  const NOW_PLAYING_VISIBLE_KEY = 'tg_player_now_playing_visible'

  const loadSavedBoolean = (key) => {
    try {
      const val = localStorage.getItem(key)
      if (val === 'true') return true
      if (val === 'false') return false
      return null
    } catch {
      return null
    }
  }

  const savedSidebarPref = loadSavedBoolean(SIDEBAR_COLLAPSED_KEY)
  const savedNowPlayingPref = loadSavedBoolean(NOW_PLAYING_VISIBLE_KEY)

  // Sidebar collapse state
  const isSidebarCollapsed = ref(savedSidebarPref === true)
  const isAutoCollapsed = ref(false)
  const userCollapsedPreference = ref(savedSidebarPref) // null = auto, true/false = explicit user choice

  const setSidebarCollapsed = (collapsed, manual = false) => {
    isSidebarCollapsed.value = collapsed
    if (manual) {
      userCollapsedPreference.value = collapsed
      try {
        localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(collapsed))
      } catch (_) {}
    }
  }

  const toggleSidebarCollapse = () => {
    setSidebarCollapsed(!isSidebarCollapsed.value, true)
  }

  // Right NowPlayingSidebar visibility state
  const isNowPlayingSidebarVisible = ref(savedNowPlayingPref !== null ? savedNowPlayingPref : true)
  const userNowPlayingPreference = ref(savedNowPlayingPref) // null = auto, boolean = explicit user choice

  const openNowPlayingSidebar = (manual = false) => {
    setNowPlayingSidebar(true, manual)
  }

  const closeNowPlayingSidebar = (manual = false) => {
    setNowPlayingSidebar(false, manual)
  }

  const toggleNowPlayingSidebar = () => {
    const next = !isNowPlayingSidebarVisible.value
    setNowPlayingSidebar(next, true)
  }

  const setNowPlayingSidebar = (visible, manual = false) => {
    isNowPlayingSidebarVisible.value = visible
    if (manual) {
      userNowPlayingPreference.value = visible
      try {
        localStorage.setItem(NOW_PLAYING_VISIBLE_KEY, String(visible))
      } catch (_) {}
    }
  }

  // Settings view active section: 'import' or 'settings'
  const settingsSection = ref('import')

  const setSettingsSection = (section) => {
    if (settingsSection.value !== section) {
      settingsSection.value = section
    }
  }

  // Pinned sidebar playlists (array of playlist IDs)
  const PINNED_PLAYLISTS_KEY = 'tg_player_pinned_playlists'
  const loadPinnedPlaylists = () => {
    try {
      const saved = localStorage.getItem(PINNED_PLAYLISTS_KEY)
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }
  const pinnedPlaylistIds = ref(loadPinnedPlaylists())

  const savePinnedPlaylists = () => {
    try {
      localStorage.setItem(PINNED_PLAYLISTS_KEY, JSON.stringify(pinnedPlaylistIds.value))
    } catch (_) {}
  }

  const isPlaylistPinned = (playlistId) => {
    if (!playlistId) return false
    return pinnedPlaylistIds.value.includes(Number(playlistId))
  }

  const pinPlaylist = (playlistId) => {
    const numId = Number(playlistId)
    if (!numId) return
    if (!pinnedPlaylistIds.value.includes(numId)) {
      pinnedPlaylistIds.value = [numId, ...pinnedPlaylistIds.value]
      savePinnedPlaylists()
    }
  }

  const unpinPlaylist = (playlistId) => {
    const numId = Number(playlistId)
    if (!numId) return
    pinnedPlaylistIds.value = pinnedPlaylistIds.value.filter(id => id !== numId)
    savePinnedPlaylists()
  }

  const togglePinPlaylist = (playlistId) => {
    const numId = Number(playlistId)
    if (!numId) return false
    if (isPlaylistPinned(numId)) {
      unpinPlaylist(numId)
      return false
    } else {
      pinPlaylist(numId)
      return true
    }
  }

  return {
    libraryTab,
    setLibraryTab,
    // Settings view active section
    settingsSection,
    setSettingsSection,
    // Pinned Playlists
    pinnedPlaylistIds,
    isPlaylistPinned,
    pinPlaylist,
    unpinPlaylist,
    togglePinPlaylist,
    // Left Sidebar state
    isSidebarCollapsed,
    isAutoCollapsed,
    userCollapsedPreference,
    setSidebarCollapsed,
    toggleSidebarCollapse,
    // Right NowPlaying Sidebar state
    isNowPlayingSidebarVisible,
    userNowPlayingPreference,
    openNowPlayingSidebar,
    closeNowPlayingSidebar,
    toggleNowPlayingSidebar,
    setNowPlayingSidebar,
    // Toast
    toasts,
    showToast,
    removeToast,
    toast
  }
})

