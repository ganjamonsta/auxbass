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
