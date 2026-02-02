/**
 * Universal Playback Actions Composable
 * 
 * Provides common playback action handlers for detail views:
 * - playAll - play all tracks from the beginning
 * - shufflePlay - shuffle and play all tracks
 * 
 * Works with any reactive tracks source (ref, computed, or getter function)
 * 
 * Usage:
 *   const { playAll, shufflePlay } = usePlaybackActions(() => playlist.value.tracks)
 *   <button @click="playAll">Play</button>
 *   <button @click="shufflePlay">Shuffle</button>
 */
import { unref } from 'vue'
import { usePlayerStore } from '@/stores/player'

/**
 * @param {Ref<Array>|ComputedRef<Array>|Function} tracksSource - Tracks array, ref, or getter
 * @returns {Object} Playback action methods
 */
export function usePlaybackActions(tracksSource) {
  const playerStore = usePlayerStore()

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
   * Shuffle tracks and start playing
   */
  const shufflePlay = () => {
    const tracks = getTracks()
    if (tracks.length > 0) {
      const shuffled = [...tracks].sort(() => Math.random() - 0.5)
      playerStore.playTrack(shuffled[0], shuffled, 0)
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
    playTrack,
    hasTracks,
    getTracks,
  }
}

export default usePlaybackActions
