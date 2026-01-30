<template>
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
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { getTrackCoverStyle, getTrackInitials } from '@/utils'

const props = defineProps({
  track: Object,
  loading: Boolean,
  isPlaying: Boolean
})

const coverStyle = computed(() => getTrackCoverStyle(props.track))
const coverInitials = computed(() => getTrackInitials(props.track))

// Visualizer logic
const visualizerBars = ref(Array(32).fill(0))
let visualizerInterval = null

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

onMounted(() => {
  visualizerInterval = setInterval(animateVisualizer, 100)
})

onUnmounted(() => {
  if (visualizerInterval) {
    clearInterval(visualizerInterval)
  }
})

watch(() => props.isPlaying, (playing) => {
  if (!playing) {
    // Gradually reduce visualizer bars when paused
    visualizerBars.value = visualizerBars.value.map(v => Math.max(5, v * 0.8))
  }
})
</script>

<style scoped>
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

.cover-scanlines, .corner-decoration {
  display: none;
}
</style>
