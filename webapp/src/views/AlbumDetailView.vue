<template>
  <div class="album-detail-view" v-if="album">
    <!-- Album header -->
    <div class="album-header">
      <div class="album-cover">
        <img v-if="album.cover_url" :src="album.cover_url" :alt="album.name" />
        <div v-else class="cover-placeholder">💿</div>
      </div>
      <div class="album-info">
        <h1>{{ album.name }}</h1>
        <p class="artist" @click="goToArtist">{{ album.artist }}</p>
        <p class="meta">
          <span v-if="album.release_date">{{ formatYear(album.release_date) }} • </span>
          <span v-if="album.total_tracks">
            {{ album.track_count }}/{{ album.total_tracks }} треков
          </span>
          <span v-else>{{ album.track_count }} треков</span>
        </p>
      </div>
    </div>

    <!-- Actions -->
    <div class="album-actions">
      <div class="action-buttons">
        <button class="action-btn play-btn" @click="playAll">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </button>
        <button class="action-btn shuffle-btn" @click="shufflePlay">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Track list - show full_tracklist if available, otherwise just user's tracks -->
    <div class="track-list">
      <!-- Full tracklist mode: shows all album tracks with availability status -->
      <template v-if="album.full_tracklist && album.full_tracklist.length">
        <div
          v-for="item in album.full_tracklist"
          :key="item.track_number"
          class="tracklist-item"
          :class="{ 
            'missing': !item.track, 
            'has-track': item.track,
            'not-in-library': item.track && !item.in_library
          }"
          @click="handleTracklistItemClick(item)"
        >
          <span class="track-number">{{ item.track_number }}</span>
          
          <div class="track-info">
            <span class="track-title" :class="{ 'missing-title': !item.track }">
              {{ item.title }}
            </span>
            <span v-if="item.artist && item.artist !== album.artist" class="track-artist">
              {{ item.artist }}
            </span>
          </div>
          
          <span class="track-duration">{{ formatDuration(item.duration) }}</span>
          
          <!-- Add to library button for tracks not in user's library -->
          <button
            v-if="item.track && !item.in_library"
            class="add-library-btn"
            @click.stop="handleAddToLibraryFromTracklist(item)"
            title="Добавить в библиотеку"
          >
            +
          </button>
          <!-- In library indicator -->
          <span v-else-if="item.track && item.in_library" class="in-library-indicator">
            ✓
          </span>
          <!-- Missing track button - track not in database -->
          <button
            v-else-if="!item.track"
            class="add-btn"
            @click.stop="handleMissingTrack(item)"
            title="Найти трек"
          >
            +
          </button>
          <!-- Playing indicator -->
          <span v-if="playerStore.currentTrack?.id === item.track_id" class="playing-indicator">
            🎵
          </span>
        </div>
      </template>
      
      <!-- Simple mode: just user's tracks (fallback when no full_tracklist) -->
      <template v-else>
        <TrackItem
          v-for="(track, index) in album.tracks"
          :key="track.id"
          :track="track"
          :trackNumber="index + 1"
          :isPlaying="playerStore.currentTrack?.id === track.id"
          :isLiked="track.is_liked"
          :hideCover="true"
          :showAddToLibrary="isGlobal"
          :inLibrary="track.in_library"
          @click="playTrack(track, index)"
          @like="handleLikeTrack(track)"
          @addToLibrary="handleAddToLibrary(track)"
          @menu="openTrackMenu(track)"
          @download="handleDirectDownload(track)"
        />
      </template>
    </div>
    
    <!-- Missing track modal -->
    <div v-if="showMissingModal" class="modal-overlay" @click="closeMissingModal">
      <div class="modal-content" @click.stop>
        <h3>{{ missingTrackItem?.title }}</h3>
        
        <div v-if="searchingTrack" class="modal-loading">
          <div class="spinner"></div>
          <p>Ищем трек...</p>
        </div>
        
        <div v-else-if="foundTrack" class="modal-found">
          <p class="success-message">✅ {{ searchResult?.message }}</p>
          <div class="found-track-info">
            <strong>{{ foundTrack.title }}</strong>
            <span>{{ foundTrack.artist }}</span>
          </div>
          <button
            v-if="!searchResult?.in_library"
            class="primary-btn"
            @click="addFoundTrack"
            :disabled="addingTrack"
          >
            {{ addingTrack ? 'Добавляем...' : 'Добавить в библиотеку' }}
          </button>
          <button v-else class="secondary-btn" @click="closeMissingModal">
            Уже в библиотеке
          </button>
        </div>
        
        <div v-else class="modal-not-found">
          <p class="info-message">{{ searchResult?.message }}</p>
          <p class="hint">Скинь этот трек боту в Telegram, и он появится в библиотеке.</p>
        </div>
        
        <button class="close-btn" @click="closeMissingModal">✕</button>
      </div>
    </div>
    
    <!-- Track context menu -->
    <TrackMenu
      :show="showMenu"
      :track="menuTrack"
      context="album"
      @close="closeMenu"
      @goToArtist="handleGoToArtist"
      @addToPlaylist="handleAddToPlaylist"
      @download="handleDownloadTrack"
    />
    
    <!-- Playlist picker modal -->
    <PlaylistPicker
      :show="showPlaylistPicker"
      :track="menuTrack"
      @close="showPlaylistPicker = false; closeMenu()"
      @createNew="showPlaylistPicker = false; closeMenu()"
      @added="handlePlaylistAdded"
    />
  </div>

  <div v-else-if="loading" class="loading">
    <div class="spinner"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import TrackItem from '@/components/TrackItem.vue'
import TrackMenu from '@/components/TrackMenu.vue'
import PlaylistPicker from '@/components/PlaylistPicker.vue'
import api, { playerApi } from '@/api/client'

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const uiStore = useUIStore()

const album = ref(null)
const loading = ref(true)
const showMenu = ref(false)
const menuTrack = ref(null)

// Scope from query
const scope = computed(() => route.query.scope || 'library')
const isGlobal = computed(() => scope.value === 'global')

// Missing track modal state
const showMissingModal = ref(false)
const missingTrackItem = ref(null)
const searchingTrack = ref(false)
const searchResult = ref(null)
const foundTrack = ref(null)
const addingTrack = ref(false)

// Get playable tracks - all tracks that have a track object (exist in database)
const playableTracks = computed(() => {
  if (album.value?.full_tracklist) {
    // All tracks with track object are playable (both library and global mode)
    return album.value.full_tracklist
      .filter(item => item.track)
      .map(item => item.track)
  }
  return album.value?.tracks || []
})

const loadAlbum = async () => {
  loading.value = true
  try {
    const params = { scope: scope.value }
    const response = await api.get(`/albums/${route.params.id}`, { params })
    album.value = response.data
  } finally {
    loading.value = false
  }
}

const playAll = () => {
  if (playableTracks.value.length) {
    playerStore.playTrack(playableTracks.value[0], playableTracks.value)
  }
}

const shufflePlay = () => {
  if (playableTracks.value.length) {
    const shuffled = [...playableTracks.value].sort(() => Math.random() - 0.5)
    playerStore.playTrack(shuffled[0], shuffled)
  }
}

const playTrack = (track, index) => {
  playerStore.playTrack(track, album.value.tracks, index)
}

const playTrackItem = (item) => {
  if (item.track) {
    const index = playableTracks.value.findIndex(t => t.id === item.track_id)
    playerStore.playTrack(item.track, playableTracks.value, index >= 0 ? index : 0)
  }
}

// Handle click on tracklist item
const handleTracklistItemClick = (item) => {
  if (item.track) {
    // Track exists in database - play it (works for both library and global mode)
    playTrackItem(item)
  } else {
    // Track not in database - show search modal to help user find/add it
    handleMissingTrack(item)
  }
}

// Add track to library from tracklist (global mode)
const handleAddToLibraryFromTracklist = async (item) => {
  if (!item.track_id) return
  const success = await libraryStore.addToLibrary(item.track_id)
  if (success) {
    item.in_library = true
  }
}

// Handle clicking on missing track
const handleMissingTrack = async (item) => {
  missingTrackItem.value = item
  showMissingModal.value = true
  searchingTrack.value = true
  searchResult.value = null
  foundTrack.value = null
  
  try {
    const response = await api.post(`/albums/${album.value.id}/find-track`, null, {
      params: {
        title: item.title,
        artist: item.artist || album.value.artist
      }
    })
    searchResult.value = response.data
    if (response.data.found && response.data.track) {
      foundTrack.value = response.data.track
    }
  } catch (error) {
    searchResult.value = {
      found: false,
      message: 'Ошибка поиска. Попробуй скинуть трек боту.'
    }
  } finally {
    searchingTrack.value = false
  }
}

const addFoundTrack = async () => {
  if (!searchResult.value?.track_id) return
  
  addingTrack.value = true
  try {
    await api.post(`/albums/${album.value.id}/add-track/${searchResult.value.track_id}`)
    // Reload album to reflect changes
    await loadAlbum()
    closeMissingModal()
  } catch (error) {
    console.error('Failed to add track:', error)
  } finally {
    addingTrack.value = false
  }
}

const closeMissingModal = () => {
  showMissingModal.value = false
  missingTrackItem.value = null
  searchResult.value = null
  foundTrack.value = null
}

const goToArtist = () => {
  const query = isGlobal.value ? { scope: 'global' } : {}
  router.push({ path: `/artist/${encodeURIComponent(album.value.artist)}`, query })
}

// Track menu handlers
const openTrackMenu = (track) => {
  menuTrack.value = track
  showMenu.value = true
}

const closeMenu = () => {
  showMenu.value = false
  menuTrack.value = null
}

const handleLikeTrack = async (track) => {
  const newLikedState = await libraryStore.toggleLike(track.id)
  track.is_liked = newLikedState
}

const handleAddToLibrary = async (track) => {
  const success = await libraryStore.addToLibrary(track.id)
  if (success) {
    track.in_library = true
  }
}

const handleGoToArtist = () => {
  closeMenu()
  const query = isGlobal.value ? { scope: 'global' } : {}
  router.push({ path: `/artist/${encodeURIComponent(menuTrack.value?.artist)}`, query })
}

const handleAddToPlaylist = () => {
  showPlaylistPicker.value = true
}

const showPlaylistPicker = ref(false)
const handlePlaylistAdded = (playlist) => {
  uiStore.toast.success('Добавлено', `Трек добавлен в плейлист "${playlist.name}"`)
}

// Direct download from TrackItem download button (for HD/large files)
const handleDirectDownload = async (track) => {
  if (!track) return
  
  try {
    await playerApi.download(track.id)
    uiStore.toast.success('Трек отправлен', 'Проверьте сообщения в Telegram')
  } catch (error) {
    console.error('Failed to download track:', error)
    const errorMsg = error.response?.data?.detail || 'Ошибка отправки'
    uiStore.toast.error('Не удалось отправить', errorMsg)
  }
}

const handleDownloadTrack = async () => {
  if (!menuTrack.value) return
  await handleDirectDownload(menuTrack.value)
  closeMenu()
}

const formatDuration = (seconds) => {
  if (!seconds) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatYear = (date) => {
  if (!date) return ''
  return new Date(date).getFullYear()
}

onMounted(() => {
  loadAlbum()
})
</script>

<style scoped>
.album-detail-view {
  padding: 16px;
  padding-bottom: 120px;
}

.album-header {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.album-cover {
  width: 160px;
  height: 160px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-elevated);
  flex-shrink: 0;
}

.album-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 64px;
}

.album-info {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.album-info h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.artist {
  color: var(--text-secondary);
  margin: 0 0 4px 0;
  cursor: pointer;
}

.artist:hover {
  text-decoration: underline;
}

.meta {
  color: var(--text-tertiary);
  font-size: 13px;
  margin: 0;
}

.album-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.action-buttons {
  display: flex;
  border-radius: 28px;
  background: var(--accent);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.3),
    -3px -3px 8px rgba(255, 255, 255, 0.1),
    inset 0 1px 1px rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.action-btn {
  width: 48px;
  height: 48px;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #000;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
}

.action-btn::after {
  content: '';
  position: absolute;
  top: 10px;
  bottom: 10px;
  width: 1px;
  background: rgba(0, 0, 0, 0.15);
}

.action-btn.play-btn::after {
  right: 0;
}

.action-btn.shuffle-btn::after {
  display: none;
}

.action-btn:active {
  background: rgba(0, 0, 0, 0.1);
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.15);
}

.action-btn.play-btn svg {
  margin-left: 2px;
}

.track-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* Full tracklist item styles */
.tracklist-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.tracklist-item:hover {
  background: var(--bg-elevated);
}

.tracklist-item.missing {
  opacity: 0.6;
}

.tracklist-item.missing:hover {
  opacity: 0.9;
}

.track-number {
  width: 24px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 14px;
}

.track-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.track-title {
  font-size: 15px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-title.missing-title {
  color: var(--text-secondary);
}

.track-artist {
  font-size: 13px;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-duration {
  color: var(--text-tertiary);
  font-size: 13px;
  min-width: 40px;
  text-align: right;
}

.add-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent);
  color: #000;
  border: none;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.add-btn:hover {
  transform: scale(1.1);
}

.add-library-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent);
  color: #000;
  border: none;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.add-library-btn:hover {
  transform: scale(1.1);
}

.in-library-indicator {
  color: var(--accent);
  font-size: 14px;
  font-weight: bold;
  width: 28px;
  text-align: center;
}

.tracklist-item.not-in-library {
  /* Slightly different style for tracks not in user's library but playable */
}

.playing-indicator {
  font-size: 16px;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.modal-content {
  background: var(--bg-elevated);
  border-radius: 16px;
  padding: 24px;
  max-width: 400px;
  width: 100%;
  position: relative;
}

.modal-content h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  padding-right: 24px;
}

.modal-loading {
  text-align: center;
  padding: 24px 0;
}

.modal-loading p {
  margin-top: 12px;
  color: var(--text-secondary);
}

.modal-found,
.modal-not-found {
  padding: 8px 0;
}

.success-message {
  color: var(--accent);
  margin-bottom: 12px;
}

.info-message {
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.hint {
  color: var(--text-tertiary);
  font-size: 13px;
}

.found-track-info {
  background: var(--bg-base);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.found-track-info strong {
  color: var(--text-primary);
}

.found-track-info span {
  color: var(--text-secondary);
  font-size: 14px;
}

.primary-btn {
  width: 100%;
  padding: 12px;
  background: var(--accent);
  color: #000;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.primary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.secondary-btn {
  width: 100%;
  padding: 12px;
  background: var(--bg-base);
  color: var(--text-primary);
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: none;
  border: none;
  color: var(--text-tertiary);
  font-size: 20px;
  cursor: pointer;
}

/* Loading */
.loading {
  display: flex;
  justify-content: center;
  padding: 48px;
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
