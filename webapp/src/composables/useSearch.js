/**
 * Search composable
 * Handles search state, tags, scopes
 */
import { ref, computed } from 'vue'

export function useSearch(libraryStore) {
  const showSearch = ref(false)
  const searchQuery = ref('')
  const searchTags = ref([])
  const searchScope = ref('library') // 'library' or 'global'
  const searchInput = ref(null)

  // Debounce timer
  let searchTimeout = null

  /**
   * Combined search query (tags + current input)
   */
  const searchQueryLower = computed(() => {
    const fullQuery = [...searchTags.value, searchQuery.value].filter(Boolean).join(' ')
    return fullQuery.toLowerCase().trim()
  })

  /**
   * Search results - artists matching query
   */
  const searchResultArtists = computed(() => {
    if (!searchQueryLower.value) return []
    const artists = searchScope.value === 'global' 
      ? libraryStore.globalArtists 
      : libraryStore.artists
    return artists.filter(a => 
      a.artist?.toLowerCase().includes(searchQueryLower.value)
    ).slice(0, 5)
  })

  /**
   * Search results - playlists matching query
   */
  const searchResultPlaylists = computed(() => {
    if (!searchQueryLower.value) return []
    return libraryStore.playlists.filter(p => 
      p.name?.toLowerCase().includes(searchQueryLower.value)
    ).slice(0, 5)
  })

  /**
   * Check if there are any search results
   */
  const hasSearchResults = computed(() => {
    return searchResultArtists.value.length > 0 ||
           searchResultPlaylists.value.length > 0
  })

  /**
   * Toggle search visibility
   */
  const toggleSearch = async () => {
    showSearch.value = !showSearch.value
    if (showSearch.value) {
      // Focus input after DOM update
      await new Promise(r => setTimeout(r, 50))
      searchInput.value?.focus()
    } else {
      closeSearch()
    }
  }

  /**
   * Close search and clear state
   */
  const closeSearch = () => {
    showSearch.value = false
    searchQuery.value = ''
    searchTags.value = []
    libraryStore.clearSearch()
  }

  /**
   * Toggle search scope (library/global)
   */
  const toggleSearchScope = () => {
    searchScope.value = searchScope.value === 'library' ? 'global' : 'library'
    // Re-trigger search with new scope
    if (searchQueryLower.value) {
      performSearch()
    }
  }

  /**
   * Add current query as a tag (on Enter)
   */
  const addTag = () => {
    const trimmed = searchQuery.value.trim()
    if (trimmed && !searchTags.value.includes(trimmed)) {
      searchTags.value.push(trimmed)
      searchQuery.value = ''
      performSearch()
    }
  }

  /**
   * Remove a search tag
   */
  const removeTag = (index) => {
    searchTags.value.splice(index, 1)
    performSearch()
  }

  /**
   * Handle backspace - remove last tag if query is empty
   */
  const handleBackspace = () => {
    if (searchQuery.value === '' && searchTags.value.length > 0) {
      searchTags.value.pop()
      performSearch()
    }
  }

  /**
   * Perform search with debounce
   */
  const debouncedSearch = () => {
    clearTimeout(searchTimeout)
    searchTimeout = setTimeout(() => {
      performSearch()
    }, 300)
  }

  /**
   * Execute search against library
   */
  const performSearch = async () => {
    const query = searchQueryLower.value
    if (!query) {
      libraryStore.clearSearch()
      return
    }
    
    await libraryStore.search(query, searchScope.value)
  }

  /**
   * Focus search input
   */
  const focusInput = () => {
    searchInput.value?.focus()
  }

  return {
    // State
    showSearch,
    searchQuery,
    searchTags,
    searchScope,
    searchInput,
    
    // Computed
    searchQueryLower,
    searchResultArtists,
    searchResultPlaylists,
    hasSearchResults,
    
    // Methods
    toggleSearch,
    closeSearch,
    toggleSearchScope,
    addTag,
    removeTag,
    handleBackspace,
    debouncedSearch,
    performSearch,
    focusInput,
  }
}
