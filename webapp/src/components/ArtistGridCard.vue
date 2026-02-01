<template>
  <div class="artist-card" @click="$emit('click', artist)" @contextmenu.prevent="$emit('contextmenu', $event)">
    <div class="artist-image">
      <img v-if="artist.image_url" :src="artist.image_url" :alt="artist.name" loading="lazy" />
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

defineProps({
  artist: {
    type: Object,
    required: true
  }
})

defineEmits(['click', 'contextmenu'])
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
  background: var(--bg-elevated);
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
  color: var(--text-primary);
  font-weight: 600;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 2px;
}

.artist-meta {
  color: var(--text-tertiary);
  font-size: 11px;
  line-height: 1.3;
}
</style>
