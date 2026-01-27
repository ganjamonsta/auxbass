import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'
import './styles/index.css'

// Initialize Telegram WebApp
const tg = window.Telegram?.WebApp

// Update viewport CSS variables and force layout recalculation
function updateViewportHeight() {
  if (tg) {
    const vh = tg.viewportHeight
    const svh = tg.viewportStableHeight
    
    document.documentElement.style.setProperty('--tg-viewport-height', `${vh}px`)
    document.documentElement.style.setProperty('--tg-viewport-stable-height', `${svh}px`)
    
    // Force layout recalculation by temporarily hiding and showing content
    const appEl = document.getElementById('app')
    if (appEl) {
      // Trigger reflow
      appEl.style.display = 'none'
      void appEl.offsetHeight // Force reflow
      appEl.style.display = ''
    }
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

const app = createApp(App)
app.use(createPinia())
app.use(router)

// Provide Telegram WebApp globally
app.provide('telegram', tg)

app.mount('#app')
