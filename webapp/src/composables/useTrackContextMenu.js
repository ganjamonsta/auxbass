/**
 * Track Context Menu composable
 * Унифицированный обработчик контекстного меню для треков
 * Используется в MiniPlayer, DesktopPlayer, TrackItem и других компонентах
 */
import { ref, inject, computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import { playerApi } from '@/api/client'

/**
 * @param {Object} options - Опции
 * @param {Function} options.getTrack - Функция получения текущего трека (для реактивности)
 * @param {Object} options.telegram - Telegram WebApp объект (опционально)
 * @param {Function} options.onMenuClose - Колбэк при закрытии меню (опционально)
 * @param {Function} options.onTrackDeleted - Колбэк после удаления трека (опционально)
 */
export function useTrackContextMenu(options = {}) {
  const router = useRouter()
  const playerStore = usePlayerStore()
  const libraryStore = useLibraryStore()
  const uiStore = useUIStore()
  
  // Inject telegram если не передан явно
  const telegram = options.telegram || inject('telegram', null)

  // ========== Menu State ==========
  const showTrackMenu = ref(false)
  
  // ========== Playlist Picker State ==========
  const showPlaylistPicker = ref(false)
  
  // ========== Edit Modal State ==========
  const showEditModal = ref(false)
  const editingTrack = ref(null)

  // ========== Menu Actions ==========
  
  const openTrackMenu = () => {
    telegram?.HapticFeedback?.impactOccurred?.('light')
    showTrackMenu.value = true
  }

  const closeTrackMenu = () => {
    showTrackMenu.value = false
    options.onMenuClose?.()
  }

  // ========== Navigation Handlers ==========
  
  const handleGoToArtist = (artist) => {
    closeTrackMenu()
    if (artist) {
      router.push(`/artist/${encodeURIComponent(artist)}`)
    }
  }

  const handleGoToAlbum = (albumId) => {
    closeTrackMenu()
    if (albumId) {
      router.push(`/album/${albumId}`)
    }
  }

  // ========== Playlist Handlers ==========
  
  const handleAddToPlaylist = (trackData) => {
    closeTrackMenu()
    showPlaylistPicker.value = true
  }

  const closePlaylistPicker = () => {
    showPlaylistPicker.value = false
  }

  const handlePlaylistAdded = (playlist) => {
    showPlaylistPicker.value = false
    uiStore.toast.success('Добавлено', `Трек добавлен в плейлист "${playlist.name}"`)
  }

  // ========== Edit Handlers ==========
  
  const handleEditTrack = (track) => {
    closeTrackMenu()
    editingTrack.value = track
    showEditModal.value = true
  }

  const closeEditModal = () => {
    showEditModal.value = false
    editingTrack.value = null
  }

  const handleTrackSaved = (updatedTrack) => {
    closeEditModal()
    // Update will be reflected through library store
  }

  // ========== Download Handler ==========
  
  const handleDownloadTrack = async (track) => {
    const trackId = track?.id || options.getTrack?.()?.id
    if (!trackId) return
    
    try {
      await playerApi.download(trackId)
    } catch (error) {
      console.error('Failed to download track:', error)
      uiStore.toast.error('Ошибка', 'Не удалось скачать трек')
    }
    closeTrackMenu()
  }

  // ========== Delete Handler ==========
  
  const handleDeleteTrack = async (track) => {
    const trackToDelete = track || options.getTrack?.()
    if (!trackToDelete?.id) return
    
    if (confirm('Удалить трек полностью?')) {
      try {
        await libraryStore.deleteTrack(trackToDelete.id)
        // Переключить на следующий трек если удаляем текущий
        if (playerStore.currentTrack?.id === trackToDelete.id) {
          playerStore.next()
        }
        options.onTrackDeleted?.(trackToDelete)
      } catch (error) {
        console.error('Failed to delete track:', error)
        uiStore.toast.error('Ошибка', 'Не удалось удалить трек')
      }
    }
    closeTrackMenu()
  }

  // ========== Library Handlers ==========
  
  const handleRemoveFromLibrary = async (track) => {
    const trackToRemove = track || options.getTrack?.()
    if (!trackToRemove?.id) return
    
    try {
      await libraryStore.removeFromLibrary(trackToRemove.id)
      uiStore.toast.success('Удалено', 'Трек убран из библиотеки')
    } catch (error) {
      console.error('Failed to remove from library:', error)
      uiStore.toast.error('Ошибка', 'Не удалось убрать трек из библиотеки')
    }
    closeTrackMenu()
  }

  const handleAddToLibrary = async (track) => {
    const trackToAdd = track || options.getTrack?.()
    if (!trackToAdd?.id) return
    
    try {
      await libraryStore.addToLibrary(trackToAdd.id)
      uiStore.toast.success('Добавлено', 'Трек добавлен в библиотеку')
    } catch (error) {
      console.error('Failed to add to library:', error)
      uiStore.toast.error('Ошибка', 'Не удалось добавить трек в библиотеку')
    }
    closeTrackMenu()
  }

  // ========== Queue Handlers ==========
  
  const handlePlayNext = (track) => {
    const trackToQueue = track || options.getTrack?.()
    if (!trackToQueue) return
    
    playerStore.playNext(trackToQueue)
    uiStore.toast.success('Добавлено', 'Трек будет воспроизведён следующим')
    closeTrackMenu()
  }

  const handleAddToQueue = (track) => {
    const trackToQueue = track || options.getTrack?.()
    if (!trackToQueue) return
    
    playerStore.addToQueue(trackToQueue)
    uiStore.toast.success('Добавлено', 'Трек добавлен в очередь')
    closeTrackMenu()
  }

  return {
    // Menu state
    showTrackMenu,
    openTrackMenu,
    closeTrackMenu,
    
    // Playlist picker state
    showPlaylistPicker,
    closePlaylistPicker,
    handlePlaylistAdded,
    
    // Edit modal state
    showEditModal,
    editingTrack,
    closeEditModal,
    handleTrackSaved,
    
    // All handlers for TrackMenu events
    handleGoToArtist,
    handleGoToAlbum,
    handleAddToPlaylist,
    handleEditTrack,
    handleDownloadTrack,
    handleDeleteTrack,
    handleRemoveFromLibrary,
    handleAddToLibrary,
    handlePlayNext,
    handleAddToQueue,
    
    // Convenience object for v-bind on TrackMenu
    menuHandlers: {
      close: closeTrackMenu,
      goToArtist: handleGoToArtist,
      goToAlbum: handleGoToAlbum,
      addToPlaylist: handleAddToPlaylist,
      edit: handleEditTrack,
      download: handleDownloadTrack,
      delete: handleDeleteTrack,
      removeFromLibrary: handleRemoveFromLibrary,
      addToLibrary: handleAddToLibrary,
      playNext: handlePlayNext,
      addToQueue: handleAddToQueue,
    }
  }
}
