/**
 * Resolve Audio Source
 * Single source of truth for the priority cascade:
 *   1. Blob cache (instant)
 *   2. Preloaded Audio element (fast swap)
 *   3. Cached URL token (skip API call)
 *   4. Fresh URL from API
 *
 * Previously copy-pasted in play(), next(), prev(), resumeFromState() — ~600 LOC of duplication.
 */
import {
  getCachedAudio,
  getPreloadedAudio,
  getCachedUrl,
  setCachedUrl,
  deleteCachedUrl,
  deleteCachedAudio,
  clearPreloadAudio,
} from './playerCache'
import { getCachedTrack } from '../utils/audioCacheDb'

/**
 * @param {number|Object} trackOrId
 * @param {Function} getStreamUrl - playerApi.getStreamUrl (async)
 * @returns {Promise<Object>} resolved source descriptor
 *
 * Return shapes:
 *   { type: 'blob',       src: string, buffered: true }
 *   { type: 'preloaded',  audio: HTMLAudioElement }
 *   { type: 'cached-url', src: string }
 *   { type: 'fresh-url',  src: string, meta: object }
 *   { type: 'error',      reason: string }
 */
export async function resolveAudioSource(trackOrId, getStreamUrl) {
  const trackId = typeof trackOrId === 'object' && trackOrId !== null ? trackOrId.id : trackOrId
  const currentTrack = typeof trackOrId === 'object' ? trackOrId : null

  // === PRIORITY 1: Persistent IndexedDB Blob cache (instant offline playback) ===
  if (trackId) {
    const cached = await getCachedTrack(trackId)
    if (cached && cached.blobUrl) {
      const cachedDuration = cached.metadata?.duration || 0
      const trackDuration = currentTrack?.duration || 0

      // Self-healing check: detect if cached blob is a stale 30s preview chunk
      // 1. Cached record was explicitly marked as a chunk
      // 2. Or playing a full track (!currentTrack?.is_chunk) while cached duration is <= 35s and expected duration > 35s
      // 3. Or duration difference indicates a chunk vs full track
      // 4. Or cached size is very small (< 650KB) while expected track is a full song (> 45s)
      const isStaleChunk = cached.metadata?.is_chunk ||
        (currentTrack && !currentTrack.is_chunk && trackDuration > 35 && cachedDuration <= 35) ||
        (currentTrack && !currentTrack.is_chunk && trackDuration > 45 && cached.size < 650 * 1024) ||
        (currentTrack && !currentTrack.is_chunk && trackDuration && cachedDuration && (trackDuration - cachedDuration > 15))

      if (isStaleChunk && currentTrack && !currentTrack.is_chunk) {
        console.warn(`[Play] Evicting stale preview chunk from cache for track ${trackId} (cached: ${cachedDuration}s / ${(cached.size / 1024).toFixed(0)}KB, expected: ${trackDuration}s)`)
        await deleteCachedAudio(trackId)
        deleteCachedUrl(trackId)
      } else if (!currentTrack?.is_chunk) {
        console.log(`[Play] Using persistent blob cache for track ${trackId} - instant start`)
        return { type: 'blob', src: cached.blobUrl, buffered: true, isCached: true }
      }
    }
  }

  // === PRIORITY 2: Cached URL token (from prefetch/preload) ===
  const cachedUrl = getCachedUrl(trackId)
  if (cachedUrl && !currentTrack?.is_chunk) {
    console.log('[Play] Using cached URL token')
    return { type: 'cached-url', src: cachedUrl }
  }

  // If user is offline, do NOT make a failing network request!
  if (typeof navigator !== 'undefined' && !navigator.onLine) {
    console.log(`[Play] Device is offline and track ${trackId} is not cached in IndexedDB`)
    return {
      type: 'offline-unavailable',
      reason: 'Трек не сохранён для оффлайн-прослушивания'
    }
  }

  // === PRIORITY 3: Fresh URL from API ===
  try {
    console.log('[Play] Fetching new stream URL from API')
    const response = await getStreamUrl(trackId)
    const url = response.data.url
    setCachedUrl(trackId, url, response.data.expires_at)

    const meta = {}
    if (response.data.is_hd_available) {
      meta.hdInfo = {
        id: response.data.hd_track_id,
        title: response.data.hd_track_title
      }
    }

    return { type: 'fresh-url', src: url, meta }
  } catch (e) {
    return { type: 'error', reason: e.message || 'no-source', error: e }
  }
}
