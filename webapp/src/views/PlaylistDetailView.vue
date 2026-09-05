<template>
  <div class="playlist-detail-view" v-if="playlist">
    <!-- Unified Hero Header -->
    <div class="hero-header">
      <div class="hero-cover playlist-cover">
        <div class="cover-grid" :class="{ 'single-cover': coverImages.length === 1 }" v-if="coverImages.length">
          <img
            v-for="(cover, i) in coverImages"
            :key="i"
            :src="cover"
          />
        </div>
        <div v-else class="cover-placeholder"><Music :size="48" /></div>
      </div>
      <div class="hero-info">
        <h1 class="hero-title">{{ playlist.name }}</h1>
        <p class="hero-meta">
          <span>{{ playlist.track_count }} треков</span>
          <span v-if="playlist.is_public" class="public-badge"><Globe :size="14" /> Публичный</span>
          <span v-if="playlist.owner_name && !isOwner" class="owner-info" :class="{ 'clickable': !!playlist.owner_id }" @click="goToOwner">от {{ playlist.owner_name }}</span>
        </p>
      </div>
    </div>

    <!-- Unified Actions -->
    <div class="hero-actions">
      <div class="action-buttons">
        <button class="action-btn play-btn" @click="playAll" :disabled="!playlist.tracks?.length" title="Слушать все">
          <Play :size="20" fill="currentColor" />
        </button>
        <button class="action-btn shuffle-btn" @click="shufflePlay" :disabled="isShuffling" title="Перемешать">
          <Shuffle :size="18" />
        </button>
        <!-- Edit button for owner -->
        <button v-if="isOwner" class="action-btn edit-btn" @click="openEditModal" title="Редактировать">
          <Edit3 :size="18" />
        </button>
        <!-- Add tracks button for owner -->
        <button v-if="isOwner" class="action-btn add-btn" @click="openEditModal" title="Добавить треки">
          <Plus :size="18" />
        </button>
        <!-- Subscribe/Unsubscribe button for non-owner public playlists -->
        <button 
          v-else-if="playlist.is_public" 
          class="action-btn subscribe-action-btn"
          :class="{ subscribed: playlist.is_subscribed }"
          @click="toggleSubscription"
          :disabled="subscribing"
          :title="playlist.is_subscribed ? 'В медиатеке' : 'Добавить в медиатеку'"
        >
          <Check v-if="playlist.is_subscribed" :size="18" />
          <Plus v-else :size="18" />
        </button>
        <!-- Share button -->
        <button class="action-btn share-btn" @click="handleSharePlaylist" title="Поделиться">
          <Share2 :size="18" />
        </button>
      </div>
    </div>

    <!-- Track list -->
    <div class="track-list" v-if="playlist.tracks?.length">
      <TrackItem
        v-for="(track, index) in playlist.tracks"
        :key="track.id"
        :track="track"
        :isPlaying="playerStore.currentTrack?.id === track.id"
        :isLiked="track.is_liked"
        @click="playTrack(track, index)"
        @like="handleLikeTrack(track)"
        @menu="(e) => openMenu('track', track, `playlist:${playlist.id}`, e)"
        @download="handleDirectDownload(track)"
        @hdNotice="handleHdNotice"
      />
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <span class="empty-icon"><Music :size="48" /></span>
      <p>Плейлист пуст</p>
      <button v-if="isOwner" class="empty-add-btn" @click="openEditModal">
        <Plus :size="18" />
        <span>Добавить треки</span>
      </button>
      <p v-else class="hint">В этом плейлисте пока нет треков</p>
    </div>

    <!-- Edit modal -->
    <EditPlaylistModal
      :show="showEditModal"
      :playlist="playlist"
      @close="showEditModal = false"
      @save="handleSavePlaylist"
      @delete="deletePlaylist"
      @update:tracks="handleTracksUpdate"
    />
  </div>

  <div v-else-if="loading" class="loading">
    <div class="spinner"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useAuthStore } from '@/stores/auth'
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import { useContextMenu } from '@/composables/useContextMenu'
import { useTrackActions, usePlaybackActions, useTrackSync, useShare } from '@/composables'
import TrackItem from '@/components/TrackItem.vue'
import EditPlaylistModal from '@/components/EditPlaylistModal.vue'
import api from '@/api/client'
import { Music, Check, Plus, Globe, Play, Shuffle, Edit3, Share2 } from 'lucide-vue-next'
import { getCoverUrl, CoverSize } from '@/utils'

// Universal context menu
const { openMenu } = useContextMenu()

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()
const authStore = useAuthStore()
const libraryStore = useLibraryStore()
const uiStore = useUIStore()

// Unified track actions
const { handleDirectDownload, handleHdNotice, handleLikeTrack } = useTrackActions()
const { share } = useShare()

const handleSharePlaylist = () => {
  if (!playlist.value) return
  share({
    type: 'playlist',
    id: playlist.value.id,
    title: playlist.value.name,
    text: `Послушай плейлист «${playlist.value.name}» в TG Player!`,
  })
}

const goToOwner = () => {
  if (playlist.value?.owner_id) {
    router.push(`/user/${playlist.value.owner_id}`)
  }
}

// State
const playlist = ref(null)
const loading = ref(true)

// Sync playlist tracks with global track events
useTrackSync(() => playlist.value?.tracks)
const showEditModal = ref(false)
const subscribing = ref(false)

// Cache-bust helper to force image reload in UI when cover changes
const addCacheBust = (url) => {
  if (!url) return null
  const sep = url.includes('?') ? '&' : '?'
  return `${url}${sep}_cb=${Date.now()}`
}

// Unified playback actions - use shufflePlayFull for lazy loading all playlist tracks
const { playAll, shufflePlayFull, isShuffling, playTrack } = usePlaybackActions(() => playlist.value?.tracks)

// Shuffle play handler using lazy loading
const shufflePlay = () => {
  if (playlist.value?.id) {
    shufflePlayFull('playlist', playlist.value.id)
  }
}

// Computed
const isOwner = computed(() => {
  if (!playlist.value || !authStore.user) return true
  return playlist.value.owner_id === authStore.user.id || !playlist.value.owner_id
})

const coverImages = computed(() => {
  if (playlist.value?.custom_cover_url) {
    return [getCoverUrl(playlist.value.custom_cover_url, CoverSize.LARGE)]
  }
  // Use covers array from API (track covers collage, up to 4)
  if (playlist.value?.covers?.length) {
    // Use large size for single cover, small for multi-cover grid
    const size = playlist.value.covers.length === 1 ? CoverSize.LARGE : CoverSize.SMALL
    return playlist.value.covers.map(url => getCoverUrl(url, size))
  }
  // Fallback to track covers for collage (use small size for grid)
  if (!playlist.value?.tracks) return []
  return playlist.value.tracks.filter(t => t.cover_url).slice(0, 4).map(t => getCoverUrl(t.cover_url, CoverSize.SMALL))
})

// Data loading
const loadPlaylist = async () => {
  if (!route.params.id) return
  loading.value = true
  try {
    const response = await api.get(`/playlists/${route.params.id}`)
    playlist.value = response.data
  } catch (error) {
    console.error('Failed to load playlist:', error)
  } finally {
    loading.value = false
  }
}

// Edit modal handlers
const openEditModal = () => {
  showEditModal.value = true
}

const handleSavePlaylist = async ({ name, isPublic, covers }) => {
  playlist.value.name = name
  playlist.value.is_public = isPublic
  
  // Update covers array (track collage covers from save response)
  if (covers?.length) {
    playlist.value.covers = covers.map(addCacheBust)
  }
  
  // Notify entire app (sidebar, grids, cache)
  await libraryStore.notifyPlaylistChange(playlist.value.id)
  
  showEditModal.value = false
  uiStore.toast.success('Сохранено', 'Плейлист обновлён')
}

const handleTracksUpdate = (tracks) => {
  playlist.value.tracks = tracks
  playlist.value.track_count = tracks.length
  // Notify app about track list change (updates sidebar counts, covers, cache)
  libraryStore.notifyPlaylistChange(playlist.value.id)
}

const deletePlaylist = async () => {
  try {
    await libraryStore.deletePlaylist(playlist.value.id)
    uiStore.toast.success('Удалено', 'Плейлист удален')
    router.push('/playlists')
  } catch (error) {
    console.error('Failed to delete playlist:', error)
    uiStore.toast.error('Ошибка', 'Не удалось удалить плейлист')
  }
}

// Subscription
const toggleSubscription = async () => {
  if (subscribing.value) return
  subscribing.value = true
  
  try {
    if (playlist.value.is_subscribed) {
      // Unsubscribe
      await api.delete(`/playlists/${playlist.value.id}/subscribe`)
      playlist.value.is_subscribed = false
      uiStore.toast.success('Удалено', 'Плейлист убран из медиатеки')
    } else {
      // Subscribe
      await api.post(`/playlists/${playlist.value.id}/subscribe`)
      playlist.value.is_subscribed = true
      uiStore.toast.success('Добавлено', 'Плейлист добавлен в медиатеку')
    }
    // Notify entire app about subscription change
    await libraryStore.notifyPlaylistChange(playlist.value.id)
  } catch (error) {
    console.error('Failed to toggle subscription:', error)
    const errorMsg = error.response?.data?.detail || 'Ошибка'
    uiStore.toast.error('Ошибка', errorMsg)
  } finally {
    subscribing.value = false
  }
}

const onPlaylistChanged = (e) => {
  const changedId = e?.detail?.playlistId
  if (!changedId || String(changedId) === String(route.params.id) || (playlist.value && String(changedId) === String(playlist.value.id))) {
    loadPlaylist()
  }
}

// Load on mount & listen for global changes
onMounted(() => {
  loadPlaylist()
  window.addEventListener('playlist:changed', onPlaylistChanged)
})

onUnmounted(() => {
  window.removeEventListener('playlist:changed', onPlaylistChanged)
})

// Reload when route params change (for sidebar navigation)
watch(
  () => route.params.id,
  (newId, oldId) => {
    if (newId && newId !== oldId) {
      loadPlaylist()
    }
  }
)
</script>

<style scoped>
.playlist-detail-view {
  padding: 16px;
}

.cover-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  width: 100%;
  height: 100%;
}

.cover-grid.single-cover {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
}

.cover-grid img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.play-btn svg {
  margin-left: 2px;
}

.track-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.empty-state {
  text-align: center;
  padding: 48px 16px;
  color: var(--c-text-2);
}

.empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.empty-add-btn {
  margin-top: 16px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 20px;
  background: var(--c-accent);
  color: #fff;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
}

.empty-add-btn:active {
  transform: scale(0.97);
}

.empty-add-btn:hover {
  opacity: 0.9;
}

.hint {
  color: var(--c-text-3);
  font-size: 14px;
  margin-top: 8px;
}

.public-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--c-accent);
  font-size: 13px;
  font-weight: 500;
}

.owner-info {
  font-size: 13px;
  color: var(--c-text-3);
}
.owner-info.clickable {
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.owner-info.clickable:hover {
  color: var(--c-accent);
}

.share-btn {
  background: var(--c-bg-2);
}

.share-btn:hover {
  background: var(--c-bg-3);
}
</style>
