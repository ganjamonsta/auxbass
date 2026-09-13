/**
 * Profile shared utilities — word declension, initials, job subtext.
 */

/**
 * Russian declension for "трек/трека/треков"
 */
export const getTracksWord = (count) => {
  const c = count || 0
  const mod10 = c % 10
  const mod100 = c % 100
  if (mod100 >= 11 && mod100 <= 14) return 'треков'
  if (mod10 === 1) return 'трек'
  if (mod10 >= 2 && mod10 <= 4) return 'трека'
  return 'треков'
}

/**
 * Russian declension for "плейлист/плейлиста/плейлистов"
 */
export const getPlaylistsWord = (count) => {
  const c = count || 0
  const mod10 = c % 10
  const mod100 = c % 100
  if (mod100 >= 11 && mod100 <= 14) return 'плейлистов'
  if (mod10 === 1) return 'плейлист'
  if (mod10 >= 2 && mod10 <= 4) return 'плейлиста'
  return 'плейлистов'
}

/**
 * Get initials from a user object, with self-user fallback via authStore.
 */
export const getInitials = (user, isSelf, authStore) => {
  if (isSelf && authStore?.userDisplayName) {
    return authStore.userDisplayName.charAt(0).toUpperCase()
  }
  if (!user) return '?'
  if (user.custom_nickname) return user.custom_nickname.charAt(0).toUpperCase()
  if (user.first_name) return user.first_name.charAt(0).toUpperCase()
  if (user.display_name) return user.display_name.charAt(0).toUpperCase()
  if (user.username) return user.username.charAt(0).toUpperCase()
  return '?'
}

/**
 * Format subtext for an import/ingestion job card.
 */
export const subtextFor = (job) => {
  if (!job) return ''
  if (job.status === 'completed') return job.current_step || 'Импорт завершён'
  if (job.status === 'failed') return job.error_message || 'Ошибка'
  if (job.status === 'cancelled') return 'Отменено'

  if (job.current_step && job.current_track_title) {
    return `${job.current_track_title} • ${job.current_step}`
  }
  if (job.current_track_title) {
    return job.current_track_title
  }
  return job.current_step || 'Синхронизация...'
}

/**
 * Compute a gradient style based on a user string (name/username).
 */
export const computeAvatarGradient = (str) => {
  const s = str || 'User'
  let hash = 0
  for (let i = 0; i < s.length; i++) {
    hash = s.charCodeAt(i) + ((hash << 5) - hash)
  }
  const h1 = Math.abs(hash % 360)
  const h2 = (h1 + 60) % 360
  return {
    background: `linear-gradient(135deg, hsl(${h1}, 70%, 45%) 0%, hsl(${h2}, 75%, 55%) 100%)`
  }
}

/**
 * Compute the ambient glow radial gradient for the hero card.
 */
export const computeAmbientGlow = (str) => {
  const s = str || 'User'
  let hash = 0
  for (let i = 0; i < s.length; i++) {
    hash = s.charCodeAt(i) + ((hash << 5) - hash)
  }
  const h1 = Math.abs(hash % 360)
  return {
    background: `radial-gradient(ellipse at 30% 0%, hsla(${h1}, 75%, 50%, 0.18) 0%, rgba(14, 18, 24, 0) 75%)`
  }
}

/**
 * Compute a playlist cover fallback gradient.
 */
export const computePlaylistCoverGradient = (name) => {
  const str = name || 'Playlist'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const h1 = Math.abs(hash % 360)
  const h2 = (h1 + 40) % 360
  return {
    background: `linear-gradient(135deg, hsl(${h1}, 65%, 28%) 0%, hsl(${h2}, 60%, 18%) 100%)`
  }
}
