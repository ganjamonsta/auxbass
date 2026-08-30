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
      <!-- Unified Tab switcher -->
      <div class="neu-tab-bar friends-tabs">
        <button 
          class="neu-tab" 
          :class="{ active: activeTab === 'following' }"
          @click="activeTab = 'following'"
        >
          <span class="neu-tab-content" data-text="Подписки">Подписки</span>
        </button>
        <button 
          class="neu-tab" 
          :class="{ active: activeTab === 'followers' }"
          @click="activeTab = 'followers'"
        >
          <span class="neu-tab-content" data-text="Подписчики">Подписчики</span>
        </button>
        <button 
          v-if="canUseSocial"
          class="neu-tab" 
          :class="{ active: activeTab === 'search' }"
          @click="activeTab = 'search'"
        >
          <Search :size="15" />
          <span class="neu-tab-content" data-text="Поиск">Поиск</span>
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
          <button v-if="canUseSocial" class="btn-pill-primary" @click="activeTab = 'search'">
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
              class="btn-unfollow" 
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
              class="btn-follow" 
              @click.stop="followUser(user)"
            >
              Подписаться
            </button>
            <button 
              v-else
              class="btn-unfollow" 
              @click.stop="unfollowUser(user)"
            >
              <Check :size="14" /> Подписан
            </button>
          </div>
        </div>
      </div>

      <!-- Search Tab -->
      <div v-show="activeTab === 'search'" class="tab-content">
        <div class="search-section">
          <SearchBar
            v-model="searchQuery"
            placeholder="Поиск по имени или @username"
            @input="debouncedSearch"
          />
        </div>

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
              class="btn-follow" 
              @click.stop="followUser(user)"
            >
              Подписаться
            </button>
            <button 
              v-else
              class="btn-unfollow" 
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
              class="btn-pill-primary modal-action-btn"
              @click="followUser(selectedUser)"
            >
              Подписаться
            </button>
            <button 
              v-else
              class="btn-unfollow modal-action-btn"
              @click="unfollowUser(selectedUser)"
            >
              <Check :size="14" /> Подписан
            </button>
          </div>

          <div class="profile-content">
            <!-- Tabs for user content -->
            <div class="neu-tab-bar modal-tabs">
              <button 
                class="neu-tab"
                :class="{ active: profileTab === 'library' }"
                @click="profileTab = 'library'; loadUserLibrary()"
              >
                <Music :size="14" />
                <span class="neu-tab-content" data-text="Библиотека">Библиотека</span>
              </button>
              <button 
                class="neu-tab"
                :class="{ active: profileTab === 'playlists' }"
                @click="profileTab = 'playlists'; loadUserPlaylists()"
              >
                <Folder :size="14" />
                <span class="neu-tab-content" data-text="Плейлисты">Плейлисты</span>
              </button>
              <button 
                class="neu-tab"
                :class="{ active: profileTab === 'albums' }"
                @click="profileTab = 'albums'; loadUserAlbums()"
              >
                <Disc3 :size="14" />
                <span class="neu-tab-content" data-text="Альбомы">Альбомы</span>
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
                class="user-track-row"
                @click="playTrack(track)"
              >
                <div class="track-cover-sm">
                  <img v-if="track.cover_url" :src="getCoverUrl(track.cover_url, CoverSize.SMALL)" />
                  <span v-else><Music :size="18" /></span>
                </div>
                <div class="track-info">
                  <div class="track-title">{{ getDisplayTitle(track) }}</div>
                  <div class="track-artist">{{ getDisplayArtist(track) }}</div>
                </div>
              </div>
              <p v-if="userTracks.length === 0" class="empty-hint">Нет треков</p>
            </div>

            <!-- Playlists -->
            <div v-else-if="profileTab === 'playlists'" class="playlists-list">
              <div 
                v-for="playlist in userPlaylists" 
                :key="playlist.id"
                class="playlist-row"
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
                <img v-if="album.cover_url" :src="getCoverUrl(album.cover_url, CoverSize.SMALL)" />
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
import { getDisplayTitle, getDisplayArtist, getCoverUrl, CoverSize } from '@/utils'
import api, { socialApi } from '@/api/client'
import { useTrackSync } from '@/composables/useTrackSync'
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

// Sync user tracks with global track events
useTrackSync(userTracks)

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
    const response = await socialApi.getFollowing()
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
    const response = await socialApi.getFollowers()
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
    const response = await socialApi.searchUsers(searchQuery.value)
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
    await socialApi.follow(user.id)
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
    await socialApi.unfollow(user.id)
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
    const response = await socialApi.getUserLibrary(selectedUser.value.id, { per_page: 20 })
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
    const response = await socialApi.getUserAlbums(selectedUser.value.id, { per_page: 20 })
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
    const response = await socialApi.getUser(userId)
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

.friends-tabs {
  margin-bottom: 20px;
}

.search-hint {
  text-align: center;
  padding: 48px 24px;
  color: var(--c-text-2);
}

.hint-icon {
  font-size: 32px;
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
  color: var(--c-accent);
}

/* Users list */
.users-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--c-bg-2);
  border-radius: var(--r-lg);
  box-shadow: 
    3px 3px 8px var(--sh-dark),
    -2px -2px 4px var(--sh-light);
  border: 1px solid rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.15s ease;
}

.user-card:hover {
  background: var(--c-bg-3);
}

.user-card:active {
  transform: scale(0.98);
}

.user-avatar {
  width: 44px;
  height: 44px;
  border-radius: var(--r-full);
  background: linear-gradient(135deg, var(--c-accent), #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 2px 2px 6px var(--sh-dark);
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  color: var(--c-text-1);
  font-size: 15px;
}

.user-meta {
  font-size: 13px;
  color: var(--c-text-2);
  margin-top: 2px;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--c-text-2);
}

.empty-icon {
  font-size: 48px;
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
  color: var(--c-text-3);
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
  background: var(--c-bg-2);
  border-radius: var(--r-xl) var(--r-xl) 0 0;
  width: 100%;
  max-width: 560px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 -8px 24px var(--sh-dark);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-bottom: none;
  animation: slideUp 0.25s ease;
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
  width: 60px;
  height: 60px;
  border-radius: var(--r-full);
  background: linear-gradient(135deg, var(--c-accent), #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  box-shadow: 4px 4px 10px var(--sh-dark);
  flex-shrink: 0;
}

.profile-info {
  flex: 1;
}

.profile-info h2 {
  margin: 0;
  font-size: 20px;
  color: var(--c-text-1);
}

.profile-info p {
  margin: 4px 0 0;
  color: var(--c-text-2);
  font-size: 14px;
}

.close-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--r-full);
  background: var(--c-bg-3);
  border: none;
  color: var(--c-text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.close-btn:hover {
  background: var(--c-bg-4);
  color: var(--c-text-1);
}

.profile-stats {
  display: flex;
  justify-content: space-around;
  padding: 16px 24px;
  border-top: 1px solid var(--c-bg-3);
  border-bottom: 1px solid var(--c-bg-3);
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: var(--c-text-1);
}

.stat-label {
  font-size: 12px;
  color: var(--c-text-2);
}

.profile-actions {
  padding: 16px 24px;
  display: flex;
  gap: 12px;
}

.modal-action-btn {
  flex: 1;
}

.profile-content {
  padding: 0 16px 24px;
}

.modal-tabs {
  margin-bottom: 16px;
}

/* Tracks list in modal */
.tracks-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.user-track-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--c-bg-3);
  border-radius: var(--r-md);
  cursor: pointer;
  transition: all 0.15s ease;
}

.user-track-row:hover {
  background: var(--c-bg-4);
}

.track-cover-sm {
  width: 40px;
  height: 40px;
  border-radius: var(--r-sm);
  background: var(--c-bg-4);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.track-cover-sm img {
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
  font-weight: 600;
  color: var(--c-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.track-artist {
  font-size: 12px;
  color: var(--c-text-3);
}

/* Playlists list */
.playlists-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.playlist-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: var(--c-bg-3);
  border-radius: var(--r-md);
  cursor: pointer;
  transition: all 0.15s ease;
}

.playlist-row:hover {
  background: var(--c-bg-4);
}

.playlist-icon {
  color: var(--c-accent);
}

.playlist-info {
  flex: 1;
}

.playlist-name {
  font-weight: 600;
  color: var(--c-text-1);
  font-size: 14px;
}

.playlist-meta {
  font-size: 12px;
  color: var(--c-text-3);
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
  border-radius: var(--r-md);
  object-fit: cover;
  background: var(--c-bg-3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-3);
  box-shadow: 2px 2px 6px var(--sh-dark);
}

.album-item .album-name {
  margin-top: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--c-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-hint {
  text-align: center;
  color: var(--c-text-3);
  padding: 24px;
  font-size: 14px;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 24px;
}
</style>
