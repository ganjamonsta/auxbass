import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUIStore = defineStore('ui', () => {
  // Collections tab state: 'albums' or 'playlists'
  const collectionsTab = ref('albums')

  const setCollectionsTab = (tab) => {
    collectionsTab.value = tab
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

  return {
    collectionsTab,
    setCollectionsTab,
    // Toast
    toasts,
    showToast,
    removeToast,
    toast
  }
})
