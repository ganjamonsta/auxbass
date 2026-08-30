<template>
  <div class="album-card" @click="$emit('click', album)" @contextmenu.prevent="$emit('contextmenu', $event)">
    <div class="album-cover">
      <img v-if="album.cover_url" :src="getCoverUrl(album.cover_url, CoverSize.MEDIUM)" :alt="album.name" loading="lazy" />
      <div v-else class="cover-placeholder"><Disc3 :size="32" /></div>
      <button class="play-btn" @click.stop="$emit('play', album)"><Play :size="20" fill="currentColor" /></button>
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
import { Disc3, Play } from 'lucide-vue-next'
import { getCoverUrl, CoverSize } from '@/utils'

defineProps({
  album: {
    type: Object,
    required: true
  }
})

defineEmits(['click', 'play', 'contextmenu'])
</script>

<style scoped>
.album-card {
  cursor: pointer;
  transition: transform 0.2s;
  min-width: 0;
}

.album-card:active {
  transform: scale(0.98);
}

.album-cover {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: var(--c-bg-3);
  margin-bottom: 8px;
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
  right: 8px;
  bottom: 8px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--c-accent);
  border: none;
  color: #000;
  font-size: 14px;
  cursor: pointer;
  opacity: 0;
  transform: translateY(8px);
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.album-card:hover .play-btn {
  opacity: 1;
  transform: translateY(0);
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.album-artist {
  font-size: 11px;
  color: var(--c-text-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.track-count {
  font-size: 11px;
  color: var(--c-text-3);
}
</style>
