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
        :is-liked="isLiked"
        @expand="$emit('expand-player')"
        @toggle="$emit('toggle-play')"
        @next="$emit('next-track')"
        @toggleShuffle="$emit('toggle-shuffle')"
        @toggleRepeat="$emit('toggle-repeat')"
        @like="$emit('like')"
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
import { ListMusic, Disc3, Users, Heart, Settings } from 'lucide-vue-next'

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
  isLiked: {
    type: Boolean,
    default: false
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
      { path: '/liked', icon: Heart, label: 'Любимое', matchPaths: ['/liked'] },
      { path: '/collections', icon: Disc3, label: 'Коллекции', matchPaths: ['/collections', '/albums', '/playlists'] },
      { path: '/friends', icon: Users, label: 'Кенты', matchPaths: ['/friends'] },
      { path: '/settings', icon: Settings, label: 'Настройки', matchPaths: ['/settings'] },
    ]
  }
})

const emit = defineEmits([
  'expand-player', 
  'toggle-play', 
  'next-track',
  'toggle-shuffle',
  'toggle-repeat',
  'like',
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

const scrollToTop = () => {
  // 1. Primary main-content container
  const mainContent = document.querySelector('.main-content')
  if (mainContent) {
    mainContent.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // 2. All possible scroll containers
  const scrollContainers = document.querySelectorAll(
    '.main-content, .main-content-wrapper, .library-view, .collections-view, .liked-tracks-view, .friends-view, .settings-view, .virtual-track-list, .virtual-grid, .page-scroll-container, .mobile-page-content'
  )
  scrollContainers.forEach((el) => {
    if (el && el.scrollTop > 0) {
      el.scrollTo({ top: 0, behavior: 'smooth' })
    }
  })

  // 3. Global window fallback
  window.scrollTo({ top: 0, behavior: 'smooth' })
  if (document.documentElement) {
    document.documentElement.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const handleNavClick = (path) => {
  const currentNav = props.navItems.find(i => i.path === path)
  const isCurrentActive = isActiveRoute(path, currentNav?.matchPaths || [path])

  if (isCurrentActive) {
    const mainContent = document.querySelector('.main-content')
    const currentScroll = mainContent ? mainContent.scrollTop : (window.scrollY || document.documentElement.scrollTop || 0)

    // Smoothly scroll to top
    scrollToTop()

    // If already at or near top (or user taps again at top), reset view state / filters
    if (currentScroll <= 30) {
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
  background: var(--c-bg-2);
  border-top: 2px solid var(--c-bg-4);
  padding-bottom: env(safe-area-inset-bottom);
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.08);
}

/* Player section */
.footer-player {
  background: var(--c-bg-1);
  padding: 8px 0;
}

/* Navigation */
.footer-nav {
  height: 72px;
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 8px 0;
  background: var(--c-bg-2);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-decoration: none;
  color: var(--c-text-3);
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
  color: var(--c-accent);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 32px;
  height: 3px;
  background: var(--c-accent);
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
