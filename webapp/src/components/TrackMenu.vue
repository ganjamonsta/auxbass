<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="menu-overlay" @click="$emit('close')">
        <Transition name="slide-up">
          <div v-if="show" class="menu-sheet" @click.stop>
            <!-- Track info header with close button -->
            <div class="menu-header">
              <div class="menu-cover">🎵</div>
              <div class="menu-info">
                <div class="menu-title">{{ track?.title || 'Без названия' }}</div>
                <div class="menu-artist">{{ track?.artist || 'Неизвестный исполнитель' }}</div>
              </div>
              <button class="menu-close" @click="$emit('close')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
                </svg>
              </button>
            </div>

            <!-- Menu items -->
            <div class="menu-items">
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

const emit = defineEmits(['close', 'addToPlaylist', 'edit', 'delete', 'download'])

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
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   🎵 TRACK MENU - Compact Bottom Sheet
   Action menu for tracks with soft shadows
   ═══════════════════════════════════════════════════════════ */

.menu-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
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
  padding: 12px 16px;
  padding-bottom: max(12px, env(safe-area-inset-bottom));
  box-shadow: 
    0 -8px 24px var(--neu-shadow-dark),
    0 -2px 8px var(--neu-shadow-light);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-bottom: none;
}

/* ─── Header ─── */
.menu-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0 8px;
}

.menu-cover {
  width: 44px;
  height: 44px;
  border-radius: var(--neu-radius-sm);
  background: var(--xm-bg-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 
    3px 3px 6px var(--neu-shadow-dark),
    -1px -1px 3px var(--neu-shadow-light);
}

.menu-info {
  flex: 1;
  min-width: 0;
}

.menu-title {
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--xm-text-primary);
}

.menu-artist {
  font-size: 13px;
  color: var(--xm-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 1px;
}

.menu-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--xm-bg-surface);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.menu-close:active {
  background: var(--xm-bg-hover);
  transform: scale(0.92);
}

/* ─── Divider ─── */
.menu-divider {
  height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    var(--xm-bg-hover) 20%, 
    var(--xm-bg-hover) 80%, 
    transparent 100%);
  margin: 6px 0;
}

/* ─── Menu Items ─── */
.menu-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 11px 10px;
  background: transparent;
  border: none;
  border-radius: var(--neu-radius-sm);
  font-size: 15px;
  font-weight: 500;
  color: var(--xm-text-primary);
  cursor: pointer;
  text-align: left;
  transition: all 0.12s ease;
}

.menu-item:active {
  background: var(--xm-bg-surface);
  transform: scale(0.98);
}

.menu-item.danger {
  color: var(--xm-accent);
}

.menu-item.danger:active {
  background: rgba(229, 57, 53, 0.1);
}

.menu-icon {
  font-size: 18px;
  width: 26px;
  text-align: center;
  flex-shrink: 0;
}

/* ─── Animations ─── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}
</style>
