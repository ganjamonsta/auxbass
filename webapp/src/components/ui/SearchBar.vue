<template>
  <div class="search-bar">
    <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
      <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
    </svg>
    <input
      ref="inputRef"
      :value="modelValue"
      type="text"
      :placeholder="placeholder"
      @input="handleInput"
    />
    <div v-if="loading" class="search-spinner"></div>
    <button v-show="modelValue && !loading" class="clear-search" @click="clear">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

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
  }
})

const emit = defineEmits(['update:modelValue', 'input', 'clear'])
const inputRef = ref(null)

const handleInput = (event) => {
  const value = event.target.value
  emit('update:modelValue', value)
  emit('input', event)
}

const clear = () => {
  emit('update:modelValue', '')
  emit('input', { target: { value: '' } }) // Mock event for debounce handlers
  emit('clear')
  // Keep focus on input if needed, or maybe not. 
}

defineExpose({
    focus: () => inputRef.value?.focus()
})
</script>

<style scoped>
/* Search bar - unified neumorphic style */
.search-bar {
  display: flex;
  align-items: center;
  background: var(--c-bg-0);
  border-radius: var(--r-lg);
  padding: 0 14px;
  gap: 10px;
  height: 44px; /* Fixed height! */
  box-shadow:
    inset 3px 3px 6px var(--sh-inset-dark),
    inset -2px -2px 4px var(--sh-inset-light);
  transition: box-shadow 0.2s ease;
  margin-bottom: 16px;
}

.search-bar:focus-within {
  box-shadow:
    inset 3px 3px 6px var(--sh-inset-dark),
    inset -2px -2px 4px var(--sh-inset-light),
    0 0 0 2px var(--accent-glow);
}

.search-bar input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--c-text-1);
  font-size: 14px; /* Unified font size */
  outline: none;
  padding: 0;
  height: 100%;
}

.search-bar input::placeholder {
  color: var(--c-text-3);
}

.search-icon {
  color: var(--c-text-3);
  flex-shrink: 0;
}

.clear-search {
  background: none;
  border: none;
  color: var(--c-text-3);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: color 0.2s, background-color 0.2s;
}

.clear-search:hover {
  color: var(--c-text-1);
  background-color: var(--c-bg-2);
}

.search-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--c-bg-2, var(--bg-highlight));
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
