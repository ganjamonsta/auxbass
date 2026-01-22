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

const emit = defineEmits(['close', 'addToPlaylist', 'edit', 'delete'])

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
</script>

<style scoped>
.menu-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.menu-sheet {
  width: 100%;
  max-width: 500px;
  background: var(--tg-theme-bg-color);
  border-radius: 16px 16px 0 0;
  padding: 16px;
  padding-bottom: max(16px, env(safe-area-inset-bottom));
}

.menu-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.menu-cover {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: var(--tg-theme-secondary-bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.menu-info {
  flex: 1;
  min-width: 0;
}

.menu-title {
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.menu-artist {
  font-size: 14px;
  color: var(--tg-theme-hint-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.menu-divider {
  height: 1px;
  background: var(--tg-theme-secondary-bg-color);
  margin: 8px 0;
}

.menu-items {
  display: flex;
  flex-direction: column;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 8px;
  background: none;
  border: none;
  font-size: 16px;
  color: var(--tg-theme-text-color);
  cursor: pointer;
  text-align: left;
  border-radius: 8px;
  transition: background 0.2s;
}

.menu-item:active {
  background: var(--tg-theme-secondary-bg-color);
}

.menu-item.danger {
  color: #ff3b30;
}

.menu-icon {
  font-size: 20px;
  width: 28px;
  text-align: center;
}

.menu-cancel {
  width: 100%;
  padding: 16px;
  margin-top: 8px;
  background: var(--tg-theme-secondary-bg-color);
  border: none;
  border-radius: 12px;
  font-size: 17px;
  font-weight: 600;
  color: var(--tg-theme-link-color);
  cursor: pointer;
}

/* Animations */
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
  transition: transform 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}
</style>
