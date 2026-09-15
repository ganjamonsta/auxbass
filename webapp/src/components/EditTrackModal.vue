<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
        <div class="modal" :class="{ 'with-automatch': showAutoMatch }">
          <div class="modal-header">
            <h3>Редактирование трека</h3>
            <button class="modal-close" @click="$emit('close')"><X :size="20" /></button>
          </div>

          <form @submit.prevent="handleSubmit" class="modal-form">
            <!-- Cover section -->
            <div class="cover-section">
              <div class="cover-preview-box">
                <img 
                  v-if="currentCoverUrl" 
                  :src="currentCoverUrl" 
                  alt="Track Cover" 
                  class="cover-preview-img" 
                />
                <div v-else class="cover-placeholder-box">
                  <Music :size="28" />
                </div>
                <div v-if="coverLoading" class="cover-spinner-overlay">
                  <div class="cover-spinner"></div>
                </div>
              </div>

              <div class="cover-info-and-actions">
                <div class="cover-section-title">Обложка трека</div>
                <div class="cover-action-buttons">
                  <button 
                    type="button" 
                    class="cover-btn automatch-btn" 
                    :class="{ active: showAutoMatch }"
                    @click="toggleAutoMatch" 
                    :disabled="coverLoading"
                    title="Автоматический подбор качественной обложки"
                  >
                    <Wand2 :size="13" />
                    <span>Автоподбор</span>
                  </button>

                  <button 
                    type="button" 
                    class="cover-btn upload-btn" 
                    @click="triggerFileInput" 
                    :disabled="coverLoading"
                    title="Загрузить свою обложку"
                  >
                    <Upload :size="13" />
                    <span>Файл</span>
                  </button>

                  <button 
                    v-if="currentCoverUrl" 
                    type="button" 
                    class="cover-btn remove-btn" 
                    @click="removeCover" 
                    :disabled="coverLoading"
                    title="Удалить обложку"
                  >
                    <Trash2 :size="13" />
                  </button>

                  <input
                    ref="fileInputRef"
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    class="hidden-cover-input"
                    @change="handleCoverFileChange"
                  />
                </div>
              </div>
            </div>

            <!-- Auto-match suggestions drawer -->
            <Transition name="slide-expand">
              <div v-if="showAutoMatch" class="automatch-panel">
                <div class="automatch-header">
                  <div class="automatch-search-row">
                    <div class="automatch-input-wrapper">
                      <Search :size="14" class="search-icon" />
                      <input
                        v-model="autoMatchQuery"
                        type="text"
                        placeholder="Поиск по артисту и названию..."
                        class="automatch-input"
                        @keyup.enter="handleSearchSuggestions"
                      />
                      <button 
                        v-if="autoMatchQuery" 
                        type="button" 
                        class="clear-query-btn" 
                        @click="autoMatchQuery = ''"
                      >
                        <X :size="13" />
                      </button>
                    </div>
                    <button 
                      type="button" 
                      class="automatch-search-btn" 
                      @click="handleSearchSuggestions"
                      :disabled="loadingSuggestions"
                      title="Искать"
                    >
                      <RefreshCw :size="13" :class="{ 'spinning': loadingSuggestions }" />
                    </button>
                  </div>
                </div>

                <!-- Suggestions Container -->
                <div class="suggestions-container">
                  <div v-if="loadingSuggestions" class="suggestions-loading">
                    <div class="cover-spinner"></div>
                    <span>Поиск обложек в Apple Music и Deezer...</span>
                  </div>

                  <div v-else-if="suggestions.length > 0" class="suggestions-grid">
                    <div
                      v-for="sug in suggestions"
                      :key="sug.id"
                      class="suggestion-card"
                      :class="{ 'is-selected': selectedSuggestionId === sug.id }"
                      @click="applySuggestion(sug)"
                    >
                      <div class="suggestion-img-wrapper">
                        <img 
                          :src="getCoverUrl(sug.cover_url, CoverSize.MEDIUM)" 
                          :alt="sug.album || sug.title"
                          class="suggestion-img"
                          loading="lazy"
                        />
                        <span 
                          class="source-badge"
                          :class="sug.source === 'itunes' ? 'badge-apple' : 'badge-deezer'"
                        >
                          {{ sug.source === 'itunes' ? 'Apple Music' : 'Deezer' }}
                        </span>
                        <div v-if="selectedSuggestionId === sug.id" class="suggestion-check-overlay">
                          <Check :size="18" />
                        </div>
                      </div>
                      <div class="suggestion-meta">
                        <div class="suggestion-album" :title="sug.album || sug.title">
                          {{ sug.album || sug.title || 'Сингл' }}
                        </div>
                        <div class="suggestion-sub">
                          <span v-if="sug.year">{{ sug.year }}</span>
                          <span v-if="sug.year && sug.artist" class="bullet">•</span>
                          <span class="suggestion-artist" :title="sug.artist">{{ sug.artist }}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-else class="suggestions-empty">
                    <ImageIcon :size="28" class="empty-icon" />
                    <p>По запросу «{{ autoMatchQuery }}» ничего не найдено</p>
                    <span class="hint">Попробуйте ввести оригинальное имя артиста на английском</span>
                  </div>
                </div>
              </div>
            </Transition>

            <!-- Metadata text fields -->
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
import { ref, computed, watch, inject } from 'vue'
import { useLibraryStore } from '../stores/library'
import { useUIStore } from '../stores/ui'
import { tracksApi } from '../api/tracks'
import { getCoverUrl, CoverSize } from '@/utils'
import { 
  X, Upload, Trash2, Wand2, Search, Image as ImageIcon,
  Music, Check, RefreshCw 
} from 'lucide-vue-next'

const props = defineProps({
  show: Boolean,
  track: Object
})

const emit = defineEmits(['close', 'saved'])

const library = useLibraryStore()
const uiStore = useUIStore()
const telegram = inject('telegram')

const saving = ref(false)
const coverLoading = ref(false)
const fileInputRef = ref(null)

const form = ref({
  title: '',
  artist: '',
  album: '',
  genre: ''
})

const customCoverUrl = ref(null)

// Auto-match state
const showAutoMatch = ref(false)
const autoMatchQuery = ref('')
const suggestions = ref([])
const loadingSuggestions = ref(false)
const selectedSuggestionId = ref(null)

const currentCoverUrl = computed(() => {
  if (customCoverUrl.value) {
    return getCoverUrl(customCoverUrl.value, CoverSize.MEDIUM)
  }
  const raw = props.track?.cover_url || props.track?.enrichment?.cover_url
  return raw ? getCoverUrl(raw, CoverSize.MEDIUM) : null
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
    customCoverUrl.value = track.cover_url || track.enrichment?.cover_url || null
    selectedSuggestionId.value = null
    showAutoMatch.value = false
    suggestions.value = []
  }
}, { immediate: true })

watch(() => props.show, (show) => {
  if (!show) {
    showAutoMatch.value = false
    suggestions.value = []
    loadingSuggestions.value = false
    selectedSuggestionId.value = null
  }
})

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleCoverFileChange = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    uiStore.toast?.error('Ошибка', 'Выберите файл изображения (JPG, PNG, WebP)')
    return
  }

  coverLoading.value = true
  try {
    const res = await library.uploadTrackCover(props.track.id, file)
    customCoverUrl.value = res.cover_url
    telegram?.HapticFeedback?.notificationOccurred?.('success')
    uiStore.toast?.success('Обложка обновлена', 'Файл успешно загружен в Telegram')
  } catch (error) {
    console.error('Failed to upload track cover:', error)
    telegram?.HapticFeedback?.notificationOccurred?.('error')
    const errMsg = error?.response?.data?.detail || 'Не удалось загрузить обложку'
    uiStore.toast?.error('Ошибка загрузки', errMsg)
  } finally {
    coverLoading.value = false
    if (fileInputRef.value) fileInputRef.value.value = ''
  }
}

const removeCover = async () => {
  if (!props.track) return
  coverLoading.value = true
  try {
    await library.deleteTrackCover(props.track.id)
    customCoverUrl.value = null
    selectedSuggestionId.value = null
    telegram?.HapticFeedback?.notificationOccurred?.('success')
    uiStore.toast?.info('Обложка удалена', 'Обложка трека сброшена')
  } catch (error) {
    console.error('Failed to delete track cover:', error)
    telegram?.HapticFeedback?.notificationOccurred?.('error')
    uiStore.toast?.error('Ошибка', 'Не удалось удалить обложку')
  } finally {
    coverLoading.value = false
  }
}

const toggleAutoMatch = () => {
  showAutoMatch.value = !showAutoMatch.value
  if (showAutoMatch.value) {
    const q = `${form.value.artist || ''} ${form.value.title || ''}`.trim()
    autoMatchQuery.value = q || props.track?.title || ''
    if (suggestions.value.length === 0) {
      handleSearchSuggestions()
    }
  }
}

const handleSearchSuggestions = async () => {
  if (!props.track || !autoMatchQuery.value.trim()) return
  loadingSuggestions.value = true
  try {
    const res = await tracksApi.getCoverSuggestions(props.track.id, autoMatchQuery.value.trim())
    suggestions.value = res.data || []
  } catch (error) {
    console.error('Failed to fetch cover suggestions:', error)
    uiStore.toast?.error('Ошибка поиска', 'Не удалось получить варианты обложек')
  } finally {
    loadingSuggestions.value = false
  }
}

const applySuggestion = async (sug) => {
  if (!props.track || !sug.cover_url) return
  coverLoading.value = true
  selectedSuggestionId.value = sug.id
  try {
    const res = await library.setTrackCover(props.track.id, sug.cover_url)
    customCoverUrl.value = res.cover_url
    
    // Autofill album if empty in form
    if (sug.album && (!form.value.album || !form.value.album.trim())) {
      form.value.album = sug.album
    }

    telegram?.HapticFeedback?.notificationOccurred?.('success')
    const sourceLabel = sug.source === 'itunes' ? 'Apple Music' : 'Deezer'
    uiStore.toast?.success('Обложка установлена', `Оригинал из ${sourceLabel} сохранён`)
  } catch (error) {
    console.error('Failed to apply cover suggestion:', error)
    telegram?.HapticFeedback?.notificationOccurred?.('error')
    uiStore.toast?.error('Ошибка', 'Не удалось установить выбранную обложку')
    selectedSuggestionId.value = null
  } finally {
    coverLoading.value = false
  }
}

const handleSubmit = async () => {
  if (!props.track) return
  
  saving.value = true
  try {
    const updated = await library.updateTrack(props.track.id, form.value)
    if (updated) {
      telegram?.HapticFeedback?.notificationOccurred?.('success')
      uiStore.toast?.success('Сохранено', 'Данные трека обновлены')
      emit('saved', updated)
      emit('close')
    }
  } catch (error) {
    console.error('Failed to update track:', error)
    telegram?.HapticFeedback?.notificationOccurred?.('error')
    const errMsg = error?.response?.data?.detail || 'Не удалось обновить трек'
    uiStore.toast?.error('Ошибка сохранения', errMsg)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal, 1200);
  padding: 16px;
}

.modal {
  background: var(--c-bg-2);
  border-radius: var(--r-xl);
  width: 100%;
  max-width: 440px;
  max-height: 90vh;
  overflow-y: overlay;
  overflow-x: hidden;
  scrollbar-gutter: auto;
  box-shadow: 
    12px 12px 24px var(--sh-dark),
    -6px -6px 12px var(--sh-light),
    0 0 40px rgba(0, 0, 0, 0.5);
  transition: max-width 0.25s ease;
}

.modal.with-automatch {
  max-width: 500px;
}

.modal::-webkit-scrollbar {
  width: 6px;
  background: transparent;
}

.modal::-webkit-scrollbar-track {
  background: transparent;
}

.modal::-webkit-scrollbar-thumb {
  background: var(--c-accent-glow);
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
    4px 4px 8px var(--sh-dark),
    -2px -2px 4px var(--sh-light);
  transition: all 0.15s ease;
}

.modal-close:active {
  box-shadow: 
    inset 2px 2px 4px var(--sh-inset-dark),
    inset -1px -1px 2px var(--sh-inset-light);
}

.modal-form {
  padding: 20px 22px;
}

/* Cover Section */
.cover-section {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  background: var(--c-bg-3);
  border-radius: var(--r-lg);
  margin-bottom: 18px;
  box-shadow: 
    inset 2px 2px 5px var(--sh-inset-dark),
    inset -1px -1px 3px var(--sh-inset-light);
}

.cover-preview-box {
  width: 68px;
  height: 68px;
  border-radius: 10px;
  background: var(--c-bg-2);
  border: 1px solid var(--c-bg-4);
  overflow: hidden;
  position: relative;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 
    4px 4px 8px var(--sh-dark),
    -2px -2px 4px var(--sh-light);
}

.cover-preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder-box {
  color: var(--c-text-3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-spinner-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-spinner {
  width: 22px;
  height: 22px;
  border: 2.5px solid rgba(255, 255, 255, 0.25);
  border-top-color: var(--c-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.cover-info-and-actions {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.cover-section-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--c-text-2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.cover-action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.cover-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 8px;
  border: 1px solid var(--c-bg-4);
  background: var(--c-bg-2);
  color: var(--c-text-1);
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 
    3px 3px 6px var(--sh-dark),
    -1px -1px 3px var(--sh-light);
}

.cover-btn:hover:not(:disabled) {
  background: var(--c-bg-4);
  transform: translateY(-1px);
}

.cover-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 
    inset 2px 2px 4px var(--sh-inset-dark),
    inset -1px -1px 2px var(--sh-inset-light);
}

.cover-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.automatch-btn {
  background: linear-gradient(135deg, rgba(29, 185, 84, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
  border-color: rgba(29, 185, 84, 0.3);
  color: var(--c-accent);
}

.automatch-btn.active {
  background: var(--c-accent);
  color: #000;
  font-weight: 700;
  box-shadow: 0 0 12px var(--c-accent-glow);
}

.remove-btn {
  color: #ff5555;
  padding: 6px 8px;
}

.remove-btn:hover:not(:disabled) {
  background: rgba(255, 85, 85, 0.15);
  border-color: rgba(255, 85, 85, 0.3);
}

.hidden-cover-input {
  display: none;
}

/* Auto-Match Panel */
.automatch-panel {
  background: var(--c-bg-1);
  border-radius: var(--r-lg);
  padding: 14px;
  margin-bottom: 20px;
  border: 1px solid var(--c-bg-3);
  box-shadow: 
    inset 3px 3px 6px var(--sh-inset-dark),
    inset -1px -1px 3px var(--sh-inset-light);
}

.automatch-header {
  margin-bottom: 12px;
}

.automatch-search-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.automatch-input-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.automatch-input-wrapper .search-icon {
  position: absolute;
  left: 12px;
  color: var(--c-text-3);
  pointer-events: none;
}

.automatch-input {
  width: 100%;
  padding: 8px 32px 8px 34px;
  border: 1px solid var(--c-bg-4);
  border-radius: 8px;
  background: var(--c-bg-2);
  color: var(--c-text-1);
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.automatch-input:focus {
  border-color: var(--c-accent);
}

.clear-query-btn {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  color: var(--c-text-3);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
}

.automatch-search-btn {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  border: 1px solid var(--c-bg-4);
  background: var(--c-bg-3);
  color: var(--c-text-1);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.automatch-search-btn:hover:not(:disabled) {
  background: var(--c-bg-4);
  color: var(--c-accent);
}

.suggestions-container {
  max-height: 250px;
  overflow-y: auto;
  padding-right: 4px;
}

.suggestions-container::-webkit-scrollbar {
  width: 5px;
}

.suggestions-container::-webkit-scrollbar-thumb {
  background: var(--c-bg-4);
  border-radius: 3px;
}

.suggestions-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  gap: 12px;
  color: var(--c-text-3);
  font-size: 13px;
}

.suggestions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(115px, 1fr));
  gap: 10px;
}

.suggestion-card {
  background: var(--c-bg-2);
  border: 1px solid var(--c-bg-4);
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
}

.suggestion-card:hover {
  transform: translateY(-2px);
  border-color: var(--c-accent);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.suggestion-card.is-selected {
  border-color: var(--c-accent);
  box-shadow: 0 0 0 2px var(--c-accent);
}

.suggestion-img-wrapper {
  position: relative;
  width: 100%;
  padding-top: 100%; /* 1:1 Aspect ratio */
  background: var(--c-bg-3);
}

.suggestion-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.source-badge {
  position: absolute;
  top: 5px;
  right: 5px;
  font-size: 9px;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: 4px;
  letter-spacing: 0.2px;
  backdrop-filter: blur(4px);
}

.badge-apple {
  background: rgba(250, 45, 72, 0.85);
  color: #fff;
}

.badge-deezer {
  background: rgba(162, 56, 255, 0.85);
  color: #fff;
}

.suggestion-check-overlay {
  position: absolute;
  inset: 0;
  background: rgba(29, 185, 84, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.suggestion-meta {
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.suggestion-album {
  font-size: 11px;
  font-weight: 600;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.suggestion-sub {
  font-size: 10px;
  color: var(--c-text-3);
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.suggestion-artist {
  overflow: hidden;
  text-overflow: ellipsis;
}

.bullet {
  opacity: 0.5;
}

.suggestions-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  text-align: center;
  gap: 8px;
  color: var(--c-text-3);
}

.empty-icon {
  color: var(--c-text-3);
  opacity: 0.5;
}

.suggestions-empty p {
  font-size: 13px;
  margin: 0;
}

.suggestions-empty .hint {
  font-size: 11px;
  color: var(--c-text-3);
  opacity: 0.7;
}

/* Form fields */
.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-3);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-input {
  width: 100%;
  padding: 12px 14px;
  border: none;
  border-radius: var(--r-md);
  background: var(--c-bg-3);
  color: var(--c-text-1);
  font-size: 15px;
  outline: none;
  transition: all 0.2s ease;
  box-shadow: 
    inset 4px 4px 8px var(--sh-inset-dark),
    inset -2px -2px 4px var(--sh-inset-light);
}

.form-input:focus {
  box-shadow: 
    inset 4px 4px 8px var(--sh-inset-dark),
    inset -2px -2px 4px var(--sh-inset-light),
    0 0 0 2px var(--c-accent);
}

.form-input::placeholder {
  color: var(--c-text-3);
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
  border-radius: var(--r-md);
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-primary {
  background: linear-gradient(180deg, var(--c-accent) 0%, var(--c-accent-dark) 100%);
  color: white;
  box-shadow: 
    4px 4px 10px var(--sh-dark),
    -2px -2px 6px var(--sh-light),
    0 4px 15px var(--c-accent-glow);
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
    4px 4px 10px var(--sh-dark),
    -2px -2px 6px var(--sh-light);
}

.btn-secondary:active {
  box-shadow: 
    inset 2px 2px 4px var(--sh-inset-dark),
    inset -1px -1px 2px var(--sh-inset-light);
}

/* Animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-expand-enter-active,
.slide-expand-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}

.slide-expand-enter-from,
.slide-expand-leave-to {
  opacity: 0;
  transform: translateY(-8px);
  max-height: 0;
  margin-bottom: 0;
  padding-top: 0;
  padding-bottom: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinning {
  animation: spin 0.8s linear infinite;
}
</style>
