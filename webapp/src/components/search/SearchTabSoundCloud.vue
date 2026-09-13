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
