/**
 * Universal Playback Actions Composable
 * 
 * Provides common playback action handlers for detail views:
 * - playAll / togglePlay - toggles playback if active, or plays all tracks from beginning
 * - restartAll - restart all tracks from the beginning
 * - shufflePlay - shuffle and play all tracks (loaded only - for small lists)
 * - shufflePlayFull - shuffle with lazy loading via API (for large collections)
 * - isPlaying - boolean ref indicating if this context is currently playing
 * - isCurrentContext - boolean ref indicating if this context is the active playback context
 * - playButtonTitle - 'Пауза' | 'Продолжить' | 'Слушать все'
 * 
 * Works with any reactive tracks source (ref, computed, or getter function)
 */
import { ref, unref, computed } from 'vue'
import { usePlayerStore } from '@/stores/player'

/**
 * @param {Ref<Array>|ComputedRef<Array>|Function} tracksSource - Tracks array, ref, or getter
 * @param {Ref<Object>|ComputedRef<Object>|Function|Object} contextSource - Optional context (e.g. { type: 'playlist', id, name })
 * @returns {Object} Playback action methods and reactive state
 */
export function usePlaybackActions(tracksSource, contextSource = null) {
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
   * Get playback context if available
   */
  const getContext = () => {
    if (typeof contextSource === 'function') {
      return contextSource() || null
    }
    return unref(contextSource) || null
  }

  /**
   * Check if this collection/context is the active playback context
   */
  const isCurrentContext = computed(() => {
    const ctx = getContext()
    const currentTrack = playerStore.currentTrack
    if (!currentTrack) return false

    const playCtx = playerStore.playbackContext
    const lazyCtx = playerStore.lazyShuffleContext

    // 1. If explicit contextSource was provided (e.g. { type: 'album', id: 42 })
    if (ctx && ctx.type) {
      // Check lazy shuffle context
      if (lazyCtx && lazyCtx.type === ctx.type) {
        if (ctx.id !== undefined && ctx.id !== null) {
          if (String(lazyCtx.id) === String(ctx.id)) return true
        } else if (ctx.name && lazyCtx.name === ctx.name) {
          return true
        } else if (!ctx.id && !ctx.name) {
          return true
        }
      }

      // Check playbackContext
      if (playCtx && playCtx.type === ctx.type) {
        if (ctx.id !== undefined && ctx.id !== null) {
          if (String(playCtx.id) === String(ctx.id)) return true
        } else if (ctx.name && playCtx.name === ctx.name) {
          return true
        } else if (!ctx.id && !ctx.name) {
          return true
        }
      }

      // If active context belongs to a different context, then this is not active
      if (playCtx && playCtx.type && playCtx.type !== ctx.type) {
        return false
      }
      if (playCtx && playCtx.type === ctx.type && ctx.id && playCtx.id && String(playCtx.id) !== String(ctx.id)) {
        return false
      }
      if (lazyCtx && lazyCtx.type && lazyCtx.type !== ctx.type) {
        return false
      }
      if (lazyCtx && lazyCtx.type === ctx.type && ctx.id && lazyCtx.id && String(lazyCtx.id) !== String(ctx.id)) {
        return false
      }
    }

    // 2. Fallback matching: currentTrack in collection tracks (when no conflicting context)
    if (ctx?.type === 'album') {
      const trackAlbumId = currentTrack.album_id || currentTrack.album?.id
      if (ctx.id && trackAlbumId && String(trackAlbumId) === String(ctx.id)) {
        return true
      }
    }

    const tracks = getTracks()
    if (tracks && tracks.length > 0) {
      return tracks.some(t => {
        if (!t) return false
        const id = t.id || t.track_id || t.track?.id
        return id === currentTrack.id
      })
    }

    return false
  })

  /**
   * Whether this collection is actively playing right now
   */
  const isPlaying = computed(() => {
    return playerStore.isPlaying && isCurrentContext.value
  })

  /**
   * Tooltip / title for play/pause button
   */
  const playButtonTitle = computed(() => {
    if (isPlaying.value) return 'Пауза'
    if (isCurrentContext.value) return 'Продолжить'
    return 'Слушать все'
  })

  /**
   * Restart playback from the beginning
   */
  const restartAll = (overrideContext = null) => {
    const tracks = getTracks()
    if (tracks.length > 0) {
      const firstItem = tracks.find(t => t && (t.id || t.track))
      const trackToPlay = firstItem?.track || firstItem || tracks[0]
      const queueToPlay = tracks.filter(t => t && (t.id || t.track)).map(t => t.track || t)
      playerStore.playTrack(trackToPlay, queueToPlay.length ? queueToPlay : tracks, overrideContext || getContext())
    }
  }

  /**
   * Toggle playback:
   * - If this collection is currently active, toggle player play/pause
   * - Otherwise start playback from beginning
   */
  const togglePlay = (overrideContext = null) => {
    if (isCurrentContext.value) {
      playerStore.togglePlay()
    } else {
      restartAll(overrideContext)
    }
  }

  // playAll defaults to togglePlay behavior
  const playAll = togglePlay

  /**
   * Shuffle currently loaded tracks and start playing
   * Use for small lists that are fully loaded (e.g., liked tracks)
   * For large collections, use shufflePlayFull instead
   */
  const shufflePlay = () => {
    const tracks = getTracks()
    if (tracks.length > 0) {
      const flatTracks = tracks.filter(t => t && (t.id || t.track)).map(t => t.track || t)
      // Fisher-Yates shuffle (unbiased)
      const shuffled = [...flatTracks]
      for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
      }
      playerStore.playTrack(shuffled[0], shuffled, getContext())
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
  const shufflePlayFull = async (context, contextId = null, options = {}) => {
    if (isShuffling.value) return
    
    isShuffling.value = true
    try {
      await playerStore.playShuffleAll(context, contextId, null, options)
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
   * @param {Object} overrideContext - Optional context override
   */
  const playTrack = (track, index = -1, overrideContext = null) => {
    const tracks = getTracks()
    const flatTracks = tracks.filter(t => t && (t.id || t.track)).map(t => t.track || t)
    playerStore.playTrack(track, flatTracks.length ? flatTracks : tracks, overrideContext || getContext())
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
    togglePlay,
    restartAll,
    isPlaying,
    isCurrentContext,
    playButtonTitle,
    shufflePlay,
    shufflePlayFull,
    isShuffling,
    playTrack,
    hasTracks,
    getTracks,
  }
}

export default usePlaybackActions
