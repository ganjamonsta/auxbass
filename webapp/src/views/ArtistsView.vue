<template>
  <div class="artists-view">
    <!-- Search -->
    <SearchBar
      v-model="searchQuery"
      placeholder="Поиск исполнителей..."
      @input="debouncedSearch"
    />

    <!-- Unified artists component with global scope -->
    <LibraryArtists
      ref="artistsRef"
      scope="global"
      :searchQuery="debouncedSearchQuery"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useDebouncedSearch } from '@/composables'
import SearchBar from '@/components/ui/SearchBar.vue'
import LibraryArtists from '@/components/library/LibraryArtists.vue'

// Refs to child components
const artistsRef = ref(null)

// Debounced search using composable
const { 
  query: searchQuery, 
  debouncedQuery: debouncedSearchQuery, 
  search: debouncedSearch, 
  clear: clearSearch 
} = useDebouncedSearch()

// Обработчик сброса состояния
const handleResetState = (event) => {
  if (event.detail.route === '/artists') {
    // Сбрасываем поиск
    clearSearch()
    // Сбрасываем компонент
    artistsRef.value?.reset()
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
.artists-view {
  padding: 16px;
}
</style>
