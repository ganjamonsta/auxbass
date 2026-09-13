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
