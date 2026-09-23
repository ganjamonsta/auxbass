/**
 * Legacy API Client — Backward Compatibility Re-export
 * 
 * All API modules have been extracted to separate files under @/api/.
 * New code should import from '@/api' directly:
 *   import { tracksApi, playlistsApi } from '@/api'
 * 
 * This file re-exports everything for backward compatibility.
 */

// Core axios instance (default export)
export { default } from './core'
export { authStorage } from './core'

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
