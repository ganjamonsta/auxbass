<template>
  <div class="pagination-nav" v-if="totalPages > 1">
    <!-- Top navigation (compact) -->
    <div v-if="position === 'top'" class="pagination-top">
      <button 
        class="nav-btn back-to-top" 
        @click="$emit('goToFirst')"
        :disabled="isFirstPage || loading"
        v-if="!isFirstPage"
      >
        ↑ К началу
      </button>
      <span class="page-indicator">
        {{ pageInfo.itemsFrom }}-{{ pageInfo.itemsTo }} из {{ pageInfo.itemsTotal }}
      </span>
    </div>

    <!-- Bottom navigation (full) -->
    <div v-else class="pagination-bottom">
      <!-- Page info -->
      <div class="page-info">
        Страница {{ currentPage }} из {{ totalPages }}
        <span class="items-info">({{ pageInfo.itemsFrom }}-{{ pageInfo.itemsTo }} из {{ pageInfo.itemsTotal }})</span>
      </div>

      <!-- Navigation buttons -->
      <div class="nav-buttons">
        <button 
          class="nav-btn" 
          @click="$emit('goToFirst')"
          :disabled="isFirstPage || loading"
          title="В начало"
        >
          <ChevronsLeft :size="18" />
        </button>
        
        <button 
          class="nav-btn" 
          @click="$emit('prevPage')"
          :disabled="isFirstPage || loading"
          title="Предыдущая"
        >
          <ChevronLeft :size="18" />
        </button>

        <!-- Page numbers -->
        <div class="page-numbers">
          <button
            v-for="page in visiblePages"
            :key="page"
            class="page-btn"
            :class="{ active: page === currentPage, ellipsis: page === '...' }"
            :disabled="page === '...' || page === currentPage || loading"
            @click="page !== '...' && $emit('goToPage', page)"
          >
            {{ page }}
          </button>
        </div>

        <button 
          class="nav-btn" 
          @click="$emit('nextPage')"
          :disabled="isLastPage || loading"
          title="Следующая"
        >
          <ChevronRight :size="18" />
        </button>
        
        <button 
          class="nav-btn" 
          @click="$emit('goToLast')"
          :disabled="isLastPage || loading"
          title="В конец"
        >
          <ChevronsRight :size="18" />
        </button>
      </div>

      <!-- Quick jump -->
      <div class="quick-jump" v-if="totalPages > 10">
        <span>Перейти:</span>
        <input
          type="number"
          :min="1"
          :max="totalPages"
          :value="currentPage"
          @keyup.enter="handleQuickJump"
          @blur="handleQuickJump"
          :disabled="loading"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ChevronsLeft, ChevronLeft, ChevronRight, ChevronsRight } from 'lucide-vue-next'

const props = defineProps({
  currentPage: { type: Number, required: true },
  totalPages: { type: Number, required: true },
  pageInfo: { type: Object, required: true },
  isFirstPage: { type: Boolean, default: false },
  isLastPage: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  position: { type: String, default: 'bottom', validator: v => ['top', 'bottom'].includes(v) },
  maxVisiblePages: { type: Number, default: 5 }
})

const emit = defineEmits(['goToPage', 'goToFirst', 'goToLast', 'prevPage', 'nextPage'])

// Calculate visible page numbers with ellipsis
const visiblePages = computed(() => {
  const { currentPage, totalPages, maxVisiblePages } = props
  
  if (totalPages <= maxVisiblePages) {
    return Array.from({ length: totalPages }, (_, i) => i + 1)
  }
  
  const pages = []
  const half = Math.floor(maxVisiblePages / 2)
  
  let start = Math.max(1, currentPage - half)
  let end = Math.min(totalPages, currentPage + half)
  
  // Adjust if at edges
  if (currentPage <= half) {
    end = maxVisiblePages
  } else if (currentPage >= totalPages - half) {
    start = totalPages - maxVisiblePages + 1
  }
  
  // Add first page and ellipsis if needed
  if (start > 1) {
    pages.push(1)
    if (start > 2) pages.push('...')
  }
  
  // Add visible pages
  for (let i = start; i <= end; i++) {
    if (!pages.includes(i)) pages.push(i)
  }
  
  // Add ellipsis and last page if needed
  if (end < totalPages) {
    if (end < totalPages - 1) pages.push('...')
    pages.push(totalPages)
  }
  
  return pages
})

const handleQuickJump = (event) => {
  const value = parseInt(event.target.value)
  if (value >= 1 && value <= props.totalPages && value !== props.currentPage) {
    emit('goToPage', value)
  }
}
</script>

<style scoped>
.pagination-nav {
  padding: 12px 0;
}

/* Top navigation */
.pagination-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: var(--bg-elevated);
  border-radius: 8px;
  margin-bottom: 12px;
}

.back-to-top {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: var(--accent);
  color: var(--accent-text, #000);
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.back-to-top:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-indicator {
  color: var(--text-secondary);
  font-size: 13px;
}

/* Bottom navigation */
.pagination-bottom {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--bg-elevated);
  border-radius: 12px;
}

.page-info {
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
}

.items-info {
  color: var(--text-secondary);
  font-weight: 400;
  margin-left: 4px;
}

.nav-buttons {
  display: flex;
  align-items: center;
  gap: 6px;
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--bg-secondary);
  border: none;
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn:hover:not(:disabled) {
  background: var(--accent);
  color: var(--accent-text, #000);
}

.nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 4px;
  margin: 0 8px;
}

.page-btn {
  min-width: 36px;
  height: 36px;
  padding: 0 8px;
  background: var(--bg-secondary);
  border: none;
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled):not(.ellipsis) {
  background: var(--accent-light);
}

.page-btn.active {
  background: var(--accent);
  color: var(--accent-text, #000);
  font-weight: 600;
}

.page-btn.ellipsis {
  background: transparent;
  cursor: default;
  color: var(--text-secondary);
}

.quick-jump {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 13px;
}

.quick-jump input {
  width: 60px;
  padding: 6px 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 14px;
  text-align: center;
}

.quick-jump input:focus {
  outline: none;
  border-color: var(--accent);
}

/* Mobile responsive */
@media (max-width: 480px) {
  .pagination-bottom {
    padding: 12px;
  }
  
  .nav-btn,
  .page-btn {
    width: 32px;
    height: 32px;
    font-size: 12px;
  }
  
  .page-numbers {
    gap: 2px;
    margin: 0 4px;
  }
  
  .page-btn {
    min-width: 32px;
    padding: 0 4px;
  }
}
</style>
