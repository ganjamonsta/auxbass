<template>
  <div class="albums-results-mode">
    <div class="section-header">
      <span class="section-title">
        <Disc3 :size="18" /> Альбомы
      </span>
      <span class="section-count">{{ albumsResults.length }}</span>
    </div>
    <div v-if="albumsResults.length > 0" class="albums-grid">
      <div 
        v-for="album in albumsResults" 
        :key="album.id"
        class="feed-card"
        @click="$emit('goToAlbum', album.id)"
        @contextmenu.prevent="(e) => $emit('menu', e, 'album', album)"
      >
        <div class="feed-card-cover">
          <img 
            v-if="album.cover_url" 
            :src="getCoverUrl(album.cover_url, CoverSize.MEDIUM)" 
            alt="" 
            loading="lazy"
          />
          <Disc3 v-else :size="32" />
        </div>
        <div class="feed-card-title">{{ album.name }}</div>
        <div class="feed-card-subtitle">{{ album.artist }}</div>
        <div v-if="album.tags?.length" class="card-tags">
          <span v-for="t in album.tags.slice(0, 2)" :key="t" class="card-tag">#{{ t }}</span>
        </div>
      </div>
    </div>
    <NoResultsBox v-else-if="!isAlbumsSearching" text="Альбомы не найдены" hint="Попробуйте изменить поисковый запрос" />
  </div>
</template>

<script setup>
import { Disc3 } from 'lucide-vue-next'
import NoResultsBox from '@/components/NoResultsBox.vue'
import { getCoverUrl, CoverSize } from '@/utils'

const props = defineProps({
  albumsResults: { type: Array, required: true },
  isAlbumsSearching: { type: Boolean, required: true }
})

const emit = defineEmits(['goToAlbum', 'menu'])
</script>

<style scoped>
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  letter-spacing: -0.01em;
}

.section-count {
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-3, rgba(255, 255, 255, 0.45));
}

.albums-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(136px, 1fr));
  gap: 14px;
  margin-top: 8px;
}

@media (min-width: 768px) {
  .albums-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 16px;
  }
}

.albums-grid .feed-card {
  width: 100%;
  flex: initial;
}

.feed-card {
  flex: 0 0 136px;
  width: 136px;
  cursor: pointer;
  user-select: none;
  transition: transform 0.2s ease;
}

@media (min-width: 768px) {
  .feed-card {
    flex: 0 0 156px;
    width: 156px;
  }
}

.feed-card:hover {
  transform: translateY(-2px);
}

.feed-card:active {
  transform: scale(0.97);
}

.feed-card-cover {
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  background: var(--c-bg-2, #181818);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.4);
}

.feed-card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.feed-card:hover .feed-card-cover img {
  transform: scale(1.04);
}

.feed-card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.feed-card-subtitle {
  font-size: 12px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.card-tag {
  font-size: 10px;
  font-weight: 500;
  color: var(--c-accent, #1db954);
  background: rgba(29, 185, 84, 0.12);
  padding: 1px 6px;
  border-radius: 4px;
  white-space: nowrap;
  letter-spacing: 0.2px;
  line-height: 14px;
}
</style>
