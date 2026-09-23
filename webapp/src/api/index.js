/**
 * TG Player API — Unified Re-export
 * 
 * Import API modules from here:
 *   import { tracksApi, playlistsApi } from '@/api'
 *   import api from '@/api'  // raw axios instance
 */

// Core axios instance (default export)
export { default } from './core'
export { authStorage, cacheable, nonCacheable } from './core'

// Domain API modules
export { authApi } from './auth'
export { tracksApi } from './tracks'
export { playlistsApi } from './playlists'
export { artistsApi } from './artists'
export { albumsApi } from './albums'
export { playerApi } from './player'
export { socialApi } from './social'
export { ingestionApi } from './ingestion'
export { discordApi } from './discord'
