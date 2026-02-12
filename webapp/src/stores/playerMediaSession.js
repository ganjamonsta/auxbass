/**
 * Player Media Session & Keyboard Shortcuts
 * Handles lock-screen controls, Bluetooth, media keys, and keyboard shortcuts.
 * Extracted from player.js to reduce god-object.
 */
import { getDisplayTitle, getDisplayArtist } from '../utils/formatters'

/**
 * Update Media Session metadata from current track.
 */
export function updateMediaSession(track, updatePlaybackStateFn) {
  if (!('mediaSession' in navigator) || !track) return

  const coverUrl = track.cover_url
  const artwork = coverUrl ? [
    { src: coverUrl, sizes: '96x96', type: 'image/jpeg' },
    { src: coverUrl, sizes: '128x128', type: 'image/jpeg' },
    { src: coverUrl, sizes: '256x256', type: 'image/jpeg' },
    { src: coverUrl, sizes: '512x512', type: 'image/jpeg' },
  ] : []

  navigator.mediaSession.metadata = new MediaMetadata({
    title: getDisplayTitle(track),
    artist: getDisplayArtist(track),
    album: track.album || '',
    artwork
  })

  if (updatePlaybackStateFn) updatePlaybackStateFn()
}

/**
 * Sync Media Session playback state.
 */
export function updatePlaybackState(isPlaying) {
  if (!('mediaSession' in navigator)) return
  navigator.mediaSession.playbackState = isPlaying ? 'playing' : 'paused'
}

/**
 * Sync Media Session position state.
 */
export function updatePositionState(audio, progressVal, durationVal) {
  if (!('mediaSession' in navigator) || !audio || !durationVal || !isFinite(durationVal)) return
  try {
    const position = Math.min(progressVal, durationVal)
    if (isFinite(position) && position >= 0) {
      navigator.mediaSession.setPositionState({
        duration: durationVal,
        playbackRate: audio.playbackRate || 1,
        position
      })
    }
  } catch (_) { /* ignore during transitions */ }
}

/**
 * Register Media Session action handlers.
 * @param {Object} actions - { play, pause, prev, next, seek, stop }
 */
export function setupMediaSession(actions) {
  if (!('mediaSession' in navigator)) return

  navigator.mediaSession.setActionHandler('play', actions.play)
  navigator.mediaSession.setActionHandler('pause', actions.pause)
  navigator.mediaSession.setActionHandler('previoustrack', actions.prev)
  navigator.mediaSession.setActionHandler('nexttrack', actions.next)

  navigator.mediaSession.setActionHandler('seekto', (details) => {
    if (details.seekTime !== undefined) actions.seek(details.seekTime)
  })
  navigator.mediaSession.setActionHandler('seekbackward', (details) => {
    actions.seekBackward(details.seekOffset || 10)
  })
  navigator.mediaSession.setActionHandler('seekforward', (details) => {
    actions.seekForward(details.seekOffset || 10)
  })

  try {
    navigator.mediaSession.setActionHandler('stop', actions.stop)
  } catch (_) { /* not supported in all browsers */ }
}

let _keyboardAttached = false

/**
 * Attach global keyboard shortcuts (idempotent).
 * @param {Object} actions - { toggle, next, prev, seek, seekBack, setVolume, toggleMute, toggleShuffle, toggleRepeat, getVolume, getProgress, getDuration }
 */
export function setupKeyboardShortcuts(actions) {
  if (_keyboardAttached) return
  _keyboardAttached = true

  document.addEventListener('keydown', (e) => {
    const tag = e.target.tagName
    if (tag === 'INPUT' || tag === 'TEXTAREA' || e.target.isContentEditable) return

    switch (e.code) {
      case 'Space':
      case 'MediaPlayPause':
        e.preventDefault(); actions.toggle(); break

      case 'MediaTrackNext':
        e.preventDefault(); actions.next(); break

      case 'MediaTrackPrevious':
        e.preventDefault(); actions.prev(); break

      case 'ArrowRight':
        if (!e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
          e.preventDefault()
          actions.seek(Math.min(actions.getDuration(), actions.getProgress() + 10))
        }
        break

      case 'ArrowLeft':
        if (!e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
          e.preventDefault()
          actions.seek(Math.max(0, actions.getProgress() - 10))
        }
        break

      case 'KeyM':
        if (!e.ctrlKey && !e.metaKey) { e.preventDefault(); actions.toggleMute() }
        break

      case 'KeyN':
        if (!e.ctrlKey && !e.metaKey) { e.preventDefault(); actions.next() }
        break

      case 'KeyP':
        if (!e.ctrlKey && !e.metaKey) { e.preventDefault(); actions.prev() }
        break

      case 'KeyS':
        if (!e.ctrlKey && !e.metaKey) { e.preventDefault(); actions.toggleShuffle() }
        break

      case 'KeyR':
        if (!e.ctrlKey && !e.metaKey) { e.preventDefault(); actions.toggleRepeat() }
        break

      case 'ArrowUp':
        if (!e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
          e.preventDefault()
          actions.setVolume(Math.min(1, actions.getVolume() + 0.1))
        }
        break

      case 'ArrowDown':
        if (!e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
          e.preventDefault()
          actions.setVolume(Math.max(0, actions.getVolume() - 0.1))
        }
        break
    }
  })
}
