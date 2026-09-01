<template>
  <div 
    class="artist-card" 
    @click="handleClick" 
    @contextmenu.prevent="$emit('contextmenu', $event)"
    @touchstart="handleTouchStart"
    @touchmove="handleTouchMove"
    @touchend="handleTouchEnd"
    @touchcancel="handleTouchEnd"
  >
    <div class="artist-image">
      <img v-if="artist.image_url" :src="getCoverUrl(artist.image_url, CoverSize.MEDIUM)" :alt="artist.name" loading="lazy" />
      <div v-else class="image-placeholder"><User :size="32" /></div>
    </div>
    <div class="artist-name">{{ artist.name }}</div>
    <div class="artist-meta">
      {{ artist.track_count }} треков • {{ artist.album_count }} альбомов
    </div>
  </div>
</template>

<script setup>
import { User } from 'lucide-vue-next'
import { getCoverUrl, CoverSize } from '@/utils'

const props = defineProps({
  artist: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click', 'contextmenu'])

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
  emit('click', props.artist)
}
</script>

<style scoped>
.artist-card {
  text-align: center;
  cursor: pointer;
  min-width: 0;
}

.artist-image {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 50%;
  overflow: hidden;
  background: var(--c-bg-3);
  margin-bottom: 8px;
}

.artist-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 40px;
}

.artist-name {
  color: var(--c-text-1);
  font-weight: 600;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 2px;
}

.artist-meta {
  color: var(--c-text-3);
  font-size: 11px;
  line-height: 1.3;
}
</style>
