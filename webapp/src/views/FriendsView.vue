<template>
  <div class="friends-view">
    <!-- No channel - show setup prompt -->
    <div v-if="!authStore.hasChannel" class="no-channel-prompt">
      <div class="prompt-icon"><Users :size="48" /></div>
      <h2>Кенты</h2>
      <p>Подключите Telegram-канал, чтобы находить друзей и подписываться на их музыку</p>
      <button class="setup-btn" @click="goToChannelSetup">
        Подключить канал
      </button>
    </div>

    <!-- Has channel - show friends -->
    <template v-else>
    <!-- Tab switcher -->
    <div class="tabs-header">
      <button 
        class="tab-btn" 
        :class="{ active: activeTab === 'following' }"
        @click="activeTab = 'following'"
      >
        Подписки
      </button>
      <button 
        class="tab-btn" 
        :class="{ active: activeTab === 'followers' }"
        @click="activeTab = 'followers'"
      >
        Подписчики
      </button>
      <button 
        v-if="canUseSocial"
        class="tab-btn" 
        :class="{ active: activeTab === 'search' }"
        @click="activeTab = 'search'"
      >
        <Search :size="18" />
      </button>
    </div>

    <!-- Following Tab -->
    <div v-show="activeTab === 'following'" class="tab-content">
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
      </div>

      <div v-else-if="following.length === 0" class="empty-state">
        <span class="empty-icon"><Users :size="48" /></span>
        <p>Вы пока ни на кого не подписаны</p>
        <button v-if="canUseSocial" class="action-btn" @click="activeTab = 'search'">
          Найти друзей
        </button>
        <p v-else class="hint">Подключите канал для поиска друзей</p>
      </div>

      <div v-else class="users-list">
        <div 
          v-for="user in following" 
          :key="user.id"
          class="user-card"
          @click="viewUserProfile(user)"
        >
          <div class="user-avatar">
            {{ getInitials(user) }}
          </div>
          <div class="user-info">
            <div class="user-name">{{ user.display_name }}</div>
            <div class="user-meta">
              {{ user.track_count }} треков • {{ user.playlist_count }} плейлистов
            </div>
          </div>
          <button 
            class="unfollow-btn" 
            @click.stop="unfollowUser(user)"
          >
            <Check :size="14" /> Подписан
          </button>
        </div>
      </div>
    </div>

    <!-- Followers Tab -->
    <div v-show="activeTab === 'followers'" class="tab-content">
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
      </div>

      <div v-else-if="followers.length === 0" class="empty-state">
        <span class="empty-icon"><User :size="48" /></span>
        <p>Пока никто не подписался на вас</p>
      </div>

      <div v-else class="users-list">
        <div 
          v-for="user in followers" 
          :key="user.id"
          class="user-card"
          @click="viewUserProfile(user)"
        >
          <div class="user-avatar">
            {{ getInitials(user) }}
          </div>
          <div class="user-info">
            <div class="user-name">{{ user.display_name }}</div>
            <div class="user-meta">
              {{ user.track_count }} треков • {{ user.playlist_count }} плейлистов
            </div>
          </div>
          <button 
            v-if="!user.is_following"
            class="follow-btn" 
            @click.stop="followUser(user)"
          >
            Подписаться
          </button>
          <button 
            v-else
            class="unfollow-btn" 
            @click.stop="unfollowUser(user)"
          >
            <Check :size="14" /> Подписан
          </button>
        </div>
      </div>
    </div>

    <!-- Search Tab -->
    <div v-show="activeTab === 'search'" class="tab-content">
      <SearchBar
        v-model="searchQuery"
        placeholder="Поиск по имени или @username"
        @input="debouncedSearch"
      />

      <div v-if="searching" class="loading">
        <div class="spinner"></div>
      </div>

      <div v-else-if="searchQuery && searchResults.length === 0" class="empty-state">
        <span class="empty-icon"><Search :size="48" /></span>
        <p>Никого не найдено</p>
      </div>

      <div v-else-if="searchResults.length" class="users-list">
        <div 
          v-for="user in searchResults" 
          :key="user.id"
          class="user-card"
          @click="viewUserProfile(user)"
        >
          <div class="user-avatar">
            {{ getInitials(user) }}
          </div>
          <div class="user-info">
            <div class="user-name">{{ user.display_name }}</div>
            <div class="user-meta">
              <span v-if="user.username">@{{ user.username }}</span>
              <span v-else>{{ user.track_count }} треков</span>
            </div>
          </div>
          <button 
            v-if="!user.is_following"
            class="follow-btn" 
            @click.stop="followUser(user)"
          >
            Подписаться
          </button>
          <button 
            v-else
            class="unfollow-btn" 
            @click.stop="unfollowUser(user)"
          >
            <Check :size="14" /> Подписан
          </button>
        </div>
      </div>

      <div v-else-if="!searchQuery" class="search-hint">
        <span class="hint-icon"><Lightbulb :size="24" /></span>
        <p>Введите имя или username друга</p>
      </div>
    </div>

    <!-- User Profile Modal -->
    <div v-if="selectedUser" class="modal-overlay" @click.self="closeProfile">
      <div class="profile-modal">
        <div class="profile-header">
          <div class="profile-avatar">
            {{ getInitials(selectedUser) }}
          </div>
          <div class="profile-info">
            <h2>{{ selectedUser.display_name }}</h2>
            <p v-if="selectedUser.username">@{{ selectedUser.username }}</p>
          </div>
          <button class="close-btn" @click="closeProfile"><X :size="20" /></button>
        </div>

        <div class="profile-stats">
          <div class="stat">
            <span class="stat-value">{{ selectedUser.track_count }}</span>
            <span class="stat-label">треков</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ selectedUser.playlist_count }}</span>
            <span class="stat-label">плейлистов</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ selectedUser.followers_count }}</span>
            <span class="stat-label">подписчиков</span>
          </div>
        </div>

        <div class="profile-actions">
          <button 
            v-if="!selectedUser.is_following"
            class="action-btn primary"
            @click="followUser(selectedUser)"
          >
            Подписаться
          </button>
          <button 
            v-else
            class="action-btn secondary"
            @click="unfollowUser(selectedUser)"
          >
            Отписаться
          </button>
        </div>

        <div class="profile-content">
          <!-- Tabs for user content -->
          <div class="content-tabs">
            <button 
              :class="{ active: profileTab === 'library' }"
              @click="profileTab = 'library'; loadUserLibrary()"
            >
              <Music :size="16" /> Библиотека
            </button>
            <button 
              :class="{ active: profileTab === 'playlists' }"
              @click="profileTab = 'playlists'; loadUserPlaylists()"
            >
              <Folder :size="16" /> Плейлисты
            </button>
            <button 
              :class="{ active: profileTab === 'albums' }"
              @click="profileTab = 'albums'; loadUserAlbums()"
            >
              <Disc3 :size="16" /> Альбомы
            </button>
          </div>

          <div v-if="loadingUserContent" class="loading">
            <div class="spinner"></div>
          </div>

          <!-- Library tracks -->
          <div v-else-if="profileTab === 'library'" class="tracks-list">
            <div 
              v-for="track in userTracks" 
              :key="track.id"
              class="track-item"
              @click="playTrack(track)"
            >
              <div class="track-cover">
                <img v-if="track.cover_url" :src="track.cover_url" />
                <span v-else><Music :size="20" /></span>
              </div>
              <div class="track-info">
                <div class="track-title">{{ track.title || 'Без названия' }}</div>
                <div class="track-artist">{{ track.artist || 'Неизвестен' }}</div>
              </div>
            </div>
            <p v-if="userTracks.length === 0" class="empty-hint">Нет треков</p>
          </div>

          <!-- Playlists -->
          <div v-else-if="profileTab === 'playlists'" class="playlists-list">
            <div 
              v-for="playlist in userPlaylists" 
              :key="playlist.id"
              class="playlist-item"
              @click="$router.push(`/playlist/${playlist.id}`); closeProfile()"
            >
              <div class="playlist-icon"><Folder :size="20" /></div>
              <div class="playlist-info">
                <div class="playlist-name">{{ playlist.name }}</div>
                <div class="playlist-meta">{{ playlist.track_count }} треков</div>
              </div>
            </div>
            <p v-if="userPlaylists.length === 0" class="empty-hint">Нет публичных плейлистов</p>
          </div>

          <!-- Albums -->
          <div v-else-if="profileTab === 'albums'" class="albums-grid-small">
            <div 
              v-for="album in userAlbums" 
              :key="album.id"
              class="album-item"
              @click="$router.push(`/album/${album.id}`); closeProfile()"
              @contextmenu.prevent="handleAlbumContextMenu(album, $event)"
            >
              <img v-if="album.cover_url" :src="album.cover_url" />
              <div v-else class="album-placeholder"><Disc3 :size="24" /></div>
              <div class="album-name">{{ album.name }}</div>
            </div>
            <p v-if="userAlbums.length === 0" class="empty-hint">Нет альбомов</p>
          </div>
        </div>
      </div>
    </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useAuthStore } from '@/stores/auth'
import { useContextMenu } from '@/composables/useContextMenu'
import api from '@/api/client'
import SearchBar from '@/components/ui/SearchBar.vue'
import { Users, User, Search, Check, X, Music, Folder, Disc3, Lightbulb } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const playerStore = usePlayerStore()
const authStore = useAuthStore()

// Context menu
const { openMenu } = useContextMenu()

const handleAlbumContextMenu = (album, event) => {
  openMenu('album', album, 'friend', event)
}

// Navigate to channel setup
const goToChannelSetup = () => {
  router.push({ name: 'settings', query: { section: 'channel' } })
}

// Check if user can use social features
const canUseSocial = computed(() => authStore.hasChannel)

// Tab state
const activeTab = ref('following')

// Data
const following = ref([])
const followers = ref([])
const searchResults = ref([])
const loading = ref(false)
const searching = ref(false)
const searchQuery = ref('')

// Selected user profile
const selectedUser = ref(null)
const profileTab = ref('library')
const loadingUserContent = ref(false)
const userTracks = ref([])
const userPlaylists = ref([])
const userAlbums = ref([])

// Debounce timer
let searchTimer = null

const getInitials = (user) => {
  if (user.first_name) {
    return user.first_name.charAt(0).toUpperCase()
  }
  if (user.username) {
    return user.username.charAt(0).toUpperCase()
  }
  return '?'
}

const loadFollowing = async () => {
  loading.value = true
  try {
    const response = await api.get('/social/following')
    following.value = response.data.items || []
  } catch (error) {
    console.error('Failed to load following:', error)
  } finally {
    loading.value = false
  }
}

const loadFollowers = async () => {
  loading.value = true
  try {
    const response = await api.get('/social/followers')
    followers.value = response.data.items || []
  } catch (error) {
    console.error('Failed to load followers:', error)
  } finally {
    loading.value = false
  }
}

const debouncedSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(searchUsers, 300)
}

const searchUsers = async () => {
  if (!searchQuery.value || searchQuery.value.length < 2) {
    searchResults.value = []
    return
  }
  
  searching.value = true
  try {
    const response = await api.get('/social/search', {
      params: { q: searchQuery.value }
    })
    searchResults.value = response.data.items || []
  } catch (error) {
    console.error('Search failed:', error)
  } finally {
    searching.value = false
  }
}

const followUser = async (user) => {
  if (!canUseSocial.value) {
    authStore.promptChannelSetup()
    return
  }
  try {
    await api.post('/social/follow', { user_id: user.id })
    user.is_following = true
    // Add to following list if not there
    if (!following.value.find(u => u.id === user.id)) {
      following.value.unshift(user)
    }
  } catch (error) {
    if (error.response?.status === 403) {
      authStore.promptChannelSetup()
    } else {
      console.error('Failed to follow:', error)
    }
  }
}

const unfollowUser = async (user) => {
  if (!canUseSocial.value) {
    authStore.promptChannelSetup()
    return
  }
  try {
    await api.post('/social/unfollow', { user_id: user.id })
    user.is_following = false
    // Remove from following list
    following.value = following.value.filter(u => u.id !== user.id)
  } catch (error) {
    if (error.response?.status === 403) {
      authStore.promptChannelSetup()
    } else {
      console.error('Failed to unfollow:', error)
    }
  }
}

const viewUserProfile = async (user) => {
  selectedUser.value = user
  profileTab.value = 'library'
  loadUserLibrary()
}

const closeProfile = () => {
  selectedUser.value = null
  userTracks.value = []
  userPlaylists.value = []
  userAlbums.value = []
}

const loadUserLibrary = async () => {
  if (!selectedUser.value) return
  loadingUserContent.value = true
  try {
    const response = await api.get(`/social/user/${selectedUser.value.id}/library`, {
      params: { per_page: 20 }
    })
    userTracks.value = response.data.items || []
  } catch (error) {
    console.error('Failed to load user library:', error)
  } finally {
    loadingUserContent.value = false
  }
}

const loadUserPlaylists = async () => {
  if (!selectedUser.value) return
  loadingUserContent.value = true
  try {
    const response = await api.get(`/playlists/user/${selectedUser.value.id}`)
    userPlaylists.value = response.data.items || []
  } catch (error) {
    console.error('Failed to load user playlists:', error)
  } finally {
    loadingUserContent.value = false
  }
}

const loadUserAlbums = async () => {
  if (!selectedUser.value) return
  loadingUserContent.value = true
  try {
    const response = await api.get(`/social/user/${selectedUser.value.id}/albums`, {
      params: { per_page: 20 }
    })
    userAlbums.value = response.data.items || []
  } catch (error) {
    console.error('Failed to load user albums:', error)
  } finally {
    loadingUserContent.value = false
  }
}

const playTrack = (track) => {
  playerStore.playTrack(track, userTracks.value)
}

// Load user by ID (for direct navigation from NowPlayingSidebar)
const loadUserById = async (userId) => {
  try {
    const response = await api.get(`/social/user/${userId}`)
    if (response.data) {
      selectedUser.value = response.data
      profileTab.value = 'library'
      loadUserLibrary()
    }
  } catch (error) {
    console.error('Failed to load user:', error)
  }
}

// Load data on tab change
watch(activeTab, (tab) => {
  if (tab === 'following') {
    loadFollowing()
  } else if (tab === 'followers') {
    loadFollowers()
  }
})

onMounted(() => {
  loadFollowing()
  
  // Check if we need to open a user profile from query params
  if (route.query.viewUser) {
    loadUserById(route.query.viewUser)
    // Clear the query param
    router.replace({ name: 'friends' })
  }
  
  // Слушаем событие сброса состояния
  window.addEventListener('reset-view-state', handleResetState)
})

onUnmounted(() => {
  window.removeEventListener('reset-view-state', handleResetState)
})

// Обработчик сброса состояния
const handleResetState = (event) => {
  if (event.detail.route === '/friends') {
    // Сбрасываем на вкладку "Подписки"
    activeTab.value = 'following'
    // Сбрасываем поиск
    searchQuery.value = ''
    searchResults.value = []
    // Перезагружаем данные
    loadFollowing()
  }
}
</script>

<style scoped>
.friends-view {
  padding: 16px;
}

.tabs-header {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  padding: 4px;
  background: var(--c-bg-0);
  border-radius: var(--r-md);
  box-shadow:
    inset 2px 2px 4px var(--sh-inset-dark),
    inset -1px -1px 3px var(--sh-inset-light);
}

.tab-btn {
  flex: 1;
  padding: 10px 14px;
  background: transparent;
  border: none;
  border-radius: calc(var(--r-md) - 2px);
  color: var(--c-text-2);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.tab-btn:hover {
  color: var(--c-text-1);
}

.tab-btn.active {
  background: var(--c-bg-2);
  color: var(--c-text-1);
  font-weight: 600;
  box-shadow:
    2px 2px 4px var(--sh-dark),
    -1px -1px 2px var(--sh-light);
}

/* Search - neumorphic inset style */
/* Removed old search-box styles */

.search-hint {
  text-align: center;
  padding: 48px 24px;
  color: var(--text-secondary);
}

.hint-icon {
  font-size: 32px;
  display: block;
  margin-bottom: 12px;
}

/* Users list */
.users-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-elevated);
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.user-card:active {
  background: var(--bg-highlight);
}

.user-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  color: #fff;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 15px;
}

.user-meta {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.follow-btn, .unfollow-btn {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  cursor: pointer;
}

.follow-btn {
  background: var(--accent);
  color: #000;
}

.unfollow-btn {
  background: var(--bg-highlight);
  color: var(--text-secondary);
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.action-btn {
  margin-top: 16px;
  background: var(--accent);
  color: #000;
  border: none;
  border-radius: 20px;
  padding: 12px 24px;
  font-weight: 600;
  cursor: pointer;
}

/* Profile Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1000;
}

.profile-modal {
  background: var(--bg-secondary);
  border-radius: 24px 24px 0 0;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  padding-bottom: 16px;
}

.profile-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  color: #fff;
}

.profile-info {
  flex: 1;
}

.profile-info h2 {
  margin: 0;
  font-size: 20px;
  color: var(--text-primary);
}

.profile-info p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.close-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--bg-elevated);
  border: none;
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
}

.profile-stats {
  display: flex;
  justify-content: space-around;
  padding: 16px 24px;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.profile-actions {
  padding: 16px 24px;
  display: flex;
  gap: 12px;
}

.action-btn.primary {
  flex: 1;
  background: var(--accent);
  color: #000;
}

.action-btn.secondary {
  flex: 1;
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.profile-content {
  padding: 0 16px 24px;
}

.content-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  overflow-x: auto;
}

.content-tabs button {
  padding: 8px 16px;
  background: var(--bg-elevated);
  border: none;
  border-radius: 20px;
  color: var(--text-secondary);
  font-size: 13px;
  white-space: nowrap;
  cursor: pointer;
}

.content-tabs button.active {
  background: var(--accent);
  color: #000;
}

/* Tracks list */
.tracks-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.track-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background: var(--bg-elevated);
  border-radius: 10px;
  cursor: pointer;
}

.track-cover {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  background: var(--bg-highlight);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.track-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.track-info {
  flex: 1;
  min-width: 0;
}

.track-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.track-artist {
  font-size: 12px;
  color: var(--text-secondary);
}

/* Playlists list */
.playlists-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.playlist-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-elevated);
  border-radius: 10px;
  cursor: pointer;
}

.playlist-icon {
  font-size: 24px;
}

.playlist-info {
  flex: 1;
}

.playlist-name {
  font-weight: 500;
  color: var(--text-primary);
}

.playlist-meta {
  font-size: 12px;
  color: var(--text-secondary);
}

/* Albums grid small */
.albums-grid-small {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.album-item {
  cursor: pointer;
}

.album-item img,
.album-placeholder {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  object-fit: cover;
  background: var(--bg-elevated);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
}

.album-item .album-name {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-hint {
  text-align: center;
  color: var(--text-tertiary);
  padding: 24px;
  font-size: 14px;
}

/* Loading */
.loading {
  display: flex;
  justify-content: center;
  padding: 24px;
}


/* No channel prompt */
.no-channel-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  padding: 32px 24px;
}

.no-channel-prompt .prompt-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.no-channel-prompt h2 {
  color: var(--text-primary);
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 12px 0;
}

.no-channel-prompt p {
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.5;
  margin: 0 0 24px 0;
  max-width: 300px;
}

.no-channel-prompt .setup-btn {
  background: linear-gradient(135deg, var(--accent) 0%, #00c853 100%);
  border: none;
  border-radius: 24px;
  color: #000;
  font-size: 16px;
  font-weight: 600;
  padding: 14px 32px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.no-channel-prompt .setup-btn:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 16px rgba(0, 230, 118, 0.3);
}
.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--bg-highlight);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
