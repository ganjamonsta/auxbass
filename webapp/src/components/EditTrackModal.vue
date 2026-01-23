<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
        <div class="modal">
          <div class="modal-header">
            <h3>Редактирование трека</h3>
            <button class="modal-close" @click="$emit('close')">✕</button>
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
      album: track.album || '',
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
  max-height: 90vh;
  overflow-y: auto;
  overflow-x: hidden;
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

.modal-form {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--tg-theme-hint-color);
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--tg-theme-secondary-bg-color);
  border-radius: 10px;
  background: var(--tg-theme-secondary-bg-color);
  color: var(--tg-theme-text-color);
  font-size: 16px;
  outline: none;
  transition: border-color 0.2s;
}

.form-input:focus {
  border-color: var(--tg-theme-button-color);
}

.form-input::placeholder {
  color: var(--tg-theme-hint-color);
}

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn-primary,
.btn-secondary {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-primary {
  background: var(--tg-theme-button-color);
  color: var(--tg-theme-button-text-color);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--tg-theme-secondary-bg-color);
  color: var(--tg-theme-text-color);
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
