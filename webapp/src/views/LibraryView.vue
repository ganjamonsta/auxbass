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
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LibraryTracks from '@/components/library/LibraryTracks.vue'
import LibraryAlbums from '@/components/library/LibraryAlbums.vue'
import LibraryArtists from '@/components/library/LibraryArtists.vue'
import LibraryPlaylists from '@/components/library/LibraryPlaylists.vue'

const router = useRouter()
const authStore = useAuthStore()

const goToChannelSetup = () => {
  router.push('/settings#channel')
}

const tabs = [
  { id: 'tracks', label: 'Треки', component: LibraryTracks, placeholder: 'Название или исполнитель...' },
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

/* Search bar - neumorphic style */
.search-bar {
  display: flex;
  align-items: center;
  background: var(--c-bg-0);
  border-radius: var(--r-lg);
  padding: 0 14px;
  height: 44px;
  gap: 10px;
  box-shadow:
    inset 3px 3px 6px var(--sh-inset-dark),
    inset -2px -2px 4px var(--sh-inset-light);
  transition: box-shadow 0.2s ease;
}

.search-bar:focus-within {
  box-shadow:
    inset 3px 3px 6px var(--sh-inset-dark),
    inset -2px -2px 4px var(--sh-inset-light),
    0 0 0 2px var(--accent-glow);
}

.search-bar input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--c-text-1);
  font-size: 14px;
  outline: none;
}

.search-bar input::placeholder {
  color: var(--c-text-3);
}

.search-icon {
  color: var(--c-text-3);
  flex-shrink: 0;
}

.clear-search {
  background: none;
  border: none;
  color: var(--c-text-3);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Tabs Styles - use design system */
.library-tabs {
  margin-bottom: 20px;
}

/* Override base .neu-tab-bar for this specific use case */
.library-tabs.neu-tab-bar {
  padding: 4px;
}

.neu-tab-content {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.neu-tab-content::after {
  content: attr(data-text);
  height: 0;
  visibility: hidden;
  overflow: hidden;
  user-select: none;
  pointer-events: none;
  font-weight: 600;
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
  color: var(--text-primary);
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 12px 0;
}

.no-channel-prompt p {
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.5;
  margin: 0 0 24px 0;
  max-width: 300px;
}

.no-channel-prompt .setup-btn {
  background: linear-gradient(135deg, var(--accent) 0%, #00c853 100%);
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

