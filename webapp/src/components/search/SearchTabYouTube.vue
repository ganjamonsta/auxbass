<template>
  <div class="youtube-results-mode">
    <!-- Back to full search breadcrumb bar -->
    <div class="sc-nav-breadcrumb-bar">
      <button class="sc-back-search-btn" @click="$emit('resetToAllSearch')">
        <ArrowLeft :size="15" />
        <span>Все разделы поиска</span>
      </button>
      <div class="sc-service-pill yt">
        <span class="yt-badge">YT</span>
        <span>YouTube Music</span>
      </div>
    </div>

    <!-- Section Header -->
    <div class="section-header">
      <span class="section-title">
        <span class="yt-badge">YT</span> YouTube Music (Глобальный поиск)
      </span>
      <span class="section-count">{{ youtubeResults.length }}</span>
    </div>

    <!-- Loading Indicator -->
    <div v-if="isYouTubeSearching" class="section-loading-indicator">
      <div class="spinner small"></div>
      <span>Поиск на YouTube Music...</span>
    </div>

    <!-- Results List -->
    <div v-else-if="youtubeResults.length > 0" class="sc-results-list full-list">
      <ExternalTrackItem
        v-for="item in youtubeResults"
        :key="item.url"
        :item="item"
        variant="youtube"
        :show-badges="true"
        :is-importing="importingTrackUrl === item.url"
        :is-downloading="tasksStore.isTrackDownloading(item.url)"
        :is-queued="tasksStore.isTrackQueued(item.url)"
        :is-in-library="isTrackInLibrary(item)"
        @play="$emit('quickPlayYouTube', item)"
        @add="$emit('quickAddYouTube', item)"
      />

      <!-- Load More Button -->
      <div class="sc-load-more-wrap">
        <button 
          v-if="youtubeResults.length < 60"
          class="sc-load-more-btn yt-load-more"
          :disabled="isLoadingMoreYouTube"
          @click="$emit('loadMoreYouTube')"
        >
          <div v-if="isLoadingMoreYouTube" class="spinner small"></div>
          <template v-else>Загрузить ещё (до 60)</template>
        </button>
        <span v-else class="sc-end-notice">Показаны 60 лучших результатов YouTube Music</span>
      </div>
    </div>

    <!-- No Results Box -->
    <NoResultsBox 
      v-else-if="!isYouTubeSearching" 
      :text="searchQuery.trim() ? 'В каталоге YouTube Music ничего не найдено' : 'Введите поисковый запрос выше для поиска треков в YouTube Music'" 
    />
  </div>
</template>

<script setup>
import { ArrowLeft } from 'lucide-vue-next'
import ExternalTrackItem from '@/components/ExternalTrackItem.vue'
import NoResultsBox from '@/components/NoResultsBox.vue'
import { useTasksStore } from '@/stores/tasks'

defineProps({
  youtubeResults: { type: Array, required: true },
  searchQuery: { type: String, required: true },
  isYouTubeSearching: { type: Boolean, required: true },
  isLoadingMoreYouTube: { type: Boolean, required: true },
  importingTrackUrl: { type: String, default: null }
})

defineEmits([
  'resetToAllSearch',
  'loadMoreYouTube',
  'quickPlayYouTube',
  'quickAddYouTube'
])

const tasksStore = useTasksStore()

const isTrackInLibrary = (item) => {
  if (!item) return false
  return item.in_library || tasksStore.isTrackCompleted(item.url)
}
</script>

<style scoped>
.youtube-results-mode {
  padding-bottom: 32px;
}

.sc-nav-breadcrumb-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 8px;
}

.sc-back-search-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 6px 12px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-back-search-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.2);
}

.sc-service-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.sc-service-pill.yt {
  background: rgba(255, 0, 51, 0.12);
  border: 1px solid rgba(255, 0, 51, 0.3);
  color: #ff334b;
}

.yt-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #ff0033;
  color: #fff;
  font-size: 9px;
  font-weight: 800;
  padding: 2px 5px;
  border-radius: 4px;
  letter-spacing: 0.04em;
}

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
  background: rgba(255, 0, 51, 0.12);
  border: 1px solid rgba(255, 0, 51, 0.3);
  border-radius: 12px;
  color: #ff334b;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-load-more-btn:hover:not(:disabled) {
  background: rgba(255, 0, 51, 0.22);
  border-color: rgba(255, 0, 51, 0.5);
  color: #fff;
  transform: translateY(-1px);
}

.sc-load-more-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sc-end-notice {
  font-size: 12px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.4));
  font-style: italic;
}

.spinner.small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: #ff0033;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
