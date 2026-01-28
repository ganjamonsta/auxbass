import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUIStore = defineStore('ui', () => {
  // Collections tab state: 'albums' or 'playlists'
  const collectionsTab = ref('albums')

  const setCollectionsTab = (tab) => {
    collectionsTab.value = tab
  }

  return {
    collectionsTab,
    setCollectionsTab
  }
})
