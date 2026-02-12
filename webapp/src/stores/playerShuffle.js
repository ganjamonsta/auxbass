/**
 * Player Shuffle Module
 * Fisher-Yates shuffle order generation + lazy-shuffle helpers.
 * Extracted from player.js to reduce god-object.
 */

/**
 * Generate a Fisher-Yates shuffle order for a queue.
 *
 * @param {number} length - queue length
 * @param {number} [startingIndex=-1] - index to place first (current track)
 * @returns {{ order: number[], index: number }} shuffled indices + start index
 */
export function generateShuffleOrder(length, startingIndex = -1) {
  if (length === 0) return { order: [], index: -1 }

  const indices = Array.from({ length }, (_, i) => i)

  // Fisher-Yates (unbiased)
  for (let i = indices.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[indices[i], indices[j]] = [indices[j], indices[i]]
  }

  // Move starting track to front so current track plays first
  if (startingIndex >= 0 && startingIndex < length) {
    const pos = indices.indexOf(startingIndex)
    if (pos > 0) {
      indices.splice(pos, 1)
      indices.unshift(startingIndex)
    }
  }

  return { order: indices, index: 0 }
}

/**
 * Get the next queue index considering shuffle / normal order.
 *
 * @param {Object} state - reactive refs snapshot
 * @param {boolean} state.shuffle
 * @param {number[]} state.shuffleOrder
 * @param {number} state.shuffleIndex
 * @param {number} state.queueIndex
 * @param {number} state.queueLength
 * @param {string} state.repeat - 'none'|'one'|'all'
 * @returns {number} next queue index, or -1 if end
 */
export function getNextTrackIndex({ shuffle, shuffleOrder, shuffleIndex, queueIndex, queueLength, repeat }) {
  if (shuffle && shuffleOrder.length > 0) {
    const next = shuffleIndex + 1
    if (next >= shuffleOrder.length) {
      return repeat === 'all' ? shuffleOrder[0] : -1
    }
    return shuffleOrder[next]
  }
  const next = queueIndex + 1
  if (next >= queueLength) {
    return repeat === 'all' ? 0 : -1
  }
  return next
}

/**
 * Get next track ID in lazy shuffle mode.
 */
export function getNextLazyShuffleTrackId(ids, currentIndex, repeat) {
  if (!ids.length || currentIndex < 0) return null
  const next = currentIndex + 1
  if (next >= ids.length) {
    return repeat === 'all' ? ids[0] : null
  }
  return ids[next]
}

/**
 * Get previous track ID in lazy shuffle mode.
 */
export function getPrevLazyShuffleTrackId(ids, currentIndex, repeat) {
  if (!ids.length || currentIndex < 0) return null
  const prev = currentIndex - 1
  if (prev < 0) {
    return repeat === 'all' ? ids[ids.length - 1] : null
  }
  return ids[prev]
}
