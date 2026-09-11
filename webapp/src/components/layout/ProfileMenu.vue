<template>
  <Teleport to="body">
    <Transition name="profile-menu-fade">
      <div 
        v-if="modelValue" 
        class="profile-menu-backdrop" 
        :class="{ 'is-mobile': isMobile, 'is-desktop': !isMobile }"
        @click="close"
        @keydown.esc="close"
        tabindex="-1"
      >
        <div 
          class="profile-menu-container" 
          :class="{ 'is-mobile': isMobile, 'is-desktop': !isMobile }"
          :style="!isMobile ? desktopStyle : {}"
          @click.stop
        >
          <!-- Mobile drag handle -->
          <div v-if="isMobile" class="sheet-handle-bar" @click="close">
            <div class="sheet-handle"></div>
          </div>

          <!-- User Card -->
          <div class="profile-user-card" @click="goToMyProfile">
            <div class="profile-avatar">
              {{ userInitials }}
            </div>
            <div class="profile-user-details">
              <span class="profile-user-name">{{ userName }}</span>
              <span class="profile-user-handle">{{ userHandle }}</span>
            </div>
            <div class="profile-chevron">
              <ChevronRight :size="18" />
            </div>
          </div>

          <div class="profile-menu-divider"></div>

          <!-- Menu Navigation Options -->
          <div class="profile-menu-items">
            <button class="profile-menu-item" @click="navigate('/friends')">
              <div class="item-icon-box">
                <Users :size="18" />
              </div>
              <span class="item-label">Кенты</span>
              <span v-if="friendsCount" class="item-badge">{{ friendsCount }}</span>
            </button>

            <button class="profile-menu-item" @click="navigate('/settings')">
              <div class="item-icon-box">
                <Settings :size="18" />
              </div>
              <span class="item-label">Настройки</span>
            </button>

            <button class="profile-menu-item" @click="navigate('/settings#channel')">
              <div class="item-icon-box">
                <Radio :size="18" />
              </div>
              <span class="item-label">Telegram-канал</span>
              <span 
                class="channel-status-pill"
                :class="{ connected: authStore.hasChannel }"
              >
                {{ authStore.hasChannel ? 'Подключен' : 'Не настроен' }}
              </span>
            </button>

            <button class="profile-menu-item" @click="navigate('/downloaded')">
              <div class="item-icon-box">
                <Download :size="18" />
              </div>
              <span class="item-label">Офлайн-треки</span>
            </button>

            <button 
              v-if="!pwaInstall.isInstalled" 
              class="profile-menu-item pwa-item" 
              @click="handleInstallPwa"
            >
              <div class="item-icon-box">
                <Sparkles :size="18" />
              </div>
              <span class="item-label">Установить приложение</span>
            </button>
          </div>

          <div class="profile-menu-divider"></div>

          <!-- Logout Button -->
          <div class="profile-menu-footer">
            <button class="profile-menu-item logout-item" @click="handleLogout">
              <div class="item-icon-box">
                <LogOut :size="18" />
              </div>
              <span class="item-label">Выйти из аккаунта</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import { usePwaInstall } from '@/composables/usePwaInstall'
import { 
  Users, 
  Settings, 
  Radio, 
  Download, 
  LogOut, 
  ChevronRight, 
  Sparkles 
} from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  placement: {
    type: String,
    default: 'sidebar' // 'sidebar' | 'header'
  }
})

const emit = defineEmits(['update:modelValue', 'close'])

const router = useRouter()
const authStore = useAuthStore()
const playerStore = usePlayerStore()
const pwaInstall = usePwaInstall()

const isMobile = ref(window.innerWidth < 1024)
const desktopStyle = ref({})

const updateScreen = () => {
  isMobile.value = window.innerWidth < 1024
}

const updateDesktopPosition = () => {
  if (isMobile.value) {
    desktopStyle.value = {}
    return
  }

  // Header placement
  if (props.placement === 'header') {
    const headerBtn = document.querySelector('.header-profile-btn')
    if (headerBtn) {
      const rect = headerBtn.getBoundingClientRect()
      desktopStyle.value = {
        position: 'fixed',
        top: `${Math.round(rect.bottom + 8)}px`,
        right: `${Math.max(16, Math.round(window.innerWidth - rect.right))}px`,
        width: '280px',
        maxHeight: `calc(100vh - ${Math.round(rect.bottom + 24)}px)`,
        transformOrigin: 'top right'
      }
      return
    }
  }

  // Sidebar placement (default for desktop)
  const footerEl = document.querySelector('.sidebar-footer')
  if (footerEl) {
    const rect = footerEl.getBoundingClientRect()
    const bottom = Math.max(12, Math.round(window.innerHeight - rect.top + 8))
    const left = Math.max(8, Math.round(rect.left + 10))
    const width = Math.min(264, Math.max(240, Math.round(rect.width - 20)))
    const maxHeight = Math.max(220, Math.round(rect.top - 20))

    desktopStyle.value = {
      position: 'fixed',
      left: `${left}px`,
      bottom: `${bottom}px`,
      width: `${width}px`,
      maxHeight: `${maxHeight}px`,
      transformOrigin: 'bottom left'
    }
  } else {
    desktopStyle.value = {
      position: 'fixed',
      left: '12px',
      bottom: '80px',
      width: '260px',
      transformOrigin: 'bottom left'
    }
  }
}

const userName = computed(() => {
  const u = authStore.user
  if (!u) return 'Пользователь'
  if (u.first_name && u.last_name) return `${u.first_name} ${u.last_name}`
  return u.first_name || u.username || `Пользователь #${u.id}`
})

const userHandle = computed(() => {
  const u = authStore.user
  if (!u) return ''
  if (u.username) return `@${u.username}`
  return `ID: ${u.id}`
})

const userInitials = computed(() => {
  const name = userName.value || 'U'
  return name.substring(0, 2).toUpperCase()
})

const friendsCount = computed(() => {
  return null
})

const close = () => {
  emit('update:modelValue', false)
  emit('close')
}

const navigate = (path) => {
  close()
  router.push(path)
}

const goToMyProfile = () => {
  close()
  if (authStore.user?.id) {
    router.push(`/user/${authStore.user.id}`)
  } else {
    router.push('/settings')
  }
}

const handleInstallPwa = () => {
  close()
  pwaInstall.promptInstall()
}

const handleLogout = () => {
  close()
  if (confirm('Вы уверены, что хотите выйти из аккаунта?')) {
    authStore.logout()
    window.location.href = '/login'
  }
}

const handleResize = () => {
  updateScreen()
  if (props.modelValue && !isMobile.value) {
    updateDesktopPosition()
  }
}

const handleKeyDown = (e) => {
  if (e.key === 'Escape' && props.modelValue) {
    close()
  }
}

watch(() => props.modelValue, (isOpen) => {
  if (isOpen && !isMobile.value) {
    nextTick(updateDesktopPosition)
  }
})

watch(() => playerStore.currentTrack, () => {
  if (props.modelValue && !isMobile.value) {
    nextTick(updateDesktopPosition)
  }
})

onMounted(() => {
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeyDown)
  if (props.modelValue && !isMobile.value) {
    nextTick(updateDesktopPosition)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.profile-menu-backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--z-contextmenu, 1100);
}

/* Mobile backdrop: dimmed overlay with blur */
.profile-menu-backdrop.is-mobile {
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  justify-content: flex-end;
  align-items: flex-start;
  padding: 60px 16px 16px;
}

/* Desktop backdrop: transparent, NO BLUR, catches clicks outside to close */
.profile-menu-backdrop.is-desktop {
  background: transparent;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  display: block;
  padding: 0;
}

.profile-menu-container {
  width: 300px;
  max-width: 92vw;
  background: rgba(20, 24, 33, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Desktop container */
.profile-menu-container.is-desktop {
  background: #141821;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.75), 0 0 0 1px rgba(255, 255, 255, 0.08);
  overflow-y: auto;
  overflow-x: hidden;
}

.profile-menu-container.is-desktop::-webkit-scrollbar {
  width: 4px;
}

.profile-menu-container.is-desktop::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
}

/* Mobile Bottom Sheet style */
.profile-menu-container.is-mobile {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  max-width: 100%;
  border-radius: 20px 20px 0 0;
  padding-bottom: env(safe-area-inset-bottom, 16px);
  border-bottom: none;
}

.sheet-handle-bar {
  display: flex;
  justify-content: center;
  padding: 10px 0 4px;
  cursor: pointer;
}

.sheet-handle {
  width: 36px;
  height: 4px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 2px;
}

/* User Card */
.profile-user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.profile-user-card:hover {
  background: rgba(255, 255, 255, 0.06);
}

.profile-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--c-accent, #1db954), #8b5cf6);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.profile-user-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.profile-user-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.profile-user-handle {
  font-size: 12px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.profile-chevron {
  color: var(--c-text-3, rgba(255, 255, 255, 0.4));
  flex-shrink: 0;
}

.profile-menu-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
  margin: 4px 12px;
}

/* Menu Items */
.profile-menu-items {
  display: flex;
  flex-direction: column;
  padding: 4px 8px;
  gap: 2px;
}

.profile-menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: transparent;
  border: none;
  border-radius: 10px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.85));
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  width: 100%;
  text-align: left;
  font-family: inherit;
}

.profile-menu-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-1, #fff);
}

.item-icon-box {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  flex-shrink: 0;
}

.item-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-badge {
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  background: var(--c-accent, #1db954);
  padding: 2px 7px;
  border-radius: 10px;
}

.channel-status-pill {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.channel-status-pill.connected {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.pwa-item .item-icon-box {
  color: var(--c-accent, #1db954);
}

.profile-menu-footer {
  padding: 4px 8px 8px;
}

.logout-item {
  color: #f87171;
}

.logout-item .item-icon-box {
  color: #f87171;
}

.logout-item:hover {
  background: rgba(239, 68, 68, 0.12);
  color: #fca5a5;
}

/* Animations */
.profile-menu-fade-enter-active,
.profile-menu-fade-leave-active {
  transition: opacity 0.18s ease;
}

/* Mobile slide transition */
.profile-menu-fade-enter-active .profile-menu-container.is-mobile,
.profile-menu-fade-leave-active .profile-menu-container.is-mobile {
  transition: transform 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.profile-menu-fade-enter-from,
.profile-menu-fade-leave-to {
  opacity: 0;
}

.profile-menu-fade-enter-from .profile-menu-container.is-desktop,
.profile-menu-fade-leave-to .profile-menu-container.is-desktop {
  opacity: 0;
  transform: translateY(6px) scale(0.97);
}

.profile-menu-fade-enter-active .profile-menu-container.is-desktop,
.profile-menu-fade-leave-active .profile-menu-container.is-desktop {
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.18s ease;
}

.profile-menu-fade-enter-from .profile-menu-container.is-mobile,
.profile-menu-fade-leave-to .profile-menu-container.is-mobile {
  transform: translateY(100%);
}
</style>
