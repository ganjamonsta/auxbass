<template>
  <div class="soundcloud-results-mode">
    <!-- Back to full search breadcrumb bar -->
    <div class="sc-nav-breadcrumb-bar">
      <button class="sc-back-search-btn" @click="$emit('resetToAllSearch')">
        <ArrowLeft :size="15" />
        <span>Все разделы поиска</span>
      </button>
      <div class="sc-service-pill sc">
        <span class="sc-badge">SC</span>
        <span>SoundCloud</span>
      </div>
    </div>

    <!-- Sub-tab Switcher -->
    <div class="sc-tab-switcher">
      <button 
        class="sc-subtab-btn" 
        :class="{ active: scSubTab === 'search' }"
        @click="$emit('setScSubTab', 'search')"
      >
        <Globe :size="15" />
        <span>Глобальный поиск</span>
        <span v-if="soundcloudResults.length > 0" class="sc-subtab-count">{{ soundcloudResults.length }}</span>
      </button>
      <button 
        class="sc-subtab-btn" 
        :class="{ active: scSubTab === 'likes' }"
        @click="$emit('setScSubTab', 'likes')"
      >
        <Heart :size="15" />
        <span>Мои лайки</span>
        <span v-if="searchQuery.trim()" class="sc-subtab-count">{{ filteredScLikes.length }}</span>
        <span v-else-if="scAccount?.likes_count" class="sc-subtab-count">{{ scAccount.likes_count }}</span>
      </button>
    </div>

    <!-- 1. SEARCH MODE -->
    <template v-if="scSubTab === 'search'">
      <div class="section-header">
        <span class="section-title">
          <span class="sc-badge">SC</span> SoundCloud (Глобальный поиск)
        </span>
        <span class="section-count">{{ soundcloudResults.length }}</span>
      </div>

      <div v-if="isSoundCloudSearching" class="section-loading-indicator">
        <div class="spinner small"></div>
        <span>Поиск на SoundCloud...</span>
      </div>

      <div v-else-if="soundcloudResults.length > 0" class="sc-results-list full-list">
        <ExternalTrackItem
          v-for="item in soundcloudResults"
          :key="item.url"
          :item="item"
          variant="soundcloud"
          :show-badges="true"
          :is-importing="importingTrackUrl === item.url"
          :is-downloading="tasksStore.isTrackDownloading(item.url)"
          :is-queued="tasksStore.isTrackQueued(item.url)"
          :is-in-library="isTrackInLibrary(item)"
          @play="$emit('quickPlaySoundCloud', item)"
          @add="$emit('quickAddSoundCloud', item)"
        />

        <!-- Load More SoundCloud Button -->
        <div class="sc-load-more-wrap">
          <button 
            v-if="soundcloudResults.length < 60"
            class="sc-load-more-btn"
            :disabled="isLoadingMoreSoundCloud"
            @click="$emit('loadMoreSoundCloud')"
          >
            <div v-if="isLoadingMoreSoundCloud" class="spinner small"></div>
            <template v-else>Загрузить ещё (до 60)</template>
          </button>
          <span v-else class="sc-end-notice">Показаны 60 лучших результатов SoundCloud</span>
        </div>
      </div>

      <NoResultsBox 
        v-else-if="!isSoundCloudSearching" 
        :text="searchQuery.trim() ? 'На SoundCloud ничего не найдено' : 'Введите поисковый запрос выше для поиска треков на SoundCloud'" 
      />
    </template>

    <!-- 2. LIKES MODE -->
    <template v-else-if="scSubTab === 'likes'">
      <!-- Account Connected Header -->
      <div v-if="scAccount?.connected" class="sc-likes-header-card">
        <div class="sc-likes-user-bar">
          <img 
            v-if="scAccount.avatar_url" 
            :src="scAccount.avatar_url" 
            alt="" 
            class="sc-likes-avatar"
            referrerpolicy="no-referrer" 
          />
          <div v-else class="sc-likes-avatar-placeholder">
            <Radio :size="18" />
          </div>
          <div class="sc-likes-user-meta">
            <span class="sc-likes-username">{{ scAccount.display_name || scAccount.username }}</span>
            <span class="sc-likes-stats-text">❤️ {{ scAccount.likes_count || scLikes.length }} лайков на SoundCloud</span>
          </div>
        </div>

        <div class="sc-likes-header-actions">
          <button 
            class="sc-sync-btn"
            :disabled="isSyncingAllLikes || isScLikesLoading || unimportedLikesCount === 0"
            @click="$emit('handleSyncAllLikes')"
            title="Импортировать все новые треки в медиатеку и канал"
          >
            <div v-if="isSyncingAllLikes" class="spinner small"></div>
            <CloudDownload v-else :size="15" />
            <span>{{ isSyncingAllLikes ? 'Синхронизация...' : `Синхронизировать новые (${unimportedLikesCount})` }}</span>
          </button>
          <button 
            class="sc-refresh-icon-btn" 
            :disabled="isScLikesLoading"
            @click="$emit('fetchScLikes', true)"
            title="Обновить список лайков"
          >
            <RefreshCw :size="15" :class="{ 'spin-icon': isScLikesLoading }" />
          </button>
        </div>
      </div>

      <!-- Sync progress bar if active -->
      <div v-if="syncJobProgress" class="sc-sync-progress-banner">
        <div class="sc-sync-info-row">
          <span class="sc-sync-msg">Импорт: {{ syncJobProgress.current_track_title || 'Загрузка...' }}</span>
          <span class="sc-sync-count">{{ syncJobProgress.processed_tracks }} / {{ syncJobProgress.total_tracks }}</span>
        </div>
        <div class="sc-sync-bar-track">
          <div 
            class="sc-sync-bar-fill" 
            :style="{ width: `${Math.round((syncJobProgress.processed_tracks / (syncJobProgress.total_tracks || 1)) * 100)}%` }"
          ></div>
        </div>
      </div>

      <!-- Loading indicator -->
      <div v-if="isScLikesLoading && scLikes.length === 0" class="section-loading-indicator">
        <div class="spinner small"></div>
        <span>Загрузка лайков с SoundCloud...</span>
      </div>

      <!-- Active Search Filter Banner for Likes -->
      <div v-if="searchQuery.trim() && scLikes.length > 0" class="sc-likes-filter-notice">
        <span>Фильтр лайков: <b>«{{ searchQuery.trim() }}»</b> (найдено {{ filteredScLikes.length }})</span>
        <button class="clear-filter-mini-btn" @click="$emit('clearSearchInput')" title="Сбросить фильтр поиска">
          ✕ Сбросить
        </button>
      </div>

      <!-- Likes Track List -->
      <div v-if="filteredScLikes.length > 0" class="sc-results-list full-list">
        <ExternalTrackItem
          v-for="item in filteredScLikes"
          :key="item.url"
          :item="item"
          variant="soundcloud"
          :show-badges="true"
          :is-importing="importingTrackUrl === item.url"
          :is-downloading="tasksStore.isTrackDownloading(item.url)"
          :is-queued="tasksStore.isTrackQueued(item.url)"
          :is-in-library="isTrackInLibrary(item)"
          @play="$emit('quickPlaySoundCloud', item)"
          @add="$emit('quickAddSoundCloud', item)"
        />

        <!-- Load more likes button -->
        <div v-if="scLikesCursor" class="sc-load-more-wrap">
          <button 
            class="sc-load-more-btn"
            :disabled="isLoadingMoreScLikes || isSearchingDeeperLikes"
            @click="searchQuery.trim() ? $emit('loadAllLikesUntilMatch') : $emit('loadMoreScLikes')"
          >
            <div v-if="isLoadingMoreScLikes || isSearchingDeeperLikes" class="spinner small"></div>
            <template v-else>
              {{ searchQuery.trim() ? 'Искать глубже в остальных лайках' : `Загрузить ещё лайки (${scLikes.length} из ${scAccount?.likes_count || '...'})` }}
            </template>
          </button>
        </div>
      </div>

      <!-- No results in likes matching query -->
      <NoResultsBox 
        v-else-if="searchQuery.trim() && scLikes.length > 0 && !isScLikesLoading" 
        :text="`В загруженных лайках нет треков по запросу «${searchQuery}»`" 
        :hint="`Проверено ${scLikes.length} из ${scAccount?.likes_count || scLikes.length} лайков вашего профиля.`"
      >
        <div class="sc-no-results-actions">
          <button 
            v-if="scLikesCursor"
            class="sc-load-more-btn"
            :disabled="isLoadingMoreScLikes || isSearchingDeeperLikes"
            @click="$emit('loadAllLikesUntilMatch')"
          >
            <div v-if="isLoadingMoreScLikes || isSearchingDeeperLikes" class="spinner small"></div>
            <template v-else>Искать дальше в остальных лайках</template>
          </button>
          <button class="sc-load-more-btn sc-global-fallback-btn" @click="$emit('setScSubTab', 'search')">
            <Globe :size="15" />
            <span>Искать во всём каталоге SoundCloud</span>
          </button>
        </div>
      </NoResultsBox>

      <!-- Not Connected Prompt -->
      <div v-else-if="!scAccount?.connected && !isScLikesLoading" class="sc-not-connected-banner">
        <div class="sc-banner-icon">
          <Radio :size="32" />
        </div>
        <h4 class="sc-banner-title">Аккаунт SoundCloud не подключен</h4>
        <p class="sc-banner-desc">
          Привяжите ваш профиль SoundCloud в настройках, чтобы просматривать лайки, слушать и автоматически сохранять аудиофайлы в личный Telegram-канал.
        </p>
        <button class="sc-btn primary" @click="$emit('goToSettings')">
          <Settings :size="15" />
          <span>Открыть настройки</span>
        </button>
      </div>

      <!-- Empty likes -->
      <NoResultsBox 
        v-else-if="!isScLikesLoading" 
        text="Лайков на SoundCloud пока нет" 
        hint="Поставьте лайки на SoundCloud и нажмите «Обновить»" 
      />
    </template>
  </div>
</template>

<script setup>
import { ArrowLeft, Globe, Heart, CloudDownload, RefreshCw, Radio, Settings } from 'lucide-vue-next'
import ExternalTrackItem from '@/components/ExternalTrackItem.vue'
import NoResultsBox from '@/components/NoResultsBox.vue'
import { useTasksStore } from '@/stores/tasks'

const props = defineProps({
  soundcloudResults: { type: Array, required: true },
  searchQuery: { type: String, required: true },
  scSubTab: { type: String, required: true },
  isSoundCloudSearching: { type: Boolean, required: true },
  isLoadingMoreSoundCloud: { type: Boolean, required: true },
  importingTrackUrl: { type: String, default: null },
  
  scAccount: { type: Object, default: null },
  scLikes: { type: Array, required: true },
  filteredScLikes: { type: Array, required: true },
  scLikesCursor: { type: String, default: null },
  isScLikesLoading: { type: Boolean, required: true },
  isLoadingMoreScLikes: { type: Boolean, required: true },
  isSearchingDeeperLikes: { type: Boolean, required: true },
  isSyncingAllLikes: { type: Boolean, required: true },
  syncJobProgress: { type: Object, default: null },
  unimportedLikesCount: { type: Number, required: true }
})

const emit = defineEmits([
  'resetToAllSearch',
  'setScSubTab',
  'loadMoreSoundCloud',
  'quickPlaySoundCloud',
  'quickAddSoundCloud',
  'handleSyncAllLikes',
  'fetchScLikes',
  'clearSearchInput',
  'loadAllLikesUntilMatch',
  'loadMoreScLikes',
  'goToSettings'
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

/* SoundCloud Search Styles */
.sc-badge {
  background: #ff5500;
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.5px;
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
  background: rgba(255, 85, 0, 0.12);
  border: 1px solid rgba(255, 85, 0, 0.3);
  border-radius: 12px;
  color: #ff7700;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-load-more-btn:hover:not(:disabled) {
  background: #ff5500;
  color: #fff;
  border-color: #ff5500;
  box-shadow: 0 4px 16px rgba(255, 85, 0, 0.3);
}

.sc-load-more-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sc-end-notice {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.4);
}

/* SoundCloud Navigation & Sub-tabs */
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
  background: #ff5500;
  color: #fff;
  box-shadow: 0 2px 10px rgba(255, 85, 0, 0.35);
}

.sc-subtab-count {
  font-size: 11px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
}

.sc-likes-filter-notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: rgba(255, 85, 0, 0.1);
  border: 1px solid rgba(255, 85, 0, 0.25);
  border-radius: 10px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--c-text-1);
}

.clear-filter-mini-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 6px;
  color: #ffaa77;
  font-size: 11px;
  padding: 4px 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.clear-filter-mini-btn:hover {
  background: rgba(255, 85, 0, 0.25);
  color: #fff;
}

.sc-no-results-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 14px;
  flex-wrap: wrap;
}

.sc-global-fallback-btn {
  background: #ff5500 !important;
  color: #fff !important;
  border-color: #ff5500 !important;
}

.sc-likes-header-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(255, 85, 0, 0.06);
  border: 1px solid rgba(255, 85, 0, 0.2);
  border-radius: 14px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.sc-likes-user-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sc-likes-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 2px solid #ff5500;
  object-fit: cover;
}

.sc-likes-avatar-placeholder {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: rgba(255, 85, 0, 0.2);
  color: #ff5500;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sc-likes-user-meta {
  display: flex;
  flex-direction: column;
}

.sc-likes-username {
  font-size: 14px;
  font-weight: 700;
  color: var(--c-text-1);
}

.sc-likes-stats-text {
  font-size: 12px;
  color: var(--c-text-3);
}

.sc-likes-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sc-sync-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: #ff5500;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(255, 85, 0, 0.3);
  transition: all 0.2s ease;
}

.sc-sync-btn:hover:not(:disabled) {
  background: #ff6611;
  transform: translateY(-1px);
}

.sc-sync-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sc-refresh-icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-refresh-icon-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.sc-sync-progress-banner {
  padding: 10px 14px;
  background: rgba(255, 85, 0, 0.1);
  border: 1px solid rgba(255, 85, 0, 0.25);
  border-radius: 10px;
  margin-bottom: 14px;
}

.sc-sync-info-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-1);
  margin-bottom: 6px;
}

.sc-sync-msg {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80%;
}

.sc-sync-bar-track {
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.sc-sync-bar-fill {
  height: 100%;
  background: #ff5500;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.sc-not-connected-banner {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 32px 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px dashed rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  margin-top: 16px;
}

.sc-banner-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(255, 85, 0, 0.12);
  color: #ff5500;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.sc-banner-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0 0 6px 0;
}

.sc-banner-desc {
  font-size: 13px;
  color: var(--c-text-3);
  max-width: 440px;
  line-height: 1.5;
  margin: 0 0 16px 0;
}

.sc-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 9px 16px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  font-family: inherit;
}

.sc-btn.primary {
  background: #ff5500;
  color: #fff;
  box-shadow: 0 4px 12px rgba(255, 85, 0, 0.3);
}

.sc-btn.primary:hover {
  background: #ff6611;
  transform: translateY(-1px);
}
</style>
