import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'

/**
 * Universal Virtual Scroll Composable
 * 
 * Provides infinite scroll with memory optimization:
 * - Loads items as user scrolls down
 * - Optionally unloads items outside viewport (virtual scrolling)
 * - Shows skeletons to maintain layout
 * - Works with both list and grid layouts
 * 
 * @param {Object} options - Configuration options
 * @param {Function} options.fetchFn - Async function that fetches data
 *                                     Receives { offset, limit }
 *                                     Must return { items: Array, total: number }
 * @param {number} [options.limit=30] - Number of items per page
 * @param {boolean} [options.immediate=true] - Whether to load immediately on mount
 * @param {boolean} [options.virtualize=false] - Enable virtual scrolling (unload items outside viewport)
 * @param {number} [options.bufferSize=2] - Number of pages to keep in buffer (for virtualize mode)
 * @param {string} [options.rootMargin='200px'] - IntersectionObserver margin for triggering loads
 * @param {Ref<HTMLElement>} [options.scrollContainer=null] - Custom scroll container ref
 * 
 * @example
 * const { 
 *   items, loading, hasMore, total,
 *   loadTriggerRef, reset, refresh
 * } = useVirtualScroll({
 *   fetchFn: async ({ offset, limit }) => api.get('/items', { params: { offset, limit } }),
 *   limit: 30
 * })
 */
export function useVirtualScroll(options) {
  const {
    fetchFn,
    limit = 30,
    immediate = true,
    virtualize = false,
    bufferSize = 2,
    rootMargin = '200px',
    scrollContainer = null
  } = options

  // State
  const items = ref([])
  const total = ref(0)
  const offset = ref(0)
  const loading = ref(false)
  const loadingMore = ref(false)
  const error = ref(null)
  const initialized = ref(false)
  
  // For virtual scrolling
  const visibleStartIndex = ref(0)
  const visibleEndIndex = ref(0)
  const itemHeight = ref(0) // Estimated item height for virtual scrolling
  
  // Extra params for filtering/searching/sorting
  const extraParams = ref({})
  
  // Refs for DOM elements
  const loadTriggerRef = ref(null)
  const containerRef = ref(null)
  
  // Observer reference
  let intersectionObserver = null

  // Computed properties
  const hasMore = computed(() => items.value.length < total.value)
  const currentPage = computed(() => Math.ceil(offset.value / limit))
  const totalPages = computed(() => Math.ceil(total.value / limit))
  const isEmpty = computed(() => !loading.value && items.value.length === 0)
  
  // Items to render (for virtual scrolling, only visible items; otherwise all)
  const visibleItems = computed(() => {
    if (!virtualize) return items.value
    return items.value.slice(visibleStartIndex.value, visibleEndIndex.value)
  })
  
  // Skeleton count to show before content
  const topSkeletonCount = computed(() => {
    if (!virtualize) return 0
    return visibleStartIndex.value
  })
  
  // Skeleton count to show after content
  const bottomSkeletonCount = computed(() => {
    if (!virtualize) return 0
    return Math.max(0, total.value - visibleEndIndex.value)
  })

  /**
   * Fetch items from server
   * @param {boolean} append - Append to existing items or replace
   */
  const fetchItems = async (append = false) => {
    if (loading.value && !append) return
    if (loadingMore.value && append) return
    
    if (append) {
      loadingMore.value = true
    } else {
      loading.value = true
    }
    error.value = null
    
    try {
      const currentOffset = append ? offset.value : 0
      
      const result = await fetchFn({
        offset: currentOffset,
        limit,
        ...extraParams.value
      })
      
      const newItems = result.items || []
      
      if (append) {
        items.value = [...items.value, ...newItems]
      } else {
        items.value = newItems
        offset.value = 0
      }
      
      total.value = result.total || 0
      offset.value = append ? offset.value + newItems.length : newItems.length
      initialized.value = true
      
      return result
    } catch (err) {
      error.value = err
      console.error('Virtual scroll fetch error:', err)
      throw err
    } finally {
      loading.value = false
      loadingMore.value = false
    }
  }

  /**
   * Load more items (for infinite scroll)
   */
  const loadMore = async () => {
    if (!hasMore.value || loading.value || loadingMore.value) return
    return fetchItems(true)
  }

  /**
   * Reset and reload with optional new params
   * @param {Object} params - New extra params
   */
  const reset = async (params = null) => {
    if (params !== null) {
      extraParams.value = params
    }
    offset.value = 0
    items.value = []
    return fetchItems(false)
  }

  /**
   * Update params and reload
   * @param {Object} params - Params to merge
   */
  const setParams = async (params) => {
    extraParams.value = { ...extraParams.value, ...params }
    offset.value = 0
    items.value = []
    return fetchItems(false)
  }

  /**
   * Refresh current data (keep params)
   */
  const refresh = async () => {
    offset.value = 0
    return fetchItems(false)
  }

  /**
   * Clear all data
   */
  const clear = () => {
    items.value = []
    total.value = 0
    offset.value = 0
    error.value = null
    initialized.value = false
  }

  /**
   * Setup IntersectionObserver for infinite scroll
   */
  const setupObserver = () => {
    if (intersectionObserver) {
      intersectionObserver.disconnect()
    }
    
    const root = scrollContainer?.value || null
    
    intersectionObserver = new IntersectionObserver(
      (entries) => {
        const entry = entries[0]
        if (entry?.isIntersecting && hasMore.value && !loading.value && !loadingMore.value) {
          loadMore()
        }
      },
      { 
        root,
        rootMargin,
        threshold: 0 
      }
    )
    
    // Observe load trigger if exists
    if (loadTriggerRef.value) {
      intersectionObserver.observe(loadTriggerRef.value)
    }
  }

  /**
   * Watch for load trigger changes
   */
  watch(loadTriggerRef, (el) => {
    if (el && intersectionObserver) {
      intersectionObserver.observe(el)
    }
  })

  /**
   * Watch hasMore to stop observing when no more items
   */
  watch(hasMore, (value) => {
    if (!value && loadTriggerRef.value && intersectionObserver) {
      intersectionObserver.unobserve(loadTriggerRef.value)
    } else if (value && loadTriggerRef.value && intersectionObserver) {
      intersectionObserver.observe(loadTriggerRef.value)
    }
  })

  // Lifecycle
  onMounted(() => {
    setupObserver()
    if (immediate) {
      fetchItems(false)
    }
  })

  onUnmounted(() => {
    if (intersectionObserver) {
      intersectionObserver.disconnect()
      intersectionObserver = null
    }
  })

  return {
    // State
    items,
    visibleItems,
    total,
    loading,
    loadingMore,
    error,
    hasMore,
    isEmpty,
    initialized,
    currentPage,
    totalPages,
    
    // Skeleton counts for virtual scrolling
    topSkeletonCount,
    bottomSkeletonCount,
    
    // Refs for DOM elements
    loadTriggerRef,
    containerRef,
    
    // Extra params (reactive)
    extraParams,
    
    // Methods
    loadMore,
    reset,
    setParams,
    refresh,
    clear,
    
    // Manual fetch (for advanced usage)
    fetchItems
  }
}

export default useVirtualScroll
