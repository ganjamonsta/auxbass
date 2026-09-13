<template>
  <Teleport to="body">
    <Transition name="offline-fade">
      <div 
        v-if="shouldShowOverlay" 
        class="offline-overlay"
        :class="{ 'is-minimized': isMinimized }"
      >
        <!-- Minimized Bar (when user browses /downloaded or explicitly minimized) -->
        <div v-if="isMinimized" class="offline-minimized-bar" @click="isMinimized = false">
          <div class="status-indicator-mini pulse-warning"></div>
          <span class="mini-text">{{ currentTitle }}</span>
          <span class="mini-retry-timer">({{ countdown }}с)</span>
          <button class="mini-expand-btn" title="Подробнее">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="18 15 12 9 6 15" />
            </svg>
          </button>
        </div>

        <!-- Fullscreen Dialog Card -->
        <div v-else class="offline-modal-card">
          <!-- Close/Minimize button if offline tracks are available or already on /downloaded -->
          <button 
            v-if="canMinimize" 
            class="modal-close-btn" 
            @click="isMinimized = true"
            title="Свернуть и слушать оффлайн"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>

          <!-- Animated Pulse Icon -->
          <div class="offline-icon-wrapper">
            <div class="pulse-ring"></div>
            <div class="offline-icon-badge" :class="iconBadgeClass">
              <!-- Maintenance gear icon -->
              <svg v-if="isMaintenance" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="gear-spin">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>

              <!-- Bot offline icon -->
              <svg v-else-if="!isBotOnline && !isBackendDown" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="10" rx="2" />
                <circle cx="12" cy="5" r="2" />
                <path d="M12 7v4" />
                <line x1="8" y1="16" x2="8.01" y2="16" />
                <line x1="16" y1="16" x2="16.01" y2="16" />
              </svg>

              <!-- Server unreachable / Network down icon -->
              <svg v-else width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="1" y1="1" x2="23" y2="23" />
                <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55" />
                <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39" />
                <path d="M10.71 5.05A16 16 0 0 1 22.56 9" />
                <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88" />
                <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
                <line x1="12" y1="20" x2="12.01" y2="20" />
              </svg>
            </div>
          </div>

          <!-- Status badge -->
          <div class="status-pill" :class="statusPillClass">
            <span class="status-dot"></span>
            {{ statusPillText }}
          </div>

          <!-- Header & Text -->
          <h2 class="offline-title">{{ currentTitle }}</h2>
          <p class="offline-desc">{{ currentDescription }}</p>

          <!-- Auto-check Timer Info -->
          <div class="retry-timer-box">
            <div class="timer-bar-track">
              <div class="timer-bar-fill" :style="{ width: `${progressPercent}%` }"></div>
            </div>
            <span class="timer-text">Автопроверка через <strong>{{ countdown }}</strong> сек...</span>
          </div>

          <!-- Actions -->
          <div class="offline-actions">
            <button 
              class="btn-primary-retry" 
              :disabled="checkingNow" 
              @click="handleManualRetry"
            >
              <svg 
                class="retry-icon" 
                :class="{ 'spin': checkingNow }" 
                width="16" 
                height="16" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                stroke-width="2.5" 
                stroke-linecap="round" 
                stroke-linejoin="round"
              >
                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
              </svg>
              <span>{{ checkingNow ? 'Проверка связи...' : 'Проверить сейчас' }}</span>
            </button>

            <!-- Go to downloaded tracks button -->
            <button 
              v-if="route.name !== 'downloaded'" 
              class="btn-secondary-offline" 
              @click="goToDownloaded"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              <span>Слушать скачанное</span>
            </button>
          </div>

          <!-- Footer note -->
          <div class="offline-footer-note">
            <span>Ваша медиатека и плейлисты в полной сохранности</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNetworkMonitor } from '@/composables/useNetworkMonitor'

const router = useRouter()
const route = useRoute()

const {
  isOffline,
  isBackendDown,
  isBotOnline,
  isMaintenance,
  forceCheck,
} = useNetworkMonitor()

// State
const isMinimized = ref(false)
const checkingNow = ref(false)
const countdown = ref(5)
const CHECK_INTERVAL = 5
let timerInterval = null

// Show overlay whenever backend is unreachable, maintenance is active, or bot is offline
const shouldShowOverlay = computed(() => {
  return isBackendDown.value || isMaintenance.value || (!isBotOnline.value) || isOffline.value
})

const canMinimize = computed(() => {
  // Allow minimizing if user is in downloaded view or wants to see cached UI
  return route.name === 'downloaded' || isMinimized.value
})

const currentTitle = computed(() => {
  if (isMaintenance.value) return 'Технические работы'
  if (isBackendDown.value) return 'Сервер временно оффлайн'
  if (!isBotOnline.value) return 'Telegram-бот переподключается'
  if (isOffline.value) return 'Нет подключения к сети'
  return 'Сервер недоступен'
})

const currentDescription = computed(() => {
  if (isMaintenance.value) {
    return 'Ведутся плановые технические работы или обновление. Мы уже всё настраиваем и скоро вернёмся!'
  }
  if (isBackendDown.value) {
    return 'Сервер плеера временно оффлайн (идёт перезапуск или обновление контейнера). Связь восстановится автоматически.'
  }
  if (!isBotOnline.value) {
    return 'Telegram-бот потерял связь с Telegram API и уже автоматически восстанавливает подключение.'
  }
  return 'Проверьте ваше подключение к интернету. Приложение подключится автоматически, как только сеть восстановится.'
})

const statusPillText = computed(() => {
  if (isMaintenance.value) return 'Техобслуживание'
  if (isBackendDown.value) return 'Оффлайн'
  if (!isBotOnline.value) return 'Переподключение'
  return 'Нет сети'
})

const statusPillClass = computed(() => ({
  'pill-amber': isMaintenance.value || !isBotOnline.value,
  'pill-red': isBackendDown.value || isOffline.value,
}))

const iconBadgeClass = computed(() => ({
  'badge-amber': isMaintenance.value || !isBotOnline.value,
  'badge-red': isBackendDown.value || isOffline.value,
}))

const progressPercent = computed(() => {
  return ((CHECK_INTERVAL - countdown.value) / CHECK_INTERVAL) * 100
})

const handleManualRetry = async () => {
  checkingNow.value = true
  try {
    await forceCheck()
  } finally {
    checkingNow.value = false
    countdown.value = CHECK_INTERVAL
  }
}

const goToDownloaded = () => {
  isMinimized.value = true
  router.push('/downloaded')
}

// Countdown timer loop
const startTimer = () => {
  stopTimer()
  countdown.value = CHECK_INTERVAL
  timerInterval = setInterval(async () => {
    if (!shouldShowOverlay.value) return
    
    countdown.value--
    if (countdown.value <= 0) {
      countdown.value = CHECK_INTERVAL
      try {
        await forceCheck()
      } catch (_) {}
    }
  }, 1000)
}

const stopTimer = () => {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

// If on /downloaded, automatically minimize so user can play cached music
watch(
  () => route.name,
  (newRoute) => {
    if (newRoute === 'downloaded') {
      isMinimized.value = true
    }
  }
)

// When overlay appears, start countdown. When it disappears, reset.
watch(shouldShowOverlay, (val) => {
  if (val) {
    startTimer()
    if (route.name === 'downloaded') {
      isMinimized.value = true
    }
  } else {
    stopTimer()
    isMinimized.value = false
  }
}, { immediate: true })

onMounted(() => {
  if (shouldShowOverlay.value) {
    startTimer()
  }
})

onUnmounted(() => {
  stopTimer()
})
</script>

<style scoped>
.offline-overlay {
  position: fixed;
  inset: 0;
  z-index: 100000; /* Over everything */
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 10, 10, 0.88);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  padding: 20px;
}

.offline-overlay.is-minimized {
  inset: 0 0 auto 0;
  background: transparent;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  padding: 8px 16px;
  pointer-events: none;
}

/* Minimized banner on top */
.offline-minimized-bar {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(26, 26, 26, 0.95);
  border: 1px solid rgba(245, 155, 35, 0.4);
  border-radius: var(--r-full, 9999px);
  padding: 6px 14px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  cursor: pointer;
  transition: all 0.2s ease;
  margin: 0 auto;
}

.offline-minimized-bar:hover {
  background: rgba(35, 35, 35, 0.98);
  border-color: rgba(245, 155, 35, 0.7);
  transform: translateY(1px);
}

.status-indicator-mini {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f59e0b;
  box-shadow: 0 0 8px #f59e0b;
}

.pulse-warning {
  animation: mini-pulse 1.8s infinite ease-in-out;
}

@keyframes mini-pulse {
  0%, 100% { opacity: 0.4; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.1); }
}

.mini-text {
  font-size: 12px;
  font-weight: 600;
  color: #fff;
}

.mini-retry-timer {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
}

.mini-expand-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  padding: 0;
  display: flex;
  cursor: pointer;
}

/* Fullscreen modal card */
.offline-modal-card {
  position: relative;
  width: 100%;
  max-width: 420px;
  background: linear-gradient(180deg, #1c1c1e 0%, #121214 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  padding: 32px 24px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  box-shadow: 0 24px 48px -12px rgba(0, 0, 0, 0.8),
              0 0 0 1px rgba(255, 255, 255, 0.05);
}

.modal-close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  border: none;
  color: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-close-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
}

/* Icon with glowing rings */
.offline-icon-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
}

.pulse-ring {
  position: absolute;
  width: 90px;
  height: 90px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(245, 158, 11, 0.25) 0%, rgba(245, 158, 11, 0) 70%);
  animation: pulse-ring 2.4s infinite ease-out;
}

@keyframes pulse-ring {
  0% { transform: scale(0.7); opacity: 0.8; }
  50% { transform: scale(1.2); opacity: 0.3; }
  100% { transform: scale(0.7); opacity: 0.8; }
}

.offline-icon-badge {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 2;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.badge-amber {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.25), rgba(217, 119, 6, 0.15));
  border: 1px solid rgba(245, 158, 11, 0.4);
  color: #fbbf24;
}

.badge-red {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.25), rgba(185, 28, 28, 0.15));
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #f87171;
}

.gear-spin {
  animation: spin 10s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Status Pill */
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  padding: 4px 12px;
  border-radius: 9999px;
  margin-bottom: 14px;
}

.pill-amber {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.pill-red {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

/* Typography */
.offline-title {
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 10px;
  letter-spacing: -0.3px;
}

.offline-desc {
  font-size: 13px;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.65);
  margin: 0 0 20px;
  max-width: 340px;
}

/* Timer track */
.retry-timer-box {
  width: 100%;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 10px 14px;
  margin-bottom: 22px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.timer-bar-track {
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  overflow: hidden;
}

.timer-bar-fill {
  height: 100%;
  background: var(--c-accent, #1db954);
  transition: width 0.3s linear;
}

.timer-text {
  font-size: 11.5px;
  color: rgba(255, 255, 255, 0.55);
}

.timer-text strong {
  color: #fff;
}

/* Actions */
.offline-actions {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.btn-primary-retry {
  width: 100%;
  height: 44px;
  border-radius: 12px;
  background: var(--c-accent, #1db954);
  color: #000;
  font-size: 14px;
  font-weight: 700;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px rgba(29, 185, 84, 0.3);
}

.btn-primary-retry:hover:not(:disabled) {
  background: var(--c-accent-light, #1ed760);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(29, 185, 84, 0.4);
}

.btn-primary-retry:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary-offline {
  width: 100%;
  height: 42px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
  font-size: 13.5px;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.12);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.btn-secondary-offline:hover {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.2);
}

.offline-footer-note {
  margin-top: 18px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

/* Animations */
.spin {
  animation: spin 0.8s linear infinite;
}

.offline-fade-enter-active,
.offline-fade-leave-active {
  transition: opacity 0.3s ease;
}

.offline-fade-enter-from,
.offline-fade-leave-to {
  opacity: 0;
}
</style>
