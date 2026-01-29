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
      <component v-else :is="coverIcon" :size="32" class="cover-icon" />
      
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
import { Bot, Megaphone, User, Folder, Disc3 } from 'lucide-vue-next'

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
    if (type === 'bot') return Bot
    if (type === 'channel') return Megaphone
    if (type === 'user') return User
    return Folder
  }
  if (props.playlist.is_auto_album) return Disc3
  return Folder
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
  border-radius: var(--neu-radius-md, 12px);
  background: var(--xm-bg-elevated, #1A1A1A);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  position: relative;
  box-shadow: 
    6px 6px 12px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -3px -3px 6px var(--neu-shadow-light, rgba(255, 255, 255, 0.03));
  transition: box-shadow 0.15s ease;
}

.playlist-card:active .playlist-cover {
  box-shadow: 
    inset 3px 3px 6px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -2px -2px 4px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
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

/* Artist overlay on album cover */
.artist-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent 0%, rgba(0,0,0,0.9) 100%);
  padding: 18px 6px 6px;
}

.artist-text {
  display: block;
  font-size: 10px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-shadow: 0 1px 3px rgba(0,0,0,0.7);
}

.type-badge {
  position: absolute;
  bottom: 5px;
  right: 5px;
  font-size: 8px;
  padding: 3px 5px;
  border-radius: var(--neu-radius-sm, 8px);
  background: var(--xm-bg-deep, #0D0D0D);
  color: var(--xm-accent, #E53935);
  font-weight: 700;
  text-transform: uppercase;
  box-shadow: 
    2px 2px 4px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -1px -1px 2px var(--neu-shadow-light, rgba(255, 255, 255, 0.03));
}

.playlist-name {
  font-size: 12px;
  font-weight: 600;
  margin-top: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--xm-text-primary, #fff);
}

.playlist-meta {
  font-size: 11px;
  color: var(--xm-text-muted, #888);
  white-space: nowrap;
}
</style>
