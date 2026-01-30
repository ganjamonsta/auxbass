<template>
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
</template>

<script setup>
defineProps({
  volume: Number,
  isMuted: Boolean
})

defineEmits(['toggleMute', 'setVolume'])
</script>

<style scoped>
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
</style>
