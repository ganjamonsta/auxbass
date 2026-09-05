<template>
  <div class="user-profile-view">
    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
    </div>

    <!-- Private / Forbidden Profile -->
    <div v-else-if="isForbidden" class="empty-state private-profile">
      <div class="empty-icon"><Lock :size="56" /></div>
      <h2>Профиль скрыт</h2>
      <p>Пользователь ограничил доступ к своей медиатеке настройками приватности</p>
      <button class="btn-pill-secondary" @click="router.back()">
        Назад
      </button>
    </div>

    <!-- Error / Not Found -->
    <div v-else-if="error || !user" class="empty-state error-profile">
      <div class="empty-icon"><UserX :size="56" /></div>
      <h2>Пользователь не найден</h2>
      <p>{{ error || 'Не удалось загрузить данные пользователя' }}</p>
      <button class="btn-pill-secondary" @click="router.back()">
        Назад
      </button>
    </div>

    <!-- Normal Profile View -->
    <template v-else>
      <!-- Hero Header -->
      <div class="hero-header user-hero">
        <div class="hero-avatar neu-avatar">
          <span>{{ getInitials(user) }}</span>
        </div>
        <div class="hero-info">
          <h1 class="hero-title">{{ user.display_name }}</h1>
          <p v-if="user.username" class="user-handle">@{{ user.username }}</p>
          
          <!-- Stats bar -->
          <div class="profile-stats-bar">
            <div class="stat-badge" @click="activeTab = 'tracks'">
              <span class="stat-num">{{ user.track_count }}</span>
              <span class="stat-desc">треков</span>
            </div>
            <div class="stat-badge" @click="activeTab = 'playlists'">
              <span class="stat-num">{{ user.playlist_count }}</span>
              <span class="stat-desc">плейлистов</span>
            </div>
            <div class="stat-badge">
              <span class="stat-num">{{ user.followers_count }}</span>
              <span class="stat-desc">подписчиков</span>
            </div>
            <div class="stat-badge">
              <span class="stat-num">{{ user.following_count }}</span>
              <span class="stat-desc">подписок</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Action buttons -->
      <div class="profile-actions-bar">
        <button
          v-if="!isSelf"
          class="btn-action follow-btn"
          :class="{ 'is-following': isFollowing }"
          :disabled="followLoading"
          @click="toggleFollow"
        >
          <Check v-if="isFollowing" :size="16" />
          <UserPlus v-else :size="16" />
          <span>{{ isFollowing ? 'Подписан' : 'Подписаться' }}</span>
        </button>

        <button class="btn-action share-btn" @click="handleShare" title="Поделиться профилем">
          <Share2 :size="16" />
          <span>Поделиться</span>
        </button>
      </div>

      <!-- Tabs -->
      <div class="neu-tab-bar user-tabs">
        <button
          class="neu-tab"
          :class="{ active: activeTab === 'tracks' }"
          @click="activeTab = 'tracks'"
        >
          <Music :size="15" />
          <span class="neu-tab-content" data-text="Треки">Треки</span>
        </button>
        <button
          class="neu-tab"
          :class="{ active: activeTab === 'playlists' }"
          @click="activeTab = 'playlists'"
        >
          <Folder :size="15" />
          <span class="neu-tab-content" data-text="Плейлисты">Плейлисты</span>
        </button>
        <button
          class="neu-tab"
          :class="{ active: activeTab === 'albums' }"
          @click="activeTab = 'albums'"
        >
          <Disc3 :size="15" />
          <span class="neu-tab-content" data-text="Альбомы">Альбомы</span>
        </button>
      </div>

      <!-- Tracks Tab Content -->
      <div v-show="activeTab === 'tracks'" class="tab-pane tracks-pane">
        <VirtualTrackList
          ref="virtualTrackListRef"
          :fetchFn="fetchUserTracks"
          :pageSize="50"
          :skeletonCount="12"
          :showAlbum="true"
          :showAddToLibrary="true"
          menuContext="social"
          @click="handleTrackClick"
          @like="handleLikeTrack"
          @menu="handleTrackMenu"
          @download="handleDirectDownload"
          @addToLibrary="handleAddToLibrary"
        >
          <template #empty>
            <span class="empty-icon"><Music :size="48" /></span>
            <p>У пользователя нет треков в библиотеке</p>
          </template>
        </VirtualTrackList>
      </div>

      <!-- Playlists Tab Content -->
      <div v-show="activeTab === 'playlists'" class="tab-pane playlists-pane">
        <VirtualGrid
          ref="playlistsGridRef"
          type="playlist"
          :fetchFn="fetchUserPlaylists"
          :pageSize="30"
          :skeletonCount="8"
          @click="goToPlaylist"
          @play="shufflePlaylist"
          @contextmenu="handlePlaylistContextMenu"
        >
          <template #empty>
            <span class="empty-icon"><Folder :size="48" /></span>
            <p>Нет публичных плейлистов</p>
          </template>
        </VirtualGrid>
      </div>

      <!-- Albums Tab Content -->
      <div v-show="activeTab === 'albums'" class="tab-pane albums-pane">
        <VirtualGrid
          ref="albumsGridRef"
          type="album"
          :fetchFn="fetchUserAlbums"
          :pageSize="30"
          :skeletonCount="8"
          @click="goToAlbum"
          @play="shuffleAlbum"
          @contextmenu="handleAlbumContextMenu"
        >
          <template #empty>
            <span class="empty-icon"><Disc3 :size="48" /></span>
            <p>Нет альбомов в библиотеке</p>
          </template>
        </VirtualGrid>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import { useContextMenu } from '@/composables/useContextMenu'
import { useTrackActions, usePlaybackActions, useShare } from '@/composables'
import { socialApi, playlistsApi } from '@/api/client'
import VirtualTrackList from '@/components/VirtualTrackList.vue'
import VirtualGrid from '@/components/VirtualGrid.vue'
import {
  UserPlus,
  Check,
  Share2,
  Lock,
  UserX,
  Music,
  Folder,
  Disc3,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const playerStore = usePlayerStore()
const { openMenu } = useContextMenu()
const { share } = useShare()

// Unified actions
const { handleDirectDownload, handleLikeTrack, handleAddToLibrary } = useTrackActions()
const { playTrack, playQueue } = usePlaybackActions()

const userId = computed(() => Number(route.params.id))
const isSelf = computed(() => authStore.user && authStore.user.id === userId.value)

// State
const user = ref(null)
const loading = ref(true)
const error = ref(null)
const isForbidden = ref(false)
const isFollowing = ref(false)
const followLoading = ref(false)
const activeTab = ref('tracks')

// Refs
const virtualTrackListRef = ref(null)
const playlistsGridRef = ref(null)
const albumsGridRef = ref(null)

const getInitials = (u) => {
  if (!u) return '?'
  if (u.first_name) return u.first_name.charAt(0).toUpperCase()
  if (u.display_name) return u.display_name.charAt(0).toUpperCase()
  if (u.username) return u.username.charAt(0).toUpperCase()
  return '?'
}

// Fetch user profile
const loadUserProfile = async () => {
  if (!userId.value) return
  loading.value = true
  error.value = null
  isForbidden.value = false

  try {
    const res = await socialApi.getUser(userId.value)
    user.value = res.data
    isFollowing.value = !!res.data.is_following
  } catch (err) {
    if (err.response?.status === 403) {
      isForbidden.value = true
    } else if (err.response?.status === 404) {
      error.value = 'Пользователь не существует'
    } else {
      error.value = 'Ошибка загрузки профиля'
    }
  } finally {
    loading.value = false
  }
}

// Toggle follow / unfollow
const toggleFollow = async () => {
  if (!authStore.hasChannel) {
    authStore.promptChannelSetup()
    return
  }
  if (!user.value || followLoading.value) return

  followLoading.value = true
  try {
    if (isFollowing.value) {
      await socialApi.unfollow(user.value.id)
      isFollowing.value = false
      if (user.value.followers_count > 0) user.value.followers_count--
    } else {
      await socialApi.follow(user.value.id)
      isFollowing.value = true
      user.value.followers_count++
    }
  } catch (err) {
    if (err.response?.status === 403) {
      authStore.promptChannelSetup()
    } else {
      console.error('Failed to toggle follow:', err)
    }
  } finally {
    followLoading.value = false
  }
}

// Share profile
const handleShare = () => {
  if (!user.value) return
  share({
    type: 'user',
    id: user.value.id,
    title: user.value.display_name,
    text: `Посмотри медиатеку ${user.value.display_name} в TG Player!`,
  })
}

// Track actions
const fetchUserTracks = async ({ offset, limit }) => {
  const page = Math.floor(offset / limit) + 1
  try {
    const res = await socialApi.getUserLibrary(userId.value, { page, per_page: limit })
    return {
      items: res.data.items || [],
      total: res.data.total || 0,
    }
  } catch (err) {
    console.error('Failed to fetch user tracks:', err)
    return { items: [], total: 0 }
  }
}

const handleTrackClick = (track, index) => {
  if (virtualTrackListRef.value?.allItems) {
    const items = virtualTrackListRef.value.allItems.filter(Boolean)
    const validIndex = items.findIndex((t) => t.id === track.id)
    playQueue(items, validIndex >= 0 ? validIndex : index)
  } else {
    playTrack(track)
  }
}

const handleTrackMenu = (track, index, event) => {
  openMenu('track', track, 'social', event)
}

// Playlist actions
const fetchUserPlaylists = async ({ offset, limit }) => {
  try {
    const res = await playlistsApi.getUserPlaylists(userId.value)
    const all = res.data.items || []
    return {
      items: all.slice(offset, offset + limit),
      total: all.length,
    }
  } catch (err) {
    console.error('Failed to fetch user playlists:', err)
    return { items: [], total: 0 }
  }
}

const goToPlaylist = (playlist) => {
  router.push(`/playlist/${playlist.id}`)
}

const shufflePlaylist = async (playlist) => {
  await playerStore.playShuffleAll('playlist', playlist.id, playlist.name)
}

const handlePlaylistContextMenu = (playlist, event) => {
  openMenu('playlist', playlist, 'social', event)
}

// Album actions
const fetchUserAlbums = async ({ offset, limit }) => {
  const page = Math.floor(offset / limit) + 1
  try {
    const res = await socialApi.getUserAlbums(userId.value, { page, per_page: limit })
    return {
      items: res.data.items || [],
      total: res.data.total || 0,
    }
  } catch (err) {
    console.error('Failed to fetch user albums:', err)
    return { items: [], total: 0 }
  }
}

const goToAlbum = (album) => {
  router.push(`/album/${album.id}`)
}

const shuffleAlbum = async (album) => {
  await playerStore.playShuffleAll('album', album.id, album.name)
}

const handleAlbumContextMenu = (album, event) => {
  openMenu('album', album, 'social', event)
}

watch(
  () => route.params.id,
  (newId) => {
    if (newId && route.name === 'user-profile') {
      loadUserProfile()
    }
  }
)

onMounted(() => {
  loadUserProfile()
})
</script>

<style scoped>
.user-profile-view {
  padding: 16px;
  max-width: 1000px;
  margin: 0 auto;
  min-height: calc(100vh - 120px);
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 80px 0;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon {
  color: var(--c-accent);
  opacity: 0.8;
  margin-bottom: 8px;
}

.empty-state h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--c-text-1);
}

.empty-state p {
  color: var(--c-text-2);
  font-size: 14px;
  max-width: 320px;
}

/* User Hero Header */
.user-hero {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding: 20px;
  background: var(--c-bg-2);
  border-radius: var(--r-xl);
  box-shadow: 
    4px 4px 12px var(--sh-dark),
    -2px -2px 6px var(--sh-light);
  border: 1px solid rgba(255, 255, 255, 0.03);
}

.hero-avatar {
  width: 80px;
  height: 80px;
  min-width: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--c-accent), #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.hero-info {
  flex: 1;
  min-width: 0;
}

.hero-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0 0 4px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-handle {
  font-size: 14px;
  color: var(--c-accent);
  margin: 0 0 12px 0;
  font-weight: 500;
}

.profile-stats-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.stat-badge {
  display: flex;
  flex-direction: column;
  cursor: pointer;
  user-select: none;
  transition: transform 0.15s ease;
}

.stat-badge:hover {
  transform: translateY(-1px);
}

.stat-num {
  font-size: 16px;
  font-weight: 700;
  color: var(--c-text-1);
}

.stat-desc {
  font-size: 12px;
  color: var(--c-text-2);
}

/* Actions Bar */
.profile-actions-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.btn-action {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: var(--r-full);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.follow-btn {
  background: var(--c-accent);
  color: #fff;
}

.follow-btn.is-following {
  background: var(--c-bg-3);
  color: var(--c-text-1);
  box-shadow: 
    2px 2px 5px var(--sh-dark),
    -1px -1px 3px var(--sh-light);
}

.follow-btn:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.share-btn {
  background: var(--c-bg-2);
  color: var(--c-text-1);
  box-shadow: 
    3px 3px 8px var(--sh-dark),
    -2px -2px 4px var(--sh-light);
  border: 1px solid rgba(255, 255, 255, 0.02);
}

.share-btn:hover {
  background: var(--c-bg-3);
}

.btn-pill-secondary {
  padding: 10px 24px;
  border-radius: var(--r-full);
  background: var(--c-bg-3);
  color: var(--c-text-1);
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
}

.user-tabs {
  margin-bottom: 16px;
}

.tab-pane {
  min-height: 200px;
}

@media (max-width: 600px) {
  .user-hero {
    flex-direction: column;
    text-align: center;
    gap: 14px;
    padding: 16px;
  }
  .hero-avatar {
    width: 72px;
    height: 72px;
    font-size: 28px;
  }
  .profile-stats-bar {
    justify-content: center;
    gap: 12px;
  }
  .profile-actions-bar {
    justify-content: center;
  }
}
</style>
