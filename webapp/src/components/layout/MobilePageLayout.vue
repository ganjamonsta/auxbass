<template>
  <div class="mobile-page-layout" :class="layoutClasses">
    <!-- Fixed Header Area -->
    <header class="layout-header" ref="headerRef">
      <!-- Primary header - always visible, never hides on scroll -->
      <div class="header-primary">
        <slot name="header">
          <PageHeader 
            :title="title" 
            :showBack="showBack"
            @goBack="$emit('goBack')"
          >
            <template v-if="$slots['header-toggle']" #toggle>
              <slot name="header-toggle"></slot>
            </template>
            <template v-if="$slots['header-actions']" #actions>
              <slot name="header-actions"></slot>
            </template>
          </PageHeader>
        </slot>
      </div>
      
      <!-- Sub-header - optionally hides on scroll -->
      <div 
        v-if="$slots['sub-header']" 
        class="header-sub"
        :class="{ 'header-sub--hidden': hideSubHeaderOnScroll && isScrolled }"
      >
        <slot name="sub-header"></slot>
      </div>
    </header>

    <!-- Scrollable Content Area -->
    <main 
      class="layout-content" 
      ref="contentRef"
      @scroll="handleScroll"
    >
      <slot></slot>
    </main>

    <!-- Fixed Footer Area -->
    <footer class="layout-footer" v-if="showFooter">
      <slot name="footer">
        <!-- Default: nothing, will be handled by App.vue -->
      </slot>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, provide } from 'vue'
import PageHeader from '@/components/PageHeader.vue'

const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  showBack: {
    type: Boolean,
    default: true
  },
  hideSubHeaderOnScroll: {
    type: Boolean,
    default: true
  },
  showFooter: {
    type: Boolean,
    default: false
  },
  hasPlayer: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['goBack', 'scroll'])

const headerRef = ref(null)
const contentRef = ref(null)
const isScrolled = ref(false)
const scrollTop = ref(0)
let lastScrollTop = 0
const scrollThreshold = 50

const handleScroll = (event) => {
  const target = event.target
  scrollTop.value = target.scrollTop
  
  // Determine if we should hide sub-header
  if (target.scrollTop > scrollThreshold) {
    if (target.scrollTop > lastScrollTop) {
      // Scrolling down - hide
      isScrolled.value = true
    } else {
      // Scrolling up - show
      isScrolled.value = false
    }
  } else {
    isScrolled.value = false
  }
  
  lastScrollTop = target.scrollTop
  emit('scroll', { scrollTop: target.scrollTop, isScrolled: isScrolled.value })
}

const layoutClasses = computed(() => ({
  'layout--has-player': props.hasPlayer,
  'layout--scrolled': isScrolled.value
}))

// Expose scroll methods for external control
const scrollToTop = () => {
  if (contentRef.value) {
    contentRef.value.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

// Provide content ref for child components that need to know scroll position
provide('layoutContentRef', contentRef)
provide('scrollToTop', scrollToTop)

defineExpose({
  scrollToTop,
  contentRef
})
</script>

<style scoped>
.mobile-page-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: var(--bg-primary);
}

/* Fixed Header */
.layout-header {
  flex-shrink: 0;
  position: relative;
  z-index: var(--z-sticky, 20);
  background: var(--bg-primary);
}

.header-primary {
  /* Always visible, no transitions */
}

.header-sub {
  transition: transform 0.2s ease, opacity 0.2s ease, max-height 0.2s ease;
  max-height: 200px;
  overflow: hidden;
}

.header-sub--hidden {
  transform: translateY(-10px);
  opacity: 0;
  max-height: 0;
  pointer-events: none;
}

/* Scrollable Content */
.layout-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  min-height: 0;
  /* Custom scrollbar */
  scrollbar-width: thin;
  scrollbar-color: var(--bg-highlight) transparent;
}

.layout-content::-webkit-scrollbar {
  width: 6px;
}

.layout-content::-webkit-scrollbar-track {
  background: transparent;
}

.layout-content::-webkit-scrollbar-thumb {
  background: var(--bg-highlight);
  border-radius: 3px;
}

.layout-content::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}

/* Fixed Footer */
.layout-footer {
  flex-shrink: 0;
  position: relative;
  z-index: var(--z-sticky, 20);
  background: var(--bg-primary);
}

/* Player adjustment */
.layout--has-player .layout-content {
  /* Space is handled by footer now, no extra padding needed */
}

/* Desktop adjustments - hide on desktop */
@media (min-width: 1024px) {
  .mobile-page-layout {
    /* On desktop, this component is not typically used */
  }
}
</style>
