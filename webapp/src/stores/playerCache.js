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

/**
 * Delete a single URL from cache
 */
export const deleteCachedUrl = (trackId) => {
  urlCache.delete(trackId)
}


import {
  getCachedTrack,
  saveTrackToCache,
  deleteCachedTrack,
  clearAllCache,
  hasCachedTrack
} from '../utils/audioCacheDb'

// ============== Audio Blob Cache (IndexedDB-backed) ==============
// Tracks active Blob URLs to revoke on cleanup/replacement
const _activeBlobUrls = new Map()

/**
 * Get cached audio blob URL from persistent IndexedDB
 * @param {number} trackId
 * @returns {Promise<string|null>}
 */
export const getCachedAudio = async (trackId) => {
  if (!trackId) return null
  const cached = await getCachedTrack(trackId)
  if (!cached || !cached.blobUrl) return null

  // Revoke previous blob URL if exists for this track
  const oldUrl = _activeBlobUrls.get(trackId)
  if (oldUrl && oldUrl !== cached.blobUrl) {
    URL.revokeObjectURL(oldUrl)
  }
  _activeBlobUrls.set(trackId, cached.blobUrl)
  return cached.blobUrl
}

/**
 * Cache audio blob in IndexedDB
 * @param {Object} track
 * @param {Blob} blob
 * @param {string} [mimeType]
 */
export const setCachedAudio = async (track, blob, mimeType) => {
  if (!track || !blob) return false
  return await saveTrackToCache(track, blob, mimeType)
}

/**
 * Delete a single audio blob from persistent cache
 * @param {number} trackId
 */
export const deleteCachedAudio = async (trackId) => {
  const url = _activeBlobUrls.get(trackId)
  if (url) {
    URL.revokeObjectURL(url)
    _activeBlobUrls.delete(trackId)
  }
  return await deleteCachedTrack(trackId)
}

/**
 * Clear all cached audio files
 */
export const clearAudioCache = async () => {
  _activeBlobUrls.forEach((url) => URL.revokeObjectURL(url))
  _activeBlobUrls.clear()
  return await clearAllCache()
}


// ============== Preload Audio System ==============
// Use separate Audio element for preloading next track
let preloadAudio = null
let preloadTrackId = null

const getPreloadAudio = () => {
  if (!preloadAudio) {
    preloadAudio = new Audio()
    preloadAudio.crossOrigin = 'anonymous'
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
  
  // Clear any previous state completely
  audio.pause()
  audio.src = ''
  
  // Small delay to ensure the old audio is fully cleared
  // This prevents race conditions with readyState from previous track
  preloadTrackId = null
  
  // Set the new track
  preloadTrackId = trackId
  audio.src = url
  audio.load()
  
  // Add error handler to detect failed preloads
  const errorHandler = () => {
    console.warn(`[Preload] Failed to preload track ${trackId}, marking as invalid`)
    // Only clear if this is still the same track being preloaded
    if (preloadTrackId === trackId) {
      preloadTrackId = null
    }
    audio.removeEventListener('error', errorHandler)
  }
  audio.addEventListener('error', errorHandler, { once: true })
  
  console.log(`[Preload] Started preloading track ${trackId} with Audio element`)
}

/**
 * Get preloaded audio if available and ready
 */
export const getPreloadedAudio = (trackId) => {
  // First check if track IDs match
  if (preloadTrackId !== trackId) {
    if (preloadTrackId !== null) {
      console.log(`[Preload] Requested track ${trackId} but preloaded is ${preloadTrackId}, ignoring`)
    }
    return null
  }
  
  if (!preloadAudio || !preloadAudio.src) {
    return null
  }
  
  // Check that audio is not in error state
  if (preloadAudio.error) {
    console.log(`[Preload] Audio for track ${trackId} has error, clearing`)
    clearPreloadAudio()
    return null
  }
  
  // Check networkState - NETWORK_NO_SOURCE (3) means load failed
  // NETWORK_EMPTY (0) means not initialized
  if (preloadAudio.networkState === 3 || preloadAudio.networkState === 0) {
    console.log(`[Preload] Audio for track ${trackId} has bad networkState: ${preloadAudio.networkState}, clearing`)
    clearPreloadAudio()
    return null
  }
  
  // Check src is not empty or default
  if (!preloadAudio.src || preloadAudio.src === '' || preloadAudio.src === window.location.href) {
    console.log(`[Preload] Audio for track ${trackId} has invalid src, clearing`)
    clearPreloadAudio()
    return null
  }
  
  // Verify src contains valid audio token path
  if (!preloadAudio.src.includes('/api/player/audio/')) {
    console.log(`[Preload] Audio for track ${trackId} has wrong src format, clearing`)
    clearPreloadAudio()
    return null
  }
  
  // Verify that audio has actually started loading (duration > 0 or readyState >= 1)
  // This prevents using stale readyState from a previous track
  if (preloadAudio.readyState < 1 && !isFinite(preloadAudio.duration)) {
    console.log(`[Preload] Audio for track ${trackId} not ready yet (readyState=${preloadAudio.readyState})`)
    return null
  }
  
  console.log(`[Preload] Returning preloaded audio for track ${trackId} (readyState=${preloadAudio.readyState}, networkState=${preloadAudio.networkState})`)
  return preloadAudio
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

/**
 * Recycle an audio element for preloading (reuse old audio after swap)
 */
export const recyclePreloadAudio = (audioElement) => {
  if (preloadAudio) {
    preloadAudio.pause()
    preloadAudio.src = ''
  }
  preloadAudio = audioElement || new Audio()
  preloadAudio.preload = 'auto'
  preloadAudio.volume = 0
  preloadTrackId = null
}
