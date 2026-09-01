<template>
  <div class="virtual-track-list" ref="containerRef">
    <!-- Initial loading skeleton (before first fetch) -->
    <div v-if="loading && items.length === 0" class="track-list initial-loading">
      <TrackSkeleton v-for="i in skeletonCount" :key="i" />
    </div>
    
    <!-- Track list with progressive infinite scroll -->
    <template v-else-if="items.length > 0">
      <div class="track-list">
        <TrackItem
          v-for="(item, idx) in items"
          :key="item.id"
          :track="item"
          :isPlaying="playerStore.currentTrack?.id === item.id"
          :isActive="playerStore.isPlaying && playerStore.currentTrack?.id === item.id"
          :isLiked="item.is_liked"
          :showAlbum="showAlbum"
          :showAddToLibrary="showAddToLibrary"
          :inLibrary="item.in_library"
          @click="handleClick(item, idx)"
          @like="handleLike(item)"
          @menu="(e) => handleMenu(item, idx, e)"
          @download="handleDownload(item)"
          @addToLibrary="handleAddToLibrary(item)"
          @hdNotice="handleHdNotice"
        />
      </div>
      
      <!-- Loading more skeleton items -->
      <div v-if="loadingMore" class="track-list loading-more-list">
        <TrackSkeleton v-for="i in 4" :key="`loading-${i}`" />
      </div>

      <!-- Scroll Sentinel for IntersectionObserver -->
      <div ref="sentinelRef" class="scroll-sentinel" />
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
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
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
const sentinelRef = ref(null)
const items = ref([])
const total = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
let observer = null
let scrollContainer = null

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

// Fetch next page
const loadMore = async () => {
  if (loading.value || loadingMore.value) return
  if (items.value.length >= total.value && total.value > 0) return

  loadingMore.value = true
  try {
    const offset = items.value.length
    const result = await props.fetchFn({
      offset,
      limit: props.pageSize
    })

    if (result) {
      total.value = result.total ?? (items.value.length + (result.items?.length || 0))
      const newItems = result.items || []
      
      // Deduplicate items by ID
      const existingIds = new Set(items.value.map(i => i.id))
      const filtered = newItems.filter(i => !existingIds.has(i.id))
      items.value.push(...filtered)

      emit('update:items', items.value)
      emit('update:total', total.value)
    }
  } catch (err) {
    console.error('VirtualTrackList loadMore error:', err)
  } finally {
    loadingMore.value = false
  }
}

// Initial load
const load = async () => {
  loading.value = true
  items.value = []
  total.value = 0
  try {
    const result = await props.fetchFn({
      offset: 0,
      limit: props.pageSize
    })
    if (result) {
      items.value = result.items || []
      total.value = result.total ?? items.value.length
      emit('update:items', items.value)
      emit('update:total', total.value)
    }
  } catch (err) {
    console.error('VirtualTrackList initial load error:', err)
  } finally {
    loading.value = false
    nextTick(() => {
      setupObserver()
    })
  }
}

// Reset and reload
const reset = async () => {
  await load()
}

// Refresh loaded tracks
const refresh = async () => {
  await load()
}

// Event handlers
const handleClick = (track, index) => {
  emit('click', { track, index, allTracks: items.value })
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
  return items.value
}

// Fallback scroll handler
const handleScroll = () => {
  if (loading.value || loadingMore.value) return
  if (items.value.length >= total.value && total.value > 0) return

  if (scrollContainer) {
    let scrollBottom = 0
    if (scrollContainer === window) {
      scrollBottom = window.scrollY + window.innerHeight
      const docHeight = document.documentElement.scrollHeight
      if (docHeight - scrollBottom < 500) {
        loadMore()
      }
    } else {
      scrollBottom = scrollContainer.scrollTop + scrollContainer.clientHeight
      const scrollHeight = scrollContainer.scrollHeight
      if (scrollHeight - scrollBottom < 500) {
        loadMore()
      }
    }
  }
}

// Setup IntersectionObserver on sentinel
const setupObserver = () => {
  if (observer) {
    observer.disconnect()
    observer = null
  }

  if (!sentinelRef.value) return

  const root = scrollContainer === window ? null : scrollContainer
  observer = new IntersectionObserver(
    (entries) => {
      const entry = entries[0]
      if (entry && entry.isIntersecting) {
        loadMore()
      }
    },
    {
      root,
      rootMargin: '400px',
      threshold: 0
    }
  )

  observer.observe(sentinelRef.value)
}

watch(sentinelRef, () => {
  setupObserver()
})

// Listen for track:changed events to patch tracks in-place
const onTrackChanged = (event) => {
  const { trackId, data } = event.detail || {}
  if (!trackId || !data) return
  for (let i = 0; i < items.value.length; i++) {
    if (items.value[i]?.id === trackId) {
      Object.assign(items.value[i], data)
    }
  }
}

// Listen for track:removed events to remove tracks in-place
const onTrackRemoved = (event) => {
  const { trackId } = event.detail || {}
  if (!trackId) return
  const idx = items.value.findIndex(item => item?.id === trackId)
  if (idx !== -1) {
    items.value.splice(idx, 1)
    total.value = Math.max(0, total.value - 1)
    emit('update:total', total.value)
    emit('update:items', items.value)
  }
}

// Listen for library-specific track removal
const onLibraryTrackRemoved = (event) => {
  const { trackId } = event.detail || {}
  if (!trackId) return
  if (props.menuContext === 'library') {
    onTrackRemoved(event)
  }
}

// Listen for track added to library
const onLibraryTrackAdded = () => {
  if (props.menuContext === 'library') {
    reset()
  }
}

// Setup
onMounted(() => {
  scrollContainer = findScrollContainer(containerRef.value)
  
  if (scrollContainer === window) {
    window.addEventListener('scroll', handleScroll, { passive: true })
  } else if (scrollContainer) {
    scrollContainer.addEventListener('scroll', handleScroll, { passive: true })
  }
  
  window.addEventListener('track:changed', onTrackChanged)
  window.addEventListener('track:removed', onTrackRemoved)
  window.addEventListener('track:removed:library', onLibraryTrackRemoved)
  window.addEventListener('track:added:library', onLibraryTrackAdded)
  load()
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
    observer = null
  }
  if (scrollContainer === window) {
    window.removeEventListener('scroll', handleScroll)
  } else if (scrollContainer) {
    scrollContainer.removeEventListener('scroll', handleScroll)
  }
  window.removeEventListener('track:changed', onTrackChanged)
  window.removeEventListener('track:removed', onTrackRemoved)
  window.removeEventListener('track:removed:library', onLibraryTrackRemoved)
  window.removeEventListener('track:added:library', onLibraryTrackAdded)
})

// Expose methods
defineExpose({
  reset,
  refresh,
  getLoadedTracks,
  total,
  items
})
</script>

<style scoped>
.virtual-track-list {
  position: relative;
  width: 100%;
}

.track-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.initial-loading {
  padding: 0;
}

.loading-more-list {
  margin-top: 4px;
}

.scroll-sentinel {
  width: 100%;
  height: 20px;
  pointer-events: none;
  opacity: 0;
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
