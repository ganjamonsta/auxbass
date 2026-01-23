import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { playerApi, tracksApi } from '../api/client'

// ============== LocalStorage helpers ==============
const STORAGE_KEY = 'tg_player_settings'

const loadSettings = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('Failed to load player settings:', e)
  }
  return {}
}

const saveSettings = (settings) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch (e) {
    console.error('Failed to save player settings:', e)
  }
}

// Load saved settings
const savedSettings = loadSettings()

// Audio cache - stores blob URLs for already loaded tracks
const audioCache = new Map()
const MAX_CACHE_SIZE = 50

const getCachedAudio = (trackId) => {
  return audioCache.get(trackId)
}

const setCachedAudio = (trackId, blobUrl) => {
  // Limit cache size - use LRU-like eviction (remove oldest)
  if (audioCache.size >= MAX_CACHE_SIZE) {
    const firstKey = audioCache.keys().next().value
    const oldUrl = audioCache.get(firstKey)
    URL.revokeObjectURL(oldUrl)
    audioCache.delete(firstKey)
  }
  audioCache.set(trackId, blobUrl)
}

// ============== Adaptive Preload System ==============
// Tracks download speed to adapt preload strategy
let _lastDownloadSpeed = 0  // bytes per second
let _userInteractionTime = 0  // timestamp of last user action (play/next/prev)
const USER_INTERACTION_COOLDOWN = 2000  // 2 seconds - wait before resuming background preloads

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
  
  // Flag to prevent duplicate preload triggers per track
  let preloadTriggered = false
  
  // Callback for track unavailable
  let onTrackUnavailableCallback = null
  const setOnTrackUnavailable = (callback) => {
    onTrackUnavailableCallback = callback
  }

  // Update Media Session metadata
  const updateMediaSession = () => {
    if (!('mediaSession' in navigator) || !currentTrack.value) return
    
    const track = currentTrack.value
    const artwork = track.cover_art_url ? [
      { src: track.cover_art_url, sizes: '96x96', type: 'image/jpeg' },
      { src: track.cover_art_url, sizes: '128x128', type: 'image/jpeg' },
      { src: track.cover_art_url, sizes: '256x256', type: 'image/jpeg' },
      { src: track.cover_art_url, sizes: '512x512', type: 'image/jpeg' },
    ] : []
    
    navigator.mediaSession.metadata = new MediaMetadata({
      title: track.title || 'Unknown',
      artist: track.artist || 'Unknown Artist',
      album: track.album || '',
      artwork
    })
  }

  // Setup Media Session handlers
  const setupMediaSession = () => {
    if (!('mediaSession' in navigator)) return
    
    navigator.mediaSession.setActionHandler('play', () => {
      if (audio.value) audio.value.play()
    })
    
    navigator.mediaSession.setActionHandler('pause', () => {
      if (audio.value) audio.value.pause()
    })
    
    navigator.mediaSession.setActionHandler('previoustrack', () => {
      prev()
    })
    
    navigator.mediaSession.setActionHandler('nexttrack', () => {
      next()
    })
    
    navigator.mediaSession.setActionHandler('seekto', (details) => {
      if (details.seekTime !== undefined) {
        seek(details.seekTime)
      }
    })
    
    navigator.mediaSession.setActionHandler('seekbackward', (details) => {
      const skipTime = details.seekOffset || 10
      seek(Math.max(0, progress.value - skipTime))
    })
    
    navigator.mediaSession.setActionHandler('seekforward', (details) => {
      const skipTime = details.seekOffset || 10
      seek(Math.min(duration.value, progress.value + skipTime))
    })
  }

  // Update Media Session playback state
  const updatePlaybackState = () => {
    if (!('mediaSession' in navigator)) return
    navigator.mediaSession.playbackState = isPlaying.value ? 'playing' : 'paused'
  }

  // Update Media Session position
  const updatePositionState = () => {
    if (!('mediaSession' in navigator) || !audio.value || !duration.value) return
    try {
      navigator.mediaSession.setPositionState({
        duration: duration.value,
        playbackRate: audio.value.playbackRate,
        position: progress.value
      })
    } catch (e) {
      // Ignore errors
    }
  }

  // Initialize audio element
  const initAudio = () => {
    if (audio.value) return
    
    audio.value = new Audio()
    audio.value.volume = volume.value
    // Changed to 'metadata' to prevent aggressive buffering blocking startup
    // user reported "2 minutes loaded" issues causing slow start
    audio.value.preload = 'metadata' 
    
    // Setup Media Session handlers once
    setupMediaSession()
    
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

      // Update position state every 5 seconds for media session
      if (Math.floor(progress.value) % 5 === 0) {
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
      updatePlaybackState()
    })
    
    audio.value.addEventListener('pause', () => {
      isPlaying.value = false
      updatePlaybackState()
    })
    
    audio.value.addEventListener('error', (e) => {
      console.error('Audio error:', e)
      loading.value = false
    })
    
    // Preload next track when we have a safe buffer
    // Note: preloadTriggered is defined at store level, reset in play()
    audio.value.addEventListener('timeupdate', () => {
      // Calculate how many seconds we have buffered ahead of current position
      const currentBuffer = (buffered.value || 0) - progress.value
      
      // Smart Preload Condition:
      // 1. We have > 20 seconds of audio buffered ahead (safe reserve)
      // 2. OR the entire track is almost fully buffered
      // 3. AND we haven't started preloading yet
      const isBufferHealthy = currentBuffer > 20 || (duration.value > 0 && buffered.value >= duration.value - 2)

      if (duration.value > 0 && !preloadTriggered && isBufferHealthy) {
        console.log(`[Smart Preload] Triggering: Buffer ahead=${currentBuffer.toFixed(1)}s`)
        preloadTriggered = true
        preloadNextTrack()
      }
    })
    
    // Reset preload flag on new track
    audio.value.addEventListener('loadstart', () => {
      // Don't reset here, handled in play() for better control
    })
  }

  // Preload next tracks (caches them for gapless playback)
  // ADAPTIVE: Adjusts how many tracks to preload based on user activity
  const preloadNextTrack = async () => {
    if (queue.value.length === 0) return
    
    // If user is actively switching tracks, don't start new preloads
    // This prevents wasting bandwidth on tracks user might skip
    if (isUserActivelyBrowsing()) {
      console.log('[Preload] User actively browsing, deferring preload...')
      // Retry after cooldown
      setTimeout(() => preloadNextTrack(), USER_INTERACTION_COOLDOWN)
      return
    }
    
    // Determine how many tracks to preload based on network speed
    // Fast connection (>1MB/s): preload 2-3 tracks
    // Slow connection (<500KB/s): preload only 1 track
    let maxPreload = 2
    if (_lastDownloadSpeed > 0) {
      if (_lastDownloadSpeed > 1024 * 1024) {
        maxPreload = 3
      } else if (_lastDownloadSpeed < 500 * 1024) {
        maxPreload = 1
      }
    }
    
    // Collect tracks to preload
    const tracksToPreload = []
    
    for (let offset = 1; offset <= maxPreload; offset++) {
      let nextIndex = queueIndex.value + offset
      if (nextIndex >= queue.value.length) {
        if (repeat.value === 'all') {
          nextIndex = nextIndex % queue.value.length
        } else {
          break
        }
      }
      
      const track = queue.value[nextIndex]
      if (track && !getCachedAudio(track.id)) {
        tracksToPreload.push(track)
      }
    }
    
    // Mark first one as "preloaded" for quick access
    const nextTrack = queue.value[queueIndex.value + 1] || 
                      (repeat.value === 'all' ? queue.value[0] : null)
    
    if (nextTrack && getCachedAudio(nextTrack.id)) {
      nextTrackPreloaded.value = {
        track: nextTrack,
        url: getCachedAudio(nextTrack.id),
        cached: true
      }
    }
    
    // Preload tracks SEQUENTIALLY to prioritize next track
    // This ensures track N+1 finishes before N+2 starts
    for (const track of tracksToPreload) {
      // Re-check if user became active
      if (isUserActivelyBrowsing()) {
        console.log('[Preload] User became active, pausing preloads')
        break
      }
      await preloadSingleTrack(track)
    }
  }
  
  // Set to track which tracks are currently being preloaded
  // Map<trackId, AbortController>
  const _preloadingTracks = new Map()
  
  // Cancel preloads that are no longer relevant (not in next N positions)
  const cancelIrrelevantPreloads = () => {
    const relevantIds = new Set()
    
    // Keep next 3 tracks as relevant
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
      // Check if track is cached (blob URL)
      const cachedUrl = getCachedAudio(track.id)
      if (cachedUrl) {
        // Stop current playback and reset before changing source
        audio.value.pause()
        audio.value.currentTime = 0
        audio.value.src = cachedUrl
        audio.value.load()  // Force reload with new source
        await audio.value.play()
        loading.value = false
        
        // Start preloading next tracks immediately
        nextTrackPreloaded.value = null
        preloadNextTrack()
        return
      }
      
      // Get stream URL from API
      const response = await playerApi.getStreamUrl(track.id)
      const { url } = response.data
      
      // Stream directly - fastest start time
      // Caching is done via preloadNextTrack() which loads NEXT tracks in background
      audio.value.src = url
      buffered.value = 0
      await audio.value.play()
      
      // Reset preload triggering flag for the new track
      preloadTriggered = false
      nextTrackPreloaded.value = null
      
      // Note: We deliberately DO NOT call preloadNextTrack() here immediately.
      // We wait for the 'timeupdate' event to confirm we have a healthy buffer
      // before starting to download the next track. This prevents bandwidth contention.
      
    } catch (error) {
      console.error('Failed to play track:', error)
      
      // Check if file is unavailable (503 error)
      if (error.response?.status === 503) {
        lastError.value = {
          type: 'unavailable',
          track: track,
          message: error.response?.data?.detail || 'Файл недоступен'
        }
        
        // Mark track as unavailable
        try {
          await tracksApi.markUnavailable(track.id)
          track.is_unavailable = true
        } catch (e) {
          console.error('Failed to mark track unavailable:', e)
        }
        
        // Call callback if set
        if (onTrackUnavailableCallback) {
          onTrackUnavailableCallback(track, lastError.value.message)
        }
        
        // Auto-skip to next track
        setTimeout(() => next(), 1500)
      }
    } finally {
      loading.value = false
    }
  }

  // Toggle play/pause
  const toggle = () => {
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
    
    // Mark user interaction and cancel irrelevant preloads
    markUserInteraction()
    cancelIrrelevantPreloads()
    preloadTriggered = false
    
    let nextIndex
    
    if (shuffle.value) {
      nextIndex = Math.floor(Math.random() * queue.value.length)
    } else {
      nextIndex = queueIndex.value + 1
      if (nextIndex >= queue.value.length) {
        if (repeat.value === 'all') {
          nextIndex = 0
        } else {
          // End of queue, no repeat - stop playback
          isPlaying.value = false
          return
        }
      }
    }
    
    queueIndex.value = nextIndex
    const nextTrack = queue.value[nextIndex]
    
    // Use preloaded/cached if available
    const cachedUrl = getCachedAudio(nextTrack.id)
    const preloadedUrl = nextTrackPreloaded.value?.track?.id === nextTrack.id 
      ? nextTrackPreloaded.value.url 
      : null
    
    if (cachedUrl || preloadedUrl) {
      initAudio()
      loading.value = true
      currentTrack.value = nextTrack
      updateMediaSession()
      
      try {
        // Stop current playback and reset before changing source
        audio.value.pause()
        audio.value.currentTime = 0
        audio.value.src = cachedUrl || preloadedUrl
        buffered.value = duration.value // Buffered fully if cached
        audio.value.load()  // Force reload with new source
        await audio.value.play()
        loading.value = false
        nextTrackPreloaded.value = null
        
        // Immediately start preloading next tracks for gapless playback
        preloadNextTrack()
        return  // Success - exit
      } catch (e) {
        console.error('Failed to play cached/preloaded track, falling back:', e)
        // Invalidate bad cache entry
        if (cachedUrl) {
          audioCache.delete(nextTrack.id)
        }
        nextTrackPreloaded.value = null
        // Fall through to regular play()
      }
    }
    
    // Regular play (no cache or cache failed)
    await play(nextTrack)
  }

  // Previous track
  const prev = async () => {
    if (queue.value.length === 0) return
    
    // Mark user interaction and cancel irrelevant preloads
    markUserInteraction()
    cancelIrrelevantPreloads()
    preloadTriggered = false
    
    // If more than 3 seconds played, restart current track
    if (progress.value > 3) {
      seek(0)
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
    
    // Check cache for previous track
    const prevTrack = queue.value[prevIndex]
    const cachedUrl = getCachedAudio(prevTrack.id)
    if (cachedUrl) {
      initAudio()
      loading.value = true
      currentTrack.value = prevTrack
      updateMediaSession()
      try {
        // Stop current playback and reset before changing source
        audio.value.pause()
        audio.value.currentTime = 0
        audio.value.src = cachedUrl
        audio.value.load()  // Force reload with new source
        await audio.value.play()
      } catch (e) {
        console.error('Failed to play cached track:', e)
      } finally {
        loading.value = false
      }
    } else {
      await play(prevTrack)
    }
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
  }

  // Add to queue (at the end)
  const addToQueue = (track) => {
    if (!queue.value.find(t => t.id === track.id)) {
      queue.value.push(track)
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
    play,
    toggle,
    next,
    prev,
    seek,
    setVolume,
    toggleMute,
    playNext,
    addToQueue,
    toggleShuffle,
    toggleRepeat,
    playFromQueue,
    stop,
    setOnTrackUnavailable,
  }
})
