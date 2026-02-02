<template>
  <div class="virtual-scroll-container" ref="containerRef">
    <!-- Loading state (initial load) -->
    <div v-if="loading && !initialized" class="virtual-scroll-loading">
      <slot name="loading">
        <div class="loading-spinner">
          <div class="spinner"></div>
          <span v-if="loadingText">{{ loadingText }}</span>
        </div>
      </slot>
    </div>

    <!-- Empty state -->
    <div v-else-if="isEmpty" class="virtual-scroll-empty">
      <slot name="empty">
        <p>Нет элементов</p>
      </slot>
    </div>

    <!-- Content -->
    <template v-else>
      <!-- Top skeletons (for virtual scrolling) -->
      <div 
        v-if="topSkeletonCount > 0" 
        class="skeleton-spacer"
        :style="{ height: `${topSkeletonCount * estimatedItemHeight}px` }"
      >
        <slot name="skeleton" v-for="i in Math.min(topSkeletonCount, skeletonPreviewCount)" :key="'top-' + i" />
      </div>

      <!-- Grid layout -->
      <div 
        v-if="layout === 'grid'" 
        class="virtual-scroll-grid"
        :class="gridClass"
      >
        <slot :items="items" :loading="loadingMore">
          <component
            v-for="(item, index) in items"
            :key="getItemKey(item, index)"
            :is="itemComponent"
            v-bind="getItemProps(item)"
            @click="$emit('item-click', item)"
            @contextmenu.prevent="(e) => $emit('item-contextmenu', { item, event: e })"
          />
        </slot>
      </div>

      <!-- List layout -->
      <div v-else class="virtual-scroll-list">
        <slot :items="items" :loading="loadingMore">
          <component
            v-for="(item, index) in items"
            :key="getItemKey(item, index)"
            :is="itemComponent"
            v-bind="getItemProps(item)"
            @click="$emit('item-click', item)"
            @contextmenu.prevent="(e) => $emit('item-contextmenu', { item, event: e })"
          />
        </slot>
      </div>

      <!-- Bottom skeletons (for virtual scrolling) -->
      <div 
        v-if="bottomSkeletonCount > 0" 
        class="skeleton-spacer"
        :style="{ height: `${bottomSkeletonCount * estimatedItemHeight}px` }"
      >
        <slot name="skeleton" v-for="i in Math.min(bottomSkeletonCount, skeletonPreviewCount)" :key="'bottom-' + i" />
      </div>

      <!-- Load more trigger -->
      <div 
        ref="loadTriggerRef" 
        class="load-trigger" 
        v-show="hasMore && !loading"
      />

      <!-- Loading more indicator -->
      <div v-if="loadingMore" class="loading-more">
        <slot name="loading-more">
          <div class="spinner small"></div>
        </slot>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, toRefs, watch, onMounted, onUnmounted } from 'vue'
import { useVirtualScroll } from '@/composables/useVirtualScroll'

const props = defineProps({
  /**
   * Fetch function: async ({ offset, limit, ...params }) => { items, total }
   */
  fetchFn: {
    type: Function,
    required: true
  },
  /**
   * Items per page
   */
  limit: {
    type: Number,
    default: 30
  },
  /**
   * Layout type: 'grid' or 'list'
   */
  layout: {
    type: String,
    default: 'list',
    validator: v => ['grid', 'list'].includes(v)
  },
  /**
   * Grid CSS class (e.g., 'type-artist', 'type-album')
   */
  gridClass: {
    type: String,
    default: ''
  },
  /**
   * Component to render each item
   */
  itemComponent: {
    type: [Object, String],
    default: null
  },
  /**
   * Function to get item key
   */
  itemKey: {
    type: [String, Function],
    default: 'id'
  },
  /**
   * Function to get item props or prop name mapping
   */
  itemProps: {
    type: [Object, Function],
    default: null
  },
  /**
   * Load immediately on mount
   */
  immediate: {
    type: Boolean,
    default: true
  },
  /**
   * Enable virtual scrolling (unload off-screen items)
   */
  virtualize: {
    type: Boolean,
    default: false
  },
  /**
   * Estimated item height for virtual scrolling
   */
  estimatedItemHeight: {
    type: Number,
    default: 72
  },
  /**
   * Number of skeleton items to show as preview
   */
  skeletonPreviewCount: {
    type: Number,
    default: 3
  },
  /**
   * Loading text for initial load
   */
  loadingText: {
    type: String,
    default: ''
  },
  /**
   * Extra params for fetch (reactive)
   */
  params: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['item-click', 'item-contextmenu', 'loaded', 'error'])

// Create virtual scroll composable
const {
  items,
  total,
  loading,
  loadingMore,
  error,
  hasMore,
  isEmpty,
  initialized,
  currentPage,
  totalPages,
  topSkeletonCount,
  bottomSkeletonCount,
  loadTriggerRef,
  containerRef,
  reset,
  refresh,
  setParams
} = useVirtualScroll({
  fetchFn: props.fetchFn,
  limit: props.limit,
  immediate: props.immediate,
  virtualize: props.virtualize
})

// Watch for param changes
watch(
  () => props.params,
  (newParams) => {
    setParams(newParams)
  },
  { deep: true }
)

// Emit events
watch(error, (err) => {
  if (err) emit('error', err)
})

watch(items, () => {
  emit('loaded', { items: items.value, total: total.value })
})

// Helper functions
const getItemKey = (item, index) => {
  if (typeof props.itemKey === 'function') {
    return props.itemKey(item, index)
  }
  return item[props.itemKey] ?? index
}

const getItemProps = (item) => {
  if (typeof props.itemProps === 'function') {
    return props.itemProps(item)
  }
  if (props.itemProps) {
    const result = {}
    for (const [key, value] of Object.entries(props.itemProps)) {
      result[key] = typeof value === 'string' ? item[value] : value
    }
    return result
  }
  // Default: pass item as-is with common prop names
  return { item }
}

// Expose methods and state
defineExpose({
  items,
  total,
  loading,
  loadingMore,
  hasMore,
  isEmpty,
  initialized,
  currentPage,
  totalPages,
  reset,
  refresh,
  setParams
})
</script>

<style scoped>
.virtual-scroll-container {
  position: relative;
  width: 100%;
}

.virtual-scroll-grid {
  display: grid;
  gap: 24px;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
}

.virtual-scroll-grid.type-artist {
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 24px;
}

.virtual-scroll-grid.type-album {
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
}

.virtual-scroll-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.virtual-scroll-loading,
.virtual-scroll-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  color: var(--text-secondary, #888);
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--bg-highlight, rgba(255,255,255,0.1));
  border-top-color: var(--accent, #1DB954);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.spinner.small {
  width: 20px;
  height: 20px;
  border-width: 2px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.load-trigger {
  height: 1px;
  width: 100%;
}

.loading-more {
  display: flex;
  justify-content: center;
  padding: 16px;
}

.skeleton-spacer {
  position: relative;
  overflow: hidden;
}

/* Responsive */
@media (max-width: 768px) {
  .virtual-scroll-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 16px;
  }
}
</style>
