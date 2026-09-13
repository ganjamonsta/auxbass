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

  // Sidebar collapse & overlay drawer state
  const isSidebarCollapsed = ref(false)
  const isSidebarOverlayOpen = ref(false)
  const isAutoCollapsed = ref(false)
  const userCollapsedPreference = ref(null) // null = auto, true/false = explicit user choice

  const openSidebarOverlay = () => {
    isSidebarOverlayOpen.value = true
  }

  const closeSidebarOverlay = () => {
    isSidebarOverlayOpen.value = false
  }

  const toggleSidebarOverlay = () => {
    isSidebarOverlayOpen.value = !isSidebarOverlayOpen.value
  }

  const setSidebarCollapsed = (collapsed, manual = false) => {
    isSidebarCollapsed.value = collapsed
    if (manual) {
      userCollapsedPreference.value = collapsed
    }
    if (!collapsed) {
      isSidebarOverlayOpen.value = false
    }
  }

  const toggleSidebarCollapse = () => {
    if (isSidebarCollapsed.value) {
      // If already collapsed to icons, clicking burger button toggles the overlay drawer
      toggleSidebarOverlay()
    } else {
      // If expanded in normal desktop grid, collapse to icons
      setSidebarCollapsed(true, true)
    }
  }

  return {
    libraryTab,
    setLibraryTab,
    // Sidebar state
    isSidebarCollapsed,
    isSidebarOverlayOpen,
    isAutoCollapsed,
    userCollapsedPreference,
    openSidebarOverlay,
    closeSidebarOverlay,
    toggleSidebarOverlay,
    setSidebarCollapsed,
    toggleSidebarCollapse,
    // Toast
    toasts,
    showToast,
    removeToast,
    toast
  }
})
