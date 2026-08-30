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
  background: var(--c-bg-2);
  border-radius: var(--r-xl);
  width: 100%;
  max-width: 400px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 
    12px 12px 24px var(--sh-dark)),
    -6px -6px 12px var(--sh-light)),
    0 0 40px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid var(--c-bg-3);
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--c-text-1);
}

.modal-close {
  width: 36px;
  height: 36px;
  border: none;
  background: var(--c-bg-3);
  border-radius: var(--r-full);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-3);
  box-shadow: 
    4px 4px 8px var(--sh-dark)),
    -2px -2px 4px var(--sh-light));
  transition: all 0.15s ease;
}

.modal-close:active {
  box-shadow: 
    inset 2px 2px 4px var(--sh-inset-dark)),
    inset -1px -1px 2px var(--sh-inset-light));
}

.playlist-list {
  flex: 1;
  min-height: 0;
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
  background: var(--c-accent-glow));
  border-radius: 3px;
}

.create-first {
  width: 100%;
  padding: 40px 20px;
  background: var(--c-bg-3);
  border: 2px dashed var(--c-accent);
  border-radius: var(--r-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  color: var(--c-accent);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 
    inset 4px 4px 8px var(--sh-inset-dark)),
    inset -2px -2px 4px var(--sh-inset-light));
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
  background: var(--c-bg-3);
  border: none;
  border-radius: var(--r-md);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
  margin-bottom: 10px;
  box-shadow: 
    4px 4px 8px var(--sh-dark)),
    -2px -2px 4px var(--sh-light));
}

.playlist-option:active {
  box-shadow: 
    inset 2px 2px 4px var(--sh-inset-dark)),
    inset -1px -1px 2px var(--sh-inset-light));
}

.playlist-option.create {
  color: var(--c-accent);
  background: linear-gradient(180deg, var(--c-bg-3) 0%, var(--c-bg-2) 100%);
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
  color: var(--c-text-1);
}

.playlist-count {
  display: block;
  font-size: 13px;
  color: var(--c-text-3);
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
