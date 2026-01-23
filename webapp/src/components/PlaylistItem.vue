<template>
  <div class="playlist-card" @click="$emit('click')">
    <div class="playlist-cover" :class="coverClass">
      <!-- Single cover image (albums or custom cover) -->
      <img v-if="playlist.cover_url" :src="playlist.cover_url" alt="" class="cover-image" />
      
      <!-- Collage from track covers -->
      <div v-else-if="collageCovers.length > 0" class="cover-collage" :class="'collage-' + collageCovers.length">
        <img v-for="(cover, i) in collageCovers" :key="i" :src="cover" alt="" class="collage-img" />
      </div>
      
      <!-- Fallback icon -->
      <span v-else class="cover-icon">{{ coverIcon }}</span>
      
      <!-- Artist overlay on cover for albums -->
      <div v-if="playlist.album_artist" class="artist-overlay">
        <span class="artist-text">{{ playlist.album_artist }}</span>
      </div>
      <span v-else-if="playlist.is_auto_source" class="type-badge">{{ sourceLabel }}</span>
    </div>
    <div class="playlist-name">{{ playlist.name }}</div>
    <div class="playlist-meta">{{ playlist.track_count }} треков</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  playlist: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click'])

// Get up to 4 unique covers for collage
const collageCovers = computed(() => {
  if (!props.playlist.track_covers) return []
  return props.playlist.track_covers.slice(0, 4)
})

const coverClass = computed(() => ({
  'has-image': props.playlist.cover_url || collageCovers.value.length > 0
}))

const coverIcon = computed(() => {
  if (props.playlist.is_auto_source) {
    const type = props.playlist.source_type
    if (type === 'bot') return '🤖'
    if (type === 'channel') return '📢'
    if (type === 'user') return '👤'
    return '📁'
  }
  if (props.playlist.is_auto_album) return '💿'
  return '📁'
})

const sourceLabel = computed(() => {
  const type = props.playlist.source_type
  if (type === 'bot') return 'Бот'
  if (type === 'channel') return 'Канал'
  if (type === 'user') return 'Юзер'
  return ''
})
</script>

<style scoped>
.playlist-card {
  display: flex;
  flex-direction: column;
  width: 90px;
  flex-shrink: 0;
  cursor: pointer;
}

.playlist-card:active {
  opacity: 0.8;
}

.playlist-cover {
  width: 90px;
  height: 90px;
  border-radius: 6px;
  background: var(--spotify-gray);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  position: relative;
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
  font-size: 28px;
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

/* Artist overlay on album cover */
.artist-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent 0%, rgba(0,0,0,0.85) 100%);
  padding: 16px 4px 4px;
}

.artist-text {
  display: block;
  font-size: 9px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}

.type-badge {
  position: absolute;
  bottom: 4px;
  right: 4px;
  font-size: 8px;
  padding: 2px 4px;
  border-radius: 3px;
  background: rgba(0, 0, 0, 0.7);
  color: #a78bfa;
  font-weight: 600;
  text-transform: uppercase;
}

.playlist-name {
  font-size: 11px;
  font-weight: 500;
  margin-top: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--spotify-text);
}

.playlist-meta {
  font-size: 10px;
  color: var(--spotify-text-muted);
  white-space: nowrap;
}
</style>
