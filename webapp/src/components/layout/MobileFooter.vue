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
        @toggleShuffle="$emit('toggle-shuffle')"
        @toggleRepeat="$emit('toggle-repeat')"
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
        <component :is="item.icon" class="nav-icon" :size="22" :stroke-width="2" />
        <span class="nav-label">{{ item.label }}</span>
      </button>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MiniPlayer from '@/components/MiniPlayer.vue'
import { ListMusic, Disc3, Users, Music2, Settings } from 'lucide-vue-next'

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
      { path: '/', icon: ListMusic, label: 'Библиотека', matchPaths: ['/'] },
      { path: '/collections', icon: Disc3, label: 'Коллекции', matchPaths: ['/collections', '/albums', '/playlists'] },
      { path: '/artists', icon: Music2, label: 'Артисты', matchPaths: ['/artists'] },
      { path: '/friends', icon: Users, label: 'Кенты', matchPaths: ['/friends'] },
      { path: '/settings', icon: Settings, label: 'Настройки', matchPaths: ['/settings'] },
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
  border-top: 2px solid var(--border);
  padding-bottom: env(safe-area-inset-bottom);
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.08);
}

/* Player section */
.footer-player {
  background: var(--bg-primary);
  padding: 8px 0;
}

/* Navigation */
.footer-nav {
  height: 72px;
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 8px 0;
  background: var(--bg-secondary);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-decoration: none;
  color: var(--text-tertiary);
  font-size: 11px;
  padding: 10px 12px;
  transition: all 0.2s ease;
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
  -webkit-tap-highlight-color: transparent;
  border-radius: 12px;
  position: relative;
  min-width: 64px;
}

.nav-item.active {
  color: var(--accent);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 32px;
  height: 3px;
  background: var(--accent);
  border-radius: 0 0 3px 3px;
}

.nav-item:active {
  transform: scale(0.95);
  opacity: 0.7;
}

.nav-icon {
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.nav-item.active .nav-icon {
  transform: translateY(-2px);
}

.nav-label {
  font-weight: 500;
  letter-spacing: 0.02em;
}

/* Desktop: hide mobile footer */
@media (min-width: 1024px) {
  .mobile-footer {
    display: none;
  }
}
</style>
