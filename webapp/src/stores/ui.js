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
  const NARROW_WIDTH_THRESHOLD = 1200

  const isNarrowScreen = () => {
    return typeof window !== 'undefined' && window.innerWidth < NARROW_WIDTH_THRESHOLD
  }

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

  // Safe initial width for responsive defaults
  const initialWidth = typeof window !== 'undefined' ? window.innerWidth : 1280
  let initialSidebarCollapsed = savedSidebarPref !== null
    ? savedSidebarPref === true
    : initialWidth < 1000

  let initialNowPlayingVisible = savedNowPlayingPref !== null
    ? savedNowPlayingPref === true
    : initialWidth >= 1200

  // Under narrow conditions (< 1200px), prevent both sidebars from opening simultaneously on initial load
  if (initialWidth < NARROW_WIDTH_THRESHOLD && !initialSidebarCollapsed && initialNowPlayingVisible) {
    if (savedNowPlayingPref === true && savedSidebarPref !== false) {
      initialSidebarCollapsed = true
    } else {
      initialNowPlayingVisible = false
    }
  }

  // Sidebar collapse state
  const isSidebarCollapsed = ref(initialSidebarCollapsed)
  const isAutoCollapsed = ref(false)
  const userCollapsedPreference = ref(savedSidebarPref) // null = auto, true/false = explicit user choice

  const setSidebarCollapsed = (collapsed, manual = false) => {
    isSidebarCollapsed.value = collapsed

    if (!collapsed) {
      // Expanding left sidebar to full mode (280px)
      if (isNarrowScreen()) {
        // Under narrow conditions, Full Left and Right sidebars cannot coexist.
        // Swap: auto-hide Right sidebar so Left sidebar can expand without pushing content out of frame.
        if (isNowPlayingSidebarVisible.value) {
          isNowPlayingSidebarVisible.value = false
          isRightAutoHidden.value = true
        }
      }
    } else {
      // Collapsing left sidebar to rail mode (72px)
      // If Right sidebar was previously auto-hidden to yield, restore it!
      if (isRightAutoHidden.value && userNowPlayingPreference.value !== false) {
        isNowPlayingSidebarVisible.value = true
        isRightAutoHidden.value = false
      }
    }

    if (manual) {
      userCollapsedPreference.value = collapsed
      isAutoCollapsed.value = false
      try {
        localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(collapsed))
      } catch (_) {}
    }
  }

  const toggleSidebarCollapse = () => {
    setSidebarCollapsed(!isSidebarCollapsed.value, true)
  }

  // Right NowPlayingSidebar visibility state
  const isNowPlayingSidebarVisible = ref(initialNowPlayingVisible)
  const isRightAutoHidden = ref(false)
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

    if (visible) {
      // Right sidebar is being opened (320px)
      isRightAutoHidden.value = false
      if (isNarrowScreen()) {
        // Under narrow conditions, Full Left and Right sidebars cannot coexist.
        // Swap: auto-collapse Left sidebar to rail (72px) so Right sidebar can open safely.
        if (!isSidebarCollapsed.value) {
          isSidebarCollapsed.value = true
          isAutoCollapsed.value = true
        }
      }
    } else {
      // Right sidebar is being closed
      // If Left sidebar was auto-collapsed to make room for Right, restore it to full mode!
      if (isAutoCollapsed.value && userCollapsedPreference.value !== true) {
        isSidebarCollapsed.value = false
        isAutoCollapsed.value = false
      }
    }

    if (manual) {
      userNowPlayingPreference.value = visible
      isRightAutoHidden.value = false
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
    isRightAutoHidden,
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

