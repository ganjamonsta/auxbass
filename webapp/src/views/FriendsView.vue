<template>
  <div class="friends-view">
    <!-- No channel - show setup prompt -->
    <div v-if="!authStore.hasChannel" class="no-channel-prompt">
      <div class="prompt-icon"><Users :size="48" /></div>
      <h2>Подписки</h2>
      <p>Подключите Telegram-канал, чтобы находить друзей и подписываться на их музыку</p>
      <button class="setup-btn" @click="goToChannelSetup">
        Подключить канал
      </button>
    </div>

    <!-- Has channel - show friends hub -->
    <template v-else>
      <!-- My Profile banner -->
      <div v-if="authStore.user" class="my-profile-banner" @click="router.push(`/user/${authStore.user.id}`)">
        <div class="user-avatar my-avatar">
          <img v-if="authStore.userAvatarUrl" :src="authStore.userAvatarUrl" class="card-avatar-img" alt="Avatar" />
          <template v-else>{{ getInitials(authStore.user) }}</template>
        </div>
        <div class="user-info">
          <div class="user-name">
            {{ authStore.userDisplayName }}
            <span class="self-badge">Вы</span>
          </div>
          <div class="user-meta">
            <span v-if="authStore.user.username">@{{ authStore.user.username }} • </span>
            <span>Мой публичный профиль</span>
          </div>
        </div>
        <div class="my-profile-arrow">
          <ChevronRight :size="20" />
        </div>
      </div>

      <!-- Unified Tab switcher -->
      <div class="neu-tab-bar friends-tabs">
        <button 
          class="neu-tab" 
          :class="{ active: activeTab === 'feed' }"
          @click="activeTab = 'feed'"
        >
          <Flame :size="15" />
          <span class="neu-tab-content" data-text="Лента">Лента</span>
        </button>

        <button 
          class="neu-tab" 
          :class="{ active: activeTab === 'following' }"
          @click="activeTab = 'following'"
        >
          <Users :size="15" />
          <span class="neu-tab-content" data-text="Подписки">
            Подписки
            <span v-if="following.length" class="tab-badge">{{ following.length }}</span>
          </span>
        </button>

        <button 
          class="neu-tab" 
          :class="{ active: activeTab === 'followers' }"
          @click="activeTab = 'followers'"
        >
          <User :size="15" />
          <span class="neu-tab-content" data-text="Подписчики">
            Подписчики
            <span v-if="followers.length" class="tab-badge">{{ followers.length }}</span>
          </span>
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

      <!-- Tab 1: Activity Feed -->
      <div v-show="activeTab === 'feed'" class="tab-content">
        <SocialFeed @navigate-tab="handleNavigateTab" />
      </div>

      <!-- Tab 2: Following List -->
      <div v-show="activeTab === 'following'" class="tab-content">
        <!-- Local search filter for friends -->
        <div v-if="following.length > 3" class="friends-filter-bar">
          <SearchBar
            v-model="followingSearch"
            placeholder="Фильтр по имени или @username..."
          />
        </div>

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

        <div v-else-if="filteredFollowing.length === 0" class="empty-state">
          <span class="empty-icon"><Search :size="40" /></span>
          <p>Друзей с таким именем не найдено</p>
        </div>

        <div v-else class="users-grid">
          <div 
            v-for="user in filteredFollowing" 
            :key="user.id"
            class="user-card"
            @click="viewUserProfile(user)"
          >
            <div class="user-card-main">
              <div class="user-avatar">
                <img v-if="getUserAvatar(user)" :src="getUserAvatar(user)" class="card-avatar-img" alt="Avatar" />
                <template v-else>{{ getInitials(user) }}</template>
              </div>
              <div class="user-info">
                <div class="user-name-line">
                  <span class="user-name">{{ user.display_name }}</span>
                  <span v-if="user.username" class="user-handle">@{{ user.username }}</span>
                </div>
                <div class="user-stats-row">
                  <span class="user-stat-chip">{{ user.track_count }} {{ getTracksWord(user.track_count) }}</span>
                  <span v-if="user.playlist_count" class="stat-dot">•</span>
                  <span v-if="user.playlist_count" class="user-stat-chip">{{ user.playlist_count }} плейл.</span>
                  <span v-if="user.followers_count" class="stat-dot">•</span>
                  <span v-if="user.followers_count" class="user-stat-chip">{{ user.followers_count }} подп.</span>
                </div>
              </div>
            </div>

            <!-- Card Actions -->
            <div class="user-card-actions">
              <!-- Quick Play Library -->
              <button 
                v-if="user.track_count > 0"
                class="btn-user-listen"
                @click.stop="handlePlayUserTracks(user)"
                title="Слушать медиатеку пользователя"
              >
                <Play :size="14" fill="currentColor" />
                <span>Слушать</span>
              </button>

              <!-- Unfollow Button -->
              <button 
                class="btn-unfollow" 
                @click.stop="unfollowUser(user)"
                title="Отписаться"
              >
                <Check :size="14" />
                <span>Подписан</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab 3: Followers List -->
      <div v-show="activeTab === 'followers'" class="tab-content">
        <!-- Local search filter for followers -->
        <div v-if="followers.length > 3" class="friends-filter-bar">
          <SearchBar
            v-model="followersSearch"
            placeholder="Фильтр подписчиков..."
          />
        </div>

        <div v-if="loading" class="loading">
          <div class="spinner"></div>
        </div>

        <div v-else-if="followers.length === 0" class="empty-state">
          <span class="empty-icon"><User :size="48" /></span>
          <p>Пока никто не подписался на вас</p>
        </div>

        <div v-else-if="filteredFollowers.length === 0" class="empty-state">
          <span class="empty-icon"><Search :size="40" /></span>
          <p>Подписчиков с таким именем не найдено</p>
        </div>

        <div v-else class="users-grid">
          <div 
            v-for="user in filteredFollowers" 
            :key="user.id"
            class="user-card"
            @click="viewUserProfile(user)"
          >
            <div class="user-card-main">
              <div class="user-avatar">
                <img v-if="getUserAvatar(user)" :src="getUserAvatar(user)" class="card-avatar-img" alt="Avatar" />
                <template v-else>{{ getInitials(user) }}</template>
              </div>
              <div class="user-info">
                <div class="user-name-line">
                  <span class="user-name">{{ user.display_name }}</span>
                  <span v-if="user.username" class="user-handle">@{{ user.username }}</span>
                </div>
                <div class="user-stats-row">
                  <span class="user-stat-chip">{{ user.track_count }} {{ getTracksWord(user.track_count) }}</span>
                  <span v-if="user.playlist_count" class="stat-dot">•</span>
                  <span v-if="user.playlist_count" class="user-stat-chip">{{ user.playlist_count }} плейл.</span>
                </div>
              </div>
            </div>

            <!-- Card Actions -->
            <div class="user-card-actions">
              <button 
                v-if="user.track_count > 0"
                class="btn-user-listen"
                @click.stop="handlePlayUserTracks(user)"
                title="Слушать медиатеку пользователя"
              >
                <Play :size="14" fill="currentColor" />
                <span>Слушать</span>
              </button>

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
      </div>

      <!-- Tab 4: Search -->
      <div v-show="activeTab === 'search'" class="tab-content">
        <div class="search-section">
          <SearchBar
            v-model="searchQuery"
            placeholder="Поиск по имени или @username..."
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

        <div v-else-if="searchResults.length" class="users-grid">
          <div 
            v-for="user in searchResults" 
            :key="user.id"
            class="user-card"
            @click="viewUserProfile(user)"
          >
            <div class="user-card-main">
              <div class="user-avatar">
                <img v-if="getUserAvatar(user)" :src="getUserAvatar(user)" class="card-avatar-img" alt="Avatar" />
                <template v-else>{{ getInitials(user) }}</template>
              </div>
              <div class="user-info">
                <div class="user-name-line">
                  <span class="user-name">{{ user.display_name }}</span>
                  <span v-if="user.username" class="user-handle">@{{ user.username }}</span>
                </div>
                <div class="user-stats-row">
                  <span class="user-stat-chip">{{ user.track_count }} {{ getTracksWord(user.track_count) }}</span>
                </div>
              </div>
            </div>

            <!-- Card Actions -->
            <div class="user-card-actions">
              <button 
                v-if="user.track_count > 0"
                class="btn-user-listen"
                @click.stop="handlePlayUserTracks(user)"
                title="Слушать медиатеку пользователя"
              >
                <Play :size="14" fill="currentColor" />
                <span>Слушать</span>
              </button>

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

        <div v-else-if="!searchQuery" class="search-hint">
          <span class="hint-icon"><Lightbulb :size="24" /></span>
          <p>Введите имя или username друга для поиска</p>
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
import { socialApi } from '@/api/client'
import SearchBar from '@/components/ui/SearchBar.vue'
import SocialFeed from '@/components/social/SocialFeed.vue'
import { 
  Users, 
  User, 
  Search, 
  Check, 
  Play, 
  Flame, 
  Lightbulb, 
  ChevronRight 
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const playerStore = usePlayerStore()
const authStore = useAuthStore()

// Navigate to channel setup
const goToChannelSetup = () => {
  router.push({ name: 'settings', query: { section: 'channel' } })
}

// Check if user can use social features
const canUseSocial = computed(() => authStore.hasChannel)

// Tab state (default to feed!)
const activeTab = ref(route.query.tab || 'feed')

// Data
const following = ref([])
const followers = ref([])
const searchResults = ref([])
const loading = ref(false)
const searching = ref(false)
const searchQuery = ref('')
const followingSearch = ref('')
const followersSearch = ref('')

// Debounce timer
let searchTimer = null

const filteredFollowing = computed(() => {
  if (!followingSearch.value.trim()) return following.value
  const q = followingSearch.value.toLowerCase().trim()
  return following.value.filter(u => 
    (u.display_name && u.display_name.toLowerCase().includes(q)) ||
    (u.username && u.username.toLowerCase().includes(q))
  )
})

const filteredFollowers = computed(() => {
  if (!followersSearch.value.trim()) return followers.value
  const q = followersSearch.value.toLowerCase().trim()
  return followers.value.filter(u => 
    (u.display_name && u.display_name.toLowerCase().includes(q)) ||
    (u.username && u.username.toLowerCase().includes(q))
  )
})

const getUserAvatar = (user) => {
  if (!user) return null
  if (user.id === authStore.user?.id && authStore.userAvatarUrl) {
    return authStore.userAvatarUrl
  }
  return user.avatar_url || user.custom_avatar_url || user.photo_url || null
}

const getInitials = (user) => {
  if (user?.id === authStore.user?.id && authStore.userDisplayName) {
    return authStore.userDisplayName.charAt(0).toUpperCase()
  }
  if (!user) return '?'
  if (user.custom_nickname) {
    return user.custom_nickname.charAt(0).toUpperCase()
  }
  if (user.display_name) {
    return user.display_name.charAt(0).toUpperCase()
  }
  if (user.first_name) {
    return user.first_name.charAt(0).toUpperCase()
  }
  if (user.username) {
    return user.username.charAt(0).toUpperCase()
  }
  return '?'
}

const getTracksWord = (count) => {
  const n = Math.abs(count) % 100
  const n1 = n % 10
  if (n > 10 && n < 20) return 'треков'
  if (n1 > 1 && n1 < 5) return 'трека'
  if (n1 === 1) return 'трек'
  return 'треков'
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
    following.value = following.value.filter(u => u.id !== user.id)
  } catch (error) {
    if (error.response?.status === 403) {
      authStore.promptChannelSetup()
    } else {
      console.error('Failed to unfollow:', error)
    }
  }
}

const handlePlayUserTracks = async (user) => {
  try {
    const res = await socialApi.getUserLibrary(user.id, { per_page: 50 })
    const tracks = res.data?.items || []
    if (tracks.length > 0) {
      playerStore.playTrack(tracks[0], tracks)
    }
  } catch (e) {
    console.error('Failed to play user tracks:', e)
  }
}

const viewUserProfile = (user) => {
  router.push(`/user/${user.id}`)
}

const handleNavigateTab = (tabName) => {
  activeTab.value = tabName
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
  // Always load following in background so badges & lists are ready
  loadFollowing()
  
  if (route.query.viewUser) {
    router.replace(`/user/${route.query.viewUser}`)
  }
  
  window.addEventListener('reset-view-state', handleResetState)
})

onUnmounted(() => {
  window.removeEventListener('reset-view-state', handleResetState)
})

const handleResetState = (event) => {
  if (event.detail.route === '/friends') {
    activeTab.value = 'feed'
    searchQuery.value = ''
    searchResults.value = []
    followingSearch.value = ''
    followersSearch.value = ''
    loadFollowing()
  }
}
</script>

<style scoped>
.friends-view {
  padding: 16px;
  max-width: 900px;
  margin: 0 auto;
}

/* My profile banner */
.my-profile-banner {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  background: var(--c-bg-2);
  border-radius: var(--r-xl);
  box-shadow: 
    3px 3px 10px var(--sh-dark),
    -2px -2px 5px var(--sh-light);
  border: 1px solid rgba(255, 255, 255, 0.03);
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.my-profile-banner:hover {
  background: var(--c-bg-3);
  transform: translateY(-1px);
}

.my-profile-banner:active {
  transform: scale(0.99);
}

.my-profile-arrow {
  margin-left: auto;
  color: var(--c-text-2);
  display: flex;
  align-items: center;
}

.self-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: var(--r-full);
  background: var(--c-accent);
  color: #fff;
  margin-left: 6px;
  vertical-align: middle;
}

.friends-tabs {
  margin-bottom: 20px;
}

.tab-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  margin-left: 6px;
  font-size: 11px;
  font-weight: 700;
  border-radius: var(--r-full);
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-2);
}

.neu-tab.active .tab-badge {
  background: var(--c-accent);
  color: #fff;
}

.friends-filter-bar {
  margin-bottom: 16px;
}

.search-section {
  margin-bottom: 16px;
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

/* Users Grid */
.users-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  background: var(--c-bg-2);
  border-radius: var(--r-xl);
  box-shadow: 
    3px 3px 8px var(--sh-dark),
    -2px -2px 4px var(--sh-light);
  border: 1px solid rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-card:hover {
  background: var(--c-bg-3);
  border-color: rgba(255, 255, 255, 0.05);
  transform: translateY(-1px);
}

.user-card:active {
  transform: scale(0.99);
}

.user-card-main {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
  flex: 1;
}

.user-avatar {
  width: 48px;
  height: 48px;
  border-radius: var(--r-full);
  background: linear-gradient(135deg, var(--c-accent), #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow: 2px 2px 6px var(--sh-dark);
}

.card-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name-line {
  display: flex;
  align-items: baseline;
  gap: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-name {
  font-weight: 600;
  color: var(--c-text-1);
  font-size: 15px;
}

.user-handle {
  font-size: 13px;
  color: var(--c-text-3);
}

.user-stats-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  font-size: 12px;
  color: var(--c-text-2);
}

.user-stat-chip {
  color: var(--c-text-2);
}

.stat-dot {
  color: var(--c-text-3);
  font-size: 10px;
}

/* User Card Actions */
.user-card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.btn-user-listen {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 12px;
  border-radius: var(--r-full);
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.25);
  color: var(--c-accent);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-user-listen:hover {
  background: var(--c-accent);
  color: #fff;
  transform: translateY(-1px);
}

.btn-user-listen:active {
  transform: scale(0.96);
}

.btn-follow {
  padding: 7px 16px;
  border-radius: var(--r-full);
  background: var(--c-accent);
  border: none;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-follow:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-unfollow {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 14px;
  border-radius: var(--r-full);
  background: var(--c-bg-3);
  border: 1px solid rgba(255, 255, 255, 0.05);
  color: var(--c-text-2);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-unfollow:hover {
  background: var(--c-bg-4);
  color: var(--c-text-1);
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

.loading {
  display: flex;
  justify-content: center;
  padding: 32px;
}

/* No channel prompt */
.no-channel-prompt {
  text-align: center;
  padding: 64px 24px;
  background: var(--c-bg-2);
  border-radius: var(--r-xl);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.prompt-icon {
  color: var(--c-accent);
  margin-bottom: 16px;
}

.setup-btn {
  margin-top: 16px;
  padding: 10px 24px;
  border-radius: var(--r-full);
  background: var(--c-accent);
  color: #fff;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
</style>
