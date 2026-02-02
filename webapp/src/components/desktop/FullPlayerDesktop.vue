<template>
  <Transition name="fullplayer-desktop">
    <div v-if="show" class="fullplayer-desktop" @click.self="$emit('close')">
      <div class="cockpit-container">
        
        <PlayerHeader 
          @close="$emit('close')" 
          @openTrackMenu="openTrackContextMenu" 
        />

        <!-- Main Content Grid -->
        <div class="cockpit-grid">
          <!-- Left Panel: Cover Art & Visualizer -->
          <div class="panel-left">
            <CoverSection 
              :track="track" 
              :loading="loading" 
              :isPlaying="isPlaying" 
            />

            <ArtistLibrary 
              :track="track" 
              @play="handlePlayArtistTrack" 
            />
          </div>

          <!-- Center Panel: Main Information Display -->
          <div class="panel-center">
            <div class="panel-center-main">
              <TrackInfo 
                :track="track"
                :hdTrackInfo="hdTrackInfo"
                :isLiked="isLiked"
                @goToAlbum="handleGoToAlbum"
              />

              <PlayerControls 
                :isPlaying="isPlaying"
                :progress="progress"
                :duration="duration"
                :buffered="buffered"
                :shuffle="shuffle"
                :repeat="repeat"
                :isLiked="isLiked"
                :hdTrackInfo="hdTrackInfo"
                @seek="$emit('seek', $event)"
                @toggle="$emit('toggle')"
                @prev="$emit('prev')"
                @next="$emit('next')"
                @toggleShuffle="$emit('toggleShuffle')"
                @toggleRepeat="$emit('toggleRepeat')"
                @like="$emit('like')"
                @addToPlaylist="handleAddToPlaylist"
                @downloadHD="handleDownloadHD"
              />
            </div>

            <VolumeControl 
              :volume="volume"
              :isMuted="isMuted"
              @toggleMute="$emit('toggleMute')"
              @setVolume="$emit('setVolume', $event)"
            />
          </div>

          <!-- Right Panel: Queue & Context -->
          <div class="panel-right">
            <QueuePanel 
              :contextInfo="contextInfo"
              :queueLength="queueLength"
              :upcomingQueue="upcomingQueue"
              :historyTracks="historyTracks"
              :lazyShuffleMode="lazyShuffleMode"
              :lazyShuffleIndex="lazyShuffleIndex"
              :lazyShuffleTotal="lazyShuffleTotal"
              @playFromQueue="$emit('playFromQueue', $event)"
              @playFromHistory="$emit('playFromHistory', $event)"
            />

            <PlayerStats 
              :bufferedPercent="bufferedPercent"
              :bitrate="track?.bitrate"
              :playCount="track?.play_count"
              :playModeText="playModeText"
            />
          </div>
        </div>

        <!-- Animated grid background -->
        <div class="grid-background"></div>
        
        <!-- Glow effects -->
        <div class="glow-effect glow-1"></div>
        <div class="glow-effect glow-2"></div>

        <!-- Full-screen background visualizer -->
        <div class="fullscreen-visualizer" :class="{ 'playing': isPlaying }">
          <div class="viz-bar" v-for="i in 64" :key="i" :style="getVisualizerStyle(i)"></div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useAuthStore } from '@/stores/auth'
import { useContextMenu } from '@/composables/useContextMenu'

// New sub-components
import PlayerHeader from './fullplayer/PlayerHeader.vue'
import CoverSection from './fullplayer/CoverSection.vue'
import ArtistLibrary from './fullplayer/ArtistLibrary.vue'
import TrackInfo from './fullplayer/TrackInfo.vue'
import PlayerControls from './fullplayer/PlayerControls.vue'
import VolumeControl from './fullplayer/VolumeControl.vue'
import QueuePanel from './fullplayer/QueuePanel.vue'
import PlayerStats from './fullplayer/PlayerStats.vue'

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
const authStore = useAuthStore()
const { openMenu } = useContextMenu()

// Computed
const bufferedPercent = computed(() => {
  if (!props.duration) return 0
  return Math.round((props.buffered / props.duration) * 100)
})

const playModeText = computed(() => {
  if (props.shuffle) return 'SHUFFLE'
  if (props.repeat === 'one') return 'REPEAT 1'
  if (props.repeat === 'all') return 'REPEAT ALL'
  return 'NORMAL'
})

// Full-screen visualizer
const visualizerBars = ref(Array(64).fill(0))
const visualizerPeak = ref(0)
let visualizerInterval = null

const getVisualizerStyle = (index) => {
  const height = visualizerBars.value[index - 1] || 5
  const delay = index * 0.015
  
  // Dynamic color based on peak intensity
  const intensity = visualizerPeak.value / 100
  const hue = 350 + (intensity * 30) // Shift from red to pink/purple on peaks
  const saturation = 70 + (intensity * 30)
  
  return {
    height: `${height}%`,
    animationDelay: `${delay}s`,
    background: `linear-gradient(to top, hsl(${hue}, ${saturation}%, 50%), hsl(${hue}, ${saturation}%, 65%))`,
    boxShadow: `0 0 ${4 + intensity * 8}px hsla(${hue}, ${saturation}%, 60%, ${0.3 + intensity * 0.4})`
  }
}

const animateVisualizer = () => {
  if (props.isPlaying) {
    const newBars = visualizerBars.value.map((_, i) => {
      // Create more dynamic waves across bars
      const baseHeight = 15 + Math.random() * 85
      const wave = Math.sin(Date.now() / 500 + i * 0.2) * 20
      return Math.max(5, Math.min(100, baseHeight + wave))
    })
    visualizerBars.value = newBars
    
    // Calculate peak for color changes
    const avgHeight = newBars.reduce((a, b) => a + b, 0) / newBars.length
    visualizerPeak.value = avgHeight
  } else {
    visualizerBars.value = visualizerBars.value.map(v => {
      return Math.max(5, v * 0.92)
    })
    visualizerPeak.value = visualizerPeak.value * 0.9
  }
}

onMounted(() => {
  visualizerInterval = setInterval(animateVisualizer, 80)
})

onUnmounted(() => {
  if (visualizerInterval) {
    clearInterval(visualizerInterval)
  }
})

watch(() => props.isPlaying, (playing) => {
  if (!playing) {
    visualizerBars.value = visualizerBars.value.map(v => Math.max(5, v * 0.8))
  }
})

// Methods
const openTrackContextMenu = () => {
  openMenu('track', props.track, 'player')
}

const handleDownloadHD = () => {
  if (props.hdTrackInfo) {
    playerStore.downloadTrack(props.hdTrackInfo)
  }
}

const handlePlayArtistTrack = (track) => {
  playerStore.playTrack(track, { type: 'artist', artist: props.track.artist })
}

const handleGoToAlbum = () => {
  if (!props.track?.album) return
  router.push(`/album/${props.track.album.id}`)
}

const handleAddToPlaylist = () => {
  openMenu('track', props.track, 'player')
}
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
    20px 20px 60px var(--sh-dark),
    -20px -20px 60px var(--sh-light);
  overflow: hidden;
  display: flex;
  flex-direction: column;
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

/* Panel Containers */
.panel-left {
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 10px;
}

.panel-left::-webkit-scrollbar {
  width: 6px;
}

.panel-left::-webkit-scrollbar-track {
  background: transparent;
}

.panel-left::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, var(--c-accent) 0%, var(--c-accent-light) 100%);
  border-radius: 3px;
}

.panel-center {
  display: flex;
  flex-direction: row;
  gap: 18px;
  overflow: hidden;
  padding-right: 0;
}

.panel-center-main {
  display: flex;
  flex-direction: column;
  gap: 18px;
  overflow-y: hidden;
  padding-right: 0;
  flex: 1;
}

.panel-center-main::-webkit-scrollbar {
  width: 8px;
}

.panel-center-main::-webkit-scrollbar-track {
  background: #12121e;
  border-radius: 10px;
  @apply shadow-neu-inset;
}

.panel-center-main::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--c-accent) 0%, var(--c-accent-light) 100%);
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(232, 92, 124, 0.4);
}

.panel-center-main::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, var(--c-accent-light) 0%, var(--c-accent) 100%);
}

.panel-right {
  display: flex;
  flex-direction: column;
  gap: 18px;
  overflow: hidden;
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

/* Background elements - kept for structure but display:none in original css */
.grid-background,
.glow-effect {
  display: none;
}

/* Full-screen background visualizer */
.fullscreen-visualizer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 0;
  padding: 0;
  z-index: 1;
  opacity: 0.12;
  pointer-events: none;
  transition: opacity 0.3s ease;
}

.fullscreen-visualizer.playing {
  opacity: 0.18;
}

.fullscreen-visualizer .viz-bar {
  flex: 1;
  min-height: 4px;
  border-radius: 0;
  transition: height 0.08s ease, background 0.2s ease;
  filter: blur(1px);
}

/* Responsive adjustments */
@media (max-width: 1600px) {
  .cockpit-grid {
    grid-template-columns: 320px 1fr 320px;
  }
}

@media (max-width: 1400px) {
  .cockpit-grid {
    grid-template-columns: 280px 1fr 300px;
    gap: 15px;
  }
}
</style>
