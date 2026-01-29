<template>
  <Teleport to="body">
    <Transition name="slide-down">
      <div v-if="authStore.showChannelBanner" class="channel-banner" @click="goToSettings">
        <div class="banner-content">
          <div class="banner-icon"><Lock :size="24" /></div>
          <div class="banner-text">
            <div class="banner-title">Подключите канал</div>
            <div class="banner-subtitle">Чтобы сохранять музыку и создавать плейлисты</div>
          </div>
          <div class="banner-arrow">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
            </svg>
          </div>
        </div>
        <button class="banner-close" @click.stop="dismiss">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
          </svg>
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Lock } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const goToSettings = () => {
  authStore.dismissChannelBanner()
  router.push('/settings#channel')
}

const dismiss = () => {
  authStore.dismissChannelBanner()
}
</script>

<style scoped>
.channel-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 16px;
  padding-top: calc(12px + env(safe-area-inset-top, 0));
  z-index: 10001;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.banner-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.banner-icon {
  font-size: 24px;
}

.banner-text {
  flex: 1;
}

.banner-title {
  font-weight: 600;
  font-size: 15px;
}

.banner-subtitle {
  font-size: 12px;
  opacity: 0.9;
}

.banner-arrow {
  opacity: 0.8;
}

.banner-close {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
  transition: background 0.2s;
}

.banner-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Animation */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
</style>
