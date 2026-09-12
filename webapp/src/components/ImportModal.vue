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
                <p class="modal-subtitle">Выборочный импорт треков и плейлистов</p>
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
                placeholder="Вставьте ссылку на трек, плейлист или лайки..."
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
              <span>Пример: <code>soundcloud.com/artist/sets/playlist</code> или <code>.../user/likes</code></span>
            </div>

            <div v-if="scAccount?.connected" class="sc-quick-actions-bar">
              <button class="sc-chip-btn" @click="handleLoadMyLikes">
                <Heart :size="13" />
                <span>Загрузить мои лайки SoundCloud (@{{ scAccount.username }})</span>
              </button>
            </div>

            <!-- Error Banner -->
            <div v-if="errorMessage" class="error-banner">
              <AlertCircle :size="16" class="error-icon" />
              <span>{{ errorMessage }}</span>
            </div>

            <!-- Preview Section -->
            <Transition name="slide-up">
              <div v-if="preview" class="preview-section">
                <!-- Overview Card -->
                <div class="preview-card">
                  <div class="preview-cover">
                    <img v-if="preview.cover_url" :src="preview.cover_url" alt="Cover" />
                    <Music v-else :size="32" class="placeholder-icon" />
                  </div>
                  <div class="preview-info">
                    <div class="preview-badge-row">
                      <span class="preview-badge" :class="preview.provider">
                        {{ preview.provider.toUpperCase() }} • {{ preview.entity_type === 'playlist' ? 'ПЛЕЙЛИСТ' : 'ТРЕК' }}
                      </span>
                      <!-- For single track recognition badge -->
                      <template v-if="preview.tracks?.length === 1">
                        <span v-if="preview.tracks[0].in_library" class="track-badge in-lib">
                          <Check :size="11" /> В медиатеке
                        </span>
                        <span v-else-if="preview.tracks[0].already_in_tg" class="track-badge in-tg">
                          <Zap :size="11" /> В базе TG
                        </span>
                        <span v-else class="track-badge new-track">
                          Новый трек
                        </span>
                      </template>
                    </div>

                    <div class="preview-title" :title="preview.title">{{ preview.title }}</div>
                    <div class="preview-author">{{ preview.author || 'Неизвестный автор' }}</div>
                    <div class="preview-count">
                      {{ preview.track_count }} {{ getTrackWord(preview.track_count) }}
                      <template v-if="preview.tracks?.length > 1 && inLibraryCount > 0">
                        • <span class="accent-lib">{{ inLibraryCount }} уже в медиатеке</span>
                      </template>
                    </div>
                  </div>
                </div>

                <!-- Multiple Tracks: Selection & Checklist -->
                <div v-if="preview.tracks?.length > 1" class="selection-panel">
                  <!-- Toolbar -->
                  <div class="selection-toolbar">
                    <div class="selection-info">
                      <span class="sel-count">Выбрано: <strong>{{ selectedCount }}</strong> из {{ preview.tracks.length }}</span>
                      <div class="tags-row">
                        <span v-if="newTracksCount > 0" class="mini-tag new">{{ newTracksCount }} новых</span>
                        <span v-if="inLibraryCount > 0" class="mini-tag lib">{{ inLibraryCount }} в медиатеке</span>
                        <span v-if="alreadyInTgCount > 0" class="mini-tag tg">{{ alreadyInTgCount }} в TG</span>
                      </div>
                    </div>

                    <div class="toolbar-actions">
                      <button
                        v-if="newTracksCount > 0"
                        class="tool-btn highlight"
                        title="Выбрать только ещё не скачанные треки"
                        @click="selectOnlyNew"
                      >
                        <Sparkles :size="12" />
                        <span>Новые ({{ newTracksCount }})</span>
                      </button>
                      <button class="tool-btn" @click="selectAll">Все</button>
                      <button class="tool-btn" @click="deselectAll">Снять</button>
                    </div>
                  </div>

                  <!-- Scrollable Tracklist -->
                  <div class="tracklist-scroll">
                    <div
                      v-for="(track, idx) in preview.tracks"
                      :key="track.url || idx"
                      class="track-item"
                      :class="{ selected: isSelected(track.url), 'is-in-library': track.in_library }"
                      @click="toggleTrack(track.url)"
                    >
                      <!-- Custom Checkbox -->
                      <div class="custom-checkbox" :class="{ checked: isSelected(track.url) }">
                        <Check v-if="isSelected(track.url)" :size="12" class="check-icon" />
                      </div>

                      <span class="track-idx">{{ idx + 1 }}</span>

                      <div class="track-thumb">
                        <img v-if="track.cover_url" :src="track.cover_url" alt="Thumb" loading="lazy" />
                        <Music v-else :size="14" class="thumb-fallback" />
                      </div>

                      <div class="track-meta">
                        <div class="track-title" :title="track.title">{{ track.title }}</div>
                        <div class="track-artist" :title="track.artist">{{ track.artist }}</div>
                      </div>

                      <div class="track-status">
                        <span v-if="track.in_library" class="track-badge in-lib" title="Трек уже добавлен в вашу медиатеку">
                          <Check :size="11" /> В медиатеке
                        </span>
                        <span v-else-if="track.already_in_tg" class="track-badge in-tg" title="Файл уже есть в базе Telegram. Добавится мгновенно без скачивания!">
                          <Zap :size="11" /> В базе TG
                        </span>
                        <span v-else class="track-badge new-track">
                          Новый
                        </span>
                      </div>

                      <div class="track-duration">
                        {{ formatDuration(track.duration) }}
                      </div>
                    </div>
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

              <!-- Track mini progress for download -->
              <div 
                v-if="activeJob.download_percent !== null && activeJob.download_percent !== undefined && activeJob.status === 'in_progress'"
                class="track-mini-progress"
              >
                <div class="track-mini-bar-track">
                  <div class="track-mini-bar-fill" :style="{ width: `${activeJob.download_percent}%` }"></div>
                </div>
                <div class="track-mini-meta">
                  <span>{{ activeJob.current_step || 'Скачивание аудио 320 kbps' }}</span>
                  <span>{{ activeJob.download_percent }}%</span>
                </div>
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
                :disabled="starting || (preview.tracks?.length > 1 && selectedCount === 0)"
                @click="handleStartImport"
              >
                <div v-if="starting" class="spinner small"></div>
                <template v-else>
                  <template v-if="preview.tracks?.length > 1">
                    Импортировать выбранные ({{ selectedCount }})
                  </template>
                  <template v-else>
                    Импортировать трек
                  </template>
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
  Zap,
  Sparkles,
  Heart,
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
const selectedUrls = ref(new Set())

let pollTimer = null

// Connected SoundCloud account shortcut
const scAccount = ref(null)

const checkScAccount = async () => {
  try {
    const res = await ingestionApi.getSoundCloudAccount()
    if (res.data?.connected) {
      scAccount.value = res.data
    } else {
      scAccount.value = null
    }
  } catch (_) {
    scAccount.value = null
  }
}

const handleLoadMyLikes = () => {
  if (scAccount.value?.profile_url) {
    urlInput.value = `${scAccount.value.profile_url}/likes`
    nextTick(() => {
      handlePreview()
    })
  }
}

const handleReset = () => {
  errorMessage.value = ''
  preview.value = null
  activeJob.value = null
  selectedUrls.value = new Set()
  stopPolling()
}

const isValidUrl = computed(() => {
  const trimmed = urlInput.value.trim().toLowerCase()
  return (
    trimmed.startsWith('http://') ||
    trimmed.startsWith('https://')
  ) && (trimmed.includes('soundcloud.com') || trimmed.includes('spotify.com'))
})

const selectedCount = computed(() => selectedUrls.value.size)

const inLibraryCount = computed(() => {
  if (!preview.value?.tracks) return 0
  return preview.value.tracks.filter(t => t.in_library).length
})

const alreadyInTgCount = computed(() => {
  if (!preview.value?.tracks) return 0
  return preview.value.tracks.filter(t => !t.in_library && t.already_in_tg).length
})

const newTracksCount = computed(() => {
  if (!preview.value?.tracks) return 0
  return preview.value.tracks.filter(t => !t.in_library).length
})

const isSelected = (url) => selectedUrls.value.has(url)

const toggleTrack = (url) => {
  const next = new Set(selectedUrls.value)
  if (next.has(url)) {
    next.delete(url)
  } else {
    next.add(url)
  }
  selectedUrls.value = next
}

const selectAll = () => {
  if (!preview.value?.tracks) return
  selectedUrls.value = new Set(preview.value.tracks.map(t => t.url))
}

const selectOnlyNew = () => {
  if (!preview.value?.tracks) return
  selectedUrls.value = new Set(
    preview.value.tracks.filter(t => !t.in_library).map(t => t.url)
  )
}

const deselectAll = () => {
  selectedUrls.value = new Set()
}

const formatDuration = (seconds) => {
  if (!seconds) return '--:--'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

const statusDescription = computed(() => {
  if (!activeJob.value) return ''
  switch (activeJob.value.status) {
    case 'pending':
      return 'В очереди на импорт...'
    case 'in_progress':
      return activeJob.value.current_step
        ? `${activeJob.value.current_step} • ${activeJob.value.processed_tracks} из ${activeJob.value.total_tracks}`
        : `Импортировано ${activeJob.value.processed_tracks} из ${activeJob.value.total_tracks} треков`
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
      handleReset()
      checkScAccount()
      nextTick(() => {
        inputRef.value?.focus()
      })
    } else {
      handleReset()
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
  selectedUrls.value = new Set()

  try {
    const res = await ingestionApi.preview(urlInput.value.trim())
    preview.value = res.data

    if (preview.value.tracks && preview.value.tracks.length > 0) {
      // By default, select tracks that are not yet in the library!
      const newTracks = preview.value.tracks.filter(t => !t.in_library)
      if (newTracks.length > 0) {
        selectedUrls.value = new Set(newTracks.map(t => t.url))
      } else {
        // If all are in library, select all so user can re-import into a playlist
        selectedUrls.value = new Set(preview.value.tracks.map(t => t.url))
      }
    }
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

  const urlsToImport = (preview.value.tracks && preview.value.tracks.length > 1)
    ? Array.from(selectedUrls.value)
    : null

  try {
    const res = await ingestionApi.start(preview.value.url, urlsToImport)
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
  max-width: 560px;
  max-height: 90vh;
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
  flex-shrink: 0;
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
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  flex-shrink: 0;
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
  padding: 18px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;
  max-height: calc(90vh - 140px);
}

.input-wrapper {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
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

/* Preview Section */
.preview-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
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

.preview-badge-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.preview-badge {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.5px;
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

.accent-lib {
  color: #4ade80;
  font-weight: 500;
}

/* Selection Panel */
.selection-panel {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.selection-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  gap: 10px;
}

.selection-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sel-count {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.85);
}

.sel-count strong {
  color: #ff5500;
  font-weight: 700;
}

.tags-row {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.mini-tag {
  font-size: 0.68rem;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.mini-tag.new {
  background: rgba(255, 85, 0, 0.15);
  color: #ff8800;
}

.mini-tag.lib {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
}

.mini-tag.tg {
  background: rgba(147, 51, 234, 0.15);
  color: #c084fc;
}

.toolbar-actions {
  display: flex;
  gap: 6px;
}

.tool-btn {
  padding: 5px 10px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.75);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.tool-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
}

.tool-btn.highlight {
  background: rgba(255, 85, 0, 0.18);
  border-color: rgba(255, 85, 0, 0.4);
  color: #ff9933;
}

.tool-btn.highlight:hover {
  background: rgba(255, 85, 0, 0.3);
  color: #fff;
}

/* Tracklist Scroll */
.tracklist-scroll {
  max-height: 260px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding: 6px;
  gap: 2px;
}

.tracklist-scroll::-webkit-scrollbar {
  width: 6px;
}

.tracklist-scroll::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
}

.track-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
  user-select: none;
}

.track-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.track-item.selected {
  background: rgba(255, 85, 0, 0.06);
  border-color: rgba(255, 85, 0, 0.15);
}

.track-item.is-in-library:not(.selected) {
  opacity: 0.75;
}

.custom-checkbox {
  width: 18px;
  height: 18px;
  border-radius: 5px;
  border: 1.5px solid rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
  background: rgba(0, 0, 0, 0.3);
}

.custom-checkbox.checked {
  background: #ff5500;
  border-color: #ff5500;
  color: #fff;
  box-shadow: 0 0 8px rgba(255, 85, 0, 0.4);
}

.check-icon {
  color: #fff;
}

.track-idx {
  width: 20px;
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.35);
  text-align: center;
  flex-shrink: 0;
}

.track-thumb {
  width: 34px;
  height: 34px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
  background: #1e1e24;
  display: flex;
  align-items: center;
  justify-content: center;
}

.track-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-fallback {
  color: rgba(255, 255, 255, 0.3);
}

.track-meta {
  flex: 1;
  min-width: 0;
}

.track-title {
  font-size: 0.85rem;
  font-weight: 500;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-artist {
  font-size: 0.73rem;
  color: rgba(255, 255, 255, 0.5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 1px;
}

.track-status {
  flex-shrink: 0;
}

.track-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.68rem;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 6px;
  white-space: nowrap;
}

.track-badge.in-lib {
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #4ade80;
}

.track-badge.in-tg {
  background: rgba(147, 51, 234, 0.15);
  border: 1px solid rgba(147, 51, 234, 0.3);
  color: #c084fc;
}

.track-badge.new-track {
  background: rgba(255, 85, 0, 0.1);
  border: 1px solid rgba(255, 85, 0, 0.25);
  color: #ff8800;
}

.track-duration {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.4);
  width: 38px;
  text-align: right;
  flex-shrink: 0;
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
  flex-shrink: 0;
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

.sc-quick-actions-bar {
  margin-top: 8px;
  display: flex;
}

.sc-chip-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(255, 85, 0, 0.12);
  border: 1px solid rgba(255, 85, 0, 0.3);
  border-radius: 999px;
  color: #ff7700;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-chip-btn:hover {
  background: #ff5500;
  color: #fff;
  border-color: #ff5500;
  box-shadow: 0 2px 8px rgba(255, 85, 0, 0.3);
}

.track-mini-progress {
  margin-top: 12px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
}

.track-mini-bar-track {
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 6px;
}

.track-mini-bar-fill {
  height: 100%;
  background: #ff7700;
  border-radius: 2px;
  transition: width 0.2s ease;
}

.track-mini-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #ff9944;
  font-weight: 500;
}
</style>
