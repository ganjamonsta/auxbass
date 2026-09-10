<template>
  <div class="cover-section">
    <div class="cover-container" :class="{ playing: isPlaying }">
      <!-- Ambient glow behind cover -->
      <div class="cover-glow" :style="coverGlowStyle"></div>

      <!-- Vinyl disc -->
      <div class="vinyl-disc" :class="{ spinning: isPlaying }">
        <div class="vinyl-groove"></div>
        <div class="vinyl-groove inner"></div>
        <div class="vinyl-label" :style="coverStyle">
          <div class="vinyl-center"></div>
        </div>
      </div>

      <!-- Front Album Cover -->
      <div class="cover-art neu-surface" :style="coverStyle">
        <img 
          v-if="track?.cover_url" 
          :src="getCoverUrl(track.cover_url, CoverSize.XL)" 
          alt="Обложка трека" 
          class="cover-image"
          loading="eager"
        />
        <div v-else class="cover-placeholder">
          <span class="cover-initials">{{ coverInitials }}</span>
        </div>

        <!-- Loading overlay -->
        <Transition name="fade">
          <div v-if="loading" class="loading-overlay">
            <div class="loading-spinner"></div>
            <span class="loading-text">Загрузка...</span>
          </div>
        </Transition>
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

const coverGlowStyle = computed(() => {
  if (props.track?.cover_url) {
    return {
      backgroundImage: `url(${getCoverUrl(props.track.cover_url, CoverSize.MEDIUM)})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  return {
    background: 'radial-gradient(circle, var(--c-accent-glow) 0%, transparent 70%)'
  }
})
</script>

<style scoped>
.cover-section {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 10px 0 20px;
}

.cover-container {
  position: relative;
  width: 320px;
  height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Ambient glow */
.cover-glow {
  position: absolute;
  inset: -15px;
  border-radius: var(--r-xl);
  filter: blur(28px);
  opacity: 0.28;
  z-index: 0;
  pointer-events: none;
  transform: translateZ(0);
  transition: opacity 0.4s ease;
}

.cover-container.playing .cover-glow {
  opacity: 0.42;
}

/* Vinyl disc */
.vinyl-disc {
  position: absolute;
  top: 10px;
  bottom: 10px;
  left: 10px;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: radial-gradient(circle, #252525 0%, #151515 50%, #0d0d0d 100%);
  border: 2px solid #2e2e2e;
  box-shadow: 
    8px 8px 24px rgba(0, 0, 0, 0.7),
    inset 0 0 20px rgba(0, 0, 0, 0.9);
  z-index: 1;
  transition: transform 0.5s cubic-bezier(0.2, 0.8, 0.2, 1), opacity 0.4s ease;
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transform: translateX(0);
}

.cover-container.playing .vinyl-disc {
  opacity: 1;
  transform: translateX(64px);
}

.vinyl-disc.spinning {
  animation: vinylSpin 6s linear infinite;
}

@keyframes vinylSpin {
  from {
    transform: translateX(64px) rotate(0deg);
  }
  to {
    transform: translateX(64px) rotate(360deg);
  }
}

.vinyl-groove {
  position: absolute;
  inset: 18px;
  border-radius: 50%;
  border: 1px dashed rgba(255, 255, 255, 0.06);
}

.vinyl-groove.inner {
  inset: 48px;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.vinyl-label {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
  border: 2px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.vinyl-center {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #0d0d0d;
  border: 3px solid #333;
}

/* Cover art */
.cover-art {
  position: relative;
  width: 320px;
  height: 320px;
  border-radius: var(--r-xl);
  overflow: hidden;
  z-index: 2;
  box-shadow: 
    8px 8px 24px var(--sh-dark),
    -4px -4px 12px var(--sh-light);
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-bg-2);
}

.cover-container.playing .cover-art {
  transform: scale(0.98);
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, var(--c-bg-3) 0%, var(--c-bg-1) 100%);
}

.cover-initials {
  font-size: 72px;
  font-weight: 800;
  color: var(--c-accent);
  text-shadow: 0 2px 12px var(--c-accent-glow);
  user-select: none;
}

/* Loading overlay */
.loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(13, 13, 13, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 5;
}

.loading-spinner {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 3px solid var(--c-bg-3);
  border-top-color: var(--c-accent);
  animation: spin 0.8s linear infinite;
}

.loading-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-2);
  letter-spacing: 0.5px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 1440px) {
  .cover-container, .cover-art {
    width: 280px;
    height: 280px;
  }
  .vinyl-disc {
    width: 260px;
    height: 260px;
  }
}
</style>
