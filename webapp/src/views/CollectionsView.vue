<template>
  <div class="collections-view">
    <!-- Type Switcher (Tabs) - Desktop Only -->
    <div class="neu-tab-bar collections-tabs">
      <button 
        class="neu-tab"
        :class="{ active: activeTab === 'albums' }"
        @click="setActiveTab('albums')"
      >
        <span class="neu-tab-content" data-text="Альбомы">Альбомы</span>
      </button>
      <button 
        class="neu-tab"
        :class="{ active: activeTab === 'playlists' }"
        @click="setActiveTab('playlists')"
      >
        <span class="neu-tab-content" data-text="Плейлисты">Плейлисты</span>
      </button>
    </div>

    <!-- Albums Tab - using unified component -->
    <div v-show="activeTab === 'albums'" class="tab-content">
      <SearchBar
        v-model="albumSearchQuery"
        placeholder="Поиск альбомов..."
        @input="debouncedAlbumSearch"
      />

      <LibraryAlbums
        ref="albumsRef"
        scope="global"
        :searchQuery="debouncedAlbumQuery"
      />
    </div>

    <!-- Playlists Tab - using unified component -->
    <div v-show="activeTab === 'playlists'" class="tab-content">
      <SearchBar
        v-model="playlistSearchQuery"
        placeholder="Поиск плейлистов..."
        @input="debouncedPlaylistSearch"
      />

      <LibraryPlaylists
        ref="playlistsRef"
        scope="global"
        :searchQuery="debouncedPlaylistQuery"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useUIStore } from '@/stores/ui'
import { useDebouncedSearch } from '@/composables'
import SearchBar from '@/components/ui/SearchBar.vue'
import LibraryAlbums from '@/components/library/LibraryAlbums.vue'
import LibraryPlaylists from '@/components/library/LibraryPlaylists.vue'

const uiStore = useUIStore()

// Tab state from uiStore
const activeTab = computed(() => uiStore.collectionsTab)

const setActiveTab = (tab) => {
  uiStore.setCollectionsTab(tab)
}

// Refs to child components
const albumsRef = ref(null)
const playlistsRef = ref(null)

// Album search with debounce
const { 
  query: albumSearchQuery, 
  debouncedQuery: debouncedAlbumQuery, 
  search: debouncedAlbumSearch,
  clear: clearAlbumSearch 
} = useDebouncedSearch()

// Playlist search with debounce
const { 
  query: playlistSearchQuery, 
  debouncedQuery: debouncedPlaylistQuery, 
  search: debouncedPlaylistSearch,
  clear: clearPlaylistSearch 
} = useDebouncedSearch()

// Handle reset state event
const handleResetState = (event) => {
  if (event.detail.route === '/collections') {
    if (activeTab.value === 'albums') {
      clearAlbumSearch()
      albumsRef.value?.reset()
    } else if (activeTab.value === 'playlists') {
      clearPlaylistSearch()
      playlistsRef.value?.reset()
    }
  }
}

onMounted(() => {
  window.addEventListener('reset-view-state', handleResetState)
})

onUnmounted(() => {
  window.removeEventListener('reset-view-state', handleResetState)
})
</script>

<style scoped>
.collections-view {
  padding: 8px 16px 16px 16px;
}

/* Tabs Styles - use design system */
.collections-tabs {
  margin-bottom: 20px;
  display: none; /* Hide on mobile, tabs are in PageHeader */
}

/* Show collections-tabs only on desktop */
@media (min-width: 1024px) {
  .collections-tabs {
    display: flex;
  }
}

/* Override base .neu-tab-bar for this specific use case */
.collections-tabs.neu-tab-bar {
  padding: 4px;
}
</style>
