<template>
  <div class="library-albums">
    <!-- Info banner for global scope -->
    <InfoBanner
      v-if="scope === 'global'"
      :icon="Disc3"
      title="Общая коллекция альбомов"
      description="Все альбомы, доступные в системе"
    />

    <!-- Sort options (Stats + SortChips) -->
    <div class="sort-options">
      <div class="stats">
        {{ virtualGridRef?.total ?? 0 }} альбомов
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
        <p v-else>{{ scope === 'global' ? 'Нет альбомов в коллекции' : 'В библиотеке нет альбомов' }}</p>
      </template>
    </VirtualGrid>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useSort } from '@/composables'
import { useContextMenu } from '@/composables/useContextMenu'
import SortChips from '@/components/SortChips.vue'
import VirtualGrid from '@/components/VirtualGrid.vue'
import InfoBanner from '@/components/InfoBanner.vue'
import api from '@/api/client'
import { Disc3 } from 'lucide-vue-next'

// Universal context menu
const { openMenu } = useContextMenu()

const props = defineProps({
  searchQuery: {
    type: String,
    default: ''
  },
  scope: {
    type: String,
    default: 'library',
    validator: v => ['library', 'global'].includes(v)
  }
})

const router = useRouter()
const playerStore = usePlayerStore()
const virtualGridRef = ref(null)

// Sort state (persisted to localStorage) - separate key per scope
const sortStorageKey = computed(() => 
  props.scope === 'global' ? 'global-albums-sort' : 'library-albums-sort'
)

const { 
  sortBy, 
  sortOrder, 
  currentOption, 
  nextSort, 
  toggleOrder 
} = useSort(sortStorageKey.value, 'albums', { sortBy: 'release_date', sortOrder: 'desc' })

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
  // For global scope, require at least 1 track
  if (props.scope === 'global') {
    params.min_tracks = 1
  }
  const endpoint = props.scope === 'global' ? '/albums/global' : '/albums'
  const response = await api.get(endpoint, { params })
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
  const query = props.scope === 'global' ? { scope: 'global' } : {}
  router.push({ 
    path: `/album/${album.id}`,
    query
  })
}

// Play album
const playAlbum = async (album) => {
  try {
    const params = props.scope === 'global' ? { scope: 'global' } : {}
    const response = await api.get(`/albums/${album.id}`, { params })
    const albumData = response.data
    
    // Get playable tracks - from full_tracklist or tracks array
    let tracks = []
    if (albumData.full_tracklist?.length) {
      tracks = albumData.full_tracklist
        .filter(item => item.track)
        .map(item => item.track)
    } else if (albumData.tracks?.length) {
      tracks = albumData.tracks
    }
    
    if (tracks.length) {
      playerStore.playTrack(tracks[0], tracks)
    }
  } catch (error) {
    console.error('Failed to load album:', error)
  }
}

// Context menu
const handleContextMenu = ({ item, event }) => {
  openMenu('album', item, props.scope, event)
}

// Watch scope changes to reload
watch(() => props.scope, () => {
  virtualGridRef.value?.reset()
})

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
  color: var(--c-text-2);
  font-size: 14px;
}
</style>
