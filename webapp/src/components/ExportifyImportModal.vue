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

              <!-- Saved Imports List from Telegram Channel -->
              <div v-if="externalAccountsStore.recentSpotifyImports.length > 0" class="saved-channel-files-section">
                <div class="saved-section-header">
                  <div class="saved-file-badge">
                    <span class="pulse-dot"></span>
                    <span>Сохранённые импорты в Telegram ({{ externalAccountsStore.recentSpotifyImports.length }})</span>
                  </div>
                </div>
                <div class="saved-files-grid">
                  <div 
                    v-for="file in externalAccountsStore.recentSpotifyImports" 
                    :key="file.file_id || file.id"
                    class="saved-file-item"
                    :class="{ 'is-loading': loadingFileId === file.file_id }"
                  >
                    <div class="saved-file-icon">
                      <FileSpreadsheet :size="20" />
                    </div>
                    <div class="saved-file-meta" @click="loadLastSavedImport(file.file_id)">
                      <span class="saved-file-name" :title="file.filename">
                        {{ formatImportFilename(file.filename) }}
                      </span>
                      <span class="saved-file-sub">
                        {{ file.total_tracks }} треков
                        <template v-if="file.summary?.new_tracks_count">
                          • {{ file.summary.new_tracks_count }} новых
                        </template>
                        <template v-if="file.created_at">
                          • {{ new Date(file.created_at).toLocaleDateString() }}
                        </template>
                      </span>
                    </div>
                    <div class="saved-file-actions">
                      <button 
                        class="action-btn primary small saved-file-btn"
                        :disabled="isParsing"
                        @click.stop="loadLastSavedImport(file.file_id)"
                        title="Открыть треклист"
                      >
                        <div v-if="loadingFileId === file.file_id" class="spinner micro"></div>
                        <template v-else>
                          <FolderOpen :size="13" />
                          <span>Открыть</span>
                        </template>
                      </button>
                      <button 
                        class="action-btn danger-icon small"
                        @click.stop="confirmDeleteFile(file)"
                        title="Удалить файл из истории"
                      >
                        <Trash2 :size="14" />
                      </button>
                    </div>
                  </div>
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
                  <h4 class="dropzone-title">Перетащите новый файл .csv сюда</h4>
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
                    <span class="summary-filename-text" :title="previewData.filename">
                      {{ formatImportFilename(previewData.filename) }}
                    </span>
                    <span class="file-ext-tag">CSV</span>
                  </div>
                  <div class="summary-file-actions">
                    <!-- File switcher dropdown -->
                    <div v-if="externalAccountsStore.recentSpotifyImports.length > 1" class="file-switcher-dropdown-wrap">
                      <button 
                        class="file-switcher-btn" 
                        @click="showFileSwitcher = !showFileSwitcher"
                        title="Выбрать другой сохранённый файл"
                      >
                        <ListFilter :size="13" />
                        <span>Выбрать плейлист</span>
                        <ChevronDown :size="13" class="switcher-chevron" :class="{ 'rotate-180': showFileSwitcher }" />
                      </button>
                      <div v-if="showFileSwitcher" class="file-switcher-dropdown">
                        <div class="file-switcher-header">Сохранённые импорты:</div>
                        <div 
                          v-for="f in externalAccountsStore.recentSpotifyImports" 
                          :key="f.file_id || f.id"
                          class="file-switcher-item"
                          :class="{ active: currentActiveFileId === f.file_id }"
                          @click="switchToFile(f)"
                        >
                          <FileSpreadsheet :size="14" />
                          <span class="switcher-item-name">{{ formatImportFilename(f.filename) }}</span>
                          <span class="switcher-item-count">{{ f.total_tracks }} треков</span>
                        </div>
                      </div>
                    </div>

                    <button class="reset-file-btn" @click="resetPreview" title="Загрузить другой файл">
                      <Upload :size="12" />
                      <span>Новый файл</span>
                    </button>

                    <button 
                      v-if="currentActiveFileId" 
                      class="delete-active-file-btn" 
                      @click="confirmDeleteCurrentFile" 
                      title="Удалить этот файл импорта из истории"
                    >
                      <Trash2 :size="13" />
                      <span>Удалить файл</span>
                    </button>
                  </div>
                </div>

                <div class="stats-pills-row">
                  <div class="stat-pill total">
                    <span class="stat-pill-label">Всего:</span>
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

              <!-- Search & Filter Controls -->
              <div class="search-filter-section">
                <div class="search-input-wrap">
                  <Search :size="15" class="search-icon" />
                  <input 
                    v-model="searchQuery" 
                    type="text" 
                    placeholder="Поиск по названию трека, исполнителю или альбому..." 
                    class="search-input"
                  />
                  <button v-if="searchQuery" class="clear-search-btn" @click="searchQuery = ''" title="Очистить поиск">
                    <X :size="13" />
                  </button>
                </div>

                <div class="filter-chips-row">
                  <button 
                    class="filter-chip" 
                    :class="{ active: activeFilter === 'all' }"
                    @click="activeFilter = 'all'"
                  >
                    Все ({{ previewData.total_tracks }})
                  </button>
                  <button 
                    class="filter-chip new" 
                    :class="{ active: activeFilter === 'new' }"
                    @click="activeFilter = 'new'"
                  >
                    <Sparkles :size="11" />
                    <span>Новые ({{ previewData.new_tracks_count }})</span>
                  </button>
                  <button 
                    v-if="previewData.in_library_count > 0"
                    class="filter-chip in-lib" 
                    :class="{ active: activeFilter === 'in_library' }"
                    @click="activeFilter = 'in_library'"
                  >
                    <Check :size="11" />
                    <span>В медиатеке ({{ previewData.in_library_count }})</span>
                  </button>
                  <button 
                    v-if="previewData.already_in_tg_count > 0 || previewData.in_channel_count > 0"
                    class="filter-chip in-tg" 
                    :class="{ active: activeFilter === 'in_tg' }"
                    @click="activeFilter = 'in_tg'"
                  >
                    <Zap :size="11" />
                    <span>В Telegram ({{ previewData.already_in_tg_count + previewData.in_channel_count }})</span>
                  </button>
                  <button 
                    class="filter-chip selected" 
                    :class="{ active: activeFilter === 'selected' }"
                    @click="activeFilter = 'selected'"
                  >
                    <span>Выбранные ({{ selectedUrls.size }})</span>
                  </button>
                </div>
              </div>

              <!-- Selection Controls Toolbar -->
              <div class="selection-toolbar">
                <div class="selection-count-text">
                  Выбрано: <strong>{{ selectedUrls.size }}</strong> из {{ previewData.tracks.length }}
                  <span v-if="searchQuery.trim() || activeFilter !== 'all'" class="filtered-hint">
                    (в фильтре: {{ filteredTracks.length }})
                  </span>
                </div>
                <div class="selection-buttons">
                  <button 
                    v-if="searchQuery.trim() || activeFilter !== 'all'"
                    class="sel-btn highlight"
                    @click="selectFiltered"
                    title="Выбрать все треки в текущем фильтре"
                  >
                    <CheckCheck :size="13" />
                    <span>Выбрать показанные</span>
                  </button>
                  <button 
                    v-if="searchQuery.trim() || activeFilter !== 'all'"
                    class="sel-btn"
                    @click="deselectFiltered"
                    title="Снять выбор с показанных треков"
                  >
                    <span>Снять показанные</span>
                  </button>
                  <button 
                    class="sel-btn highlight"
                    :class="{ active: isOnlyNewSelected }"
                    @click="selectOnlyNew"
                    title="Выбрать только треки, которых ещё нет в вашей медиатеке"
                  >
                    <Sparkles :size="13" />
                    <span>Только новые</span>
                  </button>
                  <button class="sel-btn" @click="selectAll">Все</button>
                  <button class="sel-btn" @click="deselectAll">Снять</button>
                </div>
              </div>

              <!-- Destination Options (Playlist Selection) -->
              <div class="destination-section">
                <div class="destination-label">Куда сохранить треки:</div>
                <div class="destination-modes">
                  <label class="destination-chip" :class="{ active: destinationMode === 'none' }">
                    <input type="radio" value="none" v-model="destinationMode" />
                    <Library :size="13" />
                    <span>Только в медиатеку</span>
                  </label>
                  <label class="destination-chip" :class="{ active: destinationMode === 'new' }">
                    <input type="radio" value="new" v-model="destinationMode" />
                    <Plus :size="13" />
                    <span>Создать новый плейлист</span>
                  </label>
                  <label 
                    class="destination-chip" 
                    :class="{ active: destinationMode === 'existing', disabled: !userPlaylists.length }"
                  >
                    <input type="radio" value="existing" v-model="destinationMode" :disabled="!userPlaylists.length" />
                    <FolderPlus :size="13" />
                    <span>В существующий плейлист</span>
                  </label>
                </div>

                <!-- If creating new playlist -->
                <div v-if="destinationMode === 'new'" class="destination-input-wrap">
                  <input 
                    v-model="playlistName"
                    type="text" 
                    placeholder="Название нового плейлиста" 
                    class="playlist-name-input"
                  />
                </div>

                <!-- If selecting existing playlist -->
                <div v-if="destinationMode === 'existing'" class="destination-select-wrap">
                  <div class="custom-select-wrapper">
                    <select v-model="selectedExistingPlaylistId" class="playlist-dropdown">
                      <option :value="null" disabled>-- Выберите плейлист из вашей медиатеки --</option>
                      <option 
                        v-for="pl in userPlaylists" 
                        :key="pl.id" 
                        :value="pl.id"
                      >
                        {{ pl.name }} ({{ pl.track_count || 0 }} треков)
                      </option>
                    </select>
                  </div>
                  <span v-if="selectedPlaylistSummary" class="destination-summary-hint">
                    Треки будут добавлены в конец плейлиста «{{ selectedPlaylistSummary.name }}»
                  </span>
                </div>
              </div>

              <!-- Tracklist (Progressive Rendering with Scroll to prevent lag) -->
              <div class="tracklist-box" @scroll="handleTracklistScroll">
                <div v-if="filteredTracks.length === 0" class="no-tracks-found">
                  <Search :size="28" />
                  <span>Ничего не найдено по вашему запросу</span>
                  <button class="reset-filter-btn" @click="resetFilters">Сбросить поиск и фильтры</button>
                </div>

                <div 
                  v-for="(track, idx) in visibleTracks" 
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

                <div v-if="visibleTracks.length < filteredTracks.length" class="scroll-more-indicator">
                  <span>Показано {{ visibleTracks.length }} из {{ filteredTracks.length }} (прокрутите для отображения остальных)</span>
                </div>
              </div>

              <!-- Bottom Action Bar -->
              <div class="preview-actions-bar">
                <button class="action-btn secondary" @click="handleClose">
                  Отмена
                </button>
                <button 
                  class="action-btn primary"
                  :disabled="selectedUrls.size === 0 || isStartingImport || (destinationMode === 'existing' && !selectedExistingPlaylistId)"
                  @click="handleStartImport"
                >
                  <div v-if="isStartingImport" class="spinner small"></div>
                  <CloudDownload v-else :size="16" />
                  <span>
                    {{ isStartingImport ? 'Запуск...' : actionButtonLabel }}
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
  CheckCheck,
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
  Trash2,
  Search,
  ChevronDown,
  ListFilter,
  Library,
  Plus,
  FolderPlus,
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
const loadingFileId = ref(null)
const parseError = ref(null)

const previewData = ref(null)
const currentActiveFileId = ref(null)
const showFileSwitcher = ref(false)
const selectedUrls = ref(new Set())

// Search & filter
const searchQuery = ref('')
const activeFilter = ref('all') // 'all' | 'new' | 'in_library' | 'in_tg' | 'selected'
const displayLimit = ref(60)

// Destination
const destinationMode = ref('new') // 'none' | 'new' | 'existing'
const playlistName = ref('')
const selectedExistingPlaylistId = ref(null)

const isStartingImport = ref(false)
const activeJob = ref(null)
let pollTimer = null

const userPlaylists = computed(() => libraryStore.playlists || [])

const selectedPlaylistSummary = computed(() => {
  if (!selectedExistingPlaylistId.value) return null
  return userPlaylists.value.find(p => p.id === selectedExistingPlaylistId.value) || null
})

const formatImportFilename = (name) => {
  if (!name) return 'Spotify CSV'
  return name.replace(/\.csv$/i, '').replace(/[_-]/g, ' ')
}

const filteredTracks = computed(() => {
  if (!previewData.value?.tracks) return []
  let list = previewData.value.tracks

  if (activeFilter.value === 'new') {
    list = list.filter(t => !t.in_library)
  } else if (activeFilter.value === 'in_library') {
    list = list.filter(t => t.in_library)
  } else if (activeFilter.value === 'in_tg') {
    list = list.filter(t => t.already_in_tg || t.in_channel)
  } else if (activeFilter.value === 'selected') {
    list = list.filter(t => selectedUrls.value.has(t.url))
  }

  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter(t => 
      (t.title && t.title.toLowerCase().includes(q)) ||
      (t.artist && t.artist.toLowerCase().includes(q)) ||
      (t.album && t.album.toLowerCase().includes(q))
    )
  }
  return list
})

const visibleTracks = computed(() => {
  return filteredTracks.value.slice(0, displayLimit.value)
})

const isOnlyNewSelected = computed(() => {
  if (!previewData.value || previewData.value.tracks.length === 0) return false
  const newTracks = previewData.value.tracks.filter(t => !t.in_library)
  if (newTracks.length === 0) return false
  if (selectedUrls.value.size !== newTracks.length) return false
  return newTracks.every(t => selectedUrls.value.has(t.url))
})

const actionButtonLabel = computed(() => {
  const count = selectedUrls.value.size
  if (destinationMode.value === 'existing') {
    const plName = selectedPlaylistSummary.value?.name
    return plName ? `Добавить в «${plName}» (${count})` : `Добавить в плейлист (${count})`
  }
  if (destinationMode.value === 'new') {
    return `Создать плейлист и импортировать (${count})`
  }
  return `Импортировать ${count} треков`
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
  resetFilters()

  try {
    const formData = new FormData()
    formData.append('file', file)

    const res = await ingestionApi.previewExportifyCsv(formData)
    previewData.value = res.data
    currentActiveFileId.value = res.data.file_id || null

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
  // Clear any existing previewData immediately so we don't display the previous file's tracks
  previewData.value = null
  selectedUrls.value = new Set()
  resetFilters()

  isParsing.value = true
  loadingSavedFile.value = true
  const targetFileId = fileId || tasksStore.exportifyModalOptions?.fileId || null
  loadingFileId.value = targetFileId
  parseError.value = null

  try {
    const res = await ingestionApi.previewLastSpotifyImport(targetFileId ? { file_id: targetFileId } : undefined)
    previewData.value = res.data
    currentActiveFileId.value = res.data.file_id || targetFileId

    const cleanName = (res.data.filename || 'Spotify Playlist').replace(/\.csv$/i, '').replace(/[_-]/g, ' ')
    playlistName.value = cleanName.charAt(0).toUpperCase() + cleanName.slice(1)

    selectOnlyNew()
  } catch (err) {
    console.error('Failed to load saved Spotify import from Telegram:', err)
    parseError.value = err.response?.data?.detail || 'Не удалось загрузить сохранённый файл из Telegram.'
  } finally {
    isParsing.value = false
    loadingSavedFile.value = false
    loadingFileId.value = null
  }
}

const switchToFile = (file) => {
  showFileSwitcher.value = false
  loadLastSavedImport(file.file_id)
}

const confirmDeleteFile = async (file) => {
  const name = formatImportFilename(file.filename)
  if (confirm(`Удалить сохранённый файл импорта «${name}» из истории?`)) {
    try {
      await externalAccountsStore.deleteSpotifyImport(file.file_id || file.id)
      uiStore.toast?.success('Удалено', `Файл импорта «${name}» удалён`)
      if (currentActiveFileId.value === file.file_id) {
        resetPreview()
      }
    } catch (err) {
      console.error('Failed to delete import file:', err)
      uiStore.toast?.error('Ошибка', 'Не удалось удалить файл')
    }
  }
}

const confirmDeleteCurrentFile = async () => {
  if (!currentActiveFileId.value) return
  const name = formatImportFilename(previewData.value?.filename || 'файл')
  if (confirm(`Удалить файл импорта «${name}» из истории?`)) {
    try {
      await externalAccountsStore.deleteSpotifyImport(currentActiveFileId.value)
      uiStore.toast?.success('Удалено', `Файл импорта «${name}» удалён`)
      resetPreview()
    } catch (err) {
      console.error('Failed to delete import file:', err)
      uiStore.toast?.error('Ошибка', 'Не удалось удалить файл')
    }
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

const selectFiltered = () => {
  const next = new Set(selectedUrls.value)
  for (const t of filteredTracks.value) {
    next.add(t.url)
  }
  selectedUrls.value = next
}

const deselectFiltered = () => {
  const next = new Set(selectedUrls.value)
  for (const t of filteredTracks.value) {
    next.delete(t.url)
  }
  selectedUrls.value = next
}

const resetFilters = () => {
  searchQuery.value = ''
  activeFilter.value = 'all'
  displayLimit.value = 60
}

const handleTracklistScroll = (e) => {
  const el = e.target
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 300) {
    if (displayLimit.value < filteredTracks.value.length) {
      displayLimit.value = Math.min(displayLimit.value + 60, filteredTracks.value.length)
    }
  }
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

  if (isTrackPlaying(track)) {
    playerStore.togglePlay()
    return
  }

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
  currentActiveFileId.value = null
  selectedUrls.value = new Set()
  parseError.value = null
  showFileSwitcher.value = false
  resetFilters()
}

const handleStartImport = async () => {
  if (!previewData.value || selectedUrls.value.size === 0 || isStartingImport.value) return
  if (destinationMode.value === 'existing' && !selectedExistingPlaylistId.value) {
    uiStore.toast?.warning('Выберите плейлист', 'Пожалуйста, выберите существующий плейлист из списка')
    return
  }

  isStartingImport.value = true
  try {
    const chosenTracks = previewData.value.tracks.filter(t => selectedUrls.value.has(t.url))
    const payload = {
      title: destinationMode.value === 'existing'
        ? (selectedPlaylistSummary.value?.name || 'Spotify Import')
        : (playlistName.value || 'Импорт Spotify'),
      tracks: chosenTracks,
      create_playlist: destinationMode.value === 'new',
      playlist_name: destinationMode.value === 'new' ? (playlistName.value || 'Spotify Playlist') : null,
      target_playlist_id: destinationMode.value === 'existing' ? selectedExistingPlaylistId.value : null,
    }

    const res = await ingestionApi.startExportifyImport(payload)
    activeJob.value = res.data
    tasksStore.registerJob(res.data, {
      type: 'exportify',
      title: payload.title,
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
        libraryStore.fetchPlaylists(true)
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
  () => tasksStore.exportifyModalOptions,
  (opts) => {
    if (props.show && opts?.loadLastSaved) {
      loadLastSavedImport(opts.fileId)
    }
  },
  { deep: true }
)

watch(
  [searchQuery, activeFilter],
  () => {
    displayLimit.value = 60
  }
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
      if (!libraryStore.playlists || libraryStore.playlists.length === 0) {
        libraryStore.fetchPlaylists()
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

/* Saved Channel Files Section */
.saved-channel-files-section {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 14px 16px;
  margin-bottom: 16px;
}

.saved-section-header {
  margin-bottom: 10px;
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

.saved-files-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
  padding-right: 4px;
}

.saved-file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  transition: all 0.2s ease;
}

.saved-file-item:hover {
  background: rgba(29, 185, 84, 0.08);
  border-color: rgba(29, 185, 84, 0.3);
}

.saved-file-icon {
  width: 36px;
  height: 36px;
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
  cursor: pointer;
}

.saved-file-name {
  font-size: 13px;
  font-weight: 600;
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.saved-file-sub {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
}

.saved-file-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.saved-file-btn {
  padding: 6px 12px;
  font-size: 12px;
  gap: 5px;
  border-radius: 8px;
}

.action-btn.danger-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #ef4444;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn.danger-icon:hover {
  background: rgba(239, 68, 68, 0.25);
  border-color: #ef4444;
  color: #fff;
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
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.summary-file-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #f1f3f5;
  min-width: 0;
  flex: 1;
}

.summary-filename-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-ext-tag {
  font-size: 10px;
  font-weight: 700;
  background: rgba(29, 185, 84, 0.15);
  color: #1ed760;
  padding: 1px 5px;
  border-radius: 4px;
  border: 1px solid rgba(29, 185, 84, 0.3);
}

.summary-file-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* File switcher */
.file-switcher-dropdown-wrap {
  position: relative;
}

.file-switcher-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(29, 185, 84, 0.12);
  border: 1px solid rgba(29, 185, 84, 0.3);
  color: #1ed760;
  padding: 5px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.file-switcher-btn:hover {
  background: rgba(29, 185, 84, 0.2);
  border-color: #1ed760;
}

.switcher-chevron {
  transition: transform 0.2s ease;
}

.switcher-chevron.rotate-180 {
  transform: rotate(180deg);
}

.file-switcher-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 100;
  background: #181b20;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  padding: 6px;
  width: 240px;
  max-height: 240px;
  overflow-y: auto;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.6);
}

.file-switcher-header {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  padding: 6px 8px 4px 8px;
}

.file-switcher-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 12px;
  color: #cbd5e1;
  cursor: pointer;
  transition: all 0.15s;
}

.file-switcher-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.file-switcher-item.active {
  background: rgba(29, 185, 84, 0.15);
  color: #1ed760;
  font-weight: 600;
}

.switcher-item-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.switcher-item-count {
  font-size: 11px;
  color: #64748b;
}

.reset-file-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #8b929a;
  padding: 5px 10px;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-file-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
}

.delete-active-file-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.25);
  color: #f87171;
  padding: 5px 10px;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.delete-active-file-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: #ef4444;
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

/* Search & Filter Bar */
.search-filter-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
}

.search-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input-wrap .search-icon {
  position: absolute;
  left: 12px;
  color: #64748b;
  pointer-events: none;
}

.search-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #fff;
  border-radius: 10px;
  padding: 9px 36px 9px 36px;
  font-size: 13px;
  outline: none;
  transition: all 0.2s;
}

.search-input:focus {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(29, 185, 84, 0.5);
  box-shadow: 0 0 12px rgba(29, 185, 84, 0.15);
}

.clear-search-btn {
  position: absolute;
  right: 10px;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  border-radius: 50%;
}

.clear-search-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

.filter-chips-row {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.filter-chip:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}

.filter-chip.active {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.25);
  color: #fff;
  font-weight: 600;
}

.filter-chip.new.active {
  background: rgba(29, 185, 84, 0.2);
  border-color: #1ed760;
  color: #1ed760;
}

.filter-chip.in-lib.active {
  background: rgba(59, 130, 246, 0.2);
  border-color: #60a5fa;
  color: #93c5fd;
}

.filter-chip.in-tg.active {
  background: rgba(168, 85, 247, 0.2);
  border-color: #c084fc;
  color: #d8b4fe;
}

.filter-chip.selected.active {
  background: rgba(245, 158, 11, 0.2);
  border-color: #fbbf24;
  color: #fcd34d;
}

.filtered-hint {
  color: #64748b;
  font-weight: 400;
  margin-left: 4px;
}

/* Destination Section */
.destination-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 12px;
}

.destination-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.destination-modes {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.destination-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.15s;
  user-select: none;
}

.destination-chip input[type="radio"] {
  display: none;
}

.destination-chip:hover:not(.disabled) {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.destination-chip.active {
  background: rgba(29, 185, 84, 0.15);
  border-color: rgba(29, 185, 84, 0.4);
  color: #1ed760;
  font-weight: 600;
}

.destination-chip.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.destination-input-wrap, .destination-select-wrap {
  margin-top: 4px;
}

.custom-select-wrapper {
  position: relative;
}

.playlist-dropdown {
  width: 100%;
  background: #181b20;
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #fff;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
  outline: none;
  cursor: pointer;
}

.playlist-dropdown:focus {
  border-color: #1db954;
}

.playlist-dropdown option {
  background: #181b20;
  color: #fff;
}

.destination-summary-hint {
  display: block;
  margin-top: 6px;
  font-size: 11px;
  color: #64748b;
}

.scroll-more-indicator {
  padding: 12px;
  text-align: center;
  font-size: 11px;
  color: #64748b;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  margin-top: 6px;
}

.no-tracks-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px 16px;
  color: #64748b;
  font-size: 13px;
}

.reset-filter-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #e2e8f0;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-filter-btn:hover {
  background: rgba(29, 185, 84, 0.2);
  border-color: #1ed760;
  color: #1ed760;
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
