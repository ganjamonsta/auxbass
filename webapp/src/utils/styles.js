/**
 * TG Player - Style Utilities
 * Common style generation functions
 */

import { getDisplayTitle } from './formatters'

/**
 * Generate gradient style for artist avatar based on name
 * @param {string} name - Artist name
 * @param {object|null} cachedImage - Cached artist image URL
 * @returns {object} Style object
 */
export function getArtistAvatarStyle(name, cachedImage = null) {
  if (cachedImage) return {}
  
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue1 = Math.abs(hash % 360)
  const hue2 = (hue1 + 40) % 360
  
  return {
    background: `linear-gradient(135deg, hsl(${hue1}, 60%, 45%) 0%, hsl(${hue2}, 50%, 35%) 100%)`
  }
}

/**
 * Get initials for artist avatar
 * @param {string} name - Artist name
 * @returns {string} 1-2 character initials
 */
export function getArtistInitials(name) {
  if (!name) return '?'
  const words = name.split(' ').filter(w => w.length > 0)
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

/**
 * Genre color mappings for consistent styling
 */
const GENRE_COLORS = {
  'Rock': { h1: 0, h2: 30 },
  'Pop': { h1: 300, h2: 330 },
  'Hip-Hop': { h1: 40, h2: 60 },
  'Rap': { h1: 35, h2: 55 },
  'Electronic': { h1: 180, h2: 220 },
  'Dance': { h1: 280, h2: 320 },
  'House': { h1: 200, h2: 240 },
  'Techno': { h1: 260, h2: 290 },
  'Dubstep': { h1: 270, h2: 300 },
  'Drum and Bass': { h1: 15, h2: 45 },
  'Jazz': { h1: 45, h2: 70 },
  'Classical': { h1: 220, h2: 250 },
  'Metal': { h1: 0, h2: 20 },
  'R&B': { h1: 320, h2: 350 },
  'Soul': { h1: 30, h2: 50 },
  'Country': { h1: 35, h2: 55 },
  'Reggae': { h1: 100, h2: 140 },
  'Blues': { h1: 210, h2: 240 },
  'Indie': { h1: 150, h2: 180 },
  'Alternative': { h1: 160, h2: 190 },
}

/**
 * Generate gradient style for genre card
 * @param {string} genre - Genre name
 * @returns {object} Style object with background gradient
 */
export function getGenreStyle(genre) {
  const found = Object.entries(GENRE_COLORS).find(([key]) => 
    genre.toLowerCase().includes(key.toLowerCase())
  )
  
  let hue1, hue2
  if (found) {
    hue1 = found[1].h1
    hue2 = found[1].h2
  } else {
    // Generate from name hash
    let hash = 0
    for (let i = 0; i < genre.length; i++) {
      hash = genre.charCodeAt(i) + ((hash << 5) - hash)
    }
    hue1 = Math.abs(hash % 360)
    hue2 = (hue1 + 40) % 360
  }
  
  return {
    background: `linear-gradient(135deg, hsl(${hue1}, 70%, 40%) 0%, hsl(${hue2}, 60%, 30%) 100%)`
  }
}

/**
 * Generate cover style for track card
 * @param {object} track - Track object
 * @returns {object} Style object
 */
export function getTrackCoverStyle(track) {
  if (track.cover_url) return {}
  
  const title = getDisplayTitle(track)
  const str = title + (track.artist || '')
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue1 = Math.abs(hash % 360)
  const hue2 = (hue1 + 45) % 360
  
  return {
    background: `linear-gradient(135deg, hsl(${hue1}, 55%, 40%) 0%, hsl(${hue2}, 45%, 30%) 100%)`
  }
}

/**
 * Get track initials for placeholder
 * @param {object} track - Track object
 * @returns {string} 1-2 character initials
 */
export function getTrackInitials(track) {
  const title = getDisplayTitle(track)
  const words = title.split(' ').filter(w => w.length > 0)
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }
  return title.substring(0, 2).toUpperCase()
}
