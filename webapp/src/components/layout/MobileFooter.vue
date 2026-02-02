<template>
  <div class="mobile-footer" :class="footerClasses">
    <!-- Mini Player (when track is playing) -->
    <div v-if="showPlayer && currentTrack" class="footer-player">
      <MiniPlayer
        :track="currentTrack"
        :is-playing="isPlaying"
        :loading="loading"
        :progress="progress"
        :duration="duration"
        :buffered="buffered"
        @expand="$emit('expand-player')"
        @toggle="$emit('toggle-play')"
        @next="$emit('next-track')"
      />
    </div>

    <!-- Bottom Navigation -->
    <nav v-if="showNav" class="footer-nav">
      <button 
        v-for="item in navItems" 
        :key="item.path"
        class="nav-item" 
        :class="{ active: isActiveRoute(item.path, item.matchPaths) }"
        @click="handleNavClick(item.path)"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </button>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MiniPlayer from '@/components/MiniPlayer.vue'

const props = defineProps({
  // Player props
  showPlayer: {
    type: Boolean,
    default: false
  },
  currentTrack: {
    type: Object,
    default: null
  },
  isPlaying: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  progress: {
    type: Number,
    default: 0
  },
  duration: {
    type: Number,
    default: 0
  },
  buffered: {
    type: Number,
    default: 0
  },
  // Navigation props
  showNav: {
    type: Boolean,
    default: true
  },
  navItems: {
    type: Array,
    default: () => [
      { path: '/', icon: '🎵', label: 'Библиотека', matchPaths: ['/'] },
      { path: '/collections', icon: '💿', label: 'Коллекции', matchPaths: ['/collections', '/albums', '/playlists'] },
      { path: '/artists', icon: '🎤', label: 'Артисты', matchPaths: ['/artists'] },
      { path: '/friends', icon: '👥', label: 'Кенты', matchPaths: ['/friends'] },
      { path: '/settings', icon: '⚙️', label: 'Настройки', matchPaths: ['/settings'] },
    ]
  }
})

const emit = defineEmits([
  'expand-player', 
  'toggle-play', 
  'next-track',
  'nav-click',
  'reset-view'
])

const route = useRoute()
const router = useRouter()

const footerClasses = computed(() => ({
  'footer--has-player': props.showPlayer && props.currentTrack,
  'footer--nav-only': props.showNav && (!props.showPlayer || !props.currentTrack)
}))

const isActiveRoute = (path, matchPaths = []) => {
  if (path === '/') return route.path === '/'
  return matchPaths.some(p => route.path.startsWith(p))
}

const handleNavClick = (path) => {
  // If already on this page
  if (isActiveRoute(path, props.navItems.find(i => i.path === path)?.matchPaths || [path])) {
    // Check if we're at the top of the page
    const scrollTop = window.scrollY || document.documentElement.scrollTop
    
    if (scrollTop > 100) {
      // If not at top - scroll to top
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } else {
      // If already at top - reset view state
      emit('reset-view', path)
      window.dispatchEvent(new CustomEvent('reset-view-state', { detail: { route: path } }))
    }
  } else {
    // Navigate to new page
    emit('nav-click', path)
    router.push(path)
  }
}
</script>

<style scoped>
.mobile-footer {
  flex-shrink: 0;
  z-index: var(--z-overlay, 100);
  background: var(--bg-secondary);
  border-top: 1px solid var(--border);
  padding-bottom: env(safe-area-inset-bottom);
}

/* Player section */
.footer-player {
  border-bottom: 1px solid var(--border);
}

/* Navigation */
.footer-nav {
  height: var(--nav-height, 60px);
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  text-decoration: none;
  color: var(--text-tertiary);
  font-size: 10px;
  padding: 8px 12px;
  transition: color 0.2s;
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
  -webkit-tap-highlight-color: transparent;
}

.nav-item.active {
  color: var(--text-primary);
}

.nav-item:active {
  opacity: 0.7;
}

.nav-icon {
  font-size: 22px;
  line-height: 1;
}

.nav-label {
  font-weight: 500;
}

/* Desktop: hide mobile footer */
@media (min-width: 1024px) {
  .mobile-footer {
    display: none;
  }
}
</style>
