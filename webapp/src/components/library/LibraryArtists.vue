<template>
  <div class="library-artists">
    <!-- Sort options (Stats + SortChips) -->
    <div class="sort-options">
      <div class="stats">
        {{ virtualGridRef?.total?.value ?? 0 }} исполнителей
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
      type="artist"
      :fetchFn="fetchArtists"
      :pageSize="30"
      :skeletonCount="12"
      @click="goToArtist"
      @contextmenu="handleContextMenu"
    >
      <template #empty>
        <span class="empty-icon"><User :size="48" /></span>
        <p v-if="searchQuery">Ничего не найдено</p>
        <p v-else>Нет исполнителей</p>
      </template>
    </VirtualGrid>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSort } from '@/composables'
import { useContextMenu } from '@/composables/useContextMenu'
import SortChips from '@/components/SortChips.vue'
import VirtualGrid from '@/components/VirtualGrid.vue'
import api from '@/api/client'
import { User } from 'lucide-vue-next'

// Universal context menu
const { openMenu } = useContextMenu()

const props = defineProps({
  searchQuery: {
    type: String,
    default: ''
  }
})

const router = useRouter()
const virtualGridRef = ref(null)

// Sort state (persisted to localStorage)
const { 
  sortBy, 
  sortOrder, 
  currentOption, 
  nextSort, 
  toggleOrder 
} = useSort('library-artists-sort', 'artists', { sortBy: 'name', sortOrder: 'asc' })

// Fetch function for virtual grid
const fetchArtists = async ({ offset, limit }) => {
  const params = {
    offset,
    limit,
    sort_by: sortBy.value,
    sort_order: sortOrder.value
  }
  
  if (props.searchQuery) {
    params.search = props.searchQuery
  }
  
  const response = await api.get('/artists', { params })
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
const goToArtist = (artist) => {
  router.push(`/artist/${encodeURIComponent(artist.name)}`)
}

// Context menu
const handleContextMenu = ({ item, event }) => {
  openMenu('artist', item, 'library', event)
}

// Expose for parent
defineExpose({
  reset: () => virtualGridRef.value?.reset()
})
</script>

<style scoped>
.library-artists {
  padding-bottom: 20px;
}

.sort-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 12px;
}

.stats {
  color: var(--text-secondary);
  font-size: 14px;
}
</style>
