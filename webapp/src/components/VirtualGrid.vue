<template>
  <div class="virtual-grid-container" ref="containerRef">
    <!-- Initial loading skeleton (before first fetch) -->
    <div
      v-if="loading && total === 0"
      class="media-grid initial-loading"
      :class="`type-${type}`"
    >
      <GridSkeleton v-for="i in skeletonCount" :key="`init-skel-${i}`" :type="type" />
    </div>

    <!-- Virtual Grid Canvas with Windowed Rows -->
    <div
      v-else-if="total > 0"
      class="virtual-grid-canvas"
      :style="{ height: `${totalHeight}px` }"
    >
      <div
        class="virtual-grid-window media-grid"
        :class="`type-${type}`"
        :style="{
          transform: `translateY(${topOffset}px)`,
          gridTemplateColumns: `repeat(${colCount}, minmax(0, 1fr))`
        }"
      >
        <template v-for="vItem in visibleItems" :key="vItem.index">
          <template v-if="!vItem.isPlaceholder && vItem.data">
            <AlbumGridCard
              v-if="type === 'album'"
              :album="vItem.data"
              @click="handleClick(vItem.data)"
              @play="handlePlay(vItem.data)"
              @contextmenu="(e) => handleContextMenu(vItem.data, e)"
            />
            <ArtistGridCard
              v-else-if="type === 'artist'"
              :artist="vItem.data"
              @click="handleClick(vItem.data)"
              @contextmenu="(e) => handleContextMenu(vItem.data, e)"
            />
            <PlaylistGridCard
              v-else-if="type === 'playlist'"
              :playlist="vItem.data"
              @click="handleClick(vItem.data)"
              @play="handlePlay(vItem.data)"
              @contextmenu="(e) => handleContextMenu(vItem.data, e)"
            />
          </template>
          <GridSkeleton v-else :type="type" />
        </template>
      </div>
    </div>

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
import { computed, watch } from 'vue'
import { useVirtualScroll } from '@/composables/useVirtualScroll'
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
  // Grid gap in px
  gap: {
    type: Number,
    default: 14
  }
})

const emit = defineEmits(['click', 'play', 'contextmenu', 'update:total', 'update:items'])

// Helpers for responsive grid columns and row heights
const getMinColWidth = (width, type) => {
  if (type === 'artist') {
    if (width >= 700) return 140
    if (width >= 500) return 130
    return 110
  }
  return 130
}

const calcColumns = (width, type) => {
  const w = width || 360
  const minW = getMinColWidth(w, type)
  const gap = props.gap
  return Math.max(1, Math.floor((w + gap) / (minW + gap)))
}

const calcRowHeight = (width, type) => {
  const w = width || 360
  const cols = calcColumns(w, type)
  const gap = props.gap
  const colWidth = Math.max(80, (w - (cols - 1) * gap) / cols)
  if (type === 'artist') {
    return colWidth + 38 // Round avatar + name
  }
  return colWidth + 62 // Square cover + margin + name + artist/meta
}

// Initialize virtual scroll engine
const {
  containerRef,
  containerWidth,
  total,
  loading,
  loadingMore,
  error,
  totalHeight,
  topOffset,
  visibleItems,
  getLoadedItems,
  reset,
  refresh,
  updateScroll
} = useVirtualScroll({
  fetchFn: props.fetchFn,
  pageSize: props.pageSize,
  columns: (w) => calcColumns(w, props.type),
  itemHeight: (w) => calcRowHeight(w, props.type),
  gap: props.gap,
  overscan: 2, // 2 rows above and below
  immediate: true
})

// Current column count for styling grid-template-columns
const colCount = computed(() => {
  return calcColumns(containerWidth.value, props.type)
})

watch(total, (newTotal) => {
  emit('update:total', newTotal)
  emit('update:items', getLoadedItems())
})

// Event handlers
const handleClick = (item) => emit('click', item)
const handlePlay = (item) => emit('play', item)
const handleContextMenu = (item, event) => emit('contextmenu', { item, event })

defineExpose({
  reset,
  refresh,
  total,
  items: computed(() => getLoadedItems()),
  updateScroll
})
</script>

<style scoped>
.virtual-grid-container {
  position: relative;
  width: 100%;
}

.virtual-grid-canvas {
  position: relative;
  width: 100%;
  contain: layout paint;
}

.virtual-grid-window {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  width: 100%;
  will-change: transform;
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
