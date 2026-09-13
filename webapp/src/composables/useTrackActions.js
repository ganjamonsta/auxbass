/**
 * Universal Track Actions Composable
 * 
 * Provides common track action handlers used across all views:
 * - handleDirectDownload - download HD/large tracks via Telegram
 * - handleHdNotice - show notice for HD-only tracks
 * - handleLikeTrack - toggle track like status
 * - handleAddToLibrary - add track to user's library
 * 
 * Usage:
 *   const { handleDirectDownload, handleHdNotice, handleLikeTrack, handleAddToLibrary } = useTrackActions()
 *   <TrackItem @download="handleDirectDownload(track)" @hdNotice="handleHdNotice" ... />
 */
import { useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { playerApi, albumsApi } from '@/api/client'

export function useTrackActions() {
  const router = useRouter()
  const libraryStore = useLibraryStore()
  const uiStore = useUIStore()
  const authStore = useAuthStore()

  /**
   * Handle direct download for large/HD files
   * Sends track to user's Telegram
   * @param {Object} track - Track object with id
   */
  const handleDirectDownload = async (track) => {
    if (!track?.id) return
    
    try {
      await playerApi.download(track.id)
      uiStore.toast.success('Трек отправлен', 'Проверьте сообщения в Telegram')
    } catch (error) {
      console.error('Failed to download track:', error)
      const errorMsg = error.response?.data?.detail || 'Ошибка отправки'
      uiStore.toast.error('Не удалось отправить', errorMsg)
    }
  }

  /**
   * Show notice that track is HD-only (not streamable)
   * @param {Object} track - Track object with file_size
   */
  const handleHdNotice = (track) => {
    const sizeMB = track?.file_size 
      ? (track.file_size / 1024 / 1024).toFixed(1) 
      : '20+'
    uiStore.toast.info(
      'Только HD', 
      `Этот трек (${sizeMB} MB) доступен только для скачивания. Используйте кнопку загрузки.`
    )
  }

  /**
   * Toggle track like status
   * @param {Object} track - Track object with id and is_liked
   * @returns {Promise<boolean>} New liked state
   */
  const handleLikeTrack = async (track) => {
    if (!track?.id) return false
    
    if (!authStore.requireChannel('сохранения в любимые треки')) {
      return track.is_liked === true
    }

    const current = track.is_liked === true
    track.is_liked = !current
    const newLikedState = await libraryStore.toggleLike(track.id, current)
    // Update track object if mutable
    if (track && typeof track === 'object') {
      track.is_liked = newLikedState
    }
    return newLikedState
  }

  /**
   * Add track to user's library (for global/friends tracks)
   * @param {Object} track - Track object with id
   * @returns {Promise<boolean>} Success status
   */
  const handleAddToLibrary = async (track) => {
    if (!track?.id) return false
    
    if (!authStore.requireChannel('добавления в медиатеку')) {
      return false
    }

    const success = await libraryStore.addToLibrary(track.id)
    if (success && track && typeof track === 'object') {
      track.in_library = true
    }
    return success
  }

  /**
   * Navigate to album page, resolving or creating the album if needed
   * @param {Object} track - Track object
   */
  const goToTrackAlbum = async (track) => {
    if (!track) return
    const albumId = track.album_id || track.album?.id
    if (albumId) {
      router.push(`/album/${albumId}`)
      return
    }

    const albumName = track.album?.name || track.album_name || (typeof track.album === 'string' ? track.album : null)
    if (track.id || albumName) {
      try {
        const res = await albumsApi.resolve({
          track_id: track.id,
          album_name: albumName,
          artist: track.artist
        })
        if (res?.data?.album_id) {
          router.push(`/album/${res.data.album_id}`)
        } else {
          uiStore.toast.info('Альбом', 'Альбом не найден')
        }
      } catch (err) {
        console.error('Failed to resolve album:', err)
        uiStore.toast.error('Ошибка', 'Не удалось открыть альбом')
      }
    }
  }

  return {
    handleDirectDownload,
    handleHdNotice,
    handleLikeTrack,
    handleAddToLibrary,
    goToTrackAlbum,
  }
}

export default useTrackActions
