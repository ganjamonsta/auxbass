<template>
  <div 
    class="search-result-item"
    :class="{ 'already-added': isInPlaylist, 'is-playing': isCurrentTrack }"
  >
    <div class="cover-wrapper" @click.stop="togglePlay">
      <div class="cover">
        <img v-if="track.cover_url" :src="track.cover_url" />
        <span v-else>🎵</span>
      </div>
      <div class="play-overlay" :class="{ 'is-playing': isCurrentTrack && playerStore.isPlaying }">
        <svg v-if="isCurrentTrack && playerStore.isPlaying" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z"/>
        </svg>
      </div>
    </div>
    
    <div class="content">
      <div class="info">
        <div class="artist">{{ track.artist }}</div>
        <div class="title">{{ track.title }}</div>
      </div>
      <div v-if="isCurrentTrack" class="progress" @click="seek" @mousedown="startDrag">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        <div class="progress-thumb" :style="{ left: progressPercent + '%' }"></div>
      </div>
    </div>
    
    <div class="time">{{ displayTime }}</div>
    
    <button 
      v-if="!isInPlaylist"
      class="action-btn add"
      @click="$emit('add', track)"
      :disabled="isAdding"
    >
      <span v-if="isAdding">...</span>
      <span v-else>+</span>
    </button>
    <button 
      v-else
      class="action-btn remove"
      @click="$emit('remove', track)"
      :disabled="isRemoving"
    >
      <span v-if="isRemoving">...</span>
      <span v-else>✓</span>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { usePlayerStore } from '@/stores/player'

const props = defineProps({
  track: { type: Object, required: true },
  isInPlaylist: Boolean,
  isAdding: Boolean,
  isRemoving: Boolean
})

defineEmits(['add', 'remove'])

const playerStore = usePlayerStore()

const isCurrentTrack = computed(() => playerStore.currentTrack?.id === props.track.id)
const progressPercent = computed(() => (playerStore.progress / playerStore.duration) * 100 || 0)

const displayTime = computed(() => {
  const seconds = isCurrentTrack.value ? playerStore.progress : props.track.duration
  if (!seconds || isNaN(seconds)) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
})

const togglePlay = () => {
  if (isCurrentTrack.value) {
    playerStore.togglePlay()
  } else {
    playerStore.playTrack(props.track, [props.track])
  }
}

const seek = (event) => {
  if (!isCurrentTrack.value) return
  const rect = event.currentTarget.getBoundingClientRect()
  const percent = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width))
  playerStore.seek(percent * playerStore.duration)
}

let isDragging = false
const startDrag = (event) => {
  if (!isCurrentTrack.value) return
  isDragging = true
  const progressBar = event.currentTarget
  
  const onMouseMove = (e) => {
    if (!isDragging) return
    const rect = progressBar.getBoundingClientRect()
    const percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
    playerStore.seek(percent * playerStore.duration)
  }
  
  const onMouseUp = () => {
    isDragging = false
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
  
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}
</script>

<style scoped>
.search-result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 8px;
  transition: background 0.2s;
}

.search-result-item:hover { background: var(--bg-elevated); }
.search-result-item.already-added { opacity: 0.6; }
.search-result-item.is-playing { background: rgba(29, 185, 84, 0.1); }

.cover-wrapper {
  position: relative;
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  cursor: pointer;
  border-radius: 6px;
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
  transition: filter 0.2s;
}

.cover-wrapper:hover .cover img { filter: brightness(0.6); }

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

.content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info { display: flex; flex-direction: column; gap: 2px; }

.title {
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
}

.artist {
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
  font-size: 13px;
  color: var(--text-tertiary);
  font-variant-numeric: tabular-nums;
  min-width: 40px;
  text-align: right;
}

.is-playing .time { color: var(--accent); }

.action-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--accent);
  border: none;
  color: #000;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.action-btn:hover { transform: scale(1.1); }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.action-btn.remove:hover { background: var(--danger, #e53935); color: #fff; }
</style>
