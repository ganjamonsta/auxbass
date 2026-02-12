/**
 * Universal Playback Actions Composable
 * 
 * Provides common playback action handlers for detail views:
 * - playAll - play all tracks from the beginning
 * - shufflePlay - shuffle and play all tracks (loaded only - for small lists)
 * - shufflePlayFull - shuffle with lazy loading via API (for large collections)
 * 
 * Works with any reactive tracks source (ref, computed, or getter function)
 * 
 * Usage:
 *   const { playAll, shufflePlay, shufflePlayFull } = usePlaybackActions(() => playlist.value.tracks)
 *   <button @click="playAll">Play</button>
 *   <button @click="shufflePlayFull('playlist', playlistId)">Shuffle</button>
 */
import { ref, unref } from 'vue'
import { usePlayerStore } from '@/stores/player'

/**
 * @param {Ref<Array>|ComputedRef<Array>|Function} tracksSource - Tracks array, ref, or getter
 * @returns {Object} Playback action methods
 */
export function usePlaybackActions(tracksSource) {
  const playerStore = usePlayerStore()
  
  // Loading state for shuffle operations
  const isShuffling = ref(false)

  /**
   * Get tracks array from source (handles ref, computed, and functions)
   * @returns {Array} Tracks array
   */
  const getTracks = () => {
    if (typeof tracksSource === 'function') {
      return tracksSource() || []
    }
    return unref(tracksSource) || []
  }

  /**
   * Play all tracks from the beginning
   */
  const playAll = () => {
    const tracks = getTracks()
    if (tracks.length > 0) {
      playerStore.playTrack(tracks[0], tracks, 0)
    }
  }

  /**
   * Shuffle currently loaded tracks and start playing
   * Use for small lists that are fully loaded (e.g., liked tracks)
   * For large collections, use shufflePlayFull instead
   */
  const shufflePlay = () => {
    const tracks = getTracks()
    if (tracks.length > 0) {
      // Fisher-Yates shuffle (unbiased)
      const shuffled = [...tracks]
      for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
      }
      playerStore.playTrack(shuffled[0], shuffled)
    }
  }

  /**
   * Shuffle play with full lazy loading support
   * Fetches all track IDs from server and plays with lazy loading
   * Use for large collections (playlists, albums, artists, library)
   * 
   * @param {'library'|'playlist'|'album'|'artist'} context - Type of collection
   * @param {number|string|null} contextId - ID for playlist/album, name for artist, null for library
   * @returns {Promise<void>}
   */
  const shufflePlayFull = async (context, contextId = null) => {
    if (isShuffling.value) return
    
    isShuffling.value = true
    try {
      await playerStore.playShuffleAll(context, contextId)
    } catch (error) {
      console.error(`[ShufflePlayFull] Failed to shuffle ${context}:`, error)
    } finally {
      isShuffling.value = false
    }
  }

  /**
   * Play specific track in context of all tracks
   * @param {Object} track - Track to play
   * @param {number} index - Optional index in tracks array
   */
  const playTrack = (track, index = -1) => {
    const tracks = getTracks()
    const trackIndex = index >= 0 ? index : tracks.findIndex(t => t.id === track.id)
    playerStore.playTrack(track, tracks, trackIndex >= 0 ? trackIndex : 0)
  }

  /**
   * Check if there are tracks available
   * @returns {boolean}
   */
  const hasTracks = () => {
    return getTracks().length > 0
  }

  return {
    playAll,
    shufflePlay,
    shufflePlayFull,
    isShuffling,
    playTrack,
    hasTracks,
    getTracks,
  }
}

export default usePlaybackActions
