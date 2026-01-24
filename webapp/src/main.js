import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './style.css'

// Initialize Telegram WebApp
const tg = window.Telegram?.WebApp

// Update viewport CSS variables
function updateViewportHeight() {
  if (tg) {
    document.documentElement.style.setProperty('--tg-viewport-height', `${tg.viewportHeight}px`)
    document.documentElement.style.setProperty('--tg-viewport-stable-height', `${tg.viewportStableHeight}px`)
  }
}

if (tg) {
  tg.ready()
  tg.expand()
  
  // Apply Telegram theme initially
  updateViewportHeight()
  
  // Listen for viewport changes (when mini app is minimized/expanded)
  tg.onEvent('viewportChanged', ({ isStateStable }) => {
    updateViewportHeight()
    // Re-expand when viewport becomes stable after being minimized
    if (isStateStable && !tg.isExpanded) {
      tg.expand()
    }
  })
  
  // Also update on window resize for additional reliability
  window.addEventListener('resize', () => {
    requestAnimationFrame(updateViewportHeight)
  })
}

const app = createApp(App)
app.use(createPinia())

// Provide Telegram WebApp globally
app.provide('telegram', tg)

app.mount('#app')
