<template>
  <div class="virtual-track-list" ref="containerRef">
    <!-- Initial loading skeleton (before first fetch) -->
    <div v-if="loading && !initialized" class="track-list initial-loading">
      <TrackSkeleton v-for="i in skeletonCount" :key="i" />
    </div>
    
    <!-- Spotify-style virtual scroll list -->
    <template v-else-if="total > 0">
      <!-- Full height spacer for proper scrollbar -->
      <div class="virtual-spacer" :style="{ minHeight: totalHeight + 'px' }">
        <!-- Top skeleton padding (for items above viewport) -->
        <div 
          v-if="topSkeletonCount > 0" 
          class="skeleton-section top-skeletons"
          :style="{ height: topSkeletonHeight + 'px' }"
        >
          <div class="skeleton-placeholder" v-for="i in Math.min(topSkeletonCount, 5)" :key="'top-sk-' + i">
            <TrackSkeleton />
          </div>
        </div>
        
        <!-- Visible items -->
        <div class="visible-items">
          <template v-for="(item, idx) in visibleItems" :key="item?.id ?? `skeleton-${startIndex + idx}`">
            <!-- Skeleton for unloaded items within visible range -->
            <TrackSkeleton v-if="!item" />
            
            <!-- Actual track item -->
            <TrackItem
              v-else
              :track="item"
              :isPlaying="playerStore.currentTrack?.id === item.id"
              :isActive="playerStore.isPlaying && playerStore.currentTrack?.id === item.id"
              :isLiked="item.is_liked"
              :showAlbum="showAlbum"
              :showAddToLibrary="showAddToLibrary"
              :inLibrary="item.in_library"
              @click="handleClick(item, startIndex + idx)"
              @like="handleLike(item)"
              @menu="(e) => handleMenu(item, startIndex + idx, e)"
              @download="handleDownload(item)"
              @addToLibrary="handleAddToLibrary(item)"
              @hdNotice="handleHdNotice"
            />
          </template>
        </div>
        
        <!-- Bottom skeleton padding (for items below viewport) -->
        <div 
          v-if="bottomSkeletonCount > 0" 
          class="skeleton-section bottom-skeletons"
          :style="{ height: bottomSkeletonHeight + 'px' }"
        >
          <div class="skeleton-placeholder" v-for="i in Math.min(bottomSkeletonCount, 5)" :key="'bot-sk-' + i">
            <TrackSkeleton />
          </div>
        </div>
      </div>
      
      <!-- Loading more indicator -->
      <div v-if="loadingMore" class="loading-more">
        <TrackSkeleton v-for="i in 3" :key="`loading-${i}`" />
      </div>
    </template>
    
    <!-- Empty state -->
    <div v-else-if="!loading && total === 0" class="empty-state">
      <slot name="empty">
        <span class="empty-icon"><Music :size="48" /></span>
        <p>Нет треков</p>
      </slot>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { usePlayerStore } from '@/stores/player'
import TrackItem from '@/components/TrackItem.vue'
import TrackSkeleton from '@/components/TrackSkeleton.vue'
import { Music } from 'lucide-vue-next'

const props = defineProps({
  // Fetch function: ({ offset, limit }) => Promise<{ items, total }>
  fetchFn: {
    type: Function,
    required: true
  },
  // Number of items per page
  pageSize: {
    type: Number,
    default: 50
  },
  // Initial skeleton count
  skeletonCount: {
    type: Number,
    default: 12
  },
  // Show album info in track item
  showAlbum: {
    type: Boolean,
    default: false
  },
  // Show add to library button
  showAddToLibrary: {
    type: Boolean,
    default: false
  },
  // Menu context for track actions
  menuContext: {
    type: String,
    default: 'library'
  },
  // Item height in pixels (track row height)
  itemHeight: {
    type: Number,
    default: 72
  },
  // Gap between items
  gap: {
    type: Number,
    default: 2
  },
  // Number of items to overscan (render beyond viewport)
  overscan: {
    type: Number,
    default: 5
  }
})

const emit = defineEmits([
  'click',
  'like',
  'menu',
  'download',
  'addToLibrary',
  'hdNotice',
  'update:items',
  'update:total'
])

const playerStore = usePlayerStore()

// State
const containerRef = ref(null)
const loading = ref(true)
const loadingMore = ref(false)
const initialized = ref(false)
const total = ref(0)
const scrollTop = ref(0)
const containerOffset = ref(Infinity) // Start with Infinity so relativeScroll = 0 until calculated
const viewportHeight = ref(800)
const loadedPages = ref(new Set())
const pendingFetches = ref(new Set())
const sparseItems = ref([])

// Calculate row height with gap
const rowHeight = computed(() => props.itemHeight + props.gap)

// Total list height
const totalHeight = computed(() => {
  if (total.value === 0) return 0
  return total.value * rowHeight.value - props.gap
})

// Calculate visible range based on scroll position relative to container
const startIndex = computed(() => {
  // scrollTop is relative to scroll container, need to subtract container offset
  const relativeScroll = Math.max(0, scrollTop.value - containerOffset.value)
  const start = Math.floor(relativeScroll / rowHeight.value) - props.overscan
  return Math.max(0, start)
})

const endIndex = computed(() => {
  const relativeScroll = Math.max(0, scrollTop.value - containerOffset.value)
  const visibleCount = Math.ceil(viewportHeight.value / rowHeight.value)
  const end = Math.floor(relativeScroll / rowHeight.value) + visibleCount + props.overscan
  return Math.min(total.value, end)
})

// Visible items (with nulls for unloaded)
const visibleItems = computed(() => {
  const result = []
  for (let i = startIndex.value; i < endIndex.value; i++) {
    result.push(sparseItems.value[i] || null)
  }
  return result
})

// Skeleton counts and heights for padding
const topSkeletonCount = computed(() => startIndex.value)
const bottomSkeletonCount = computed(() => Math.max(0, total.value - endIndex.value))
const topSkeletonHeight = computed(() => startIndex.value * rowHeight.value)
const bottomSkeletonHeight = computed(() => bottomSkeletonCount.value * rowHeight.value)

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
    emit('update:items', sparseItems.value)
    emit('update:total', total.value)
    
  } catch (err) {
    console.error('VirtualTrackList fetch error:', err)
  } finally {
    pendingFetches.value.delete(pageNum)
  }
}

// Load pages in visible range
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

// Scroll handler - find scroll container
let scrollContainer = null
let ticking = false

const updateContainerOffset = () => {
  if (containerRef.value && scrollContainer) {
    if (scrollContainer === window) {
      const rect = containerRef.value.getBoundingClientRect()
      containerOffset.value = rect.top + window.scrollY
    } else {
      // Get offset relative to scroll container
      const containerRect = containerRef.value.getBoundingClientRect()
      const scrollRect = scrollContainer.getBoundingClientRect()
      containerOffset.value = containerRect.top - scrollRect.top + scrollContainer.scrollTop
    }
  }
}

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
        // Update container offset on each scroll for dynamic layouts
        updateContainerOffset()
        loadVisiblePages()
      }
      ticking = false
    })
    ticking = true
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
  
  await load()
}

// Refresh (reload all loaded pages)
const refresh = async () => {
  const pages = Array.from(loadedPages.value)
  loadedPages.value.clear()
  await Promise.all(pages.map(p => fetchPage(p)))
}

// Event handlers
const handleClick = (track, index) => {
  emit('click', { track, index, allTracks: sparseItems.value.filter(Boolean) })
}

const handleLike = (track) => {
  emit('like', track)
}

const handleMenu = (track, index, event) => {
  emit('menu', { track, index, event, context: props.menuContext })
}

const handleDownload = (track) => {
  emit('download', track)
}

const handleAddToLibrary = (track) => {
  emit('addToLibrary', track)
}

const handleHdNotice = () => {
  emit('hdNotice')
}

// Get all loaded tracks (for playback)
const getLoadedTracks = () => {
  return sparseItems.value.filter(Boolean)
}

// Listen for track:changed events to patch tracks in-place
const onTrackChanged = (event) => {
  const { trackId, data } = event.detail || {}
  if (!trackId || !data) return
  for (let i = 0; i < sparseItems.value.length; i++) {
    if (sparseItems.value[i]?.id === trackId) {
      Object.assign(sparseItems.value[i], data)
    }
  }
}

// Setup
onMounted(() => {
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
  
  // Calculate initial container offset after next tick (when layout is ready)
  nextTick(() => {
    updateContainerOffset()
    // Trigger initial visible pages load after offset is calculated
    loadVisiblePages()
  })
  
  window.addEventListener('track:changed', onTrackChanged)
  load()
})

onUnmounted(() => {
  if (scrollContainer === window) {
    window.removeEventListener('scroll', handleScroll)
  } else if (scrollContainer) {
    scrollContainer.removeEventListener('scroll', handleScroll)
  }
  window.removeEventListener('track:changed', onTrackChanged)
})

// Expose methods
defineExpose({
  reset,
  refresh,
  getLoadedTracks,
  total,
  items: sparseItems
})
</script>

<style scoped>
.virtual-track-list {
  position: relative;
}

.track-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.initial-loading {
  padding: 0;
}

.virtual-spacer {
  position: relative;
}

.skeleton-section {
  overflow: hidden;
  position: relative;
}

.skeleton-section .skeleton-placeholder {
  position: absolute;
  left: 0;
  right: 0;
}

.top-skeletons .skeleton-placeholder:nth-child(1) { bottom: 0; }
.top-skeletons .skeleton-placeholder:nth-child(2) { bottom: 74px; }
.top-skeletons .skeleton-placeholder:nth-child(3) { bottom: 148px; }
.top-skeletons .skeleton-placeholder:nth-child(4) { bottom: 222px; }
.top-skeletons .skeleton-placeholder:nth-child(5) { bottom: 296px; }

.bottom-skeletons .skeleton-placeholder:nth-child(1) { top: 0; }
.bottom-skeletons .skeleton-placeholder:nth-child(2) { top: 74px; }
.bottom-skeletons .skeleton-placeholder:nth-child(3) { top: 148px; }
.bottom-skeletons .skeleton-placeholder:nth-child(4) { top: 222px; }
.bottom-skeletons .skeleton-placeholder:nth-child(5) { top: 296px; }

.visible-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.loading-more {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  color: var(--c-text-2);
}

.empty-icon {
  color: var(--c-text-3);
  margin-bottom: 16px;
}
</style>
