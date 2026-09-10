<template>
  <div class="dj-controls-section">
    <!-- Timeline / LED Progress Scrubber -->
    <div class="timeline-module">
      <span class="time-readout">{{ formatTime(displayProgress) }}</span>

      <div 
        class="scrubber-track"
        @mousedown="handleMouseDown"
      >
        <!-- Buffered section -->
        <div class="buffered-bar" :style="{ width: bufferedPercent + '%' }"></div>
        <!-- Active playback bar -->
        <div class="active-bar" :style="{ width: progressPercent + '%' }">
          <div class="needle-glow"></div>
        </div>

        <input 
          type="range"
          class="seek-input"
          :value="displayProgress"
          min="0"
          :max="duration || 100"
          step="0.5"
          @input="handleInput"
          @change="handleChange"
          aria-label="Перемотка"
        />
      </div>

      <span class="time-readout remain">{{ formatTime(duration) }}</span>
    </div>

    <!-- Main DJ Transport Row -->
    <div class="transport-row">
      <!-- SYNC / SHUFFLE Button -->
      <button 
        class="dj-tactile-btn sync-btn" 
        :class="{ active: shuffle }"
        @click="$emit('toggleShuffle')"
        :title="shuffle ? 'Случайно: ВКЛ' : 'Перемешать треки'"
      >
        <Shuffle :size="15" />
        <span class="btn-label">SYNC</span>
      </button>

      <!-- CUE / PREV Button -->
      <button 
        class="dj-tactile-btn cue-btn" 
        @click="$emit('prev')"
        title="Предыдущий трек"
      >
        <SkipBack :size="18" />
        <span class="btn-label">CUE</span>
      </button>

      <!-- Giant Circular PLAY / PAUSE Button -->
      <button 
        class="dj-play-button"
        :class="{ playing: isPlaying }"
        @click="$emit('toggle')"
        :title="isPlaying ? 'Пауза (Space)' : 'Воспроизведение (Space)'"
      >
        <div class="play-halo"></div>
        <div class="play-inner">
          <Pause v-if="isPlaying" :size="24" fill="currentColor" />
          <Play v-else :size="24" fill="currentColor" class="play-icon-offset" />
        </div>
      </button>

      <!-- NEXT Button -->
      <button 
        class="dj-tactile-btn step-btn" 
        @click="$emit('next')"
        title="Следующий трек"
      >
        <SkipForward :size="18" />
        <span class="btn-label">NEXT</span>
      </button>

      <!-- LOOP / REPEAT Button -->
      <button 
        class="dj-tactile-btn loop-btn" 
        :class="{ active: repeat !== 'none' }"
        @click="$emit('toggleRepeat')"
        :title="repeatTooltip"
      >
        <Repeat1 v-if="repeat === 'one'" :size="15" />
        <Repeat v-else :size="15" />
        <span class="btn-label">{{ repeat === 'one' ? 'LOOP 1' : 'LOOP' }}</span>
      </button>
    </div>

    <!-- Bottom Mixer Strip: Volume Fader & Deck Utilities -->
    <div class="mixer-strip">
      <!-- Volume Fader Section -->
      <div class="fader-group" @wheel.prevent="handleVolumeWheel">
        <button 
          class="mute-toggle-btn"
          :class="{ muted: isMuted || volume === 0 }"
          @click="$emit('toggleMute')"
          :title="isMuted ? 'Включить звук' : 'Выключить звук'"
        >
          <VolumeX v-if="isMuted || volume === 0" :size="15" />
          <Volume2 v-else :size="15" />
        </button>

        <div class="fader-track-container">
          <div class="fader-ticks">
            <span>-∞</span>
            <span>-12</span>
            <span>0</span>
            <span>+6</span>
          </div>

          <div class="fader-rail">
            <div class="fader-fill" :style="{ width: volumePercent + '%' }"></div>
            <div class="fader-cap" :style="{ left: volumePercent + '%' }">
              <div class="cap-line"></div>
            </div>
            <input 
              type="range"
              class="fader-native-input"
              :value="volumePercent"
              min="0"
              max="100"
              @input="handleVolumeInput"
              aria-label="Громкость"
            />
          </div>
        </div>

        <span class="volume-readout">{{ volumePercent }}%</span>
      </div>

      <!-- Quick Action Hardware Buttons -->
      <div class="deck-actions-group">
        <!-- Favorite (Heart) -->
        <button 
          class="dj-action-btn"
          :class="{ active: isLiked }"
          @click="$emit('like')"
          title="В любимое"
        >
          <Heart :size="14" :fill="isLiked ? 'currentColor' : 'none'" />
        </button>

        <!-- Add to Playlist -->
        <button 
          class="dj-action-btn"
          @click="$emit('addToPlaylist')"
          title="Добавить в плейлист"
        >
          <ListPlus :size="14" />
        </button>

        <!-- Download HD (if available) -->
        <button 
          v-if="hdTrackInfo" 
          class="dj-action-btn hd-btn"
          @click="$emit('downloadHD')"
          title="Скачать HD версию"
        >
          <Download :size="14" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { 
  Play, Pause, SkipBack, SkipForward, 
  Shuffle, Repeat, Repeat1, Heart, 
  ListPlus, Download, Volume2, VolumeX 
} from 'lucide-vue-next'

const props = defineProps({
  isPlaying: Boolean,
  progress: { type: Number, default: 0 },
  duration: { type: Number, default: 0 },
  buffered: { type: Number, default: 0 },
  shuffle: Boolean,
  repeat: { type: String, default: 'none' },
  isLiked: Boolean,
  hdTrackInfo: Object,
  volume: { type: Number, default: 1 },
  isMuted: { type: Boolean, default: false }
})

const emit = defineEmits([
  'seek', 'toggle', 'prev', 'next', 'toggleShuffle', 
  'toggleRepeat', 'like', 'addToPlaylist', 'downloadHD', 'toggleLyrics',
  'setVolume', 'toggleMute'
])

// Scrubber state
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

const volumePercent = computed(() => {
  if (props.isMuted) return 0
  return Math.round((props.volume ?? 1) * 100)
})

const repeatTooltip = computed(() => {
  if (props.repeat === 'one') return 'Повтор 1 трека'
  if (props.repeat === 'all') return 'Повтор всех'
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

const handleVolumeInput = (e) => {
  const val = Number(e.target.value) / 100
  emit('setVolume', Math.max(0, Math.min(1, val)))
}

const handleVolumeWheel = (e) => {
  const delta = e.deltaY < 0 ? 0.05 : -0.05
  const newVol = Math.max(0, Math.min(1, (props.volume ?? 1) + delta))
  emit('setVolume', newVol)
}

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds) || seconds < 0) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.dj-controls-section {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 440px;
  gap: 12px;
  user-select: none;
  flex-shrink: 0;
}

/* Timeline / Scrubber */
.timeline-module {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 4px 6px;
  background: #090a0d;
  border-radius: var(--r-xs);
  border: 1px solid #191c23;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.9);
}

.time-readout {
  font-size: 11px;
  font-weight: 800;
  font-family: var(--font-mono, monospace);
  color: var(--c-accent);
  min-width: 36px;
  text-align: center;
  letter-spacing: 0.5px;
}

.time-readout.remain {
  color: var(--c-text-3);
}

.scrubber-track {
  position: relative;
  flex: 1;
  height: 8px;
  background: #14171e;
  border-radius: 2px;
  cursor: pointer;
  overflow: hidden;
}

.buffered-bar {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.active-bar {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: linear-gradient(90deg, #169c46 0%, #1db954 100%);
  border-radius: 2px;
  box-shadow: 0 0 8px rgba(29, 185, 84, 0.7);
}

.needle-glow {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #ffffff;
  box-shadow: 0 0 6px #ffffff;
}

.seek-input {
  position: absolute;
  inset: -6px 0;
  width: 100%;
  height: calc(100% + 12px);
  opacity: 0;
  cursor: pointer;
  z-index: 5;
  margin: 0;
}

/* Transport Row */
.transport-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 12px;
  background: #121418;
  border-radius: var(--r-sm);
  border: 1px solid #232730;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.dj-tactile-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  width: 48px;
  height: 48px;
  background: linear-gradient(180deg, #23262f 0%, #15171c 100%);
  border: 1px solid #323742;
  border-radius: var(--r-xs);
  color: var(--c-text-2);
  cursor: pointer;
  box-shadow: 
    0 3px 6px rgba(0, 0, 0, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  transition: all 0.12s ease;
}

.dj-tactile-btn:hover {
  background: linear-gradient(180deg, #2b2f3a 0%, #1a1d24 100%);
  color: #ffffff;
}

.dj-tactile-btn:active {
  transform: translateY(1px);
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.8);
}

.dj-tactile-btn.active {
  color: var(--c-accent);
  border-color: var(--c-accent);
  box-shadow: 
    0 0 12px rgba(29, 185, 84, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.btn-label {
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 0.5px;
  font-family: var(--font-mono, monospace);
}

/* Giant Circular DJ Play Button */
.dj-play-button {
  position: relative;
  width: 62px;
  height: 62px;
  border-radius: 50%;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s ease;
}

.dj-play-button:hover {
  transform: scale(1.05);
}

.dj-play-button:active {
  transform: scale(0.96);
}

.play-halo {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid #3a404e;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.7);
  transition: all 0.2s ease;
}

.dj-play-button.playing .play-halo {
  border-color: var(--c-accent);
  box-shadow: 
    0 0 20px var(--c-accent-glow),
    inset 0 0 10px rgba(29, 185, 84, 0.3);
}

.play-inner {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(180deg, #2b303b 0%, #15171d 100%);
  border: 1px solid #444b59;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.dj-play-button.playing .play-inner {
  background: linear-gradient(180deg, #1db954 0%, #13883c 100%);
  border-color: #1ed760;
  color: #000000;
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.5);
}

.play-icon-offset {
  margin-left: 2px;
}

/* Mixer Strip (Volume Fader & Actions) */
.mixer-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
  background: #0b0c0f;
  border-radius: var(--r-sm);
  border: 1px solid #1c1f27;
}

.fader-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.mute-toggle-btn {
  width: 26px;
  height: 26px;
  border-radius: var(--r-xs);
  border: 1px solid #292d37;
  background: #171920;
  color: var(--c-text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.mute-toggle-btn:hover {
  color: #ffffff;
  border-color: #3f4554;
}

.mute-toggle-btn.muted {
  color: #ff4444;
  border-color: rgba(255, 68, 68, 0.4);
}

.fader-track-container {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
}

.fader-ticks {
  display: flex;
  justify-content: space-between;
  font-size: 7px;
  font-weight: 800;
  color: var(--c-text-4);
  font-family: var(--font-mono, monospace);
  padding: 0 2px;
}

.fader-rail {
  position: relative;
  width: 100%;
  height: 6px;
  background: #16181f;
  border-radius: 2px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
}

.fader-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, #169c46 0%, #1db954 100%);
  pointer-events: none;
}

.fader-cap {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 14px;
  height: 18px;
  background: linear-gradient(180deg, #444a57 0%, #202329 100%);
  border: 1px solid #5a6273;
  border-radius: 2px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.8);
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cap-line {
  width: 10px;
  height: 2px;
  background: var(--c-accent);
}

.fader-native-input {
  position: absolute;
  inset: -6px 0;
  width: 100%;
  height: calc(100% + 12px);
  opacity: 0;
  cursor: pointer;
  z-index: 5;
  margin: 0;
}

.volume-readout {
  font-size: 10px;
  font-weight: 800;
  font-family: var(--font-mono, monospace);
  color: var(--c-text-3);
  min-width: 28px;
  text-align: right;
}

/* Actions Group */
.deck-actions-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dj-action-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--r-xs);
  border: 1px solid #282c36;
  background: #15181f;
  color: var(--c-text-3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.dj-action-btn:hover {
  color: #ffffff;
  border-color: #3e4453;
}

.dj-action-btn.active {
  color: #ff4d6d;
  border-color: rgba(255, 77, 109, 0.4);
  box-shadow: 0 0 8px rgba(255, 77, 109, 0.4);
}

.dj-action-btn.hd-btn {
  color: #ffd700;
}
</style>
