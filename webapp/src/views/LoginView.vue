<template>
  <div class="login-view">
    <div class="login-container neu-card">
      <div class="logo">
        <div class="logo-icon-wrap neu-well">
          <Music :size="40" class="logo-music" />
        </div>
      </div>
      <h1>{{ appName }}</h1>
      <p class="subtitle">Музыкальный плеер с хранением в Telegram</p>

      <div v-if="!showCodeInput" class="auth-info">
        <p>Для входа отправьте команду <code>/code</code> боту</p>
        <a 
          v-if="botUsername && botLink !== '#'" 
          :href="botLink" 
          target="_blank" 
          class="bot-link neu-btn-rubber"
        >
          Открыть бота @{{ botUsername }}
        </a>
        <div v-else class="bot-link neu-btn-rubber disabled-link">
          Открыть бота
        </div>
        <button class="primary-btn neu-btn-primary" @click="showCodeInput = true">
          У меня есть код
        </button>

        <div v-if="isDev" class="dev-section">
          <div class="dev-divider">
            <span>Режим разработки</span>
          </div>
          <button class="dev-btn neu-btn-rubber" :disabled="loading" @click="handleDevLogin">
            <Zap :size="18" class="dev-icon" />
            <span>{{ loading ? 'Вход...' : 'Быстрый вход (Dev Mode)' }}</span>
          </button>
          <div class="dev-hint">Вход как тестовый пользователь без Telegram</div>
        </div>
      </div>

      <div v-else class="code-input-section">
        <p>Введите 8-значный код из бота:</p>
        <div class="code-inputs">
          <template v-for="(_, i) in 8" :key="i">
            <span v-if="i === 4" class="code-divider">—</span>
            <input
              ref="codeInputs"
              type="text"
              maxlength="1"
              pattern="[0-9]"
              inputmode="numeric"
              class="code-digit neu-input"
              :value="codeDigits[i]"
              @input="onCodeInput($event, i)"
              @keydown="onCodeKeydown($event, i)"
              @paste="onPaste"
            />
          </template>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button 
          class="primary-btn neu-btn-primary" 
          @click="verifyCode" 
          :disabled="loading || code.length !== 8"
        >
          {{ loading ? 'Проверка...' : 'Войти' }}
        </button>
        <button class="text-btn" @click="showCodeInput = false">
          Назад
        </button>

        <div v-if="isDev" class="dev-section dev-section-sub">
          <button class="dev-btn neu-btn-rubber" :disabled="loading" @click="handleDevLogin">
            <Zap :size="16" class="dev-icon" />
            <span>Быстрый вход (Dev Mode)</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/client'
import { Music, Zap } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isDev = computed(() => import.meta.env.DEV)

const showCodeInput = ref(false)
const codeInputs = ref([])
const codeDigits = ref(['', '', '', '', '', '', '', ''])
const loading = ref(false)
const error = ref('')
const appName = ref('TG Player')
const botUsername = ref('')

const isCleanBotUsername = (username) => {
  if (!username) return false
  const lower = String(username).trim().toLowerCase()
  return !lower.includes('your_bot') && !lower.includes('enter_') && lower !== 'tg_player_bot'
}

const botLink = computed(() => {
  return isCleanBotUsername(botUsername.value) ? `https://t.me/${botUsername.value.trim().replace(/^@/, '')}` : '#'
})

const code = computed(() => codeDigits.value.join(''))

const onCodeInput = async (event, index) => {
  const value = event.target.value
  
  // Only allow digits
  if (!/^\d*$/.test(value)) {
    event.target.value = ''
    return
  }

  codeDigits.value[index] = value

  // Move to next input
  if (value && index < 7) {
    await nextTick()
    codeInputs.value[index + 1]?.focus()
  }

  // Auto-submit when all 8 digits entered
  if (code.value.length === 8) {
    verifyCode()
  }
}

const onCodeKeydown = (event, index) => {
  // Handle backspace navigation
  if (event.key === 'Backspace') {
    if (!codeDigits.value[index] && index > 0) {
      codeDigits.value[index - 1] = ''
      codeInputs.value[index - 1]?.focus()
    } else {
      codeDigits.value[index] = ''
    }
  }
}

const onPaste = async (event) => {
  event.preventDefault()
  // Clean pasted string: allow digits even if copied with spaces or dashes (e.g. 1234-5678)
  const pastedData = event.clipboardData.getData('text').replace(/\D/g, '')
  
  if (pastedData.length >= 8) {
    for (let i = 0; i < 8; i++) {
      codeDigits.value[i] = pastedData[i]
      if (codeInputs.value[i]) {
        codeInputs.value[i].value = pastedData[i]
      }
    }
    await nextTick()
    verifyCode()
  }
}

const verifyCode = async () => {
  if (code.value.length !== 8 || loading.value) return
  
  loading.value = true
  error.value = ''
  
  try {
    await authStore.loginWithCode(code.value)
    
    // Use window.location for a cleaner transition after login
    // to ensure all stores are properly initialized with new user data
    const redirect = route.query.redirect || '/'
    window.location.href = redirect
  } catch (err) {
    const serverDetail = err.response?.data?.detail
    if (typeof serverDetail === 'string') {
      error.value = serverDetail
    } else {
      error.value = 'Неверный или истёкший код'
    }
    // Clear inputs
    codeDigits.value = ['', '', '', '', '', '', '', '']
    codeInputs.value.forEach(input => {
      if (input) input.value = ''
    })
    codeInputs.value[0]?.focus()
  } finally {
    loading.value = false
  }
}

const handleDevLogin = async () => {
  loading.value = true
  error.value = ''
  try {
    await authStore.devLogin()
    const redirect = route.query.redirect || '/'
    window.location.href = redirect
  } catch (err) {
    error.value = 'Ошибка тестового входа'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  // Check if already authenticated
  if (authStore.isAuthenticated) {
    router.push('/')
    return
  }

  // Auto-login in development if ?dev=1 or ?dev=true is present
  if (isDev.value && (route.query.dev === '1' || route.query.dev === 'true')) {
    handleDevLogin()
    return
  }
  // Load app config (bot username for display and link)
  try {
    const response = await authApi.getConfig()
    const raw = response.data?.bot_username
    if (isCleanBotUsername(raw)) {
      const clean = raw.trim().replace(/^@/, '')
      appName.value = clean
      botUsername.value = clean
    }
  } catch (err) {
    console.error('Failed to load config:', err)
  }
  
  // Check if already authenticated
  if (authStore.isAuthenticated) {
    router.push('/')
  }
  
  // Check for code in URL (from deep link)
  const urlCode = route.query.code
  if (urlCode && /^\d{6,8}$/.test(urlCode)) {
    showCodeInput.value = true
    for (let i = 0; i < urlCode.length && i < 8; i++) {
      codeDigits.value[i] = urlCode[i]
    }
    if (urlCode.length === 8) {
      nextTick(() => verifyCode())
    }
  }
})
</script>

<style scoped>
.login-view {
  height: 100%;
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--c-bg-0);
}

.login-container {
  text-align: center;
  max-width: 400px;
  width: 100%;
  padding: 36px 28px;
  border-radius: var(--r-xl);
}

.logo {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.logo-icon-wrap {
  width: 76px;
  height: 76px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-accent);
}

.logo-music {
  filter: drop-shadow(0 0 10px var(--c-accent-glow));
}

h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

.subtitle {
  color: var(--c-text-2);
  margin: 0 0 28px 0;
  font-size: 14px;
}

.auth-info p {
  color: var(--c-text-2);
  margin-bottom: 20px;
  font-size: 14px;
}

.auth-info code {
  background: var(--c-bg-1);
  padding: 3px 8px;
  border-radius: 6px;
  color: var(--c-accent);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.bot-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 13px 20px;
  color: var(--c-accent);
  text-decoration: none;
  font-weight: 500;
  font-size: 15px;
  margin-bottom: 14px;
}

.bot-link.disabled-link {
  opacity: 0.5;
  cursor: default;
}

.primary-btn {
  width: 100%;
  padding: 14px 20px;
  font-weight: 600;
  font-size: 15px;
  cursor: pointer;
}

.dev-section {
  margin-top: 28px;
}

.dev-section-sub {
  margin-top: 18px;
}

.dev-divider {
  display: flex;
  align-items: center;
  text-align: center;
  color: var(--c-text-3);
  font-size: 12px;
  margin-bottom: 16px;
}

.dev-divider::before,
.dev-divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.dev-divider span {
  padding: 0 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.dev-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 13px 20px;
  color: var(--c-secondary);
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  border: 1px solid rgba(0, 188, 212, 0.25);
  background: var(--c-bg-2);
}

.dev-btn:hover {
  border-color: rgba(0, 188, 212, 0.5);
  box-shadow: 0 0 14px rgba(0, 188, 212, 0.3);
}

.dev-icon {
  color: var(--c-secondary);
  filter: drop-shadow(0 0 6px rgba(0, 188, 212, 0.5));
}

.dev-hint {
  font-size: 11px;
  color: var(--c-text-3);
  margin-top: 8px;
}

.code-input-section p {
  color: var(--c-text-2);
  margin-bottom: 24px;
  font-size: 14px;
}

.code-inputs {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  margin-bottom: 24px;
}

.code-divider {
  color: var(--c-text-2);
  font-size: 18px;
  font-weight: 600;
  user-select: none;
  padding: 0 2px;
}

.code-digit {
  width: 36px;
  height: 48px;
  text-align: center;
  font-size: 20px;
  font-weight: 600;
  padding: 0;
}

@media (max-width: 400px) {
  .code-inputs {
    gap: 4px;
  }
  .code-digit {
    width: 32px;
    height: 44px;
    font-size: 18px;
  }
}

.error {
  color: var(--c-error);
  margin-bottom: 16px;
  font-size: 14px;
}

.text-btn {
  display: block;
  width: 100%;
  padding: 12px;
  background: transparent;
  border: none;
  color: var(--c-text-2);
  font-size: 14px;
  cursor: pointer;
  margin-top: 12px;
  transition: color 0.15s ease;
}

.text-btn:hover {
  color: var(--c-text-1);
}
</style>
