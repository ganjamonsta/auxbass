/**
 * Universal Debounced Search Composable
 * 
 * Provides debounced search functionality with automatic cleanup:
 * - query - reactive search query (v-model)
 * - debouncedQuery - debounced value for API calls
 * - search - trigger debounced search
 * - clear - clear search and reset
 * 
 * Usage:
 *   const { query, debouncedQuery, search, clear } = useDebouncedSearch(reset, 300)
 *   <SearchBar v-model="query" @input="search" @clear="clear" />
 */
import { ref, onUnmounted } from 'vue'

/**
 * @param {Function} onSearch - Callback to run after debounce (e.g., reset pagination)
 * @param {number} delay - Debounce delay in ms (default: 300)
 * @returns {Object} Search state and methods
 */
export function useDebouncedSearch(onSearch = null, delay = 300) {
  const query = ref('')
  const debouncedQuery = ref('')
  let timeout = null

  /**
   * Trigger debounced search
   * Call this on @input event
   */
  const search = () => {
    if (timeout) {
      clearTimeout(timeout)
    }
    timeout = setTimeout(() => {
      debouncedQuery.value = query.value
      onSearch?.()
    }, delay)
  }

  /**
   * Clear search query and trigger callback
   */
  const clear = () => {
    if (timeout) {
      clearTimeout(timeout)
      timeout = null
    }
    query.value = ''
    debouncedQuery.value = ''
    onSearch?.()
  }

  /**
   * Set search query programmatically (with optional immediate trigger)
   * @param {string} value - New query value
   * @param {boolean} immediate - If true, skip debounce
   */
  const setQuery = (value, immediate = false) => {
    query.value = value
    if (immediate) {
      if (timeout) {
        clearTimeout(timeout)
        timeout = null
      }
      debouncedQuery.value = value
      onSearch?.()
    } else {
      search()
    }
  }

  /**
   * Check if there's an active search query
   * @returns {boolean}
   */
  const hasQuery = () => {
    return query.value.trim().length > 0
  }

  // Cleanup on unmount
  onUnmounted(() => {
    if (timeout) {
      clearTimeout(timeout)
      timeout = null
    }
  })

  return {
    query,
    debouncedQuery,
    search,
    clear,
    setQuery,
    hasQuery,
  }
}

export default useDebouncedSearch
