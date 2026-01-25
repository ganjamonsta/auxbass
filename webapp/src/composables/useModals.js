/**
 * Modals composable
 * Manages all modal/dialog states in the app
 */
import { ref } from 'vue'

export function useModals(telegram = null) {
  // Track menu state
  const showTrackMenuModal = ref(false)
  const selectedTrack = ref(null)

  // Playlist menu state
  const showPlaylistMenuModal = ref(false)
  const selectedPlaylist = ref(null)

  // Edit modal state
  const showEditModal = ref(false)
  const editingTrack = ref(null)

  // Confirm dialog state
  const showConfirmDelete = ref(false)
  const deletingTrack = ref(null)

  // Playlist picker state
  const showPlaylistPicker = ref(false)
  const trackForPlaylist = ref(null)

  // Create playlist dialog
  const showCreatePlaylist = ref(false)
  const newPlaylistName = ref('')

  // Full player (mobile)
  const showFullPlayer = ref(false)

  // Toast notification ref
  const toast = ref(null)

  // ========== Track Menu ==========
  
  const showTrackMenu = (track) => {
    selectedTrack.value = track
    showTrackMenuModal.value = true
    telegram?.HapticFeedback?.impactOccurred?.('light')
  }

  const closeTrackMenu = () => {
    showTrackMenuModal.value = false
    selectedTrack.value = null
  }

  // ========== Playlist Menu ==========
  
  const showPlaylistMenu = (playlist) => {
    selectedPlaylist.value = playlist
    showPlaylistMenuModal.value = true
    telegram?.HapticFeedback?.impactOccurred?.('light')
  }

  const closePlaylistMenu = () => {
    showPlaylistMenuModal.value = false
    selectedPlaylist.value = null
  }

  // ========== Edit Modal ==========
  
  const openEditModal = (track) => {
    editingTrack.value = { ...track }
    showEditModal.value = true
    closeTrackMenu()
  }

  const closeEditModal = () => {
    showEditModal.value = false
    editingTrack.value = null
  }

  // ========== Delete Confirmation ==========
  
  const confirmDelete = (track) => {
    deletingTrack.value = track
    showConfirmDelete.value = true
    closeTrackMenu()
  }

  const closeConfirmDelete = () => {
    showConfirmDelete.value = false
    deletingTrack.value = null
  }

  // ========== Playlist Picker ==========
  
  const openPlaylistPicker = (track) => {
    trackForPlaylist.value = track
    showPlaylistPicker.value = true
    closeTrackMenu()
  }

  const closePlaylistPicker = () => {
    showPlaylistPicker.value = false
    trackForPlaylist.value = null
  }

  // ========== Create Playlist ==========
  
  const openCreatePlaylist = () => {
    newPlaylistName.value = ''
    showCreatePlaylist.value = true
  }

  const closeCreatePlaylist = () => {
    showCreatePlaylist.value = false
    newPlaylistName.value = ''
  }

  // ========== Full Player ==========
  
  const openFullPlayer = () => {
    showFullPlayer.value = true
  }

  const closeFullPlayer = () => {
    showFullPlayer.value = false
  }

  // ========== Toast ==========
  
  const showToast = (message, type = 'info') => {
    toast.value?.show(message, type)
  }

  return {
    // Track Menu
    showTrackMenuModal,
    selectedTrack,
    showTrackMenu,
    closeTrackMenu,
    
    // Playlist Menu
    showPlaylistMenuModal,
    selectedPlaylist,
    showPlaylistMenu,
    closePlaylistMenu,
    
    // Edit Modal
    showEditModal,
    editingTrack,
    openEditModal,
    closeEditModal,
    
    // Delete Confirmation
    showConfirmDelete,
    deletingTrack,
    confirmDelete,
    closeConfirmDelete,
    
    // Playlist Picker
    showPlaylistPicker,
    trackForPlaylist,
    openPlaylistPicker,
    closePlaylistPicker,
    
    // Create Playlist
    showCreatePlaylist,
    newPlaylistName,
    openCreatePlaylist,
    closeCreatePlaylist,
    
    // Full Player
    showFullPlayer,
    openFullPlayer,
    closeFullPlayer,
    
    // Toast
    toast,
    showToast,
  }
}
