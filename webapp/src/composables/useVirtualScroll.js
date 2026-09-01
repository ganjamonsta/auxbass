import { ref, shallowRef, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'

/**
 * Universal Windowed Virtual Scroll Composable
 * 
 * Implements high-performance DOM windowing with sparse paged data fetching:
 * - Accurate total virtual height known from `total` (scrollbar immediately reflects full size)
 * - Windowed DOM mounting: only mounts visible items + overscan buffer (~20-30 items)
 * - Automatically unmounts items scrolled out of view to keep memory & DOM size constant
 * - Sparse data loading: placeholders/skeletons rendered for un-fetched chunks
 * - Reliable relative-top scroll tracking inside nested scroll containers or window
 * 
 * @param {Object} options - Configuration options
 * @param {Function} options.fetchFn - Async function ({ offset, limit, ...params }) => Promise<{ items, total }>
 * @param {number} [options.pageSize=50] - Number of items per fetched page
 * @param {number|Function} [options.itemHeight=64] - Item/row height in px
 * @param {number} [options.gap=2] - Gap between items/rows in px
 * @param {number} [options.overscan=10] - Number of items/rows to pre-render outside viewport
 * @param {number|Function|Ref} [options.columns=1] - Number of columns (1 for lists, dynamic for grids)
 * @param {boolean} [options.immediate=true] - Whether to load first page immediately on mount
 * @param {Ref<HTMLElement>} [options.scrollContainer=null] - Custom scroll container ref
 */
export function useVirtualScroll(options = {}) {
  const {
    fetchFn,
    pageSize = options.limit || 50,
    itemHeight = 64,
    gap = 2,
    overscan = 10,
    columns = 1,
    immediate = true,
    scrollContainer = null
  } = options

  // State
  const total = ref(0)
  const loading = ref(false)
  const loadingMore = ref(false)
  const error = ref(null)
  const initialized = ref(false)
  const loadTriggerRef = ref(null)

  // Map of loaded items: index -> item
  const itemsMap = shallowRef(new Map())
  const loadedPages = new Set()
  const pendingPages = new Set()

  // Scroll tracking state
  const containerRef = ref(null)
  const scrollTop = ref(0)
  const viewportHeight = ref(800)
  const containerWidth = ref(0)

  // Extra parameters for filtering/searching/sorting
  const extraParams = ref({})

  let detectedScrollContainer = null
  let ticking = false
  let resizeObserver = null

  // Helpers
  const findScrollContainer = (el) => {
    if (scrollContainer?.value) return scrollContainer.value
    if (scrollContainer && typeof scrollContainer === 'object' && 'nodeType' in scrollContainer) return scrollContainer
    let parent = el?.parentElement
    while (parent) {
      const style = window.getComputedStyle(parent)
      if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
        return parent
      }
      parent = parent.parentElement
    }
    return window
  }

  // Column count (reactive or prop/option)
  const colCount = computed(() => {
    if (typeof columns === 'function') return Math.max(1, columns(containerWidth.value))
    if (typeof columns === 'object' && 'value' in columns) return Math.max(1, columns.value)
    return Math.max(1, Number(columns) || 1)
  })

  // Height calculations
  const effectiveItemHeight = computed(() => {
    const h = typeof itemHeight === 'function' ? itemHeight(containerWidth.value) : itemHeight
    return Number(h) || 64
  })

  const effectiveRowHeight = computed(() => effectiveItemHeight.value + gap)

  const totalRows = computed(() => Math.ceil(total.value / colCount.value))

  const totalHeight = computed(() => {
    if (total.value <= 0) return 0
    return Math.max(0, totalRows.value * effectiveRowHeight.value - gap)
  })

  // Windowed indices calculation
  const startRow = computed(() => {
    return Math.max(0, Math.floor(scrollTop.value / effectiveRowHeight.value) - overscan)
  })

  const endRow = computed(() => {
    return Math.min(totalRows.value, Math.ceil((scrollTop.value + viewportHeight.value) / effectiveRowHeight.value) + overscan)
  })

  const startIndex = computed(() => startRow.value * colCount.value)
  const endIndex = computed(() => Math.min(total.value, endRow.value * colCount.value))

  const topOffset = computed(() => startRow.value * effectiveRowHeight.value)

  // Visible items slice
  const visibleItems = computed(() => {
    const list = []
    const start = startIndex.value
    const end = endIndex.value
    const map = itemsMap.value

    for (let i = start; i < end; i++) {
      const hasItem = map.has(i)
      list.push({
        index: i,
        data: hasItem ? map.get(i) : null,
        isPlaceholder: !hasItem
      })
    }
    return list
  })

  const hasMore = computed(() => itemsMap.value.size < total.value)
  const isEmpty = computed(() => initialized.value && !loading.value && total.value === 0)

  // Fetch a specific page/chunk by offset
  const fetchPage = async (pageOffset) => {
    if (loadedPages.has(pageOffset) || pendingPages.has(pageOffset)) return
    if (!fetchFn) return

    pendingPages.add(pageOffset)

    if (pageOffset === 0 && !initialized.value) {
      loading.value = true
    } else {
      loadingMore.value = true
    }

    try {
      const result = await fetchFn({
        offset: pageOffset,
        limit: pageSize,
        ...extraParams.value
      })

      if (result) {
        total.value = result.total ?? (pageOffset + (result.items?.length || 0))
        const newItems = result.items || []

        // Update itemsMap
        const updated = new Map(itemsMap.value)
        for (let i = 0; i < newItems.length; i++) {
          updated.set(pageOffset + i, newItems[i])
        }
        itemsMap.value = updated
        loadedPages.add(pageOffset)
      }
    } catch (err) {
      error.value = err
      console.error(`[useVirtualScroll] Error fetching offset ${pageOffset}:`, err)
    } finally {
      pendingPages.delete(pageOffset)
      loading.value = false
      loadingMore.value = pendingPages.size > 0
      initialized.value = true
    }
  }

  // Check which pages are needed for the current visible window
  const checkNeededPages = () => {
    if (total.value <= 0) return
    const start = startIndex.value
    const end = endIndex.value

    for (let i = start; i < end; i++) {
      if (!itemsMap.value.has(i)) {
        const pageOffset = Math.floor(i / pageSize) * pageSize
        if (!loadedPages.has(pageOffset) && !pendingPages.has(pageOffset)) {
          fetchPage(pageOffset)
        }
      }
    }
  }

  // Update scroll metrics
  const updateScroll = () => {
    if (!containerRef.value) return
    const sc = detectedScrollContainer || findScrollContainer(containerRef.value)
    detectedScrollContainer = sc

    const containerRect = containerRef.value.getBoundingClientRect()
    containerWidth.value = containerRef.value.clientWidth

    if (sc === window) {
      viewportHeight.value = window.innerHeight
      const listTop = containerRect.top
      scrollTop.value = Math.max(0, -listTop)
    } else if (sc) {
      viewportHeight.value = sc.clientHeight
      const scRect = sc.getBoundingClientRect()
      const relativeTop = containerRect.top - scRect.top
      scrollTop.value = Math.max(0, -relativeTop)
    }

    checkNeededPages()
    ticking = false
  }

  const handleScroll = () => {
    if (!ticking) {
      window.requestAnimationFrame(updateScroll)
      ticking = true
    }
  }

  // Reset data and reload from offset 0
  const reset = async (params = null) => {
    if (params !== null) {
      extraParams.value = params
    }
    loadedPages.clear()
    pendingPages.clear()
    itemsMap.value = new Map()
    total.value = 0
    scrollTop.value = 0
    await fetchPage(0)
    await nextTick()
    updateScroll()
  }

  const refresh = async () => {
    loadedPages.clear()
    pendingPages.clear()
    itemsMap.value = new Map()
    await fetchPage(0)
    await nextTick()
    updateScroll()
  }

  const setParams = async (params) => {
    extraParams.value = { ...extraParams.value, ...params }
    return reset()
  }

  const clear = () => {
    loadedPages.clear()
    pendingPages.clear()
    itemsMap.value = new Map()
    total.value = 0
    initialized.value = false
  }

  // Array of all loaded items in order (for player queue, etc.)
  const getLoadedItems = () => {
    const result = []
    for (let i = 0; i < total.value; i++) {
      if (itemsMap.value.has(i)) {
        result.push(itemsMap.value.get(i))
      }
    }
    return result
  }

  // Patch item by id or predicate
  const patchItem = (predicateOrId, data) => {
    const isFn = typeof predicateOrId === 'function'
    const updated = new Map(itemsMap.value)
    let modified = false

    for (const [index, item] of updated.entries()) {
      if (item && (isFn ? predicateOrId(item) : item.id === predicateOrId)) {
        updated.set(index, { ...item, ...data })
        modified = true
      }
    }
    if (modified) {
      itemsMap.value = updated
    }
  }

  // Remove item by id or predicate
  const removeItem = (predicateOrId) => {
    const isFn = typeof predicateOrId === 'function'
    const current = itemsMap.value
    let targetIndex = -1

    for (const [index, item] of current.entries()) {
      if (item && (isFn ? predicateOrId(item) : item.id === predicateOrId)) {
        targetIndex = index
        break
      }
    }

    if (targetIndex !== -1) {
      const updated = new Map()
      for (const [index, item] of current.entries()) {
        if (index < targetIndex) {
          updated.set(index, item)
        } else if (index > targetIndex) {
          updated.set(index - 1, item)
        }
      }
      itemsMap.value = updated
      total.value = Math.max(0, total.value - 1)
      loadedPages.clear() // Invalidate page boundary cache after shift
    }
  }

  // Watch startIndex / endIndex to fetch missing chunks
  watch([startIndex, endIndex, total], () => {
    checkNeededPages()
  })

  onMounted(async () => {
    await nextTick()
    detectedScrollContainer = findScrollContainer(containerRef.value)
    
    if (detectedScrollContainer === window) {
      window.addEventListener('scroll', handleScroll, { passive: true })
      window.addEventListener('resize', handleScroll, { passive: true })
    } else if (detectedScrollContainer) {
      detectedScrollContainer.addEventListener('scroll', handleScroll, { passive: true })
      window.addEventListener('resize', handleScroll, { passive: true })
    }

    if (containerRef.value) {
      containerWidth.value = containerRef.value.clientWidth
      resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
          containerWidth.value = entry.contentRect.width
          updateScroll()
        }
      })
      resizeObserver.observe(containerRef.value)
    }

    if (immediate) {
      await fetchPage(0)
      await nextTick()
      updateScroll()
    }
  })

  onUnmounted(() => {
    if (detectedScrollContainer === window) {
      window.removeEventListener('scroll', handleScroll)
      window.removeEventListener('resize', handleScroll)
    } else if (detectedScrollContainer) {
      detectedScrollContainer.removeEventListener('scroll', handleScroll)
      window.removeEventListener('resize', handleScroll)
    }
    if (resizeObserver) {
      resizeObserver.disconnect()
      resizeObserver = null
    }
  })

  return {
    // State
    containerRef,
    loadTriggerRef,
    total,
    loading,
    loadingMore,
    loadingSkeletonCount: computed(() => (loadingMore.value ? 4 : 0)),
    error,
    initialized,
    hasMore,
    isEmpty,
    itemsMap,
    items: computed(() => getLoadedItems()),
    
    // Windowing metrics
    scrollTop,
    viewportHeight,
    containerWidth,
    totalHeight,
    topOffset,
    startIndex,
    endIndex,
    visibleItems,
    
    // Methods
    fetchPage,
    reset,
    refresh,
    setParams,
    clear,
    updateScroll,
    getLoadedItems,
    patchItem,
    removeItem
  }
}

export default useVirtualScroll
