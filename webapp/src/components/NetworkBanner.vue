<template>
  <Teleport to="body">
    <Transition name="banner">
      <div 
        v-if="showBanner" 
        class="network-banner"
        :class="bannerClass"
        @click="handleClick"
      >
        <div class="banner-content">
          <!-- Icon -->
          <div class="banner-icon">
            <!-- Offline -->
            <svg v-if="isOffline" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="1" y1="1" x2="23" y2="23"/>
              <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/>
              <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/>
              <path d="M10.71 5.05A16 16 0 0 1 22.56 9"/>
              <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/>
              <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
              <line x1="12" y1="20" x2="12.01" y2="20"/>
            </svg>
            <!-- Reconnecting (animated) -->
            <svg v-else-if="isReconnecting" class="spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M12 2a10 10 0 0 1 10 10"/>
            </svg>
            <!-- Slow -->
            <svg v-else-if="isSlow" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1.42 9a16 16 0 0 1 21.16 0"/>
              <path d="M5 12.55a11 11 0 0 1 14.08 0"/>
              <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
              <line x1="12" y1="20" x2="12.01" y2="20"/>
            </svg>
          </div>
          
          <!-- Text -->
          <div class="banner-text">
            <span class="banner-title">{{ statusMessage }}</span>
            <span v-if="latencyText" class="banner-detail">{{ latencyText }}</span>
          </div>
        </div>

        <!-- Go to downloaded tracks when offline -->
        <button 
          v-if="isOffline && route.name !== 'downloaded'" 
          class="banner-action-btn"
          @click.stop="router.push('/downloaded')"
        >
          Скачанные
        </button>
        
        <!-- Dismiss button (only for slow) -->
        <button v-if="isSlow && canDismiss" class="banner-dismiss" @click.stop="dismiss">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
          </svg>
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
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
  hasIssues,
  statusMessage,
} = useNetworkMonitor()

const dismissed = ref(false)
const canDismiss = ref(true)

// Показывать баннер при проблемах с сетью
const showBanner = computed(() => {
  if (dismissed.value && isSlow.value) return false
  return hasIssues.value
})

const bannerClass = computed(() => ({
  'banner-offline': isOffline.value,
  'banner-reconnecting': isReconnecting.value,
  'banner-slow': isSlow.value,
}))

const latencyText = computed(() => {
  if (latency.value > 0 && isSlow.value) {
    return `Задержка: ${latency.value}мс`
  }
  return ''
})

const dismiss = () => {
  dismissed.value = true
}

const handleClick = () => {
  // Dismiss slow banner on click
  if (isSlow.value) {
    dismiss()
  }
}

// Сбросить dismissed при смене состояния
watch(connectionState, (newState, oldState) => {
  if (newState !== oldState) {
    dismissed.value = false
  }
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
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  min-height: 36px;
  cursor: default;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.banner-offline {
  background: rgba(233, 20, 41, 0.9);
  color: #fff;
}

.banner-reconnecting {
  background: rgba(245, 155, 35, 0.9);
  color: #fff;
}

.banner-slow {
  background: rgba(245, 155, 35, 0.75);
  color: #fff;
  cursor: pointer;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 10px;
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
  font-size: 13px;
  line-height: 1.3;
}

.banner-title {
  font-weight: 600;
}

.banner-detail {
  font-size: 11px;
  opacity: 0.8;
}

.banner-action-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.45);
  color: #fff;
  border-radius: var(--r-full);
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  cursor: pointer;
  margin-left: auto;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.banner-action-btn:hover {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-1px);
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

/* Spinner animation */
@keyframes spin {
  to { transform: rotate(360deg); }
}

.spin {
  animation: spin 0.8s linear infinite;
}

/* Transition */
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

/* Mobile safe area */
@supports (padding-top: env(safe-area-inset-top)) {
  .network-banner {
    padding-top: calc(8px + env(safe-area-inset-top));
  }
}
</style>
