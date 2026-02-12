/**
 * Player Store — Core
 *
 * Refactored from a 2728-line god-object into a ~900-line core that delegates to:
 *   - playerAudioEngine.js  — audio element lifecycle, event listeners (BUG-3 fix)
 *   - playerEnhancer.js     — WebAudio EQ / compressor
 *   - playerShuffle.js      — Fisher-Yates shuffle order, lazy shuffle helpers
 *   - playerPreload.js      — batch URL fetch, adaptive preload, blob caching
 *   - playerMediaSession.js — lock screen, media keys, keyboard shortcuts
 *   - playerStallRecovery.js — stall detection, retry, cascading-skip guard
 *   - playerResolver.js     — resolveAudioSource (eliminates 4× priority-cascade duplication)
 *   - playerCache.js        — URL + blob cache (unchanged)
 *   - playerStorage.js      — localStorage persistence (unchanged)
 */
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { playerApi, tracksApi, playlistsApi, albumsApi } from '../api/client'
import { useNetworkMonitor } from '../composables/useNetworkMonitor'

// --- Extracted modules ---
import {
  setupAudioListeners,
  cleanupAudioListeners,
  isTrackNotStreamable,
  createAudioElement,
} from './playerAudioEngine'

import {
  initAudioContext,
  connectAudioSource as connectEnhancer,
  updateEnhancerParams as _updateEnhancer,
} from './playerEnhancer'

import {
  generateShuffleOrder as genShuffle,
  getNextTrackIndex as calcNextIdx,
} from './playerShuffle'

import {
  markUserInteraction,
  isUserActivelyBrowsing,
  cancelIrrelevantPreloads,
  collectRelevantIds,
  collectTracksToPreload,
  executeBatchPreload,
} from './playerPreload'

import {
  updateMediaSession as _updateMS,
  updatePlaybackState as _updatePBS,
  updatePositionState as _updatePS,
  setupMediaSession,
  setupKeyboardShortcuts,
} from './playerMediaSession'

import {
  clearStallTimer,
  startStallTimer,
  resetStallRetry,
  handleStallTimeout,
  checkCascadingSkips,
  resetSkipCount,
  getAudioRetryCount,
  incrementAudioRetry,
  resetAudioRetry,
  getAudioRetryDelay,
  getMaxAudioRetries,
} from './playerStallRecovery'

import { resolveAudioSource } from './playerResolver'

// --- Existing helpers ---
import {
  loadSettings, saveSettings, loadPlayerState, savePlayerState,
  clearPlayerState, STATE_SAVE_INTERVAL,
} from './playerStorage'

import {
  getCachedUrl, setCachedUrl, deleteCachedUrl,
  getCachedAudio, setCachedAudio, deleteCachedAudio,
  preloadTrackWithAudio, getPreloadedAudio,
  clearPreloadAudio, getPreloadTrackId, recyclePreloadAudio,
} from './playerCache'

import { getDisplayTitle, getDisplayArtist } from '../utils/formatters'

// Load saved settings/state
const savedSettings = loadSettings()
const savedState = loadPlayerState()

export const usePlayerStore = defineStore('player', () => {
  // ===================== STATE =====================
  const audio = ref(null)
  const currentTrack = ref(null)
  const queue = ref([])
  const queueIndex = ref(-1)
  const shuffleOrder = ref([])
  const shuffleIndex = ref(-1)
  const isPlaying = ref(false)
  const progress = ref(0)
  const duration = ref(0)
  const volume = ref(savedSettings.volume ?? 1)
  const isMuted = ref(savedSettings.isMuted ?? false)
  const shuffle = ref(savedSettings.shuffle ?? false)
  const repeat = ref(savedSettings.repeat ?? 'none')
  const uiScale = ref(savedSettings.uiScale ?? 1.0)

  // Enhancer
  const enhancerEnabled = ref(savedSettings.enhancerEnabled ?? false)
  const bassGain = ref(savedSettings.bassGain ?? 0)
  const trebleGain = ref(savedSettings.trebleGain ?? 0)
  const autoGain = ref(savedSettings.autoGain ?? false)

  const loading = ref(false)
  const buffered = ref(0)
  const nextTrackPreloaded = ref(null)
  const lastError = ref(null)
  const stateRestored = ref(false)
  const hdTrackInfo = ref(null)

  // Lazy shuffle
  const lazyShuffleIds = ref([])
  const lazyShuffleIndex = ref(-1)
  const lazyShuffleContext = ref(null)

  // Private flags
  let stateSaveInterval = null
  let preloadTriggered = false
  let isSkipping = false
  let _playGeneration = 0
  let shuffleInProgress = false
  let lastPositionUpdate = 0

  // Callback for track unavailable
  let onTrackUnavailableCallback = null
  const setOnTrackUnavailable = (cb) => { onTrackUnavailableCallback = cb }

  // ===================== NETWORK RECOVERY =====================
  const _networkMonitor = useNetworkMonitor()
  watch(() => _networkMonitor.networkRecovered.value, (recovered) => {
    if (recovered && currentTrack.value && !isPlaying.value && lastError.value?.type === 'stall_timeout') {
      console.log('[Player] Network recovered, retrying last stalled track')
      lastError.value = null
      resetStallRetry()
      play(currentTrack.value)
    }
  })

  // ===================== ENHANCER WATCHERS =====================
  watch([enhancerEnabled, bassGain, trebleGain, autoGain], () => {
    _updateEnhancer({
      enabled: enhancerEnabled.value,
      bass: bassGain.value,
      treble: trebleGain.value,
      autoGain: autoGain.value,
    })
    persistSettings()
  })
  watch(uiScale, () => persistSettings())

  // ===================== HELPERS =====================
  const isLazyShuffleMode = () => lazyShuffleIds.value.length > 0 && lazyShuffleIndex.value >= 0

  const clearLazyShuffle = () => {
    lazyShuffleIds.value = []
    lazyShuffleIndex.value = -1
    lazyShuffleContext.value = null
  }

  const generateShuffleOrder = (startingIndex = -1) => {
    const result = genShuffle(queue.value.length, startingIndex)
    shuffleOrder.value = result.order
    shuffleIndex.value = result.index
  }

  const getNextTrackIndex = () => calcNextIdx({
    shuffle: shuffle.value,
    shuffleOrder: shuffleOrder.value,
    shuffleIndex: shuffleIndex.value,
    queueIndex: queueIndex.value,
    queueLength: queue.value.length,
    repeat: repeat.value,
  })

  const getNextTrackForPreload = () => {
    const idx = getNextTrackIndex()
    return idx === -1 ? null : queue.value[idx] || null
  }

  const loadTrackById = async (trackId) => {
    try {
      const r = await tracksApi.getOne(trackId)
      return r.data
    } catch (e) {
      console.error(`[Lazy Shuffle] Failed to load track ${trackId}:`, e)
      return null
    }
  }

  // ===================== RELEVANT IDS HELPER =====================
  const _collectRelevantIds = () => collectRelevantIds({
    isLazy: isLazyShuffleMode(),
    lazyShuffleIds: lazyShuffleIds.value,
    lazyShuffleIndex: lazyShuffleIndex.value,
    shuffle: shuffle.value,
    shuffleOrder: shuffleOrder.value,
    shuffleIndex: shuffleIndex.value,
    queue: queue.value,
    queueIndex: queueIndex.value,
    repeat: repeat.value,
  })

  // ===================== MEDIA SESSION WRAPPERS =====================
  const updateMediaSession = () => _updateMS(currentTrack.value, updatePlaybackState)
  const updatePlaybackState = () => _updatePBS(isPlaying.value)
  const updatePositionState = () => _updatePS(audio.value, progress.value, duration.value)

  // ===================== PERSISTENCE =====================
  const persistSettings = () => {
    saveSettings({
      volume: volume.value, isMuted: isMuted.value,
      shuffle: shuffle.value, repeat: repeat.value,
      uiScale: uiScale.value,
      enhancerEnabled: enhancerEnabled.value,
      bassGain: bassGain.value, trebleGain: trebleGain.value,
      autoGain: autoGain.value,
    })
  }

  const persistState = () => {
    if (!currentTrack.value) { clearPlayerState(); return }
    savePlayerState({
      currentTrack: currentTrack.value,
      queue: queue.value,
      queueIndex: queueIndex.value,
      progress: progress.value,
      duration: duration.value,
    })
  }

  const startStateSaving = () => {
    if (stateSaveInterval) return
    stateSaveInterval = setInterval(() => {
      if (currentTrack.value && isPlaying.value) persistState()
    }, STATE_SAVE_INTERVAL)
  }

  const stopStateSaving = () => {
    if (stateSaveInterval) { clearInterval(stateSaveInterval); stateSaveInterval = null }
  }

  // ===================== PRELOAD ORCHESTRATOR =====================
  const preloadNextTracks = async () => {
    if (isUserActivelyBrowsing()) {
      setTimeout(() => preloadNextTracks(), 1000)
      return
    }

    const params = {
      isLazy: isLazyShuffleMode(),
      lazyShuffleIds: lazyShuffleIds.value,
      lazyShuffleIndex: lazyShuffleIndex.value,
      shuffle: shuffle.value,
      shuffleOrder: shuffleOrder.value,
      shuffleIndex: shuffleIndex.value,
      queue: queue.value,
      queueIndex: queueIndex.value,
      repeat: repeat.value,
      getNextTrackForPreload,
    }

    const { trackIds, nextTrack: collectedNext, isLazy } = collectTracksToPreload(params)

    // For lazy mode, determine next track from lazy shuffle IDs
    let nextT = collectedNext
    if (isLazy && lazyShuffleIds.value.length > 0) {
      const nextIdx = lazyShuffleIndex.value + 1
      if (nextIdx < lazyShuffleIds.value.length) {
        nextT = { id: lazyShuffleIds.value[nextIdx] }
      }
    }

    await executeBatchPreload({
      trackIds,
      getBatchUrls: playerApi.getBatchUrls.bind(playerApi),
      nextTrack: nextT,
      onNextPreloaded: (info) => { nextTrackPreloaded.value = info },
    })
  }

  const preloadNextTrack = preloadNextTracks  // legacy alias

  // ===================== AUDIO EVENT HANDLERS =====================
  const buildAudioHandlers = () => ({
    onCanPlay: () => {
      loading.value = false; clearStallTimer(); resetStallRetry()
    },
    onPlaying: () => {
      loading.value = false; clearStallTimer(); resetStallRetry(); resetAudioRetry()
    },
    onWaiting: () => {
      if (audio.value && audio.value.readyState < 3) {
        loading.value = true
        const isInitial = audio.value.readyState === 0 && audio.value.currentTime === 0
        startStallTimer(isInitial, () => stallRecovery())
      }
    },
    onStalled: () => {
      if (audio.value && (!audio.value.paused || loading.value)) {
        startStallTimer(false, () => stallRecovery())
      }
    },
    onSuspend: () => { /* normal browser behavior */ },
    onTimeUpdate: () => {
      if (!audio.value) return
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
      clearStallTimer()
      const now = Date.now()
      if (now - lastPositionUpdate >= 1000) {
        lastPositionUpdate = now
        updatePositionState()
      }
      // Fallback preload trigger
      if (duration.value > 0 && !preloadTriggered && progress.value > 0.5) {
        preloadTriggered = true
        preloadNextTracks()
      }
    },
    onProgress: () => {
      if (!audio.value) return
      if (audio.value.buffered.length > 0) {
        buffered.value = audio.value.buffered.end(audio.value.buffered.length - 1)
        if (loading.value && buffered.value - progress.value > 2) {
          loading.value = false; clearStallTimer()
        }
      }
    },
    onDurationChange: () => {
      if (audio.value) { duration.value = audio.value.duration; updatePositionState() }
    },
    onEnded: (e) => {
      if (e.target?._obsolete) return
      clearStallTimer()
      handleEnded()
    },
    onPlay: () => {
      if (audio.value) audio.value._obsolete = false
      isPlaying.value = true
      isSkipping = false
      resetSkipCount(); resetAudioRetry(); resetStallRetry()
      clearStallTimer()
      updatePlaybackState()
      startStateSaving()
    },
    onPause: () => {
      isPlaying.value = false
      clearStallTimer()
      updatePlaybackState()
      persistState()
    },
    onError: async (e) => {
      loading.value = false; clearStallTimer()
      if (e.target?._obsolete) return
      const el = audio.value
      if (!el) return
      const errorCode = el.error?.code
      if (errorCode === 1 || isSkipping) return

      // Network retry
      const track = currentTrack.value
      if (errorCode === 2 && getAudioRetryCount() < getMaxAudioRetries() && track) {
        incrementAudioRetry()
        loading.value = true
        try {
          await new Promise(r => setTimeout(r, getAudioRetryDelay()))
          const resp = await playerApi.getStreamUrl(track.id)
          setCachedUrl(track.id, resp.data.url, resp.data.expires_at)
          const savedTime = el.currentTime || 0
          el.src = resp.data.url
          if (savedTime > 1) el.currentTime = savedTime - 0.5
          await el.play()
          loading.value = false
          return
        } catch (_) { loading.value = false }
      }

      // Cascading skip guard
      if (checkCascadingSkips()) {
        lastError.value = { type: 'cascade_error', track, message: 'Слишком много ошибок подряд, воспроизведение остановлено' }
        window.dispatchEvent(new CustomEvent('player:error', { detail: lastError.value }))
        isPlaying.value = false
        return
      }

      const errorNames = { 2: 'NETWORK', 3: 'DECODE', 4: 'SRC_NOT_SUPPORTED' }
      if (errorCode >= 2) {
        lastError.value = { type: 'audio_error', track, message: `Ошибка аудио: ${errorNames[errorCode] || errorCode}` }
        window.dispatchEvent(new CustomEvent('player:error', { detail: lastError.value }))
        isSkipping = true
        setTimeout(() => { next(); isSkipping = false }, 1000)
      }
    },
    onCanPlayThrough: () => {
      if (!preloadTriggered && duration.value > 0) {
        preloadTriggered = true
        preloadNextTracks()
      }
    },
  })

  // Stall recovery helper
  const stallRecovery = () => {
    handleStallTimeout({
      audio: audio.value,
      track: currentTrack.value,
      generation: _playGeneration,
      currentGeneration: _playGeneration,
      getStreamUrl: playerApi.getStreamUrl.bind(playerApi),
      setCachedUrl,
      onRecovered: () => { resetStallRetry() },
      onFailed: (track) => {
        lastError.value = { type: 'stall_timeout', track, message: 'Не удалось загрузить аудио — проблемы с сетью' }
        window.dispatchEvent(new CustomEvent('player:error', { detail: lastError.value }))
        isSkipping = true
        setTimeout(() => { next(); isSkipping = false }, 500)
      },
    })
  }

  // ===================== INIT AUDIO =====================
  const initAudio = () => {
    if (audio.value) return
    audio.value = createAudioElement(volume.value)

    initAudioContext()
    connectEnhancer(audio.value)

    setupMediaSession({
      play: () => audio.value?.play(),
      pause: () => audio.value?.pause(),
      prev: () => prev(),
      next: () => next(),
      seek: (t) => seek(t),
      seekBackward: (s) => seek(Math.max(0, progress.value - s)),
      seekForward: (s) => seek(Math.min(duration.value, progress.value + s)),
      stop: () => { if (audio.value) { audio.value.pause(); audio.value.currentTime = 0 }; isPlaying.value = false; updatePlaybackState() },
    })

    setupKeyboardShortcuts({
      toggle, next, prev, seek,
      setVolume, toggleMute, toggleShuffle, toggleRepeat,
      getVolume: () => volume.value,
      getProgress: () => progress.value,
      getDuration: () => duration.value,
    })

    setupAudioListeners(audio.value, buildAudioHandlers())
  }

  const reattachAudioListeners = () => {
    if (!audio.value) return
    // BUG-3 FIX: setupAudioListeners uses WeakMap to clean up old listeners before attaching
    setupAudioListeners(audio.value, buildAudioHandlers())
  }

  // ===================== UNIFIED SOURCE APPLICATION =====================
  /**
   * Apply a resolved audio source to the audio element.
   * Used by play(), next(), prev(), resumeFromState() — eliminating 4× duplication.
   */
  const applySource = async (track, source) => {
    switch (source.type) {
      case 'blob': {
        audio.value.pause()
        audio.value.currentTime = 0
        audio.value.src = source.src
        buffered.value = duration.value
        audio.value.load()
        await audio.value.play()
        hdTrackInfo.value = null
        break
      }
      case 'preloaded': {
        if (audio.value) {
          audio.value.pause()
          audio.value._obsolete = true
          audio.value.src = ''
        }
        const oldAudio = audio.value
        audio.value = source.audio
        audio.value.volume = volume.value
        audio.value.muted = isMuted.value
        reattachAudioListeners()
        connectEnhancer(audio.value)
        try {
          await audio.value.play()
          recyclePreloadAudio(oldAudio)
        } catch (e) {
          console.error('[Play] Preloaded audio failed, falling back:', e)
          audio.value = oldAudio
          if (oldAudio) reattachAudioListeners()
          clearPreloadAudio()
          // Fall through to cached/fresh URL
          const fallback = await resolveAudioSource(track.id, playerApi.getStreamUrl.bind(playerApi))
          if (fallback.type === 'error') throw fallback.error || new Error(fallback.reason)
          audio.value.src = fallback.src
          buffered.value = 0
          await audio.value.play()
        }
        break
      }
      case 'cached-url':
      case 'fresh-url': {
        audio.value.src = source.src
        buffered.value = 0
        await audio.value.play()
        if (source.meta?.hdInfo) {
          hdTrackInfo.value = source.meta.hdInfo
        } else if (source.type !== 'cached-url') {
          hdTrackInfo.value = null
        }
        break
      }
      case 'error':
        throw source.error || new Error(source.reason)
    }
  }

  // ===================== PLAY =====================
  const play = async (track, newQueue = null) => {
    initAudio()
    markUserInteraction()
    cancelIrrelevantPreloads(_collectRelevantIds())

    // Update queue
    if (newQueue) {
      clearLazyShuffle()
      queue.value = [...newQueue]
      queueIndex.value = newQueue.findIndex(t => t.id === track.id)
      if (shuffle.value) generateShuffleOrder(queueIndex.value)
    } else if (shuffle.value && shuffleOrder.value.length === 0 && !isLazyShuffleMode()) {
      generateShuffleOrder(queueIndex.value)
    }

    // Same track → toggle
    if (currentTrack.value?.id === track.id) { toggle(); return }

    // HD check with streamable substitution
    if (isTrackNotStreamable(track)) {
      console.log(`[Play] Track "${track.title}" is HD/large (mime: ${track.mime_type}, size: ${track.file_size})`)
      if (track.streamable_id) {
        try {
          const r = await tracksApi.getOne(track.streamable_id)  // BUG-1 FIX: was getById (undefined)
          hdTrackInfo.value = { id: track.id, title: track.title, isOriginalHd: true }
          const merged = { ...r.data, cover_url: track.cover_url || r.data.cover_url, _originalHdId: track.id }
          currentTrack.value = null
          await play(merged, null)
          return
        } catch (_) { /* fall through — API will try auto-substitution */ }
      }
      console.log('[Play] No pre-resolved streamable_id, will try API auto-substitution')
    }

    preloadTriggered = false
    loading.value = true
    currentTrack.value = track
    lastError.value = null
    const generation = ++_playGeneration
    updateMediaSession()

    try {
      const source = await resolveAudioSource(track.id, playerApi.getStreamUrl.bind(playerApi))
      await applySource(track, source)
      loading.value = false
      nextTrackPreloaded.value = null
      persistState()
      startStateSaving()
      preloadNextTracks()
    } catch (error) {
      if (error.name === 'AbortError') { loading.value = false; return }
      if (generation !== _playGeneration) return

      console.error('[Play Error]', error)
      const statusCode = error.response?.status
      const detail = error.response?.data?.detail || error.message || 'Ошибка воспроизведения'

      if (checkCascadingSkips()) {
        lastError.value = { type: 'cascade_error', track, message: 'Слишком много ошибок подряд' }
        window.dispatchEvent(new CustomEvent('player:error', { detail: lastError.value }))
        isPlaying.value = false; loading.value = false
        return
      }

      if (statusCode === 503) {
        const isLargeFile = detail.includes('слишком большой') || (track.file_size && track.file_size > 20 * 1024 * 1024)
        const isHdFormat = detail.includes('высокого качества') || detail.includes('HD') || detail.includes('FLAC')
        lastError.value = { type: isLargeFile ? 'too_large' : isHdFormat ? 'hd_only' : 'unavailable', track, message: detail }
        if (!isLargeFile && !isHdFormat) {
          try { await tracksApi.markUnavailable(track.id); track.is_unavailable = true } catch (_) {}
        }
        if (onTrackUnavailableCallback) onTrackUnavailableCallback(track, detail, isLargeFile || isHdFormat)
        setTimeout(() => next(), 1500)
      } else if (statusCode === 401) {
        deleteCachedUrl(track.id)
        lastError.value = { type: 'auth_expired', track, message: 'Токен истёк, переключаем трек...' }
        window.dispatchEvent(new CustomEvent('player:error', { detail: lastError.value }))
        setTimeout(() => next(), 500)
      } else if (statusCode === 404) {
        lastError.value = { type: 'not_found', track, message: 'Трек не найден' }
        window.dispatchEvent(new CustomEvent('player:error', { detail: lastError.value }))
        try { await tracksApi.markUnavailable(track.id); track.is_unavailable = true } catch (_) {}
        setTimeout(() => next(), 1000)
      } else {
        lastError.value = { type: 'playback_error', track, message: detail }
        window.dispatchEvent(new CustomEvent('player:error', { detail: lastError.value }))
        setTimeout(() => next(), 1000)
      }
    } finally {
      loading.value = false
    }
  }

  // ===================== PLAY SHUFFLE ALL =====================
  const playShuffleAll = async (context, contextId = null, contextName = null) => {
    if (shuffleInProgress) return
    shuffleInProgress = true
    loading.value = true

    try {
      let response
      switch (context) {
        case 'library':  response = await tracksApi.getAllIds({ sort_by: 'random' }); break
        case 'artist': {
          const name = contextName || contextId
          if (!name) throw new Error('Artist name required')
          response = await tracksApi.getArtistIds(name, { shuffle: true, role: 'primary' })
          break
        }
        case 'album':    if (!contextId) throw new Error('Album ID required'); response = await albumsApi.getIds(contextId, { shuffle: true }); break
        case 'playlist': if (!contextId) throw new Error('Playlist ID required'); response = await playlistsApi.getIds(contextId, { shuffle: true }); break
        default: throw new Error(`Unknown context: ${context}`)
      }

      const ids = response.data?.ids || response.data
      if (!ids?.length) { loading.value = false; shuffleInProgress = false; return }

      lazyShuffleIds.value = ids
      lazyShuffleIndex.value = 0
      lazyShuffleContext.value = { type: context, id: contextId, name: context === 'artist' ? (contextName || contextId) : contextName }
      shuffle.value = true
      saveSettings({ shuffle: true, volume: volume.value, isMuted: isMuted.value, repeat: repeat.value })
      queue.value = []; queueIndex.value = -1; shuffleOrder.value = []; shuffleIndex.value = -1

      const firstTrack = await loadTrackById(ids[0])
      if (!firstTrack) { clearLazyShuffle(); loading.value = false; shuffleInProgress = false; return }

      queue.value = [firstTrack]; queueIndex.value = 0
      if (audio.value) { audio.value._obsolete = true; audio.value.pause(); audio.value.src = '' }
      duration.value = 0; currentTrack.value = null
      await play(firstTrack)
      shuffleInProgress = false
    } catch (error) {
      console.error('[Lazy Shuffle] Failed:', error)
      clearLazyShuffle(); loading.value = false; shuffleInProgress = false
    }
  }

  // ===================== TOGGLE / SEEK =====================
  const toggle = async () => {
    if (currentTrack.value && (!audio.value || !audio.value.src)) { await resumeFromState(); return }
    if (!audio.value) return
    isPlaying.value ? audio.value.pause() : audio.value.play()
  }

  const seek = (time) => {
    if (!audio.value) return
    audio.value.currentTime = time
    updatePositionState()
  }

  // ===================== NEXT =====================
  const next = async () => {
    isSkipping = true
    markUserInteraction()
    cancelIrrelevantPreloads(_collectRelevantIds())
    preloadTriggered = false
    clearPreloadAudio()

    // === LAZY SHUFFLE ===
    if (isLazyShuffleMode()) {
      lazyShuffleIndex.value++
      if (lazyShuffleIndex.value >= lazyShuffleIds.value.length) {
        if (repeat.value === 'all') lazyShuffleIndex.value = 0
        else { isPlaying.value = false; isSkipping = false; clearLazyShuffle(); return }
      }
      const nextTrackId = lazyShuffleIds.value[lazyShuffleIndex.value]

      // Try blob cache first
      const blobUrl = getCachedAudio(nextTrackId)
      if (blobUrl) {
        const t = await loadTrackById(nextTrackId)
        if (t) {
          queue.value = [t]; queueIndex.value = 0
          initAudio(); loading.value = true; currentTrack.value = t; updateMediaSession()
          try {
            audio.value.pause(); audio.value.currentTime = 0
            audio.value.src = blobUrl; buffered.value = duration.value
            audio.value.load(); await audio.value.play()
            loading.value = false; isSkipping = false; persistState(); preloadNextTracks()
            return
          } catch (_) { /* fall through */ }
        }
      }

      loading.value = true
      const t = await loadTrackById(nextTrackId)
      if (!t) { isSkipping = false; loading.value = false; await next(); return }
      queue.value = [t]; queueIndex.value = 0; shuffleOrder.value = []; shuffleIndex.value = -1
      isSkipping = false; await play(t)
      return
    }

    // === REGULAR ===
    if (queue.value.length === 0) { isSkipping = false; return }

    let nextIndex
    if (shuffle.value && shuffleOrder.value.length > 0) {
      shuffleIndex.value++
      if (shuffleIndex.value >= shuffleOrder.value.length) {
        if (repeat.value === 'all') generateShuffleOrder()
        else { isPlaying.value = false; isSkipping = false; return }
      }
      nextIndex = shuffleOrder.value[shuffleIndex.value]
    } else {
      nextIndex = queueIndex.value + 1
      if (nextIndex >= queue.value.length) {
        if (repeat.value === 'all') nextIndex = 0
        else { isPlaying.value = false; isSkipping = false; return }
      }
    }

    queueIndex.value = nextIndex
    const nextTrack = queue.value[nextIndex]

    // Use unified resolveAudioSource instead of 4× duplicated cascade
    initAudio()
    loading.value = true
    currentTrack.value = nextTrack
    updateMediaSession()

    try {
      const source = await resolveAudioSource(nextTrack.id, playerApi.getStreamUrl.bind(playerApi))
      await applySource(nextTrack, source)
      loading.value = false
      isSkipping = false
      nextTrackPreloaded.value = null
      clearPreloadAudio()
      persistState()
      preloadNextTracks()
    } catch (e) {
      if (e.name === 'AbortError') return
      console.error('[Next] Failed:', e)
      isSkipping = false
      await play(nextTrack)
    }
  }

  // ===================== PREV =====================
  const prev = async () => {
    isSkipping = true
    markUserInteraction()
    preloadTriggered = false
    clearPreloadAudio()

    if (progress.value > 3) { seek(0); isSkipping = false; return }

    // === LAZY SHUFFLE ===
    if (isLazyShuffleMode()) {
      lazyShuffleIndex.value--
      if (lazyShuffleIndex.value < 0) {
        if (repeat.value === 'all') lazyShuffleIndex.value = lazyShuffleIds.value.length - 1
        else lazyShuffleIndex.value = 0
      }
      const prevTrackId = lazyShuffleIds.value[lazyShuffleIndex.value]
      loading.value = true
      const t = await loadTrackById(prevTrackId)
      if (!t) { isSkipping = false; loading.value = false; return }
      queue.value = [t]; queueIndex.value = 0; shuffleOrder.value = []; shuffleIndex.value = -1
      isSkipping = false; await play(t)
      return
    }

    if (queue.value.length === 0) { isSkipping = false; return }
    let prevIndex = queueIndex.value - 1
    if (prevIndex < 0) prevIndex = repeat.value === 'all' ? queue.value.length - 1 : 0
    queueIndex.value = prevIndex
    const prevTrack = queue.value[prevIndex]

    // Use unified resolveAudioSource (BUG-1 FIX: no more undefined audioCache.delete)
    initAudio()
    loading.value = true
    currentTrack.value = prevTrack
    updateMediaSession()

    try {
      const source = await resolveAudioSource(prevTrack.id, playerApi.getStreamUrl.bind(playerApi))
      await applySource(prevTrack, source)
      loading.value = false
      isSkipping = false
      persistState()
      preloadNextTracks()
    } catch (e) {
      loading.value = false
      isSkipping = false
      await play(prevTrack)
    }
  }

  // ===================== HANDLE ENDED =====================
  const handleEnded = async () => {
    const track = currentTrack.value
    const played = audio.value?.currentTime || 0
    const total = duration.value || 0
    if (!track || total === 0 || !audio.value?.src) return
    if (played < 1 && total > 5) return

    if (currentTrack.value) {
      try { await playerApi.recordPlay(currentTrack.value.id) } catch (_) {}
    }

    if (repeat.value === 'one') { seek(0); audio.value.play() }
    else next()
  }

  // ===================== QUEUE MANAGEMENT =====================
  const playFromQueue = async (relativeIndex) => {
    const idx = queueIndex.value + 1 + relativeIndex
    if (idx >= 0 && idx < queue.value.length) { queueIndex.value = idx; await play(queue.value[idx]) }
  }

  const toggleShuffle = () => {
    if (shuffle.value && isLazyShuffleMode()) {
      shuffle.value = false; shuffleOrder.value = []; shuffleIndex.value = -1
      clearLazyShuffle(); preloadTriggered = false; preloadNextTracks(); persistSettings()
      return
    }
    if (isLazyShuffleMode()) {
      if (!shuffle.value) { shuffle.value = true; persistSettings() }
      return
    }
    shuffle.value = !shuffle.value
    if (shuffle.value) generateShuffleOrder(queueIndex.value)
    else { shuffleOrder.value = []; shuffleIndex.value = -1; clearLazyShuffle() }
    preloadTriggered = false; preloadNextTracks(); persistSettings()
  }

  const toggleRepeat = () => {
    const modes = ['none', 'all', 'one']
    repeat.value = modes[(modes.indexOf(repeat.value) + 1) % modes.length]
    persistSettings()
  }

  const setVolume = (val) => {
    volume.value = Math.max(0, Math.min(1, val))
    if (audio.value) audio.value.volume = volume.value
    if (volume.value > 0) isMuted.value = false
    persistSettings()
  }

  const toggleMute = () => {
    isMuted.value = !isMuted.value
    if (audio.value) audio.value.muted = isMuted.value
    persistSettings()
  }

  const playNext = (track) => {
    // Handle Lazy Shuffle mode
    if (isLazyShuffleMode()) {
      const tid = track.id
      const idx = lazyShuffleIds.value.indexOf(tid)
      if (idx !== -1) {
        lazyShuffleIds.value.splice(idx, 1)
        if (idx <= lazyShuffleIndex.value) lazyShuffleIndex.value--
      }
      lazyShuffleIds.value.splice(lazyShuffleIndex.value + 1, 0, tid)
      persistState(); return
    }

    const insertIndex = queueIndex.value + 1
    const existing = queue.value.findIndex(t => t.id === track.id)
    if (existing !== -1) {
      if (shuffle.value && shuffleOrder.value.length > 0) {
        const sp = shuffleOrder.value.indexOf(existing)
        if (sp !== -1) { shuffleOrder.value.splice(sp, 1); if (sp <= shuffleIndex.value) shuffleIndex.value-- }
        shuffleOrder.value = shuffleOrder.value.map(i => i > existing ? i - 1 : i)
      }
      queue.value.splice(existing, 1)
      if (existing < queueIndex.value) queueIndex.value--
    }
    queue.value.splice(insertIndex, 0, track)
    if (shuffle.value && shuffleOrder.value.length > 0) {
      shuffleOrder.value = shuffleOrder.value.map(i => i >= insertIndex ? i + 1 : i)
      shuffleOrder.value.splice(shuffleIndex.value + 1, 0, insertIndex)
    }
    persistState()
  }

  const addToQueue = (track) => {
    if (!queue.value.find(t => t.id === track.id)) { queue.value.push(track); persistState() }
  }

  const removeFromQueue = (relIdx) => {
    const idx = queueIndex.value + 1 + relIdx
    if (idx > queueIndex.value && idx < queue.value.length) { queue.value.splice(idx, 1); persistState() }
  }

  const moveInQueue = (fromRel, toRel) => {
    const from = queueIndex.value + 1 + fromRel
    const to = queueIndex.value + 1 + toRel
    if (from > queueIndex.value && from < queue.value.length && to > queueIndex.value && to <= queue.value.length) {
      const [item] = queue.value.splice(from, 1)
      queue.value.splice(to > from ? to - 1 : to, 0, item)
      persistState()
    }
  }

  const stop = () => {
    if (audio.value) { audio.value._obsolete = true; audio.value.pause(); audio.value.src = '' }
    currentTrack.value = null; isPlaying.value = false
    progress.value = 0; duration.value = 0
    queue.value = []; queueIndex.value = -1
    stopStateSaving(); clearPlayerState()
  }

  /**
   * Patch track data in-place (currentTrack + queue).
   * Used by notifyTrackChange to keep player UI in sync after track edits.
   */
  const patchTrack = (trackId, data) => {
    if (currentTrack.value?.id === trackId) { Object.assign(currentTrack.value, data); updateMediaSession() }
    for (const t of queue.value) { if (t.id === trackId) Object.assign(t, data) }
  }

  // ===================== STATE RESTORE =====================
  const restoreState = async () => {
    if (stateRestored.value || !savedState) return false
    stateRestored.value = true
    const maxAge = 24 * 60 * 60 * 1000
    if (savedState.savedAt && Date.now() - savedState.savedAt > maxAge) { clearPlayerState(); return false }
    if (!savedState.currentTrack || !savedState.queue?.length) return false

    queue.value = savedState.queue
    queueIndex.value = savedState.queueIndex ?? 0
    currentTrack.value = savedState.currentTrack
    duration.value = savedState.duration ?? 0
    progress.value = savedState.progress ?? 0

    initAudio(); updateMediaSession(); startStateSaving()

    // Background prefetch
    const prefetchIds = [savedState.currentTrack, ...savedState.queue.slice((savedState.queueIndex ?? 0) + 1, (savedState.queueIndex ?? 0) + 4)].map(t => t.id)
    playerApi.getBatchUrls(prefetchIds)
      .then(r => { for (const item of (r.data.urls || [])) { if (item.url && !item.error) setCachedUrl(item.track_id, item.url, item.expires_at) } })
      .catch(() => {})
    return true
  }

  const resumeFromState = async () => {
    if (!currentTrack.value) return
    const savedProgress = progress.value
    try {
      loading.value = true
      const source = await resolveAudioSource(currentTrack.value.id, playerApi.getStreamUrl.bind(playerApi))

      if (source.type === 'blob') {
        audio.value.src = source.src; audio.value.load()
        if (savedProgress > 0) audio.value.currentTime = savedProgress
        await audio.value.play()
      } else if (source.type === 'error') {
        throw source.error || new Error(source.reason)
      } else {
        audio.value.src = source.src; buffered.value = 0
        await new Promise((resolve, reject) => {
          const h1 = () => { audio.value.removeEventListener('loadedmetadata', h1); audio.value.removeEventListener('error', h2); resolve() }
          const h2 = (e) => { audio.value.removeEventListener('loadedmetadata', h1); audio.value.removeEventListener('error', h2); reject(e) }
          audio.value.addEventListener('loadedmetadata', h1); audio.value.addEventListener('error', h2)
          audio.value.load()
        })
        if (savedProgress > 0 && savedProgress < audio.value.duration - 1) audio.value.currentTime = savedProgress
        await audio.value.play()
      }
      loading.value = false
      preloadNextTracks()
    } catch (e) {
      console.error('Failed to resume playback:', e); loading.value = false
    }
  }

  const hasSavedState = () => savedState && savedState.currentTrack && savedState.queue?.length > 0

  // ===================== RETURN =====================
  return {
    currentTrack,
    queue,
    queueIndex,
    shuffleOrder,
    shuffleIndex,
    isPlaying,
    progress,
    duration,
    volume,
    isMuted,
    shuffle,
    repeat,
    
    // UI Scale
    uiScale,
    
    // Enhancer
    enhancerEnabled,
    bassGain,
    trebleGain,
    autoGain,
    
    loading,
    buffered,
    lastError,
    stateRestored,
    hdTrackInfo,
    lazyShuffleContext,
    lazyShuffleIndex,
    lazyShuffleIds,
    play,
    playTrack: play,
    playShuffleAll,
    toggle,
    togglePlay: toggle,
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
    patchTrack,
    setOnTrackUnavailable,
    restoreState,
    resumeFromState,
    hasSavedState,
    persistState,
    isLazyShuffleMode,
  }
})
