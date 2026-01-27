<template>
  <div class="library-view">
    <!-- Search bar -->
    <div class="search-section">
      <div class="search-bar">
        <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="searchPlaceholder"
          @input="debouncedSearch"
        />
        <button v-if="searchQuery" class="clear-search" @click="clearSearch">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Type Switcher (Tabs) -->
    <div class="library-tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        class="tab-btn"
        :class="{ active: currentTabId === tab.id }"
        @click="currentTabId = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Dynamic Content Window -->
    <div class="library-content">
       <component 
          :is="currentTabComponent" 
          :searchQuery="debouncedQuery"
       />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import LibraryTracks from '@/components/library/LibraryTracks.vue'
import LibraryAlbums from '@/components/library/LibraryAlbums.vue'
import LibraryArtists from '@/components/library/LibraryArtists.vue'
import LibraryPlaylists from '@/components/library/LibraryPlaylists.vue'

const tabs = [
  { id: 'tracks', label: 'Треки', component: LibraryTracks, placeholder: 'Поиск треков...' },
  { id: 'albums', label: 'Альбомы', component: LibraryAlbums, placeholder: 'Поиск альбомов...' },
  { id: 'artists', label: 'Артисты', component: LibraryArtists, placeholder: 'Поиск исполнителей...' },
  { id: 'playlists', label: 'Плейлисты', component: LibraryPlaylists, placeholder: 'Поиск плейлистов...' },
]

// Tab State configuration
const STORAGE_KEY = 'library_active_tab'
const currentTabId = ref(localStorage.getItem(STORAGE_KEY) || 'tracks')

const currentTab = computed(() => tabs.find(t => t.id === currentTabId.value) || tabs[0])
const currentTabComponent = computed(() => currentTab.value.component)
const searchPlaceholder = computed(() => currentTab.value.placeholder)

// Persist tab selection
watch(currentTabId, (newVal) => {
  localStorage.setItem(STORAGE_KEY, newVal)
  // Clear search on tab switch maybe? 
  // User might expect search to persist if relevant (e.g. searching "Linkin Park" works for all)
  // But if I list tracks and switch to playlists, "Linkin Park" might verify emptiness. 
  // I'll keep it.
})

// Search State
const searchQuery = ref('')
const debouncedQuery = ref('')
let searchTimeout = null

const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    debouncedQuery.value = searchQuery.value
  }, 300)
}

const clearSearch = () => {
  searchQuery.value = ''
  debouncedQuery.value = ''
}

</script>

<style scoped>
.library-view {
  padding: 16px;
  padding-bottom: 120px; /* Space for player */
  min-height: 100vh;
}

.search-section {
  margin-bottom: 16px;
}

.search-bar {
  display: flex;
  align-items: center;
  background: var(--bg-elevated);
  border-radius: 8px;
  padding: 8px 12px;
  gap: 8px;
}

.search-bar input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 16px;
  outline: none;
}

.search-icon {
  color: var(--text-secondary);
}

.clear-search {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
}

/* Tabs Styles */
.library-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  overflow-x: auto;
  padding-bottom: 4px; /* for scrollbar */
  scrollbar-width: none; /* Firefox */
}

.library-tabs::-webkit-scrollbar {
  display: none;
}

.tab-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: var(--text-primary);
  background: var(--bg-elevated);
}

.tab-btn.active {
  background: var(--text-primary); /* High contrast active state like pills */
  color: var(--bg-card); /* Inverted text for active */
  font-weight: 600;
}

/* Make it look more "Apple Music" or "Spotify" style: 
   or the "Albums Design" as presumably requested (usually simple text or pill).
   I went with Pill style for clear indication. */

</style>

