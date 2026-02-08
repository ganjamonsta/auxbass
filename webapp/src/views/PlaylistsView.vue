<template>
  <div class="collection-view">
    <!-- Search -->
    <SearchBar
      v-model="searchQuery"
      placeholder="Поиск плейлистов..."
      @input="search"
    />

    <!-- Unified playlists component with global scope -->
    <LibraryPlaylists
      ref="contentRef"
      scope="global"
      :searchQuery="debouncedQuery"
    />
  </div>
</template>

<script setup>
import { useCollectionView } from '@/composables'
import SearchBar from '@/components/ui/SearchBar.vue'
import LibraryPlaylists from '@/components/library/LibraryPlaylists.vue'

const { searchQuery, debouncedQuery, search, contentRef } = useCollectionView('/playlists')
</script>

<style scoped>
.collection-view {
  padding: 16px;
}
</style>
