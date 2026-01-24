<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="menu-overlay" @click="$emit('close')">
        <Transition name="slide-up">
          <div v-if="show" class="menu-sheet" @click.stop>
            <!-- Track info header -->
            <div class="menu-header">
              <div class="menu-cover">🎵</div>
              <div class="menu-info">
                <div class="menu-title">{{ track?.title || 'Без названия' }}</div>
                <div class="menu-artist">{{ track?.artist || 'Неизвестный исполнитель' }}</div>
              </div>
            </div>

            <div class="menu-divider"></div>

            <!-- Menu items -->
            <div class="menu-items">
              <!-- Retry button for unavailable tracks -->
              <button v-if="track?.is_unavailable" class="menu-item retry" @click="handleRetry">
                <span class="menu-icon">🔄</span>
                <span>Повторить загрузку</span>
              </button>

              <div v-if="track?.is_unavailable" class="menu-divider"></div>

              <button class="menu-item" @click="handlePlayNext">
                <span class="menu-icon">▶️</span>
                <span>Воспроизвести следующим</span>
              </button>
              
              <button class="menu-item" @click="handleAddToQueue">
                <span class="menu-icon">📋</span>
                <span>Добавить в очередь</span>
              </button>

              <div class="menu-divider"></div>

              <button class="menu-item" @click="handleAddToPlaylist">
                <span class="menu-icon">➕</span>
                <span>Добавить в плейлист</span>
              </button>

              <button class="menu-item" @click="handleEdit">
                <span class="menu-icon">✏️</span>
                <span>Редактировать</span>
              </button>

              <button class="menu-item" @click="handleDownload">
                <span class="menu-icon">📥</span>
                <span>Скачать</span>
              </button>

              <div class="menu-divider"></div>

              <button class="menu-item danger" @click="handleDelete">
                <span class="menu-icon">🗑️</span>
                <span>Удалить</span>
              </button>
            </div>

            <button class="menu-cancel" @click="$emit('close')">
              Отмена
            </button>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { usePlayerStore } from '../stores/player'

const props = defineProps({
  show: Boolean,
  track: Object
})

const emit = defineEmits(['close', 'addToPlaylist', 'edit', 'delete', 'download', 'retry'])

const player = usePlayerStore()
const telegram = inject('telegram')

// Haptic feedback helper
const haptic = (type = 'light') => {
  telegram?.HapticFeedback?.impactOccurred?.(type)
}

const handlePlayNext = () => {
  if (props.track) {
    player.playNext(props.track)
    haptic('light')
  }
  emit('close')
}

const handleAddToQueue = () => {
  if (props.track) {
    player.addToQueue(props.track)
    haptic('light')
  }
  emit('close')
}

const handleAddToPlaylist = () => {
  haptic('light')
  emit('addToPlaylist', props.track)
  emit('close')
}

const handleEdit = () => {
  haptic('light')
  emit('edit', props.track)
  emit('close')
}

const handleDelete = () => {
  haptic('warning')
  emit('delete', props.track)
  emit('close')
}

const handleDownload = () => {
  haptic('light')
  emit('download', props.track)
  emit('close')
}

const handleRetry = () => {
  haptic('medium')
  emit('retry', props.track)
  emit('close')
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   🎵 TRACK MENU - Neumorphic Bottom Sheet
   Action menu for tracks with soft shadows
   ═══════════════════════════════════════════════════════════ */

.menu-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.menu-sheet {
  width: 100%;
  max-width: 500px;
  background: var(--xm-bg-elevated);
  border-radius: var(--neu-radius-xl) var(--neu-radius-xl) 0 0;
  padding: 20px;
  padding-bottom: max(20px, env(safe-area-inset-bottom));
  box-shadow: 
    0 -10px 40px var(--neu-shadow-dark),
    0 -4px 12px var(--neu-shadow-light);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-bottom: none;
}

/* ─── Header ─── */
.menu-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 0;
}

.menu-cover {
  width: 56px;
  height: 56px;
  border-radius: var(--neu-radius-md);
  background: var(--xm-bg-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light);
}

.menu-info {
  flex: 1;
  min-width: 0;
}

.menu-title {
  font-size: 17px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--xm-text-primary);
}

.menu-artist {
  font-size: 14px;
  color: var(--xm-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

/* ─── Divider ─── */
.menu-divider {
  height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    var(--xm-bg-hover) 20%, 
    var(--xm-bg-hover) 80%, 
    transparent 100%);
  margin: 10px 0;
}

/* ─── Menu Items ─── */
.menu-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 12px;
  background: transparent;
  border: none;
  border-radius: var(--neu-radius-md);
  font-size: 16px;
  font-weight: 500;
  color: var(--xm-text-primary);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
}

.menu-item:active {
  background: var(--xm-bg-surface);
  transform: scale(0.98);
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark),
    inset -1px -1px 3px var(--neu-shadow-inset-light);
}

.menu-item.danger {
  color: var(--xm-accent);
}

.menu-item.danger:active {
  background: rgba(229, 57, 53, 0.1);
}

.menu-item.retry {
  color: #4CAF50;
}

.menu-item.retry:active {
  background: rgba(76, 175, 80, 0.1);
}

.menu-icon {
  font-size: 22px;
  width: 32px;
  text-align: center;
  flex-shrink: 0;
}

/* ─── Cancel Button ─── */
.menu-cancel {
  width: 100%;
  padding: 16px;
  margin-top: 12px;
  background: var(--xm-bg-surface);
  border: none;
  border-radius: var(--neu-radius-lg);
  font-size: 17px;
  font-weight: 700;
  color: var(--xm-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light);
}

.menu-cancel:active {
  transform: scale(0.98);
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark),
    inset -1px -1px 3px var(--neu-shadow-inset-light);
}

/* ─── Animations ─── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}
</style>
