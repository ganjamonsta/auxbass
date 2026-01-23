<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
        <div class="modal">
          <div class="modal-header">
            <h3>Добавить в плейлист</h3>
            <button class="modal-close" @click="$emit('close')">✕</button>
          </div>

          <div class="playlist-list">
            <button 
              v-if="playlists.length === 0" 
              class="create-first"
              @click="$emit('createNew')"
            >
              <span class="create-icon">➕</span>
              <span>Создать первый плейлист</span>
            </button>

            <template v-else>
              <button class="playlist-option create" @click="$emit('createNew')">
                <span class="playlist-icon">➕</span>
                <span>Новый плейлист</span>
              </button>

              <button 
                v-for="playlist in playlists"
                :key="playlist.id"
                class="playlist-option"
                @click="handleSelect(playlist)"
              >
                <span class="playlist-icon">📁</span>
                <div class="playlist-info">
                  <span class="playlist-name">{{ playlist.name }}</span>
                  <span class="playlist-count">{{ playlist.track_count }} треков</span>
                </div>
              </button>
            </template>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { inject, computed, watch } from 'vue'
import { useLibraryStore } from '../stores/library'

const props = defineProps({
  show: Boolean,
  track: Object
})

const emit = defineEmits(['close', 'createNew', 'added'])

const library = useLibraryStore()
const telegram = inject('telegram')

// Use computed to reactively get playlists
const playlists = computed(() => library.playlists)

// Fetch playlists when modal opens
watch(() => props.show, async (isOpen) => {
  if (isOpen) {
    await library.fetchPlaylists()
  }
})

const handleSelect = async (playlist) => {
  if (!props.track) return
  
  const success = await library.addTrackToPlaylist(playlist.id, props.track.id)
  if (success) {
    telegram?.HapticFeedback?.notificationOccurred?.('success')
    emit('added', playlist)
  } else {
    telegram?.HapticFeedback?.notificationOccurred?.('error')
  }
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 20px;
}

.modal {
  background: var(--tg-theme-bg-color);
  border-radius: 16px;
  width: 100%;
  max-width: 400px;
  max-height: 70vh;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--tg-theme-secondary-bg-color);
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--tg-theme-secondary-bg-color);
  border-radius: 50%;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.playlist-list {
  max-height: calc(70vh - 70px);
  overflow-y: auto;
  padding: 8px;
}

.create-first {
  width: 100%;
  padding: 40px 20px;
  background: none;
  border: 2px dashed var(--tg-theme-hint-color);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--tg-theme-hint-color);
  font-size: 16px;
  cursor: pointer;
}

.create-icon {
  font-size: 32px;
}

.playlist-option {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 12px;
  background: none;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  text-align: left;
  transition: background 0.2s;
}

.playlist-option:active {
  background: var(--tg-theme-secondary-bg-color);
}

.playlist-option.create {
  color: var(--tg-theme-link-color);
}

.playlist-icon {
  font-size: 24px;
  width: 32px;
  text-align: center;
}

.playlist-info {
  flex: 1;
  min-width: 0;
}

.playlist-name {
  display: block;
  font-size: 16px;
  font-weight: 500;
  color: var(--tg-theme-text-color);
}

.playlist-count {
  display: block;
  font-size: 13px;
  color: var(--tg-theme-hint-color);
}

/* Animation */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
