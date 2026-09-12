<template>
  <div class="library-artists">
    <!-- Info banner for global scope -->
    <InfoBanner
      v-if="scope === 'global'"
      :icon="User"
      title="Общая коллекция артистов"
      description="Все артисты, доступные в системе"
    />

    <!-- Unified Toolbar: Back button + Title + Controls + Expandable Search -->
    <div class="library-toolbar" :class="{ 'search-active': isSearchOpen }">
      <!-- Left side: Back button and Section Title (hidden when search is open) -->
      <div v-if="!isSearchOpen" class="toolbar-left">
        <button 
          v-if="showBack" 
          type="button"
          class="subtab-back-btn" 
          @click="$emit('back')"
          title="Все разделы"
        >
          <ChevronLeft :size="18" />
          <span>Все разделы</span>
        </button>
        <h1 class="toolbar-section-title">Исполнители</h1>
      </div>

      <!-- Right side: Controls & Expandable Search (controls pressed up to search) -->
      <div class="toolbar-right">
        <!-- Sort controls (hidden when search is open) -->
        <div v-if="!isSearchOpen" class="toolbar-controls">
          <div class="stats" v-if="virtualGridRef?.total">
            {{ virtualGridRef?.total }}
          </div>
          <SortChips
            :currentOption="currentOption"
            :sortOrder="sortOrder"
            @next="onNextSort"
            @toggle-order="onToggleOrder"
          />
        </div>

        <!-- Expandable Search -->
        <ExpandableSearch
          v-model="localQuery"
          v-model:open="isSearchOpen"
          placeholder="Поиск исполнителей..."
          title="Поиск исполнителей"
          @input="onSearchInput"
          @clear="onSearchClear"
        />
      </div>
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
        <template v-if="searchQuery || localQuery">
          <h3>Артисты не найдены</h3>
          <p class="empty-subtext">По запросу «{{ localQuery || searchQuery }}» среди исполнителей ничего не найдено</p>
          <button 
            type="button" 
            class="btn-global-search" 
            @click="goToGlobalSearch"
          >
            <Search :size="16" />
            <span>Искать в глобальном поиске</span>
          </button>
        </template>
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
import ExpandableSearch from '@/components/ui/ExpandableSearch.vue'
import VirtualGrid from '@/components/VirtualGrid.vue'
import InfoBanner from '@/components/InfoBanner.vue'
import api, { artistsApi } from '@/api/client'
import { User, ChevronLeft, Search } from 'lucide-vue-next'

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
  },
  showBack: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['back', 'update:searchQuery'])

const localQuery = ref(props.searchQuery || '')
const isSearchOpen = ref(Boolean(props.searchQuery?.trim()))

watch(() => props.searchQuery, (val) => {
  localQuery.value = val || ''
  if (val) {
    isSearchOpen.value = true
  }
})

let searchDebounceTimer = null
const onSearchInput = () => {
  clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    emit('update:searchQuery', localQuery.value)
  }, 250)
}

const onSearchClear = () => {
  clearTimeout(searchDebounceTimer)
  localQuery.value = ''
  emit('update:searchQuery', '')
}

const goToGlobalSearch = () => {
  const q = (localQuery.value || props.searchQuery || '').trim()
  if (q) {
    router.push({ path: '/search', query: { q } })
  }
}

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

.library-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 12px;
  min-height: 40px;
}

.library-toolbar.search-active {
  justify-content: stretch;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}

.toolbar-section-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  margin: 0;
  line-height: 1;
  white-space: nowrap;
  letter-spacing: -0.02em;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
  flex-shrink: 0;
}

.library-toolbar.search-active .toolbar-right {
  width: 100%;
  margin-left: 0;
}

.subtab-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  height: 38px;
  padding: 0 14px 0 10px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.75));
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.subtab-back-btn:hover {
  background: rgba(255, 255, 255, 0.14);
  color: var(--c-text-1, #fff);
  transform: translateY(-1px);
}

.subtab-back-btn:active {
  transform: scale(0.96);
}

.toolbar-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: nowrap;
  flex-shrink: 0;
}

@media (max-width: 640px) {
  .subtab-back-btn span {
    display: none;
  }
  .subtab-back-btn {
    width: 38px;
    padding: 0;
    justify-content: center;
  }
  .toolbar-section-title {
    font-size: 16px;
  }
}

.stats {
  color: var(--c-text-2);
  font-size: 14px;
}

@media (max-width: 640px) {
  .subtab-back-btn span {
    display: none;
  }
  .subtab-back-btn {
    width: 38px;
    padding: 0;
    justify-content: center;
  }
  .stats {
    display: none;
  }
}
</style>
