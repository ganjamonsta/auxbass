<template>
  <Teleport to="body">
    <Transition name="pwa-slide">
      <div 
        v-if="showBanner && isInstallable" 
        class="pwa-install-banner"
        role="alert"
        aria-live="polite"
      >
        <div class="pwa-banner-card" @click="handleCardClick">
          <!-- App Icon / Logo -->
          <div class="pwa-app-icon">
            <img src="/icons/icon-96x96.png" alt="AuxBass" class="pwa-logo-img" />
            <span class="pwa-badge-pulse"></span>
          </div>

          <!-- Description -->
          <div class="pwa-info">
            <div class="pwa-title">Установить AuxBass</div>
            <div class="pwa-desc">
              {{ bannerSubtitle }}
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="pwa-actions">
            <button 
              class="pwa-install-btn" 
              @click.stop="handleInstallClick"
              type="button"
            >
              <Download :size="16" />
              <span>{{ installButtonText }}</span>
            </button>
            <button 
              class="pwa-close-btn" 
              @click.stop="dismissBanner"
              type="button"
              aria-label="Закрыть"
              title="Скрыть"
            >
              <X :size="16" />
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { Download, X } from 'lucide-vue-next'
import { usePwaInstall } from '@/composables/usePwaInstall'

const {
  showBanner,
  isInstallable,
  canPromptDirectly,
  isIOS,
  isTelegram,
  promptInstall,
  dismissBanner
} = usePwaInstall()

const bannerSubtitle = computed(() => {
  if (isTelegram.value) return 'Добавьте ярлык для быстрого запуска'
  if (isIOS.value) return 'Добавьте на домашний экран iOS'
  return 'Быстрый запуск и фоновое аудио'
})

const installButtonText = computed(() => {
  if (canPromptDirectly.value) return 'Установить'
  if (isIOS.value) return 'Инструкция'
  return 'Установить'
})

const handleInstallClick = () => {
  promptInstall()
}

const handleCardClick = () => {
  promptInstall()
}
</script>

<style scoped>
.pwa-install-banner {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10002;
  width: calc(100% - 32px);
  max-width: 440px;
  pointer-events: none;
}

@supports (padding-top: env(safe-area-inset-top)) {
  .pwa-install-banner {
    top: calc(16px + env(safe-area-inset-top, 0px));
  }
}

.pwa-banner-card {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(22, 22, 26, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  box-shadow: 
    0 12px 36px rgba(0, 0, 0, 0.55),
    0 2px 8px rgba(0, 0, 0, 0.3),
    0 0 20px rgba(29, 185, 84, 0.15);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  cursor: pointer;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s ease, border-color 0.2s ease;
}

.pwa-banner-card:hover {
  transform: translateY(-2px);
  border-color: rgba(29, 185, 84, 0.4);
  box-shadow: 
    0 16px 40px rgba(0, 0, 0, 0.65),
    0 0 25px rgba(29, 185, 84, 0.25);
}

.pwa-app-icon {
  position: relative;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 10px;
  overflow: visible;
}

.pwa-logo-img {
  width: 100%;
  height: 100%;
  border-radius: 10px;
  object-fit: cover;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

.pwa-badge-pulse {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 8px;
  height: 8px;
  background-color: var(--c-accent, #1db954);
  border-radius: 50%;
  box-shadow: 0 0 8px var(--c-accent, #1db954);
  animation: pulse-glow 2s infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.4);
    opacity: 0.6;
  }
}

.pwa-info {
  flex: 1;
  min-width: 0;
}

.pwa-title {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
  line-height: 1.25;
  letter-spacing: -0.01em;
}

.pwa-desc {
  font-size: 12px;
  color: var(--c-text-2, #b0b0b0);
  line-height: 1.3;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pwa-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.pwa-install-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--c-accent, #1db954);
  color: #000000;
  border: none;
  border-radius: 9999px;
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 2px 8px rgba(29, 185, 84, 0.35);
}

.pwa-install-btn:hover {
  background: var(--c-accent-light, #1ed760);
  transform: scale(1.04);
  box-shadow: 0 4px 12px rgba(29, 185, 84, 0.5);
}

.pwa-install-btn:active {
  transform: scale(0.96);
}

.pwa-close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: rgba(255, 255, 255, 0.08);
  border: none;
  border-radius: 50%;
  color: var(--c-text-2, #b0b0b0);
  cursor: pointer;
  transition: all 0.15s ease;
}

.pwa-close-btn:hover {
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
}

/* Animations */
.pwa-slide-enter-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.pwa-slide-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.pwa-slide-enter-from {
  opacity: 0;
  transform: translate(-50%, -24px) scale(0.92);
}

.pwa-slide-leave-to {
  opacity: 0;
  transform: translate(-50%, -16px) scale(0.96);
}

/* Responsive adjustment */
@media (min-width: 1024px) {
  .pwa-install-banner {
    top: auto;
    bottom: 24px;
    right: 24px;
    left: auto;
    transform: none;
    max-width: 380px;
  }

  .pwa-slide-enter-from {
    opacity: 0;
    transform: translateY(24px) scale(0.92);
  }

  .pwa-slide-leave-to {
    opacity: 0;
    transform: translateY(16px) scale(0.96);
  }
}
</style>
