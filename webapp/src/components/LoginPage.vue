<template>
  <div class="login-page">
    <div class="login-container">
      <!-- Logo / Brand -->
      <div class="login-header">
        <div class="logo">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
          </svg>
        </div>
        <h1 class="app-name">TG Player</h1>
        <p class="tagline">Музыкальный плеер для Telegram</p>
      </div>

      <!-- Login Content -->
      <div class="login-content">
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>Проверка авторизации...</p>
        </div>

        <div v-else-if="error" class="error-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
          </svg>
          <p>{{ error }}</p>
          <button @click="retry" class="retry-btn">Попробовать снова</button>
        </div>

        <div v-else class="login-options">
          <p class="login-info">
            Войдите через Telegram, чтобы получить доступ к своей музыке
          </p>

          <!-- Telegram Login Widget Container -->
          <div ref="telegramLoginContainer" class="telegram-login-container">
            <!-- Widget will be injected here -->
          </div>

          <div v-if="!botUsername" class="no-widget-fallback">
            <p class="fallback-text">
              Для авторизации откройте приложение через
              <a href="https://t.me/your_bot" target="_blank" class="tg-link">
                Telegram бота
              </a>
            </p>
          </div>

          <!-- Alternative: Open in Telegram -->
          <div class="alternative-login">
            <span class="divider-text">или</span>
            <a :href="telegramBotLink" class="open-telegram-btn">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
              </svg>
              Открыть в Telegram
            </a>
          </div>
        </div>
      </div>

      <!-- Features Preview -->
      <div class="features">
        <div class="feature">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
          </svg>
          <span>Стриминг музыки</span>
        </div>
        <div class="feature">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 12.5v-9l6 4.5-6 4.5z"/>
          </svg>
          <span>Плейлисты</span>
        </div>
        <div class="feature">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
          </svg>
          <span>Глобальная библиотека</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { authApi, authStorage } from '../api/client'

const emit = defineEmits(['login'])

const loading = ref(true)
const error = ref(null)
const botUsername = ref('')
const telegramLoginContainer = ref(null)

const telegramBotLink = computed(() => {
  if (botUsername.value) {
    return `https://t.me/${botUsername.value}`
  }
  return 'https://t.me'
})

// Load auth config and setup Telegram Login Widget
onMounted(async () => {
  try {
    // Check if already authenticated
    if (authStorage.isAuthenticated()) {
      // Validate the existing auth
      const response = await authApi.validate()
      if (response.data.valid) {
        if (response.data.token) {
          authStorage.setToken(response.data.token)
        }
        if (response.data.user) {
          authStorage.setUser(response.data.user)
        }
        emit('login', response.data.user)
        return
      }
    }
    
    // Get auth config
    const configResponse = await authApi.getConfig()
    botUsername.value = configResponse.data.bot_username
    
    // Setup Telegram Login Widget
    if (botUsername.value && telegramLoginContainer.value) {
      setupTelegramWidget()
    }
    
    loading.value = false
  } catch (e) {
    console.error('Auth check failed:', e)
    loading.value = false
  }
})

const setupTelegramWidget = () => {
  // Create callback function for Telegram Login
  window.onTelegramAuth = async (user) => {
    try {
      loading.value = true
      error.value = null
      
      // Send login data to backend
      const response = await authApi.telegramLogin(user)
      
      if (response.data.valid && response.data.token) {
        authStorage.setToken(response.data.token)
        authStorage.setUser(response.data.user)
        emit('login', response.data.user)
      } else {
        error.value = 'Ошибка авторизации'
        loading.value = false
      }
    } catch (e) {
      console.error('Telegram login failed:', e)
      error.value = 'Ошибка авторизации: ' + (e.response?.data?.detail || e.message)
      loading.value = false
    }
  }
  
  // Create and inject the Telegram Login Widget script
  const script = document.createElement('script')
  script.src = 'https://telegram.org/js/telegram-widget.js?22'
  script.setAttribute('data-telegram-login', botUsername.value)
  script.setAttribute('data-size', 'large')
  script.setAttribute('data-radius', '8')
  script.setAttribute('data-onauth', 'onTelegramAuth(user)')
  script.setAttribute('data-request-access', 'write')
  script.async = true
  
  telegramLoginContainer.value.appendChild(script)
}

const retry = () => {
  error.value = null
  loading.value = true
  location.reload()
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 20px;
}

.login-container {
  max-width: 400px;
  width: 100%;
  text-align: center;
}

.login-header {
  margin-bottom: 40px;
}

.logo {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #1DB954, #1ed760);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  color: white;
  box-shadow: 0 8px 32px rgba(29, 185, 84, 0.3);
}

.app-name {
  font-size: 32px;
  font-weight: 700;
  color: white;
  margin: 0 0 8px;
}

.tagline {
  color: rgba(255, 255, 255, 0.6);
  font-size: 16px;
  margin: 0;
}

.login-content {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 32px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 32px;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: rgba(255, 255, 255, 0.8);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #1DB954;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state svg {
  color: #ff6b6b;
}

.retry-btn {
  background: #1DB954;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: #1ed760;
  transform: scale(1.02);
}

.login-options {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.login-info {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  margin: 0;
  line-height: 1.5;
}

.telegram-login-container {
  display: flex;
  justify-content: center;
  min-height: 50px;
}

.no-widget-fallback {
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.tg-link {
  color: #1DB954;
  text-decoration: none;
}

.tg-link:hover {
  text-decoration: underline;
}

.alternative-login {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.divider-text {
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.open-telegram-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #0088cc;
  color: white;
  text-decoration: none;
  padding: 14px 28px;
  border-radius: 28px;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.2s;
}

.open-telegram-btn:hover {
  background: #0099dd;
  transform: scale(1.02);
}

.features {
  display: flex;
  justify-content: center;
  gap: 24px;
  flex-wrap: wrap;
}

.feature {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}

.feature svg {
  opacity: 0.6;
}

/* Dark theme for Telegram widget */
:deep(iframe) {
  color-scheme: dark;
}
</style>
