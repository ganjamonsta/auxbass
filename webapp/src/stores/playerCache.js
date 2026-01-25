/**
 * Player Cache utilities
 * Handles URL caching and audio blob caching
 */

// ============== URL Cache for pre-generated tokens ==============
// Maps track_id -> { url, expires_at }
const urlCache = new Map()
const URL_CACHE_MARGIN = 60 // Refresh URL 60 seconds before expiry

/**
 * Get cached URL for a track
 */
export const getCachedUrl = (trackId) => {
  // Check local cache first
  let cached = urlCache.get(trackId)
  
  // Also check prefetched URLs from library.js (stored on window)
  if (!cached && window._prefetchedUrls) {
    cached = window._prefetchedUrls.get(trackId)
    if (cached) {
      // Move to local cache for consistency
      urlCache.set(trackId, cached)
      window._prefetchedUrls.delete(trackId)
      console.log(`[Cache] Using prefetched URL for track ${trackId}`)
    }
  }
  
  if (!cached) return null
  
  // Check if not expired (with margin)
  if (Date.now() / 1000 > cached.expires_at - URL_CACHE_MARGIN) {
    urlCache.delete(trackId)
    return null
  }
  
  // Validate URL format
  if (!cached.url || !cached.url.startsWith('/api/player/audio/')) {
    console.warn(`[Cache] Invalid cached URL for track ${trackId}, removing`)
    urlCache.delete(trackId)
    return null
  }
  
  return cached.url
}

/**
 * Cache URL for a track
 */
export const setCachedUrl = (trackId, url, expires_at) => {
  urlCache.set(trackId, { url, expires_at })
}

/**
 * Clear URL cache
 */
export const clearUrlCache = () => {
  urlCache.clear()
}


// ============== Audio Blob Cache ==============
// Stores blob URLs for already loaded tracks
const audioCache = new Map()
const MAX_CACHE_SIZE = 50

/**
 * Get cached audio blob URL
 */
export const getCachedAudio = (trackId) => {
  return audioCache.get(trackId)
}

/**
 * Cache audio blob URL with LRU eviction
 */
export const setCachedAudio = (trackId, blobUrl) => {
  // Limit cache size - use LRU-like eviction (remove oldest)
  if (audioCache.size >= MAX_CACHE_SIZE) {
    const firstKey = audioCache.keys().next().value
    const oldUrl = audioCache.get(firstKey)
    URL.revokeObjectURL(oldUrl)
    audioCache.delete(firstKey)
  }
  audioCache.set(trackId, blobUrl)
}

/**
 * Clear audio cache
 */
export const clearAudioCache = () => {
  audioCache.forEach((url) => URL.revokeObjectURL(url))
  audioCache.clear()
}


// ============== Preload Audio System ==============
// Use separate Audio element for preloading next track
let preloadAudio = null
let preloadTrackId = null

const getPreloadAudio = () => {
  if (!preloadAudio) {
    preloadAudio = new Audio()
    preloadAudio.preload = 'auto'
    preloadAudio.volume = 0 // Silent preload
  }
  return preloadAudio
}

/**
 * Start preloading a track
 */
export const preloadTrackWithAudio = (trackId, url) => {
  // Validate URL before preloading
  if (!url || url === '' || !url.startsWith('/api/player/audio/')) {
    console.warn(`[Preload] Invalid URL for track ${trackId}, skipping preload`)
    return
  }
  
  const audio = getPreloadAudio()
  
  // Clear any previous error state
  if (audio.error) {
    audio.src = ''
    audio.load()
  }
  
  preloadTrackId = trackId
  audio.src = url
  audio.load()
  
  // Add one-time error handler to detect failed preloads
  const errorHandler = () => {
    console.warn(`[Preload] Failed to preload track ${trackId}, marking as invalid`)
    preloadTrackId = null
    audio.removeEventListener('error', errorHandler)
  }
  audio.addEventListener('error', errorHandler, { once: true })
  
  console.log(`[Preload] Started preloading track ${trackId} with Audio element`)
}

/**
 * Get preloaded audio if available
 */
export const getPreloadedAudio = (trackId) => {
  if (preloadTrackId === trackId && preloadAudio && preloadAudio.src) {
    // Additional validation: check that audio is not in error state
    if (preloadAudio.error) {
      console.log(`[Preload] Audio for track ${trackId} has error, clearing`)
      clearPreloadAudio()
      return null
    }
    // Check src is not empty
    if (!preloadAudio.src || preloadAudio.src === '' || preloadAudio.src === window.location.href) {
      console.log(`[Preload] Audio for track ${trackId} has invalid src, clearing`)
      clearPreloadAudio()
      return null
    }
    return preloadAudio
  }
  return null
}

/**
 * Clear preload audio
 */
export const clearPreloadAudio = () => {
  if (preloadAudio) {
    preloadAudio.pause()
    preloadAudio.src = ''
    preloadTrackId = null
  }
}

/**
 * Get current preload track ID
 */
export const getPreloadTrackId = () => preloadTrackId
