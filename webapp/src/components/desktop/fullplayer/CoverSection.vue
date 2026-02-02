<template>
  <div class="cover-section">
    <div class="cover-frame">
      <div class="cover-scanlines"></div>
      <div class="cover-wrapper" :style="coverStyle">
        <img v-if="track?.cover_url" :src="getCoverUrl(track.cover_url, CoverSize.XL)" alt="Cover" class="cover-image" />
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { getTrackCoverStyle, getTrackInitials, getCoverUrl, CoverSize } from '@/utils'

const props = defineProps({
  track: Object,
  loading: Boolean,
  isPlaying: Boolean
})

const coverStyle = computed(() => getTrackCoverStyle(props.track))
const coverInitials = computed(() => getTrackInitials(props.track))
</script>

<style scoped>
.cover-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
  background: #12121e;
  border-radius: 40px;
  padding: 24px;
  box-shadow: 
    inset 8px 8px 16px #08080f,
    inset -8px -8px 16px #1a1a28;
}

.cover-frame {
  position: relative;
  aspect-ratio: 1;
  border-radius: 24px;
  overflow: hidden;
  /* background and shadow removed for unified look */
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

.cover-scanlines, .corner-decoration {
  display: none;
}
</style>
