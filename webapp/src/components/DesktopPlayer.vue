<template>
  <div class="desktop-player" :class="{ playing: isPlaying }">
    <!-- Left side - Volume knob -->
    <div class="player-left">
      <div 
        class="volume-knob"
        @mousedown="startVolumeAdjust"
        @wheel.prevent="handleVolumeWheel"
        :style="{ '--rotation': volumeRotation + 'deg' }"
      >
        <div class="knob-outer">
          <div class="knob-inner">
            <div class="knob-indicator"></div>
          </div>
        </div>
        <div class="knob-ring" :class="{ active: isAdjustingVolume }"></div>
      </div>
      <span class="vol-label">VOL</span>
    </div>

    <!-- Center - LCD Display -->
    <div class="lcd-panel">
      <div class="lcd-frame">
        <div class="lcd-screen">
          <!-- Title row - centered -->
          <div class="lcd-title-row">
            <span class="lcd-status">{{ isPlaying ? '▶' : '■' }}</span>
            <div class="lcd-text-container">
              <div class="lcd-text" :class="{ scrolling: shouldScroll }">
                <span class="segment-text">{{ displayText }}</span>
                <span v-if="shouldScroll" class="segment-text clone">{{ displayText }}</span>
              </div>
            </div>
          </div>

          <!-- Progress row -->
          <div class="lcd-progress-row">
            <span class="lcd-time">{{ formatTime(progress) }}</span>
            <div class="lcd-progress" @click="handleProgressClick" @mousedown="startSeek">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
                <div class="progress-buffered" :style="{ width: bufferedPercent + '%' }"></div>
              </div>
            </div>
            <span class="lcd-time">{{ formatTime(duration) }}</span>
          </div>

          <!-- Equalizer visualization -->
          <div class="lcd-eq">
            <div 
              v-for="i in 16" 
              :key="i" 
              class="eq-bar"
              :style="{ height: getEqHeight(i) + '%' }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Control buttons under LCD -->
      <div class="lcd-controls">
        <button class="ctrl-btn mode" :class="{ active: shuffle }" @click="$emit('toggleShuffle')" title="Shuffle">
          <span class="btn-label">RND</span>
        </button>
        <button class="ctrl-btn" @click="$emit('prev')" title="Previous">
          <span class="btn-icon">⏮</span>
        </button>
        <button class="ctrl-btn play-btn" @click="$emit('toggle')" :title="isPlaying ? 'Pause' : 'Play'">
          <span class="btn-icon">{{ isPlaying ? '⏸' : '⏵' }}</span>
        </button>
        <button class="ctrl-btn" @click="$emit('next')" title="Next">
          <span class="btn-icon">⏭</span>
        </button>
        <button class="ctrl-btn mode" :class="{ active: repeat !== 'none' }" @click="$emit('toggleRepeat')" title="Repeat">
          <span class="btn-label">{{ repeat === 'one' ? 'RPT1' : 'RPT' }}</span>
        </button>
      </div>
    </div>

    <!-- Right side - Cover & expand -->
    <div class="player-right">
      <div class="cover-display" @click="$emit('expand')" @contextmenu.prevent="$emit('menu')">
        <div class="cover-art" :style="coverStyle">
          <img v-if="track?.cover_url" :src="track.cover_url" alt="" />
          <span v-else class="cover-text">{{ coverInitials }}</span>
        </div>
        <div class="vinyl-disc" :class="{ spinning: isPlaying }">
          <div class="vinyl-groove"></div>
          <div class="vinyl-groove"></div>
          <div class="vinyl-groove"></div>
          <div class="vinyl-center"></div>
        </div>
      </div>
      
      <!-- Menu button for desktop -->
      <button class="menu-btn" @click="$emit('menu')" title="Меню">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
        </svg>
      </button>
      
      <button class="mute-btn" :class="{ muted: isMuted }" @click="$emit('toggleMute')">
        {{ isMuted ? '🔇' : '🔊' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  track: Object,
  isPlaying: Boolean,
  loading: Boolean,
  progress: { type: Number, default: 0 },
  duration: { type: Number, default: 0 },
  buffered: { type: Number, default: 0 },
  volume: { type: Number, default: 1 },
  isMuted: Boolean,
  shuffle: Boolean,
  repeat: { type: String, default: 'none' }
})

const emit = defineEmits([
  'toggle', 'prev', 'next', 'expand', 'menu',
  'toggleShuffle', 'toggleRepeat', 'toggleMute', 'setVolume', 'seek'
])

// Volume knob
const isAdjustingVolume = ref(false)
const startY = ref(0)
const startVolume = ref(0)

const volumeRotation = computed(() => {
  // -135deg (min) to +135deg (max)
  return -135 + (props.volume * 270)
})

const startVolumeAdjust = (e) => {
  isAdjustingVolume.value = true
  startY.value = e.clientY
  startVolume.value = props.volume
  document.addEventListener('mousemove', onVolumeMove)
  document.addEventListener('mouseup', stopVolumeAdjust)
}

const onVolumeMove = (e) => {
  if (!isAdjustingVolume.value) return
  const delta = (startY.value - e.clientY) / 100
  const newVolume = Math.max(0, Math.min(1, startVolume.value + delta))
  emit('setVolume', newVolume)
}

const stopVolumeAdjust = () => {
  isAdjustingVolume.value = false
  document.removeEventListener('mousemove', onVolumeMove)
  document.removeEventListener('mouseup', stopVolumeAdjust)
}

const handleVolumeWheel = (e) => {
  const delta = e.deltaY > 0 ? -0.05 : 0.05
  const newVolume = Math.max(0, Math.min(1, props.volume + delta))
  emit('setVolume', newVolume)
}

// Display text
const displayText = computed(() => {
  if (!props.track) return 'NO DISC'
  const artist = props.track.artist || 'UNKNOWN'
  const title = props.track.title || 'UNTITLED'
  return `${artist} - ${title}`.toUpperCase()
})

const shouldScroll = computed(() => displayText.value.length > 30)

// Progress
const progressPercent = computed(() => {
  if (!props.duration) return 0
  return (props.progress / props.duration) * 100
})

const bufferedPercent = computed(() => {
  if (!props.duration) return 0
  return (props.buffered / props.duration) * 100
})

// Seek functionality
const handleProgressClick = (e) => {
  const rect = e.currentTarget.getBoundingClientRect()
  const percent = (e.clientX - rect.left) / rect.width
  const seekTime = percent * props.duration
  emit('seek', seekTime)
}

const isSeeking = ref(false)

const startSeek = (e) => {
  isSeeking.value = true
  document.addEventListener('mousemove', onSeekMove)
  document.addEventListener('mouseup', stopSeek)
}

const onSeekMove = (e) => {
  if (!isSeeking.value) return
  const progressEl = document.querySelector('.lcd-progress')
  if (!progressEl) return
  const rect = progressEl.getBoundingClientRect()
  const percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  const seekTime = percent * props.duration
  emit('seek', seekTime)
}

const stopSeek = () => {
  isSeeking.value = false
  document.removeEventListener('mousemove', onSeekMove)
  document.removeEventListener('mouseup', stopSeek)
}

// Cover
const coverStyle = computed(() => {
  if (props.track?.cover_url) return {}
  const str = props.track?.title || 'Music'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash % 360)
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 60%, 30%) 0%, hsl(${(hue + 40) % 360}, 50%, 20%) 100%)`
  }
})

const coverInitials = computed(() => {
  const title = props.track?.title || 'M'
  return title.substring(0, 2).toUpperCase()
})

// Time format
const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// Equalizer animation
const eqValues = ref(Array(16).fill(20))

const getEqHeight = (index) => {
  return eqValues.value[index - 1]
}

let eqInterval = null

const animateEq = () => {
  if (props.isPlaying) {
    eqValues.value = eqValues.value.map(() => 
      Math.random() * 60 + 20
    )
  } else {
    eqValues.value = eqValues.value.map(() => 15)
  }
}

onMounted(() => {
  eqInterval = setInterval(animateEq, 100)
})

onUnmounted(() => {
  clearInterval(eqInterval)
  document.removeEventListener('mousemove', onVolumeMove)
  document.removeEventListener('mouseup', stopVolumeAdjust)
  document.removeEventListener('mousemove', onSeekMove)
  document.removeEventListener('mouseup', stopSeek)
})
</script>

<style scoped>
.desktop-player {
  height: 100px;
  min-height: 100px;
  max-height: 100px;
  background: linear-gradient(180deg, #1a1a1a 0%, #0d0d0d 50%, #1a1a1a 100%);
  border-top: 1px solid #333;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 20px;
  box-shadow: 
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 -4px 20px rgba(0, 0, 0, 0.5);
  position: relative;
  overflow: visible;
}

.desktop-player::before {
  content: '';
  position: absolute;
  inset: 0;
  background: 
    linear-gradient(90deg, rgba(0,0,0,0.3) 0%, transparent 10%, transparent 90%, rgba(0,0,0,0.3) 100%);
  pointer-events: none;
}

/* Volume Knob */
.player-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.volume-knob {
  position: relative;
  cursor: pointer;
}

.knob-outer {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(145deg, #2a2a2a, #1a1a1a);
  box-shadow: 
    4px 4px 10px rgba(0, 0, 0, 0.5),
    -2px -2px 8px rgba(255, 255, 255, 0.05),
    inset 0 0 20px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.knob-inner {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(145deg, #333, #222);
  box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.5);
  position: relative;
  transform: rotate(var(--rotation));
  transition: transform 0.1s ease;
}

.knob-indicator {
  position: absolute;
  top: 4px;
  left: 50%;
  transform: translateX(-50%);
  width: 3px;
  height: 8px;
  background: #4DC3FF;
  border-radius: 2px;
  box-shadow: 0 0 8px #4DC3FF, 0 0 16px rgba(77, 195, 255, 0.6);
}

.knob-ring {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.knob-ring.active {
  border-color: #4DC3FF;
  box-shadow: 0 0 15px rgba(77, 195, 255, 0.5);
}

.vol-label {
  font-size: 8px;
  color: #4DC3FF;
  text-shadow: 0 0 5px rgba(77, 195, 255, 0.6);
  font-weight: bold;
  letter-spacing: 1px;
}

/* LCD Panel */
.lcd-panel {
  flex: 1;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16px;
}

.lcd-frame {
  flex: 1;
  background: #0a0a0a;
  border-radius: 4px;
  padding: 3px;
  box-shadow: 
    inset 2px 2px 6px rgba(0, 0, 0, 0.8),
    inset -1px -1px 3px rgba(255, 255, 255, 0.05);
}

.lcd-screen {
  background: linear-gradient(180deg, #0a1520 0%, #051015 50%, #0a1520 100%);
  border-radius: 2px;
  padding: 6px 12px;
  height: 70px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

/* Title row - centered in LCD */
.lcd-title-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex: 1;
}

/* Progress row */
.lcd-progress-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.lcd-status {
  color: #4DC3FF;
  font-size: 14px;
  text-shadow: 0 0 8px rgba(77, 195, 255, 0.6);
  flex-shrink: 0;
}

.lcd-text-container {
  flex: 1;
  max-width: 500px;
  overflow: hidden;
  mask-image: linear-gradient(90deg, transparent, black 3%, black 97%, transparent);
}

.lcd-text {
  display: flex;
  white-space: nowrap;
  justify-content: center;
}

.lcd-text.scrolling {
  justify-content: flex-start;
  animation: lcd-scroll 12s linear infinite;
}

@keyframes lcd-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

.segment-text {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  font-weight: bold;
  color: #4DC3FF;
  text-shadow: 
    0 0 5px #4DC3FF,
    0 0 10px rgba(77, 195, 255, 0.6),
    0 0 20px rgba(0, 188, 212, 0.4);
  letter-spacing: 1px;
  padding-right: 50px;
}

.lcd-time {
  font-family: 'Courier New', monospace;
  font-size: 10px;
  color: #7DD3FC;
  text-shadow: 0 0 5px rgba(77, 195, 255, 0.6);
  min-width: 32px;
  flex-shrink: 0;
}

.lcd-progress {
  flex: 2;
  min-width: 100px;
  cursor: pointer;
  padding: 4px 0;
}

.progress-bar {
  height: 4px;
  background: rgba(77, 195, 255, 0.15);
  border-radius: 2px;
  position: relative;
  overflow: visible;
}

.lcd-progress:hover .progress-bar {
  height: 6px;
}

.lcd-progress:hover .progress-fill::after {
  content: '';
  position: absolute;
  right: -4px;
  top: 50%;
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  background: #4DC3FF;
  border-radius: 50%;
  box-shadow: 0 0 6px rgba(77, 195, 255, 0.8);
}

.progress-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: linear-gradient(90deg, #00BCD4, #4DC3FF);
  box-shadow: 0 0 8px rgba(77, 195, 255, 0.6);
  border-radius: 2px;
  transition: width 0.1s linear;
}

.progress-buffered {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: rgba(77, 195, 255, 0.2);
  border-radius: 2px;
  z-index: -1;
}

/* Equalizer */
.lcd-eq {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 2px;
  height: 16px;
}

.eq-bar {
  width: 6px;
  min-height: 2px;
  background: linear-gradient(180deg, #4DC3FF, #00BCD4);
  border-radius: 1px;
  box-shadow: 0 0 4px rgba(77, 195, 255, 0.6);
  transition: height 0.1s ease;
}

/* Control Buttons */
.lcd-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  flex-shrink: 0;
}

.ctrl-btn {
  background: linear-gradient(180deg, #2a2a2a, #1a1a1a);
  border: 1px solid #333;
  border-radius: 4px;
  color: #7DD3FC;
  font-size: 12px;
  padding: 8px 10px;
  cursor: pointer;
  transition: all 0.15s;
  box-shadow: 
    2px 2px 5px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.ctrl-btn:hover {
  background: linear-gradient(180deg, #333, #222);
  color: #4DC3FF;
  text-shadow: 0 0 8px rgba(77, 195, 255, 0.6);
}

.ctrl-btn:active {
  box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.5);
  transform: translateY(1px);
}

.ctrl-btn.play-btn {
  padding: 8px 16px;
  font-size: 16px;
}

.ctrl-btn.mode {
  font-size: 9px;
  padding: 8px 6px;
}

.ctrl-btn.mode.active {
  color: #4DC3FF;
  text-shadow: 0 0 8px rgba(77, 195, 255, 0.6);
  border-color: #4DC3FF;
  box-shadow: 
    2px 2px 5px rgba(0, 0, 0, 0.5),
    0 0 10px rgba(77, 195, 255, 0.3);
}

.btn-label {
  font-weight: bold;
  letter-spacing: 1px;
}

.btn-icon {
  font-family: inherit;
}

/* Right Side */
.player-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cover-display {
  position: relative;
  width: 60px;
  height: 60px;
  cursor: pointer;
}

.cover-art {
  width: 100%;
  height: 100%;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  font-weight: bold;
  position: relative;
  z-index: 2;
}

.cover-art img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.vinyl-disc {
  position: absolute;
  width: 50px;
  height: 50px;
  right: -18px;
  top: 50%;
  transform: translateY(-50%);
  background: linear-gradient(135deg, #1a1a1a, #0a0a0a);
  border-radius: 50%;
  z-index: 1;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.5);
}

.vinyl-disc.spinning {
  animation: spin-vinyl 3s linear infinite;
}

@keyframes spin-vinyl {
  to { transform: translateY(-50%) rotate(360deg); }
}

.vinyl-groove {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.vinyl-groove:nth-child(1) { inset: 15%; }
.vinyl-groove:nth-child(2) { inset: 25%; }
.vinyl-groove:nth-child(3) { inset: 35%; }

.vinyl-center {
  position: absolute;
  inset: 40%;
  background: #4DC3FF;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(77, 195, 255, 0.6);
}

.mute-btn {
  background: transparent;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.15s;
  filter: grayscale(0);
}

.mute-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.mute-btn.muted {
  filter: grayscale(1);
  opacity: 0.5;
}

/* Menu button */
.menu-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

/* Playing state glow */
.desktop-player.playing {
  box-shadow: 
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 -4px 20px rgba(0, 0, 0, 0.5),
    0 0 30px rgba(77, 195, 255, 0.15);
}

.desktop-player.playing .lcd-frame {
  box-shadow: 
    inset 2px 2px 6px rgba(0, 0, 0, 0.8),
    inset -1px -1px 3px rgba(255, 255, 255, 0.05),
    0 0 20px rgba(77, 195, 255, 0.25);
}
</style>
