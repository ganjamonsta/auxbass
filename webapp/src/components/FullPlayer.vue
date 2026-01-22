<template>
  <div class="full-player">
    <!-- Header -->
    <div class="player-header">
      <button class="close-btn" @click="$emit('close')">
        ↓
      </button>
      <span class="player-title">Сейчас играет</span>
      <div class="spacer"></div>
    </div>

    <!-- Cover art -->
    <div class="player-cover">
      <div class="cover-image">
        🎵
      </div>
    </div>

    <!-- Track info -->
    <div class="player-info">
      <h2 class="track-title">{{ track?.title || 'Без названия' }}</h2>
      <p class="track-artist">{{ track?.artist || 'Неизвестный исполнитель' }}</p>
    </div>

    <!-- Progress bar -->
    <div class="progress-container">
      <input 
        type="range"
        class="progress-slider"
        :value="progress"
        :max="duration || 100"
        @input="$emit('seek', Number($event.target.value))"
      />
      <div class="progress-times">
        <span>{{ formatTime(progress) }}</span>
        <span>{{ formatTime(duration) }}</span>
      </div>
    </div>

    <!-- Controls -->
    <div class="player-controls">
      <button 
        class="control-btn secondary"
        :class="{ active: shuffle }"
        @click="$emit('toggleShuffle')"
      >
        🔀
      </button>
      
      <button class="control-btn" @click="$emit('prev')">
        ⏮
      </button>
      
      <button class="control-btn play-btn" @click="$emit('toggle')">
        <span v-if="isPlaying">⏸</span>
        <span v-else>▶</span>
      </button>
      
      <button class="control-btn" @click="$emit('next')">
        ⏭
      </button>
      
      <button 
        class="control-btn secondary"
        :class="{ active: repeat !== 'none' }"
        @click="$emit('toggleRepeat')"
      >
        <span v-if="repeat === 'one'">🔂</span>
        <span v-else>🔁</span>
      </button>
    </div>

    <!-- Volume control -->
    <div class="volume-container">
      <button class="volume-btn" @click="$emit('toggleMute')">
        <span v-if="isMuted || volume === 0">🔇</span>
        <span v-else-if="volume < 0.5">🔉</span>
        <span v-else>🔊</span>
      </button>
      <input 
        type="range"
        class="volume-slider"
        :value="isMuted ? 0 : volume * 100"
        min="0"
        max="100"
        @input="$emit('setVolume', Number($event.target.value) / 100)"
      />
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  track: Object,
  isPlaying: Boolean,
  progress: Number,
  duration: Number,
  volume: {
    type: Number,
    default: 1
  },
  isMuted: {
    type: Boolean,
    default: false
  },
  shuffle: Boolean,
  repeat: String,
})

const emit = defineEmits([
  'close',
  'toggle',
  'next',
  'prev',
  'seek',
  'setVolume',
  'toggleMute',
  'toggleShuffle',
  'toggleRepeat',
])

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.full-player {
  position: fixed;
  inset: 0;
  background: var(--tg-theme-bg-color);
  display: flex;
  flex-direction: column;
  z-index: 100;
  padding: 20px;
}

.player-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.close-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: none;
  font-size: 24px;
  cursor: pointer;
}

.player-title {
  flex: 1;
  text-align: center;
  font-size: 14px;
  color: var(--tg-theme-hint-color);
}

.spacer {
  width: 40px;
}

.player-cover {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.cover-image {
  width: 100%;
  max-width: 300px;
  aspect-ratio: 1;
  border-radius: 12px;
  background: var(--tg-theme-secondary-bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 80px;
}

.player-info {
  text-align: center;
  margin-bottom: 24px;
}

.track-title {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 4px;
}

.track-artist {
  font-size: 16px;
  color: var(--tg-theme-hint-color);
}

.progress-container {
  margin-bottom: 24px;
}

.progress-slider {
  width: 100%;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--tg-theme-secondary-bg-color);
  border-radius: 2px;
  outline: none;
}

.progress-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--tg-theme-button-color);
  cursor: pointer;
}

.progress-times {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: var(--tg-theme-hint-color);
}

.player-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding-bottom: 20px;
}

.control-btn {
  width: 48px;
  height: 48px;
  border: none;
  background: none;
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.control-btn.secondary {
  font-size: 20px;
  opacity: 0.5;
}

.control-btn.secondary.active {
  opacity: 1;
  color: var(--tg-theme-button-color);
}

.play-btn {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--tg-theme-button-color);
  color: var(--tg-theme-button-text-color);
  font-size: 28px;
}

.volume-container {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px 20px;
}

.volume-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: none;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.volume-slider {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--tg-theme-secondary-bg-color);
  border-radius: 2px;
  outline: none;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--tg-theme-button-color);
  cursor: pointer;
}
</style>
