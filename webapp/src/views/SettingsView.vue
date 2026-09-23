<template>
  <div class="settings-view">
    <div class="settings-header">
      <h1>Настройки</h1>
    </div>

    <SettingsChannel />
    <SettingsSoundCloud />
    <SettingsSpotify />
    <SettingsDiscord />
    <SettingsPrivacy />
    <SettingsPlayback />
    <SettingsAppearance />
    <SettingsAbout />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useUIStore } from '@/stores/ui'

import SettingsChannel from './settings/SettingsChannel.vue'
import SettingsSoundCloud from './settings/SettingsSoundCloud.vue'
import SettingsSpotify from './settings/SettingsSpotify.vue'
import SettingsDiscord from './settings/SettingsDiscord.vue'
import SettingsPrivacy from './settings/SettingsPrivacy.vue'
import SettingsPlayback from './settings/SettingsPlayback.vue'
import SettingsAppearance from './settings/SettingsAppearance.vue'
import SettingsAbout from './settings/SettingsAbout.vue'

const route = useRoute()
const uiStore = useUIStore()

let detectedScrollContainer = null
let scrollTicking = false

const findScrollContainer = (el) => {
  let parent = el?.parentElement
  while (parent) {
    const style = window.getComputedStyle(parent)
    if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
      return parent
    }
    parent = parent.parentElement
  }
  return window
}

const checkSectionFromHash = () => {
  const hash = route.hash ? route.hash.replace('#', '') : (route.query.section || '')
  if (['profile', 'stats', 'notifications', 'interface', 'playback', 'storage', 'cache', 'about'].includes(hash)) {
    uiStore.setSettingsSection('settings')
  } else if (['channel', 'soundcloud', 'import', 'discord'].includes(hash)) {
    uiStore.setSettingsSection('import')
  }
}

const updateActiveSectionOnScroll = () => {
  const profileEl = document.getElementById('profile')
  if (!profileEl) return

  if (!detectedScrollContainer) {
    detectedScrollContainer = findScrollContainer(profileEl)
  }

  const isWindow = detectedScrollContainer === window || !detectedScrollContainer
  const containerTop = isWindow ? 0 : detectedScrollContainer.getBoundingClientRect().top
  const containerHeight = isWindow ? window.innerHeight : detectedScrollContainer.clientHeight
  const currentScrollTop = isWindow 
    ? (window.scrollY || document.documentElement.scrollTop) 
    : detectedScrollContainer.scrollTop

  // If near the very top of the page, import/integrations section is always active
  if (currentScrollTop < 60) {
    uiStore.setSettingsSection('import')
    return
  }

  const profileRect = profileEl.getBoundingClientRect()
  const profileTopRelativeToContainer = profileRect.top - containerTop

  // Threshold: when profile section reaches the upper portion of the viewport (<= 220px from container top or 35% of container height)
  const threshold = Math.min(220, containerHeight * 0.35)

  if (profileTopRelativeToContainer <= threshold) {
    uiStore.setSettingsSection('settings')
  } else {
    uiStore.setSettingsSection('import')
  }
}

const onScroll = () => {
  if (!scrollTicking) {
    requestAnimationFrame(() => {
      updateActiveSectionOnScroll()
      scrollTicking = false
    })
    scrollTicking = true
  }
}

const handleResetState = (event) => {
  if (event.detail.route === '/settings') {
    const container = detectedScrollContainer || findScrollContainer(document.querySelector('.settings-view'))
    if (container && container !== window) {
      container.scrollTo({ top: 0, behavior: 'smooth' })
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
    uiStore.setSettingsSection('import')
  }
}

watch([() => route.hash, () => route.query.section], () => {
  checkSectionFromHash()
  const target = route.query.section || (route.hash ? route.hash.replace('#', '') : null)
  if (target) {
    const el = document.getElementById(target)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      if (target !== 'profile') {
        el.classList.add('section-highlight')
        setTimeout(() => el.classList.remove('section-highlight'), 2200)
      }
    }
  } else {
    const container = detectedScrollContainer || findScrollContainer(document.querySelector('.settings-view'))
    if (container && container !== window) {
      container.scrollTo({ top: 0, behavior: 'smooth' })
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }
  setTimeout(updateActiveSectionOnScroll, 300)
})

onMounted(() => {
  const scrollToTargetSection = () => {
    const target = route.query.section || (route.hash ? route.hash.replace('#', '') : null)
    if (target) {
      setTimeout(() => {
        const el = document.getElementById(target)
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' })
          if (target !== 'profile') {
            el.classList.add('section-highlight')
            setTimeout(() => el.classList.remove('section-highlight'), 2200)
          }
        }
      }, 150)
    } else {
      const container = detectedScrollContainer || findScrollContainer(document.querySelector('.settings-view'))
      if (container && container !== window) {
        container.scrollTo({ top: 0, behavior: 'instant' })
      } else {
        window.scrollTo({ top: 0, behavior: 'instant' })
      }
    }
  }

  scrollToTargetSection()
  window.addEventListener('reset-view-state', handleResetState)

  nextTick(() => {
    checkSectionFromHash()
    const targetEl = document.getElementById('profile') || document.querySelector('.settings-view')
    detectedScrollContainer = findScrollContainer(targetEl)
    if (detectedScrollContainer && detectedScrollContainer !== window) {
      detectedScrollContainer.addEventListener('scroll', onScroll, { passive: true })
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll, { passive: true })

    setTimeout(() => {
      updateActiveSectionOnScroll()
    }, 200)
  })
})

onUnmounted(() => {
  if (detectedScrollContainer && detectedScrollContainer !== window) {
    detectedScrollContainer.removeEventListener('scroll', onScroll)
  }
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', onScroll)
  window.removeEventListener('reset-view-state', handleResetState)
})
</script>

<style scoped>
.settings-view {
  padding: var(--sp-6) var(--sp-4) var(--sp-12);
  max-width: 680px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.settings-header {
  margin-bottom: var(--sp-5);
}

.settings-header h1 {
  font-size: 26px;
  font-weight: 700;
  color: var(--c-text-1);
  letter-spacing: -0.5px;
  margin: 0;
  line-height: 1.2;
}

@media (max-width: 540px) {
  .settings-view {
    padding: var(--sp-4) 12px 100px;
  }
}
</style>
