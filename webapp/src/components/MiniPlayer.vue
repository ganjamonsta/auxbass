<template>
  <div class="mini-player" @click="$emit('expand')" @contextmenu.prevent="openTrackMenu">
    <!-- LCD Screen -->
    <div class="lcd-screen">
      <div class="lcd-row lcd-row-main">
        <span class="lcd-status">{{ isPlaying ? '▶' : '■' }}</span>
        <div class="lcd-title-container">
          <div class="lcd-title-track" :class="{ 'marquee': shouldMarquee }">
            <span class="lcd-title">{{ displayText }}</span>
            <span v-if="shouldMarquee" class="lcd-title lcd-title-clone">{{ displayText }}</span>
          </div>
        </div>
      </div>
      <div class="lcd-row lcd-row-sub">
        <span class="lcd-time">{{ formatTime(progress) }}/{{ formatTime(duration || track.duration) }}</span>
      </div>
      <!-- LED Progress dots -->
      <div class="lcd-progress">
        <span 
          class="lcd-dot" 
          v-for="i in 16" 
          :key="i" 
          :class="getDotClass(i)"
        ></span>
      </div>
    </div>
    
    <!-- Nokia Style Controls -->
    <div class="nokia-controls">
      <button class="nokia-btn" @click.stop="$emit('toggle')">
        <svg v-if="loading" class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
          <path d="M12 2a10 10 0 0 1 10 10"/>
        </svg>
        <svg v-else-if="isPlaying" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <rect x="6" y="4" width="4" height="16" rx="1"/>
          <rect x="14" y="4" width="4" height="16" rx="1"/>
        </svg>
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z"/>
        </svg>
      </button>
      <button class="nokia-btn" @click.stop="$emit('next')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <path d="M6 18l8.5-6L6 6v12zm8-12v12l8-6-8-6z"/>
        </svg>
      </button>
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
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useAuthStore } from '@/stores/auth'
import { playerApi } from '@/api/client'
import TrackMenu from '@/components/TrackMenu.vue'
import EditTrackModal from '@/components/EditTrackModal.vue'

const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const authStore = useAuthStore()
const telegram = inject('telegram')

const props = defineProps({
  track: {
    type: Object,
    required: true
  },
  isPlaying: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  progress: {
    type: Number,
    default: 0
  },
  duration: {
    type: Number,
    default: 0
  },
  buffered: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['expand', 'toggle', 'next'])

// Track menu state
const showTrackMenu = ref(false)

const openTrackMenu = () => {
  telegram?.HapticFeedback?.impactOccurred?.('light')
  showTrackMenu.value = true
}

const closeTrackMenu = () => {
  showTrackMenu.value = false
}

// Menu handlers
const handleGoToArtist = (artist) => {
  closeTrackMenu()
  router.push(`/artist/${encodeURIComponent(artist)}`)
}

const handleGoToAlbum = (albumId) => {
  if (albumId) {
    closeTrackMenu()
    router.push(`/album/${albumId}`)
  }
}

const handleAddToPlaylist = (track) => {
  // TODO: Show playlist picker
  closeTrackMenu()
}

const handleEditTrack = (track) => {
  closeTrackMenu()
  editingTrack.value = track
  showEditModal.value = true
}

// Edit modal state
const showEditModal = ref(false)
const editingTrack = ref(null)

const closeEditModal = () => {
  showEditModal.value = false
  editingTrack.value = null
}

const handleTrackSaved = (updatedTrack) => {
  // Update will be reflected through library store
}

const handleDownloadTrack = async (track) => {
  try {
    await playerApi.download(props.track.id)
  } catch (error) {
    console.error('Failed to download track:', error)
  }
  closeTrackMenu()
}

const handleDeleteTrack = async (track) => {
  if (confirm('Удалить трек полностью?')) {
    await libraryStore.deleteTrack(props.track.id)
    playerStore.next()
  }
  closeTrackMenu()
}

const handleRemoveFromLibrary = async (track) => {
  await libraryStore.removeFromLibrary(props.track.id)
  closeTrackMenu()
}

const progressPercent = computed(() => {
  const dur = props.duration || props.track?.duration
  if (!dur) return 0
  return (props.progress / dur) * 100
})

const bufferedPercent = computed(() => {
  const dur = props.duration || props.track?.duration
  if (!dur) return 0
  return (props.buffered / dur) * 100
})

// Get class for each LED dot
const getDotClass = (index) => {
  const dotPercent = (index / 16) * 100
  const prevDotPercent = ((index - 1) / 16) * 100
  
  // Active (played) - red
  if (dotPercent <= progressPercent.value) {
    return 'active'
  }
  
  // Next dot to light up - blinking
  if (prevDotPercent < progressPercent.value && dotPercent > progressPercent.value) {
    return 'next'
  }
  
  // Buffered - blue
  if (dotPercent <= bufferedPercent.value) {
    return 'buffered'
  }
  
  return ''
}

// Generate cover gradient
const coverGradient = computed(() => {
  const title = props.track?.title || 'Music'
  const artist = props.track?.artist || ''
  
  const str = title + artist
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  const hue1 = Math.abs(hash % 360)
  const hue2 = (hue1 + 40) % 360
  
  return `linear-gradient(135deg, hsl(${hue1}, 60%, 40%) 0%, hsl(${hue2}, 50%, 30%) 100%)`
})

const coverStyle = computed(() => {
  if (props.track?.cover_url) return {}
  return { background: coverGradient.value }
})

const coverInitials = computed(() => {
  const title = props.track?.title || 'M'
  const words = title.split(' ').filter(w => w.length > 0)
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }
  return title.substring(0, 2).toUpperCase()
})

const shouldMarqueeTitle = computed(() => {
  return (props.track?.title?.length || 0) > 20
})

const displayText = computed(() => {
  const artist = props.track?.artist || '---'
  const title = props.track?.title || 'NO TRACK'
  return `${artist} — ${title}`
})

const shouldMarquee = computed(() => {
  return displayText.value.length > 25
})

const formatTime = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   🎵 MINI PLAYER - Nokia XpressMusic Neumorphic Style
   Inspired by Nokia 5700 with modern neumorphism
   ═══════════════════════════════════════════════════════════ */

.mini-player {
  position: fixed;
  bottom: calc(var(--nav-height) + env(safe-area-inset-bottom));
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 12px;
  padding: 10px 12px;
  background: var(--xm-bg-elevated);
  border-radius: var(--neu-radius-lg);
  cursor: pointer;
  z-index: 99; /* Below nav (100), above content */
  overflow: visible;
  box-shadow: 
    6px 6px 12px var(--neu-shadow-dark),
    -3px -3px 8px var(--neu-shadow-light);
  border: 1px solid rgba(255, 255, 255, 0.03);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.mini-player:active {
  transform: scale(0.98);
  box-shadow: 
    3px 3px 6px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light);
}

/* ─── LCD Screen - Nokia XpressMusic Style ─── */
.lcd-screen {
  flex: 1;
  background: var(--lcd-bg);
  border-radius: var(--neu-radius-md);
  padding: 12px 14px 10px;
  font-family: 'Segoe UI', system-ui, sans-serif;
  border: 1px solid #1a2a40;
  box-shadow: 
    inset 0 2px 8px rgba(0, 0, 0, 0.8),
    0 1px 0 rgba(100, 150, 255, 0.1);
  min-width: 0;
  position: relative;
  overflow: visible;
}

/* Scanline effect for retro feel */
.lcd-screen::before {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.03) 2px,
    rgba(0, 0, 0, 0.03) 4px
  );
  pointer-events: none;
}

.lcd-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.lcd-row-main {
  margin-bottom: 4px;
  min-width: 0;
}

.lcd-row-sub {
  justify-content: space-between;
  margin-bottom: 8px;
  min-width: 0;
  overflow: visible;
}

.lcd-status {
  color: var(--xm-accent);
  font-size: 12px;
  font-weight: bold;
  text-shadow: 0 0 8px var(--xm-accent-glow);
  flex-shrink: 0;
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.lcd-title-container {
  flex: 1 1 0;
  min-width: 0;
  overflow: visible;
  position: relative;
  /* Clip only horizontally, allow vertical for glow */
  clip-path: inset(-10px 0 -10px 0);
  mask-image: linear-gradient(90deg, black 85%, transparent 100%);
  -webkit-mask-image: linear-gradient(90deg, black 85%, transparent 100%);
}

.lcd-title-track {
  display: inline-flex;
  white-space: nowrap;
}

.lcd-title-track.marquee {
  animation: marquee-scroll 10s linear infinite;
}

.lcd-title {
  color: var(--lcd-text);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-shadow: 0 0 10px var(--lcd-text-glow);
  white-space: nowrap;
  flex-shrink: 0;
}

.lcd-title-clone {
  margin-left: 80px;
}

@keyframes marquee-scroll {
  0%, 5% {
    transform: translateX(0);
  }
  95%, 100% {
    transform: translateX(calc(-50% - 40px));
  }
}

.lcd-time {
  color: var(--lcd-text);
  font-size: 12px;
  font-weight: 600;
  text-shadow: 0 0 6px var(--lcd-text-glow);
  flex-shrink: 0;
  letter-spacing: 1.5px;
  font-variant-numeric: tabular-nums;
}

/* ─── LED Progress Dots ─── */
.lcd-progress {
  display: flex;
  gap: 3px;
}

.lcd-dot {
  width: 100%;
  height: 4px;
  background: var(--lcd-dot-inactive);
  border-radius: 2px;
  flex: 1;
  transition: background 0.15s ease, box-shadow 0.15s ease;
}

.lcd-dot.active {
  background: var(--xm-accent);
  box-shadow: 0 0 6px var(--xm-accent-glow);
}

.lcd-dot.buffered {
  background: rgba(0, 188, 212, 0.35);
  box-shadow: none;
}

.lcd-dot.next {
  background: var(--xm-accent);
  opacity: 0.5;
  animation: dot-blink 0.6s ease-in-out infinite;
}

@keyframes dot-blink {
  0%, 100% { 
    opacity: 0.3;
    box-shadow: none;
  }
  50% { 
    opacity: 1;
    box-shadow: 0 0 8px var(--xm-accent-glow);
  }
}

/* ─── Nokia XpressMusic Style Rubber Buttons ─── */
.nokia-controls {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
}

.nokia-btn {
  width: 42px;
  height: 30px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-text-primary);
  flex-shrink: 0;
  transition: all 0.15s ease;
  position: relative;
  
  /* Nokia rubber button style */
  background: var(--rubber-bg);
  box-shadow: 
    0 3px 6px rgba(0, 0, 0, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.12),
    inset 0 -1px 0 rgba(0, 0, 0, 0.3);
  border: 1px solid var(--rubber-border);
}

/* Rubber texture bumps */
.nokia-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 28px;
  height: 16px;
  background: 
    radial-gradient(circle at 20% 50%, rgba(255,255,255,0.1) 0%, transparent 50%),
    radial-gradient(circle at 50% 50%, rgba(255,255,255,0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 50%, rgba(255,255,255,0.1) 0%, transparent 50%);
  border-radius: 4px;
  pointer-events: none;
}

.nokia-btn:active {
  transform: scale(0.94) translateY(1px);
  background: var(--rubber-bg-pressed);
  box-shadow: 
    0 1px 2px rgba(0, 0, 0, 0.5),
    inset 0 2px 4px rgba(0, 0, 0, 0.4);
}

.nokia-btn:active svg {
  color: var(--xm-accent);
  filter: drop-shadow(0 0 4px var(--xm-accent-glow));
}

.nokia-btn svg {
  transition: color 0.15s ease, filter 0.15s ease;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
