<template>
  <div class="spotify-results-mode">
    <!-- Back to full search breadcrumb bar -->
    <div class="sc-nav-breadcrumb-bar">
      <button class="sc-back-search-btn" @click="$emit('resetToAllSearch')">
        <ArrowLeft :size="15" />
        <span>Все разделы поиска</span>
      </button>
      <div class="sc-service-pill sp">
        <span class="sp-badge">SP</span>
        <span>Spotify</span>
      </div>
    </div>

    <!-- Sub-tab Switcher -->
    <div class="sc-tab-switcher">
      <button 
        class="sc-subtab-btn" 
        :class="{ active: spSubTab === 'search' }"
        @click="$emit('setSpSubTab', 'search')"
      >
        <Globe :size="15" />
        <span>Глобальный поиск</span>
        <span v-if="spotifyResults.length > 0" class="sc-subtab-count sp-count">{{ spotifyResults.length }}</span>
      </button>
      <button 
        class="sc-subtab-btn" 
        :class="{ active: spSubTab === 'exportify' }"
        @click="$emit('setSpSubTab', 'exportify')"
      >
        <FileSpreadsheet :size="15" />
        <span>Импорт Exportify (CSV)</span>
      </button>
    </div>

    <!-- 1. SEARCH MODE -->
    <template v-if="spSubTab === 'search'">
      <div class="section-header">
        <span class="section-title">
          <span class="sp-badge">SP</span> Spotify (Глобальный поиск)
        </span>
        <span class="section-count">{{ spotifyResults.length }}</span>
      </div>

      <div v-if="isSpotifySearching" class="section-loading-indicator">
        <div class="spinner small"></div>
        <span>Поиск на Spotify...</span>
      </div>

      <div v-else-if="spotifyResults.length > 0" class="sc-results-list full-list">
        <ExternalTrackItem
          v-for="item in spotifyResults"
          :key="item.url"
          :item="item"
          variant="spotify"
          :show-badges="true"
          :is-importing="importingTrackUrl === item.url"
          :is-downloading="tasksStore.isTrackDownloading(item.url)"
          :is-queued="tasksStore.isTrackQueued(item.url)"
          :is-in-library="isTrackInLibrary(item)"
          @play="$emit('quickPlaySpotify', item)"
          @add="$emit('quickAddSpotify', item)"
        />

        <!-- Load More Spotify Button -->
        <div class="sc-load-more-wrap">
          <button 
            v-if="spotifyResults.length < 60"
            class="sc-load-more-btn sp-load-more"
            :disabled="isLoadingMoreSpotify"
            @click="$emit('loadMoreSpotify')"
          >
            <div v-if="isLoadingMoreSpotify" class="spinner small"></div>
            <template v-else>Загрузить ещё (до 60)</template>
          </button>
          <span v-else class="sc-end-notice">Показаны 60 лучших результатов Spotify</span>
        </div>
      </div>

      <NoResultsBox 
        v-else-if="!isSpotifySearching" 
        :text="searchQuery.trim() ? 'В каталоге ничего не найдено' : 'Введите поисковый запрос выше для поиска треков в каталоге Spotify'" 
      />
    </template>

    <!-- 2. EXPORTIFY CSV MODE -->
    <template v-else-if="spSubTab === 'exportify'">
      <div class="sp-exportify-view-card">
        <div class="sp-exportify-header-banner">
          <div class="sp-exportify-icon-large">
            <FileSpreadsheet :size="32" />
          </div>
          <div class="sp-exportify-banner-text">
            <h3 class="sp-exportify-title">Импорт медиатеки Spotify через Exportify</h3>
            <p class="sp-exportify-subtitle">
              100% бесплатно и без ограничений: выгрузите любимые треки или плейлисты в CSV и импортируйте их в высоком качестве 320 kbps с автоматическим распознаванием дубликатов.
            </p>
          </div>
        </div>

        <div class="sp-exportify-steps-grid">
          <div class="sp-step-card">
            <span class="sp-step-badge">1</span>
            <h4>Экспорт на exportify.app</h4>
            <p>Откройте бесплатный веб-сервис в браузере (работает в 1 клик):</p>
            <a href="https://exportify.app" target="_blank" rel="noopener noreferrer" class="sp-ext-link-btn">
              <span>exportify.app</span>
              <ExternalLink :size="13" />
            </a>
          </div>
          <div class="sp-step-card">
            <span class="sp-step-badge">2</span>
            <h4>Скачайте CSV-файл</h4>
            <p>Нажмите <b>«Export»</b> напротив <b>«Liked Songs»</b> или любого плейлиста.</p>
          </div>
          <div class="sp-step-card highlight">
            <span class="sp-step-badge">3</span>
            <h4>Загрузите сюда</h4>
            <p>Откройте окно импорта и перетащите скачанный файл:</p>
            <button class="sp-open-modal-btn" @click="tasksStore.openExportifyModal()">
              <Upload :size="15" />
              <span>Открыть окно импорта CSV</span>
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ArrowLeft, Globe, FileSpreadsheet, ExternalLink, Upload } from 'lucide-vue-next'
import ExternalTrackItem from '@/components/ExternalTrackItem.vue'
import NoResultsBox from '@/components/NoResultsBox.vue'
import { useTasksStore } from '@/stores/tasks'

const props = defineProps({
  spotifyResults: { type: Array, required: true },
  searchQuery: { type: String, required: true },
  spSubTab: { type: String, required: true },
  isSpotifySearching: { type: Boolean, required: true },
  isLoadingMoreSpotify: { type: Boolean, required: true },
  importingTrackUrl: { type: String, default: null }
})

const emit = defineEmits([
  'resetToAllSearch',
  'setSpSubTab',
  'loadMoreSpotify',
  'quickPlaySpotify',
  'quickAddSpotify'
])

const tasksStore = useTasksStore()

const isTrackInLibrary = (item) => {
  if (!item) return false
  return item.in_library || tasksStore.isTrackCompleted(item.url)
}
</script>

<style scoped>
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  letter-spacing: -0.01em;
}

.section-count {
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-3, rgba(255, 255, 255, 0.45));
}

.section-loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  font-size: 13px;
}

.sc-results-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sc-results-list.full-list {
  margin-top: 12px;
}

.sc-load-more-wrap {
  display: flex;
  justify-content: center;
  margin-top: 16px;
  margin-bottom: 24px;
}

.sc-load-more-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: rgba(30, 215, 96, 0.12);
  border: 1px solid rgba(30, 215, 96, 0.3);
  border-radius: 12px;
  color: #1ed760;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-load-more-btn:hover:not(:disabled) {
  background: #1ed760;
  color: #000;
  border-color: #1ed760;
  box-shadow: 0 4px 16px rgba(30, 215, 96, 0.3);
}

.sc-load-more-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sc-end-notice {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.4);
}

/* Spotify Navigation & Sub-tabs */
.sc-nav-breadcrumb-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 2px 0;
}

.sc-back-search-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--c-text-1, #fff);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.sc-back-search-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.28);
  color: var(--c-accent, #1db954);
  transform: translateX(-2px);
}

.sc-service-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
}

.sc-tab-switcher {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  background: rgba(255, 255, 255, 0.03);
  padding: 4px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.sc-subtab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  background: none;
  color: var(--c-text-3);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-subtab-btn:hover {
  color: var(--c-text-1);
}

.sc-subtab-btn.active {
  background: #1ed760;
  color: #000;
  box-shadow: 0 2px 10px rgba(30, 215, 96, 0.35);
}

/* Spotify Styling */
.sp-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #1ed760;
  color: #000;
  font-size: 10px;
  font-weight: 800;
  padding: 1px 5px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.sp-count {
  background: rgba(30, 215, 96, 0.2);
  color: #1ed760;
}

.sp-sync-btn {
  background: #1ed760 !important;
  color: #000 !important;
  box-shadow: 0 2px 8px rgba(30, 215, 96, 0.3) !important;
}

.sp-sync-btn:hover:not(:disabled) {
  background: #22e668 !important;
}

.sp-progress-banner {
  background: rgba(30, 215, 96, 0.1) !important;
  border-color: rgba(30, 215, 96, 0.25) !important;
}

.sp-bar-fill {
  background: #1ed760 !important;
}

.sp-banner-icon {
  background: rgba(30, 215, 96, 0.12) !important;
  color: #1ed760 !important;
}

.sp-primary {
  background: #1ed760 !important;
  color: #000 !important;
  font-weight: 700 !important;
}

.sp-primary:hover:not(:disabled) {
  background: #22e668 !important;
}

.sp-placeholder {
  color: #1ed760 !important;
}

.sp-header-card {
  border-left: 3px solid #1ed760;
}

/* Exportify View Card */
.sp-exportify-view-card {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 10px 0;
}

.sp-exportify-header-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(29, 185, 84, 0.08);
  border: 1px solid rgba(29, 185, 84, 0.2);
  border-radius: 16px;
  padding: 20px 24px;
}

.sp-exportify-icon-large {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: rgba(29, 185, 84, 0.16);
  color: #1ed760;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sp-exportify-title {
  margin: 0 0 6px 0;
  font-size: 17px;
  font-weight: 700;
  color: #fff;
}

.sp-exportify-subtitle {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: #a7b1bc;
}

.sp-exportify-steps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
}

.sp-step-card {
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  padding: 18px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sp-step-card.highlight {
  background: rgba(29, 185, 84, 0.06);
  border-color: rgba(29, 185, 84, 0.25);
}

.sp-step-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #1db954;
  color: #000;
  font-weight: 700;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sp-step-card h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #f1f3f5;
}

.sp-step-card p {
  margin: 0;
  font-size: 12px;
  color: #8b929a;
  line-height: 1.4;
}

.sp-ext-link-btn {
  margin-top: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #1ed760;
  text-decoration: underline;
  font-size: 13px;
  font-weight: 600;
}

.sp-open-modal-btn {
  margin-top: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #1db954;
  color: #000;
  border: none;
  padding: 9px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(29, 185, 84, 0.3);
}

.sp-open-modal-btn:hover {
  background: #24d864;
  transform: translateY(-1px);
}
</style>
