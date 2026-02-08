<template>
  <div class="library-artists">
    <!-- Info banner for global scope -->
    <div v-if="scope === 'global'" class="info-banner">
      <div class="banner-icon">
        <User :size="20" />
      </div>
      <div class="banner-text">
        <div class="banner-title">Общая коллекция артистов</div>
        <div class="banner-description">Все артисты, доступные в системе</div>
      </div>
    </div>

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

/* Info banner for global scope */
.info-banner {
  display: flex;
  align-items: start;
  gap: 12px;
  padding: 16px;
  background: var(--c-bg-2);
  border-radius: 12px;
  margin-bottom: 16px;
  border: 1px solid var(--c-bg-3);
}

.banner-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  color: #000;
  border-radius: 10px;
}

.banner-text {
  flex: 1;
}

.banner-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text-1);
  margin-bottom: 4px;
}

.banner-description {
  font-size: 13px;
  color: var(--c-text-2);
  line-height: 1.4;
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
