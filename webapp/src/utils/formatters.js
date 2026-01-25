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
