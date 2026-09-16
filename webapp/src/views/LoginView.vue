<template>
  <div class="login-view">
    <div class="login-container">
      <div class="logo">
        <Music :size="48" />
      </div>
      <h1>{{ appName }}</h1>
      <p class="subtitle">Музыкальный плеер с хранением в Telegram</p>

      <div v-if="!showCodeInput" class="auth-info">
        <p>Для входа отправьте команду <code>/code</code> боту</p>
        <a 
          :href="botLink" 
          target="_blank" 
          class="bot-link"
        >
          Открыть бота
        </a>
        <button class="primary-btn" @click="showCodeInput = true">
          У меня есть код
        </button>
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
              class="code-digit"
              :value="codeDigits[i]"
              @input="onCodeInput($event, i)"
              @keydown="onCodeKeydown($event, i)"
              @paste="onPaste"
            />
          </template>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button 
          class="primary-btn" 
          @click="verifyCode" 
          :disabled="loading || code.length !== 8"
        >
          {{ loading ? 'Проверка...' : 'Войти' }}
        </button>
        <button class="text-btn" @click="showCodeInput = false">
          Назад
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/client'
import { Music } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const showCodeInput = ref(false)
const codeInputs = ref([])
const codeDigits = ref(['', '', '', '', '', '', '', ''])
const loading = ref(false)
const error = ref('')
const appName = ref('TG Player')
const botUsername = ref('')

const botLink = computed(() => {
  return botUsername.value ? `https://t.me/${botUsername.value}` : 'https://t.me/your_bot_username'
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
    error.value = 'Неверный или истёкший код'
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

onMounted(async () => {
  // Load app config (bot username for display and link)
  try {
    const response = await authApi.getConfig()
    if (response.data?.bot_username) {
      appName.value = response.data.bot_username
      botUsername.value = response.data.bot_username
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
  if (urlCode && /^\d{6}$/.test(urlCode)) {
    showCodeInput.value = true
    for (let i = 0; i < 6; i++) {
      codeDigits.value[i] = urlCode[i]
    }
    nextTick(() => verifyCode())
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
  background: var(--c-bg-1);
}

.login-container {
  text-align: center;
  max-width: 360px;
  width: 100%;
}

.logo {
  font-size: 72px;
  margin-bottom: 16px;
}

h1 {
  font-size: 32px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0 0 8px 0;
}

.subtitle {
  color: var(--c-text-2);
  margin: 0 0 40px 0;
}

.auth-info p {
  color: var(--c-text-2);
  margin-bottom: 24px;
}

.auth-info code {
  background: var(--c-bg-3);
  padding: 4px 8px;
  border-radius: 4px;
  color: var(--c-accent);
}

.bot-link {
  display: block;
  padding: 14px 24px;
  background: var(--c-bg-3);
  border-radius: 12px;
  color: var(--c-accent);
  text-decoration: none;
  font-weight: 500;
  margin-bottom: 16px;
}

.bot-link:hover {
  background: var(--c-bg-4);
}

.primary-btn {
  width: 100%;
  padding: 14px 24px;
  background: var(--c-accent);
  border: none;
  border-radius: 12px;
  color: #000;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
}

.primary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.code-input-section p {
  color: var(--c-text-2);
  margin-bottom: 24px;
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
  background: var(--c-bg-3);
  border: 2px solid var(--c-bg-4);
  border-radius: 10px;
  color: var(--c-text-1);
  padding: 0;
}

.code-digit:focus {
  outline: none;
  border-color: var(--c-accent);
}

@media (max-width: 400px) {
  .code-inputs {
    gap: 4px;
  }
  .code-digit {
    width: 32px;
    height: 44px;
    font-size: 18px;
    border-radius: 8px;
  }
}

.error {
  color: var(--c-error);
  margin-bottom: 16px;
}

.text-btn {
  display: block;
  width: 100%;
  padding: 14px;
  background: transparent;
  border: none;
  color: var(--c-text-2);
  font-size: 15px;
  cursor: pointer;
  margin-top: 12px;
}

.text-btn:hover {
  color: var(--c-text-1);
}
</style>
