<template>
  <div class="albums-view">
    <!-- Search -->
    <SearchBar
      v-model="searchQuery"
      placeholder="Поиск альбомов..."
      @input="debouncedSearch"
    />

    <!-- Unified albums component with global scope -->
    <LibraryAlbums
      ref="albumsRef"
      scope="global"
      :searchQuery="debouncedSearchQuery"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useDebouncedSearch } from '@/composables'
import SearchBar from '@/components/ui/SearchBar.vue'
import LibraryAlbums from '@/components/library/LibraryAlbums.vue'

// Refs to child components
const albumsRef = ref(null)

// Debounced search using composable
const { 
  query: searchQuery, 
  debouncedQuery: debouncedSearchQuery, 
  search: debouncedSearch, 
  clear: clearSearch 
} = useDebouncedSearch()

// Обработчик сброса состояния
const handleResetState = (event) => {
  if (event.detail.route === '/albums') {
    // Сбрасываем поиск
    clearSearch()
    // Сбрасываем компонент
    albumsRef.value?.reset()
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
.albums-view {
  padding: 16px;
}
</style>
