<template>
  <div class="playlists-results-mode">
    <div class="section-header">
      <span class="section-title">
        <Folder :size="18" /> Плейлисты
      </span>
      <span class="section-count">{{ playlistsResults.length }}</span>
    </div>
    <div v-if="playlistsResults.length > 0" class="playlists-grid">
      <div 
        v-for="pl in playlistsResults" 
        :key="pl.id"
        class="feed-card"
        @click="$emit('goToPlaylist', pl.id)"
        @contextmenu.prevent="(e) => $emit('menu', e, 'playlist', pl)"
      >
        <div class="feed-card-cover" :style="getPlaylistCoverStyle(pl)">
          <img 
            v-if="pl.covers?.length" 
            :src="getCoverUrl(pl.covers[0], CoverSize.MEDIUM)" 
            alt=""
            loading="lazy"
          />
          <Music v-else :size="32" />
        </div>
        <div class="feed-card-title">{{ pl.name }}</div>
        <div class="feed-card-subtitle">{{ pl.track_count || 0 }} {{ formatTrackCount(pl.track_count || 0) }}</div>
        <div v-if="pl.tags?.length" class="card-tags">
          <span v-for="t in pl.tags.slice(0, 2)" :key="t" class="card-tag">#{{ t }}</span>
        </div>
      </div>
    </div>
    <NoResultsBox v-else-if="!isPlaylistsSearching" text="Плейлисты не найдены" hint="Попробуйте изменить поисковый запрос" />
  </div>
</template>

<script setup>
import { Folder, Music } from 'lucide-vue-next'
import NoResultsBox from '@/components/NoResultsBox.vue'
import { getCoverUrl, CoverSize } from '@/utils'

const props = defineProps({
  playlistsResults: { type: Array, required: true },
  isPlaylistsSearching: { type: Boolean, required: true }
})

const emit = defineEmits(['goToPlaylist', 'menu'])

const formatTrackCount = (count) => {
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod100 >= 11 && mod100 <= 19) return 'треков'
  if (mod10 === 1) return 'трек'
  if (mod10 >= 2 && mod10 <= 4) return 'трека'
  return 'треков'
}

const getPlaylistCoverStyle = (playlist) => {
  if (playlist.covers?.length) return {}
  const str = playlist.name || 'Playlist'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash % 360)
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 55%, 35%) 0%, hsl(${(hue + 40) % 360}, 45%, 25%) 100%)`
  }
}
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

.playlists-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--card-min-width, 136px), 1fr));
  gap: 14px;
  margin-top: 8px;
}

@media (min-width: 768px) {
  .playlists-grid {
    gap: 16px;
  }
}

.playlists-grid .feed-card {
  width: 100%;
  flex: initial;
}

.feed-card {
  flex: 0 0 var(--card-min-width, 136px);
  width: var(--card-min-width, 136px);
  cursor: pointer;
  user-select: none;
  transition: transform 0.2s ease;
}

@media (min-width: 768px) {
  .feed-card {
    flex: 0 0 var(--card-min-width, 156px);
    width: var(--card-min-width, 156px);
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
