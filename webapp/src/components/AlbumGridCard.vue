<template>
  <div 
    class="album-card" 
    @click="handleClick" 
    @contextmenu.prevent="$emit('contextmenu', $event)"
    @touchstart="handleTouchStart"
    @touchmove="handleTouchMove"
    @touchend="handleTouchEnd"
    @touchcancel="handleTouchEnd"
  >
    <div class="album-cover">
      <img v-if="album.cover_url" :src="getCoverUrl(album.cover_url, CoverSize.MEDIUM)" :alt="album.name" loading="lazy" />
      <div v-else class="cover-placeholder"><Disc3 :size="32" /></div>
      <button 
        class="play-btn" 
        :class="{ 'is-playing': isPlaying }"
        @click.stop="handlePlay"
        :title="isPlaying ? 'Пауза' : 'Слушать'"
      >
        <Pause v-if="isPlaying" :size="20" fill="currentColor" />
        <Play v-else :size="20" fill="currentColor" />
      </button>
      <!-- Progress indicator if we have total_tracks -->
      <div v-if="album.total_tracks && album.track_count < album.total_tracks" class="progress-badge">
        {{ album.track_count }}/{{ album.total_tracks }}
      </div>
    </div>
    <div class="album-info">
      <span class="album-name">{{ album.name }}</span>
      <span class="album-artist">{{ album.artist }}</span>
      <span class="track-count">
        <template v-if="album.total_tracks">
          {{ album.track_count }}/{{ album.total_tracks }} треков
        </template>
        <template v-else>
          {{ album.track_count }} треков
        </template>
      </span>
    </div>
  </div>
</template>

<script setup>
import { Disc3, Play, Pause } from 'lucide-vue-next'
import { getCoverUrl, CoverSize } from '@/utils'
import { usePlayerStore } from '@/stores/player'
import { computed } from 'vue'

const playerStore = usePlayerStore()

const props = defineProps({
  album: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click', 'play', 'contextmenu'])

const isPlaying = computed(() => {
  if (!playerStore.isPlaying) return false
  const albumId = props.album?.id
  if (!albumId) return false
  if (playerStore.currentAlbumId === Number(albumId)) return true
  const ctx = playerStore.playbackContext || playerStore.lazyShuffleContext
  if (ctx?.type === 'album' && String(ctx.id) === String(albumId)) return true
  return false
})

const handlePlay = () => {
  if (isPlaying.value) {
    playerStore.togglePlay()
  } else {
    emit('play', props.album)
  }
}

let longPressTimer = null
let touchMoved = false
let touchStartX = 0
let touchStartY = 0
let isLongPressTriggered = false

const handleTouchStart = (e) => {
  touchMoved = false
  isLongPressTriggered = false
  if (e.touches.length === 1) {
    touchStartX = e.touches[0].clientX
    touchStartY = e.touches[0].clientY
    longPressTimer = setTimeout(() => {
      if (!touchMoved) {
        isLongPressTriggered = true
        emit('contextmenu', e)
      }
    }, 450)
  }
}

const handleTouchMove = (e) => {
  if (e.touches.length === 1) {
    const dx = Math.abs(e.touches[0].clientX - touchStartX)
    const dy = Math.abs(e.touches[0].clientY - touchStartY)
    if (dx > 10 || dy > 10) {
      touchMoved = true
      clearTimeout(longPressTimer)
    }
  }
}

const handleTouchEnd = () => {
  clearTimeout(longPressTimer)
}

const handleClick = (e) => {
  if (isLongPressTriggered) {
    isLongPressTriggered = false
    e?.preventDefault?.()
    e?.stopPropagation?.()
    return
  }
  emit('click', props.album)
}
</script>

<style scoped>
.album-card {
  cursor: pointer;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 8px;
  border-radius: var(--r-lg);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
}

.album-card:hover {
  background: var(--c-bg-2);
  border: var(--border-neu);
  box-shadow: 
    4px 4px 12px var(--sh-dark),
    -2px -2px 6px var(--sh-light);
  transform: translateY(-2px);
}

.album-card:active {
  transform: translateY(0) scale(0.98);
}

.album-cover {
  position: relative;
  aspect-ratio: 1;
  border-radius: var(--r-md);
  overflow: hidden;
  background: var(--c-bg-3);
  margin-bottom: 8px;
  box-shadow: 
    4px 4px 10px var(--sh-dark),
    -2px -2px 5px var(--sh-light);
  border: var(--border-neu);
}

.album-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 40px;
}

.play-btn {
  position: absolute;
  right: 10px;
  bottom: 10px;
  width: 40px;
  height: 40px;
  border-radius: var(--r-full);
  background: linear-gradient(145deg, var(--c-accent-light), var(--c-accent-dark));
  border: none;
  color: #000;
  font-size: 14px;
  cursor: pointer;
  opacity: 0;
  transform: translateY(8px);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  box-shadow: 
    3px 3px 8px rgba(0, 0, 0, 0.6),
    0 0 12px var(--c-accent-glow);
}

.album-card:hover .play-btn,
.play-btn.is-playing {
  opacity: 1;
  transform: translateY(0);
}

.play-btn:hover {
  transform: translateY(0) scale(1.08);
  box-shadow: 
    4px 4px 12px rgba(0, 0, 0, 0.7),
    0 0 18px var(--c-accent-glow);
}

.play-btn:active {
  transform: translateY(0) scale(0.95);
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.6);
}

.play-btn svg.lucide-play {
  margin-left: 2px;
}

/* Hide play button on mobile devices */
@media (max-width: 768px) {
  .play-btn {
    display: none;
  }
}

.progress-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: var(--c-accent);
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 12px;
}

.album-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.album-name {
  font-weight: 600;
  color: var(--c-text-1);
  font-size: 13px;
  line-height: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.album-artist {
  font-size: 11px;
  line-height: 14px;
  color: var(--c-text-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.track-count {
  font-size: 11px;
  line-height: 14px;
  color: var(--c-text-3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
