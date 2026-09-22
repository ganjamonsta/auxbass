/**
 * Utils barrel
 * Re-exports all utils for convenient `import { ... } from '@/utils'` usage
 */

export {
  formatDuration,
  formatDurationLong,
  formatFileSize,
  formatPlayCount,
  formatRelativeDate,
  formatFeedTimestamp,
  truncateText,
  splitArtists,
  hasMultipleArtists,
  extractFeaturedArtists,
  getAllTrackArtists,
  getDisplayTitle,
  getDisplayArtist,
  CoverSize,
  getCoverUrl,
  getCoverSrcSet,
  pluralize,
  formatTrackCount
} from './formatters'

export {
  getArtistAvatarStyle,
  getArtistInitials,
  getGenreStyle,
  getTrackCoverStyle,
  getTrackInitials,
  getPlaylistCoverStyle
} from './styles'

export {
  triggerHaptic,
  suppressNextClick,
  suppressNextContextMenu
} from './touch'
