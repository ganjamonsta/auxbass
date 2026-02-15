<template>
  <div class="virtual-grid-container" ref="containerRef">
    <!-- Initial loading skeleton (before first fetch) -->
    <div v-if="loading && !initialized" class="media-grid" :class="`type-${type}`">
      <GridSkeleton v-for="i in skeletonCount" :key="i" :type="type" />
    </div>
    
    <!-- Virtual scroll grid -->
    <template v-else-if="total > 0">
      <!-- Spacer to create proper scrollbar height -->
      <div class="virtual-grid-spacer" :style="spacerStyle">
        <!-- Top padding -->
        <div :style="{ height: paddingTop + 'px' }" />
        
        <!-- Visible rows -->
        <div class="media-grid" :class="`type-${type}`" :style="gridStyle">
          <template v-for="(item, idx) in visibleItems" :key="item?.id ?? `skeleton-${startIndex + idx}`">
            <!-- Skeleton for unloaded items -->
            <GridSkeleton v-if="!item" :type="type" />
            
            <!-- Actual item based on type -->
            <template v-else>
              <AlbumGridCard
                v-if="type === 'album'"
                :album="item"
                @click="handleClick(item)"
                @play="handlePlay(item)"
                @contextmenu="(e) => handleContextMenu(item, e)"
              />
              <ArtistGridCard
                v-else-if="type === 'artist'"
                :artist="item"
                @click="handleClick(item)"
                @contextmenu="(e) => handleContextMenu(item, e)"
              />
              <PlaylistGridCard
                v-else-if="type === 'playlist'"
                :playlist="item"
                @click="handleClick(item)"
                @play="handlePlay(item)"
                @contextmenu="(e) => handleContextMenu(item, e)"
              />
            </template>
          </template>
        </div>
        
        <!-- Bottom padding -->
        <div :style="{ height: paddingBottom + 'px' }" />
      </div>
      
      <!-- Loading more indicator -->
      <div v-if="loadingMore" class="media-grid loading-more-grid" :class="`type-${type}`">
        <GridSkeleton v-for="i in 3" :key="`loading-${i}`" :type="type" />
      </div>
    </template>
    
    <!-- Empty state -->
    <div v-else-if="!loading && total === 0" class="empty-state">
      <slot name="empty">
        <span class="empty-icon">
          <Disc3 v-if="type === 'album'" :size="48" />
          <User v-else-if="type === 'artist'" :size="48" />
          <Music v-else :size="48" />
        </span>
        <p>Ничего не найдено</p>
      </slot>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import GridSkeleton from '@/components/GridSkeleton.vue'
import AlbumGridCard from '@/components/AlbumGridCard.vue'
import ArtistGridCard from '@/components/ArtistGridCard.vue'
import PlaylistGridCard from '@/components/PlaylistGridCard.vue'
import { Disc3, User, Music } from 'lucide-vue-next'

const props = defineProps({
  // Item type: 'album', 'artist', 'playlist'
  type: {
    type: String,
    default: 'album',
    validator: v => ['album', 'artist', 'playlist'].includes(v)
  },
  // Fetch function: ({ offset, limit }) => Promise<{ items, total }>
  fetchFn: {
    type: Function,
    required: true
  },
  // Number of items per page
  pageSize: {
    type: Number,
    default: 30
  },
  // Initial skeleton count
  skeletonCount: {
    type: Number,
    default: 12
  },
  // Number of rows to overscan
  overscanRows: {
    type: Number,
    default: 2
  }
})

const emit = defineEmits(['click', 'play', 'contextmenu'])

// Constants for grid layout
const ITEM_HEIGHT = 200 // Approximate height of grid card
const GAP = 14
const MIN_ITEM_WIDTH = 130

// State
const containerRef = ref(null)
const loading = ref(true)
const loadingMore = ref(false)
const initialized = ref(false)
const total = ref(0)
const scrollTop = ref(0)
const containerOffset = ref(Infinity) // Start with Infinity so relativeScroll = 0 until calculated
const viewportHeight = ref(800)
const containerWidth = ref(0)
const loadedPages = ref(new Set())
const pendingFetches = ref(new Set())
const sparseItems = ref([])

// Scroll container reference
let scrollContainer = null

// Calculate number of columns based on container width
// Formula matches CSS auto-fill: N = floor((width + gap) / (minWidth + gap))
const columns = computed(() => {
  if (containerWidth.value === 0) return 3 // Default
  return Math.max(3, Math.floor((containerWidth.value + GAP) / (MIN_ITEM_WIDTH + GAP)))
})

// Calculate row height (item + gap)
const rowHeight = computed(() => ITEM_HEIGHT + GAP)

// Calculate total rows
const totalRows = computed(() => Math.ceil(total.value / columns.value))

// Calculate visible row range based on scroll position relative to container
const startRow = computed(() => {
  const relativeScroll = Math.max(0, scrollTop.value - containerOffset.value)
  return Math.max(0, Math.floor(relativeScroll / rowHeight.value) - props.overscanRows)
})

const endRow = computed(() => {
  const relativeScroll = Math.max(0, scrollTop.value - containerOffset.value)
  const visibleRows = Math.ceil(viewportHeight.value / rowHeight.value)
  return Math.min(totalRows.value, Math.floor(relativeScroll / rowHeight.value) + visibleRows + props.overscanRows)
})

// Calculate visible item indices
const startIndex = computed(() => startRow.value * columns.value)
const endIndex = computed(() => Math.min(total.value, endRow.value * columns.value))

// Visible items (with nulls for unloaded)
const visibleItems = computed(() => {
  const result = []
  for (let i = startIndex.value; i < endIndex.value; i++) {
    result.push(sparseItems.value[i] || null)
  }
  return result
})

// Padding for virtual scroll
const paddingTop = computed(() => startRow.value * rowHeight.value)
const paddingBottom = computed(() => Math.max(0, (totalRows.value - endRow.value) * rowHeight.value))

// Total spacer height
const spacerStyle = computed(() => ({
  minHeight: totalRows.value * rowHeight.value + 'px'
}))

const gridStyle = computed(() => ({
  // Grid styles are handled by .media-grid CSS
}))

// Page calculations
const getPageForIndex = (index) => Math.floor(index / props.pageSize)

// Fetch a page
const fetchPage = async (pageNum) => {
  if (loadedPages.value.has(pageNum) || pendingFetches.value.has(pageNum)) {
    return
  }
  
  pendingFetches.value.add(pageNum)
  
  try {
    const offset = pageNum * props.pageSize
    const result = await props.fetchFn({
      offset,
      limit: props.pageSize
    })
    
    // Update total if changed
    if (result.total !== total.value) {
      total.value = result.total
      // Resize sparse array
      if (sparseItems.value.length !== result.total) {
        const newArray = new Array(result.total)
        for (let i = 0; i < Math.min(sparseItems.value.length, result.total); i++) {
          if (sparseItems.value[i]) {
            newArray[i] = sparseItems.value[i]
          }
        }
        sparseItems.value = newArray
      }
    }
    
    // Insert items
    const items = result.items || []
    items.forEach((item, i) => {
      sparseItems.value[offset + i] = item
    })
    
    loadedPages.value.add(pageNum)
    
  } catch (err) {
    console.error('VirtualGrid fetch error:', err)
  } finally {
    pendingFetches.value.delete(pageNum)
  }
}

// Load visible pages
const loadVisiblePages = async () => {
  const startPage = getPageForIndex(startIndex.value)
  const endPage = getPageForIndex(Math.max(0, endIndex.value - 1))
  
  const pagesToLoad = []
  for (let page = startPage; page <= endPage; page++) {
    if (!loadedPages.value.has(page) && !pendingFetches.value.has(page)) {
      pagesToLoad.push(page)
    }
  }
  
  if (pagesToLoad.length > 0) {
    loadingMore.value = true
    await Promise.all(pagesToLoad.map(p => fetchPage(p)))
    loadingMore.value = false
  }
}

// Update container offset relative to scroll container
const updateContainerOffset = () => {
  if (containerRef.value && scrollContainer) {
    if (scrollContainer === window) {
      const rect = containerRef.value.getBoundingClientRect()
      containerOffset.value = rect.top + window.scrollY
    } else {
      const containerRect = containerRef.value.getBoundingClientRect()
      const scrollRect = scrollContainer.getBoundingClientRect()
      containerOffset.value = containerRect.top - scrollRect.top + scrollContainer.scrollTop
    }
  }
}

// Find scroll container (parent with overflow)
const findScrollContainer = (el) => {
  let parent = el?.parentElement
  while (parent) {
    const style = getComputedStyle(parent)
    if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
      return parent
    }
    parent = parent.parentElement
  }
  return window
}

// Scroll handler
let ticking = false
const handleScroll = () => {
  if (!ticking) {
    requestAnimationFrame(() => {
      if (scrollContainer) {
        if (scrollContainer === window) {
          scrollTop.value = window.scrollY
          viewportHeight.value = window.innerHeight
        } else {
          scrollTop.value = scrollContainer.scrollTop
          viewportHeight.value = scrollContainer.clientHeight
        }
        updateContainerOffset()
        loadVisiblePages()
      }
      ticking = false
    })
    ticking = true
  }
}

// Setup resize observer and scroll listener
let resizeObserver = null

onMounted(() => {
  if (containerRef.value) {
    containerWidth.value = containerRef.value.clientWidth
    
    // Find scroll container
    scrollContainer = findScrollContainer(containerRef.value)
    
    if (scrollContainer === window) {
      window.addEventListener('scroll', handleScroll, { passive: true })
      viewportHeight.value = window.innerHeight
      scrollTop.value = window.scrollY
    } else {
      scrollContainer.addEventListener('scroll', handleScroll, { passive: true })
      viewportHeight.value = scrollContainer.clientHeight
      scrollTop.value = scrollContainer.scrollTop
    }
    
    resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        containerWidth.value = entry.contentRect.width
      }
    })
    resizeObserver.observe(containerRef.value)
    
    // Calculate initial offset after next tick
    nextTick(() => {
      updateContainerOffset()
      loadVisiblePages()
    })
    
    // Initial load
    load()
  }
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  if (scrollContainer === window) {
    window.removeEventListener('scroll', handleScroll)
  } else if (scrollContainer) {
    scrollContainer.removeEventListener('scroll', handleScroll)
  }
})

// Initial load
const load = async () => {
  loading.value = true
  try {
    await fetchPage(0)
    initialized.value = true
    nextTick(() => {
      updateContainerOffset()
      loadVisiblePages()
    })
  } finally {
    loading.value = false
  }
}

// Reset
const reset = async () => {
  loading.value = true
  initialized.value = false
  loadedPages.value.clear()
  pendingFetches.value.clear()
  sparseItems.value = []
  total.value = 0
  scrollTop.value = 0
  
  if (scrollContainer === window) {
    window.scrollTo(0, 0)
  } else if (scrollContainer) {
    scrollContainer.scrollTop = 0
  }
  
  await load()
}

// Event handlers
const handleClick = (item) => {
  emit('click', item)
}

const handlePlay = (item) => {
  emit('play', item)
}

const handleContextMenu = (item, event) => {
  emit('contextmenu', { item, event })
}

// Scroll to top
const scrollToTop = () => {
  if (scrollContainer === window) {
    window.scrollTo(0, 0)
  } else if (scrollContainer) {
    scrollContainer.scrollTop = 0
  }
}

defineExpose({
  reset,
  scrollToTop,
  total,
  items: sparseItems
})
</script>

<style scoped>
.virtual-grid-container {
  position: relative;
}

.virtual-grid-spacer {
  position: relative;
}

.media-grid {
  display: grid;
  gap: 14px;
}

.media-grid.type-album,
.media-grid.type-playlist {
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
}

.media-grid.type-artist {
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
}

@media (min-width: 500px) {
  .media-grid.type-artist {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  }
}

@media (min-width: 700px) {
  .media-grid.type-artist {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  }
}

.loading-more-grid {
  margin-top: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  color: var(--text-secondary);
}

.empty-icon {
  color: var(--text-tertiary);
  margin-bottom: 16px;
}
</style>
