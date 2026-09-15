<template>
  <Teleport to="body">
    <Transition name="banner">
      <div 
        v-if="showBanner" 
        class="network-banner"
        :class="bannerClass"
      >
        <div class="banner-main" @click="handleBannerClick">
          <div class="banner-content">
            <!-- Icon -->
            <div class="banner-icon">
              <!-- Maintenance gear icon -->
              <svg v-if="isMaintenance" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="spin-slow">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>

              <!-- Server unreachable -->
              <svg v-else-if="isBackendDown" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>

              <!-- Bot offline -->
              <svg v-else-if="!isBotOnline" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="10" rx="2" />
                <circle cx="12" cy="5" r="2" />
                <path d="M12 7v4" />
                <line x1="8" y1="16" x2="8.01" y2="16" />
                <line x1="16" y1="16" x2="16.01" y2="16" />
              </svg>

              <!-- Offline -->
              <svg v-else-if="isOffline" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="1" y1="1" x2="23" y2="23"/>
                <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/>
                <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/>
                <path d="M10.71 5.05A16 16 0 0 1 22.56 9"/>
                <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/>
                <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
                <line x1="12" y1="20" x2="12.01" y2="20"/>
              </svg>

              <!-- Reconnecting -->
              <svg v-else-if="isReconnecting" class="spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M12 2a10 10 0 0 1 10 10"/>
              </svg>

              <!-- Slow network -->
              <svg v-else-if="isSlow" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1.42 9a16 16 0 0 1 21.16 0"/>
                <path d="M5 12.55a11 11 0 0 1 14.08 0"/>
                <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
                <line x1="12" y1="20" x2="12.01" y2="20"/>
              </svg>
            </div>
            
            <!-- Text -->
            <div class="banner-text">
              <span class="banner-title">{{ primaryText }}</span>
              <span v-if="subText" class="banner-detail">{{ subText }}</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="banner-actions" @click.stop>
            <!-- Check now button for server down -->
            <button 
              v-if="isBackendDown" 
              class="banner-action-btn check-btn"
              :disabled="checkingNow"
              @click="handleCheckNow"
              title="Проверить доступность сервера"
            >
              <svg :class="{ 'spin': checkingNow }" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
              </svg>
              <span>{{ checkingNow ? 'Проверка...' : `Повтор (${countdown}с)` }}</span>
            </button>

            <!-- Go to downloaded tracks button -->
            <button 
              v-if="(isOffline || isBackendDown) && route.name !== 'downloaded'" 
              class="banner-action-btn downloaded-btn"
              @click="router.push('/downloaded')"
              title="Перейти к скачанным трекам"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              <span>Скачанные</span>
            </button>

            <!-- Maintenance toggle details button -->
            <button 
              v-if="isMaintenance" 
              class="banner-toggle-btn"
              @click="maintenanceExpanded = !maintenanceExpanded"
              title="Подробнее"
            >
              <svg :class="{ 'rotated': maintenanceExpanded }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>
            
            <!-- Dismiss button -->
            <button 
              v-if="canDismiss" 
              class="banner-dismiss" 
              @click="dismiss"
              title="Скрыть"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Maintenance details expandable section -->
        <Transition name="expand">
          <div v-if="isMaintenance && maintenanceExpanded" class="maintenance-details">
            <p>Ведутся технические работы или обновление сервиса.</p>
            <p>Ваша медиатека в безопасности — все треки сохранены в Telegram-канале.</p>
            <div class="maintenance-actions">
              <button class="banner-action-btn downloaded-btn" @click="router.push('/downloaded')">
                Слушать скачанное
              </button>
              <button class="maintenance-dismiss-btn" @click="dismiss">
                Понятно
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNetworkMonitor } from '@/composables/useNetworkMonitor'

const router = useRouter()
const route = useRoute()

const { 
  connectionState,
  latency,
  isOffline,
  isReconnecting,
  isSlow,
  isBackendDown,
  isBotOnline,
  isMaintenance,
  hasIssues,
  statusMessage,
  forceCheck,
} = useNetworkMonitor()

const dismissed = ref(false)
const maintenanceExpanded = ref(false)
const checkingNow = ref(false)
const countdown = ref(5)
const CHECK_INTERVAL = 5
let countdownInterval = null

// Primary status text
const primaryText = computed(() => {
  if (isMaintenance.value) return 'Технические работы'
  if (isBackendDown.value) return 'Сервер временно оффлайн'
  if (!isBotOnline.value) return 'Telegram-бот переподключается'
  if (isOffline.value) return 'Оффлайн-режим'
  return statusMessage.value || 'Проблема с сетью'
})

// Subtext / hints
const subText = computed(() => {
  if (isMaintenance.value) return 'Идёт плановое обновление'
  if (isBackendDown.value) return 'Кэшированные треки доступны'
  if (!isBotOnline.value) return 'Стриминг новых треков на паузе'
  if (isOffline.value) return 'Доступна скачанная музыка'
  if (latency.value > 0 && isSlow.value) return `${latency.value}мс`
  return ''
})

// Can dismiss banner
const canDismiss = computed(() => {
  return isSlow.value || isOffline.value || (!isBotOnline.value && !isBackendDown.value)
})

// Whether to show the banner
const showBanner = computed(() => {
  if (dismissed.value) return false
  return hasIssues.value
})

const bannerClass = computed(() => ({
  'banner-offline': isOffline.value && !isBackendDown.value && !isMaintenance.value,
  'banner-server-down': isBackendDown.value,
  'banner-maintenance': isMaintenance.value,
  'banner-bot-offline': !isBotOnline.value && !isBackendDown.value && !isMaintenance.value,
  'banner-reconnecting': isReconnecting.value && !isBackendDown.value,
  'banner-slow': isSlow.value && !isBackendDown.value,
}))

const dismiss = () => {
  dismissed.value = true
}

const handleBannerClick = () => {
  if (isMaintenance.value) {
    maintenanceExpanded.value = !maintenanceExpanded.value
  } else if (isSlow.value) {
    dismiss()
  }
}

// Manual latency / health check
const handleCheckNow = async () => {
  checkingNow.value = true
  try {
    await forceCheck()
  } finally {
    checkingNow.value = false
    countdown.value = CHECK_INTERVAL
  }
}

// Countdown timer loop for backend down auto-check
const startCountdown = () => {
  stopCountdown()
  countdown.value = CHECK_INTERVAL
  countdownInterval = setInterval(async () => {
    if (!isBackendDown.value) {
      stopCountdown()
      return
    }
    countdown.value--
    if (countdown.value <= 0) {
      countdown.value = CHECK_INTERVAL
      try {
        await forceCheck()
      } catch (_) {}
    }
  }, 1000)
}

const stopCountdown = () => {
  if (countdownInterval) {
    clearInterval(countdownInterval)
    countdownInterval = null
  }
}

// Reset dismissed state on state transitions
watch(connectionState, (newState, oldState) => {
  if (newState !== oldState) {
    dismissed.value = false
  }
})

watch(isBackendDown, (isDown) => {
  if (isDown) {
    dismissed.value = false
    startCountdown()
  } else {
    stopCountdown()
  }
}, { immediate: true })

onUnmounted(() => {
  stopCountdown()
})
</script>

<style scoped>
.network-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10001;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
  cursor: default;
  transition: all 0.25s ease;
}

.banner-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 16px;
  min-height: 38px;
}

/* Color schemes */
.banner-offline {
  background: rgba(30, 30, 34, 0.94);
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  color: #fff;
}

.banner-server-down {
  background: linear-gradient(135deg, rgba(217, 119, 6, 0.95), rgba(180, 83, 9, 0.95));
  border-bottom: 1px solid rgba(245, 158, 11, 0.4);
  color: #fff;
}

.banner-maintenance {
  background: linear-gradient(135deg, rgba(202, 138, 4, 0.95), rgba(161, 98, 7, 0.95));
  border-bottom: 1px solid rgba(234, 179, 8, 0.4);
  color: #fff;
  cursor: pointer;
}

.banner-bot-offline {
  background: rgba(180, 83, 9, 0.9);
  border-bottom: 1px solid rgba(245, 158, 11, 0.3);
  color: #fff;
}

.banner-reconnecting {
  background: rgba(245, 155, 35, 0.92);
  border-bottom: 1px solid rgba(245, 155, 35, 0.4);
  color: #fff;
}

.banner-slow {
  background: rgba(38, 38, 42, 0.92);
  border-bottom: 1px solid rgba(245, 155, 35, 0.3);
  color: #fbbf24;
  cursor: pointer;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.banner-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.banner-text {
  display: flex;
  align-items: baseline;
  gap: 8px;
  min-width: 0;
  flex-wrap: wrap;
}

.banner-title {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.banner-detail {
  font-size: 11.5px;
  opacity: 0.82;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.banner-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.banner-action-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  border-radius: var(--r-full, 9999px);
  font-size: 11px;
  font-weight: 600;
  padding: 4px 11px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  border: 1px solid rgba(255, 255, 255, 0.25);
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.banner-action-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.28);
  border-color: rgba(255, 255, 255, 0.4);
  transform: translateY(-1px);
}

.banner-action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.check-btn {
  background: rgba(0, 0, 0, 0.25);
  border-color: rgba(255, 255, 255, 0.3);
}

.downloaded-btn {
  background: var(--c-accent, #1db954);
  color: #000;
  border-color: var(--c-accent, #1db954);
}

.downloaded-btn:hover {
  background: var(--c-accent-light, #1ed760);
  border-color: var(--c-accent-light, #1ed760);
  color: #000;
}

.banner-toggle-btn {
  background: none;
  border: none;
  color: #fff;
  padding: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.banner-toggle-btn svg {
  transition: transform 0.2s ease;
}

.banner-toggle-btn svg.rotated {
  transform: rotate(180deg);
}

.banner-dismiss {
  background: none;
  border: none;
  color: #fff;
  opacity: 0.7;
  padding: 4px;
  cursor: pointer;
  transition: opacity 0.2s;
  display: flex;
  align-items: center;
}

.banner-dismiss:hover {
  opacity: 1;
}

/* Maintenance expanded details */
.maintenance-details {
  padding: 8px 16px 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  font-size: 12px;
  line-height: 1.5;
  background: rgba(0, 0, 0, 0.15);
}

.maintenance-details p {
  margin: 0 0 6px;
  opacity: 0.92;
}

.maintenance-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.maintenance-dismiss-btn {
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: #fff;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 11px;
  cursor: pointer;
}

/* Animations */
.spin {
  animation: spin 0.8s linear infinite;
}

.spin-slow {
  animation: spin 10s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Transitions */
.banner-enter-active {
  transition: transform 0.3s ease-out, opacity 0.3s ease-out;
}

.banner-leave-active {
  transition: transform 0.25s ease-in, opacity 0.25s ease-in;
}

.banner-enter-from {
  transform: translateY(-100%);
  opacity: 0;
}

.banner-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}

.expand-enter-active,
.expand-leave-active {
  transition: max-height 0.25s ease, opacity 0.2s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.expand-enter-to {
  max-height: 180px;
  opacity: 1;
}

/* Mobile safe area */
@supports (padding-top: env(safe-area-inset-top)) {
  .network-banner {
    padding-top: env(safe-area-inset-top);
  }
}
</style>
