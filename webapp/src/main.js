import { createApp } from 'vue'
import { createPinia, setActivePinia } from 'pinia'

const pinia = createPinia()
setActivePinia(pinia)

import App from './App.vue'
import router from './router'
import './style.css'
import './styles/index.css'

// Initialize Telegram WebApp
const tg = window.Telegram?.WebApp

// Update viewport CSS variables smoothly without layout thrashing
function updateViewportHeight() {
  if (tg) {
    const vh = tg.viewportHeight
    const svh = tg.viewportStableHeight
    
    if (vh) {
      document.documentElement.style.setProperty('--tg-viewport-height', `${vh}px`)
    }
    if (svh) {
      document.documentElement.style.setProperty('--tg-viewport-stable-height', `${svh}px`)
    }
  }
}

if (tg) {
  tg.ready()
  tg.expand()
  
  // Disable native vertical swipe down to prevent closing the Mini App while scrolling or using in-app pull-to-refresh
  if (typeof tg.disableVerticalSwipes === 'function') {
    try {
      tg.disableVerticalSwipes()
    } catch (_) {}
  }
  
  // Enable closing confirmation so accidental gestures don't abruptly close the app and stop playback
  if (typeof tg.enableClosingConfirmation === 'function') {
    try {
      tg.enableClosingConfirmation()
    } catch (_) {}
  }
  
  // Apply Telegram theme initially
  updateViewportHeight()
  
  // Listen for viewport changes (when mini app is minimized/expanded)
  tg.onEvent('viewportChanged', ({ isStateStable }) => {
    updateViewportHeight()
    // Re-expand when viewport becomes stable after being minimized
    if (isStateStable) {
      if (!tg.isExpanded) {
        tg.expand()
      }
      // Additional delayed update for stable state
      setTimeout(updateViewportHeight, 100)
    }
  })
  
  // Also update on window resize for additional reliability
  window.addEventListener('resize', () => {
    requestAnimationFrame(updateViewportHeight)
  })
  
  // Handle visibility change (when app comes back to foreground)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      setTimeout(() => {
        tg.expand()
        updateViewportHeight()
      }, 50)
    }
  })
}

import longpress from './directives/longpress'

const app = createApp(App)
app.use(pinia)
app.use(router)
app.directive('longpress', longpress)

// Provide Telegram WebApp globally
app.provide('telegram', tg)

app.mount('#app')
