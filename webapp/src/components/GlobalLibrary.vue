<template>
  <div class="global-library">
    <!-- Stats Banner -->
    <div v-if="library.globalStats" class="stats-banner">
      <div class="stat-item">
        <span class="stat-value">{{ library.globalStats.total_tracks }}</span>
        <span class="stat-label">треков</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ library.globalStats.total_users }}</span>
        <span class="stat-label">пользователей</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ formatPlays(library.globalStats.total_plays) }}</span>
        <span class="stat-label">прослушиваний</span>
      </div>
    </div>

    <!-- Recent Uploads Section -->
    <div v-if="library.recentUploads.length > 0" class="feed-section">
      <h2 class="feed-section-title">🆕 Недавно добавленные</h2>
      <div class="horizontal-scroll">
        <div class="scroll-spacer"></div>
        <div 
          v-for="track in library.recentUploads.slice(0, 10)" 
          :key="track.id"
          class="feed-card track-card"
          @click="$emit('play', track, library.recentUploads)"
        >
          <div class="feed-card-cover" :style="getCoverStyle(track)">
            <img v-if="track.cover_url" :src="track.cover_url" alt="" />
            <svg v-else width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
            </svg>
          </div>
          <div class="feed-card-title">{{ track.title || 'Без названия' }}</div>
          <div class="feed-card-subtitle">{{ track.artist || 'Неизвестный' }}</div>
          <div class="feed-card-meta">
            <span v-if="track.uploader" class="uploader">
              {{ track.uploader.first_name || track.uploader.username }}
            </span>
          </div>
          <!-- In library indicator -->
          <div v-if="track.in_library" class="in-library-badge" title="В вашей библиотеке">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
            </svg>
          </div>
        </div>
        <div class="scroll-spacer"></div>
      </div>
    </div>

    <!-- Popular Tracks Section -->
    <div v-if="library.popularTracks.length > 0" class="feed-section">
      <h2 class="feed-section-title">🔥 Популярное</h2>
      <div class="horizontal-scroll">
        <div class="scroll-spacer"></div>
        <div 
          v-for="track in library.popularTracks.slice(0, 10)" 
          :key="track.id"
          class="feed-card track-card"
          @click="$emit('play', track, library.popularTracks)"
        >
          <div class="feed-card-cover" :style="getCoverStyle(track)">
            <img v-if="track.cover_url" :src="track.cover_url" alt="" />
            <svg v-else width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
            </svg>
            <div class="play-count-badge">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
              </svg>
              {{ formatPlays(track.play_count) }}
            </div>
          </div>
          <div class="feed-card-title">{{ track.title || 'Без названия' }}</div>
          <div class="feed-card-subtitle">{{ track.artist || 'Неизвестный' }}</div>
        </div>
        <div class="scroll-spacer"></div>
      </div>
    </div>

    <!-- All Global Tracks -->
    <div class="feed-section">
      <div class="section-header">
        <h2 class="feed-section-title">🌍 Вся музыка</h2>
        <button class="load-all-btn" @click="loadGlobalTracks">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
          </svg>
        </button>
      </div>
      
      <div v-if="library.globalLoading && !library.globalTracks.length" class="loading">
        <div class="spinner"></div>
        <span>Загрузка...</span>
      </div>
      
      <div v-else-if="library.globalTracks.length === 0" class="empty-state">
        <p>Нажмите кнопку обновления для загрузки</p>
      </div>
      
      <div v-else class="global-track-list">
        <div 
          v-for="track in library.globalTracks" 
          :key="track.id"
          class="global-track-item"
          @click="$emit('play', track, library.globalTracks)"
        >
          <div class="track-cover" :style="getCoverStyle(track)">
            <img v-if="track.cover_url" :src="track.cover_url" alt="" />
            <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
            </svg>
          </div>
          <div class="track-info">
            <span class="track-title">{{ track.title || 'Без названия' }}</span>
            <span class="track-artist">{{ track.artist || 'Неизвестный' }}</span>
            <span v-if="track.uploader" class="track-uploader">
              от {{ track.uploader.first_name || track.uploader.username }}
            </span>
          </div>
          <div class="track-actions">
            <!-- Add to library button -->
            <button 
              v-if="!track.in_library"
              class="add-btn"
              @click.stop="addToLibrary(track)"
              title="Добавить в библиотеку"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
              </svg>
            </button>
            <span v-else class="in-library-icon" title="В вашей библиотеке">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
              </svg>
            </span>
          </div>
        </div>
        
        <!-- Load more button -->
        <button 
          v-if="library.globalHasMore" 
          class="load-more-btn"
          :disabled="library.globalLoading"
          @click="library.loadMoreGlobal()"
        >
          {{ library.globalLoading ? 'Загрузка...' : 'Загрузить ещё' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, inject } from 'vue'
import { useLibraryStore } from '../stores/library'

const library = useLibraryStore()
const telegram = inject('telegram')

const emit = defineEmits(['play'])

// Format play counts
const formatPlays = (count) => {
  if (!count) return '0'
  if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`
  if (count >= 1000) return `${(count / 1000).toFixed(1)}K`
  return count.toString()
}

// Get cover style
const getCoverStyle = (track) => {
  if (track.cover_url) return {}
  // Generate gradient based on track id
  const hue = (track.id * 137) % 360
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 60%, 40%), hsl(${(hue + 60) % 360}, 60%, 30%))`
  }
}

// Load global tracks
const loadGlobalTracks = async () => {
  await library.fetchGlobalTracks()
}

// Add track to user's library
const addToLibrary = async (track) => {
  const success = await library.addToLibrary(track.id)
  if (success) {
    telegram?.HapticFeedback?.notificationOccurred?.('success')
  }
}

// Load initial data
onMounted(async () => {
  if (!library.recentUploads.length) {
    await library.fetchRecentUploads()
  }
  if (!library.popularTracks.length) {
    await library.fetchPopularTracks()
  }
})
</script>

<style scoped>
.global-library {
  padding-bottom: 20px;
}

.stats-banner {
  display: flex;
  justify-content: space-around;
  padding: 16px;
  margin: 0 16px 20px;
  background: linear-gradient(135deg, #1db954 0%, #1ed760 100%);
  border-radius: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: white;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 2px;
}

.feed-section {
  margin-bottom: 24px;
}

.feed-section-title {
  font-size: 18px;
  font-weight: 700;
  padding: 0 16px;
  margin-bottom: 12px;
  color: var(--text-primary, #fff);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-right: 16px;
}

.load-all-btn {
  background: var(--surface-elevated, #282828);
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary, #b3b3b3);
  cursor: pointer;
}

.horizontal-scroll {
  display: flex;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}

.horizontal-scroll::-webkit-scrollbar {
  display: none;
}

.scroll-spacer {
  min-width: 16px;
}

.feed-card {
  min-width: 140px;
  max-width: 140px;
  margin-right: 12px;
  scroll-snap-align: start;
  cursor: pointer;
  position: relative;
}

.feed-card-cover {
  width: 140px;
  height: 140px;
  border-radius: 8px;
  background: var(--surface-elevated, #282828);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
  color: var(--text-secondary, #b3b3b3);
}

.feed-card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.feed-card-title {
  font-size: 14px;
  font-weight: 600;
  margin-top: 8px;
  color: var(--text-primary, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feed-card-subtitle {
  font-size: 12px;
  color: var(--text-secondary, #b3b3b3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feed-card-meta {
  font-size: 11px;
  color: var(--text-tertiary, #666);
  margin-top: 2px;
}

.in-library-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #1db954;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.play-count-badge {
  position: absolute;
  bottom: 8px;
  left: 8px;
  background: rgba(0, 0, 0, 0.7);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: white;
  display: flex;
  align-items: center;
  gap: 4px;
}

.global-track-list {
  padding: 0 16px;
}

.global-track-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color, rgba(255,255,255,0.1));
  cursor: pointer;
}

.global-track-item:active {
  background: var(--surface-elevated, #282828);
}

.track-cover {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  background: var(--surface-elevated, #282828);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
  color: var(--text-secondary, #b3b3b3);
}

.track-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.track-info {
  flex: 1;
  min-width: 0;
  padding: 0 12px;
  display: flex;
  flex-direction: column;
}

.track-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-artist {
  font-size: 13px;
  color: var(--text-secondary, #b3b3b3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-uploader {
  font-size: 11px;
  color: var(--text-tertiary, #666);
}

.track-actions {
  flex-shrink: 0;
}

.add-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--text-secondary, #b3b3b3);
  background: transparent;
  color: var(--text-secondary, #b3b3b3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.add-btn:hover {
  border-color: #1db954;
  color: #1db954;
}

.in-library-icon {
  color: #1db954;
}

.load-more-btn {
  width: 100%;
  padding: 12px;
  margin-top: 12px;
  background: var(--surface-elevated, #282828);
  border: none;
  border-radius: 8px;
  color: var(--text-primary, #fff);
  font-size: 14px;
  cursor: pointer;
}

.load-more-btn:disabled {
  opacity: 0.5;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px;
  color: var(--text-secondary, #b3b3b3);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--surface-elevated, #282828);
  border-top-color: #1db954;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-secondary, #b3b3b3);
}
</style>
