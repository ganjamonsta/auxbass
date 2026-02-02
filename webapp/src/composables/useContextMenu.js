/**
 * Universal Context Menu Manager
 * Единый обработчик контекстного меню для ВСЕХ типов элементов
 * 
 * Типы: 'track', 'playlist', 'album', 'artist', 'user'
 * 
 * Использование:
 *   const { openMenu } = useContextMenu()
 *   @contextmenu.prevent="openMenu('track', track)"
 *   @contextmenu.prevent="openMenu('playlist', playlist)"
 */
import { ref, inject, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import { useModals } from '@/composables/useModals'
import { playerApi, playlistsApi, albumsApi, tracksApi } from '@/api/client'
import { getAllTrackArtists } from '@/utils/formatters'

// Singleton state - shared across all components
const isOpen = ref(false)
const menuType = ref(null)        // 'track' | 'playlist' | 'album' | 'artist' | 'user'
const menuData = ref(null)        // The actual item data
const menuContext = ref(null)     // Additional context (e.g., 'player', 'sidebar', 'library')
const menuPosition = ref({ x: 0, y: 0 })  // Mouse position for desktop context menu

// Modal states
const showPlaylistPicker = ref(false)
const showEditModal = ref(false)
const showRenameModal = ref(false)
const editingItem = ref(null)
const renameValue = ref('')

/**
 * Universal Context Menu composable
 */
export function useContextMenu() {
  const router = useRouter()
  const playerStore = usePlayerStore()
  const libraryStore = useLibraryStore()
  const uiStore = useUIStore()
  const { closeFullPlayer } = useModals()
  const telegram = inject('telegram', null)

  // ═══════════════════════════════════════════════════════════
  // MENU CONTROL
  // ═══════════════════════════════════════════════════════════

  const haptic = (type = 'light') => {
    telegram?.HapticFeedback?.impactOccurred?.(type)
  }

  /**
   * Open context menu for any element type
   * @param {string} type - 'track' | 'playlist' | 'album' | 'artist' | 'user'
   * @param {Object} data - The item data
   * @param {string} context - Optional context ('player', 'sidebar', 'library', etc.)
   */
  const openMenu = (type, data, context = null, event = null) => {
    haptic('light')
    menuType.value = type
    menuData.value = data
    menuContext.value = context
    
    // Capture mouse position for desktop
    if (event && event.clientX !== undefined) {
      menuPosition.value = { x: event.clientX, y: event.clientY }
    } else {
      menuPosition.value = { x: 0, y: 0 }
    }
    
    isOpen.value = true
  }

  const closeMenu = () => {
    isOpen.value = false
    // Delay clearing data for exit animation
    setTimeout(() => {
      menuType.value = null
      menuData.value = null
      menuContext.value = null
    }, 200)
  }

  // ═══════════════════════════════════════════════════════════
  // TRACK ACTIONS
  // ═══════════════════════════════════════════════════════════

  const trackActions = {
    goToArtist: (track) => {
      closeMenu()
      closeFullPlayer() // Close full player if open
      // Get all artists including from filename for tracks without metadata
      const artists = getAllTrackArtists(track?.artist, track?.title, track?.file_name)
      if (artists.length > 0) {
        const artistName = artists[0]
        router.push(`/artist/${encodeURIComponent(artistName)}`)
      }
    },

    // Go to specific artist by name (for multi-artist selection)
    goToArtistByName: (track, artistName) => {
      closeMenu()
      closeFullPlayer()
      if (artistName) {
        router.push(`/artist/${encodeURIComponent(artistName)}`)
      }
    },

    goToAlbum: (track) => {
      closeMenu()
      closeFullPlayer() // Close full player if open
      const albumId = track?.album_id || track?.album?.id
      if (albumId) {
        router.push(`/album/${albumId}`)
      }
    },

    playNext: (track) => {
      if (track) {
        playerStore.playNext(track)
        uiStore.toast.success('Добавлено', 'Трек будет воспроизведён следующим')
      }
      closeMenu()
    },

    addToQueue: (track) => {
      if (track) {
        playerStore.addToQueue(track)
        uiStore.toast.success('Добавлено', 'Трек добавлен в очередь')
      }
      closeMenu()
    },

    addToPlaylist: (track) => {
      closeMenu()
      editingItem.value = track
      showPlaylistPicker.value = true
    },

    edit: (track) => {
      closeMenu()
      editingItem.value = track
      showEditModal.value = true
    },

    download: async (track) => {
      if (track?.id) {
        try {
          await playerApi.download(track.id)
          uiStore.toast.success('Отправлено', 'Трек отправлен в Telegram')
        } catch (error) {
          console.error('Failed to download track:', error)
          uiStore.toast.error('Ошибка', 'Не удалось отправить трек')
        }
      }
      closeMenu()
    },

    downloadHD: async () => {
      // HD version is available only for current playing track
      const hdInfo = playerStore.hdTrackInfo
      if (hdInfo?.id) {
        try {
          await playerApi.download(hdInfo.id)
          uiStore.toast.success('HD отправлено', 'HD версия отправлена в Telegram')
        } catch (error) {
          console.error('Failed to download HD track:', error)
          uiStore.toast.error('Ошибка', 'Не удалось отправить HD версию')
        }
      }
      closeMenu()
    },

    // Download the track itself as HD (for HD tracks in context menu)
    downloadTrackHD: async (track) => {
      if (track?.id) {
        try {
          await playerApi.download(track.id)
          uiStore.toast.success('HD отправлено', 'HD файл отправлен в Telegram')
        } catch (error) {
          console.error('Failed to download HD track:', error)
          uiStore.toast.error('Ошибка', 'Не удалось отправить HD файл')
        }
      }
      closeMenu()
    },

    delete: async (track) => {
      if (!track?.id) return closeMenu()
      
      if (confirm('Удалить трек полностью?')) {
        try {
          await libraryStore.deleteTrack(track.id)
          if (playerStore.currentTrack?.id === track.id) {
            playerStore.next()
          }
          uiStore.toast.success('Удалено', 'Трек удалён')
        } catch (error) {
          console.error('Failed to delete track:', error)
          uiStore.toast.error('Ошибка', 'Не удалось удалить трек')
        }
      }
      closeMenu()
    },

    removeFromLibrary: async (track) => {
      if (!track?.id) return closeMenu()
      
      try {
        await libraryStore.removeFromLibrary(track.id)
        uiStore.toast.success('Удалено', 'Трек убран из библиотеки')
      } catch (error) {
        console.error('Failed to remove from library:', error)
        uiStore.toast.error('Ошибка', 'Не удалось убрать трек')
      }
      closeMenu()
    },

    addToLibrary: async (track) => {
      if (!track?.id) return closeMenu()
      
      try {
        await libraryStore.addToLibrary(track.id)
        uiStore.toast.success('Добавлено', 'Трек добавлен в библиотеку')
      } catch (error) {
        console.error('Failed to add to library:', error)
        uiStore.toast.error('Ошибка', 'Не удалось добавить трек')
      }
      closeMenu()
    },

    removeFromPlaylist: async (track, playlistId) => {
      if (!track?.id || !playlistId) return closeMenu()
      
      try {
        await playlistsApi.removeTrack(playlistId, track.id)
        uiStore.toast.success('Удалено', 'Трек убран из плейлиста')
      } catch (error) {
        console.error('Failed to remove from playlist:', error)
        uiStore.toast.error('Ошибка', 'Не удалось убрать трек')
      }
      closeMenu()
    },
  }

  // ═══════════════════════════════════════════════════════════
  // PLAYLIST ACTIONS
  // ═══════════════════════════════════════════════════════════

  const playlistActions = {
    open: (playlist) => {
      closeMenu()
      if (!playlist?.id) return
      
      if (playlist.is_auto_album) {
        router.push(`/album/${playlist.id}`)
      } else {
        router.push(`/playlist/${playlist.id}`)
      }
    },

    playAll: async (playlist) => {
      if (!playlist?.id) return closeMenu()
      
      try {
        const tracks = await loadPlaylistTracks(playlist)
        if (tracks?.length) {
          playerStore.play(tracks[0], tracks)
          uiStore.toast.success('Воспроизведение', `Играет: ${playlist.name}`)
        } else {
          uiStore.toast.info('Пусто', 'В плейлисте нет треков')
        }
      } catch (error) {
        console.error('Failed to play playlist:', error)
        uiStore.toast.error('Ошибка', 'Не удалось воспроизвести')
      }
      closeMenu()
    },

    shuffle: async (playlist) => {
      if (!playlist?.id) return closeMenu()
      
      try {
        const tracks = await loadPlaylistTracks(playlist)
        if (tracks?.length) {
          const shuffled = [...tracks].sort(() => Math.random() - 0.5)
          playerStore.play(shuffled[0], shuffled)
          uiStore.toast.success('Перемешивание', `Играет: ${playlist.name}`)
        }
      } catch (error) {
        console.error('Failed to shuffle playlist:', error)
        uiStore.toast.error('Ошибка', 'Не удалось воспроизвести')
      }
      closeMenu()
    },

    addToQueue: async (playlist) => {
      if (!playlist?.id) return closeMenu()
      
      try {
        const tracks = await loadPlaylistTracks(playlist)
        if (tracks?.length) {
          tracks.forEach(track => playerStore.addToQueue(track))
          uiStore.toast.success('Добавлено', `${tracks.length} треков в очереди`)
        }
      } catch (error) {
        console.error('Failed to add to queue:', error)
        uiStore.toast.error('Ошибка', 'Не удалось добавить в очередь')
      }
      closeMenu()
    },

    rename: (playlist) => {
      if (playlist?.is_auto_album) return closeMenu()
      
      closeMenu()
      editingItem.value = playlist
      renameValue.value = playlist?.name || ''
      showRenameModal.value = true
    },

    delete: async (playlist) => {
      if (!playlist?.id || playlist.is_auto_album) return closeMenu()
      
      if (confirm(`Удалить плейлист "${playlist.name}"?`)) {
        try {
          await playlistsApi.delete(playlist.id)
          await libraryStore.loadPlaylists()
          uiStore.toast.success('Удалено', `Плейлист "${playlist.name}" удалён`)
        } catch (error) {
          console.error('Failed to delete playlist:', error)
          uiStore.toast.error('Ошибка', 'Не удалось удалить плейлист')
        }
      }
      closeMenu()
    },
  }

  // ═══════════════════════════════════════════════════════════
  // ALBUM ACTIONS (similar to playlist but with album-specific logic)
  // ═══════════════════════════════════════════════════════════

  const albumActions = {
    open: (album) => {
      closeMenu()
      if (album?.id) {
        router.push(`/album/${album.id}`)
      }
    },

    playAll: async (album) => {
      if (!album?.id) return closeMenu()
      
      try {
        const response = await albumsApi.getOne(album.id)
        const tracks = response?.data?.tracks || []
        if (tracks.length) {
          playerStore.play(tracks[0], tracks)
          uiStore.toast.success('Воспроизведение', `Играет: ${album.name}`)
        } else {
          uiStore.toast.info('Пусто', 'В альбоме нет треков')
        }
      } catch (error) {
        console.error('Failed to play album:', error)
        uiStore.toast.error('Ошибка', 'Не удалось воспроизвести альбом')
      }
      closeMenu()
    },

    shuffle: async (album) => {
      if (!album?.id) return closeMenu()
      
      try {
        const response = await albumsApi.getOne(album.id)
        const tracks = response?.data?.tracks || []
        if (tracks.length) {
          const shuffled = [...tracks].sort(() => Math.random() - 0.5)
          playerStore.play(shuffled[0], shuffled)
          uiStore.toast.success('Перемешивание', `Играет: ${album.name}`)
        } else {
          uiStore.toast.info('Пусто', 'В альбоме нет треков')
        }
      } catch (error) {
        console.error('Failed to shuffle album:', error)
        uiStore.toast.error('Ошибка', 'Не удалось воспроизвести альбом')
      }
      closeMenu()
    },

    addToQueue: async (album) => {
      if (!album?.id) return closeMenu()
      
      try {
        const response = await albumsApi.getOne(album.id)
        const tracks = response?.data?.tracks || []
        if (tracks.length) {
          tracks.forEach(track => playerStore.addToQueue(track))
          uiStore.toast.success('Добавлено', `${tracks.length} треков в очереди`)
        } else {
          uiStore.toast.info('Пусто', 'В альбоме нет треков')
        }
      } catch (error) {
        console.error('Failed to add album to queue:', error)
        uiStore.toast.error('Ошибка', 'Не удалось добавить в очередь')
      }
      closeMenu()
    },

    goToArtist: (album) => {
      closeMenu()
      const artist = album?.album_artist || album?.artist
      if (artist) {
        router.push(`/artist/${encodeURIComponent(artist)}`)
      }
    },
  }

  // ═══════════════════════════════════════════════════════════
  // ARTIST ACTIONS
  // ═══════════════════════════════════════════════════════════

  const artistActions = {
    open: (artist) => {
      closeMenu()
      const name = typeof artist === 'string' ? artist : artist?.name
      if (name) {
        router.push(`/artist/${encodeURIComponent(name)}`)
      }
    },

    playAll: async (artist) => {
      const name = typeof artist === 'string' ? artist : artist?.name
      if (!name) return closeMenu()
      
      try {
        const response = await tracksApi.getArtistDetail(name)
        const tracks = response?.tracks || []
        if (tracks.length) {
          playerStore.play(tracks[0], tracks)
          uiStore.toast.success('Воспроизведение', `Играет: ${name}`)
        }
      } catch (error) {
        console.error('Failed to play artist:', error)
        uiStore.toast.error('Ошибка', 'Не удалось воспроизвести')
      }
      closeMenu()
    },

    shuffle: async (artist) => {
      const name = typeof artist === 'string' ? artist : artist?.name
      if (!name) return closeMenu()
      
      try {
        const response = await tracksApi.getArtistDetail(name)
        const tracks = response?.tracks || []
        if (tracks.length) {
          const shuffled = [...tracks].sort(() => Math.random() - 0.5)
          playerStore.play(shuffled[0], shuffled)
          uiStore.toast.success('Перемешивание', `Играет: ${name}`)
        }
      } catch (error) {
        console.error('Failed to shuffle artist:', error)
        uiStore.toast.error('Ошибка', 'Не удалось воспроизвести')
      }
      closeMenu()
    },

    addToQueue: async (artist) => {
      const name = typeof artist === 'string' ? artist : artist?.name
      if (!name) return closeMenu()
      
      try {
        const response = await tracksApi.getArtistDetail(name)
        const tracks = response?.tracks || []
        if (tracks.length) {
          tracks.forEach(track => playerStore.addToQueue(track))
          uiStore.toast.success('Добавлено', `${tracks.length} треков в очереди`)
        }
      } catch (error) {
        console.error('Failed to add artist to queue:', error)
        uiStore.toast.error('Ошибка', 'Не удалось добавить в очередь')
      }
      closeMenu()
    },
  }

  // ═══════════════════════════════════════════════════════════
  // MODAL HANDLERS
  // ═══════════════════════════════════════════════════════════

  const closePlaylistPicker = () => {
    showPlaylistPicker.value = false
    editingItem.value = null
  }

  const onPlaylistAdded = (playlist) => {
    closePlaylistPicker()
    uiStore.toast.success('Добавлено', `Трек добавлен в "${playlist.name}"`)
  }

  const closeEditModal = () => {
    showEditModal.value = false
    editingItem.value = null
  }

  const onTrackSaved = () => {
    closeEditModal()
    uiStore.toast.success('Сохранено', 'Трек обновлён')
  }

  const closeRenameModal = () => {
    showRenameModal.value = false
    editingItem.value = null
    renameValue.value = ''
  }

  const confirmRename = async () => {
    const playlist = editingItem.value
    if (!playlist?.id || !renameValue.value.trim()) return
    
    try {
      await playlistsApi.update(playlist.id, { name: renameValue.value.trim() })
      await libraryStore.loadPlaylists()
      uiStore.toast.success('Переименовано', renameValue.value.trim())
      closeRenameModal()
    } catch (error) {
      console.error('Failed to rename playlist:', error)
      uiStore.toast.error('Ошибка', 'Не удалось переименовать')
    }
  }

  // ═══════════════════════════════════════════════════════════
  // HELPERS
  // ═══════════════════════════════════════════════════════════

  const loadPlaylistTracks = async (playlist) => {
    if (!playlist?.id) return []
    
    try {
      if (playlist.is_auto_album) {
        const response = await albumsApi.getOne(playlist.id)
        return response?.data?.tracks || []
      } else {
        const response = await playlistsApi.getOne(playlist.id)
        return response?.data?.tracks || []
      }
    } catch (error) {
      console.error('Failed to load playlist tracks:', error)
      return []
    }
  }

  // ═══════════════════════════════════════════════════════════
  // UNIFIED ACTION DISPATCHER
  // ═══════════════════════════════════════════════════════════

  /**
   * Execute action based on current menu type
   * @param {string} action - Action name
   * @param {any} extra - Extra data for the action
   */
  const executeAction = (action, extra = null) => {
    const data = menuData.value
    const type = menuType.value

    switch (type) {
      case 'track':
        if (trackActions[action]) {
          trackActions[action](data, extra)
        }
        break
      case 'playlist':
        if (playlistActions[action]) {
          playlistActions[action](data, extra)
        }
        break
      case 'album':
        if (albumActions[action]) {
          albumActions[action](data, extra)
        }
        break
      case 'artist':
        if (artistActions[action]) {
          artistActions[action](data, extra)
        }
        break
      default:
        console.warn(`Unknown menu type: ${type}`)
        closeMenu()
    }
  }

  return {
    // Menu state (readonly outside)
    isOpen,
    menuType,
    menuData,
    menuContext,
    menuPosition,

    // Menu control
    openMenu,
    closeMenu,
    executeAction,

    // Direct action access (for ContextMenu component)
    trackActions,
    playlistActions,
    albumActions,
    artistActions,

    // Modal states
    showPlaylistPicker,
    showEditModal,
    showRenameModal,
    editingItem,
    renameValue,

    // Modal handlers
    closePlaylistPicker,
    onPlaylistAdded,
    closeEditModal,
    onTrackSaved,
    closeRenameModal,
    confirmRename,
  }
}
