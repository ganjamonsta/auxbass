<template>
  <div class="library-artists">
    <!-- Info banner for global scope -->
    <InfoBanner
      v-if="scope === 'global'"
      :icon="User"
      title="Общая коллекция артистов"
      description="Все артисты, доступные в системе"
    />

    <!-- Sort options (Stats + SortChips) -->
    <div class="sort-options">
      <div class="stats">
        {{ virtualGridRef?.total ?? 0 }} исполнителей
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
        <p v-else>{{ scope === 'global' ? 'Нет артистов в коллекции' : 'Нет исполнителей' }}</p>
      </template>
    </VirtualGrid>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSort } from '@/composables'
import { useContextMenu } from '@/composables/useContextMenu'
import SortChips from '@/components/SortChips.vue'
import VirtualGrid from '@/components/VirtualGrid.vue'
import InfoBanner from '@/components/InfoBanner.vue'
import api, { artistsApi } from '@/api/client'
import { User } from 'lucide-vue-next'

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
const virtualGridRef = ref(null)

// Sort state (persisted to localStorage) - separate key per scope
const sortStorageKey = computed(() => 
  props.scope === 'global' ? 'global-artists-sort' : 'library-artists-sort'
)

const { 
  sortBy, 
  sortOrder, 
  currentOption, 
  nextSort, 
  toggleOrder 
} = useSort(sortStorageKey.value, 'artists', { sortBy: 'name', sortOrder: 'asc' })

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
  
  // Use global or library endpoint based on scope
  const response = props.scope === 'global' 
    ? await artistsApi.getGlobal(params)
    : await artistsApi.getAll(params)
  
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
  const query = props.scope === 'global' ? { scope: 'global' } : {}
  router.push({ 
    path: `/artist/${encodeURIComponent(artist.name)}`,
    query
  })
}

// Context menu
const handleContextMenu = ({ item, event }) => {
  openMenu('artist', item, props.scope, event)
}

// Watch scope changes to reload
watch(() => props.scope, () => {
  virtualGridRef.value?.reset()
})

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
  color: var(--c-text-2);
  font-size: 14px;
}
</style>
