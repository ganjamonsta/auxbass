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
        <span class="stat-value">{{ formatPlayCount(library.globalStats.total_plays) }}</span>
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
              {{ formatPlayCount(track.play_count) }}
            </div>
          </div>
          <div class="feed-card-title">{{ track.title || 'Без названия' }}</div>
          <div class="feed-card-subtitle">{{ track.artist || 'Неизвестный' }}</div>
        </div>
        <div class="scroll-spacer"></div>
      </div>
    </div>

    <!-- Top Users Section -->
    <div v-if="library.topUsers.length > 0" class="feed-section">
      <h2 class="feed-section-title">👥 Пользователи</h2>
      <div class="horizontal-scroll">
        <div class="scroll-spacer"></div>
        <div 
          v-for="user in library.topUsers" 
          :key="user.id"
          class="feed-card user-card"
          @click="openUserProfile(user)"
        >
          <div class="user-avatar" :style="getAvatarStyle(user)">
            <span class="avatar-letter">{{ getInitials(user) }}</span>
          </div>
          <div class="feed-card-title">{{ user.first_name || user.username || 'User' }}</div>
          <div class="feed-card-subtitle">{{ user.track_count }} треков</div>
          <div class="feed-card-meta">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z"/>
            </svg>
            {{ formatPlayCount(user.total_plays) }}
          </div>
        </div>
        <div class="scroll-spacer"></div>
      </div>
    </div>

    <!-- User Profile View (when selected) -->
    <div v-if="library.selectedUser" class="user-profile-view">
      <div class="user-profile-header">
        <button class="back-btn" @click="library.clearSelectedUser()">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
        </button>
        <div class="user-avatar-large" :style="getAvatarStyle(library.selectedUser)">
          <span class="avatar-letter-large">{{ getInitials(library.selectedUser) }}</span>
        </div>
        <div class="user-profile-info">
          <h2>{{ library.selectedUser.first_name || library.selectedUser.username || 'User' }}</h2>
          <p v-if="library.selectedUser.username">@{{ library.selectedUser.username }}</p>
          <p class="user-stats">
            {{ library.selectedUser.track_count || library.selectedUserTracks.length }} треков • 
            {{ formatPlayCount(library.selectedUser.total_plays || 0) }} прослушиваний
          </p>
        </div>
      </div>
      <div class="user-tracks-list">
        <div 
          v-for="track in library.selectedUserTracks" 
          :key="track.id"
          class="global-track-item"
          @click="$emit('play', track, library.selectedUserTracks)"
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
          </div>
          <div class="track-actions">
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
      </div>
    </div>

    <!-- All Global Tracks (hidden when user profile is open) -->
    <div v-if="!library.selectedUser" class="feed-section">
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
import { formatPlayCount } from '@/utils'

const library = useLibraryStore()
const telegram = inject('telegram')

const emit = defineEmits(['play'])

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

// Get user initials
const getInitials = (user) => {
  if (user.first_name) {
    return user.first_name.charAt(0).toUpperCase()
  }
  if (user.username) {
    return user.username.charAt(0).toUpperCase()
  }
  return 'U'
}

// Get avatar gradient style
const getAvatarStyle = (user) => {
  const hue = ((user.id || 0) * 137) % 360
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 70%, 45%), hsl(${(hue + 40) % 360}, 70%, 35%))`
  }
}

// Open user profile
const openUserProfile = async (user) => {
  telegram?.HapticFeedback?.impactOccurred?.('light')
  await library.fetchUserTracks(user.id)
}

// Load initial data
onMounted(async () => {
  if (!library.recentUploads.length) {
    await library.fetchRecentUploads()
  }
  if (!library.popularTracks.length) {
    await library.fetchPopularTracks()
  }
  if (!library.topUsers.length) {
    await library.fetchTopUsers()
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
  padding: 18px;
  margin: 0 16px 24px;
  background: linear-gradient(135deg, var(--xm-accent, #E53935) 0%, var(--xm-accent-dark, #C62828) 100%);
  border-radius: var(--neu-radius-lg, 16px);
  box-shadow: 
    6px 6px 12px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -3px -3px 6px var(--neu-shadow-light, rgba(255, 255, 255, 0.03)),
    0 4px 20px var(--xm-accent-glow, rgba(229, 57, 53, 0.3));
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 26px;
  font-weight: 800;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.85);
  margin-top: 4px;
  font-weight: 500;
}

.feed-section {
  margin-bottom: 28px;
}

.feed-section-title {
  font-size: 18px;
  font-weight: 700;
  padding: 0 16px;
  margin-bottom: 14px;
  color: var(--xm-text-primary, #fff);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-right: 16px;
}

.load-all-btn {
  background: var(--xm-bg-elevated, #1A1A1A);
  border: none;
  border-radius: var(--neu-radius-full, 9999px);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-text-muted, #888);
  cursor: pointer;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -2px -2px 4px var(--neu-shadow-light, rgba(255, 255, 255, 0.03));
  transition: all 0.15s ease;
}

.load-all-btn:active {
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -1px -1px 2px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
}

.horizontal-scroll {
  display: flex;
  gap: 14px;
  overflow-x: auto;
  scroll-snap-type: x proximity;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  padding: 12px 0;
  padding-left: 16px;
  padding-right: 16px;
}

.horizontal-scroll::-webkit-scrollbar {
  display: none;
}

.horizontal-scroll::after {
  content: '';
  flex-shrink: 0;
  width: 4px;
}

.scroll-spacer {
  display: none;
}

.feed-card {
  flex-shrink: 0;
  min-width: 150px;
  max-width: 150px;
  scroll-snap-align: none;
  cursor: pointer;
  position: relative;
}

.feed-card-cover {
  width: 150px;
  height: 150px;
  border-radius: var(--neu-radius-md, 12px);
  background: var(--xm-bg-elevated, #1A1A1A);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
  color: var(--xm-text-muted, #888);
  box-shadow: 
    6px 6px 12px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -3px -3px 6px var(--neu-shadow-light, rgba(255, 255, 255, 0.03));
  transition: transform 0.15s ease;
}

.feed-card:active .feed-card-cover {
  transform: scale(0.97);
}

.feed-card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.feed-card-title {
  font-size: 14px;
  font-weight: 600;
  margin-top: 10px;
  color: var(--xm-text-primary, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feed-card-subtitle {
  font-size: 12px;
  color: var(--xm-text-muted, #888);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feed-card-meta {
  font-size: 11px;
  color: var(--xm-text-muted, #888);
  margin-top: 3px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.in-library-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 28px;
  height: 28px;
  border-radius: var(--neu-radius-full, 9999px);
  background: var(--xm-accent, #E53935);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 3px 10px var(--xm-accent-glow, rgba(229, 57, 53, 0.4));
}

.play-count-badge {
  position: absolute;
  bottom: 10px;
  left: 10px;
  background: var(--xm-bg-deep, #0D0D0D);
  padding: 5px 10px;
  border-radius: var(--neu-radius-sm, 8px);
  font-size: 11px;
  color: white;
  display: flex;
  align-items: center;
  gap: 5px;
  font-weight: 600;
  box-shadow: 
    2px 2px 4px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5));
}

.global-track-list {
  padding: 0 16px;
}

.global-track-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 10px;
  background: var(--xm-bg-elevated, #1A1A1A);
  border-radius: var(--neu-radius-md, 12px);
  cursor: pointer;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -2px -2px 4px var(--neu-shadow-light, rgba(255, 255, 255, 0.03));
  transition: all 0.15s ease;
}

.global-track-item:active {
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -1px -1px 2px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
}

.track-cover {
  width: 52px;
  height: 52px;
  border-radius: var(--neu-radius-sm, 8px);
  background: var(--xm-bg-surface, #222);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
  color: var(--xm-text-muted, #888);
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -1px -1px 2px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
}

.track-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.track-info {
  flex: 1;
  min-width: 0;
  padding: 0 14px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.track-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--xm-text-primary, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-artist {
  font-size: 13px;
  color: var(--xm-text-muted, #888);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-uploader {
  font-size: 11px;
  color: var(--xm-text-muted, #888);
}

.track-actions {
  flex-shrink: 0;
}

.add-btn {
  width: 40px;
  height: 40px;
  border-radius: var(--neu-radius-full, 9999px);
  border: none;
  background: var(--xm-bg-surface, #222);
  color: var(--xm-text-muted, #888);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 
    3px 3px 6px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -2px -2px 4px var(--neu-shadow-light, rgba(255, 255, 255, 0.03));
  transition: all 0.15s ease;
}

.add-btn:active {
  color: var(--xm-accent, #E53935);
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -1px -1px 2px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
}

.in-library-icon {
  color: var(--xm-accent, #E53935);
}

.load-more-btn {
  width: 100%;
  padding: 14px;
  margin-top: 14px;
  background: var(--xm-bg-elevated, #1A1A1A);
  border: none;
  border-radius: var(--neu-radius-md, 12px);
  color: var(--xm-text-primary, #fff);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -2px -2px 4px var(--neu-shadow-light, rgba(255, 255, 255, 0.03));
  transition: all 0.15s ease;
}

.load-more-btn:active {
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -1px -1px 2px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
}

.load-more-btn:disabled {
  opacity: 0.5;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 36px;
  color: var(--xm-text-muted, #888);
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--xm-bg-surface, #222);
  border-top-color: var(--xm-accent, #E53935);
  border-radius: var(--neu-radius-full, 9999px);
  animation: spin 1s linear infinite;
  margin-bottom: 14px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 36px 16px;
  color: var(--xm-text-muted, #888);
}

/* User Cards */
.user-card {
  text-align: center;
}

.user-avatar {
  width: 110px;
  height: 110px;
  border-radius: var(--neu-radius-full, 9999px);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 10px;
  box-shadow: 
    6px 6px 12px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -3px -3px 6px var(--neu-shadow-light, rgba(255, 255, 255, 0.03));
}

.avatar-letter {
  font-size: 44px;
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

/* User Profile View */
.user-profile-view {
  padding: 0 16px;
}

.user-profile-header {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 18px 0;
  border-bottom: 1px solid var(--xm-bg-surface, #222);
  margin-bottom: 18px;
}

.back-btn {
  width: 44px;
  height: 44px;
  border-radius: var(--neu-radius-full, 9999px);
  border: none;
  background: var(--xm-bg-elevated, #1A1A1A);
  color: var(--xm-text-primary, #fff);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -2px -2px 4px var(--neu-shadow-light, rgba(255, 255, 255, 0.03));
  transition: all 0.15s ease;
}

.back-btn:active {
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -1px -1px 2px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
}

.user-avatar-large {
  width: 68px;
  height: 68px;
  border-radius: var(--neu-radius-full, 9999px);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -2px -2px 4px var(--neu-shadow-light, rgba(255, 255, 255, 0.03));
}

.avatar-letter-large {
  font-size: 30px;
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.user-profile-info {
  flex: 1;
  min-width: 0;
}

.user-profile-info h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--xm-text-primary, #fff);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-profile-info p {
  font-size: 13px;
  color: var(--xm-text-muted, #888);
  margin: 3px 0 0;
}

.user-stats {
  font-size: 12px !important;
  color: var(--xm-text-muted, #888) !important;
}

.user-tracks-list {
  padding-bottom: 20px;
}
</style>
