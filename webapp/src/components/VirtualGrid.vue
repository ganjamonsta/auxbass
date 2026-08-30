<template>
  <div class="virtual-grid-container" ref="containerRef">
    <!-- Initial loading skeleton (before first fetch) -->
    <div v-if="loading && items.length === 0" class="media-grid" :class="`type-${type}`">
      <GridSkeleton v-for="i in skeletonCount" :key="i" :type="type" />
    </div>
    
    <!-- Items grid -->
    <template v-else-if="items.length > 0">
      <div class="media-grid" :class="`type-${type}`">
        <template v-for="item in items" :key="getKey(item)">
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
      </div>

      <!-- Loading more skeleton items -->
      <div v-if="loadingMore" class="media-grid loading-more-grid" :class="`type-${type}`">
        <GridSkeleton v-for="i in Math.min(6, skeletonCount)" :key="`loading-${i}`" :type="type" />
      </div>

      <!-- Scroll Sentinel for IntersectionObserver -->
      <div ref="sentinelRef" class="scroll-sentinel" />
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
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
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
  }
})

const emit = defineEmits(['click', 'play', 'contextmenu'])

const containerRef = ref(null)
const sentinelRef = ref(null)
const items = ref([])
const total = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
let observer = null
let scrollContainer = null

const getKey = (item) => {
  return item?.id ?? item?.name ?? JSON.stringify(item)
}

// Find scroll container
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
      // Deduplicate items
      const existingIds = new Set(items.value.map(i => getKey(i)))
      const filtered = newItems.filter(i => !existingIds.has(getKey(i)))
      items.value.push(...filtered)
    }
  } catch (err) {
    console.error('VirtualGrid loadMore error:', err)
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
    }
  } catch (err) {
    console.error('VirtualGrid initial load error:', err)
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

// Event handlers
const handleClick = (item) => emit('click', item)
const handlePlay = (item) => emit('play', item)
const handleContextMenu = (item, event) => emit('contextmenu', { item, event })

// Scroll handler fallback
const handleScroll = () => {
  if (loading.value || loadingMore.value) return
  if (items.value.length >= total.value && total.value > 0) return

  if (scrollContainer) {
    let scrollBottom = 0
    if (scrollContainer === window) {
      scrollBottom = window.scrollY + window.innerHeight
      const docHeight = document.documentElement.scrollHeight
      if (docHeight - scrollBottom < 600) {
        loadMore()
      }
    } else {
      scrollBottom = scrollContainer.scrollTop + scrollContainer.clientHeight
      const scrollHeight = scrollContainer.scrollHeight
      if (scrollHeight - scrollBottom < 600) {
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

onMounted(() => {
  scrollContainer = findScrollContainer(containerRef.value)

  if (scrollContainer === window) {
    window.addEventListener('scroll', handleScroll, { passive: true })
  } else if (scrollContainer) {
    scrollContainer.addEventListener('scroll', handleScroll, { passive: true })
  }

  load()
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
  }
  if (scrollContainer === window) {
    window.removeEventListener('scroll', handleScroll)
  } else if (scrollContainer) {
    scrollContainer.removeEventListener('scroll', handleScroll)
  }
})

defineExpose({
  reset,
  refresh: reset,
  total,
  items
})
</script>

<style scoped>
.virtual-grid-container {
  position: relative;
  width: 100%;
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
  margin-top: 14px;
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
