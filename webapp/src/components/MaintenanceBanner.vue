<template>
  <Teleport to="body">
    <Transition name="maintenance-banner">
      <div v-if="visible" class="maintenance-banner" @click="expanded = !expanded">
        <div class="maintenance-content">
          <div class="maintenance-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <div class="maintenance-text">
            <span class="maintenance-title">Бот временно недоступен</span>
            <span class="maintenance-subtitle">Загрузка и стриминг приостановлены</span>
          </div>
          <button class="maintenance-toggle" @click.stop="expanded = !expanded">
            <svg :class="{ rotated: expanded }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
        </div>
        <Transition name="expand">
          <div v-if="expanded" class="maintenance-details">
            <p>Мы подали апелляцию и ожидаем решения. Это может занять до 2 недель.</p>
            <p>Ваша музыкальная коллекция в безопасности — все треки сохранены в вашем бекап-канале.</p>
            <button class="maintenance-dismiss" @click.stop="dismiss">Понятно</button>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const MAINTENANCE_MODE = import.meta.env.VITE_MAINTENANCE_MODE === 'true'
const STORAGE_KEY = 'maintenance-dismissed'

const visible = ref(false)
const expanded = ref(false)

onMounted(() => {
  if (!MAINTENANCE_MODE) return
  const dismissed = localStorage.getItem(STORAGE_KEY)
  if (!dismissed) {
    visible.value = true
  }
})

const dismiss = () => {
  visible.value = false
  localStorage.setItem(STORAGE_KEY, Date.now().toString())
}
</script>

<style scoped>
.maintenance-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10000;
  background: linear-gradient(135deg, #d97706, #b45309);
  color: white;
  cursor: pointer;
  user-select: none;
  -webkit-user-select: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
}

.maintenance-content {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
}

.maintenance-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  opacity: 0.9;
}

.maintenance-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.maintenance-title {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
}

.maintenance-subtitle {
  font-size: 11px;
  opacity: 0.8;
  line-height: 1.3;
  margin-top: 1px;
}

.maintenance-toggle {
  flex-shrink: 0;
  background: none;
  border: none;
  color: white;
  padding: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.maintenance-toggle svg {
  transition: transform 0.2s ease;
}

.maintenance-toggle svg.rotated {
  transform: rotate(180deg);
}

.maintenance-details {
  padding: 0 16px 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  margin-top: 2px;
  padding-top: 10px;
}

.maintenance-details p {
  font-size: 12px;
  line-height: 1.5;
  margin: 0 0 8px;
  opacity: 0.9;
}

.maintenance-dismiss {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  margin-top: 4px;
  transition: background 0.15s ease;
}

.maintenance-dismiss:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Transitions */
.maintenance-banner-enter-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.maintenance-banner-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.maintenance-banner-enter-from {
  transform: translateY(-100%);
  opacity: 0;
}
.maintenance-banner-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}

.expand-enter-active {
  transition: max-height 0.25s ease, opacity 0.2s ease;
}
.expand-leave-active {
  transition: max-height 0.2s ease, opacity 0.15s ease;
}
.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
}
.expand-enter-to {
  max-height: 200px;
}
</style>
