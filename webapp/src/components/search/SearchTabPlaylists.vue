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
