<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="show" class="import-modal-backdrop" @click.self="handleClose">
        <div class="import-modal-container">
          <!-- Header -->
          <div class="modal-header">
            <div class="header-left">
              <div class="icon-badge">
                <CloudDownload :size="20" class="badge-icon" />
              </div>
              <div class="header-titles">
                <h3 class="modal-title">Импорт музыки</h3>
                <p class="modal-subtitle">Добавление треков и плейлистов из внешних сервисов</p>
              </div>
            </div>
            <button class="close-btn" @click="handleClose" title="Закрыть">
              <X :size="18" />
            </button>
          </div>

          <!-- Service Pills -->
          <div class="services-row">
            <div class="service-pill sc active">
              <span class="sc-dot"></span>
              <span class="pill-name">SoundCloud</span>
              <span class="pill-status ready">Работает</span>
            </div>
            <div class="service-pill sp">
              <span class="sp-dot"></span>
              <span class="pill-name">Spotify</span>
              <span class="pill-status soon">Этап 2</span>
            </div>
          </div>

          <!-- Body: Input & Preview -->
          <div v-if="!activeJob" class="modal-body">
            <div class="input-wrapper">
              <input
                ref="inputRef"
                v-model="urlInput"
                type="url"
                placeholder="Вставьте ссылку на трек или плейлист..."
                class="url-input"
                :disabled="resolving"
                @keydown.enter="handlePreview"
              />
              <button
                class="action-btn"
                :disabled="!isValidUrl || resolving"
                @click="handlePreview"
              >
                <div v-if="resolving" class="spinner small"></div>
                <template v-else>Найти</template>
              </button>
            </div>

            <div class="hints-row">
              <span>Пример: <code>soundcloud.com/artist/track-name</code></span>
            </div>

            <!-- Error Banner -->
            <div v-if="errorMessage" class="error-banner">
              <AlertCircle :size="16" class="error-icon" />
              <span>{{ errorMessage }}</span>
            </div>

            <!-- Preview Card -->
            <Transition name="slide-up">
              <div v-if="preview" class="preview-card">
                <div class="preview-cover">
                  <img v-if="preview.cover_url" :src="preview.cover_url" alt="Cover" />
                  <Music v-else :size="32" class="placeholder-icon" />
                </div>
                <div class="preview-info">
                  <div class="preview-badge" :class="preview.provider">
                    {{ preview.provider.toUpperCase() }} • {{ preview.entity_type === 'playlist' ? 'ПЛЕЙЛИСТ' : 'ТРЕК' }}
                  </div>
                  <div class="preview-title" :title="preview.title">{{ preview.title }}</div>
                  <div class="preview-author">{{ preview.author || 'Неизвестный автор' }}</div>
                  <div class="preview-count">
                    {{ preview.track_count }} {{ getTrackWord(preview.track_count) }}
                  </div>
                </div>
              </div>
            </Transition>
          </div>

          <!-- Body: Progress View -->
          <div v-else class="progress-body">
            <div class="progress-card">
              <div class="progress-cover">
                <img v-if="activeJob.cover_url" :src="activeJob.cover_url" alt="Cover" />
                <Music v-else :size="32" class="placeholder-icon" />
              </div>
              <div class="progress-details">
                <div class="progress-title">{{ activeJob.title }}</div>
                <div class="progress-subtitle">{{ activeJob.author }}</div>
                
                <div class="status-indicator">
                  <div v-if="activeJob.status === 'in_progress'" class="spinner small"></div>
                  <Check v-else-if="activeJob.status === 'completed'" :size="16" class="success-icon" />
                  <AlertCircle v-else :size="16" class="error-icon" />
                  
                  <span class="status-text">{{ statusDescription }}</span>
                </div>
              </div>
            </div>

            <!-- Progress Bar -->
            <div class="progress-bar-container">
              <div class="progress-bar-header">
                <span class="progress-label">
                  <template v-if="activeJob.current_track_title">
                    {{ activeJob.current_track_title }}
                  </template>
                  <template v-else-if="activeJob.status === 'completed'">
                    Успешно завершено!
                  </template>
                  <template v-else>
                    Подготовка к загрузке...
                  </template>
                </span>
                <span class="progress-stats">
                  {{ activeJob.processed_tracks }} / {{ activeJob.total_tracks }} ({{ activeJob.progress_percent }}%)
                </span>
              </div>
              <div class="progress-track">
                <div
                  class="progress-fill"
                  :style="{ width: `${activeJob.progress_percent}%` }"
                  :class="{ completed: activeJob.status === 'completed' }"
                ></div>
              </div>
            </div>
          </div>

          <!-- Footer Actions -->
          <div class="modal-footer">
            <template v-if="!activeJob">
              <button class="btn-cancel" @click="handleClose">Отмена</button>
              <button
                v-if="preview"
                class="btn-primary"
                :disabled="starting"
                @click="handleStartImport"
              >
                <div v-if="starting" class="spinner small"></div>
                <template v-else>
                  Импортировать {{ preview.track_count > 1 ? `(${preview.track_count})` : '' }}
                </template>
              </button>
            </template>
            <template v-else>
              <button
                v-if="activeJob.status === 'in_progress'"
                class="btn-cancel"
                @click="handleCancelJob"
              >
                Отменить
              </button>
              <button
                v-else
                class="btn-primary"
                @click="handleDone"
              >
                Готово
              </button>
            </template>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onUnmounted, nextTick } from 'vue'
import {
  X,
  CloudDownload,
  AlertCircle,
  Music,
  Check,
} from 'lucide-vue-next'
import { ingestionApi } from '../api/client'
import { useRouter } from 'vue-router'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'imported'])
const router = useRouter()

const inputRef = ref(null)
const urlInput = ref('')
const resolving = ref(false)
const starting = ref(false)
const preview = ref(null)
const errorMessage = ref('')
const activeJob = ref(null)

let pollTimer = null

const isValidUrl = computed(() => {
  const trimmed = urlInput.value.trim().toLowerCase()
  return (
    trimmed.startsWith('http://') ||
    trimmed.startsWith('https://')
  ) && (trimmed.includes('soundcloud.com') || trimmed.includes('spotify.com'))
})

const statusDescription = computed(() => {
  if (!activeJob.value) return ''
  switch (activeJob.value.status) {
    case 'pending':
      return 'В очереди на импорт...'
    case 'in_progress':
      return `Импортировано ${activeJob.value.processed_tracks} из ${activeJob.value.total_tracks} треков`
    case 'completed':
      return `Готово! Добавлено ${activeJob.value.imported_track_ids?.length || activeJob.value.processed_tracks} треков`
    case 'failed':
      return activeJob.value.error_message || 'Ошибка импорта'
    case 'cancelled':
      return 'Импорт отменён'
    default:
      return activeJob.value.status
  }
})

watch(
  () => props.show,
  (val) => {
    if (val) {
      errorMessage.value = ''
      preview.value = null
      activeJob.value = null
      nextTick(() => {
        inputRef.value?.focus()
      })
    } else {
      stopPolling()
    }
  }
)

const handleClose = () => {
  stopPolling()
  emit('close')
}

const getTrackWord = (count) => {
  const rem10 = count % 10
  const rem100 = count % 100
  if (rem100 >= 11 && rem100 <= 19) return 'треков'
  if (rem10 === 1) return 'трек'
  if (rem10 >= 2 && rem10 <= 4) return 'трека'
  return 'треков'
}

const handlePreview = async () => {
  if (!isValidUrl.value || resolving.value) return

  errorMessage.value = ''
  resolving.value = true
  preview.value = null

  try {
    const res = await ingestionApi.preview(urlInput.value.trim())
    preview.value = res.data
  } catch (err) {
    const detail = err.response?.data?.detail || err.message || 'Ошибка поиска ссылки'
    errorMessage.value = detail
  } finally {
    resolving.value = false
  }
}

const handleStartImport = async () => {
  if (!preview.value || starting.value) return

  errorMessage.value = ''
  starting.value = true

  try {
    const res = await ingestionApi.start(preview.value.url)
    activeJob.value = res.data
    startPolling(activeJob.value.id)
  } catch (err) {
    const detail = err.response?.data?.detail || err.message || 'Не удалось запустить импорт'
    errorMessage.value = detail
  } finally {
    starting.value = false
  }
}

const startPolling = (jobId) => {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const res = await ingestionApi.getJob(jobId)
      activeJob.value = res.data
      if (
        res.data.status === 'completed' ||
        res.data.status === 'failed' ||
        res.data.status === 'cancelled'
      ) {
        stopPolling()
        if (res.data.status === 'completed') {
          emit('imported', res.data)
        }
      }
    } catch (err) {
      console.warn('Job poll error:', err)
    }
  }, 1500)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const handleCancelJob = async () => {
  if (!activeJob.value) return
  try {
    await ingestionApi.cancelJob(activeJob.value.id)
    activeJob.value.status = 'cancelled'
    stopPolling()
  } catch (err) {
    console.error('Failed to cancel job:', err)
  }
}

const handleDone = () => {
  const plId = activeJob.value?.playlist_id
  handleClose()
  if (plId) {
    router.push(`/playlist/${plId}`)
  }
}

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.import-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 16px;
}

.import-modal-container {
  width: 100%;
  max-width: 520px;
  background: #141416;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: modal-pop 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modal-pop {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Header */
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.icon-badge {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(255, 85, 0, 0.2), rgba(29, 185, 84, 0.2));
  border: 1px solid rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.modal-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #fff;
  margin: 0;
}

.modal-subtitle {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  margin: 2px 0 0;
}

.close-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.2s;
}

.close-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

/* Service Pills */
.services-row {
  display: flex;
  gap: 10px;
  padding: 14px 24px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.service-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 30px;
  font-size: 0.82rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.7);
}

.service-pill.active {
  background: rgba(255, 85, 0, 0.12);
  border-color: rgba(255, 85, 0, 0.35);
  color: #fff;
}

.sc-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ff5500;
}

.sp-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #1db954;
}

.pill-status {
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 6px;
}

.pill-status.ready {
  background: rgba(29, 185, 84, 0.2);
  color: #22c55e;
}

.pill-status.soon {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.4);
}

/* Body */
.modal-body {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.input-wrapper {
  display: flex;
  gap: 10px;
}

.url-input {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  padding: 12px 16px;
  color: #fff;
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.2s;
}

.url-input:focus {
  border-color: #ff5500;
}

.action-btn {
  padding: 0 20px;
  background: #ff5500;
  color: #fff;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s;
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.hints-row {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.hints-row code {
  background: rgba(255, 255, 255, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.7);
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
  padding: 10px 14px;
  border-radius: 10px;
  color: #fca5a5;
  font-size: 0.85rem;
}

/* Preview Card */
.preview-card {
  display: flex;
  gap: 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 14px;
  align-items: center;
}

.preview-cover {
  width: 72px;
  height: 72px;
  border-radius: 10px;
  overflow: hidden;
  background: #1e1e24;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.3);
}

.preview-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-info {
  flex: 1;
  min-width: 0;
}

.preview-badge {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
  color: #ff5500;
}

.preview-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preview-author {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 2px;
}

.preview-count {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 4px;
}

/* Progress Body */
.progress-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.progress-card {
  display: flex;
  gap: 16px;
  align-items: center;
}

.progress-cover {
  width: 64px;
  height: 64px;
  border-radius: 10px;
  overflow: hidden;
  background: #1e1e24;
  flex-shrink: 0;
}

.progress-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.progress-details {
  flex: 1;
  min-width: 0;
}

.progress-title {
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.progress-subtitle {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 2px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.status-text {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
}

.success-icon {
  color: #22c55e;
}

.error-icon {
  color: #ef4444;
}

.progress-bar-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-bar-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.78rem;
}

.progress-label {
  color: rgba(255, 255, 255, 0.6);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 70%;
}

.progress-stats {
  color: #ff5500;
  font-weight: 600;
}

.progress-track {
  height: 8px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff5500, #ff8800);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-fill.completed {
  background: #22c55e;
}

/* Footer */
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.btn-cancel {
  padding: 10px 18px;
  background: transparent;
  color: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
}

.btn-primary {
  padding: 10px 22px;
  background: #ff5500;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: opacity 0.2s;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.spinner.small {
  width: 14px;
  height: 14px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
