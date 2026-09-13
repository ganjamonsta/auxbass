<template>
  <div class="artists-results-mode">
    <div class="section-header">
      <span class="section-title">
        <Users :size="18" /> Артисты
      </span>
      <span class="section-count">{{ artistsResults.length }}</span>
    </div>
    <div v-if="artistsResults.length > 0" class="artists-grid">
      <div 
        v-for="artist in artistsResults" 
        :key="artist.name || artist.artist"
        class="feed-card artist-card"
        @click="$emit('goToArtist', artist.name || artist.artist)"
      >
        <div class="feed-card-cover artist-cover" :style="getArtistCoverStyle(artist)">
          <img 
            v-if="artist.image_url" 
            :src="getCoverUrl(artist.image_url, CoverSize.MEDIUM)" 
            alt="" 
            loading="lazy"
          />
          <span v-else class="artist-initials">
            {{ getArtistInitials(artist) }}
          </span>
        </div>
        <div class="feed-card-title">{{ artist.name || artist.artist }}</div>
        <div class="feed-card-subtitle">
          <template v-if="artist.track_count">{{ artist.track_count }} {{ formatTrackCount(artist.track_count) }}</template>
          <template v-else>Исполнитель</template>
        </div>
        <div v-if="artist.tags?.length" class="card-tags center">
          <span v-for="t in artist.tags.slice(0, 2)" :key="t" class="card-tag">#{{ t }}</span>
        </div>
      </div>
    </div>
    <NoResultsBox v-else-if="!isArtistsSearching" text="Артисты не найдены" hint="Попробуйте изменить поисковый запрос" />
  </div>
</template>

<script setup>
import { Users } from 'lucide-vue-next'
import NoResultsBox from '@/components/NoResultsBox.vue'
import { getCoverUrl, CoverSize } from '@/utils'

const props = defineProps({
  artistsResults: { type: Array, required: true },
  isArtistsSearching: { type: Boolean, required: true }
})

const emit = defineEmits(['goToArtist'])

const formatTrackCount = (count) => {
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod100 >= 11 && mod100 <= 19) return 'треков'
  if (mod10 === 1) return 'трек'
  if (mod10 >= 2 && mod10 <= 4) return 'трека'
  return 'треков'
}

const getArtistInitials = (artist) => {
  const name = artist?.name || artist?.artist || ''
  return name.slice(0, 2).toUpperCase() || '♪'
}

const getArtistCoverStyle = (artist) => {
  const str = artist?.name || artist?.artist || 'Artist'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash % 360)
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 50%, 30%) 0%, hsl(${(hue + 50) % 360}, 40%, 20%) 100%)`
  }
}
</script>
