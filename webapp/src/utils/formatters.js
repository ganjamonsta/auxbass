/**
 * TG Player - Shared Formatters
 * Common formatting functions used across components
 */

/**
 * Format duration in seconds to MM:SS or HH:MM:SS
 * @param {number|null} seconds - Duration in seconds
 * @returns {string} Formatted duration
 */
export function formatDuration(seconds) {
  if (!seconds) return '0:00'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

/**
 * Format duration in human-readable form
 * @param {number|null} seconds - Duration in seconds
 * @returns {string} Formatted duration (e.g., "1 ч 23 мин")
 */
export function formatDurationLong(seconds) {
  if (!seconds) return '0 мин'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 0) {
    return `${hours} ч ${minutes} мин`
  }
  return `${minutes} мин`
}

/**
 * Format file size in human-readable form
 * @param {number|null} bytes - File size in bytes
 * @returns {string} Formatted size
 */
export function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let unitIndex = 0
  let size = bytes
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

/**
 * Format play count in human-readable form
 * @param {number} count - Play count
 * @returns {string} Formatted count
 */
export function formatPlayCount(count) {
  if (!count) return '0'
  
  if (count >= 1000000) {
    return `${(count / 1000000).toFixed(1)}M`
  }
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}K`
  }
  return count.toString()
}

/**
 * Format date relative to now
 * @param {string|Date} date - Date to format
 * @returns {string} Relative date string
 */
export function formatRelativeDate(date) {
  if (!date) return ''
  
  const d = new Date(date)
  const now = new Date()
  const diffMs = now - d
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) return 'Сегодня'
  if (diffDays === 1) return 'Вчера'
  if (diffDays < 7) return `${diffDays} дн. назад`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} нед. назад`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} мес. назад`
  return `${Math.floor(diffDays / 365)} г. назад`
}

/**
 * Truncate text with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
export function truncateText(text, maxLength = 50) {
  if (!text || text.length <= maxLength) return text
  return text.substring(0, maxLength - 3) + '...'
}

/**
 * Split artist string into individual artists
 * Handles common separators: &, ,, +, x, and, with, feat., ft., featuring
 * 
 * Examples:
 *   "Excision & Downlink" -> ["Excision", "Downlink"]
 *   "Drake, Future" -> ["Drake", "Future"]
 *   "Artist feat. Other" -> ["Artist", "Other"]
 *   "A x B x C" -> ["A", "B", "C"]
 * 
 * @param {string} artistString - Artist string to split
 * @returns {Array<string>} Array of individual artist names
 */
export function splitArtists(artistString) {
  if (!artistString) return []
  
  // Normalize unicode characters
  let str = artistString
    .replace(/'/g, "'")
    .replace(/"/g, '"')
    .replace(/–/g, '-')
    .replace(/—/g, '-')
  
  // Split by common separators (order matters - more specific first)
  // Pattern: feat., ft., featuring, and, with, x, &, +, ,
  const separatorPattern = /\s*(?:,\s*|\s+&\s+|\s+\+\s+|\s+x\s+|\s+and\s+|\s+with\s+|\s+feat\.?\s+|\s+ft\.?\s+|\s+featuring\s+)/gi
  
  const parts = str.split(separatorPattern)
  
  // Clean up each part
  const artists = parts
    .map(part => part.trim())
    .filter(part => part.length > 0)
  
  // Remove duplicates while preserving order
  const seen = new Set()
  const unique = []
  for (const artist of artists) {
    const lower = artist.toLowerCase()
    if (!seen.has(lower)) {
      seen.add(lower)
      unique.push(artist)
    }
  }
  
  return unique
}

/**
 * Check if artist string contains multiple artists
 * @param {string} artistString - Artist string to check
 * @returns {boolean} True if contains multiple artists
 */
export function hasMultipleArtists(artistString) {
  if (!artistString) return false
  return splitArtists(artistString).length > 1
}

/**
 * Extract featured/remix/prod artists from track title
 * 
 * Examples:
 *   "Sleepless (Loadstar Remix)" -> ["Loadstar"]
 *   "Track feat. Artist1 & Artist2" -> ["Artist1", "Artist2"]
 *   "Song (Prod. Producer)" -> ["Producer"]
 *   "Battle vs. Other" -> ["Other"]
 * 
 * @param {string} title - Track title
 * @returns {Array<string>} Array of extracted artist names
 */
export function extractFeaturedArtists(title) {
  if (!title) return []
  
  const artists = []
  
  // Pattern for remix: "(Artist Remix)" or "(Artist's Remix)" or "[Artist Remix]"
  const remixPatterns = [
    /[\(\[]([^\)\]]+?)(?:'s)?\s+(?:Remix|Rmx|Mix|Edit|Bootleg|Rework|Flip|VIP)[\)\]]/gi,
    /\(Remix\s+by\s+([^\)]+)\)/gi,
    /\[Remix\s+by\s+([^\]]+)\]/gi,
  ]
  for (const pattern of remixPatterns) {
    let match
    while ((match = pattern.exec(title)) !== null) {
      const artist = match[1].trim()
      if (artist && artist.length > 1) {
        artists.push(artist)
      }
    }
  }
  
  // Pattern for feat.: "feat. Artist" or "ft. Artist"
  const featMatch = title.match(/(?:feat\.?|ft\.?|featuring)\s+([^\(\)\[\]]+?)(?:\s*[\(\[]|$)/i)
  if (featMatch) {
    const featPart = featMatch[1].trim()
    // Split by & , and
    const featArtists = featPart.split(/\s*(?:&|,|\band\b)\s*/i)
    for (const fa of featArtists) {
      const cleaned = fa.trim()
      if (cleaned && cleaned.length > 1) {
        artists.push(cleaned)
      }
    }
  }
  
  // Pattern for prod: "prod. Producer" or "(Prod. by Producer)"
  const prodPatterns = [
    /(?:prod\.?|produced\s+by)\s+([^\(\)\[\]]+?)(?:\s*[\(\[]|$)/gi,
    /[\(\[](?:prod\.?|produced\s+by)\s+([^\)\]]+)[\)\]]/gi,
  ]
  for (const pattern of prodPatterns) {
    let match
    while ((match = pattern.exec(title)) !== null) {
      const artist = match[1].trim()
      if (artist && artist.length > 1) {
        artists.push(artist)
      }
    }
  }
  
  // Pattern for vs: "vs. Artist" or "vs Artist"
  const vsMatch = title.match(/\bvs\.?\s+([^\(\)\[\]]+?)(?:\s*[\(\[]|$)/i)
  if (vsMatch) {
    const artist = vsMatch[1].trim()
    if (artist && artist.length > 1) {
      artists.push(artist)
    }
  }
  
  // Remove duplicates
  const seen = new Set()
  const unique = []
  for (const a of artists) {
    const lower = a.toLowerCase()
    if (!seen.has(lower)) {
      seen.add(lower)
      unique.push(a)
    }
  }
  
  return unique
}

/**
 * Get all artists from track (from artist field + extracted from title)
 * 
 * @param {string} artistString - Artist field value
 * @param {string} title - Track title (optional)
 * @returns {Array<string>} Array of all unique artist names
 */
export function getAllTrackArtists(artistString, title = null) {
  const fromArtist = splitArtists(artistString)
  const fromTitle = title ? extractFeaturedArtists(title) : []
  
  // Combine and deduplicate
  const seen = new Set()
  const unique = []
  
  for (const artist of [...fromArtist, ...fromTitle]) {
    const lower = artist.toLowerCase()
    if (!seen.has(lower)) {
      seen.add(lower)
      unique.push(artist)
    }
  }
  
  return unique
}

/**
 * Get display title for a track
 * Falls back to filename (without extension) when title is missing or placeholder
 * 
 * @param {Object} track - Track object with title and file_name properties
 * @returns {string} Display title
 */
export function getDisplayTitle(track) {
  if (!track) return 'Без названия'
  
  // Use title if it's not a placeholder
  if (track.title && track.title !== 'Без названия') {
    return track.title
  }
  
  // Fallback to filename without extension
  if (track.file_name) {
    const lastDot = track.file_name.lastIndexOf('.')
    const name = lastDot > 0 ? track.file_name.substring(0, lastDot) : track.file_name
    if (name.trim()) {
      return name.trim()
    }
  }
  
  return 'Без названия'
}

/**
 * Get display artist for a track
 * @param {Object} track - Track object with artist property
 * @returns {string} Display artist
 */
export function getDisplayArtist(track) {
  if (!track) return 'Неизвестный исполнитель'
  return track.artist || 'Неизвестный исполнитель'
}
