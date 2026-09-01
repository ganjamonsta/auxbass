/**
 * Audio Cache IndexedDB Storage
 * Manages persistent storage for audio blobs with LRU eviction and storage statistics.
 */

const DB_NAME = 'tg_player_cache_v1'
const DB_VERSION = 1
const STORE_NAME = 'audio_tracks'

let _dbPromise = null

/**
 * Open or create the IndexedDB database
 */
export function openCacheDb() {
  if (_dbPromise) return _dbPromise

  _dbPromise = new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !window.indexedDB) {
      return reject(new Error('IndexedDB not supported'))
    }

    const request = indexedDB.open(DB_NAME, DB_VERSION)

    request.onupgradeneeded = (event) => {
      const db = event.target.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'track_id' })
        store.createIndex('last_accessed_at', 'last_accessed_at', { unique: false })
        store.createIndex('cached_at', 'cached_at', { unique: false })
      }
    }

    request.onsuccess = () => {
      resolve(request.result)
    }

    request.onerror = () => {
      _dbPromise = null
      reject(request.error || new Error('Failed to open IndexedDB'))
    }
  })

  return _dbPromise
}

/**
 * Request persistent storage to protect cache from browser auto-eviction (iOS/Safari/Android)
 */
export async function requestStoragePersistence() {
  if (typeof navigator !== 'undefined' && navigator.storage && navigator.storage.persist) {
    try {
      const isPersisted = await navigator.storage.persist()
      console.log(`[AudioCache] Storage persisted: ${isPersisted}`)
      return isPersisted
    } catch (e) {
      console.warn('[AudioCache] Failed to request storage persistence:', e)
    }
  }
  return false
}

/**
 * Check if a track is cached in IndexedDB
 * @param {number} trackId
 * @returns {Promise<boolean>}
 */
export async function hasCachedTrack(trackId) {
  if (!trackId) return false
  try {
    const db = await openCacheDb()
    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readonly')
      const store = tx.objectStore(STORE_NAME)
      const countReq = store.count(trackId)
      countReq.onsuccess = () => resolve(countReq.result > 0)
      countReq.onerror = () => resolve(false)
    })
  } catch (e) {
    return false
  }
}

/**
 * Retrieve cached audio track from IndexedDB and update last_accessed_at
 * @param {number} trackId
 * @returns {Promise<{ blob: Blob, blobUrl: string, size: number, metadata: Object } | null>}
 */
export async function getCachedTrack(trackId) {
  if (!trackId) return null
  try {
    const db = await openCacheDb()
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)
      const getReq = store.get(trackId)

      getReq.onsuccess = () => {
        const record = getReq.result
        if (!record || !record.blob) {
          resolve(null)
          return
        }

        // Update last accessed time for LRU tracking
        record.last_accessed_at = Date.now()
        store.put(record)

        const blobUrl = URL.createObjectURL(record.blob)
        resolve({
          blob: record.blob,
          blobUrl,
          size: record.size || record.blob.size,
          mimeType: record.mime_type,
          metadata: {
            title: record.title,
            artist: record.artist,
            album: record.album,
            duration: record.duration,
            cover_url: record.cover_url
          }
        })
      }

      getReq.onerror = () => {
        resolve(null)
      }
    })
  } catch (e) {
    console.error(`[AudioCache] Error getting cached track ${trackId}:`, e)
    return null
  }
}

/**
 * Save audio blob and track metadata to IndexedDB
 * @param {Object} track - track metadata
 * @param {Blob} blob - audio binary blob
 * @param {string} [mimeType]
 * @returns {Promise<boolean>}
 */
export async function saveTrackToCache(track, blob, mimeType = 'audio/mpeg') {
  if (!track || !track.id || !blob || blob.size === 0) return false

  try {
    const db = await openCacheDb()
    const now = Date.now()
    const record = {
      track_id: track.id,
      blob,
      size: blob.size,
      mime_type: mimeType || blob.type || 'audio/mpeg',
      cached_at: now,
      last_accessed_at: now,
      title: track.title || 'Без названия',
      artist: track.artist || '',
      album: track.album || '',
      duration: track.duration || 0,
      cover_url: track.cover_url || null
    }

    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)
      const putReq = store.put(record)

      putReq.onsuccess = () => {
        console.log(`[AudioCache] Saved track ${track.id} ("${track.title}") to cache (${(blob.size / 1024 / 1024).toFixed(1)} MB)`)
        resolve(true)
      }

      putReq.onerror = () => {
        console.warn(`[AudioCache] Failed to save track ${track.id}:`, putReq.error)
        resolve(false)
      }
    })
  } catch (e) {
    console.error(`[AudioCache] Save error for track ${track.id}:`, e)
    return false
  }
}

/**
 * Delete a single track from the cache
 * @param {number} trackId
 * @returns {Promise<boolean>}
 */
export async function deleteCachedTrack(trackId) {
  if (!trackId) return false
  try {
    const db = await openCacheDb()
    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)
      const delReq = store.delete(trackId)
      delReq.onsuccess = () => resolve(true)
      delReq.onerror = () => resolve(false)
    })
  } catch (e) {
    return false
  }
}

/**
 * Clear all cached audio files
 * @returns {Promise<boolean>}
 */
export async function clearAllCache() {
  try {
    const db = await openCacheDb()
    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)
      const clearReq = store.clear()
      clearReq.onsuccess = () => {
        console.log('[AudioCache] All cached audio cleared')
        resolve(true)
      }
      clearReq.onerror = () => resolve(false)
    })
  } catch (e) {
    console.error('[AudioCache] Clear cache error:', e)
    return false
  }
}

/**
 * Get cache statistics (total size, track count, browser quota)
 * @returns {Promise<{ totalBytes: number, trackCount: number, quotaBytes: number, usageBytes: number }>}
 */
export async function getCacheStats() {
  let totalBytes = 0
  let trackCount = 0

  try {
    const db = await openCacheDb()
    await new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readonly')
      const store = tx.objectStore(STORE_NAME)
      const cursorReq = store.openCursor()

      cursorReq.onsuccess = (e) => {
        const cursor = e.target.result
        if (cursor) {
          trackCount++
          totalBytes += cursor.value.size || (cursor.value.blob ? cursor.value.blob.size : 0)
          cursor.continue()
        } else {
          resolve()
        }
      }

      cursorReq.onerror = () => resolve()
    })
  } catch (e) {
    console.warn('[AudioCache] Error calculating cache stats:', e)
  }

  let quotaBytes = 0
  let usageBytes = 0
  if (typeof navigator !== 'undefined' && navigator.storage && navigator.storage.estimate) {
    try {
      const estimate = await navigator.storage.estimate()
      quotaBytes = estimate.quota || 0
      usageBytes = estimate.usage || 0
    } catch (_) {}
  }

  return {
    totalBytes,
    trackCount,
    quotaBytes,
    usageBytes
  }
}

/**
 * LRU Eviction: Remove oldest accessed tracks if total size exceeds maxBytes
 * @param {number} maxBytes - maximum allowed bytes (0 = unlimited)
 */
export async function evictOldTracksIfNeeded(maxBytes) {
  if (!maxBytes || maxBytes <= 0) return

  try {
    const stats = await getCacheStats()
    if (stats.totalBytes <= maxBytes) return

    const bytesToFree = stats.totalBytes - maxBytes
    console.log(`[AudioCache] Cache limit exceeded (${(stats.totalBytes / 1024 / 1024).toFixed(1)} MB > ${(maxBytes / 1024 / 1024).toFixed(1)} MB). Freeing ${(bytesToFree / 1024 / 1024).toFixed(1)} MB...`)

    const db = await openCacheDb()
    const entries = []

    await new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readonly')
      const store = tx.objectStore(STORE_NAME)
      const index = store.index('last_accessed_at')
      const req = index.openCursor(null, 'next') // ascending order (oldest first)

      req.onsuccess = (e) => {
        const cursor = e.target.result
        if (cursor) {
          entries.push({
            track_id: cursor.value.track_id,
            size: cursor.value.size || 0,
            last_accessed_at: cursor.value.last_accessed_at
          })
          cursor.continue()
        } else {
          resolve()
        }
      }

      req.onerror = () => resolve()
    })

    let freedBytes = 0
    const toDelete = []
    for (const entry of entries) {
      if (freedBytes >= bytesToFree) break
      toDelete.push(entry.track_id)
      freedBytes += entry.size
    }

    if (toDelete.length > 0) {
      await new Promise((resolve) => {
        const tx = db.transaction(STORE_NAME, 'readwrite')
        const store = tx.objectStore(STORE_NAME)
        for (const id of toDelete) {
          store.delete(id)
        }
        tx.oncomplete = () => {
          console.log(`[AudioCache] Evicted ${toDelete.length} oldest tracks, freed ${(freedBytes / 1024 / 1024).toFixed(1)} MB`)
          resolve()
        }
        tx.onerror = () => resolve()
      })
    }
  } catch (e) {
    console.error('[AudioCache] Eviction error:', e)
  }
}
