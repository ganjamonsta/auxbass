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
      <!-- Compact Spotify-style Profile Hero -->
      <div class="profile-hero-card">
        <div class="hero-ambient-glow" :style="ambientGlowStyle"></div>

        <div class="hero-content">
          <!-- Avatar -->
          <div class="hero-avatar" :style="avatarGradientStyle">
            <span>{{ getInitials(user) }}</span>
          </div>

          <!-- Meta Info -->
          <div class="hero-meta">
            <div class="hero-title-row">
              <h1 class="hero-name">{{ user.display_name }}</h1>
              <span v-if="isSelf" class="self-badge">Вы</span>
            </div>
            <div v-if="user.username" class="hero-handle">@{{ user.username }}</div>

            <!-- Stats Bar -->
            <div class="hero-stats-row">
              <button class="hero-stat-pill" @click="activeTab = 'tracks'" title="Смотреть треки">
                <span class="stat-num">{{ user.track_count }}</span>
                <span class="stat-label">{{ getTracksWord(user.track_count) }}</span>
              </button>
              <span class="stat-separator">•</span>
              <button class="hero-stat-pill" @click="activeTab = 'playlists'" title="Смотреть плейлисты">
                <span class="stat-num">{{ user.playlist_count }}</span>
                <span class="stat-label">{{ getPlaylistsWord(user.playlist_count) }}</span>
              </button>
              <span class="stat-separator">•</span>
              <div 
                class="hero-stat-pill"
                :class="{ 'clickable-stat': isSelf }"
                @click="isSelf && router.push('/friends')"
                :title="isSelf ? 'Перейти к кентам' : ''"
              >
                <span class="stat-num">{{ user.followers_count }}</span>
                <span class="stat-label">подписчиков</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Buttons Bar -->
        <div class="hero-actions-bar">
          <!-- Play library button -->
          <button 
            v-if="user.track_count > 0"
            class="hero-play-btn" 
            @click="handlePlayUserLibrary"
            title="Слушать медиатеку"
          >
            <Play :size="16" fill="currentColor" />
            <span>Слушать</span>
          </button>

          <!-- Shuffle button -->
          <button 
            v-if="user.track_count > 1"
            class="hero-icon-btn" 
            @click="handleShuffleUserLibrary"
            title="Перемешать медиатеку"
          >
            <Shuffle :size="16" />
          </button>

          <!-- Follow button -->
          <button
            v-if="!isSelf"
            class="hero-pill-btn follow-btn"
            :class="{ 'is-following': isFollowing }"
            :disabled="followLoading"
            @click="toggleFollow"
          >
            <Check v-if="isFollowing" :size="16" />
            <UserPlus v-else :size="16" />
            <span>{{ isFollowing ? 'Подписан' : 'Подписаться' }}</span>
          </button>

          <!-- Settings (if self) -->
          <button
            v-if="isSelf"
            class="hero-pill-btn"
            @click="router.push('/settings')"
            title="Настройки аккаунта"
          >
            <Settings :size="16" />
            <span>Настройки</span>
          </button>

          <!-- Share button -->
          <button class="hero-pill-btn share-btn" @click="handleShare" title="Поделиться профилем">
            <Share2 :size="16" />
            <span>Поделиться</span>
          </button>
        </div>
      </div>

      <!-- Tabs -->
      <div class="neu-tab-bar user-tabs">
        <button
          class="neu-tab"
          :class="{ active: activeTab === 'overview' }"
          @click="activeTab = 'overview'"
        >
          <Sparkles :size="15" />
          <span class="neu-tab-content" data-text="Обзор">Обзор</span>
        </button>
        <button
          class="neu-tab"
          :class="{ active: activeTab === 'tracks' }"
          @click="activeTab = 'tracks'"
        >
          <Music :size="15" />
          <span class="neu-tab-content" :data-text="`Треки (${user.track_count})`">
            Треки <span class="tab-count">{{ user.track_count }}</span>
          </span>
        </button>
        <button
          class="neu-tab"
          :class="{ active: activeTab === 'playlists' }"
          @click="activeTab = 'playlists'"
        >
          <Folder :size="15" />
          <span class="neu-tab-content" :data-text="`Плейлисты (${user.playlist_count})`">
            Плейлисты <span class="tab-count">{{ user.playlist_count }}</span>
          </span>
        </button>
        <button
          v-if="overviewAlbums.length > 0 || activeTab === 'albums'"
          class="neu-tab"
          :class="{ active: activeTab === 'albums' }"
          @click="activeTab = 'albums'"
        >
          <Disc3 :size="15" />
          <span class="neu-tab-content" data-text="Альбомы">Альбомы</span>
        </button>
      </div>

      <!-- Overview Tab Content (Home-like strips for Playlists, Albums, and Top Tracks) -->
      <div v-show="activeTab === 'overview'" class="tab-pane overview-pane">
        <!-- Loading overview skeletons -->
        <div v-if="loadingOverview" class="overview-loading">
          <section class="profile-section">
            <div class="section-header">
              <div class="skeleton-section-title"></div>
            </div>
            <div class="horizontal-scroll">
              <div v-for="i in 4" :key="i" class="feed-card-skeleton">
                <div class="skeleton-feed-cover"></div>
                <div class="skeleton-feed-title"></div>
                <div class="skeleton-feed-sub"></div>
              </div>
            </div>
          </section>
        </div>

        <template v-else>
          <!-- Strip 1: Playlists -->
          <section v-if="overviewPlaylists.length > 0" class="profile-section">
            <div class="section-header">
              <h2 class="section-title">Плейлисты</h2>
              <button class="section-link" @click="activeTab = 'playlists'">Все {{ user.playlist_count || overviewPlaylists.length }}</button>
            </div>
            <div class="horizontal-scroll">
              <div 
                v-for="pl in overviewPlaylists.slice(0, 10)" 
                :key="pl.id" 
                class="feed-card"
                @click="goToPlaylist(pl)"
                @contextmenu.prevent="handlePlaylistContextMenu(pl, $event)"
                v-longpress="(e) => handlePlaylistContextMenu(pl, e)"
              >
                <div class="feed-card-cover" :style="getPlaylistCoverStyle(pl)">
                  <img 
                    v-if="pl.covers?.length" 
                    :src="getCoverUrl(pl.covers[0], CoverSize.SMALL)" 
                    alt=""
                    loading="lazy"
                  />
                  <Folder v-else :size="32" />
                  <button 
                    v-if="pl.track_count > 0" 
                    class="play-overlay" 
                    @click.stop="shufflePlaylist(pl)"
                    title="Слушать"
                  >
                    <Play :size="18" fill="currentColor" />
                  </button>
                </div>
                <div class="feed-card-title">{{ pl.name }}</div>
                <div class="feed-card-subtitle">{{ pl.track_count }} {{ getTracksWord(pl.track_count) }}</div>
              </div>
            </div>
          </section>

          <!-- Strip 2: Albums -->
          <section v-if="overviewAlbums.length > 0" class="profile-section">
            <div class="section-header">
              <h2 class="section-title">Альбомы</h2>
              <button class="section-link" @click="activeTab = 'albums'">Все {{ overviewAlbums.length }}</button>
            </div>
            <div class="horizontal-scroll">
              <div 
                v-for="album in overviewAlbums.slice(0, 10)" 
                :key="album.id" 
                class="feed-card"
                @click="goToAlbum(album)"
                @contextmenu.prevent="handleAlbumContextMenu(album, $event)"
                v-longpress="(e) => handleAlbumContextMenu(album, e)"
              >
                <div class="feed-card-cover">
                  <img 
                    v-if="album.cover_url" 
                    :src="getCoverUrl(album.cover_url, CoverSize.SMALL)" 
                    alt=""
                    loading="lazy"
                  />
                  <Disc3 v-else :size="32" />
                  <button 
                    class="play-overlay" 
                    @click.stop="shuffleAlbum(album)"
                    title="Слушать"
                  >
                    <Play :size="18" fill="currentColor" />
                  </button>
                </div>
                <div class="feed-card-title">{{ album.name || album.title }}</div>
                <div class="feed-card-subtitle">{{ album.artist || 'Альбом' }}</div>
              </div>
            </div>
          </section>

          <!-- Section 3: Popular / Top Tracks -->
          <section v-if="overviewTracks.length > 0" class="profile-section">
            <div class="section-header">
              <h2 class="section-title">Треки</h2>
              <button class="section-link" @click="activeTab = 'tracks'">Все {{ user.track_count || overviewTracks.length }}</button>
            </div>
            <div class="profile-tracks-list">
              <TrackItem
                v-for="(track, index) in overviewTracks.slice(0, 5)"
                :key="track.id"
                :track="track"
                :trackNumber="index + 1"
                :isPlaying="playerStore.currentTrack?.id === track.id"
                :isLiked="libraryStore.isTrackLiked(track.id)"
                @click="handleTrackClick(track, index)"
                @like="handleLikeTrack(track)"
                @menu="(e) => handleTrackMenu(track, index, e)"
                @download="handleDirectDownload(track)"
                @addToLibrary="handleAddToLibrary(track)"
              />
            </div>
            <button 
              v-if="(user.track_count || overviewTracks.length) > 5" 
              class="profile-view-more-btn"
              @click="activeTab = 'tracks'"
            >
              <span>Показать все {{ user.track_count }} треков</span>
              <ChevronRight :size="16" />
            </button>
          </section>

          <!-- Empty State if user has no public content -->
          <div v-if="overviewPlaylists.length === 0 && overviewTracks.length === 0 && overviewAlbums.length === 0" class="empty-state">
            <div class="empty-icon"><Music :size="48" /></div>
            <h2>Медиатека пуста</h2>
            <p>У пользователя пока нет публичных треков или плейлистов</p>
          </div>
        </template>
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
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import { useContextMenu } from '@/composables/useContextMenu'
import { useTrackActions, usePlaybackActions, useShare } from '@/composables'
import { socialApi, playlistsApi } from '@/api/client'
import { getCoverUrl, CoverSize } from '@/utils'
import TrackItem from '@/components/TrackItem.vue'
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
  Settings,
  Play,
  Shuffle,
  ChevronRight,
  Sparkles,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const uiStore = useUIStore()
const { openMenu } = useContextMenu()
const { share } = useShare()

// Unified actions
const { handleDirectDownload, handleLikeTrack, handleAddToLibrary } = useTrackActions()
const { playTrack, playQueue } = usePlaybackActions()

const userId = computed(() => {
  const raw = route.params.id
  if (raw === 'me' || !raw) {
    return authStore.user?.id || 0
  }
  const parsed = Number(raw)
  return isNaN(parsed) ? (authStore.user?.id || 0) : parsed
})
const isSelf = computed(() => !!(authStore.user && authStore.user.id === userId.value))

// State
const user = ref(null)
const loading = ref(true)
const error = ref(null)
const isForbidden = ref(false)
const isFollowing = ref(false)
const followLoading = ref(false)
const activeTab = ref('overview')

// Overview data
const overviewTracks = ref([])
const overviewPlaylists = ref([])
const overviewAlbums = ref([])
const loadingOverview = ref(false)

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

const getTracksWord = (count) => {
  const c = count || 0
  const mod10 = c % 10
  const mod100 = c % 100
  if (mod100 >= 11 && mod100 <= 14) return 'треков'
  if (mod10 === 1) return 'трек'
  if (mod10 >= 2 && mod10 <= 4) return 'трека'
  return 'треков'
}

const getPlaylistsWord = (count) => {
  const c = count || 0
  const mod10 = c % 10
  const mod100 = c % 100
  if (mod100 >= 11 && mod100 <= 14) return 'плейлистов'
  if (mod10 === 1) return 'плейлист'
  if (mod10 >= 2 && mod10 <= 4) return 'плейлиста'
  return 'плейлистов'
}

const avatarGradientStyle = computed(() => {
  const str = user.value?.display_name || user.value?.username || 'User'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const h1 = Math.abs(hash % 360)
  const h2 = (h1 + 60) % 360
  return {
    background: `linear-gradient(135deg, hsl(${h1}, 70%, 45%) 0%, hsl(${h2}, 75%, 55%) 100%)`
  }
})

const ambientGlowStyle = computed(() => {
  const str = user.value?.display_name || user.value?.username || 'User'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const h1 = Math.abs(hash % 360)
  return {
    background: `radial-gradient(ellipse at 30% 0%, hsla(${h1}, 75%, 50%, 0.18) 0%, rgba(14, 18, 24, 0) 75%)`
  }
})

const getPlaylistCoverStyle = (playlist) => {
  if (playlist?.covers?.length) return {}
  const str = playlist?.name || 'Playlist'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const h1 = Math.abs(hash % 360)
  const h2 = (h1 + 40) % 360
  return {
    background: `linear-gradient(135deg, hsl(${h1}, 65%, 28%) 0%, hsl(${h2}, 60%, 18%) 100%)`
  }
}

// Load Overview Strips
const loadOverviewData = async (id) => {
  if (!id) return
  loadingOverview.value = true
  try {
    const [tracksRes, playlistsRes, albumsRes] = await Promise.allSettled([
      socialApi.getUserLibrary(id, { page: 1, per_page: 8 }),
      playlistsApi.getUserPlaylists(id),
      socialApi.getUserAlbums(id, { page: 1, per_page: 10 })
    ])

    if (tracksRes.status === 'fulfilled') {
      overviewTracks.value = tracksRes.value.data?.items || (Array.isArray(tracksRes.value.data) ? tracksRes.value.data : [])
    }
    if (playlistsRes.status === 'fulfilled') {
      overviewPlaylists.value = playlistsRes.value.data?.items || (Array.isArray(playlistsRes.value.data) ? playlistsRes.value.data : [])
    }
    if (albumsRes.status === 'fulfilled') {
      overviewAlbums.value = albumsRes.value.data?.items || (Array.isArray(albumsRes.value.data) ? albumsRes.value.data : [])
    }
  } catch (err) {
    console.error('Failed to load overview data:', err)
  } finally {
    loadingOverview.value = false
  }
}

// Fetch user profile
const loadUserProfile = async () => {
  const id = userId.value
  if (!id) {
    if (authStore.loading || !authStore.initialized) return
    error.value = 'Пользователь не найден'
    loading.value = false
    return
  }
  loading.value = true
  error.value = null
  isForbidden.value = false

  try {
    const res = await socialApi.getUser(id)
    user.value = res.data
    isFollowing.value = !!res.data.is_following
    loadOverviewData(id)
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
const handlePlayUserLibrary = async () => {
  if (overviewTracks.value?.length > 0) {
    playQueue(overviewTracks.value, 0)
    uiStore.toast.success('Воспроизведение', `Играет медиатека ${user.value.display_name}`)
  } else {
    try {
      const res = await socialApi.getUserLibrary(userId.value, { page: 1, per_page: 50 })
      const tracks = res.data?.items || []
      if (tracks.length > 0) {
        playQueue(tracks, 0)
        uiStore.toast.success('Воспроизведение', `Играет медиатека ${user.value.display_name}`)
      } else {
        uiStore.toast.info('Пусто', 'У пользователя нет доступных треков')
      }
    } catch (e) {
      console.error('Failed to play user library:', e)
    }
  }
}

const handleShuffleUserLibrary = async () => {
  try {
    const res = await socialApi.getUserLibrary(userId.value, { page: 1, per_page: 100 })
    const tracks = res.data?.items || []
    if (tracks.length > 0) {
      const shuffled = [...tracks].sort(() => Math.random() - 0.5)
      playQueue(shuffled, 0)
      uiStore.toast.success('Перемешивание', `Играет медиатека ${user.value.display_name}`)
    } else {
      uiStore.toast.info('Пусто', 'У пользователя нет доступных треков')
    }
  } catch (e) {
    console.error('Failed to shuffle user library:', e)
  }
}

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
  if (activeTab.value === 'tracks' && virtualTrackListRef.value?.allItems) {
    const items = virtualTrackListRef.value.allItems.filter(Boolean)
    const validIndex = items.findIndex((t) => t.id === track.id)
    playQueue(items, validIndex >= 0 ? validIndex : index)
  } else if (overviewTracks.value?.length) {
    playQueue(overviewTracks.value, index)
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

watch(
  () => authStore.user,
  (newUser) => {
    if (newUser && (!user.value || isSelf.value)) {
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

/* Profile Hero Card */
.profile-hero-card {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  background: var(--c-bg-2, #181818);
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 18px 20px;
  margin-bottom: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

.hero-ambient-glow {
  position: absolute;
  top: -60px;
  left: -40px;
  right: -40px;
  height: 200px;
  pointer-events: none;
  opacity: 0.9;
  filter: blur(20px);
}

.hero-content {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  z-index: 1;
}

.hero-avatar {
  width: 68px;
  height: 68px;
  min-width: 68px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
  border: 2px solid rgba(255, 255, 255, 0.15);
}

.hero-meta {
  flex: 1;
  min-width: 0;
}

.hero-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hero-name {
  font-size: 20px;
  font-weight: 800;
  color: var(--c-text-1, #fff);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.01em;
}

.hero-handle {
  font-size: 13px;
  color: var(--c-accent, #1db954);
  font-weight: 500;
  margin: 2px 0 6px;
}

.hero-stats-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.hero-stat-pill {
  background: none;
  border: none;
  padding: 0;
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  font-size: 12px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  cursor: pointer;
  transition: color 0.15s ease;
}

.hero-stat-pill:hover:not(.no-click) {
  color: var(--c-accent, #1db954);
}

.hero-stat-pill.no-click {
  cursor: default;
}

.hero-stat-pill.clickable-stat {
  cursor: pointer;
}

.stat-num {
  font-weight: 700;
  color: var(--c-text-1, #fff);
  font-size: 13px;
}

.stat-separator {
  color: rgba(255, 255, 255, 0.2);
  font-size: 10px;
}

.self-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--r-full, 9999px);
  background: var(--c-accent, #1db954);
  color: #000;
}

.hero-actions-bar {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  z-index: 1;
}

.hero-play-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  border-radius: 9999px;
  background: var(--c-accent, #1db954);
  color: #000;
  font-weight: 700;
  font-size: 13px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 14px rgba(29, 185, 84, 0.4);
}

.hero-play-btn:hover {
  transform: scale(1.03);
  background: #1ed760;
}

.hero-icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-1, #fff);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.hero-icon-btn:hover {
  background: rgba(255, 255, 255, 0.14);
  transform: scale(1.05);
}

.hero-pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-1, #fff);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.hero-pill-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
}

.hero-pill-btn.follow-btn.is-following {
  background: rgba(255, 255, 255, 0.05);
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
}

.user-tabs {
  margin-bottom: 20px;
}

.tab-count {
  font-size: 11px;
  opacity: 0.7;
  margin-left: 2px;
}

/* Profile Sections (Overview mode) */
.profile-section {
  margin-bottom: 28px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  letter-spacing: -0.01em;
}

.section-link {
  background: none;
  border: none;
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  cursor: pointer;
  transition: color 0.15s ease;
}

.section-link:hover {
  color: var(--c-accent, #1db954);
}

/* Horizontal Scroll */
.horizontal-scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 4px;
}

.horizontal-scroll::-webkit-scrollbar {
  display: none;
}

/* Feed Cards */
.feed-card {
  width: 128px;
  flex-shrink: 0;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.feed-card-cover {
  width: 128px;
  height: 128px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
  position: relative;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.feed-card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.feed-card-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.feed-card-subtitle {
  font-size: 12px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.play-overlay {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--c-accent, #1db954);
  color: #000;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  opacity: 0;
  transform: translateY(6px);
  transition: all 0.2s ease;
}

.feed-card:hover .play-overlay {
  opacity: 1;
  transform: translateY(0);
}

@media (max-width: 768px) {
  .play-overlay {
    opacity: 0.9;
    transform: translateY(0);
    width: 32px;
    height: 32px;
  }
}

/* Skeletons */
.feed-card-skeleton {
  width: 128px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.skeleton-feed-cover {
  width: 128px;
  height: 128px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  margin-bottom: 8px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-feed-title {
  height: 14px;
  width: 80%;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  margin-bottom: 6px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-feed-sub {
  height: 12px;
  width: 50%;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-section-title {
  height: 20px;
  width: 120px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 0.3; }
}

/* Profile Tracks List */
.profile-tracks-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.profile-view-more-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 8px;
}

.profile-view-more-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-1, #fff);
}

.tab-pane {
  min-height: 200px;
}

.btn-pill-secondary {
  padding: 10px 24px;
  border-radius: var(--r-full, 9999px);
  background: var(--c-bg-3, #222);
  color: var(--c-text-1, #fff);
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
}

@media (max-width: 600px) {
  .profile-hero-card {
    padding: 14px 16px;
  }
  .hero-avatar {
    width: 56px;
    height: 56px;
    min-width: 56px;
    font-size: 22px;
  }
  .hero-name {
    font-size: 18px;
  }
  .hero-actions-bar {
    gap: 8px;
  }
  .hero-play-btn {
    padding: 7px 14px;
    font-size: 12px;
  }
  .hero-pill-btn {
    padding: 7px 12px;
    font-size: 12px;
  }
}
</style>
