<template>
  <Transition name="fullplayer-desktop">
    <div v-if="show" class="fullplayer-desktop" @click.self="$emit('close')">
      <div class="cockpit-container">
        <!-- Main Header with controls -->
        <div class="cockpit-header">
          <div class="header-left">
            <button class="hud-btn minimize" @click="$emit('close')" title="Свернуть">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 13H5v-2h14v2z"/>
              </svg>
            </button>
            <div class="mode-indicator">
              <span class="status-dot"></span>
              <span class="mode-text">PLAYER ACTIVE</span>
            </div>
          </div>
          
          <div class="header-center">
            <h1 class="cockpit-title">PLAYBACK CONTROL SYSTEM</h1>
          </div>
          
          <div class="header-right">
            <button class="hud-btn" @click="openTrackMenu" title="Меню трека">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Main Content Grid -->
        <div class="cockpit-grid">
          <!-- Left Panel: Cover Art & Visualizer -->
          <div class="panel-left">
            <div class="cover-section">
              <div class="cover-frame">
                <div class="cover-scanlines"></div>
                <div class="cover-wrapper" :style="coverStyle">
                  <img v-if="track?.cover_url" :src="track.cover_url" alt="Cover" class="cover-image" />
                  <div v-else class="cover-placeholder">
                    <span class="cover-initials">{{ coverInitials }}</span>
                  </div>
                </div>
                
                <!-- Loading overlay -->
                <div v-if="loading" class="loading-overlay">
                  <div class="loading-spinner">
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                  </div>
                  <span class="loading-text">LOADING</span>
                </div>
                
                <!-- Corner decorations -->
                <div class="corner-decoration tl"></div>
                <div class="corner-decoration tr"></div>
                <div class="corner-decoration bl"></div>
                <div class="corner-decoration br"></div>
              </div>
              
              <!-- Audio visualization bars -->
              <div class="visualizer">
                <div class="viz-bar" v-for="i in 32" :key="i" :style="getVisualizerStyle(i)"></div>
              </div>
            </div>
          </div>

          <!-- Center Panel: Main Information Display -->
          <div class="panel-center">
            <!-- Track Information Module -->
            <div class="info-module primary">
              <div class="module-header">
                <span class="module-label">TRACK DATA</span>
                <div class="module-indicators">
                  <span v-if="hdTrackInfo" class="indicator hd" title="HD версия доступна">HD</span>
                  <span v-if="isLiked" class="indicator liked">♥</span>
                </div>
              </div>
              
              <div class="track-display">
                <h2 class="track-title-main">{{ track?.title || 'UNKNOWN TRACK' }}</h2>
                <p class="track-artist-main">{{ track?.artist || 'UNKNOWN ARTIST' }}</p>
              </div>

              <!-- Track metadata grid -->
              <div class="metadata-grid">
                <div class="meta-item" v-if="track?.album_title">
                  <span class="meta-label">ALBUM</span>
                  <span class="meta-value clickable" @click="handleGoToAlbum">{{ track.album_title }}</span>
                </div>
                <div class="meta-item" v-if="track?.year">
                  <span class="meta-label">YEAR</span>
                  <span class="meta-value">{{ track.year }}</span>
                </div>
                <div class="meta-item" v-if="track?.genre">
                  <span class="meta-label">GENRE</span>
                  <span class="meta-value">{{ track.genre }}</span>
                </div>
                <div class="meta-item" v-if="track?.duration">
                  <span class="meta-label">DURATION</span>
                  <span class="meta-value">{{ formatTime(track.duration) }}</span>
                </div>
                <div class="meta-item" v-if="track?.bitrate">
                  <span class="meta-label">QUALITY</span>
                  <span class="meta-value">{{ track.bitrate }} kbps</span>
                </div>
                <div class="meta-item" v-if="track?.play_count !== undefined">
                  <span class="meta-label">PLAYS</span>
                  <span class="meta-value">{{ track.play_count }}</span>
                </div>
              </div>
            </div>

            <!-- Playback Controls Module -->
            <div class="info-module controls">
              <div class="module-header">
                <span class="module-label">PLAYBACK CONTROL</span>
              </div>
              
              <!-- Progress bar -->
              <div class="progress-module">
                <div class="time-display">
                  <span class="time current">{{ formatTime(progress) }}</span>
                  <span class="time-separator">/</span>
                  <span class="time total">{{ formatTime(duration) }}</span>
                </div>
                
                <div class="progress-track-wrapper">
                  <div class="buffered-track" :style="{ width: bufferedPercent + '%' }"></div>
                  <div class="progress-track" :style="{ width: progressPercent + '%' }"></div>
                  <input 
                    type="range"
                    class="progress-input"
                    :value="progress"
                    :max="duration || 100"
                    @input="$emit('seek', Number($event.target.value))"
                  />
                </div>
              </div>

              <!-- Main control buttons -->
              <div class="control-panel">
                <button 
                  class="control-btn secondary"
                  :class="{ active: shuffle }"
                  @click="$emit('toggleShuffle')"
                  title="Перемешать"
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
                  </svg>
                </button>
                
                <button class="control-btn" @click="$emit('prev')" title="Предыдущий">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
                  </svg>
                </button>
                
                <button class="control-btn play" @click="$emit('toggle')" title="Воспроизвести/Пауза">
                  <svg v-if="isPlaying" width="36" height="36" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
                  </svg>
                  <svg v-else width="36" height="36" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8 5v14l11-7z"/>
                  </svg>
                </button>
                
                <button class="control-btn" @click="$emit('next')" title="Следующий">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
                  </svg>
                </button>
                
                <button 
                  class="control-btn secondary"
                  :class="{ active: repeat !== 'none' }"
                  @click="$emit('toggleRepeat')"
                  title="Повтор"
                >
                  <svg v-if="repeat === 'one'" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4zm-4-2V9h-1l-2 1v1h1.5v4H13z"/>
                  </svg>
                  <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/>
                  </svg>
                </button>
              </div>

              <!-- Action buttons -->
              <div class="action-buttons">
                <button 
                  class="action-btn" 
                  :class="{ active: isLiked }" 
                  @click="$emit('like')"
                  title="Добавить в любимое"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path v-if="isLiked" d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                    <path v-else d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3zm-4.4 15.55l-.1.1-.1-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04.99 3.57 2.36h1.87C13.46 5.99 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05z"/>
                  </svg>
                  <span>FAVORITE</span>
                </button>
                
                <button class="action-btn" @click="handleAddToPlaylist" title="Добавить в плейлист">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M14 10H2v2h12v-2zm0-4H2v2h12V6zm4 8v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zM2 16h8v-2H2v2z"/>
                  </svg>
                  <span>ADD TO PLAYLIST</span>
                </button>
                
                <button v-if="hdTrackInfo" class="action-btn hd" @click="handleDownloadHD" title="Скачать HD версию">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
                  </svg>
                  <span>DOWNLOAD HD</span>
                </button>
              </div>
            </div>

            <!-- Volume Control Module -->
            <div class="info-module volume">
              <div class="module-header">
                <span class="module-label">AUDIO CONTROL</span>
              </div>
              
              <div class="volume-control">
                <button class="volume-btn" @click="$emit('toggleMute')">
                  <svg v-if="isMuted || volume === 0" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
                  </svg>
                  <svg v-else-if="volume < 0.5" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM5 9v6h4l5 5V4L9 9H5z"/>
                  </svg>
                  <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
                  </svg>
                </button>
                
                <div class="volume-slider-container">
                  <input 
                    type="range"
                    class="volume-slider"
                    :value="isMuted ? 0 : volume * 100"
                    min="0"
                    max="100"
                    @input="$emit('setVolume', Number($event.target.value) / 100)"
                  />
                  <div class="volume-level" :style="{ width: (isMuted ? 0 : volume * 100) + '%' }"></div>
                </div>
                
                <span class="volume-value">{{ Math.round((isMuted ? 0 : volume) * 100) }}%</span>
              </div>
            </div>
          </div>

          <!-- Right Panel: Queue & Context -->
          <div class="panel-right">
            <!-- Context Information -->
            <div class="context-module" v-if="contextInfo">
              <div class="module-header">
                <span class="module-label">CONTEXT</span>
              </div>
              <div class="context-info">
                <div class="context-type">{{ contextType }}</div>
                <div class="context-name">{{ contextInfo.name || 'Unknown' }}</div>
                <div class="context-meta" v-if="contextInfo.tracks_count">
                  {{ contextInfo.tracks_count }} tracks
                </div>
              </div>
            </div>

            <!-- Queue Panel -->
            <div class="queue-module">
              <div class="module-header">
                <span class="module-label">QUEUE</span>
                <span class="queue-count">{{ queueLength }} tracks</span>
              </div>
              
              <div class="queue-tabs">
                <button 
                  class="queue-tab" 
                  :class="{ active: activeQueueTab === 'upcoming' }"
                  @click="activeQueueTab = 'upcoming'"
                >
                  UP NEXT
                </button>
                <button 
                  class="queue-tab" 
                  :class="{ active: activeQueueTab === 'history' }"
                  @click="activeQueueTab = 'history'"
                >
                  HISTORY
                </button>
              </div>

              <div class="queue-list" ref="queueListRef">
                <!-- Upcoming tracks -->
                <template v-if="activeQueueTab === 'upcoming'">
                  <div 
                    v-for="(t, idx) in upcomingQueue" 
                    :key="`q-${t.id}-${idx}`"
                    class="queue-track"
                    :class="{ active: idx === 0 }"
                    @click="$emit('playFromQueue', idx)"
                  >
                    <div class="queue-track-number">{{ idx + 1 }}</div>
                    <div class="queue-track-cover" :style="getTrackCoverStyle(t)">
                      <img v-if="t.cover_url" :src="t.cover_url" alt="" />
                      <span v-else>{{ getTrackInitials(t) }}</span>
                    </div>
                    <div class="queue-track-info">
                      <div class="queue-track-title">{{ t.title || 'Unknown' }}</div>
                      <div class="queue-track-artist">{{ t.artist || 'Unknown' }}</div>
                    </div>
                    <div class="queue-track-duration">{{ formatTime(t.duration) }}</div>
                  </div>
                  
                  <div v-if="lazyShuffleMode" class="queue-lazy-info">
                    <div class="lazy-icon">🔀</div>
                    <div class="lazy-text">
                      <span>Shuffle Mode</span>
                      <span class="lazy-progress">{{ lazyShuffleIndex + 1 }} / {{ lazyShuffleTotal }}</span>
                    </div>
                  </div>
                  
                  <div v-if="!upcomingQueue.length && !lazyShuffleMode" class="queue-empty">
                    <span>Queue is empty</span>
                  </div>
                </template>

                <!-- History -->
                <template v-else>
                  <div 
                    v-for="(t, idx) in historyTracks" 
                    :key="`h-${t.id}-${idx}`"
                    class="queue-track history"
                    @click="$emit('playFromHistory', idx)"
                  >
                    <div class="queue-track-number">-{{ historyTracks.length - idx }}</div>
                    <div class="queue-track-cover" :style="getTrackCoverStyle(t)">
                      <img v-if="t.cover_url" :src="t.cover_url" alt="" />
                      <span v-else>{{ getTrackInitials(t) }}</span>
                    </div>
                    <div class="queue-track-info">
                      <div class="queue-track-title">{{ t.title || 'Unknown' }}</div>
                      <div class="queue-track-artist">{{ t.artist || 'Unknown' }}</div>
                    </div>
                    <div class="queue-track-duration">{{ formatTime(t.duration) }}</div>
                  </div>
                  
                  <div v-if="!historyTracks.length" class="queue-empty">
                    <span>No history</span>
                  </div>
                </template>
              </div>
            </div>

            <!-- Statistics Module -->
            <div class="stats-module">
              <div class="module-header">
                <span class="module-label">STATISTICS</span>
              </div>
              <div class="stats-grid">
                <div class="stat-item">
                  <span class="stat-label">BUFFER</span>
                  <span class="stat-value">{{ bufferedPercent }}%</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">BITRATE</span>
                  <span class="stat-value">{{ track?.bitrate || '---' }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">PLAYS</span>
                  <span class="stat-value">{{ track?.play_count || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">MODE</span>
                  <span class="stat-value">{{ playModeText }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Animated grid background -->
        <div class="grid-background"></div>
        
        <!-- Glow effects -->
        <div class="glow-effect glow-1"></div>
        <div class="glow-effect glow-2"></div>
      </div>

      <!-- Track context menu -->
      <TrackMenu
        :show="showTrackMenu"
        :track="track"
        :current-user-id="authStore.user?.id"
        context="player"
        @close="closeTrackMenu"
        @goToArtist="handleGoToArtist"
        @goToAlbum="handleGoToAlbum"
        @addToPlaylist="handleAddToPlaylist"
        @edit="handleEditTrack"
        @download="handleDownloadTrack"
        @delete="handleDeleteTrack"
        @removeFromLibrary="handleRemoveFromLibrary"
      />
      
      <!-- Edit track modal -->
      <EditTrackModal
        :show="showEditModal"
        :track="editingTrack"
        @close="closeEditModal"
        @saved="handleTrackSaved"
      />
      
      <!-- Playlist picker -->
      <PlaylistPicker
        :show="showPlaylistPicker"
        :track="track"
        @close="showPlaylistPicker = false"
      />
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useAuthStore } from '@/stores/auth'
import { getTrackCoverStyle, getTrackInitials } from '@/utils'
import TrackMenu from '@/components/TrackMenu.vue'
import EditTrackModal from '@/components/EditTrackModal.vue'
import PlaylistPicker from '@/components/PlaylistPicker.vue'

const props = defineProps({
  show: Boolean,
  track: Object,
  isPlaying: Boolean,
  loading: Boolean,
  progress: Number,
  duration: Number,
  buffered: Number,
  volume: Number,
  isMuted: Boolean,
  shuffle: Boolean,
  repeat: String,
  isLiked: Boolean,
  upcomingQueue: Array,
  queueLength: Number,
  historyTracks: {
    type: Array,
    default: () => []
  },
  hdTrackInfo: Object,
  lazyShuffleMode: Boolean,
  lazyShuffleIndex: Number,
  lazyShuffleTotal: Number,
  contextInfo: Object
})

defineEmits([
  'close', 'toggle', 'next', 'prev', 'seek', 'setVolume',
  'toggleMute', 'toggleShuffle', 'toggleRepeat', 'like',
  'playFromQueue', 'playFromHistory'
])

const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const authStore = useAuthStore()

// State
const activeQueueTab = ref('upcoming')
const showTrackMenu = ref(false)
const showEditModal = ref(false)
const showPlaylistPicker = ref(false)
const editingTrack = ref(null)
const queueListRef = ref(null)

// Visualizer animation
const visualizerBars = ref(Array(32).fill(0))
let visualizerInterval = null

// Computed
const coverStyle = computed(() => getTrackCoverStyle(props.track))
const coverInitials = computed(() => getTrackInitials(props.track))

const progressPercent = computed(() => {
  if (!props.duration) return 0
  return (props.progress / props.duration) * 100
})

const bufferedPercent = computed(() => {
  if (!props.duration) return 0
  return Math.round((props.buffered / props.duration) * 100)
})

const contextType = computed(() => {
  if (!props.contextInfo) return ''
  const types = {
    library: 'LIBRARY',
    playlist: 'PLAYLIST',
    album: 'ALBUM',
    artist: 'ARTIST'
  }
  return types[props.contextInfo.type] || ''
})

const playModeText = computed(() => {
  if (props.shuffle) return 'SHUFFLE'
  if (props.repeat === 'one') return 'REPEAT ONE'
  if (props.repeat === 'all') return 'REPEAT ALL'
  return 'NORMAL'
})

// Methods
const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const getVisualizerStyle = (index) => {
  const height = visualizerBars.value[index - 1] || 10
  const delay = index * 0.02
  return {
    height: `${height}%`,
    animationDelay: `${delay}s`
  }
}

const animateVisualizer = () => {
  if (props.isPlaying) {
    visualizerBars.value = visualizerBars.value.map(() => {
      return 10 + Math.random() * 90
    })
  } else {
    visualizerBars.value = visualizerBars.value.map(v => {
      return Math.max(10, v * 0.9)
    })
  }
}

// Track menu handlers
const openTrackMenu = () => {
  showTrackMenu.value = true
}

const closeTrackMenu = () => {
  showTrackMenu.value = false
}

const handleGoToArtist = () => {
  closeTrackMenu()
  if (props.track?.artist_id) {
    router.push(`/artists/${props.track.artist_id}`)
  }
}

const handleGoToAlbum = () => {
  closeTrackMenu()
  if (props.track?.album_id) {
    router.push(`/albums/${props.track.album_id}`)
  }
}

const handleAddToPlaylist = () => {
  closeTrackMenu()
  showPlaylistPicker.value = true
}

const handleEditTrack = () => {
  editingTrack.value = { ...props.track }
  showEditModal.value = true
  closeTrackMenu()
}

const handleDownloadTrack = () => {
  playerStore.downloadTrack(props.track)
  closeTrackMenu()
}

const handleDownloadHD = () => {
  if (props.hdTrackInfo) {
    playerStore.downloadTrack(props.hdTrackInfo)
  }
}

const handleDeleteTrack = async () => {
  closeTrackMenu()
  // Confirmation handled by TrackMenu
}

const handleRemoveFromLibrary = async () => {
  closeTrackMenu()
  // Handled by TrackMenu
}

const closeEditModal = () => {
  showEditModal.value = false
  editingTrack.value = null
}

const handleTrackSaved = () => {
  closeEditModal()
  // Track will be updated via store
}

// Lifecycle
onMounted(() => {
  // Start visualizer animation
  visualizerInterval = setInterval(animateVisualizer, 100)
})

onUnmounted(() => {
  if (visualizerInterval) {
    clearInterval(visualizerInterval)
  }
})

// Watch for playing state changes
watch(() => props.isPlaying, (playing) => {
  if (!playing) {
    // Gradually reduce visualizer bars when paused
    visualizerBars.value = visualizerBars.value.map(v => Math.max(5, v * 0.8))
  }
})
</script>

<style scoped>
:root {
  --neu-bg: #12121e;
  --neu-shadow-light: #1a1a28;
  --neu-shadow-dark: #08080f;
  --neu-accent: #db2220;
  --neu-accent-light: #e85c7c;
  --neu-text: #e8ecf1;
  --neu-text-light: #9ca3af;
}

.fullplayer-desktop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10000;
  background: linear-gradient(135deg, #0f0f1a 0%, #08080f 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.cockpit-container {
  position: relative;
  width: 100%;
  max-width: 1800px;
  height: 100%;
  max-height: 1000px;
  background: #12121e;
  border-radius: 40px;
  box-shadow: 
    20px 20px 60px #000000,
    -20px -20px 60px #1a1a28;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Header */
.cockpit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 25px 35px;
  background: #12121e;
  position: relative;
  z-index: 10;
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 15px;
  flex: 1;
}

.header-center {
  flex: 2;
  display: flex;
  justify-content: center;
}

.cockpit-title {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #db2220 0%, #e85c7c 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-family: 'Segoe UI', -apple-system, sans-serif;
}

.mode-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: #12121e;
  border-radius: 20px;
  box-shadow: 
    inset 4px 4px 8px #08080f,
    inset -4px -4px 8px #1a1a28;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, #db2220 0%, #e85c7c 100%);
  box-shadow: 0 2px 8px rgba(232, 92, 124, 0.6);
  animation: statusPulse 2s ease-in-out infinite;
}

@keyframes statusPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(0.9); }
}

.mode-text {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1.5px;
  color: #db2220;
  font-family: 'Segoe UI', sans-serif;
}

.hud-btn {
  width: 44px;
  height: 44px;
  background: #12121e;
  border: none;
  border-radius: 12px;
  color: #db2220;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 
    6px 6px 12px #08080f,
    -6px -6px 12px #1a1a28;
}

.hud-btn:hover {
  box-shadow: 
    4px 4px 8px #08080f,
    -4px -4px 8px #1a1a28;
  transform: translateY(1px);
}

.hud-btn:active {
  box-shadow: 
    inset 4px 4px 8px #08080f,
    inset -4px -4px 8px #1a1a28;
  transform: translateY(2px);
}

.hud-btn.minimize {
  color: #e87c7c;
}

.hud-btn.minimize:hover {
  color: #ff6464;
}

/* Main Grid */
.cockpit-grid {
  display: grid;
  grid-template-columns: 380px 1fr 360px;
  gap: 25px;
  padding: 25px 35px;
  flex: 1;
  overflow: hidden;
  position: relative;
  z-index: 5;
}

/* Left Panel */
.panel-left {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.cover-section {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.cover-frame {
  position: relative;
  aspect-ratio: 1;
  border-radius: 30px;
  overflow: hidden;
  background: #12121e;
  box-shadow: 
    inset 8px 8px 16px #08080f,
    inset -8px -8px 16px #1a1a28;
}

.cover-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 20px;
  box-shadow: 
    8px 8px 20px #000000,
    -8px -8px 20px #1a1a28;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a28 0%, #12121e 100%);
  border-radius: 20px;
}

.cover-initials {
  font-size: 80px;
  font-weight: 700;
  color: #db2220;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  font-family: 'Segoe UI', sans-serif;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(18, 18, 30, 0.95);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  z-index: 10;
  border-radius: 30px;
}

.loading-spinner {
  position: relative;
  width: 60px;
  height: 60px;
}

.spinner-ring {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 4px solid #12121e;
  border-top-color: #db2220;
  border-radius: 50%;
  animation: spinRing 1.5s linear infinite;
  box-shadow: 
    0 0 10px rgba(232, 92, 124, 0.6);
}

.spinner-ring:nth-child(2) {
  border-top-color: #e85c7c;
  animation-delay: 0.5s;
  width: 80%;
  height: 80%;
  top: 10%;
  left: 10%;
}

.spinner-ring:nth-child(3) {
  border-top-color: #db2220;
  animation-delay: 1s;
  width: 60%;
  height: 60%;
  top: 20%;
  left: 20%;
}

@keyframes spinRing {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 2px;
  color: #db2220;
  font-family: 'Segoe UI', sans-serif;
}

/* Visualizer */
.visualizer {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 80px;
  gap: 3px;
  padding: 15px;
  background: #12121e;
  border-radius: 20px;
  box-shadow: 
    inset 6px 6px 12px #08080f,
    inset -6px -6px 12px #1a1a28;
}

.viz-bar {
  flex: 1;
  background: linear-gradient(to top, #db2220 0%, #e85c7c 100%);
  min-height: 8px;
  border-radius: 4px;
  transition: height 0.1s ease;
  box-shadow: 0 2px 6px rgba(232, 92, 124, 0.4);
}

/* Center Panel */
.panel-center {
  display: flex;
  flex-direction: column;
  gap: 18px;
  overflow-y: auto;
  padding-right: 10px;
}

.panel-center::-webkit-scrollbar {
  width: 8px;
}

.panel-center::-webkit-scrollbar-track {
  background: #12121e;
  border-radius: 10px;
  box-shadow: 
    inset 3px 3px 6px #08080f,
    inset -3px -3px 6px #1a1a28;
}

.panel-center::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #db2220 0%, #e85c7c 100%);
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(232, 92, 124, 0.4);
}

.panel-center::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #e85c7c 0%, #db2220 100%);
}

.info-module {
  background: #12121e;
  border-radius: 25px;
  padding: 25px;
  box-shadow: 
    8px 8px 20px #000000,
    -8px -8px 20px #1a1a28;
}

.module-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  padding-bottom: 12px;
  border-bottom: 2px solid #1a1a28;
}

.module-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #db2220;
  font-family: 'Segoe UI', sans-serif;
}

.module-indicators {
  display: flex;
  gap: 8px;
}

.indicator {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  font-family: 'Segoe UI', sans-serif;
  box-shadow: 
    3px 3px 6px #000000,
    -3px -3px 6px #1a1a28;
}

.indicator.hd {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #8b7300;
}

.indicator.liked {
  background: linear-gradient(135deg, #ff6b9d 0%, #ff8bb3 100%);
  color: #9a0036;
}

/* Track Display */
.track-display {
  margin-bottom: 20px;
}

.track-title-main {
  font-size: 32px;
  font-weight: 700;
  color: #e8ecf1;
  margin: 0 0 10px 0;
  line-height: 1.2;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.6);
}

.track-artist-main {
  font-size: 20px;
  color: #a0aec0;
  margin: 0;
  font-weight: 500;
}

/* Metadata Grid */
.metadata-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background: #12121e;
  border-radius: 12px;
  box-shadow: 
    inset 3px 3px 6px #08080f,
    inset -3px -3px 6px #1a1a28;
}

.meta-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1.5px;
  color: #e85c7c;
  font-family: 'Segoe UI', sans-serif;
}

.meta-value {
  font-size: 14px;
  color: #e8ecf1;
  font-weight: 600;
}

.meta-value.clickable {
  cursor: pointer;
  color: #db2220;
  transition: all 0.2s ease;
}

.meta-value.clickable:hover {
  color: #e85c7c;
  text-shadow: 0 2px 4px rgba(232, 92, 124, 0.3);
}

/* Progress Module */
.progress-module {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.time-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-family: 'Segoe UI', monospace;
  font-size: 18px;
  color: #db2220;
  font-weight: 600;
}

.time-separator {
  color: #a0aec0;
}

.progress-track-wrapper {
  position: relative;
  height: 12px;
  background: #12121e;
  border-radius: 10px;
  overflow: visible;
  box-shadow: 
    inset 4px 4px 8px #08080f,
    inset -4px -4px 8px #1a1a28;
}

.buffered-track {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, #1a1a28 0%, #18182a 100%);
  transition: width 0.3s ease;
  border-radius: 10px;
}

.progress-track {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, #db2220 0%, #e85c7c 100%);
  box-shadow: 0 2px 8px rgba(232, 92, 124, 0.5);
  transition: width 0.1s linear;
  border-radius: 10px;
  position: relative;
}

.progress-track::after {
  content: '';
  position: absolute;
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  background: #db2220;
  border-radius: 50%;
  box-shadow: 
    4px 4px 10px #000000,
    -4px -4px 10px #1a1a28,
    0 0 12px rgba(232, 92, 124, 0.8);
}

.progress-input {
  position: absolute;
  top: -4px;
  left: 0;
  width: 100%;
  height: 20px;
  opacity: 0;
  cursor: pointer;
  z-index: 10;
}

/* Control Panel */
.control-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 18px;
}

.control-btn {
  width: 56px;
  height: 56px;
  border: none;
  background: #12121e;
  border-radius: 50%;
  color: #db2220;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 
    8px 8px 16px #08080f,
    -8px -8px 16px #1a1a28;
}

.control-btn:hover {
  box-shadow: 
    6px 6px 12px #08080f,
    -6px -6px 12px #1a1a28;
  transform: translateY(2px);
}

.control-btn:active {
  box-shadow: 
    inset 4px 4px 8px #08080f,
    inset -4px -4px 8px #1a1a28;
  transform: translateY(3px);
}

.control-btn.play {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #12121e 0%, #0f0f1a 100%);
  box-shadow: 
    12px 12px 24px #000000,
    -12px -12px 24px #1a1a28;
}

.control-btn.play:hover {
  box-shadow: 
    10px 10px 20px #000000,
    -10px -10px 20px #1a1a28;
  transform: translateY(2px);
}

.control-btn.play:active {
  box-shadow: 
    inset 6px 6px 12px #08080f,
    inset -6px -6px 12px #1a1a28;
  transform: translateY(4px);
}

.control-btn.secondary {
  width: 48px;
  height: 48px;
}

.control-btn.active {
  background: linear-gradient(135deg, #db2220 0%, #e85c7c 100%);
  color: #ffffff;
  box-shadow: 
    8px 8px 16px #000000,
    -8px -8px 16px #1a1a28,
    inset 0 0 20px rgba(232, 92, 124, 0.4);
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  flex: 1;
  min-width: 150px;
  padding: 12px 18px;
  border: none;
  background: #12121e;
  border-radius: 16px;
  color: #db2220;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
  font-family: 'Segoe UI', sans-serif;
  transition: all 0.3s ease;
  box-shadow: 
    6px 6px 12px #08080f,
    -6px -6px 12px #1a1a28;
}

.action-btn:hover {
  box-shadow: 
    4px 4px 8px #08080f,
    -4px -4px 8px #1a1a28;
  transform: translateY(1px);
}

.action-btn:active {
  box-shadow: 
    inset 4px 4px 8px #08080f,
    inset -4px -4px 8px #1a1a28;
  transform: translateY(2px);
}

.action-btn.active {
  background: linear-gradient(135deg, #db2220 0%, #e85c7c 100%);
  color: #ffffff;
  box-shadow: 
    6px 6px 12px #000000,
    -6px -6px 12px #1a1a28,
    inset 0 0 15px rgba(232, 92, 124, 0.5);
}

.action-btn.hd {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #1a1a1a;
  box-shadow: 
    6px 6px 12px #000000,
    -6px -6px 12px #1a1a28,
    inset 0 0 15px rgba(255, 215, 0, 0.4);
}

.action-btn.hd:hover {
  box-shadow: 
    4px 4px 8px #000000,
    -4px -4px 8px #1a1a28,
    0 0 20px rgba(255, 215, 0, 0.6);
}

/* Volume Control */
.info-module.volume {
  padding: 18px 25px;
}

.volume-control {
  display: flex;
  align-items: center;
  gap: 18px;
}

.volume-btn {
  width: 48px;
  height: 48px;
  border: none;
  background: #12121e;
  border-radius: 50%;
  color: #db2220;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
  box-shadow: 
    6px 6px 12px #08080f,
    -6px -6px 12px #1a1a28;
}

.volume-btn:hover {
  box-shadow: 
    4px 4px 8px #08080f,
    -4px -4px 8px #1a1a28;
  transform: translateY(1px);
}

.volume-btn:active {
  box-shadow: 
    inset 4px 4px 8px #08080f,
    inset -4px -4px 8px #1a1a28;
}

.volume-slider-container {
  position: relative;
  flex: 1;
  height: 10px;
  background: #12121e;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 
    inset 4px 4px 8px #08080f,
    inset -4px -4px 8px #1a1a28;
}

.volume-level {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, #db2220 0%, #e85c7c 100%);
  transition: width 0.1s ease;
  pointer-events: none;
  border-radius: 10px;
  box-shadow: 0 0 10px rgba(232, 92, 124, 0.5);
}

.volume-slider {
  position: absolute;
  top: 50%;
  left: 0;
  width: 100%;
  height: 20px;
  transform: translateY(-50%);
  opacity: 0;
  cursor: pointer;
  z-index: 10;
}

.volume-value {
  font-size: 14px;
  font-weight: 600;
  color: #db2220;
  font-family: 'Segoe UI', monospace;
  min-width: 50px;
  text-align: right;
}

/* Right Panel */
.panel-right {
  display: flex;
  flex-direction: column;
  gap: 18px;
  overflow: hidden;
}

/* Context Module */
.context-module {
  background: #12121e;
  border-radius: 20px;
  padding: 18px;
  box-shadow: 
    6px 6px 12px #000000,
    -6px -6px 12px #1a1a28;
}

.context-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.context-type {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #e85c7c;
  font-family: 'Segoe UI', sans-serif;
}

.context-name {
  font-size: 16px;
  font-weight: 600;
  color: #e8ecf1;
}

.context-meta {
  font-size: 12px;
  color: #718096;
}

/* Queue Module */
.queue-module {
  flex: 1;
  background: #12121e;
  border-radius: 20px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  box-shadow: 
    6px 6px 12px #000000,
    -6px -6px 12px #1a1a28;
}

.queue-count {
  font-size: 11px;
  color: #718096;
  font-family: 'Segoe UI', sans-serif;
}

.queue-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.queue-tab {
  flex: 1;
  padding: 10px;
  border: none;
  background: #12121e;
  border-radius: 12px;
  color: #718096;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1.2px;
  font-family: 'Segoe UI', sans-serif;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 
    4px 4px 8px #08080f,
    -4px -4px 8px #1a1a28;
}

.queue-tab:hover {
  box-shadow: 
    3px 3px 6px #08080f,
    -3px -3px 6px #1a1a28;
  color: #db2220;
}

.queue-tab.active {
  background: linear-gradient(135deg, #db2220 0%, #e85c7c 100%);
  color: #ffffff;
  box-shadow: 
    inset 3px 3px 6px rgba(232, 92, 124, 0.4),
    4px 4px 8px #000000,
    -4px -4px 8px #1a1a28;
}

.queue-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.queue-list::-webkit-scrollbar {
  width: 8px;
}

.queue-list::-webkit-scrollbar-track {
  background: #12121e;
  border-radius: 10px;
  box-shadow: 
    inset 2px 2px 4px #08080f,
    inset -2px -2px 4px #1a1a28;
}

.queue-list::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #db2220 0%, #e85c7c 100%);
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(232, 92, 124, 0.4);
}

.queue-list::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #e85c7c 0%, #db2220 100%);
}

.queue-track {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 12px;
  margin-bottom: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #12121e;
}

.queue-track:hover {
  box-shadow: 
    4px 4px 8px #000000,
    -4px -4px 8px #1a1a28;
  transform: translateY(-1px);
}

.queue-track.active {
  background: linear-gradient(135deg, #db2220 0%, #e85c7c 100%);
  box-shadow: 
    6px 6px 12px #000000,
    -6px -6px 12px #1a1a28,
    inset 0 0 20px rgba(232, 92, 124, 0.4);
}

.queue-track.active .queue-track-title,
.queue-track.active .queue-track-artist,
.queue-track.active .queue-track-duration,
.queue-track.active .queue-track-number {
  color: #ffffff;
}

.queue-track.history {
  opacity: 0.8;
}

.queue-track-number {
  width: 28px;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: #db2220;
  font-family: 'Segoe UI', monospace;
  flex-shrink: 0;
}

.queue-track-cover {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a1a28;
  box-shadow: 
    inset 3px 3px 6px #08080f,
    inset -3px -3px 6px #1a1a28;
}

.queue-track-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.queue-track-cover span {
  font-size: 14px;
  font-weight: 600;
  color: #db2220;
}

.queue-track-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.queue-track-title {
  font-size: 13px;
  font-weight: 600;
  color: #e8ecf1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-track-artist {
  font-size: 11px;
  color: #718096;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-track-duration {
  font-size: 11px;
  color: #a0aec0;
  font-family: 'Segoe UI', monospace;
  flex-shrink: 0;
}

.queue-lazy-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #12121e;
  border-radius: 12px;
  margin-top: 8px;
  box-shadow: 
    inset 4px 4px 8px #08080f,
    inset -4px -4px 8px #1a1a28;
}

.lazy-icon {
  font-size: 24px;
}

.lazy-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #db2220;
  font-weight: 600;
}

.lazy-progress {
  font-size: 10px;
  color: #e85c7c;
  font-family: 'Segoe UI', monospace;
}

.queue-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 50px 20px;
  color: #a0aec0;
  font-size: 13px;
  font-family: 'Segoe UI', sans-serif;
}

/* Statistics Module */
.stats-module {
  background: #12121e;
  border-radius: 20px;
  padding: 18px;
  box-shadow: 
    6px 6px 12px #000000,
    -6px -6px 12px #1a1a28;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background: #12121e;
  border-radius: 12px;
  box-shadow: 
    inset 3px 3px 6px #08080f,
    inset -3px -3px 6px #1a1a28;
}

.stat-label {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 1.2px;
  color: #e85c7c;
  font-family: 'Segoe UI', sans-serif;
}

.stat-value {
  font-size: 14px;
  font-weight: 700;
  color: #e8ecf1;
  font-family: 'Segoe UI', monospace;
}

/* Transitions */
.fullplayer-desktop-enter-active,
.fullplayer-desktop-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.fullplayer-desktop-enter-from,
.fullplayer-desktop-leave-to {
  opacity: 0;
  transform: scale(0.98);
}

/* Background elements - удалены для чистого неоморфизма */
.grid-background,
.glow-effect,
.corner-decoration,
.cover-scanlines {
  display: none;
}

/* Transitions */
.fullplayer-desktop-enter-active,
.fullplayer-desktop-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.fullplayer-desktop-enter-from,
.fullplayer-desktop-leave-to {
  opacity: 0;
  transform: scale(0.98);
}

/* Responsive adjustments */
@media (max-width: 1600px) {
  .cockpit-grid {
    grid-template-columns: 320px 1fr 320px;
  }
  
  .track-title-main {
    font-size: 28px;
  }
}

@media (max-width: 1400px) {
  .cockpit-grid {
    grid-template-columns: 280px 1fr 300px;
    gap: 15px;
  }
  
  .metadata-grid {
    grid-template-columns: 1fr;
  }
}
</style>
