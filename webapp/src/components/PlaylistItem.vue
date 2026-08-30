<template>
  <div class="playlist-card" @click="$emit('click')">
    <div class="playlist-cover" :class="coverClass">
      <!-- Collage from track covers (using covers array from API) -->
      <div v-if="displayCovers.length > 0" class="cover-collage" :class="'collage-' + displayCovers.length">
        <img v-for="(cover, i) in displayCovers" :key="`${i}-${cover}`" :src="getCoverUrl(cover, CoverSize.SMALL)" alt="" class="collage-img" />
      </div>
      
      <!-- Fallback icon -->
      <component v-else :is="coverIcon" :size="32" class="cover-icon" />
      
    </div>
    <div class="playlist-name">{{ playlist.name }}</div>
    <div class="playlist-meta">{{ playlist.track_count }} треков</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Bot, Megaphone, User, Folder, Disc3 } from 'lucide-vue-next'
import { getCoverUrl, CoverSize } from '@/utils'

const props = defineProps({
  playlist: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click'])

// Get up to 4 unique covers for collage from API covers array or fallback to track_covers
const displayCovers = computed(() => {
  // Use covers array from API (already limited to 4)
  if (props.playlist.covers?.length) return props.playlist.covers
  // Fallback to track_covers if available
  if (props.playlist.track_covers?.length) return props.playlist.track_covers.slice(0, 4)
  return []
})

const coverClass = computed(() => ({
  'has-image': displayCovers.value.length > 0
}))

const coverIcon = computed(() => Folder)
</script>

<style scoped>
.playlist-card {
  display: flex;
  flex-direction: column;
  width: 100px;
  flex-shrink: 0;
  cursor: pointer;
  transition: transform 0.15s ease;
}

.playlist-card:active {
  transform: scale(0.96);
}

.playlist-cover {
  width: 100px;
  height: 100px;
  border-radius: var(--r-md);
  background: var(--c-bg-2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  position: relative;
  box-shadow: 
    6px 6px 12px var(--sh-dark)),
    -3px -3px 6px var(--sh-light));
  transition: box-shadow 0.15s ease;
}

.playlist-card:active .playlist-cover {
  box-shadow: 
    inset 3px 3px 6px var(--sh-inset-dark)),
    inset -2px -2px 4px var(--sh-inset-light));
}

.playlist-cover.has-image {
  background: transparent;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-icon {
  font-size: 32px;
}

/* Cover collage grid */
.cover-collage {
  display: grid;
  width: 100%;
  height: 100%;
  gap: 1px;
}

.cover-collage.collage-1 {
  grid-template-columns: 1fr;
}

.cover-collage.collage-2 {
  grid-template-columns: 1fr 1fr;
}

.cover-collage.collage-3 {
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
}

.cover-collage.collage-3 .collage-img:first-child {
  grid-row: span 2;
}

.cover-collage.collage-4 {
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
}

.collage-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}



.playlist-name {
  font-size: 12px;
  font-weight: 600;
  margin-top: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--c-text-1);
}

.playlist-meta {
  font-size: 11px;
  color: var(--c-text-3);
  white-space: nowrap;
}
</style>
