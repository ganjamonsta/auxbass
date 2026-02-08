<template>
  <div class="collection-view">
    <!-- Search -->
    <SearchBar
      v-model="searchQuery"
      placeholder="Поиск исполнителей..."
      @input="search"
    />

    <!-- Unified artists component with global scope -->
    <LibraryArtists
      ref="contentRef"
      scope="global"
      :searchQuery="debouncedQuery"
    />
  </div>
</template>

<script setup>
import { useCollectionView } from '@/composables'
import SearchBar from '@/components/ui/SearchBar.vue'
import LibraryArtists from '@/components/library/LibraryArtists.vue'

const { searchQuery, debouncedQuery, search, contentRef } = useCollectionView('/artists')
</script>

<style scoped>
.collection-view {
  padding: 16px;
}
</style>
