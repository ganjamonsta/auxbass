<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
        <div class="modal">
          <div class="modal-header">
            <h3>Редактирование трека</h3>
            <button class="modal-close" @click="$emit('close')"><X :size="20" /></button>
          </div>

          <form @submit.prevent="handleSubmit" class="modal-form">
            <div class="form-group">
              <label>Название</label>
              <input 
                v-model="form.title" 
                type="text" 
                placeholder="Название трека"
                class="form-input"
              />
            </div>

            <div class="form-group">
              <label>Исполнитель</label>
              <input 
                v-model="form.artist" 
                type="text" 
                placeholder="Имя исполнителя"
                class="form-input"
              />
            </div>

            <div class="form-group">
              <label>Альбом</label>
              <input 
                v-model="form.album" 
                type="text" 
                placeholder="Название альбома"
                class="form-input"
              />
            </div>

            <div class="form-group">
              <label>Жанр</label>
              <input 
                v-model="form.genre" 
                type="text" 
                placeholder="Жанр музыки"
                class="form-input"
              />
            </div>

            <div class="modal-actions">
              <button type="button" class="btn-secondary" @click="$emit('close')">
                Отмена
              </button>
              <button type="submit" class="btn-primary" :disabled="saving">
                {{ saving ? 'Сохранение...' : 'Сохранить' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, inject } from 'vue'
import { useLibraryStore } from '../stores/library'
import { X } from 'lucide-vue-next'

const props = defineProps({
  show: Boolean,
  track: Object
})

const emit = defineEmits(['close', 'saved'])

const library = useLibraryStore()
const telegram = inject('telegram')

const saving = ref(false)
const form = ref({
  title: '',
  artist: '',
  album: '',
  genre: ''
})

// Reset form when track changes
watch(() => props.track, (track) => {
  if (track) {
    form.value = {
      title: track.title || '',
      artist: track.artist || '',
      album: track.album_name || track.album?.name || '',
      genre: track.genre || ''
    }
  }
}, { immediate: true })

const handleSubmit = async () => {
  if (!props.track) return
  
  saving.value = true
  try {
    const updated = await library.updateTrack(props.track.id, form.value)
    if (updated) {
      telegram?.HapticFeedback?.notificationOccurred?.('success')
      emit('saved', updated)
      emit('close')
    }
  } catch (error) {
    console.error('Failed to update track:', error)
    telegram?.HapticFeedback?.notificationOccurred?.('error')
  } finally {
    saving.value = false
  }
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
  overflow-y: overlay;
  overflow-x: hidden;
  scrollbar-gutter: auto;
  box-shadow: 
    12px 12px 24px var(--sh-dark)),
    -6px -6px 12px var(--sh-light)),
    0 0 40px rgba(0, 0, 0, 0.5);
}

.modal::-webkit-scrollbar {
  width: 6px;
  background: transparent;
}

.modal::-webkit-scrollbar-track {
  background: transparent;
}

.modal::-webkit-scrollbar-thumb {
  background: var(--c-accent-glow));
  border-radius: 3px;
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

.modal-form {
  padding: 22px;
}

.form-group {
  margin-bottom: 18px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-3);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-input {
  width: 100%;
  padding: 14px 16px;
  border: none;
  border-radius: var(--r-md);
  background: var(--c-bg-3);
  color: var(--c-text-1);
  font-size: 16px;
  outline: none;
  transition: all 0.2s ease;
  box-shadow: 
    inset 4px 4px 8px var(--sh-inset-dark)),
    inset -2px -2px 4px var(--sh-inset-light));
}

.form-input:focus {
  box-shadow: 
    inset 4px 4px 8px var(--sh-inset-dark)),
    inset -2px -2px 4px var(--sh-inset-light)),
    0 0 0 2px var(--c-accent);
}

.form-input::placeholder {
  color: var(--c-text-3);
}

.modal-actions {
  display: flex;
  gap: 14px;
  margin-top: 28px;
}

.btn-primary,
.btn-secondary {
  flex: 1;
  padding: 16px;
  border: none;
  border-radius: var(--r-md);
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-primary {
  background: linear-gradient(180deg, var(--c-accent) 0%, var(--c-accent-dark) 100%);
  color: white;
  box-shadow: 
    4px 4px 10px var(--sh-dark)),
    -2px -2px 6px var(--sh-light)),
    0 4px 15px var(--c-accent-glow));
}

.btn-primary:active {
  transform: scale(0.98);
  box-shadow: 
    inset 3px 3px 6px rgba(0, 0, 0, 0.3),
    inset -2px -2px 4px rgba(255, 255, 255, 0.1);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--c-bg-3);
  color: var(--c-text-2);
  box-shadow: 
    4px 4px 10px var(--sh-dark)),
    -2px -2px 6px var(--sh-light));
}

.btn-secondary:active {
  box-shadow: 
    inset 2px 2px 4px var(--sh-inset-dark)),
    inset -1px -1px 2px var(--sh-inset-light));
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
