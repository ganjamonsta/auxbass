/**
 * Playlist Context Menu composable
 * Унифицированный обработчик контекстного меню для плейлистов и альбомов
 * Используется в Sidebar, PlaylistCard, AlbumCard и других компонентах
 */
import { ref, inject } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import { playlistsApi, albumsApi } from '@/api/client'

/**
 * @param {Object} options - Опции
 * @param {Object} options.telegram - Telegram WebApp объект (опционально)
 * @param {Function} options.onMenuClose - Колбэк при закрытии меню (опционально)
 * @param {Function} options.onPlaylistDeleted - Колбэк после удаления плейлиста (опционально)
 * @param {Function} options.onPlaylistRenamed - Колбэк после переименования (опционально)
 */
export function usePlaylistContextMenu(options = {}) {
  const router = useRouter()
  const playerStore = usePlayerStore()
  const libraryStore = useLibraryStore()
  const uiStore = useUIStore()
  
  // Inject telegram если не передан явно
  const telegram = options.telegram || inject('telegram', null)

  // ========== Menu State ==========
  const showPlaylistMenu = ref(false)
  const selectedPlaylist = ref(null)
  
  // ========== Rename Modal State ==========
  const showRenameModal = ref(false)
  const renameValue = ref('')

  // ========== Haptic Feedback ==========
  const haptic = (type = 'light') => {
    telegram?.HapticFeedback?.impactOccurred?.(type)
  }

  // ========== Menu Actions ==========
  
  const openPlaylistMenu = (playlist) => {
    haptic('light')
    selectedPlaylist.value = playlist
    showPlaylistMenu.value = true
  }

  const closePlaylistMenu = () => {
    showPlaylistMenu.value = false
    selectedPlaylist.value = null
    options.onMenuClose?.()
  }

  // ========== Navigation ==========
  
  const handleOpen = (playlist) => {
    const p = playlist || selectedPlaylist.value
    closePlaylistMenu()
    if (!p) return
    
    if (p.is_auto_album) {
      router.push(`/album/${p.id}`)
    } else {
      router.push(`/playlist/${p.id}`)
    }
  }

  // ========== Playback Handlers ==========
  
  const handlePlayAll = async (playlist) => {
    const p = playlist || selectedPlaylist.value
    closePlaylistMenu()
    if (!p?.id) return
    
    try {
      // Загрузить треки плейлиста и запустить воспроизведение
      const tracks = await loadPlaylistTracks(p)
      if (tracks?.length) {
        playerStore.playTrackList(tracks, 0)
        uiStore.toast.success('Воспроизведение', `Играет: ${p.name}`)
      }
    } catch (error) {
      console.error('Failed to play playlist:', error)
      uiStore.toast.error('Ошибка', 'Не удалось воспроизвести плейлист')
    }
  }

  const handleShuffle = async (playlist) => {
    const p = playlist || selectedPlaylist.value
    closePlaylistMenu()
    if (!p?.id) return
    
    try {
      const tracks = await loadPlaylistTracks(p)
      if (tracks?.length) {
        // Перемешать и запустить
        const shuffled = [...tracks].sort(() => Math.random() - 0.5)
        playerStore.playTrackList(shuffled, 0)
        playerStore.setShuffle(true)
        uiStore.toast.success('Перемешивание', `Играет: ${p.name}`)
      }
    } catch (error) {
      console.error('Failed to shuffle playlist:', error)
      uiStore.toast.error('Ошибка', 'Не удалось воспроизвести плейлист')
    }
  }

  const handleAddToQueue = async (playlist) => {
    const p = playlist || selectedPlaylist.value
    closePlaylistMenu()
    if (!p?.id) return
    
    try {
      const tracks = await loadPlaylistTracks(p)
      if (tracks?.length) {
        tracks.forEach(track => playerStore.addToQueue(track))
        uiStore.toast.success('Добавлено', `${tracks.length} треков добавлено в очередь`)
      }
    } catch (error) {
      console.error('Failed to add playlist to queue:', error)
      uiStore.toast.error('Ошибка', 'Не удалось добавить в очередь')
    }
  }

  // ========== Edit Handlers ==========
  
  const handleRename = (playlist) => {
    const p = playlist || selectedPlaylist.value
    closePlaylistMenu()
    if (!p || p.is_auto_album) return
    
    renameValue.value = p.name || ''
    selectedPlaylist.value = p
    showRenameModal.value = true
  }

  const closeRenameModal = () => {
    showRenameModal.value = false
    renameValue.value = ''
  }

  const confirmRename = async () => {
    const p = selectedPlaylist.value
    if (!p?.id || !renameValue.value.trim()) return
    
    try {
      await playlistsApi.update(p.id, { name: renameValue.value.trim() })
      await libraryStore.loadPlaylists()
      uiStore.toast.success('Переименовано', `Плейлист: ${renameValue.value.trim()}`)
      options.onPlaylistRenamed?.(p, renameValue.value.trim())
      closeRenameModal()
    } catch (error) {
      console.error('Failed to rename playlist:', error)
      uiStore.toast.error('Ошибка', 'Не удалось переименовать плейлист')
    }
  }

  // ========== Delete Handler ==========
  
  const handleDelete = async (playlist) => {
    const p = playlist || selectedPlaylist.value
    closePlaylistMenu()
    if (!p?.id || p.is_auto_album) return
    
    if (confirm(`Удалить плейлист "${p.name}"?`)) {
      try {
        await playlistsApi.delete(p.id)
        await libraryStore.loadPlaylists()
        uiStore.toast.success('Удалено', `Плейлист "${p.name}" удалён`)
        options.onPlaylistDeleted?.(p)
      } catch (error) {
        console.error('Failed to delete playlist:', error)
        uiStore.toast.error('Ошибка', 'Не удалось удалить плейлист')
      }
    }
  }

  // ========== Helper: Load Playlist Tracks ==========
  
  const loadPlaylistTracks = async (playlist) => {
    if (!playlist?.id) return []
    
    try {
      if (playlist.is_auto_album) {
        const response = await albumsApi.getTracks(playlist.id)
        return response?.tracks || response || []
      } else {
        const response = await playlistsApi.getTracks(playlist.id)
        return response?.tracks || response || []
      }
    } catch (error) {
      console.error('Failed to load playlist tracks:', error)
      return []
    }
  }

  return {
    // Menu state
    showPlaylistMenu,
    selectedPlaylist,
    openPlaylistMenu,
    closePlaylistMenu,
    
    // Rename modal state
    showRenameModal,
    renameValue,
    closeRenameModal,
    confirmRename,
    
    // All handlers for PlaylistMenu events
    handleOpen,
    handlePlayAll,
    handleShuffle,
    handleAddToQueue,
    handleRename,
    handleDelete,
    
    // Convenience object for v-bind on PlaylistMenu
    menuHandlers: {
      close: closePlaylistMenu,
      open: handleOpen,
      playAll: handlePlayAll,
      shuffle: handleShuffle,
      addToQueue: handleAddToQueue,
      rename: handleRename,
      delete: handleDelete,
    }
  }
}
