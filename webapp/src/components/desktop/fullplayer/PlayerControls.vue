<template>
  <div class="player-controls">
    <!-- Progress Timeline -->
    <div class="progress-section">
      <div class="time-label current">{{ formatTime(displayProgress) }}</div>

      <div 
        class="progress-bar-container"
        @mousedown="handleMouseDown"
      >
        <!-- Buffered bar -->
        <div class="progress-buffered" :style="{ width: bufferedPercent + '%' }"></div>
        <!-- Active playback progress bar -->
        <div class="progress-fill" :style="{ width: progressPercent + '%' }">
          <div class="progress-thumb"></div>
        </div>
        <!-- Native range input for accessible & smooth dragging -->
        <input 
          type="range"
          class="progress-range"
          :value="displayProgress"
          min="0"
          :max="duration || 100"
          step="0.5"
          @input="handleInput"
          @change="handleChange"
          aria-label="Перемотка трека"
        />
      </div>

      <div class="time-label duration">{{ formatTime(duration) }}</div>
    </div>

    <!-- Main Playback Buttons -->
    <div class="main-buttons-row">
      <!-- Shuffle -->
      <button 
        class="neu-btn-icon sm mode-btn" 
        :class="{ active: shuffle }"
        @click="$emit('toggleShuffle')"
        :title="shuffle ? 'Перемешивание: включено' : 'Перемешать'"
      >
        <Shuffle :size="18" />
      </button>

      <!-- Previous -->
      <button 
        class="neu-btn-icon step-btn" 
        @click="$emit('prev')"
        title="Предыдущий трек"
      >
        <SkipBack :size="20" />
      </button>

      <!-- Play / Pause -->
      <button 
        class="play-btn"
        :class="{ playing: isPlaying }"
        @click="$emit('toggle')"
        :title="isPlaying ? 'Пауза (Space)' : 'Воспроизведение (Space)'"
      >
        <Pause v-if="isPlaying" :size="28" fill="currentColor" />
        <Play v-else :size="28" fill="currentColor" class="play-icon-offset" />
      </button>

      <!-- Next -->
      <button 
        class="neu-btn-icon step-btn" 
        @click="$emit('next')"
        title="Следующий трек"
      >
        <SkipForward :size="20" />
      </button>

      <!-- Repeat -->
      <button 
        class="neu-btn-icon sm mode-btn" 
        :class="{ active: repeat !== 'none' }"
        @click="$emit('toggleRepeat')"
        :title="repeatTooltip"
      >
        <Repeat1 v-if="repeat === 'one'" :size="18" />
        <Repeat v-else :size="18" />
      </button>
    </div>

    <!-- Secondary Action Bar -->
    <div class="action-buttons-row">
      <!-- Like Button -->
      <button 
        class="action-pill-btn" 
        :class="{ liked: isLiked }"
        @click="$emit('like')"
        title="В любимое"
      >
        <Heart 
          :size="16" 
          :fill="isLiked ? 'currentColor' : 'none'" 
          :stroke="isLiked ? 'currentColor' : 'currentColor'" 
        />
        <span>{{ isLiked ? 'В любимых' : 'Любимое' }}</span>
      </button>

      <!-- Add to playlist -->
      <button 
        class="action-pill-btn"
        @click="$emit('addToPlaylist')"
        title="Добавить в плейлист"
      >
        <ListPlus :size="16" />
        <span>Плейлист</span>
      </button>

      <!-- Toggle Lyrics -->
      <button 
        class="action-pill-btn"
        @click="$emit('toggleLyrics')"
        title="Текст песни"
      >
        <FileText :size="16" />
        <span>Текст</span>
      </button>

      <!-- HD Download (if available) -->
      <button 
        v-if="hdTrackInfo" 
        class="action-pill-btn hd"
        @click="$emit('downloadHD')"
        title="Скачать HD версию"
      >
        <Download :size="16" />
        <span>HD</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { 
  Play, Pause, SkipBack, SkipForward, 
  Shuffle, Repeat, Repeat1, Heart, 
  ListPlus, FileText, Download 
} from 'lucide-vue-next'

const props = defineProps({
  isPlaying: Boolean,
  progress: {
    type: Number,
    default: 0
  },
  duration: {
    type: Number,
    default: 0
  },
  buffered: {
    type: Number,
    default: 0
  },
  shuffle: Boolean,
  repeat: {
    type: String,
    default: 'none'
  },
  isLiked: Boolean,
  hdTrackInfo: Object
})

const emit = defineEmits([
  'seek', 'toggle', 'prev', 'next', 'toggleShuffle', 
  'toggleRepeat', 'like', 'addToPlaylist', 'downloadHD', 'toggleLyrics'
])

// Drag state for smooth seeking
const isDragging = ref(false)
const dragValue = ref(0)

const displayProgress = computed(() => {
  return isDragging.value ? dragValue.value : props.progress
})

const progressPercent = computed(() => {
  if (!props.duration) return 0
  return Math.min(100, (displayProgress.value / props.duration) * 100)
})

const bufferedPercent = computed(() => {
  if (!props.duration) return 0
  return Math.min(100, (props.buffered / props.duration) * 100)
})

const repeatTooltip = computed(() => {
  if (props.repeat === 'one') return 'Повтор одного трека'
  if (props.repeat === 'all') return 'Повтор всех треков'
  return 'Повтор выключен'
})

const handleMouseDown = () => {
  isDragging.value = true
}

const handleInput = (e) => {
  dragValue.value = Number(e.target.value)
}

const handleChange = (e) => {
  isDragging.value = false
  emit('seek', Number(e.target.value))
}

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds) || seconds < 0) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.player-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 520px;
  gap: 18px;
  padding: 0 16px;
}

/* Progress Timeline */
.progress-section {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
}

.time-label {
  font-size: 12px;
  font-family: var(--font-mono, monospace);
  font-weight: 600;
  color: var(--c-text-3);
  min-width: 40px;
  user-select: none;
}

.time-label.current {
  text-align: right;
  color: var(--c-text-2);
}

.time-label.duration {
  text-align: left;
}

.progress-bar-container {
  position: relative;
  flex: 1;
  height: 6px;
  background: var(--c-bg-0);
  border-radius: var(--r-full);
  display: flex;
  align-items: center;
  cursor: pointer;
  box-shadow: inset 1px 1px 3px var(--sh-inset-dark);
}

.progress-bar-container:hover {
  height: 8px;
}

.progress-buffered {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: rgba(255, 255, 255, 0.12);
  border-radius: var(--r-full);
  pointer-events: none;
  transition: width 0.2s ease;
}

.progress-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: linear-gradient(90deg, var(--c-accent) 0%, var(--c-accent-light) 100%);
  border-radius: var(--r-full);
  pointer-events: none;
  box-shadow: 0 0 10px var(--c-accent-glow);
}

.progress-thumb {
  position: absolute;
  right: -5px;
  top: 50%;
  transform: translateY(-50%) scale(0);
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
  transition: transform 0.15s ease;
}

.progress-bar-container:hover .progress-thumb {
  transform: translateY(-50%) scale(1);
}

.progress-range {
  position: absolute;
  inset: -6px 0;
  width: 100%;
  height: calc(100% + 12px);
  opacity: 0;
  cursor: pointer;
  z-index: 5;
  margin: 0;
}

/* Playback buttons */
.main-buttons-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.step-btn {
  width: 44px;
  height: 44px;
  color: var(--c-text-2);
}

.step-btn:hover {
  color: var(--c-text-1);
}

.mode-btn {
  color: var(--c-text-3);
  transition: all 0.2s ease;
}

.mode-btn:hover {
  color: var(--c-text-1);
}

.mode-btn.active {
  color: var(--c-accent);
  box-shadow: 
    inset 2px 2px 4px var(--sh-inset-dark),
    inset -1px -1px 3px var(--sh-inset-light),
    0 0 12px var(--c-accent-glow);
}

.play-btn {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: linear-gradient(145deg, var(--c-accent-light) 0%, var(--c-accent-dark) 100%);
  color: var(--c-accent-text, #000);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 
    4px 6px 16px rgba(0, 0, 0, 0.6),
    -2px -2px 6px rgba(255, 255, 255, 0.1),
    0 0 24px var(--c-accent-glow);
  transition: all 0.18s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.play-btn:hover {
  transform: scale(1.06);
  box-shadow: 
    4px 8px 20px rgba(0, 0, 0, 0.7),
    0 0 32px var(--c-accent-glow);
}

.play-btn:active {
  transform: scale(0.96);
}

.play-icon-offset {
  margin-left: 3px;
}

/* Secondary Actions */
.action-buttons-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.action-pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: var(--r-full);
  background: var(--c-bg-2);
  border: 1px solid rgba(255, 255, 255, 0.04);
  color: var(--c-text-2);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 
    3px 3px 6px var(--sh-dark),
    -1px -1px 3px var(--sh-light);
  transition: all 0.18s ease;
}

.action-pill-btn:hover {
  color: var(--c-text-1);
  transform: translateY(-1px);
  background: var(--c-bg-3);
}

.action-pill-btn:active {
  transform: translateY(1px);
  box-shadow: inset 2px 2px 4px var(--sh-inset-dark);
}

.action-pill-btn.liked {
  color: #ff4d6d;
  box-shadow: 
    3px 3px 6px var(--sh-dark),
    -1px -1px 3px var(--sh-light),
    0 0 12px rgba(255, 77, 109, 0.3);
}

.action-pill-btn.hd {
  color: #ffd700;
}
</style>
