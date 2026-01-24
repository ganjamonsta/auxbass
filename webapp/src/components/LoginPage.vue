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
          <p>{{ loadingText }}</p>
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
            Для входа отправьте команду <code>/login</code> боту
            <a :href="telegramBotLink" target="_blank" class="bot-link">@{{ botUsername }}</a>
            и введите полученный код:
          </p>

          <!-- Code Input -->
          <div class="code-input-wrapper">
            <input
              ref="codeInput"
              v-model="authCode"
              type="text"
              inputmode="numeric"
              pattern="[0-9]*"
              maxlength="6"
              placeholder="000000"
              class="code-input"
              @keyup.enter="verifyCode"
              @input="onCodeInput"
            />
          </div>

          <button 
            @click="verifyCode" 
            :disabled="authCode.length !== 6 || verifying"
            class="verify-btn"
          >
            <span v-if="verifying" class="btn-spinner"></span>
            <span v-else>Войти</span>
          </button>

          <!-- Open bot link -->
          <div class="bot-hint">
            <a :href="telegramBotLink" target="_blank" class="open-bot-btn">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
              </svg>
              Получить код в боте
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
const loadingText = ref('Проверка авторизации...')
const error = ref(null)
const botUsername = ref('')
const authCode = ref('')
const verifying = ref(false)
const codeInput = ref(null)

const telegramBotLink = computed(() => {
  if (botUsername.value) {
    return `https://t.me/${botUsername.value}`
  }
  return 'https://t.me'
})

// Load auth config
onMounted(async () => {
  try {
    // Check if already authenticated
    if (authStorage.isAuthenticated()) {
      loadingText.value = 'Проверка сессии...'
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
    
    loading.value = false
  } catch (e) {
    console.error('Auth check failed:', e)
    loading.value = false
  }
})

const onCodeInput = (e) => {
  // Only allow digits
  authCode.value = e.target.value.replace(/\D/g, '').slice(0, 6)
}

const verifyCode = async () => {
  if (authCode.value.length !== 6 || verifying.value) return
  
  try {
    verifying.value = true
    error.value = null
    
    const response = await authApi.verifyCode({ code: authCode.value })
    
    if (response.data.valid && response.data.token) {
      authStorage.setToken(response.data.token)
      authStorage.setUser(response.data.user)
      emit('login', response.data.user)
    } else {
      error.value = 'Неверный код'
      verifying.value = false
    }
  } catch (e) {
    console.error('Code verification failed:', e)
    error.value = e.response?.data?.detail || 'Неверный или истёкший код'
    verifying.value = false
    authCode.value = ''
  }
}

const retry = () => {
  error.value = null
  authCode.value = ''
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
  line-height: 1.6;
  text-align: center;
}

.login-info code {
  background: rgba(29, 185, 84, 0.2);
  color: #1DB954;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 14px;
}

.bot-link {
  color: #1DB954;
  text-decoration: none;
  font-weight: 600;
}

.bot-link:hover {
  text-decoration: underline;
}

.code-input-wrapper {
  display: flex;
  justify-content: center;
}

.code-input {
  width: 200px;
  padding: 16px 24px;
  font-size: 32px;
  font-weight: 700;
  font-family: monospace;
  text-align: center;
  letter-spacing: 8px;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  outline: none;
  transition: all 0.2s;
}

.code-input:focus {
  border-color: #1DB954;
  background: rgba(29, 185, 84, 0.1);
}

.code-input::placeholder {
  color: rgba(255, 255, 255, 0.3);
  letter-spacing: 8px;
}

.verify-btn {
  background: #1DB954;
  color: white;
  border: none;
  padding: 14px 32px;
  border-radius: 28px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 0 auto;
  min-width: 120px;
}

.verify-btn:hover:not(:disabled) {
  background: #1ed760;
  transform: scale(1.02);
}

.verify-btn:disabled {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.3);
  cursor: not-allowed;
}

.btn-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.bot-hint {
  display: flex;
  justify-content: center;
  padding-top: 8px;
}

.open-bot-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s;
}

.open-bot-btn:hover {
  color: #1DB954;
}

.open-bot-btn svg {
  opacity: 0.8;
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
</style>
