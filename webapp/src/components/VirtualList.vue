<template>
  <div 
    ref="containerRef"
    class="virtual-list-container"
    :style="containerStyle"
    @scroll="handleScroll"
  >
    <!-- Spacer to create proper scrollbar -->
    <div class="virtual-list-spacer" :style="spacerStyle">
      <!-- Top padding for items above viewport -->
      <div class="virtual-list-padding-top" :style="{ height: paddingTop + 'px' }" />
      
      <!-- Visible items window -->
      <div class="virtual-list-content">
        <template v-for="(item, index) in visibleItems" :key="item?.id ?? `skeleton-${startIndex + index}`">
          <!-- Skeleton for unloaded items -->
          <slot 
            v-if="!item" 
            name="skeleton" 
            :index="startIndex + index"
          >
            <div class="virtual-list-skeleton" :style="{ height: itemHeight + 'px' }" />
          </slot>
          <!-- Actual item -->
          <slot 
            v-else 
            name="item" 
            :item="item" 
            :index="startIndex + index"
          />
        </template>
      </div>
      
      <!-- Bottom padding for items below viewport -->
      <div class="virtual-list-padding-bottom" :style="{ height: paddingBottom + 'px' }" />
    </div>
    
    <!-- Loading indicator for fetching more -->
    <div v-if="loadingMore" class="virtual-list-loading">
      <slot name="loading">
        <div class="loading-spinner"></div>
      </slot>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  // Total number of items (from API response)
  totalItems: {
    type: Number,
    required: true
  },
  // Loaded items array (may have gaps for unloaded items)
  items: {
    type: Array,
    required: true
  },
  // Height of each item in pixels
  itemHeight: {
    type: Number,
    default: 72
  },
  // Number of items to render above/below viewport
  overscan: {
    type: Number,
    default: 5
  },
  // Gap between items
  gap: {
    type: Number,
    default: 0
  },
  // Is currently loading more items
  loadingMore: {
    type: Boolean,
    default: false
  },
  // Custom container height (or use 100%)
  height: {
    type: String,
    default: '100%'
  },
  // Whether to use grid layout
  gridColumns: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['load-range', 'scroll'])

const containerRef = ref(null)
const scrollTop = ref(0)
const containerHeight = ref(0)

// Calculate total height of the scrollable area
const totalHeight = computed(() => {
  if (props.gridColumns > 0) {
    const rows = Math.ceil(props.totalItems / props.gridColumns)
    return rows * (props.itemHeight + props.gap) - props.gap
  }
  return props.totalItems * (props.itemHeight + props.gap) - props.gap
})

// Calculate which items are visible
const startIndex = computed(() => {
  const itemWithGap = props.itemHeight + props.gap
  if (props.gridColumns > 0) {
    const row = Math.floor(scrollTop.value / itemWithGap)
    return Math.max(0, (row - props.overscan) * props.gridColumns)
  }
  return Math.max(0, Math.floor(scrollTop.value / itemWithGap) - props.overscan)
})

const endIndex = computed(() => {
  const itemWithGap = props.itemHeight + props.gap
  if (props.gridColumns > 0) {
    const visibleRows = Math.ceil(containerHeight.value / itemWithGap)
    const endRow = Math.floor(scrollTop.value / itemWithGap) + visibleRows + props.overscan
    return Math.min(props.totalItems, endRow * props.gridColumns)
  }
  const visibleCount = Math.ceil(containerHeight.value / itemWithGap)
  return Math.min(props.totalItems, Math.floor(scrollTop.value / itemWithGap) + visibleCount + props.overscan)
})

// Create visible items array with placeholders for unloaded items
const visibleItems = computed(() => {
  const result = []
  for (let i = startIndex.value; i < endIndex.value; i++) {
    // Try to find item by index
    const item = props.items[i]
    result.push(item || null) // null = skeleton
  }
  return result
})

// Calculate padding for positioning
const paddingTop = computed(() => {
  const itemWithGap = props.itemHeight + props.gap
  if (props.gridColumns > 0) {
    const row = Math.floor(startIndex.value / props.gridColumns)
    return row * itemWithGap
  }
  return startIndex.value * itemWithGap
})

const paddingBottom = computed(() => {
  const itemWithGap = props.itemHeight + props.gap
  if (props.gridColumns > 0) {
    const endRow = Math.ceil(endIndex.value / props.gridColumns)
    const totalRows = Math.ceil(props.totalItems / props.gridColumns)
    return Math.max(0, (totalRows - endRow) * itemWithGap)
  }
  return Math.max(0, (props.totalItems - endIndex.value) * itemWithGap)
})

const containerStyle = computed(() => ({
  height: props.height,
  overflow: 'auto'
}))

const spacerStyle = computed(() => ({
  minHeight: totalHeight.value + 'px',
  position: 'relative'
}))

// Handle scroll events
let ticking = false
const handleScroll = (event) => {
  if (!ticking) {
    requestAnimationFrame(() => {
      scrollTop.value = event.target.scrollTop
      containerHeight.value = event.target.clientHeight
      
      // Emit load-range event for fetching needed items
      emit('load-range', {
        start: startIndex.value,
        end: endIndex.value,
        scrollTop: scrollTop.value
      })
      
      emit('scroll', event)
      ticking = false
    })
    ticking = true
  }
}

// Update container height on resize
let resizeObserver = null

onMounted(() => {
  if (containerRef.value) {
    containerHeight.value = containerRef.value.clientHeight
    scrollTop.value = containerRef.value.scrollTop
    
    resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        containerHeight.value = entry.contentRect.height
      }
    })
    resizeObserver.observe(containerRef.value)
    
    // Initial load range emit
    nextTick(() => {
      emit('load-range', {
        start: startIndex.value,
        end: endIndex.value,
        scrollTop: 0
      })
    })
  }
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})

// Watch for totalItems changes to trigger re-render
watch(() => props.totalItems, () => {
  if (containerRef.value) {
    emit('load-range', {
      start: startIndex.value,
      end: endIndex.value,
      scrollTop: scrollTop.value
    })
  }
})

// Expose scroll methods
const scrollToIndex = (index) => {
  if (containerRef.value) {
    const itemWithGap = props.itemHeight + props.gap
    if (props.gridColumns > 0) {
      const row = Math.floor(index / props.gridColumns)
      containerRef.value.scrollTop = row * itemWithGap
    } else {
      containerRef.value.scrollTop = index * itemWithGap
    }
  }
}

const scrollToTop = () => {
  if (containerRef.value) {
    containerRef.value.scrollTop = 0
  }
}

defineExpose({
  scrollToIndex,
  scrollToTop,
  containerRef
})
</script>

<style scoped>
.virtual-list-container {
  position: relative;
  will-change: scroll-position;
  -webkit-overflow-scrolling: touch;
}

.virtual-list-spacer {
  display: flex;
  flex-direction: column;
}

.virtual-list-content {
  display: flex;
  flex-direction: column;
}

.virtual-list-skeleton {
  background: var(--xm-bg-surface, #222);
  border-radius: var(--neu-radius-md, 12px);
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

.virtual-list-loading {
  display: flex;
  justify-content: center;
  padding: 16px;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--xm-bg-surface, #222);
  border-top-color: var(--accent, #1db954);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
