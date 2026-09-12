<template>
  <div 
    class="expandable-search-container" 
    :class="{ 'is-open': isOpen, 'is-loading': loading }"
  >
    <!-- Collapsed Trigger Button -->
    <button 
      v-if="!isOpen" 
      type="button"
      class="search-trigger-btn" 
      @click="openSearch"
      :title="title || 'Поиск'"
    >
      <Search :size="18" class="search-trigger-icon" />
    </button>

    <!-- Expanded Search Bar -->
    <div v-else class="search-input-box">
      <Search :size="18" class="search-inner-icon" />
      <input
        ref="inputRef"
        type="text"
        :value="modelValue"
        :placeholder="placeholder"
        class="search-input-field"
        @input="handleInput"
        @keydown.esc.prevent="closeSearch"
      />
      <div v-if="loading" class="search-spinner"></div>
      
      <!-- Clear query button -->
      <button 
        v-if="modelValue && !loading" 
        type="button" 
        class="search-action-btn clear-btn" 
        @click="clearQuery"
        title="Очистить"
      >
        <X :size="16" />
      </button>

      <!-- Collapse / Close search bar button -->
      <button 
        type="button" 
        class="search-action-btn close-btn" 
        @click="closeSearch"
        title="Закрыть поиск (Esc)"
      >
        <X :size="18" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { Search, X } from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Поиск...'
  },
  loading: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: 'Поиск'
  },
  // Allows parent to control open state externally via v-model:open
  open: {
    type: Boolean,
    default: false
  },
  // If true, search starts open when modelValue has text
  autoOpenOnValue: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits([
  'update:modelValue', 
  'update:open', 
  'input', 
  'clear', 
  'open', 
  'close'
])

const inputRef = ref(null)
const isOpen = ref(props.open || (props.autoOpenOnValue && Boolean(props.modelValue?.trim())))

// Sync prop changes
watch(() => props.open, (val) => {
  if (val !== isOpen.value) {
    isOpen.value = val
    if (val) {
      nextTick(() => inputRef.value?.focus())
    }
  }
})

// Auto open if query exists
watch(() => props.modelValue, (val) => {
  if (props.autoOpenOnValue && val && !isOpen.value) {
    isOpen.value = true
    emit('update:open', true)
  }
})

const openSearch = () => {
  isOpen.value = true
  emit('update:open', true)
  emit('open')
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const closeSearch = () => {
  emit('update:modelValue', '')
  emit('clear')
  isOpen.value = false
  emit('update:open', false)
  emit('close')
}

const clearQuery = () => {
  emit('update:modelValue', '')
  emit('clear')
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const handleInput = (event) => {
  emit('update:modelValue', event.target.value)
  emit('input', event)
}

defineExpose({
  open: openSearch,
  close: closeSearch,
  focus: () => inputRef.value?.focus()
})
</script>

<style scoped>
.expandable-search-container {
  display: flex;
  align-items: center;
  transition: all 0.25s cubic-bezier(0.2, 0, 0, 1);
  flex-shrink: 0;
}

.expandable-search-container.is-open {
  flex: 1;
  width: 100%;
  min-width: 0;
}

/* Collapsed circular button */
.search-trigger-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--c-bg-2, rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-2, rgba(255, 255, 255, 0.8));
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.search-trigger-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: var(--c-text-1, #fff);
  transform: translateY(-1px) scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.search-trigger-btn:active {
  transform: scale(0.95);
}

.search-trigger-icon {
  color: var(--c-text-2, rgba(255, 255, 255, 0.75));
  transition: color 0.2s ease;
}

.search-trigger-btn:hover .search-trigger-icon {
  color: var(--c-text-1, #fff);
}

/* Expanded Search Input Box */
.search-input-box {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  height: 40px;
  padding: 0 12px;
  background: var(--c-bg-0, #101010);
  border-radius: 20px;
  box-shadow:
    inset 2px 2px 5px var(--sh-inset-dark, rgba(0, 0, 0, 0.6)),
    inset -1px -1px 3px var(--sh-inset-light, rgba(255, 255, 255, 0.05)),
    0 0 0 1px rgba(255, 255, 255, 0.08);
  transition: box-shadow 0.2s ease;
  animation: expandIn 0.22s cubic-bezier(0.2, 0, 0, 1);
}

@keyframes expandIn {
  from {
    opacity: 0;
    transform: scaleX(0.85);
  }
  to {
    opacity: 1;
    transform: scaleX(1);
  }
}

.search-input-box:focus-within {
  box-shadow:
    inset 2px 2px 5px var(--sh-inset-dark, rgba(0, 0, 0, 0.6)),
    inset -1px -1px 3px var(--sh-inset-light, rgba(255, 255, 255, 0.05)),
    0 0 0 2px var(--c-accent-glow, rgba(29, 185, 84, 0.4));
}

.search-inner-icon {
  color: var(--c-text-3, rgba(255, 255, 255, 0.4));
  flex-shrink: 0;
}

.search-input-field {
  flex: 1;
  min-width: 0;
  background: transparent;
  border: none;
  outline: none;
  color: var(--c-text-1, #fff);
  font-size: 14px;
  font-weight: 500;
  height: 100%;
  padding: 0;
}

.search-input-field::placeholder {
  color: var(--c-text-3, rgba(255, 255, 255, 0.45));
}

.search-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: transparent;
  border: none;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
  padding: 0;
}

.search-action-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: var(--c-text-1, #fff);
}

.search-action-btn.close-btn {
  background: rgba(255, 255, 255, 0.06);
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  margin-left: 2px;
}

.search-action-btn.close-btn:hover {
  background: rgba(255, 255, 255, 0.18);
  color: var(--c-text-1, #fff);
}

.search-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-top-color: var(--c-accent, #1db954);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
