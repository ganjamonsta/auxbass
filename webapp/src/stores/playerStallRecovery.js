/**
 * Player Stall Recovery
 * Detects audio stalls and attempts recovery (reload / fresh URL).
 * Extracted from player.js to reduce god-object.
 */

const STALL_TIMEOUT = 10_000
const STALL_INITIAL_TIMEOUT = 15_000
const STALL_MAX_RETRIES = 2

let stallTimer = null
let stallRetryCount = 0

export function clearStallTimer() {
  if (stallTimer) {
    clearTimeout(stallTimer)
    stallTimer = null
  }
}

/**
 * Start the stall detection timer.
 * @param {boolean} initial - use longer timeout for initial load
 * @param {Function} onTimeout - callback when stall detected
 */
export function startStallTimer(initial, onTimeout) {
  clearStallTimer()
  const timeout = initial ? STALL_INITIAL_TIMEOUT : STALL_TIMEOUT
  stallTimer = setTimeout(onTimeout, timeout)
}

/**
 * Get / reset stall retry count.
 */
export function getStallRetryCount() { return stallRetryCount }
export function incrementStallRetry() { return ++stallRetryCount }
export function resetStallRetry() { stallRetryCount = 0 }

/**
 * Execute stall recovery logic.
 *
 * @param {Object} params
 * @param {HTMLAudioElement} params.audio
 * @param {Object} params.track - current track
 * @param {number} params.generation - play generation counter
 * @param {number} params.currentGeneration - current _playGeneration
 * @param {Function} params.getStreamUrl - playerApi.getStreamUrl
 * @param {Function} params.setCachedUrl
 * @param {Function} params.onRecovered - callback on successful recovery
 * @param {Function} params.onFailed - callback if all retries exhausted
 */
export async function handleStallTimeout({
  audio, track, generation, currentGeneration,
  getStreamUrl, setCachedUrl, onRecovered, onFailed
}) {
  if (!audio || !track) return

  // Already recovered?
  if (!audio.paused && audio.readyState >= 3) {
    resetStallRetry()
    return
  }

  const attempt = incrementStallRetry()
  console.warn(`[Stall Recovery] Audio stalled, attempt ${attempt}/${STALL_MAX_RETRIES}`)

  if (attempt <= STALL_MAX_RETRIES) {
    try {
      const currentTime = audio.currentTime
      const src = audio.src

      if (attempt === 1 && src) {
        // Attempt 1: reload at same position
        audio.load()
        audio.currentTime = currentTime
        await audio.play()
        if (generation !== currentGeneration) return
        onRecovered(track, attempt)
        return
      } else {
        // Attempt 2: fresh URL
        const response = await getStreamUrl(track.id)
        if (generation !== currentGeneration) return
        const newUrl = response.data.url
        setCachedUrl(track.id, newUrl, response.data.expires_at)
        audio.src = newUrl
        audio.currentTime = Math.max(0, currentTime - 0.5)
        await audio.play()
        onRecovered(track, attempt)
        return
      }
    } catch (e) {
      if (e.name === 'AbortError' || generation !== currentGeneration) return
      console.error('[Stall Recovery] Attempt failed:', e)
    }
  }

  if (generation !== currentGeneration) return
  onFailed(track)
}

// ============== Cascading Skip Protection ==============
let consecutiveSkipCount = 0
let lastSkipTime = 0
const MAX_CONSECUTIVE_SKIPS = 3
const SKIP_RESET_TIMEOUT = 5000

/**
 * Check if we should stop due to too many consecutive skips.
 * Returns true if cascade limit exceeded.
 */
export function checkCascadingSkips() {
  const now = Date.now()
  if (now - lastSkipTime < 2000) {
    consecutiveSkipCount++
  } else {
    consecutiveSkipCount = 1
  }
  lastSkipTime = now
  return consecutiveSkipCount > MAX_CONSECUTIVE_SKIPS
}

export function resetSkipCount() {
  consecutiveSkipCount = 0
}

export function getSkipCount() {
  return consecutiveSkipCount
}

// ============== Audio Error Retry ==============
const AUDIO_RETRY_DELAY = 1500
const MAX_AUDIO_RETRIES = 1
let audioRetryCount = 0

export function getAudioRetryCount() { return audioRetryCount }
export function incrementAudioRetry() { return ++audioRetryCount }
export function resetAudioRetry() { audioRetryCount = 0 }
export function getAudioRetryDelay() { return AUDIO_RETRY_DELAY }
export function getMaxAudioRetries() { return MAX_AUDIO_RETRIES }
