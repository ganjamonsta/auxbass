import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './style.css'

// Initialize Telegram WebApp
const tg = window.Telegram?.WebApp

if (tg) {
  tg.ready()
  tg.expand()
  
  // Apply Telegram theme
  document.documentElement.style.setProperty('--tg-viewport-height', `${tg.viewportHeight}px`)
  document.documentElement.style.setProperty('--tg-viewport-stable-height', `${tg.viewportStableHeight}px`)
}

const app = createApp(App)
app.use(createPinia())

// Provide Telegram WebApp globally
app.provide('telegram', tg)

app.mount('#app')
