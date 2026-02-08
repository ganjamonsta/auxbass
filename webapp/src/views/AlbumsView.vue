<template>
  <div class="collection-view">
    <!-- Search -->
    <SearchBar
      v-model="searchQuery"
      placeholder="Поиск альбомов..."
      @input="search"
    />

    <!-- Unified albums component with global scope -->
    <LibraryAlbums
      ref="contentRef"
      scope="global"
      :searchQuery="debouncedQuery"
    />
  </div>
</template>

<script setup>
import { useCollectionView } from '@/composables'
import SearchBar from '@/components/ui/SearchBar.vue'
import LibraryAlbums from '@/components/library/LibraryAlbums.vue'

const { searchQuery, debouncedQuery, search, contentRef } = useCollectionView('/albums')
</script>

<style scoped>
.collection-view {
  padding: 16px;
}
</style>
