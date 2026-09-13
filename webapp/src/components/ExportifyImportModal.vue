<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="show" class="exportify-backdrop" @click.self="handleClose">
        <div class="exportify-dialog">
          <!-- Header -->
          <div class="modal-header">
            <div class="header-left">
              <div class="sp-icon-badge">
                <Music2 :size="20" class="badge-icon" />
              </div>
              <div class="header-titles">
                <h3 class="modal-title">Импорт Spotify (Exportify CSV)</h3>
                <p class="modal-subtitle">Распознавание треков, защита от дублей и аудио 320 kbps</p>
              </div>
            </div>
            <div class="header-right-actions">
              <button 
                v-if="activeJob && activeJob.status === 'in_progress'"
                class="minimize-btn" 
                @click="handleMinimize" 
                title="Свернуть в фон"
              >
                <Minus :size="16" />
              </button>
              <button class="close-btn" @click="handleClose" title="Закрыть">
                <X :size="18" />
              </button>
            </div>
          </div>

          <!-- Body -->
          <div class="modal-body">
            <!-- Active Ingestion Progress View -->
            <div v-if="activeJob" class="progress-section">
              <div class="progress-card">
                <div class="progress-info-block">
                  <div class="progress-status-badge" :class="activeJob.status">
                    <div v-if="activeJob.status === 'in_progress'" class="spinner small"></div>
                    <Check v-else-if="activeJob.status === 'completed'" :size="15" />
                    <AlertCircle v-else :size="15" />
                    <span>{{ statusText }}</span>
                  </div>
                  <h4 class="progress-job-title">{{ activeJob.title || 'Импорт Spotify' }}</h4>
                  <div class="progress-current-track-wrap" v-if="activeJob.current_track_title">
                    <p class="progress-current-track">
                      {{ activeJob.current_track_title }}
                    </p>
                    <span v-if="activeJob.current_step && activeJob.status === 'in_progress'" class="progress-step-pill">
                      {{ activeJob.current_step }}
                    </span>
                  </div>
                </div>

                <div class="progress-bar-wrap">
                  <div class="progress-bar-track">
                    <div 
                      class="progress-bar-fill"
                      :style="{ width: `${activeJob.progress_percent}%` }"
                      :class="{ completed: activeJob.status === 'completed' }"
                    ></div>
                  </div>
                  <div class="progress-stats-row">
                    <span class="stat-count">{{ activeJob.processed_tracks }} из {{ activeJob.total_tracks }}</span>
                    <span class="stat-percent">{{ activeJob.progress_percent }}%</span>
                  </div>
                </div>

                <!-- Current track mini progress (yt-dlp download) -->
                <div 
                  v-if="activeJob.download_percent !== null && activeJob.download_percent !== undefined && activeJob.status === 'in_progress'" 
                  class="track-mini-progress"
                >
                  <div class="track-mini-bar-track">
                    <div 
                      class="track-mini-bar-fill"
                      :style="{ width: `${activeJob.download_percent}%` }"
                    ></div>
                  </div>
                  <div class="track-mini-meta">
                    <span>Скачивание аудио 320 kbps</span>
                    <span>{{ activeJob.download_percent }}%</span>
                  </div>
                </div>

                <div v-if="activeJob.skipped_tracks > 0" class="progress-skip-notice">
                  <Check :size="13" />
                  <span>Пропущено существующих треков без повторной загрузки: {{ activeJob.skipped_tracks }}</span>
                </div>

                <div v-if="activeJob.error_message" class="progress-error-box">
                  <AlertCircle :size="16" />
                  <span>{{ activeJob.error_message }}</span>
                </div>
              </div>

              <div class="progress-footer-actions">
                <button 
                  v-if="activeJob.status === 'completed' || activeJob.status === 'failed' || activeJob.status === 'cancelled'"
                  class="action-btn primary"
                  @click="handleFinish"
                >
                  <Check :size="16" />
                  <span>Готово</span>
                </button>
                <template v-else>
                  <button 
                    class="action-btn secondary"
                    @click="handleMinimize"
                    title="Свернуть процесс (продолжится в фоне)"
                  >
                    <Minus :size="15" />
                    <span>Свернуть в фон</span>
                  </button>
                  <button 
                    class="action-btn danger-outline"
                    @click="handleCancelJob"
                  >
                    <span>Отменить</span>
                  </button>
                </template>
              </div>
            </div>

            <!-- Upload / Dropzone Step -->
            <div v-else-if="!previewData" class="upload-section">
              <!-- Helper Guide Card -->
              <div class="guide-card">
                <div class="guide-header">
                  <Sparkles :size="16" class="guide-star" />
                  <span class="guide-title">Как получить CSV-файл со Spotify треками:</span>
                </div>
                <div class="guide-steps">
                  <div class="guide-step">
                    <span class="step-num">1</span>
                    <span class="step-text">
                      Перейдите на бесплатный сервис 
                      <a href="https://exportify.app" target="_blank" rel="noopener noreferrer" class="guide-link">
                        exportify.app <ExternalLink :size="12" />
                      </a>
                    </span>
                  </div>
                  <div class="guide-step">
                    <span class="step-num">2</span>
                    <span class="step-text">Нажмите <b>«Export»</b> напротив <b>«Liked Songs»</b> или любого вашего плейлиста.</span>
                  </div>
                  <div class="guide-step">
                    <span class="step-num">3</span>
                    <span class="step-text">Перетащите скачанный файл <code>.csv</code> в поле ниже:</span>
                  </div>
                </div>
              </div>

              <!-- Saved Import Card from Telegram Channel -->
              <div v-if="externalAccountsStore.hasLastSpotifyImport" class="saved-channel-file-card">
                <div class="saved-file-badge">
                  <span class="pulse-dot"></span>
                  <span>Сохранено в Telegram-канале</span>
                </div>
                <div class="saved-file-main">
                  <div class="saved-file-icon">
                    <FileSpreadsheet :size="22" />
                  </div>
                  <div class="saved-file-meta">
                    <span class="saved-file-name" :title="externalAccountsStore.lastSpotifyImport.filename">
                      {{ externalAccountsStore.lastSpotifyImport.filename }}
                    </span>
                    <span class="saved-file-sub">
                      {{ externalAccountsStore.lastSpotifyImport.total_tracks }} треков
                      <template v-if="externalAccountsStore.lastSpotifyImport.summary?.new_tracks_count">
                        • {{ externalAccountsStore.lastSpotifyImport.summary.new_tracks_count }} новых
                      </template>
                    </span>
                  </div>
                  <button 
                    class="action-btn primary saved-file-btn"
                    :disabled="isParsing"
                    @click.stop="loadLastSavedImport"
                  >
                    <div v-if="loadingSavedFile" class="spinner small"></div>
                    <template v-else>
                      <FolderOpen :size="14" />
                      <span>Открыть треклист</span>
                    </template>
                  </button>
                </div>
              </div>

              <!-- Dropzone -->
              <div 
                class="dropzone"
                :class="{ 'is-dragging': isDragging, 'is-loading': isParsing }"
                @dragover.prevent="isDragging = true"
                @dragleave.prevent="isDragging = false"
                @drop.prevent="handleFileDrop"
                @click="triggerFileInput"
              >
                <input 
                  ref="fileInputRef" 
                  type="file" 
                  accept=".csv,text/csv" 
                  class="hidden-file-input" 
                  @change="handleFileInputChange" 
                />

                <div v-if="isParsing" class="dropzone-loading">
                  <div class="spinner large"></div>
                  <span class="dropzone-text">Анализируем CSV и сверяем треки с базой...</span>
                </div>
                <div v-else class="dropzone-content">
                  <div class="dropzone-icon-wrap">
                    <FileSpreadsheet :size="36" class="dropzone-icon" />
                  </div>
                  <h4 class="dropzone-title">Перетащите файл .csv сюда</h4>
                  <p class="dropzone-hint">или нажмите для выбора файла на устройстве</p>
                  <span class="dropzone-btn">
                    <Upload :size="14" />
                    <span>Выбрать CSV файл</span>
                  </span>
                </div>
              </div>

              <!-- Parsing Error Banner -->
              <div v-if="parseError" class="error-banner">
                <AlertCircle :size="16" />
                <span>{{ parseError }}</span>
              </div>
            </div>

            <!-- Preview & Deduplication Review Step -->
            <div v-else class="preview-section">
              <!-- Summary Bar -->
              <div class="summary-card">
                <div class="summary-file-row">
                  <div class="summary-file-name">
                    <FileSpreadsheet :size="16" />
                    <span>{{ previewData.filename }}</span>
                  </div>
                  <button class="reset-file-btn" @click="resetPreview" title="Выбрать другой файл">
                    <RefreshCw :size="12" />
                    <span>Сменить файл</span>
                  </button>
                </div>

                <div class="stats-pills-row">
                  <div class="stat-pill total">
                    <span class="stat-pill-label">Всего в CSV:</span>
                    <span class="stat-pill-val">{{ previewData.total_tracks }}</span>
                  </div>
                  <div class="stat-pill new">
                    <span class="stat-pill-label">Новых:</span>
                    <span class="stat-pill-val">{{ previewData.new_tracks_count }}</span>
                  </div>
                  <div class="stat-pill in-lib" v-if="previewData.in_library_count > 0">
                    <span class="stat-pill-label">В медиатеке:</span>
                    <span class="stat-pill-val">{{ previewData.in_library_count }}</span>
                  </div>
                  <div class="stat-pill in-chan" v-if="previewData.in_channel_count > 0">
                    <span class="stat-pill-label">В канале:</span>
                    <span class="stat-pill-val">{{ previewData.in_channel_count }}</span>
                  </div>
                  <div class="stat-pill in-tg" v-if="previewData.already_in_tg_count > 0">
                    <span class="stat-pill-label">В базе TG:</span>
                    <span class="stat-pill-val">{{ previewData.already_in_tg_count }}</span>
                  </div>
                </div>
              </div>

              <!-- Selection Controls Toolbar -->
              <div class="selection-toolbar">
                <div class="selection-count-text">
                  Выбрано: <strong>{{ selectedUrls.size }}</strong> из {{ previewData.tracks.length }}
                </div>
                <div class="selection-buttons">
                  <button 
                    class="sel-btn highlight"
                    :class="{ active: isOnlyNewSelected }"
                    @click="selectOnlyNew"
                    title="Выбрать только треки, которых ещё нет в вашей медиатеке"
                  >
                    <Sparkles :size="13" />
                    <span>Только новые ({{ previewData.new_tracks_count }})</span>
                  </button>
                  <button class="sel-btn" @click="selectAll">Все</button>
                  <button class="sel-btn" @click="deselectAll">Снять</button>
                </div>
              </div>

              <!-- Options -->
              <div class="options-bar">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="createPlaylist" />
                  <span>Создать отдельный плейлист в AuxBass</span>
                </label>
                <input 
                  v-if="createPlaylist"
                  v-model="playlistName"
                  type="text" 
                  placeholder="Название плейлиста" 
                  class="playlist-name-input"
                />
              </div>

              <!-- Tracklist -->
              <div class="tracklist-box">
                <div 
                  v-for="(track, idx) in previewData.tracks" 
                  :key="track.url || idx"
                  class="track-row"
                  :class="{ 
                    selected: selectedUrls.has(track.url), 
                    'in-library': track.in_library,
                    'now-playing': isTrackPlaying(track) 
                  }"
                  @click="toggleTrack(track.url)"
                >
                  <div class="track-checkbox" :class="{ checked: selectedUrls.has(track.url) }">
                    <Check v-if="selectedUrls.has(track.url)" :size="12" />
                  </div>

                  <span class="track-index">{{ idx + 1 }}</span>

                  <!-- Track thumbnail with quick play overlay -->
                  <div 
                    class="track-thumb"
                    :class="{ 'is-playing': isTrackPlaying(track), 'is-loading': previewLoadingUrl === track.url }"
                    @click.stop="handlePreviewTrack(track, $event)"
                    :title="isTrackPlaying(track) ? 'Пауза' : 'Слушать аудио'"
                  >
                    <img v-if="track.cover_url" :src="track.cover_url" alt="" loading="lazy" />
                    <Music v-else :size="14" />

                    <div class="thumb-play-overlay">
                      <div v-if="previewLoadingUrl === track.url" class="spinner micro"></div>
                      <Pause v-else-if="isTrackPlaying(track)" :size="13" fill="currentColor" />
                      <Play v-else :size="13" fill="currentColor" />
                    </div>
                  </div>

                  <div class="track-meta">
                    <div class="track-title" :title="track.title">
                      <span class="title-text">{{ track.title }}</span>
                      <span v-if="isTrackPlaying(track)" class="playing-indicator" title="Сейчас играет">
                        <Volume2 :size="13" />
                      </span>
                    </div>
                    <div class="track-artist-row">
                      <span class="track-artist" :title="track.artist">{{ track.artist }}</span>
                      <span v-if="track.album" class="track-album" :title="track.album">• {{ track.album }}</span>
                    </div>
                  </div>

                  <!-- Recognition Status Badges -->
                  <div class="track-badges">
                    <span v-if="track.in_library" class="track-badge in-lib" title="Трек уже в вашей медиатеке. Повторно добавлен не будет.">
                      <Check :size="10" /> В медиатеке
                    </span>
                    <span v-if="track.in_channel" class="track-badge in-chan" title="Файл уже отправлен в ваш личный Telegram-канал.">
                      <CloudDownload :size="10" /> В канале
                    </span>
                    <span v-else-if="track.already_in_tg" class="track-badge in-tg" title="Файл уже загружен на сервер Telegram! Добавится мгновенно без скачивания.">
                      <Zap :size="10" /> В базе TG
                    </span>
                  </div>

                  <!-- Preview play action and duration -->
                  <div class="track-actions-right">
                    <button 
                      class="track-row-play-btn"
                      :class="{ 'is-playing': isTrackPlaying(track), 'is-loading': previewLoadingUrl === track.url }"
                      @click.stop="handlePreviewTrack(track, $event)"
                      :title="isTrackPlaying(track) ? 'Пауза' : 'Слушать аудио'"
                    >
                      <div v-if="previewLoadingUrl === track.url" class="spinner micro"></div>
                      <Pause v-else-if="isTrackPlaying(track)" :size="12" fill="currentColor" />
                      <Play v-else :size="12" fill="currentColor" />
                    </button>
                    <span class="track-duration">{{ formatDuration(track.duration) }}</span>
                  </div>
                </div>
              </div>

              <!-- Bottom Action Bar -->
              <div class="preview-actions-bar">
                <button class="action-btn secondary" @click="handleClose">
                  Отмена
                </button>
                <button 
                  class="action-btn primary"
                  :disabled="selectedUrls.size === 0 || isStartingImport"
                  @click="handleStartImport"
                >
                  <div v-if="isStartingImport" class="spinner small"></div>
                  <CloudDownload v-else :size="16" />
                  <span>
                    {{ isStartingImport ? 'Запуск...' : `Импортировать ${selectedUrls.size} треков` }}
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import {
  X,
  Check,
  Upload,
  FileSpreadsheet,
  AlertCircle,
  ExternalLink,
  Sparkles,
  CloudDownload,
  Music,
  Music2,
  Zap,
  RefreshCw,
  Play,
  Pause,
  Volume2,
  Minus,
  FolderOpen,
} from 'lucide-vue-next'
import { ingestionApi } from '@/api/client'
import { useUIStore } from '@/stores/ui'
import { useLibraryStore } from '@/stores/library'
import { usePlayerStore } from '@/stores/player'
import { useTasksStore } from '@/stores/tasks'
import { useExternalAccountsStore } from '@/stores/externalAccounts'
import { formatDuration } from '@/utils'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'imported'])

const uiStore = useUIStore()
const libraryStore = useLibraryStore()
const playerStore = usePlayerStore()
const tasksStore = useTasksStore()
const externalAccountsStore = useExternalAccountsStore()

const playingTrackUrl = ref(null)
const previewLoadingUrl = ref(null)

const fileInputRef = ref(null)
const isDragging = ref(false)
const isParsing = ref(false)
const loadingSavedFile = ref(false)
const parseError = ref(null)

const previewData = ref(null)
const selectedUrls = ref(new Set())
const createPlaylist = ref(false)
const playlistName = ref('')
const isStartingImport = ref(false)

const activeJob = ref(null)
let pollTimer = null

const isOnlyNewSelected = computed(() => {
  if (!previewData.value || previewData.value.tracks.length === 0) return false
  const newTracks = previewData.value.tracks.filter(t => !t.in_library)
  if (newTracks.length === 0) return false
  if (selectedUrls.value.size !== newTracks.length) return false
  return newTracks.every(t => selectedUrls.value.has(t.url))
})

const statusText = computed(() => {
  if (!activeJob.value) return ''
  switch (activeJob.value.status) {
    case 'in_progress':
      return activeJob.value.current_step || 'Синхронизация...'
    case 'completed':
      return 'Импорт успешно завершён!'
    case 'failed':
      return 'Ошибка импорта'
    case 'cancelled':
      return 'Отменено пользователем'
    default:
      return 'Ожидание...'
  }
})


const triggerFileInput = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click()
  }
}

const handleFileInputChange = (e) => {
  const file = e.target.files?.[0]
  if (file) {
    processFile(file)
  }
  e.target.value = ''
}

const handleFileDrop = (e) => {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) {
    processFile(file)
  }
}

const processFile = async (file) => {
  if (!file.name.toLowerCase().endsWith('.csv')) {
    parseError.value = 'Пожалуйста, выберите файл в формате .csv'
    return
  }

  isParsing.value = true
  parseError.value = null

  try {
    const formData = new FormData()
    formData.append('file', file)

    const res = await ingestionApi.previewExportifyCsv(formData)
    previewData.value = res.data

    // Set default playlist name based on file name
    const cleanName = file.name.replace(/\.csv$/i, '').replace(/[_-]/g, ' ')
    playlistName.value = cleanName.charAt(0).toUpperCase() + cleanName.slice(1)

    // Select only new tracks by default!
    selectOnlyNew()
    externalAccountsStore.fetchLastSpotifyImport(true)
  } catch (err) {
    console.error('Failed to parse Exportify CSV:', err)
    parseError.value = err.response?.data?.detail || 'Не удалось проанализировать CSV файл. Убедитесь, что это файл из Exportify.'
  } finally {
    isParsing.value = false
  }
}

const loadLastSavedImport = async (fileId = null) => {
  isParsing.value = true
  loadingSavedFile.value = true
  parseError.value = null

  const targetFileId = fileId || tasksStore.exportifyModalOptions?.fileId || null

  try {
    const res = await ingestionApi.previewLastSpotifyImport(targetFileId ? { file_id: targetFileId } : undefined)
    previewData.value = res.data

    const cleanName = (res.data.filename || 'Spotify Playlist').replace(/\.csv$/i, '').replace(/[_-]/g, ' ')
    playlistName.value = cleanName.charAt(0).toUpperCase() + cleanName.slice(1)

    selectOnlyNew()
  } catch (err) {
    console.error('Failed to load saved Spotify import from Telegram:', err)
    parseError.value = err.response?.data?.detail || 'Не удалось загрузить сохранённый файл из Telegram.'
  } finally {
    isParsing.value = false
    loadingSavedFile.value = false
  }
}

const selectOnlyNew = () => {
  if (!previewData.value) return
  const newUrls = new Set()
  for (const t of previewData.value.tracks) {
    if (!t.in_library) {
      newUrls.add(t.url)
    }
  }
  // If all tracks are already in library, select all so user can choose
  if (newUrls.size === 0) {
    selectAll()
    return
  }
  selectedUrls.value = newUrls
}

const selectAll = () => {
  if (!previewData.value) return
  const allUrls = new Set()
  for (const t of previewData.value.tracks) {
    allUrls.add(t.url)
  }
  selectedUrls.value = allUrls
}

const deselectAll = () => {
  selectedUrls.value = new Set()
}

const toggleTrack = (url) => {
  const next = new Set(selectedUrls.value)
  if (next.has(url)) {
    next.delete(url)
  } else {
    next.add(url)
  }
  selectedUrls.value = next
}

const isTrackPlaying = (track) => {
  if (!playerStore.isPlaying) return false
  if (track.track_id && playerStore.currentTrack?.id === track.track_id) return true
  return playingTrackUrl.value === track.url
}

const handlePreviewTrack = async (track, event) => {
  if (event) {
    event.stopPropagation()
  }

  // If already playing this track, toggle play/pause
  if (isTrackPlaying(track)) {
    playerStore.togglePlay()
    return
  }

  // If already in player as current track, just resume
  if (
    (track.track_id && playerStore.currentTrack?.id === track.track_id) ||
    playingTrackUrl.value === track.url
  ) {
    playerStore.togglePlay()
    return
  }

  if (previewLoadingUrl.value) return
  previewLoadingUrl.value = track.url

  try {
    const res = await ingestionApi.quickImport({
      url: track.url,
      title: track.title,
      artist: track.artist,
      duration: track.duration,
      cover_url: track.cover_url,
      add_to_library: false,
    })

    const resolved = res.data?.track
    if (resolved) {
      track.track_id = resolved.id
      track.already_in_tg = true
      playingTrackUrl.value = track.url
      playerStore.playTrack(resolved, [resolved], 0)
    }
  } catch (err) {
    console.error('Failed to preview track:', err)
    const msg = err.response?.data?.detail || 'Не удалось воспроизвести трек'
    uiStore.toast?.error('Ошибка воспроизведения', msg)
  } finally {
    previewLoadingUrl.value = null
  }
}

const resetPreview = () => {
  previewData.value = null
  selectedUrls.value = new Set()
  parseError.value = null
}

const handleStartImport = async () => {
  if (!previewData.value || selectedUrls.value.size === 0 || isStartingImport.value) return

  isStartingImport.value = true
  try {
    const chosenTracks = previewData.value.tracks.filter(t => selectedUrls.value.has(t.url))
    const payload = {
      title: playlistName.value || 'Импорт Spotify',
      tracks: chosenTracks,
      create_playlist: createPlaylist.value,
      playlist_name: createPlaylist.value ? playlistName.value : null,
    }

    const res = await ingestionApi.startExportifyImport(payload)
    activeJob.value = res.data
    tasksStore.registerJob(res.data, {
      type: 'exportify',
      title: playlistName.value || 'Импорт Spotify',
    })
    uiStore.toast?.success('Импорт запущен', `Загрузка ${chosenTracks.length} треков в медиатеку и Telegram-канал`)

    startPollingJob(res.data.id)
  } catch (err) {
    console.error('Failed to start Exportify import:', err)
    uiStore.toast?.error('Ошибка', err.response?.data?.detail || 'Не удалось запустить импорт')
  } finally {
    isStartingImport.value = false
  }
}

const startPollingJob = (jobId) => {
  stopPollingJob()
  pollTimer = setInterval(async () => {
    try {
      const res = await ingestionApi.getJob(jobId)
      activeJob.value = res.data
      if (['completed', 'failed', 'cancelled'].includes(res.data.status)) {
        stopPollingJob()
        libraryStore.fetchTracks({ refresh: true })
        if (res.data.status === 'completed') {
          uiStore.toast?.success('Импорт завершен', `Успешно обработано треков: ${res.data.processed_tracks}`)
          emit('imported')
        }
      }
    } catch (e) {
      console.error('Polling error:', e)
      stopPollingJob()
    }
  }, 1500)
}

const stopPollingJob = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const handleMinimize = () => {
  if (activeJob.value) {
    tasksStore.minimizeJob(activeJob.value.id)
  }
  emit('close')
}

const handleCancelJob = async () => {
  if (!activeJob.value) return
  try {
    await tasksStore.cancelJob(activeJob.value.id)
    activeJob.value.status = 'cancelled'
  } catch (e) {
    console.error('Cancel job error:', e)
  } finally {
    stopPollingJob()
  }
}

const handleFinish = () => {
  handleClose()
}

const handleClose = () => {
  if (activeJob.value && activeJob.value.status === 'in_progress') {
    handleMinimize()
    return
  }
  stopPollingJob()
  activeJob.value = null
  resetPreview()
  emit('close')
}

watch(
  () => tasksStore.currentExportifyJob,
  (job) => {
    if (job) {
      activeJob.value = job
    }
  },
  { immediate: true }
)

watch(
  () => props.show,
  (val) => {
    if (val) {
      if (tasksStore.currentExportifyJob) {
        activeJob.value = tasksStore.currentExportifyJob
        if (activeJob.value.status === 'in_progress') {
          startPollingJob(activeJob.value.id)
        }
      } else if (tasksStore.exportifyModalOptions?.loadLastSaved) {
        loadLastSavedImport(tasksStore.exportifyModalOptions?.fileId)
      } else {
        externalAccountsStore.fetchLastSpotifyImport()
      }
    } else {
      if (!activeJob.value || activeJob.value.status !== 'in_progress') {
        stopPollingJob()
        activeJob.value = null
        resetPreview()
      }
    }
  }
)
</script>

<style scoped>
.exportify-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.78);
  backdrop-filter: blur(10px);
  padding: 16px;
}

.exportify-dialog {
  width: 100%;
  max-width: 680px;
  max-height: 88vh;
  display: flex;
  flex-direction: column;
  background: #141619;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.6), 0 0 40px rgba(29, 185, 84, 0.08);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sp-icon-badge {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: linear-gradient(135deg, #1db954 0%, #15883e 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 14px rgba(29, 185, 84, 0.35);
}

.modal-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #f1f3f5;
}

.modal-subtitle {
  margin: 2px 0 0 0;
  font-size: 12px;
  color: #8b929a;
}

.header-right-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.minimize-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #94a3b8;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.minimize-btn:hover {
  background: rgba(255, 255, 255, 0.14);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.2);
}

.close-btn {
  background: rgba(255, 255, 255, 0.06);
  border: none;
  color: #8b929a;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

/* Saved Channel File Card */
.saved-channel-file-card {
  background: rgba(29, 185, 84, 0.08);
  border: 1px solid rgba(29, 185, 84, 0.28);
  border-radius: 14px;
  padding: 14px 16px;
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: all 0.2s ease;
}

.saved-channel-file-card:hover {
  background: rgba(29, 185, 84, 0.12);
  border-color: rgba(29, 185, 84, 0.45);
}

.saved-file-badge {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--c-accent, #1db954);
}

.pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--c-accent, #1db954);
  box-shadow: 0 0 8px rgba(29, 185, 84, 0.8);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.8; }
}

.saved-file-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.saved-file-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(29, 185, 84, 0.16);
  color: var(--c-accent, #1db954);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.saved-file-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.saved-file-name {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.saved-file-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.saved-file-btn {
  padding: 8px 14px;
  font-size: 13px;
  gap: 6px;
  flex-shrink: 0;
}

/* Guide Card */
.guide-card {
  background: rgba(29, 185, 84, 0.06);
  border: 1px solid rgba(29, 185, 84, 0.2);
  border-radius: 14px;
  padding: 14px 16px;
  margin-bottom: 18px;
}

.guide-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.guide-star {
  color: #1db954;
}

.guide-title {
  font-size: 13px;
  font-weight: 600;
  color: #e0f2e5;
}

.guide-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.guide-step {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #cfd8dc;
}

.step-num {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(29, 185, 84, 0.2);
  color: #1db954;
  font-weight: 700;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.guide-link {
  color: #1db954;
  text-decoration: underline;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-weight: 600;
}

.guide-link:hover {
  color: #24d864;
}

/* Dropzone */
.dropzone {
  border: 2px dashed rgba(255, 255, 255, 0.14);
  border-radius: 16px;
  padding: 40px 24px;
  text-align: center;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.015);
  transition: all 0.25s ease;
}

.dropzone:hover, .dropzone.is-dragging {
  border-color: #1db954;
  background: rgba(29, 185, 84, 0.05);
  box-shadow: 0 0 24px rgba(29, 185, 84, 0.15);
}

.hidden-file-input {
  display: none;
}

.dropzone-icon-wrap {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.04);
  color: #1db954;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px auto;
}

.dropzone-title {
  margin: 0 0 6px 0;
  font-size: 16px;
  font-weight: 600;
  color: #f1f3f5;
}

.dropzone-hint {
  margin: 0 0 16px 0;
  font-size: 13px;
  color: #78828c;
}

.dropzone-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #fff;
  padding: 8px 18px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
}

.dropzone-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  color: #adb5bd;
}

.error-banner {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 10px;
  color: #fca5a5;
  font-size: 13px;
}

/* Summary Card */
.summary-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  padding: 14px 16px;
  margin-bottom: 14px;
}

.summary-file-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.summary-file-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #f1f3f5;
}

.reset-file-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #8b929a;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-file-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
}

.stats-pills-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stat-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
}

.stat-pill.total {
  background: rgba(255, 255, 255, 0.06);
  color: #e2e8f0;
}
.stat-pill.new {
  background: rgba(29, 185, 84, 0.15);
  color: #1ed760;
  border: 1px solid rgba(29, 185, 84, 0.3);
}
.stat-pill.in-lib {
  background: rgba(59, 130, 246, 0.12);
  color: #93c5fd;
}
.stat-pill.in-chan {
  background: rgba(168, 85, 247, 0.12);
  color: #d8b4fe;
}
.stat-pill.in-tg {
  background: rgba(245, 158, 11, 0.12);
  color: #fcd34d;
}

.stat-pill-val {
  font-weight: 700;
}

/* Selection Toolbar */
.selection-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 0 4px;
}

.selection-count-text {
  font-size: 13px;
  color: #94a3b8;
}

.selection-buttons {
  display: flex;
  gap: 8px;
}

.sel-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
  padding: 5px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.sel-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.sel-btn.highlight {
  background: rgba(29, 185, 84, 0.18);
  border-color: rgba(29, 185, 84, 0.4);
  color: #1ed760;
}

.sel-btn.highlight.active {
  background: #1db954;
  color: #000;
  font-weight: 600;
}

/* Options Bar */
.options-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 14px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #cbd5e1;
  cursor: pointer;
  user-select: none;
}

.playlist-name-input {
  flex: 1;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 13px;
  outline: none;
}

.playlist-name-input:focus {
  border-color: #1db954;
}

/* Tracklist */
.tracklist-box {
  max-height: 380px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  background: rgba(0, 0, 0, 0.2);
  padding: 4px;
}

.track-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
  user-select: none;
}

.track-row:hover {
  background: rgba(255, 255, 255, 0.05);
}

.track-row.selected {
  background: rgba(29, 185, 84, 0.08);
}

.track-checkbox {
  width: 18px;
  height: 18px;
  border-radius: 5px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #000;
  flex-shrink: 0;
  transition: all 0.15s;
}

.track-checkbox.checked {
  background: #1db954;
  border-color: #1db954;
}

.track-index {
  font-size: 11px;
  color: #64748b;
  width: 22px;
  text-align: right;
  flex-shrink: 0;
}

.track-thumb {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  cursor: pointer;
}

.thumb-play-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.track-thumb:hover .thumb-play-overlay,
.track-thumb.is-playing .thumb-play-overlay,
.track-thumb.is-loading .thumb-play-overlay {
  opacity: 1;
}

.track-thumb.is-playing .thumb-play-overlay {
  color: #1ed760;
}

.track-row.now-playing {
  border-left: 2px solid #1db954;
  background: rgba(29, 185, 84, 0.12) !important;
}

.playing-indicator {
  display: inline-flex;
  align-items: center;
  margin-left: 6px;
  color: #1ed760;
  vertical-align: middle;
}

.track-actions-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.track-row-play-btn {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.05);
  color: #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  padding: 0;
}

.track-row-play-btn:hover {
  background: rgba(29, 185, 84, 0.2);
  border-color: rgba(29, 185, 84, 0.4);
  color: #1ed760;
  transform: scale(1.08);
}

.track-row-play-btn.is-playing {
  background: #1db954;
  border-color: #1db954;
  color: #000000;
}

.track-row-play-btn.is-loading {
  background: rgba(255, 255, 255, 0.05);
  cursor: wait;
}

.spinner.micro {
  width: 12px;
  height: 12px;
  border-width: 1.5px;
}

.track-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.track-meta {
  flex: 1;
  min-width: 0;
}

.track-title {
  font-size: 13px;
  font-weight: 500;
  color: #f1f3f5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-artist-row {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #8b929a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-album {
  color: #64748b;
}

.track-badges {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.track-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 7px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 600;
}

.track-badge.in-lib {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
}
.track-badge.in-chan {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
}
.track-badge.in-tg {
  background: rgba(168, 85, 247, 0.15);
  color: #c084fc;
}

.track-duration {
  font-size: 11px;
  color: #64748b;
  width: 40px;
  text-align: right;
  flex-shrink: 0;
}

/* Bottom Action Bar */
.preview-actions-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.action-btn.primary {
  background: #1db954;
  color: #000;
  box-shadow: 0 4px 14px rgba(29, 185, 84, 0.35);
}

.action-btn.primary:hover:not(:disabled) {
  background: #24d864;
  transform: translateY(-1px);
}

.action-btn.primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}

.action-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.14);
}

/* Progress Section */
.progress-section {
  padding: 16px 0;
}

.progress-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
}

.progress-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 12px;
}

.progress-status-badge.in_progress {
  background: rgba(29, 185, 84, 0.15);
  color: #1ed760;
}
.progress-status-badge.completed {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
}
.progress-status-badge.failed, .progress-status-badge.cancelled {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.progress-job-title {
  margin: 0 0 6px 0;
  font-size: 18px;
  font-weight: 700;
  color: #fff;
}

.progress-current-track-wrap {
  margin: 0 0 16px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.progress-current-track {
  margin: 0;
  font-size: 13px;
  color: #f1f3f5;
  font-weight: 500;
}

.progress-step-pill {
  font-size: 11px;
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.25);
  padding: 2px 10px;
  border-radius: 12px;
  font-weight: 600;
  letter-spacing: 0.2px;
}

.track-mini-progress {
  margin: 6px 0 14px 0;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
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
  background: #38bdf8;
  border-radius: 2px;
  transition: width 0.2s ease;
}

.track-mini-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #7dd3fc;
  font-weight: 500;
}

.progress-bar-wrap {
  margin: 16px 0 10px 0;
}

.progress-bar-track {
  width: 100%;
  height: 10px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #1db954 0%, #34d399 100%);
  border-radius: 5px;
  transition: width 0.3s ease;
}

.progress-bar-fill.completed {
  background: #22c55e;
}

.progress-stats-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #94a3b8;
}

.progress-skip-notice {
  margin-top: 14px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.1);
  padding: 4px 10px;
  border-radius: 8px;
}

.progress-error-box {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #f87171;
  font-size: 13px;
  background: rgba(239, 68, 68, 0.12);
  padding: 10px;
  border-radius: 8px;
  text-align: left;
}

.progress-footer-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
}

.action-btn.danger-outline {
  background: transparent;
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.danger-outline:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.5);
  color: #fff;
}



.modal-fade-enter-active, .modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from, .modal-fade-leave-to {
  opacity: 0;
}
</style>
