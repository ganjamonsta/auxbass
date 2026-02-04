<template>
  <div class="library-albums">
    <!-- Sort options (Stats + SortChips) -->
    <div class="sort-options">
      <div class="stats">
        {{ virtualGridRef?.total?.value ?? 0 }} альбомов
      </div>
      <SortChips
        :currentOption="currentOption"
        :sortOrder="sortOrder"
        @next="onNextSort"
        @toggle-order="onToggleOrder"
      />
    </div>

    <!-- Spotify-style virtual grid -->
    <VirtualGrid
      ref="virtualGridRef"
      type="album"
      :fetchFn="fetchAlbums"
      :pageSize="30"
      :skeletonCount="12"
      @click="goToAlbum"
      @play="playAlbum"
      @contextmenu="handleContextMenu"
    >
      <template #empty>
        <span class="empty-icon"><Disc3 :size="48" /></span>
        <h3 v-if="searchQuery">Ничего не найдено</h3>
        <p v-else>В библиотеке нет альбомов</p>
      </template>
    </VirtualGrid>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useSort } from '@/composables'
import { useContextMenu } from '@/composables/useContextMenu'
import SortChips from '@/components/SortChips.vue'
import VirtualGrid from '@/components/VirtualGrid.vue'
import api from '@/api/client'
import { Disc3 } from 'lucide-vue-next'

// Universal context menu
const { openMenu } = useContextMenu()

const props = defineProps({
  searchQuery: {
    type: String,
    default: ''
  }
})

const router = useRouter()
const playerStore = usePlayerStore()
const virtualGridRef = ref(null)

// Sort state (persisted to localStorage)
const { 
  sortBy, 
  sortOrder, 
  currentOption, 
  nextSort, 
  toggleOrder 
} = useSort('library-albums-sort', 'albums', { sortBy: 'release_date', sortOrder: 'desc' })

// Fetch function for virtual grid
const fetchAlbums = async ({ offset, limit }) => {
  const params = { 
    offset, 
    limit,
    sort_by: sortBy.value,
    sort_order: sortOrder.value
  }
  if (props.searchQuery) {
    params.search = props.searchQuery
  }
  const response = await api.get('/albums', { params })
  return response.data
}

// Sort handlers
const onNextSort = () => {
  nextSort()
  virtualGridRef.value?.reset()
}

const onToggleOrder = () => {
  toggleOrder()
  virtualGridRef.value?.reset()
}

// Watch search query to reload
watch(() => props.searchQuery, () => {
  virtualGridRef.value?.reset()
})

// Navigation
const goToAlbum = (album) => {
  router.push(`/album/${album.id}`)
}

// Play album
const playAlbum = async (album) => {
  try {
    const response = await api.get(`/albums/${album.id}`)
    if (response.data.tracks?.length) {
      playerStore.playTrack(response.data.tracks[0], response.data.tracks)
    }
  } catch (error) {
    console.error('Failed to load album:', error)
  }
}

// Context menu
const handleContextMenu = ({ item, event }) => {
  openMenu('album', item, 'library', event)
}

// Expose for parent
defineExpose({
  reset: () => virtualGridRef.value?.reset(),
  refresh: () => virtualGridRef.value?.reset()
})
</script>

<style scoped>
.library-albums {
  padding-bottom: 20px;
}

.sort-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 12px;
}

.stats {
  color: var(--text-secondary);
  font-size: 14px;
}
</style>
