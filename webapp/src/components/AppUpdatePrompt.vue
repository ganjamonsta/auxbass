<template>
  <Teleport to="body">
    <Transition name="update-prompt-slide">
      <aside 
        v-if="updateAvailable" 
        class="app-update-prompt"
        role="alert"
        aria-live="assertive"
      >
        <div class="update-card">
          <!-- Glowing Icon Badge -->
          <div class="update-badge">
            <Sparkles :size="18" class="update-sparkle-icon" />
            <span class="badge-pulse-glow"></span>
          </div>

          <!-- Text Details -->
          <div class="update-info">
            <div class="update-title-row">
              <span class="update-title">Доступно обновление</span>
              <span class="update-pill">Свежее</span>
            </div>
            <div class="update-subtitle">
              Сервер обновился. Нажмите для быстрой перезагрузки интерфейса.
            </div>
          </div>

          <!-- Actions -->
          <div class="update-actions">
            <button 
              type="button" 
              class="update-btn-refresh" 
              :disabled="isUpdating" 
              @click="handleRefresh"
              title="Очистить кэш и применить обновление"
            >
              <RefreshCw :size="14" :class="{ 'spin-anim': isUpdating }" />
              <span>{{ isUpdating ? 'Обновление…' : 'Обновить' }}</span>
            </button>

            <button 
              type="button" 
              class="update-btn-dismiss" 
              @click="dismissUpdate"
              title="Закрыть"
              aria-label="Закрыть"
            >
              <X :size="16" />
            </button>
          </div>
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup>
import { Sparkles, RefreshCw, X } from 'lucide-vue-next'
import { useAppUpdate } from '@/composables/useAppUpdate'

const { 
  updateAvailable, 
  isUpdating, 
  forceAppRefresh, 
  dismissUpdate 
} = useAppUpdate()

const handleRefresh = async () => {
  await forceAppRefresh()
}
</script>

<style scoped>
.app-update-prompt {
  position: fixed;
  top: calc(10px + env(safe-area-inset-top, 0px));
  left: 50%;
  transform: translateX(-50%);
  width: calc(100% - 24px);
  max-width: 440px;
  z-index: 10005;
  pointer-events: auto;
}

.update-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(18, 18, 20, 0.94);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(29, 185, 84, 0.42);
  border-radius: 14px;
  box-shadow: 0 10px 32px rgba(0, 0, 0, 0.55), 
              0 0 24px rgba(29, 185, 84, 0.22);
  user-select: none;
  -webkit-user-select: none;
}

/* Badge & Glow */
.update-badge {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(29, 185, 84, 0.22), rgba(29, 185, 84, 0.08));
  color: #1ed760;
  flex-shrink: 0;
  border: 1px solid rgba(29, 185, 84, 0.35);
}

.update-sparkle-icon {
  animation: sparkle-float 3s ease-in-out infinite;
}

.badge-pulse-glow {
  position: absolute;
  inset: -2px;
  border-radius: 12px;
  background: rgba(29, 185, 84, 0.25);
  filter: blur(4px);
  opacity: 0.7;
  animation: pulse-glow 2.4s ease-in-out infinite;
  pointer-events: none;
}

/* Text Content */
.update-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.update-title-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.update-title {
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.2px;
}

.update-pill {
  display: inline-flex;
  align-items: center;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  padding: 2px 5px;
  border-radius: 9999px;
  background: rgba(29, 185, 84, 0.2);
  color: #1ed760;
  border: 1px solid rgba(29, 185, 84, 0.3);
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.update-subtitle {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.35;
  white-space: normal;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Action buttons */
.update-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.update-btn-refresh {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #1ed760;
  color: #041008;
  border: none;
  border-radius: 9999px;
  padding: 6px 13px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 10px rgba(29, 185, 84, 0.35);
  white-space: nowrap;
}

.update-btn-refresh:hover:not(:disabled) {
  background: #22e366;
  transform: scale(1.03);
  box-shadow: 0 4px 14px rgba(29, 185, 84, 0.5);
}

.update-btn-refresh:active:not(:disabled) {
  transform: scale(0.97);
}

.update-btn-refresh:disabled {
  opacity: 0.8;
  cursor: wait;
}

.update-btn-dismiss {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.15s ease;
}

.update-btn-dismiss:hover {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
}

/* Animations */
.spin-anim {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes sparkle-float {
  0%, 100% { transform: rotate(0deg) scale(1); }
  50% { transform: rotate(12deg) scale(1.1); }
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.35; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.08); }
}

/* Transition */
.update-prompt-slide-enter-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.update-prompt-slide-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 1, 1);
}

.update-prompt-slide-enter-from {
  opacity: 0;
  transform: translate(-50%, -24px) scale(0.96);
}

.update-prompt-slide-leave-to {
  opacity: 0;
  transform: translate(-50%, -18px) scale(0.96);
}

@media (max-width: 380px) {
  .update-card {
    padding: 8px 10px;
    gap: 8px;
  }
  .update-badge {
    width: 32px;
    height: 32px;
  }
  .update-btn-refresh {
    padding: 5px 10px;
    font-size: 11px;
  }
}
</style>
