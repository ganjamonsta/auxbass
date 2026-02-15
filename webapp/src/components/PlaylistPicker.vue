<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
        <div class="modal">
          <div class="modal-header">
            <h3>Добавить в плейлист</h3>
            <button class="modal-close" @click="$emit('close')"><X :size="20" /></button>
          </div>

          <div class="playlist-list">
            <button 
              v-if="playlists.length === 0" 
              class="create-first"
              @click="$emit('createNew')"
            >
              <span class="create-icon"><Plus :size="18" /></span>
              <span>Создать первый плейлист</span>
            </button>

            <template v-else>
              <button class="playlist-option create" @click="$emit('createNew')">
                <span class="playlist-icon"><Plus :size="18" /></span>
                <span>Новый плейлист</span>
              </button>

              <button 
                v-for="playlist in playlists"
                :key="playlist.id"
                class="playlist-option"
                @click="handleSelect(playlist)"
              >
                <span class="playlist-icon"><Folder :size="18" /></span>
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
import { X, Plus, Folder } from 'lucide-vue-next'

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
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 20px;
}

.modal {
  background: var(--xm-bg-elevated, #1A1A1A);
  border-radius: var(--neu-radius-xl, 24px);
  width: 100%;
  max-width: 400px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 
    12px 12px 24px var(--neu-shadow-dark, rgba(0, 0, 0, 0.6)),
    -6px -6px 12px var(--neu-shadow-light, rgba(255, 255, 255, 0.03)),
    0 0 40px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid var(--xm-bg-surface, #222);
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--xm-text-primary, #fff);
}

.modal-close {
  width: 36px;
  height: 36px;
  border: none;
  background: var(--xm-bg-surface, #222);
  border-radius: var(--neu-radius-full, 9999px);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-text-muted, #888);
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -2px -2px 4px var(--neu-shadow-light, rgba(255, 255, 255, 0.03));
  transition: all 0.15s ease;
}

.modal-close:active {
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -1px -1px 2px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
}

.playlist-list {
  flex: 1;
  min-h-0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px;
  scrollbar-gutter: auto;
}

.playlist-list::-webkit-scrollbar {
  width: 6px;
  background: transparent;
}

.playlist-list::-webkit-scrollbar-track {
  background: transparent;
}

.playlist-list::-webkit-scrollbar-thumb {
  background: var(--xm-accent-glow, rgba(229, 57, 53, 0.3));
  border-radius: 3px;
}

.create-first {
  width: 100%;
  padding: 40px 20px;
  background: var(--xm-bg-surface, #222);
  border: 2px dashed var(--xm-accent, #E53935);
  border-radius: var(--neu-radius-lg, 16px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  color: var(--xm-accent, #E53935);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 
    inset 4px 4px 8px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -2px -2px 4px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
}

.create-icon {
  font-size: 36px;
}

.playlist-option {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  background: var(--xm-bg-surface, #222);
  border: none;
  border-radius: var(--neu-radius-md, 12px);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
  margin-bottom: 10px;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -2px -2px 4px var(--neu-shadow-light, rgba(255, 255, 255, 0.03));
}

.playlist-option:active {
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -1px -1px 2px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
}

.playlist-option.create {
  color: var(--xm-accent, #E53935);
  background: linear-gradient(180deg, var(--xm-bg-surface, #222) 0%, var(--xm-bg-elevated, #1A1A1A) 100%);
}

.playlist-icon {
  font-size: 26px;
  width: 36px;
  text-align: center;
}

.playlist-info {
  flex: 1;
  min-width: 0;
}

.playlist-name {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: var(--xm-text-primary, #fff);
}

.playlist-count {
  display: block;
  font-size: 13px;
  color: var(--xm-text-muted, #888);
  margin-top: 2px;
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
