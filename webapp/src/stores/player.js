import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { playerApi, tracksApi } from '../api/client'

// Import storage and cache utilities
import {
  loadSettings,
  saveSettings,
  loadPlayerState,
  savePlayerState,
  clearPlayerState,
  STATE_SAVE_INTERVAL,
} from './playerStorage'

import {
  getCachedUrl,
  setCachedUrl,
  getCachedAudio,
  setCachedAudio,
  preloadTrackWithAudio,
  getPreloadedAudio,
  clearPreloadAudio,
} from './playerCache'

// Load saved settings
const savedSettings = loadSettings()
const savedState = loadPlayerState()

// ============== Adaptive Preload System ==============
// Tracks download speed to adapt preload strategy
let _lastDownloadSpeed = 0  // bytes per second
let _userInteractionTime = 0  // timestamp of last user action (play/next/prev)
const USER_INTERACTION_COOLDOWN = 1000  // 1 second - reduced for faster preload resume

const markUserInteraction = () => {
  _userInteractionTime = Date.now()
}

const isUserActivelyBrowsing = () => {
  return Date.now() - _userInteractionTime < USER_INTERACTION_COOLDOWN
}

export const usePlayerStore = defineStore('player', () => {
  // State - restore from localStorage where applicable
  const audio = ref(null)
  const currentTrack = ref(null)
  const queue = ref([])
  const queueIndex = ref(-1)
  const shuffleOrder = ref([])  // Pre-generated shuffle order: array of queue indices
  const shuffleIndex = ref(-1)  // Current position in shuffleOrder
  const isPlaying = ref(false)
  const progress = ref(0)
  const duration = ref(0)
  const volume = ref(savedSettings.volume ?? 1)
  const isMuted = ref(savedSettings.isMuted ?? false)
  const shuffle = ref(savedSettings.shuffle ?? false)
  const repeat = ref(savedSettings.repeat ?? 'none') // none, one, all
  const loading = ref(false)
  const buffered = ref(0) // buffered endpoint in seconds
  const nextTrackPreloaded = ref(null)
  const lastError = ref(null)  // For error notifications
  const stateRestored = ref(false) // Flag to track if state was restored
  
  // Interval for periodic state saving
  let stateSaveInterval = null
  
  // Flag to prevent duplicate preload triggers per track
  let preloadTriggered = false
  
  // Flag to prevent error auto-skip during track change
  let isSkipping = false
  
  // Protection against cascading skips
  let consecutiveSkipCount = 0
  let lastSkipTime = 0
  const MAX_CONSECUTIVE_SKIPS = 3
  const SKIP_RESET_TIMEOUT = 5000  // Reset counter after 5 seconds of stable playback
  
  // Callback for track unavailable
  let onTrackUnavailableCallback = null
  const setOnTrackUnavailable = (callback) => {
    onTrackUnavailableCallback = callback
  }

  // ============== Shuffle Queue Management ==============
  // Generate a deterministic shuffle order so we know the next track in advance
  const generateShuffleOrder = (startingIndex = -1) => {
    if (queue.value.length === 0) {
      shuffleOrder.value = []
      shuffleIndex.value = -1
      return
    }
    
    // Create array of indices [0, 1, 2, ..., n-1]
    const indices = Array.from({ length: queue.value.length }, (_, i) => i)
    
    // Fisher-Yates shuffle
    for (let i = indices.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[indices[i], indices[j]] = [indices[j], indices[i]]
    }
    
    // If we have a starting track, move it to the front
    if (startingIndex >= 0 && startingIndex < queue.value.length) {
      const pos = indices.indexOf(startingIndex)
      if (pos > 0) {
        indices.splice(pos, 1)
        indices.unshift(startingIndex)
      }
    }
    
    shuffleOrder.value = indices
    shuffleIndex.value = 0
    console.log(`[Shuffle] Generated order for ${indices.length} tracks`)
  }

  // Get next track index based on shuffle mode
  const getNextTrackIndex = () => {
    if (shuffle.value && shuffleOrder.value.length > 0) {
      // Use pre-generated shuffle order
      const nextShuffleIdx = shuffleIndex.value + 1
      if (nextShuffleIdx >= shuffleOrder.value.length) {
        if (repeat.value === 'all') {
          return shuffleOrder.value[0] // Loop to start of shuffle
        }
        return -1 // End of queue
      }
      return shuffleOrder.value[nextShuffleIdx]
    } else {
      // Normal order
      const nextIdx = queueIndex.value + 1
      if (nextIdx >= queue.value.length) {
        if (repeat.value === 'all') {
          return 0
        }
        return -1
      }
      return nextIdx
    }
  }

  // Get the next track object for preloading (works for both shuffle and normal modes)
  const getNextTrackForPreload = () => {
    const nextIdx = getNextTrackIndex()
    if (nextIdx === -1) return null
    return queue.value[nextIdx] || null
  }

  // Update Media Session metadata (for lock screen, notification area, Bluetooth controls, etc.)
  const updateMediaSession = () => {
    if (!('mediaSession' in navigator) || !currentTrack.value) return
    
    const track = currentTrack.value
    // Use cover_url field from track model, fallback to empty array if no cover
    const coverUrl = track.cover_url
    const artwork = coverUrl ? [
      { src: coverUrl, sizes: '96x96', type: 'image/jpeg' },
      { src: coverUrl, sizes: '128x128', type: 'image/jpeg' },
      { src: coverUrl, sizes: '256x256', type: 'image/jpeg' },
      { src: coverUrl, sizes: '512x512', type: 'image/jpeg' },
    ] : []
    
    navigator.mediaSession.metadata = new MediaMetadata({
      title: track.title || 'Без названия',
      artist: track.artist || 'Неизвестный исполнитель',
      album: track.album || '',
      artwork
    })
    
    // Also update playback state when metadata changes
    updatePlaybackState()
  }

  // Setup Media Session handlers (for lock screen, notification controls, Bluetooth, etc.)
  const setupMediaSession = () => {
    if (!('mediaSession' in navigator)) return
    
    // Play/Pause handlers
    navigator.mediaSession.setActionHandler('play', () => {
      if (audio.value) audio.value.play()
    })
    
    navigator.mediaSession.setActionHandler('pause', () => {
      if (audio.value) audio.value.pause()
    })
    
    // Track navigation
    navigator.mediaSession.setActionHandler('previoustrack', () => {
      prev()
    })
    
    navigator.mediaSession.setActionHandler('nexttrack', () => {
      next()
    })
    
    // Seek to specific position (used by progress bar on lock screen)
    navigator.mediaSession.setActionHandler('seekto', (details) => {
      if (details.seekTime !== undefined && audio.value) {
        seek(details.seekTime)
        // Immediately update position for responsive UI
        updatePositionState()
      }
    })
    
    // Seek backward (headphone button double-tap, etc.)
    navigator.mediaSession.setActionHandler('seekbackward', (details) => {
      const skipTime = details.seekOffset || 10
      seek(Math.max(0, progress.value - skipTime))
      updatePositionState()
    })
    
    // Seek forward (headphone button triple-tap, etc.)
    navigator.mediaSession.setActionHandler('seekforward', (details) => {
      const skipTime = details.seekOffset || 10
      seek(Math.min(duration.value, progress.value + skipTime))
      updatePositionState()
    })
    
    // Stop handler (some systems use this instead of pause)
    try {
      navigator.mediaSession.setActionHandler('stop', () => {
        if (audio.value) {
          audio.value.pause()
          audio.value.currentTime = 0
        }
        isPlaying.value = false
        updatePlaybackState()
      })
    } catch (e) {
      // 'stop' action not supported in all browsers
      console.log('[MediaSession] stop handler not supported')
    }
  }

  // Setup global keyboard shortcuts for media control
  // Works on desktop (keyboard) and some mobile devices with external keyboards
  let keyboardHandlerAttached = false
  const setupKeyboardShortcuts = () => {
    if (keyboardHandlerAttached) return
    keyboardHandlerAttached = true
    
    document.addEventListener('keydown', (e) => {
      // Ignore if user is typing in an input field
      const target = e.target
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return
      }
      
      switch (e.code) {
        case 'Space':
          // Space - Play/Pause (only if not scrolling)
          e.preventDefault()
          toggle()
          break
          
        case 'MediaPlayPause':
          // Media key - Play/Pause
          e.preventDefault()
          toggle()
          break
          
        case 'MediaTrackNext':
          // Media key - Next track
          e.preventDefault()
          next()
          break
          
        case 'MediaTrackPrevious':
          // Media key - Previous track
          e.preventDefault()
          prev()
          break
          
        case 'ArrowRight':
          // Right arrow - Seek forward 10 seconds (when not in input)
          if (!e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
            e.preventDefault()
            seek(Math.min(duration.value, progress.value + 10))
          }
          break
          
        case 'ArrowLeft':
          // Left arrow - Seek backward 10 seconds
          if (!e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
            e.preventDefault()
            seek(Math.max(0, progress.value - 10))
          }
          break
          
        case 'KeyM':
          // M - Toggle mute
          if (!e.ctrlKey && !e.metaKey) {
            e.preventDefault()
            toggleMute()
          }
          break
          
        case 'KeyN':
          // N - Next track
          if (!e.ctrlKey && !e.metaKey) {
            e.preventDefault()
            next()
          }
          break
          
        case 'KeyP':
          // P - Previous track
          if (!e.ctrlKey && !e.metaKey) {
            e.preventDefault()
            prev()
          }
          break
          
        case 'KeyS':
          // S - Toggle shuffle
          if (!e.ctrlKey && !e.metaKey) {
            e.preventDefault()
            toggleShuffle()
          }
          break
          
        case 'KeyR':
          // R - Toggle repeat
          if (!e.ctrlKey && !e.metaKey) {
            e.preventDefault()
            toggleRepeat()
          }
          break
          
        case 'ArrowUp':
          // Up arrow - Volume up
          if (!e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
            e.preventDefault()
            setVolume(Math.min(1, volume.value + 0.1))
          }
          break
          
        case 'ArrowDown':
          // Down arrow - Volume down
          if (!e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
            e.preventDefault()
            setVolume(Math.max(0, volume.value - 0.1))
          }
          break
      }
    })
    
    console.log('[Keyboard] Global shortcuts enabled: Space=play/pause, ←/→=seek, ↑/↓=volume, M=mute, N/P=next/prev, S=shuffle, R=repeat')
  }

  // Update Media Session playback state
  const updatePlaybackState = () => {
    if (!('mediaSession' in navigator)) return
    navigator.mediaSession.playbackState = isPlaying.value ? 'playing' : 'paused'
  }

  // Update Media Session position (shows progress on lock screen)
  const updatePositionState = () => {
    if (!('mediaSession' in navigator) || !audio.value || !duration.value || !isFinite(duration.value)) return
    try {
      const position = Math.min(progress.value, duration.value)
      if (isFinite(position) && position >= 0) {
        navigator.mediaSession.setPositionState({
          duration: duration.value,
          playbackRate: audio.value.playbackRate || 1,
          position: position
        })
      }
    } catch (e) {
      // Ignore errors (can happen during track transitions)
    }
  }
  
  // Track for position update throttling
  let lastPositionUpdate = 0

  // Initialize audio element
  const initAudio = () => {
    if (audio.value) return
    
    audio.value = new Audio()
    audio.value.volume = volume.value
    // Use 'auto' for faster startup - browser will buffer intelligently
    // The slow start issue was due to sequential API calls, not buffering
    audio.value.preload = 'auto' 
    
    // Setup Media Session handlers once (for lock screen, notification controls, etc.)
    setupMediaSession()
    
    // Setup global keyboard shortcuts (for desktop media control)
    setupKeyboardShortcuts()
    
    // canplay event - audio ready to play
    audio.value.addEventListener('canplay', () => {
      loading.value = false
    })

    // playing event - actually playing
    audio.value.addEventListener('playing', () => {
       loading.value = false
    })
    
    // waiting event - buffering
    audio.value.addEventListener('waiting', () => {
      // Only show loading if we are really stalled (buffer < 0.5s ahead)
      // Sometimes browsers fire 'waiting' momentarily during seek
      if (audio.value.readyState < 3) { 
        loading.value = true
      }
    })
    
    audio.value.addEventListener('timeupdate', () => {
      progress.value = audio.value.currentTime
      
      // Update buffered state
      if (audio.value.buffered.length > 0) {
        // Find the buffered range that covers the current time
        for (let i = 0; i < audio.value.buffered.length; i++) {
          if (audio.value.buffered.start(i) <= audio.value.currentTime && 
              audio.value.buffered.end(i) >= audio.value.currentTime) {
            buffered.value = audio.value.buffered.end(i)
            break
          }
        }
      }

      // Update position state every second for media session (throttled)
      const now = Date.now()
      if (now - lastPositionUpdate >= 1000) {
        lastPositionUpdate = now
        updatePositionState()
      }
    })
    
    
    // progress event - download progress
    audio.value.addEventListener('progress', () => {
       if (audio.value.buffered.length > 0) {
        // Just take the end of the last buffered range or the one covering current time
        // Often a simple approximation of the last range is enough for simple UI
        const lastIndex = audio.value.buffered.length - 1
        buffered.value = audio.value.buffered.end(lastIndex)
        
        // Ensure loading is false if we have enough buffer
        if (loading.value && buffered.value - progress.value > 2) {
           loading.value = false
        }
      }
    })

    audio.value.addEventListener('durationchange', () => {
      duration.value = audio.value.duration
      updatePositionState()
    })
    
    audio.value.addEventListener('ended', () => {
      handleEnded()
    })
    
    audio.value.addEventListener('play', () => {
      isPlaying.value = true
      isSkipping = false  // Reset skip flag on successful playback
      updatePlaybackState()
      startStateSaving()
    })
    
    audio.value.addEventListener('pause', () => {
      isPlaying.value = false
      updatePlaybackState()
      persistState() // Save state on pause
    })
    
    audio.value.addEventListener('error', (e) => {
      console.error('Audio error:', e)
      loading.value = false
      
      const errorCode = audio.value?.error?.code
      const errorMsg = audio.value?.error?.message || 'Ошибка воспроизведения'
      
      // Error code 1 = ABORTED - this is normal during src change, always ignore
      if (errorCode === 1) {
        console.log('[Audio Error] ABORTED (code 1) - normal during src change, ignoring')
        return
      }
      
      // Ignore errors during track change
      if (isSkipping) {
        console.log('[Audio Error] Ignoring error during track skip')
        return
      }
      
      // Protection against cascading skips
      const now = Date.now()
      if (now - lastSkipTime < 2000) {
        consecutiveSkipCount++
      } else {
        consecutiveSkipCount = 1
      }
      lastSkipTime = now
      
      if (consecutiveSkipCount > MAX_CONSECUTIVE_SKIPS) {
        console.warn(`[Audio Error] Too many consecutive skips (${consecutiveSkipCount}), stopping`)
        lastError.value = {
          type: 'cascade_error',
          track: currentTrack.value,
          message: 'Слишком много ошибок подряд, воспроизведение остановлено'
        }
        isPlaying.value = false
        return
      }
      
      // Auto-skip on audio element errors (network issues, decode errors, etc.)
      // Error codes: 2=NETWORK, 3=DECODE, 4=SRC_NOT_SUPPORTED
      if (errorCode && errorCode >= 2) {
        console.warn(`[Audio Error] Code ${errorCode}: ${errorMsg}, auto-skipping (${consecutiveSkipCount}/${MAX_CONSECUTIVE_SKIPS})`)
        lastError.value = {
          type: 'audio_error',
          track: currentTrack.value,
          message: `Ошибка аудио: ${errorMsg}`
        }
        // Auto-skip to keep music playing
        isSkipping = true
        setTimeout(() => {
          next()
          isSkipping = false
        }, 1000)
      }
    })
    
    // Preload next track ASAP - when current track can play through
    audio.value.addEventListener('canplaythrough', () => {
      if (!preloadTriggered && duration.value > 0) {
        console.log('[Instant Preload] Triggering on canplaythrough')
        preloadTriggered = true
        preloadNextTracks()
      }
    })
    
    // Fallback: Also trigger preload on timeupdate if canplaythrough didn't fire
    audio.value.addEventListener('timeupdate', () => {
      // Trigger after 0.5 seconds of playback as fallback
      if (duration.value > 0 && !preloadTriggered && progress.value > 0.5) {
        console.log(`[Instant Preload] Fallback trigger at ${progress.value.toFixed(1)}s`)
        preloadTriggered = true
        preloadNextTracks()
      }
    })
    
    // Reset preload flag on new track
    audio.value.addEventListener('loadstart', () => {
      // Don't reset here, handled in play() for better control
    })
  }

  // Re-attach event listeners when swapping audio elements
  const reattachAudioListeners = () => {
    if (!audio.value) return
    
    audio.value.addEventListener('canplay', () => {
      loading.value = false
    })
    
    audio.value.addEventListener('canplaythrough', () => {
      // Trigger preload on canplaythrough for faster next track start
      if (!preloadTriggered && duration.value > 0) {
        console.log('[Instant Preload] Triggering on canplaythrough (reattached)')
        preloadTriggered = true
        preloadNextTracks()
      }
    })
    
    audio.value.addEventListener('playing', () => {
      loading.value = false
    })
    
    audio.value.addEventListener('waiting', () => {
      if (audio.value.readyState < 3) {
        loading.value = true
      }
    })
    
    audio.value.addEventListener('timeupdate', () => {
      progress.value = audio.value.currentTime
      
      if (audio.value.buffered.length > 0) {
        for (let i = 0; i < audio.value.buffered.length; i++) {
          if (audio.value.buffered.start(i) <= audio.value.currentTime && 
              audio.value.buffered.end(i) >= audio.value.currentTime) {
            buffered.value = audio.value.buffered.end(i)
            break
          }
        }
      }
      
      if (Math.floor(progress.value) % 5 === 0) {
        updatePositionState()
      }
      
      // Fallback preload trigger (if canplaythrough didn't fire)
      if (duration.value > 0 && !preloadTriggered && progress.value > 0.5) {
        preloadTriggered = true
        preloadNextTracks()
      }
    })
    
    audio.value.addEventListener('progress', () => {
      if (audio.value.buffered.length > 0) {
        const lastIndex = audio.value.buffered.length - 1
        buffered.value = audio.value.buffered.end(lastIndex)
        if (loading.value && buffered.value - progress.value > 2) {
          loading.value = false
        }
      }
    })
    
    audio.value.addEventListener('durationchange', () => {
      duration.value = audio.value.duration
      updatePositionState()
    })
    
    audio.value.addEventListener('ended', () => {
      handleEnded()
    })
    
    audio.value.addEventListener('play', () => {
      isPlaying.value = true
      isSkipping = false  // Reset skip flag on successful playback
      consecutiveSkipCount = 0  // Reset consecutive skip counter
      updatePlaybackState()
      startStateSaving()
    })
    
    audio.value.addEventListener('pause', () => {
      isPlaying.value = false
      updatePlaybackState()
      persistState()
    })
    
    audio.value.addEventListener('error', (e) => {
      console.error('Audio error:', e)
      loading.value = false
      
      const errorCode = audio.value?.error?.code
      const errorMsg = audio.value?.error?.message || 'Ошибка воспроизведения'
      
      // Error code 1 = ABORTED - this is normal during src change, always ignore
      if (errorCode === 1) {
        console.log('[Audio Error] ABORTED (code 1) - normal during src change, ignoring')
        return
      }
      
      // Ignore errors during track change
      if (isSkipping) {
        console.log('[Audio Error] Ignoring error during track skip')
        return
      }
      
      // Protection against cascading skips
      const now = Date.now()
      if (now - lastSkipTime < 2000) {
        consecutiveSkipCount++
      } else {
        consecutiveSkipCount = 1
      }
      lastSkipTime = now
      
      if (consecutiveSkipCount > MAX_CONSECUTIVE_SKIPS) {
        console.warn(`[Audio Error] Too many consecutive skips (${consecutiveSkipCount}), stopping`)
        lastError.value = {
          type: 'cascade_error',
          track: currentTrack.value,
          message: 'Слишком много ошибок подряд, воспроизведение остановлено'
        }
        isPlaying.value = false
        return
      }
      
      // Auto-skip on audio element errors (network issues, decode errors, etc.)
      if (errorCode && errorCode >= 2) {
        console.warn(`[Audio Error] Code ${errorCode}: ${errorMsg}, auto-skipping (${consecutiveSkipCount}/${MAX_CONSECUTIVE_SKIPS})`)
        lastError.value = {
          type: 'audio_error',
          track: currentTrack.value,
          message: `Ошибка аудио: ${errorMsg}`
        }
        isSkipping = true
        setTimeout(() => {
          next()
          isSkipping = false
        }, 1000)
      }
    })
  }
  // Preload next 2-3 tracks using batch API for instant playback
  // Uses Audio preload="auto" for the immediate next track
  const preloadNextTracks = async () => {
    if (queue.value.length === 0) return
    
    // Don't preload if user is actively switching tracks
    if (isUserActivelyBrowsing()) {
      console.log('[Preload] User actively browsing, deferring...')
      setTimeout(() => preloadNextTracks(), USER_INTERACTION_COOLDOWN)
      return
    }
    
    // Collect next tracks to preload
    const tracksToPreload = []
    
    if (shuffle.value && shuffleOrder.value.length > 0) {
      // SHUFFLE MODE with pre-generated order: we KNOW the next tracks!
      for (let offset = 1; offset <= 3; offset++) {
        const nextShuffleIdx = shuffleIndex.value + offset
        if (nextShuffleIdx >= shuffleOrder.value.length) {
          if (repeat.value === 'all' && nextShuffleIdx < shuffleOrder.value.length + 3) {
            // Wrap around for repeat all
            const wrappedIdx = nextShuffleIdx % shuffleOrder.value.length
            const queueIdx = shuffleOrder.value[wrappedIdx]
            const track = queue.value[queueIdx]
            if (track && !getCachedUrl(track.id) && !getCachedAudio(track.id)) {
              tracksToPreload.push(track)
            }
          }
          continue
        }
        const queueIdx = shuffleOrder.value[nextShuffleIdx]
        const track = queue.value[queueIdx]
        if (track && !getCachedUrl(track.id) && !getCachedAudio(track.id)) {
          tracksToPreload.push(track)
        }
      }
      console.log(`[Preload] Shuffle mode: preloading ${tracksToPreload.length} next tracks from shuffle order`)
    } else {
      // NORMAL MODE: Preload next 3 tracks in order
      for (let offset = 1; offset <= 3; offset++) {
        let nextIndex = queueIndex.value + offset
        if (nextIndex >= queue.value.length) {
          if (repeat.value === 'all') {
            nextIndex = nextIndex % queue.value.length
          } else {
            break
          }
        }
        const track = queue.value[nextIndex]
        if (track && !getCachedUrl(track.id) && !getCachedAudio(track.id)) {
          tracksToPreload.push(track)
        }
      }
    }
    
    if (tracksToPreload.length === 0) {
      console.log('[Preload] All next tracks already have URLs cached')
      // Start Audio preloading for immediate next track
      const nextTrackToPreload = getNextTrackForPreload()
      if (nextTrackToPreload) {
        const url = getCachedUrl(nextTrackToPreload.id)
        if (url && preloadTrackId !== nextTrackToPreload.id) {
          preloadTrackWithAudio(nextTrackToPreload.id, url)
          nextTrackPreloaded.value = {
            track: nextTrackToPreload,
            url: url,
            audioPreloaded: true
          }
        }
      }
      return
    }
    
    try {
      // Batch request for all URLs at once (parallel file_path fetching on server)
      const trackIds = tracksToPreload.map(t => t.id)
      console.log(`[Preload] Fetching batch URLs for ${trackIds.length} tracks`)
      
      const response = await playerApi.getBatchUrls(trackIds)
      const urlData = response.data.urls || []
      
      // Cache all valid URLs
      let cachedCount = 0
      for (const item of urlData) {
        // Validate URL format before caching
        if (item.url && !item.error && item.url.startsWith('/api/player/audio/')) {
          setCachedUrl(item.track_id, item.url, item.expires_at)
          cachedCount++
        } else if (item.error) {
          console.warn(`[Preload] Track ${item.track_id} error: ${item.error}`)
        }
      }
      
      // Start preloading the immediate next track with Audio element
      const nextTrackToPreload = getNextTrackForPreload()
      if (nextTrackToPreload) {
        const nextUrl = getCachedUrl(nextTrackToPreload.id)
        if (nextUrl && preloadTrackId !== nextTrackToPreload.id) {
          preloadTrackWithAudio(nextTrackToPreload.id, nextUrl)
          nextTrackPreloaded.value = {
            track: nextTrackToPreload,
            url: nextUrl,
            audioPreloaded: true
          }
        }
      }
      
      console.log(`[Preload] Cached ${cachedCount} URLs, next track audio preloading`)
      
    } catch (e) {
      console.error('[Preload] Batch URL fetch failed:', e)
    }
  }

  // Legacy function name for compatibility
  const preloadNextTrack = preloadNextTracks
  
  // Set to track which tracks are currently being preloaded
  // Map<trackId, AbortController>
  const _preloadingTracks = new Map()
  
  // Cancel preloads that are no longer relevant (not in next N positions)
  const cancelIrrelevantPreloads = () => {
    const relevantIds = new Set()
    
    if (shuffle.value && shuffleOrder.value.length > 0) {
      // In shuffle mode with order: keep next 3 in shuffle order
      for (let offset = 1; offset <= 3; offset++) {
        const nextShuffleIdx = shuffleIndex.value + offset
        if (nextShuffleIdx < shuffleOrder.value.length) {
          const queueIdx = shuffleOrder.value[nextShuffleIdx]
          if (queue.value[queueIdx]) {
            relevantIds.add(queue.value[queueIdx].id)
          }
        } else if (repeat.value === 'all') {
          const wrappedIdx = nextShuffleIdx % shuffleOrder.value.length
          const queueIdx = shuffleOrder.value[wrappedIdx]
          if (queue.value[queueIdx]) {
            relevantIds.add(queue.value[queueIdx].id)
          }
        }
      }
    } else {
      // Normal mode: keep next 3 tracks in order
      for (let offset = 1; offset <= 3; offset++) {
        let idx = queueIndex.value + offset
        if (idx >= queue.value.length) {
          if (repeat.value === 'all') {
            idx = idx % queue.value.length
          } else {
            continue
          }
        }
        if (queue.value[idx]) {
          relevantIds.add(queue.value[idx].id)
        }
      }
    }
    
    // Cancel any preload not in relevant set
    for (const [trackId, controller] of _preloadingTracks.entries()) {
      if (!relevantIds.has(trackId)) {
        console.log(`[Preload] Cancelling irrelevant preload: track ${trackId}`)
        controller.abort()
        _preloadingTracks.delete(trackId)
      }
    }
  }

  // Preload a single track into cache
  const preloadSingleTrack = async (track) => {
    // Skip if already cached or currently loading
    if (getCachedAudio(track.id) || _preloadingTracks.has(track.id)) return
    
    const controller = new AbortController()
    _preloadingTracks.set(track.id, controller)
    
    console.log(`[Preload] Starting: ${track.title}`)
    const startTime = Date.now()
    
    try {
      const response = await playerApi.getStreamUrl(track.id)
      const streamUrl = response.data.url
      
      const audioResponse = await fetch(streamUrl, { signal: controller.signal })
      if (!audioResponse.ok) {
        console.warn(`[Preload] Failed to fetch: ${track.title}`, audioResponse.status)
        return
      }
      
      const blob = await audioResponse.blob()
      const blobUrl = URL.createObjectURL(blob)
      
      // Track download speed for adaptive preloading
      const downloadTime = (Date.now() - startTime) / 1000  // seconds
      if (downloadTime > 0) {
        _lastDownloadSpeed = blob.size / downloadTime
        console.log(`[Preload] Speed: ${(_lastDownloadSpeed / 1024).toFixed(0)} KB/s`)
      }
      
      setCachedAudio(track.id, blobUrl)
      console.log(`[Preload] Cached: ${track.title} (${(blob.size / 1024 / 1024).toFixed(1)}MB in ${downloadTime.toFixed(1)}s)`)
      
      // Update nextTrackPreloaded if this is the next track
      const nextIndex = queueIndex.value + 1
      const nextTrack = queue.value[nextIndex] || 
                        (repeat.value === 'all' ? queue.value[0] : null)
      
      if (nextTrack && nextTrack.id === track.id) {
        nextTrackPreloaded.value = {
          track: track,
          url: blobUrl,
          cached: true
        }
      }
      
      console.log(`Preloaded: ${track.title}`)
    } catch (e) {
      if (e.name === 'AbortError') {
        console.log(`[Preload] Aborted: ${track.title}`)
      } else {
        console.error('Failed to preload track:', track.title, e)
      }
    } finally {
      if (_preloadingTracks.get(track.id) === controller) {
        _preloadingTracks.delete(track.id)
      }
    }
  }

  // Play track
  const play = async (track, newQueue = null) => {
    initAudio()
    
    // Mark user interaction to pause background preloads
    markUserInteraction()
    
    // Cancel preloads that are no longer relevant to new position
    cancelIrrelevantPreloads()
    
    // Update queue if provided
    if (newQueue) {
      queue.value = [...newQueue]
      queueIndex.value = newQueue.findIndex(t => t.id === track.id)
      
      // Generate shuffle order for new queue if shuffle is enabled
      if (shuffle.value) {
        generateShuffleOrder(queueIndex.value)
      }
    } else if (shuffle.value && shuffleOrder.value.length === 0) {
      // Shuffle is on but no order generated yet
      generateShuffleOrder(queueIndex.value)
    }
    
    // If same track, just toggle
    if (currentTrack.value?.id === track.id) {
      toggle()
      return
    }
    
    // Reset preload trigger flag for new track
    preloadTriggered = false
    
    loading.value = true
    currentTrack.value = track
    lastError.value = null
    
    // Update Media Session
    updateMediaSession()
    
    try {
      // === PRIORITY 1: Blob cache (fully downloaded) ===
      const cachedBlobUrl = getCachedAudio(track.id)
      if (cachedBlobUrl) {
        console.log('[Play] Using blob cache - instant start')
        audio.value.pause()
        audio.value.currentTime = 0
        audio.value.src = cachedBlobUrl
        buffered.value = duration.value  // Fully buffered
        audio.value.load()
        await audio.value.play()
        loading.value = false
        persistState()
        startStateSaving()
        nextTrackPreloaded.value = null
        preloadNextTrack()
        return
      }
      
      // === PRIORITY 2: Preloaded Audio element (already buffering) ===
      const preloadedAudio = getPreloadedAudio(track.id)
      if (preloadedAudio && preloadedAudio.readyState >= 2) {
        console.log('[Play] Using preloaded Audio element - fast start')
        
        // Swap audio elements
        if (audio.value) {
          audio.value.pause()
          audio.value.src = ''
        }
        
        const oldAudio = audio.value
        audio.value = preloadedAudio
        audio.value.volume = volume.value
        audio.value.muted = isMuted.value
        
        // Reattach event listeners to new audio element
        reattachAudioListeners()
        
        await audio.value.play()
        loading.value = false
        
        // Recycle old audio for next preload
        preloadAudio = oldAudio || new Audio()
        preloadAudio.preload = 'auto'
        preloadAudio.volume = 0
        preloadTrackId = null
        
        persistState()
        startStateSaving()
        nextTrackPreloaded.value = null
        preloadNextTracks()
        return
      }
      
      // === PRIORITY 3: Cached URL token (skip first API call) ===
      let streamUrl = getCachedUrl(track.id)
      
      if (streamUrl) {
        console.log('[Play] Using cached URL token - skip API call')
      } else {
        // Fallback: Fetch new URL from API
        console.log('[Play] Fetching new stream URL from API')
        const response = await playerApi.getStreamUrl(track.id)
        streamUrl = response.data.url
        // Cache for potential retry
        setCachedUrl(track.id, streamUrl, response.data.expires_at)
      }
      
      // Stream directly
      audio.value.src = streamUrl
      buffered.value = 0
      await audio.value.play()
      
      loading.value = false
      nextTrackPreloaded.value = null
      
      // Save state after starting playback
      persistState()
      startStateSaving()
      
      // Preload is now triggered by canplaythrough event for faster start
      
    } catch (error) {
      console.error('Failed to play track:', error)
      
      const statusCode = error.response?.status
      const errorDetail = error.response?.data?.detail || error.message || 'Ошибка воспроизведения'
      
      // Protection against cascading skips
      const now = Date.now()
      if (now - lastSkipTime < 2000) {
        consecutiveSkipCount++
      } else {
        consecutiveSkipCount = 1
      }
      lastSkipTime = now
      
      if (consecutiveSkipCount > MAX_CONSECUTIVE_SKIPS) {
        console.warn(`[Play] Too many consecutive errors (${consecutiveSkipCount}), stopping playback`)
        lastError.value = {
          type: 'cascade_error',
          track: track,
          message: 'Слишком много ошибок подряд, воспроизведение остановлено'
        }
        isPlaying.value = false
        loading.value = false
        return
      }
      
      // Check if file is unavailable (503 error)
      if (statusCode === 503) {
        const isLargeFile = errorDetail.includes('слишком большой') || errorDetail.includes('too large') ||
                           (track.file_size && track.file_size > 20 * 1024 * 1024)
        
        lastError.value = {
          type: isLargeFile ? 'too_large' : 'unavailable',
          track: track,
          message: errorDetail
        }
        
        // Only mark as unavailable if file is truly gone (not just too large)
        if (!isLargeFile) {
          try {
            await tracksApi.markUnavailable(track.id)
            track.is_unavailable = true
          } catch (e) {
            console.error('Failed to mark track unavailable:', e)
          }
        }
        
        // Call callback if set
        if (onTrackUnavailableCallback) {
          onTrackUnavailableCallback(track, errorDetail, isLargeFile)
        }
        
        // Auto-skip to next track
        setTimeout(() => next(), 1500)
      } else if (statusCode === 401) {
        // Token expired - clear URL cache and retry once, or skip
        console.warn('[Play] Stream token expired, clearing cache and skipping')
        urlCache.delete(track.id)
        lastError.value = {
          type: 'auth_expired',
          track: track,
          message: 'Токен истёк, переключаем трек...'
        }
        setTimeout(() => next(), 500)
      } else if (statusCode === 404) {
        // Track/file not found
        lastError.value = {
          type: 'not_found',
          track: track,
          message: 'Трек не найден'
        }
        try {
          await tracksApi.markUnavailable(track.id)
          track.is_unavailable = true
        } catch (e) {
          console.error('Failed to mark track unavailable:', e)
        }
        setTimeout(() => next(), 1000)
      } else {
        // Any other error (network, etc) - just skip to keep music playing
        console.warn('[Play] Unknown error, auto-skipping:', statusCode, errorDetail)
        lastError.value = {
          type: 'playback_error',
          track: track,
          message: errorDetail
        }
        setTimeout(() => next(), 1000)
      }
    } finally {
      loading.value = false
    }
  }

  // Toggle play/pause
  const toggle = async () => {
    // If we have a restored state but audio is not loaded, resume from state
    if (currentTrack.value && (!audio.value || !audio.value.src)) {
      await resumeFromState()
      return
    }
    
    if (!audio.value) return
    
    if (isPlaying.value) {
      audio.value.pause()
    } else {
      audio.value.play()
    }
  }

  // Next track
  const next = async () => {
    if (queue.value.length === 0) return
    
    // Prevent error handlers from triggering during track change
    isSkipping = true
    
    // Mark user interaction and cancel irrelevant preloads
    markUserInteraction()
    cancelIrrelevantPreloads()
    preloadTriggered = false
    
    let nextIndex
    
    if (shuffle.value && shuffleOrder.value.length > 0) {
      // Use pre-generated shuffle order for deterministic next track
      shuffleIndex.value++
      if (shuffleIndex.value >= shuffleOrder.value.length) {
        if (repeat.value === 'all') {
          // Re-shuffle and start from beginning
          generateShuffleOrder()
        } else {
          // End of shuffle queue
          isPlaying.value = false
          isSkipping = false
          return
        }
      }
      nextIndex = shuffleOrder.value[shuffleIndex.value]
    } else {
      nextIndex = queueIndex.value + 1
      if (nextIndex >= queue.value.length) {
        if (repeat.value === 'all') {
          nextIndex = 0
        } else {
          // End of queue, no repeat - stop playback
          isPlaying.value = false
          isSkipping = false
          return
        }
      }
    }
    
    queueIndex.value = nextIndex
    const nextTrack = queue.value[nextIndex]
    
    // Priority 1: Use blob-cached audio (fully downloaded)
    const cachedBlobUrl = getCachedAudio(nextTrack.id)
    if (cachedBlobUrl) {
      console.log('[Next] Using blob cache')
      initAudio()
      loading.value = true
      currentTrack.value = nextTrack
      updateMediaSession()
      
      try {
        audio.value.pause()
        audio.value.currentTime = 0
        audio.value.src = cachedBlobUrl
        buffered.value = duration.value
        audio.value.load()
        await audio.value.play()
        loading.value = false
        isSkipping = false  // Success - reset skip flag
        nextTrackPreloaded.value = null
        clearPreloadAudio()
        persistState()
        preloadNextTracks()
        return
      } catch (e) {
        console.error('[Next] Failed to play cached blob, falling back:', e)
        audioCache.delete(nextTrack.id)
      }
    }
    
    // Priority 2: Use preloaded Audio element
    // But first check if the URL token is still valid (not expired)
    const preloadedUrlStillValid = getCachedUrl(nextTrack.id) !== null
    const preloadedAudio = getPreloadedAudio(nextTrack.id)
    
    if (preloadedAudio && preloadedAudio.readyState >= 2) {
      if (!preloadedUrlStillValid) {
        console.log('[Next] Preloaded audio exists but URL token expired, skipping to fetch new URL')
        clearPreloadAudio()
      } else {
        console.log('[Next] Using preloaded Audio element, readyState:', preloadedAudio.readyState)
      
        if (audio.value) {
          audio.value.pause()
          audio.value.src = ''
        }
      
        const oldAudio = audio.value
        audio.value = preloadedAudio
        audio.value.volume = volume.value
        audio.value.muted = isMuted.value
      
        reattachAudioListeners()
      
        loading.value = true
        currentTrack.value = nextTrack
        updateMediaSession()
      
        try {
          await audio.value.play()
          loading.value = false
          isSkipping = false  // Success - reset skip flag
          nextTrackPreloaded.value = null
        
          preloadAudio = oldAudio || new Audio()
          preloadAudio.preload = 'auto'
          preloadAudio.volume = 0
          preloadTrackId = null
        
          persistState()
          preloadNextTracks()
          return
        } catch (e) {
          console.error('[Next] Failed to play preloaded audio, falling back:', e)
          // Restore old audio and continue to next priority
          audio.value = oldAudio
          if (oldAudio) {
            reattachAudioListeners()
          }
          // Clear the broken preload
          clearPreloadAudio()
        }
      }
    }
    
    // Priority 3: Use cached URL for instant start
    const cachedUrl = getCachedUrl(nextTrack.id)
    if (cachedUrl) {
      console.log('[Next] Using cached URL')
      initAudio()
      loading.value = true
      currentTrack.value = nextTrack
      updateMediaSession()
      
      try {
        audio.value.pause()
        audio.value.currentTime = 0
        audio.value.src = cachedUrl
        buffered.value = 0
        await audio.value.play()
        loading.value = false
        isSkipping = false  // Success - reset skip flag
        nextTrackPreloaded.value = null
        clearPreloadAudio()
        persistState()
        preloadNextTracks()
        return
      } catch (e) {
        console.error('[Next] Failed to play from cached URL, falling back:', e)
        urlCache.delete(nextTrack.id)
      }
    }
    
    // Fallback: Regular play (fetch new URL)
    console.log('[Next] Fetching new URL')
    clearPreloadAudio()
    isSkipping = false  // Reset before calling play()
    await play(nextTrack)
  }

  // Previous track
  const prev = async () => {
    if (queue.value.length === 0) return
    
    // Prevent error handlers from triggering during track change
    isSkipping = true
    
    // Mark user interaction and cancel irrelevant preloads
    markUserInteraction()
    cancelIrrelevantPreloads()
    preloadTriggered = false
    
    // If more than 3 seconds played, restart current track
    if (progress.value > 3) {
      seek(0)
      isSkipping = false
      return
    }
    
    let prevIndex = queueIndex.value - 1
    if (prevIndex < 0) {
      if (repeat.value === 'all') {
        prevIndex = queue.value.length - 1
      } else {
        prevIndex = 0
      }
    }
    
    queueIndex.value = prevIndex
    const prevTrack = queue.value[prevIndex]
    
    // Priority 1: Blob cache
    const cachedBlobUrl = getCachedAudio(prevTrack.id)
    if (cachedBlobUrl) {
      console.log('[Prev] Using blob cache')
      initAudio()
      loading.value = true
      currentTrack.value = prevTrack
      updateMediaSession()
      try {
        audio.value.pause()
        audio.value.currentTime = 0
        audio.value.src = cachedBlobUrl
        audio.value.load()
        await audio.value.play()
        isSkipping = false  // Success
        persistState()
        preloadNextTracks()
        return
      } catch (e) {
        console.error('[Prev] Failed to play cached blob, falling back:', e)
        audioCache.delete(prevTrack.id)
      } finally {
        loading.value = false
      }
    }
    
    // Priority 2: Cached URL
    const cachedUrl = getCachedUrl(prevTrack.id)
    if (cachedUrl) {
      console.log('[Prev] Using cached URL')
      initAudio()
      loading.value = true
      currentTrack.value = prevTrack
      updateMediaSession()
      try {
        audio.value.pause()
        audio.value.currentTime = 0
        audio.value.src = cachedUrl
        buffered.value = 0
        await audio.value.play()
        isSkipping = false  // Success
        persistState()
        preloadNextTracks()
        return
      } catch (e) {
        console.error('[Prev] Failed to play from cached URL, falling back:', e)
        urlCache.delete(prevTrack.id)
      } finally {
        loading.value = false
      }
    }
    
    // Fallback: Regular play
    isSkipping = false  // Reset before calling play()
    await play(prevTrack)
  }

  // Seek
  const seek = (time) => {
    if (!audio.value) return
    audio.value.currentTime = time
    updatePositionState()
  }

  // Handle track end
  const handleEnded = async () => {
    // Record play completion
    if (currentTrack.value) {
      try {
        await playerApi.recordPlay(currentTrack.value.id)
      } catch (e) {
        console.error('Failed to record play:', e)
      }
    }
    
    if (repeat.value === 'one') {
      seek(0)
      audio.value.play()
    } else {
      next()
    }
  }

  // Play from queue by index (relative to current)
  const playFromQueue = async (relativeIndex) => {
    const targetIndex = queueIndex.value + 1 + relativeIndex
    if (targetIndex >= 0 && targetIndex < queue.value.length) {
      queueIndex.value = targetIndex
      await play(queue.value[targetIndex])
    }
  }

  // Toggle shuffle
  const toggleShuffle = () => {
    shuffle.value = !shuffle.value
    
    // Generate or clear shuffle order
    if (shuffle.value) {
      // Generate shuffle order starting from current track
      generateShuffleOrder(queueIndex.value)
    } else {
      // Clear shuffle order
      shuffleOrder.value = []
      shuffleIndex.value = -1
    }
    
    // Trigger preload with new order
    preloadTriggered = false
    preloadNextTracks()
    
    persistSettings()
  }

  // Toggle repeat
  const toggleRepeat = () => {
    const modes = ['none', 'all', 'one']
    const currentIndex = modes.indexOf(repeat.value)
    repeat.value = modes[(currentIndex + 1) % modes.length]
    persistSettings()
  }

  // Set volume
  const setVolume = (val) => {
    volume.value = Math.max(0, Math.min(1, val))
    if (audio.value) {
      audio.value.volume = volume.value
    }
    if (volume.value > 0) {
      isMuted.value = false
    }
    persistSettings()
  }

  // Toggle mute
  const toggleMute = () => {
    isMuted.value = !isMuted.value
    if (audio.value) {
      audio.value.muted = isMuted.value
    }
    persistSettings()
  }
  
  // Persist settings to localStorage
  const persistSettings = () => {
    saveSettings({
      volume: volume.value,
      isMuted: isMuted.value,
      shuffle: shuffle.value,
      repeat: repeat.value,
    })
  }
  
  // Persist player state (current track, queue, position)
  const persistState = () => {
    if (!currentTrack.value) {
      clearPlayerState()
      return
    }
    
    savePlayerState({
      currentTrack: currentTrack.value,
      queue: queue.value,
      queueIndex: queueIndex.value,
      progress: progress.value,
      duration: duration.value,
    })
  }
  
  // Start periodic state saving
  const startStateSaving = () => {
    if (stateSaveInterval) return
    stateSaveInterval = setInterval(() => {
      if (currentTrack.value && isPlaying.value) {
        persistState()
      }
    }, STATE_SAVE_INTERVAL)
  }
  
  // Stop periodic state saving
  const stopStateSaving = () => {
    if (stateSaveInterval) {
      clearInterval(stateSaveInterval)
      stateSaveInterval = null
    }
  }
  
  // Restore player state from localStorage
  const restoreState = async () => {
    if (stateRestored.value || !savedState) return false
    
    stateRestored.value = true
    
    // Check if saved state is not too old (24 hours max)
    const maxAge = 24 * 60 * 60 * 1000 // 24 hours
    if (savedState.savedAt && Date.now() - savedState.savedAt > maxAge) {
      console.log('[Player] Saved state too old, discarding')
      clearPlayerState()
      return false
    }
    
    if (!savedState.currentTrack || !savedState.queue || savedState.queue.length === 0) {
      return false
    }
    
    console.log('[Player] Restoring saved state:', {
      track: savedState.currentTrack?.title,
      queueLength: savedState.queue?.length,
      progress: savedState.progress
    })
    
    // Restore queue and current track
    queue.value = savedState.queue
    queueIndex.value = savedState.queueIndex ?? 0
    currentTrack.value = savedState.currentTrack
    duration.value = savedState.duration ?? 0
    progress.value = savedState.progress ?? 0
    
    // Initialize audio but don't auto-play (paused state)
    initAudio()
    updateMediaSession()
    
    // Start state saving
    startStateSaving()
    
    // Pre-fetch URLs for current and next tracks immediately
    // This ensures instant playback when user presses play
    const tracksToPrefetch = [savedState.currentTrack]
    for (let i = 1; i <= 3; i++) {
      const idx = (savedState.queueIndex ?? 0) + i
      if (idx < savedState.queue.length) {
        tracksToPrefetch.push(savedState.queue[idx])
      }
    }
    
    // Fire batch URL prefetch (don't await - background)
    const trackIds = tracksToPrefetch.map(t => t.id)
    playerApi.getBatchUrls(trackIds)
      .then(response => {
        const urlData = response.data.urls || []
        for (const item of urlData) {
          if (item.url && !item.error) {
            setCachedUrl(item.track_id, item.url, item.expires_at)
          }
        }
        console.log(`[Restore] Pre-cached ${urlData.filter(u => u.url).length} URLs`)
      })
      .catch(e => console.warn('[Restore] Prefetch failed:', e))
    
    return true
  }
  
  // Resume playback from restored state
  const resumeFromState = async () => {
    if (!currentTrack.value) return
    
    const savedProgress = progress.value
    const trackId = currentTrack.value.id
    
    try {
      loading.value = true
      
      // Priority 1: Check blob cache
      const cachedBlobUrl = getCachedAudio(trackId)
      if (cachedBlobUrl) {
        console.log('[Resume] Using cached blob')
        audio.value.src = cachedBlobUrl
        audio.value.load()
        
        if (savedProgress > 0) {
          audio.value.currentTime = savedProgress
        }
        
        await audio.value.play()
        loading.value = false
        
        // Start preloading next tracks
        preloadNextTracks()
        return
      }
      
      // Priority 2: Check URL cache
      let url = getCachedUrl(trackId)
      
      // Fallback: Get new stream URL
      if (!url) {
        console.log('[Resume] Fetching new stream URL')
        const response = await playerApi.getStreamUrl(currentTrack.value.id)
        url = response.data.url
        if (response.data.expires_at) {
          setCachedUrl(trackId, url, response.data.expires_at)
        }
      } else {
        console.log('[Resume] Using cached URL')
      }
      
      audio.value.src = url
      buffered.value = 0
      
      // Wait for metadata to load before seeking
      await new Promise((resolve, reject) => {
        const onLoaded = () => {
          audio.value.removeEventListener('loadedmetadata', onLoaded)
          audio.value.removeEventListener('error', onError)
          resolve()
        }
        const onError = (e) => {
          audio.value.removeEventListener('loadedmetadata', onLoaded)
          audio.value.removeEventListener('error', onError)
          reject(e)
        }
        audio.value.addEventListener('loadedmetadata', onLoaded)
        audio.value.addEventListener('error', onError)
        audio.value.load()
      })
      
      // Seek to saved position
      if (savedProgress > 0 && savedProgress < audio.value.duration - 1) {
        audio.value.currentTime = savedProgress
      }
      
      await audio.value.play()
      loading.value = false
      
      // Start preloading next tracks immediately after resume
      preloadNextTracks()
      
    } catch (error) {
      console.error('Failed to resume playback:', error)
      loading.value = false
    }
  }
  
  // Check if there's a saved state to restore
  const hasSavedState = () => {
    return savedState && savedState.currentTrack && savedState.queue?.length > 0
  }

  // Play next (insert track after current)
  const playNext = (track) => {
    const insertIndex = queueIndex.value + 1
    // Remove if already in queue
    const existingIndex = queue.value.findIndex(t => t.id === track.id)
    if (existingIndex !== -1) {
      queue.value.splice(existingIndex, 1)
      if (existingIndex < queueIndex.value) {
        queueIndex.value--
      }
    }
    queue.value.splice(insertIndex, 0, track)
    persistState() // Save queue change
  }

  // Add to queue (at the end)
  const addToQueue = (track) => {
    if (!queue.value.find(t => t.id === track.id)) {
      queue.value.push(track)
      persistState() // Save queue change
    }
  }

  // Remove from queue (by index relative to upcoming queue, i.e., after current track)
  const removeFromQueue = (relativeIndex) => {
    const targetIndex = queueIndex.value + 1 + relativeIndex
    if (targetIndex > queueIndex.value && targetIndex < queue.value.length) {
      queue.value.splice(targetIndex, 1)
      persistState() // Save queue change
    }
  }

  // Move item in queue (reorder)
  const moveInQueue = (fromRelativeIndex, toRelativeIndex) => {
    const fromIndex = queueIndex.value + 1 + fromRelativeIndex
    const toIndex = queueIndex.value + 1 + toRelativeIndex
    
    if (fromIndex > queueIndex.value && fromIndex < queue.value.length &&
        toIndex > queueIndex.value && toIndex <= queue.value.length) {
      const [item] = queue.value.splice(fromIndex, 1)
      queue.value.splice(toIndex > fromIndex ? toIndex - 1 : toIndex, 0, item)
      persistState() // Save queue change
    }
  }

  // Stop
  const stop = () => {
    if (audio.value) {
      audio.value.pause()
      audio.value.src = ''
    }
    currentTrack.value = null
    isPlaying.value = false
    progress.value = 0
    duration.value = 0
    queue.value = []
    queueIndex.value = -1
    stopStateSaving()
    clearPlayerState()
  }

  return {
    currentTrack,
    queue,
    queueIndex,
    isPlaying,
    progress,
    duration,
    volume,
    isMuted,
    shuffle,
    repeat,
    loading,
    buffered,
    lastError,
    stateRestored,
    play,
    toggle,
    next,
    prev,
    seek,
    setVolume,
    toggleMute,
    playNext,
    addToQueue,
    removeFromQueue,
    moveInQueue,
    toggleShuffle,
    toggleRepeat,
    playFromQueue,
    stop,
    setOnTrackUnavailable,
    restoreState,
    resumeFromState,
    hasSavedState,
    persistState,
  }
})
