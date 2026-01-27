import { ref, computed } from 'vue'

/**
 * Universal pagination composable with memory optimization
 * 
 * Supports two modes:
 * - 'append': Traditional infinite scroll (accumulates all items)
 * - 'windowed': Memory-optimized pagination (shows only current page window)
 * 
 * @param {Object} options - Configuration options
 * @param {Function} options.fetchFn - Async function that fetches data. Receives { offset, limit, page, ...params }
 *                                     Must return { items: Array, total: number }
 * @param {number} [options.limit=30] - Number of items per page
 * @param {boolean} [options.immediate=true] - Whether to load immediately on mount
 * @param {'append'|'windowed'} [options.mode='append'] - Pagination mode
 * @param {number} [options.windowSize=2] - Number of pages to keep in memory (for windowed mode)
 * 
 * @returns {Object} Pagination state and methods
 * 
 * @example
 * // Append mode (infinite scroll)
 * const { items, loading, hasMore, loadMore } = usePagination({
 *   fetchFn: async ({ offset, limit }) => api.get('/items', { params: { offset, limit } }).then(r => r.data),
 *   limit: 30
 * })
 * 
 * @example
 * // Windowed mode (memory optimized)
 * const { items, currentPage, totalPages, goToPage } = usePagination({
 *   fetchFn: async ({ offset, limit }) => api.get('/items', { params: { offset, limit } }).then(r => r.data),
 *   limit: 30,
 *   mode: 'windowed'
 * })
 */
export function usePagination(options) {
  const {
    fetchFn,
    limit = 30,
    immediate = true,
    mode = 'append',
    windowSize = 2
  } = options

  const items = ref([])
  const total = ref(0)
  const offset = ref(0)
  const loading = ref(false)
  const error = ref(null)
  const currentPage = ref(1)
  
  // Extra params for filtering/searching
  const extraParams = ref({})

  // Computed properties
  const hasMore = computed(() => items.value.length < total.value)
  const totalPages = computed(() => Math.ceil(total.value / limit))
  const isFirstPage = computed(() => currentPage.value === 1)
  const isLastPage = computed(() => currentPage.value >= totalPages.value)
  
  // Page info for UI
  const pageInfo = computed(() => ({
    current: currentPage.value,
    total: totalPages.value,
    itemsFrom: total.value === 0 ? 0 : (currentPage.value - 1) * limit + 1,
    itemsTo: Math.min(currentPage.value * limit, total.value),
    itemsTotal: total.value
  }))

  /**
   * Load items for append mode
   * @param {boolean} append - If true, append to existing items
   */
  const loadAppend = async (append = false) => {
    loading.value = true
    error.value = null
    
    try {
      const currentOffset = append ? offset.value : 0
      
      const result = await fetchFn({
        offset: currentOffset,
        limit,
        page: Math.floor(currentOffset / limit) + 1,
        ...extraParams.value
      })
      
      const newItems = result.items || []
      
      if (append) {
        items.value.push(...newItems)
      } else {
        items.value = newItems
        offset.value = 0
        currentPage.value = 1
      }
      
      total.value = result.total || 0
      offset.value += newItems.length
      currentPage.value = Math.ceil(offset.value / limit)
      
      return result
    } catch (err) {
      error.value = err
      console.error('Pagination fetch error:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Load items for windowed mode (replaces items, doesn't accumulate)
   * @param {number} page - Page number to load (1-based)
   */
  const loadWindowed = async (page = 1) => {
    loading.value = true
    error.value = null
    
    try {
      const pageOffset = (page - 1) * limit
      
      const result = await fetchFn({
        offset: pageOffset,
        limit,
        page,
        ...extraParams.value
      })
      
      items.value = result.items || []
      total.value = result.total || 0
      currentPage.value = page
      offset.value = pageOffset + items.value.length
      
      return result
    } catch (err) {
      error.value = err
      console.error('Pagination fetch error:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Universal load function
   */
  const load = async (appendOrPage = false) => {
    if (mode === 'windowed') {
      const page = typeof appendOrPage === 'number' ? appendOrPage : 1
      return loadWindowed(page)
    }
    return loadAppend(appendOrPage)
  }

  /**
   * Load more items (append mode only)
   */
  const loadMore = async () => {
    if (mode === 'windowed') {
      return goToPage(currentPage.value + 1)
    }
    return loadAppend(true)
  }

  /**
   * Go to specific page (windowed mode)
   * @param {number} page - Page number (1-based)
   */
  const goToPage = async (page) => {
    if (page < 1 || page > totalPages.value || loading.value) return
    
    if (mode === 'windowed') {
      return loadWindowed(page)
    }
    
    // For append mode, we need to load all pages up to the target
    // This is not optimal, so windowed mode is recommended for jumping
    const targetOffset = (page - 1) * limit
    if (targetOffset < offset.value) {
      // Going back - need to reload from start
      offset.value = 0
      items.value = []
    }
    
    while (offset.value < targetOffset && hasMore.value) {
      await loadAppend(true)
    }
    
    currentPage.value = page
  }

  /**
   * Go to first page
   */
  const goToFirst = async () => {
    if (mode === 'windowed') {
      return loadWindowed(1)
    }
    // For append mode, just scroll to top (items already loaded)
    currentPage.value = 1
  }

  /**
   * Go to last page
   */
  const goToLast = async () => {
    if (totalPages.value > 0) {
      return goToPage(totalPages.value)
    }
  }

  /**
   * Go to previous page
   */
  const prevPage = async () => {
    if (currentPage.value > 1) {
      return goToPage(currentPage.value - 1)
    }
  }

  /**
   * Go to next page
   */
  const nextPage = async () => {
    if (currentPage.value < totalPages.value) {
      return goToPage(currentPage.value + 1)
    }
  }

  /**
   * Reset and reload with new params
   * @param {Object} params - New extra params (search, filters, etc.)
   */
  const reset = async (params = {}) => {
    extraParams.value = params
    offset.value = 0
    currentPage.value = 1
    return load(mode === 'windowed' ? 1 : false)
  }

  /**
   * Update params and reload
   * @param {Object} params - Params to merge with existing
   */
  const setParams = async (params) => {
    extraParams.value = { ...extraParams.value, ...params }
    offset.value = 0
    currentPage.value = 1
    return load(mode === 'windowed' ? 1 : false)
  }

  /**
   * Clear all items and reset state
   */
  const clear = () => {
    items.value = []
    total.value = 0
    offset.value = 0
    currentPage.value = 1
    error.value = null
    extraParams.value = {}
  }

  /**
   * Refresh current page/state
   */
  const refresh = async () => {
    if (mode === 'windowed') {
      return loadWindowed(currentPage.value)
    }
    // For append mode, reload everything
    offset.value = 0
    return loadAppend(false)
  }

  // Load immediately if requested
  if (immediate) {
    load(mode === 'windowed' ? 1 : false)
  }

  return {
    // State
    items,
    total,
    loading,
    error,
    hasMore,
    offset,
    currentPage,
    totalPages,
    isFirstPage,
    isLastPage,
    pageInfo,
    
    // Methods
    load,
    loadMore,
    reset,
    setParams,
    clear,
    refresh,
    
    // Navigation (windowed mode)
    goToPage,
    goToFirst,
    goToLast,
    prevPage,
    nextPage
  }
}

export default usePagination
