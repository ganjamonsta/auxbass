<template>
  <div 
    class="volume-control" 
    @wheel.prevent="handleWheel"
    title="Колёсико мыши для регулировки громкости"
  >
    <button 
      class="neu-btn-icon sm volume-btn" 
      :class="{ muted: isMuted || volume === 0 }"
      @click="$emit('toggleMute')"
      :title="isMuted ? 'Включить звук' : 'Выключить звук'"
    >
      <VolumeX v-if="isMuted || volume === 0" :size="18" />
      <Volume1 v-else-if="volume < 0.5" :size="18" />
      <Volume2 v-else :size="18" />
    </button>

    <div class="slider-wrapper">
      <input 
        type="range"
        class="neu-slider volume-slider"
        :value="currentVolumePercent"
        min="0"
        max="100"
        step="1"
        @input="handleInput"
        aria-label="Громкость"
      />
      <div 
        class="volume-fill" 
        :style="{ width: currentVolumePercent + '%' }"
      ></div>
    </div>

    <span class="volume-label">{{ currentVolumePercent }}%</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Volume2, Volume1, VolumeX } from 'lucide-vue-next'

const props = defineProps({
  volume: {
    type: Number,
    default: 1
  },
  isMuted: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggleMute', 'setVolume'])

const currentVolumePercent = computed(() => {
  if (props.isMuted) return 0
  return Math.round((props.volume ?? 1) * 100)
})

const handleInput = (e) => {
  const val = Number(e.target.value) / 100
  emit('setVolume', Math.max(0, Math.min(1, val)))
}

const handleWheel = (e) => {
  const delta = e.deltaY < 0 ? 0.05 : -0.05
  const newVol = Math.max(0, Math.min(1, (props.volume ?? 1) + delta))
  emit('setVolume', newVol)
}
</script>

<style scoped>
.volume-control {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 14px;
  border-radius: var(--r-full);
  background: var(--c-bg-2);
  border: 1px solid rgba(255, 255, 255, 0.04);
  box-shadow: 
    3px 3px 8px var(--sh-dark),
    -2px -2px 5px var(--sh-light);
  min-width: 190px;
}

.volume-btn {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  color: var(--c-text-2);
}

.volume-btn.muted {
  color: var(--c-error, #f44336);
}

.slider-wrapper {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  height: 6px;
  background: var(--c-bg-0);
  border-radius: var(--r-full);
  box-shadow: inset 1px 1px 3px var(--sh-inset-dark);
}

.volume-slider {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: 3;
  margin: 0;
}

.volume-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  border-radius: var(--r-full);
  background: linear-gradient(90deg, var(--c-accent) 0%, var(--c-accent-light) 100%);
  box-shadow: 0 0 8px var(--c-accent-glow);
  pointer-events: none;
  transition: width 0.05s linear;
}

.volume-label {
  font-size: 11px;
  font-weight: 700;
  font-family: var(--font-mono, monospace);
  color: var(--c-text-3);
  min-width: 34px;
  text-align: right;
  user-select: none;
}
</style>
