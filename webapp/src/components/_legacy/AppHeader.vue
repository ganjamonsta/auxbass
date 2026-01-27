<template>
  <!-- Library view header with search -->
  <header v-if="isLibraryView" class="oneui-header">
    <div class="header-row">
      <!-- Left slot: EnrichmentStatus OR Search field -->
      <div class="header-left-slot" :class="{ expanded: showSearch }">
        <Transition name="fade-slide" mode="out-in">
          <!-- Enrichment status (when search is closed) -->
          <EnrichmentStatus v-if="!showSearch" key="enrichment" />
          
          <!-- Search field (when search is open) -->
          <div v-else key="search" class="search-wrapper" @click="focusInput">
            <!-- Scope toggle (Library / Global) -->
            <button 
              class="search-scope-btn" 
              :class="{ global: searchScope === 'global' }"
              @click.stop="$emit('toggleScope')"
              :title="searchScope === 'library' ? 'Искать в своей библиотеке' : 'Искать везде'"
            >
              <svg v-if="searchScope === 'library'" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
              </svg>
              <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
              </svg>
            </button>
            <div class="search-content">
              <span 
                v-for="(tag, index) in searchTags" 
                :key="index" 
                class="search-tag" 
                @click.stop="$emit('removeTag', index)"
              >
                {{ tag }}
              </span>
              <input 
                ref="searchInputRef"
                :value="searchQuery"
                type="text"
                :placeholder="searchScope === 'library' ? 'Поиск в библиотеке...' : 'Глобальный поиск...'"
                class="search-input-inline"
                @input="$emit('update:searchQuery', $event.target.value)"
                @keyup.escape="$emit('closeSearch')"
                @keydown.enter.prevent="$emit('addTag')"
                @keydown.backspace="$emit('handleBackspace')"
              />
            </div>
          </div>
        </Transition>
      </div>
      
      <!-- Title (visible when search is closed) -->
      <h1 v-if="!showSearch" class="header-title-main" @click="$emit('goHome')">
        {{ tabName }}
      </h1>
      
      <!-- Search Toggle Button -->
      <button @click="$emit('toggleSearch')" class="icon-btn search-toggle">
        <Transition name="icon-flip" mode="out-in">
          <svg v-if="!showSearch" key="search" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
          </svg>
          <svg v-else key="close" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
          </svg>
        </Transition>
      </button>
    </div>
  </header>

  <!-- Compact Header for other views -->
  <header v-else class="compact-header">
    <button @click="$emit('goBack')" class="icon-btn">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
      </svg>
    </button>
    <span class="header-title">{{ title }}</span>
    <div class="spacer"></div>
  </header>
</template>

<script setup>
import { ref, watch } from 'vue'
import EnrichmentStatus from './EnrichmentStatus.vue'

const props = defineProps({
  isLibraryView: { type: Boolean, default: true },
  showSearch: { type: Boolean, default: false },
  searchQuery: { type: String, default: '' },
  searchTags: { type: Array, default: () => [] },
  searchScope: { type: String, default: 'library' },
  tabName: { type: String, default: 'Музыка' },
  title: { type: String, default: 'TG Player' },
})

defineEmits([
  'toggleSearch',
  'closeSearch', 
  'toggleScope',
  'update:searchQuery',
  'addTag',
  'removeTag',
  'handleBackspace',
  'goHome',
  'goBack',
])

const searchInputRef = ref(null)

// Focus input when search opens
watch(() => props.showSearch, async (isOpen) => {
  if (isOpen) {
    await new Promise(r => setTimeout(r, 50))
    searchInputRef.value?.focus()
  }
})

const focusInput = () => {
  searchInputRef.value?.focus()
}

defineExpose({ focusInput })
</script>
