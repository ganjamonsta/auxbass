<template>
  <div class="library-view">
    <!-- No channel - show setup prompt -->
    <div v-if="!authStore.hasChannel" class="no-channel-prompt">
      <div class="prompt-icon">📚</div>
      <h2>Ваша библиотека</h2>
      <p>Подключите Telegram-канал, чтобы сохранять треки и создавать свою коллекцию музыки</p>
      <button class="setup-btn" @click="goToChannelSetup">
        Подключить канал
      </button>
    </div>

    <!-- Has channel - show library -->
    <template v-else>
      <!-- Type Switcher (Tabs) - Neumorphic style -->
      <div class="neu-tab-bar library-tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          class="neu-tab"
          :class="{ active: currentTabId === tab.id }"
          @click="currentTabId = tab.id"
        >
          <span class="neu-tab-content" :data-text="tab.label">{{ tab.label }}</span>
        </button>
      </div>

      <!-- Search bar -->
      <div class="search-section">
        <SearchBar 
          v-model="searchQuery"
          :placeholder="searchPlaceholder"
          @input="debouncedSearch"
          @clear="handleClearSearch"
        />
      </div>

      <!-- Dynamic Content Window -->
      <div class="library-content">
        <component 
          :is="currentTabComponent" 
          :searchQuery="debouncedQuery"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, onActivated } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { useDebouncedSearch } from '@/composables'
import LibraryTracks from '@/components/library/LibraryTracks.vue'
import LibraryAlbums from '@/components/library/LibraryAlbums.vue'
import LibraryArtists from '@/components/library/LibraryArtists.vue'
import LibraryPlaylists from '@/components/library/LibraryPlaylists.vue'
import SearchBar from '@/components/ui/SearchBar.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const uiStore = useUIStore()

const goToChannelSetup = () => {
  router.push('/settings#channel')
}

const tabs = [
  { id: 'tracks', label: 'Треки', component: LibraryTracks, placeholder: 'Название или исполнитель...' },
  { id: 'albums', label: 'Альбомы', component: LibraryAlbums, placeholder: 'Поиск альбомов...' },
  { id: 'artists', label: 'Артисты', component: LibraryArtists, placeholder: 'Поиск исполнителей...' },
  { id: 'playlists', label: 'Плейлисты', component: LibraryPlaylists, placeholder: 'Поиск плейлистов...' },
]

// Use centralized tab state from uiStore
const currentTabId = computed({
  get: () => uiStore.libraryTab,
  set: (val) => uiStore.setLibraryTab(val)
})

const currentTab = computed(() => tabs.find(t => t.id === currentTabId.value) || tabs[0])
const currentTabComponent = computed(() => currentTab.value.component)
const searchPlaceholder = computed(() => currentTab.value.placeholder)

// Debounced search using composable
const { query: searchQuery, debouncedQuery, search: debouncedSearch, clear: clearSearch, setQuery } = useDebouncedSearch()

// Sync search query from route or external trigger
const applyRouteSearch = (queryOverride) => {
  const queryParam = queryOverride || route.query.search || route.query.q
  if (queryParam && typeof queryParam === 'string') {
    uiStore.setLibraryTab('tracks')
    setQuery(queryParam, true)
  }
}

const handleAppSearch = (event) => {
  const query = event.detail?.query
  if (query) {
    uiStore.setLibraryTab('tracks')
    setQuery(query, true)
  }
}

const handleClearSearch = () => {
  clearSearch()
  if (route.query.search || route.query.q) {
    router.replace({ path: '/', query: {} })
  }
}

// Watch route search query param changes
watch(
  () => route.query.search || route.query.q,
  (newVal) => {
    if (newVal && typeof newVal === 'string') {
      if (searchQuery.value !== newVal) {
        uiStore.setLibraryTab('tracks')
        setQuery(newVal, true)
      }
    }
  }
)

// Слушаем событие сброса состояния
const handleResetState = (event) => {
  if (event.detail.route === '/') {
    // Сбрасываем поиск
    handleClearSearch()
    // Сбрасываем на первую вкладку (Треки)
    currentTabId.value = 'tracks'
  }
}

onMounted(() => {
  applyRouteSearch()
  window.addEventListener('reset-view-state', handleResetState)
  window.addEventListener('app-search', handleAppSearch)
})

onActivated(() => {
  applyRouteSearch()
})

onUnmounted(() => {
  window.removeEventListener('reset-view-state', handleResetState)
  window.removeEventListener('app-search', handleAppSearch)
})

</script>

<style scoped>
.library-view {
  padding: 16px;
  /* No padding-bottom needed - handled by App.vue layout */
}

.search-section {
  margin-bottom: 16px;
}

/* Tabs Styles - use design system */
.library-tabs {
  margin-bottom: 20px;
  display: none; /* Hide on mobile, tabs are in PageHeader */
}

/* Show library-tabs only on desktop */
@media (min-width: 1024px) {
  .library-tabs {
    display: flex;
  }
}

/* Override base .neu-tab-bar for this specific use case */
.library-tabs.neu-tab-bar {
  padding: 4px;
}

/* No channel prompt */
.no-channel-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  padding: 32px 24px;
}

.no-channel-prompt .prompt-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.no-channel-prompt h2 {
  color: var(--c-text-1);
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 12px 0;
}

.no-channel-prompt p {
  color: var(--c-text-2);
  font-size: 15px;
  line-height: 1.5;
  margin: 0 0 24px 0;
  max-width: 300px;
}

.no-channel-prompt .setup-btn {
  background: linear-gradient(135deg, var(--c-accent) 0%, #00c853 100%);
  border: none;
  border-radius: 24px;
  color: #000;
  font-size: 16px;
  font-weight: 600;
  padding: 14px 32px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.no-channel-prompt .setup-btn:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 16px rgba(0, 230, 118, 0.3);
}

/* Make it look more "Apple Music" or "Spotify" style: 
   or the "Albums Design" as presumably requested (usually simple text or pill).
   I went with Pill style for clear indication. */

</style>

