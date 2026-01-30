<template>
  <div class="player-controls-wrapper">
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

        <button 
          class="control-btn secondary" 
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
        
        <button class="control-btn secondary" @click="$emit('addToPlaylist')" title="Добавить в плейлист">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M14 10H2v2h12v-2zm0-4H2v2h12V6zm4 8v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zM2 16h8v-2H2v2z"/>
          </svg>
          <span>ADD TO PLAYLIST</span>
        </button>
        
        <button v-if="hdTrackInfo" class="action-btn hd" @click="$emit('downloadHD')" title="Скачать HD версию">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
          </svg>
          <span>DOWNLOAD HD</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  isPlaying: Boolean,
  progress: Number,
  duration: Number,
  buffered: Number,
  shuffle: Boolean,
  repeat: String,
  isLiked: Boolean,
  hdTrackInfo: Object
})

defineEmits([
  'seek', 'toggle', 'prev', 'next', 'toggleShuffle', 
  'toggleRepeat', 'like', 'addToPlaylist', 'downloadHD'
])

const progressPercent = computed(() => {
  if (!props.duration) return 0
  return (props.progress / props.duration) * 100
})

const bufferedPercent = computed(() => {
  if (!props.duration) return 0
  return Math.round((props.buffered / props.duration) * 100)
})

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.player-controls-wrapper {
  display: flex;
  flex-direction: column;
  gap: 18px;
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
  margin-bottom: 1px;
  padding-bottom: 2px;
  border-bottom: 2px solid #1a1a28;
}

.module-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #db2220;
  font-family: 'Segoe UI', sans-serif;
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
  flex-wrap: wrap;
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
  width: auto;
  min-width: 48px;
  height: 48px;
  padding: 0 12px;
  border-radius: 24px;
  gap: 8px;
}

.control-btn.secondary span {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
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
</style>
