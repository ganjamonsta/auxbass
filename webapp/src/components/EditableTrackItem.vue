<template>
  <div 
    class="editable-track"
    :class="{ 'is-dragging': isDragging, 'drag-over': isDragOver, 'is-playing': isCurrentTrack }"
    draggable="true"
    @dragstart="$emit('dragstart', $event)"
    @dragend="$emit('dragend')"
    @dragover.prevent="$emit('dragover', $event)"
    @drop="$emit('drop', $event)"
  >
    <div class="drag-handle">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M3 15h18v-2H3v2zm0 4h18v-2H3v2zm0-8h18V9H3v2zm0-6v2h18V5H3z"/>
      </svg>
    </div>
    
    <div class="track-number">{{ index + 1 }}</div>
    
    <div class="cover-wrapper" @click.stop="togglePlay">
      <div class="cover">
        <img v-if="track.cover_url" :src="track.cover_url" />
        <span v-else>🎵</span>
      </div>
      <div class="play-overlay" :class="{ 'is-playing': isCurrentTrack && playerStore.isPlaying }">
        <svg v-if="isCurrentTrack && playerStore.isPlaying" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
        </svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z"/>
        </svg>
      </div>
    </div>
    
    <div class="track-info">
      <div class="track-title">{{ track.title }}</div>
      <div class="track-artist">{{ track.artist }}</div>
      <div v-if="isCurrentTrack" class="progress" @click="seek" @mousedown="startDrag">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        <div class="progress-thumb" :style="{ left: progressPercent + '%' }"></div>
      </div>
    </div>
    
    <div class="time" v-if="isCurrentTrack">{{ displayTime }}</div>
    
    <button class="remove-btn" @click="$emit('remove')" title="Удалить">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { usePlayerStore } from '@/stores/player'

const props = defineProps({
  track: { type: Object, required: true },
  index: { type: Number, required: true },
  isDragging: Boolean,
  isDragOver: Boolean,
  allTracks: { type: Array, default: () => [] }
})

defineEmits(['dragstart', 'dragend', 'dragover', 'drop', 'remove'])

const playerStore = usePlayerStore()
const isCurrentTrack = computed(() => playerStore.currentTrack?.id === props.track.id)
const progressPercent = computed(() => (playerStore.progress / playerStore.duration) * 100 || 0)

const displayTime = computed(() => {
  const seconds = playerStore.progress
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
})

const togglePlay = () => {
  if (isCurrentTrack.value) {
    playerStore.togglePlay()
  } else {
    playerStore.playTrack(props.track, props.allTracks.length ? props.allTracks : [props.track])
  }
}

const seek = (event) => {
  if (!isCurrentTrack.value) return
  const rect = event.currentTarget.getBoundingClientRect()
  const percent = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width))
  playerStore.seek(percent * playerStore.duration)
}

let isDraggingProgress = false
const startDrag = (event) => {
  if (!isCurrentTrack.value) return
  isDraggingProgress = true
  const progressBar = event.currentTarget
  
  const onMouseMove = (e) => {
    if (!isDraggingProgress) return
    const rect = progressBar.getBoundingClientRect()
    const percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
    playerStore.seek(percent * playerStore.duration)
  }
  
  const onMouseUp = () => {
    isDraggingProgress = false
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
  
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}
</script>

<style scoped>
.editable-track {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.15s;
  background: transparent;
  position: relative;
}

.editable-track:hover { background: var(--bg-elevated); }
.editable-track.is-dragging { opacity: 0.5; transform: scale(0.98); }
.editable-track.drag-over { background: var(--bg-highlight); }
.editable-track.is-playing { background: rgba(29, 185, 84, 0.1); }

.editable-track.drag-over::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent);
}

.drag-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 32px;
  cursor: grab;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.drag-handle:active { cursor: grabbing; }

.track-number {
  width: 20px;
  text-align: center;
  font-size: 12px;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.cover-wrapper {
  position: relative;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  cursor: pointer;
  border-radius: 4px;
  overflow: hidden;
}

.cover {
  width: 100%;
  height: 100%;
  background: var(--bg-highlight);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.play-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  opacity: 0;
  transition: opacity 0.2s;
  color: #fff;
}

.cover-wrapper:hover .play-overlay { opacity: 1; }
.play-overlay.is-playing { opacity: 1; background: rgba(0, 0, 0, 0.3); }

.track-info {
  flex: 1;
  min-width: 0;
}

.track-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-artist {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.progress {
  position: relative;
  width: 100%;
  height: 12px;
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 0;
  margin-top: 4px;
}

.progress::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
}

.progress-fill {
  position: absolute;
  left: 0;
  height: 3px;
  background: var(--accent);
  border-radius: 2px;
  pointer-events: none;
}

.progress-thumb {
  position: absolute;
  width: 10px;
  height: 10px;
  background: var(--accent);
  border-radius: 50%;
  transform: translateX(-50%);
  opacity: 0;
  pointer-events: none;
}

.progress:hover .progress-thumb { opacity: 1; }

.time {
  font-size: 12px;
  color: var(--accent);
  font-variant-numeric: tabular-nums;
  min-width: 36px;
  text-align: right;
  flex-shrink: 0;
}

.remove-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  opacity: 0;
  transition: all 0.2s;
}

.editable-track:hover .remove-btn { opacity: 1; }
.remove-btn:hover { background: var(--danger, #e53935); color: #fff; }
</style>
