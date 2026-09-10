<template>
  <div class="dj-turntable-deck">
    <!-- Turntable Platter Base -->
    <div class="platter-chassis">
      <!-- Direct Drive & Speed Badge -->
      <div class="deck-indicator-top">
        <span class="speed-badge">33 ⅓ RPM</span>
        <span class="drive-badge">DIRECT DRIVE</span>
      </div>

      <!-- Rotating Turntable Platter -->
      <div class="turntable-platter" :class="{ spinning: isPlaying }">
        <!-- Aluminum Strobe Rim -->
        <div class="strobe-rim"></div>

        <!-- Vinyl Grooves -->
        <div class="vinyl-body">
          <div class="groove-ring ring-1"></div>
          <div class="groove-ring ring-2"></div>
          <div class="groove-ring ring-3"></div>

          <!-- Center Record Label with Cover Art -->
          <div class="record-label" :style="coverStyle">
            <img 
              v-if="track?.cover_url" 
              :src="getCoverUrl(track.cover_url, CoverSize.MEDIUM)" 
              alt="Обложка трека" 
              class="cover-image"
              loading="eager"
            />
            <span v-else class="initials">{{ coverInitials }}</span>
            
            <!-- Center Spindle -->
            <div class="center-spindle">
              <div class="spindle-dot"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Turntable Tone-arm Accent (DJ Deck aesthetic) -->
      <div class="tonearm-assembly" :class="{ engaged: isPlaying }">
        <div class="tonearm-base"></div>
        <div class="tonearm-shaft"></div>
        <div class="tonearm-headshell">
          <div class="cartridge-light" :class="{ active: isPlaying }"></div>
        </div>
      </div>

      <!-- Loading overlay -->
      <div v-if="loading" class="deck-loading-overlay">
        <div class="turntable-spinner"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
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
.dj-turntable-deck {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 8px 0;
  flex-shrink: 0;
}

.platter-chassis {
  position: relative;
  width: 250px;
  height: 250px;
  border-radius: 50%;
  background: radial-gradient(circle, #1a1c22 0%, #0d0e11 80%);
  border: 3px solid #232730;
  box-shadow: 
    0 12px 28px rgba(0, 0, 0, 0.8),
    inset 0 2px 6px rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Indicators */
.deck-indicator-top {
  position: absolute;
  top: -10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 10;
  pointer-events: none;
}

.speed-badge, .drive-badge {
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 0.8px;
  padding: 2px 7px;
  border-radius: 2px;
  background: #090a0d;
  color: var(--c-accent);
  border: 1px solid rgba(255, 255, 255, 0.08);
  font-family: var(--font-mono, monospace);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.drive-badge {
  color: var(--c-text-3);
}

/* Turntable Platter */
.turntable-platter {
  position: relative;
  width: 228px;
  height: 228px;
  border-radius: 50%;
  background: #0b0c0f;
  box-shadow: inset 0 0 12px rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
}

.turntable-platter.spinning {
  animation: turntableRotate 4s linear infinite;
}

@keyframes turntableRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Aluminum Strobe Rim with tactile notches */
.strobe-rim {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 4px dashed #3a3f4c;
  opacity: 0.8;
  pointer-events: none;
}

/* Vinyl Body */
.vinyl-body {
  position: relative;
  width: 212px;
  height: 212px;
  border-radius: 50%;
  background: radial-gradient(circle, #252830 0%, #121418 60%, #0a0b0d 100%);
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.7),
    inset 0 0 16px rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.groove-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.04);
  pointer-events: none;
}

.ring-1 { inset: 12px; }
.ring-2 { inset: 26px; border-style: dashed; }
.ring-3 { inset: 42px; }

/* Center Label with Cover Art */
.record-label {
  position: relative;
  width: 104px;
  height: 104px;
  border-radius: 50%;
  border: 2px solid #2a2e38;
  box-shadow: 0 0 14px rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: var(--c-bg-2);
  z-index: 2;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  pointer-events: none;
}

.initials {
  font-size: 26px;
  font-weight: 900;
  color: var(--c-accent);
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.8);
}

/* Spindle */
.center-spindle {
  position: absolute;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: radial-gradient(circle, #ced4da 0%, #6c757d 60%, #343a40 100%);
  border: 2px solid #212529;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3;
}

.spindle-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #000;
}

/* Tonearm Assembly */
.tonearm-assembly {
  position: absolute;
  top: 10px;
  right: -14px;
  width: 50px;
  height: 180px;
  pointer-events: none;
  z-index: 8;
  transition: transform 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
  transform-origin: 35px 25px;
  transform: rotate(-16deg);
}

.tonearm-assembly.engaged {
  transform: rotate(8deg);
}

.tonearm-base {
  position: absolute;
  top: 10px;
  right: 6px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: radial-gradient(circle, #495057 0%, #212529 100%);
  border: 2px solid #6c757d;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.8);
}

.tonearm-shaft {
  position: absolute;
  top: 25px;
  right: 18px;
  width: 3px;
  height: 130px;
  background: linear-gradient(90deg, #adb5bd 0%, #495057 100%);
  border-radius: 2px;
  transform-origin: top center;
  transform: rotate(4deg);
}

.tonearm-headshell {
  position: absolute;
  bottom: 12px;
  left: 12px;
  width: 14px;
  height: 24px;
  background: #212529;
  border: 1px solid #495057;
  border-radius: 2px;
  transform: rotate(20deg);
}

.cartridge-light {
  position: absolute;
  bottom: 2px;
  left: 4px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #333;
}

.cartridge-light.active {
  background: var(--c-accent);
  box-shadow: 0 0 8px var(--c-accent);
}

/* Loading overlay */
.deck-loading-overlay {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(9, 10, 13, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.turntable-spinner {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: var(--c-accent);
  animation: spinnerRotate 0.8s linear infinite;
}

@keyframes spinnerRotate {
  to { transform: rotate(360deg); }
}
</style>
