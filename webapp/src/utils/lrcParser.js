/**
 * TG Player - LRC (Synchronized Lyrics) Parser and Utilities
 * 
 * Supports:
 * - Standard timestamp formats: [mm:ss.xx], [mm:ss.xxx], [mm:ss]
 * - Multi-timestamp lines: [00:12.00][00:18.50] Hello world
 * - Offset tags: [offset:+500] (in milliseconds)
 * - Binary search for fast real-time line tracking during playback
 */

/**
 * Parse a timestamp string like "01:23.45" or "83.45" into seconds (float).
 * @param {string} minSec 
 * @returns {number|null}
 */
export function parseTimestamp(minSec) {
  if (!minSec) return null
  const parts = minSec.split(':')
  if (parts.length === 2) {
    const minutes = parseFloat(parts[0])
    const seconds = parseFloat(parts[1])
    if (!isNaN(minutes) && !isNaN(seconds)) {
      return minutes * 60 + seconds
    }
  } else if (parts.length === 3) {
    const hours = parseFloat(parts[0])
    const minutes = parseFloat(parts[1])
    const seconds = parseFloat(parts[2])
    if (!isNaN(hours) && !isNaN(minutes) && !isNaN(seconds)) {
      return hours * 3600 + minutes * 60 + seconds
    }
  }
  return null
}

/**
 * Format seconds into mm:ss.xx
 * @param {number} seconds 
 * @returns {string}
 */
export function formatLrcTimestamp(seconds) {
  if (isNaN(seconds) || seconds < 0) seconds = 0
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  const mStr = String(m).padStart(2, '0')
  const sStr = s.toFixed(2).padStart(5, '0')
  return `[${mStr}:${sStr}]`
}

/**
 * Parse an LRC formatted string into an array of synced lines and metadata.
 * 
 * @param {string} lrcText 
 * @returns {{ lines: Array<{ time: number, text: string }>, offset: number, metadata: Object }}
 */
export function parseLrc(lrcText) {
  if (!lrcText || typeof lrcText !== 'string') {
    return { lines: [], offset: 0, metadata: {} }
  }

  const lines = []
  const metadata = {}
  let offset = 0

  const timeTagRegex = /\[(\d{1,3}:\d{2}(?:\.\d{1,3})?)\]/g
  const metaTagRegex = /^\[([a-zA-Z]+):(.*)\]$/

  const rawLines = lrcText.split(/\r?\n/)

  for (const rawLine of rawLines) {
    const trimmed = rawLine.trim()
    if (!trimmed) continue

    // Check for metadata tags like [offset:+500], [ti:Title], [ar:Artist]
    const metaMatch = trimmed.match(metaTagRegex)
    if (metaMatch && !trimmed.match(timeTagRegex)) {
      const key = metaMatch[1].toLowerCase()
      const value = metaMatch[2].trim()
      metadata[key] = value
      if (key === 'offset') {
        const parsedOffset = parseInt(value, 10)
        if (!isNaN(parsedOffset)) {
          offset = parsedOffset
        }
      }
      continue
    }

    // Extract all timestamps from the line
    const timestamps = []
    let match
    while ((match = timeTagRegex.exec(trimmed)) !== null) {
      const sec = parseTimestamp(match[1])
      if (sec !== null) {
        timestamps.push(sec)
      }
    }

    if (timestamps.length > 0) {
      // The lyrics text is whatever remains after stripping all [time] tags
      const text = trimmed.replace(timeTagRegex, '').trim()
      for (const time of timestamps) {
        lines.push({ time, text })
      }
    }
  }

  // Sort chronologically
  lines.sort((a, b) => a.time - b.time)

  return { lines, offset, metadata }
}

/**
 * Find the index of the currently active line for a given playback time.
 * Uses binary search for high performance (60fps updates).
 * 
 * @param {Array<{ time: number, text: string }>} lines 
 * @param {number} currentTime Current playback time in seconds
 * @param {number} [offsetMs=0] Additional user offset in milliseconds
 * @returns {number} Index of active line, or -1 if before first line
 */
export function getActiveLineIndex(lines, currentTime, offsetMs = 0) {
  if (!lines || lines.length === 0) return -1

  const adjustedTime = currentTime + (offsetMs / 1000)

  if (adjustedTime < lines[0].time) {
    return -1
  }

  let low = 0
  let high = lines.length - 1
  let result = 0

  while (low <= high) {
    const mid = (low + high) >> 1
    if (lines[mid].time <= adjustedTime) {
      result = mid
      low = mid + 1
    } else {
      high = mid - 1
    }
  }

  return result
}
