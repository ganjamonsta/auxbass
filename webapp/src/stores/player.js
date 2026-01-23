import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { playerApi, tracksApi } from '../api/client'

export const usePlayerStore = defineStore('player', () => {
  // State
  const audio = ref(null)
  const currentTrack = ref(null)
  const queue = ref([])
  const queueIndex = ref(-1)
  const isPlaying = ref(false)
  const progress = ref(0)
  const duration = ref(0)
  const volume = ref(1)
  const isMuted = ref(false)
  const shuffle = ref(false)
  const repeat = ref('none') // none, one, all
  const loading = ref(false)
  const nextTrackPreloaded = ref(null)
  const lastError = ref(null)  // For error notifications
  
  // Callback for track unavailable
  let onTrackUnavailableCallback = null
  const setOnTrackUnavailable = (callback) => {
    onTrackUnavailableCallback = callback
  }

  // Initialize audio element
  const initAudio = () => {
    if (audio.value) return
    
    audio.value = new Audio()
    audio.value.volume = volume.value
    audio.value.preload = 'auto'  // Aggressive preloading for faster start
    
    // canplay event - audio ready to play
    audio.value.addEventListener('canplay', () => {
      loading.value = false
    })
    
    // waiting event - buffering
    audio.value.addEventListener('waiting', () => {
      loading.value = true
    })
    
    audio.value.addEventListener('timeupdate', () => {
      progress.value = audio.value.currentTime
    })
    
    audio.value.addEventListener('durationchange', () => {
      duration.value = audio.value.duration
    })
    
    audio.value.addEventListener('ended', () => {
      handleEnded()
    })
    
    audio.value.addEventListener('play', () => {
      isPlaying.value = true
    })
    
    audio.value.addEventListener('pause', () => {
      isPlaying.value = false
    })
    
    audio.value.addEventListener('error', (e) => {
      console.error('Audio error:', e)
      loading.value = false
    })
    
    // Preload next track when current is 80% done
    audio.value.addEventListener('timeupdate', () => {
      if (duration.value > 0 && progress.value / duration.value > 0.8) {
        preloadNextTrack()
      }
    })
  }

  // Preload next track
  const preloadNextTrack = async () => {
    if (nextTrackPreloaded.value || queue.value.length === 0) return
    
    let nextIndex = queueIndex.value + 1
    if (nextIndex >= queue.value.length) {
      if (repeat.value === 'all') nextIndex = 0
      else return
    }
    
    const nextTrack = queue.value[nextIndex]
    if (!nextTrack) return
    
    try {
      const response = await playerApi.getStreamUrl(nextTrack.id)
      nextTrackPreloaded.value = {
        track: nextTrack,
        url: response.data.url
      }
    } catch (e) {
      console.error('Failed to preload next track:', e)
    }
  }

  // Play track
  const play = async (track, newQueue = null) => {
    initAudio()
    
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
    
    loading.value = true
    currentTrack.value = track
    lastError.value = null
    
    try {
      // Get stream URL from API
      const response = await playerApi.getStreamUrl(track.id)
      const { url } = response.data
      
      audio.value.src = url
      await audio.value.play()
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
    
    let nextIndex
    
    if (shuffle.value) {
      nextIndex = Math.floor(Math.random() * queue.value.length)
    } else {
      nextIndex = queueIndex.value + 1
      if (nextIndex >= queue.value.length) {
        if (repeat.value === 'all') {
          nextIndex = 0
        } else {
          return
        }
      }
    }
    
    queueIndex.value = nextIndex
    const nextTrack = queue.value[nextIndex]
    
    // Use preloaded if available
    if (nextTrackPreloaded.value?.track?.id === nextTrack.id) {
      initAudio()
      loading.value = true
      currentTrack.value = nextTrack
      try {
        audio.value.src = nextTrackPreloaded.value.url
        await audio.value.play()
      } catch (e) {
        console.error('Failed to play preloaded track:', e)
      } finally {
        loading.value = false
        nextTrackPreloaded.value = null
      }
    } else {
      await play(nextTrack)
    }
  }

  // Previous track
  const prev = async () => {
    if (queue.value.length === 0) return
    
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
    await play(queue.value[prevIndex])
  }

  // Seek
  const seek = (time) => {
    if (!audio.value) return
    audio.value.currentTime = time
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
  }

  // Toggle repeat
  const toggleRepeat = () => {
    const modes = ['none', 'all', 'one']
    const currentIndex = modes.indexOf(repeat.value)
    repeat.value = modes[(currentIndex + 1) % modes.length]
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
  }

  // Toggle mute
  const toggleMute = () => {
    isMuted.value = !isMuted.value
    if (audio.value) {
      audio.value.muted = isMuted.value
    }
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
