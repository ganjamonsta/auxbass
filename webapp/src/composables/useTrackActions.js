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
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import { playerApi } from '@/api/client'

export function useTrackActions() {
  const libraryStore = useLibraryStore()
  const uiStore = useUIStore()

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
    
    const newLikedState = await libraryStore.toggleLike(track.id)
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
    
    const success = await libraryStore.addToLibrary(track.id)
    if (success && track && typeof track === 'object') {
      track.in_library = true
    }
    return success
  }

  return {
    handleDirectDownload,
    handleHdNotice,
    handleLikeTrack,
    handleAddToLibrary,
  }
}

export default useTrackActions
