<template>
  <div class="mobile-footer" :class="footerClasses" :style="footerStyle">
    <!-- Bottom Navigation / Player Controls hybrid -->
    <nav class="footer-nav">
      <button
        v-for="(item, idx) in navItems"
        :key="item.path"
        class="nav-item"
        :class="{
          active: !playerExpanded && isActiveRoute(item.path, item.matchPaths),
          'control-active': playerExpanded && controlItems[idx]?.isActive,
        }"
        @click="handleItemClick(idx, item)"
      >
        <!-- Nav icon layer (fades out when expanded) -->
        <div class="nav-layer">
          <component :is="item.icon" class="nav-icon" :size="22" :stroke-width="2" />
          <span class="nav-label">{{ item.label }}</span>
        </div>
        <!-- Player control layer (fades in when expanded) -->
        <div class="control-layer">
          <component
            v-if="controlItems[idx]"
            :is="controlItems[idx].iconComponent"
            class="control-icon"
            :size="controlItems[idx].size || 24"
            :stroke-width="2"
          />
          <span class="control-label">{{ controlItems[idx]?.label || '' }}</span>
        </div>
      </button>
    </nav>
  </div>
</template>

<script setup>
import { computed, h, defineComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ListMusic, Disc3, Users, Heart, Settings, SkipBack, Shuffle, Play, Pause, Repeat, Repeat1, SkipForward } from 'lucide-vue-next'

const props = defineProps({
  showPlayer: { type: Boolean, default: false },
  currentTrack: { type: Object, default: null },
  isPlaying: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  playerExpanded: { type: Boolean, default: false },
  expandProgress: { type: Number, default: 0 },
  shuffle: { type: Boolean, default: false },
  repeat: { type: String, default: 'none' },
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
  'toggle-play',
  'next-track',
  'prev-track',
  'toggle-shuffle',
  'toggle-repeat',
  'nav-click',
  'reset-view',
])

const route = useRoute()
const router = useRouter()

const footerClasses = computed(() => ({
  'footer--player-expanded': props.playerExpanded,
}))

const footerStyle = computed(() => ({
  '--expand': props.expandProgress,
}))

// Loading spinner as component
const SpinnerIcon = defineComponent({
  props: { size: { type: Number, default: 24 }, strokeWidth: { type: Number, default: 2 } },
  setup(props) {
    return () => h('svg', {
      class: 'spin',
      width: props.size, height: props.size,
      viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor',
      'stroke-width': props.strokeWidth,
    }, [
      h('path', { d: 'M12 2a10 10 0 0 1 10 10' })
    ])
  }
})

// Map nav positions to player controls
const controlItems = computed(() => {
  const playIcon = props.loading ? SpinnerIcon : (props.isPlaying ? Pause : Play)

  return [
    { iconComponent: SkipBack, label: 'Назад', action: 'prev', size: 22, isActive: false },
    { iconComponent: Shuffle, label: 'Шафл', action: 'shuffle', size: 20, isActive: props.shuffle },
    { iconComponent: playIcon, label: props.isPlaying ? 'Пауза' : 'Играть', action: 'toggle', size: 28, isActive: props.isPlaying, isPlayBtn: true },
    { iconComponent: props.repeat === 'one' ? Repeat1 : Repeat, label: 'Повтор', action: 'repeat', size: 20, isActive: props.repeat !== 'none' },
    { iconComponent: SkipForward, label: 'Далее', action: 'next', size: 22, isActive: false },
  ]
})

const isActiveRoute = (path, matchPaths = []) => {
  if (path === '/') return route.path === '/'
  return matchPaths.some(p => route.path.startsWith(p))
}

const scrollToTop = () => {
  const mainContent = document.querySelector('.main-content')
  if (mainContent) mainContent.scrollTo({ top: 0, behavior: 'smooth' })
  const scrollContainers = document.querySelectorAll(
    '.main-content, .main-content-wrapper, .library-view, .collections-view, .liked-tracks-view, .friends-view, .settings-view, .virtual-track-list, .virtual-grid, .page-scroll-container, .mobile-page-content'
  )
  scrollContainers.forEach((el) => {
    if (el && el.scrollTop > 0) el.scrollTo({ top: 0, behavior: 'smooth' })
  })
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const handleItemClick = (idx, navItem) => {
  if (props.playerExpanded) {
    // Player controls mode
    const control = controlItems.value[idx]
    if (!control) return
    switch (control.action) {
      case 'prev': emit('prev-track'); break
      case 'shuffle': emit('toggle-shuffle'); break
      case 'toggle': emit('toggle-play'); break
      case 'repeat': emit('toggle-repeat'); break
      case 'next': emit('next-track'); break
    }
    return
  }

  // Navigation mode
  const currentNav = props.navItems.find(i => i.path === navItem.path)
  const isCurrentActive = isActiveRoute(navItem.path, currentNav?.matchPaths || [navItem.path])

  if (isCurrentActive) {
    const mainContent = document.querySelector('.main-content')
    const currentScroll = mainContent ? mainContent.scrollTop : 0
    scrollToTop()
    if (currentScroll <= 30) {
      emit('reset-view', navItem.path)
      window.dispatchEvent(new CustomEvent('reset-view-state', { detail: { route: navItem.path } }))
    }
  } else {
    emit('nav-click', navItem.path)
    router.push(navItem.path)
  }
}
</script>

<style scoped>
.mobile-footer {
  flex-shrink: 0;
  z-index: var(--z-overlay, 100);
  background: rgba(14, 18, 24, 0.85);
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: env(safe-area-inset-bottom);
  box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.45);
}

/* When player is expanded, style differently */
.footer--player-expanded {
  background: rgba(10, 12, 16, 0.95);
  border-top-color: rgba(255, 255, 255, 0.06);
}

/* Navigation */
.footer-nav {
  height: 64px;
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 4px 0;
  background: transparent;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
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
  /* Stack nav and control layers */
  overflow: hidden;
}

/* Active route indicator (nav mode only) */
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

/* Active control indicator (player mode) */
.nav-item.control-active {
  color: var(--c-accent);
}

.nav-item:active {
  transform: scale(0.95);
  opacity: 0.7;
}

/* ─── Layer Crossfade ─── */
.nav-layer,
.control-layer {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: opacity 0.3s ease, transform 0.3s ease;
  position: absolute;
  inset: 0;
  padding: 8px 0;
}

.nav-layer {
  opacity: calc(1 - var(--expand, 0));
  transform: translateY(calc(var(--expand, 0) * -8px));
  pointer-events: auto;
}

.control-layer {
  opacity: calc(var(--expand, 0));
  transform: translateY(calc((1 - var(--expand, 0)) * 8px));
  pointer-events: auto;
}

.footer--player-expanded .nav-layer {
  pointer-events: none;
}

:not(.footer--player-expanded) .control-layer {
  pointer-events: none;
}

.nav-icon, .control-icon {
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.nav-item.active .nav-icon {
  transform: translateY(-2px);
}

.nav-label, .control-label {
  font-weight: 500;
  letter-spacing: 0.02em;
  font-size: 10px;
}

/* ─── Play button highlight (center position) ─── */
.footer--player-expanded .nav-item:nth-child(3) {
  color: var(--c-text-1);
}

.footer--player-expanded .nav-item:nth-child(3) .control-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(145deg, #22e066 0%, #159b43 100%);
  color: #000;
  border-radius: var(--r-full);
  padding: 10px;
  box-shadow:
    0 4px 16px rgba(29, 185, 84, 0.4),
    inset 0 1px 1px rgba(255, 255, 255, 0.4);
  transform: translateY(-4px);
}

.footer--player-expanded .nav-item:nth-child(3):active .control-icon {
  transform: translateY(-4px) scale(0.92);
  box-shadow:
    inset 3px 3px 6px rgba(0, 0, 0, 0.5),
    0 0 12px var(--c-accent-glow);
}

.footer--player-expanded .nav-item:nth-child(3) .control-label {
  display: none;
}

/* Desktop: hide mobile footer */
@media (min-width: 1024px) {
  .mobile-footer {
    display: none;
  }
}

/* Spinner */
.spin { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
