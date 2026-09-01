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
  clearPreloadAudio,
} from './playerCache'

/**
 * @param {number} trackId
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
export async function resolveAudioSource(trackId, getStreamUrl) {
  // === PRIORITY 1: Blob cache (fully downloaded) ===
  const blobUrl = getCachedAudio(trackId)
  if (blobUrl) {
    console.log('[Play] Using blob cache - instant start')
    return { type: 'blob', src: blobUrl, buffered: true }
  }

  // === PRIORITY 2: Cached URL token (from prefetch/preload) ===
  const cachedUrl = getCachedUrl(trackId)
  if (cachedUrl) {
    console.log('[Play] Using cached URL token')
    return { type: 'cached-url', src: cachedUrl }
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
