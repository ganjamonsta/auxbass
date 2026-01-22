<template>
  <div class="app">
    <!-- Header -->
    <header class="header">
      <div class="header-content">
        <button 
          v-if="currentView !== 'library'" 
          @click="goBack"
          class="back-btn"
        >
          ← 
        </button>
        <h1 class="title">{{ headerTitle }}</h1>
        <div class="header-right">
          <EnrichmentStatus />
          <button 
            v-if="currentView === 'library'"
            @click="showSearch = !showSearch"
            class="search-btn"
          >
            🔍
          </button>
        </div>
      </div>
      
      <!-- Search bar -->
      <Transition name="slide-down">
        <div v-if="showSearch && currentView === 'library'" class="search-bar">
          <input 
            v-model="searchQuery"
            type="text"
            placeholder="Поиск по названию, артисту..."
            class="search-input"
            @input="debouncedSearch"
          />
        </div>
      </Transition>
    </header>

    <!-- Main content -->
    <main class="content">
      <!-- Library view -->
      <div v-if="currentView === 'library'" class="library">
        <!-- Tabs -->
        <div class="tabs">
          <button 
            :class="['tab', { active: activeTab === 'tracks' }]"
            @click="activeTab = 'tracks'"
          >
            Треки
          </button>
          <button 
            :class="['tab', { active: activeTab === 'playlists' }]"
            @click="activeTab = 'playlists'"
          >
            Плейлисты
          </button>
          <button 
            :class="['tab', { active: activeTab === 'artists' }]"
            @click="activeTab = 'artists'; library.fetchArtists()"
          >
            Артисты
          </button>
          <button 
            :class="['tab', { active: activeTab === 'genres' }]"
            @click="activeTab = 'genres'; library.fetchGenres()"
          >
            Жанры
          </button>
        </div>

        <!-- Track list -->
        <div v-if="activeTab === 'tracks'" class="track-list">
          <div v-if="library.loading" class="skeleton-list">
            <TrackSkeleton v-for="i in 6" :key="i" />
          </div>
          <div v-else-if="library.tracks.length === 0" class="empty">
            <p>🎵 Библиотека пуста</p>
            <p class="hint">Отправь аудиофайлы боту, чтобы добавить музыку</p>
          </div>
          <TransitionGroup v-else name="list" tag="div">
            <TrackItem 
              v-for="track in library.tracks" 
              :key="track.id"
              :track="track"
              :isPlaying="player.currentTrack?.id === track.id && player.isPlaying"
              @click="playTrack(track)"
              @menu="showTrackMenu(track)"
            />
          </TransitionGroup>
        </div>

        <!-- Playlists -->
        <div v-if="activeTab === 'playlists'" class="playlist-list">
          <button @click="createPlaylist" class="create-playlist-btn">
            + Создать плейлист
          </button>
          <div v-if="library.playlists.length === 0" class="empty">
            <p>📁 Нет плейлистов</p>
          </div>
          <PlaylistItem
            v-for="playlist in library.playlists"
            :key="playlist.id"
            :playlist="playlist"
            @click="openPlaylist(playlist)"
          />
        </div>

        <!-- Artists -->
        <div v-if="activeTab === 'artists'" class="artist-list">
          <div v-if="library.artists.length === 0" class="empty">
            <p>👤 Нет артистов</p>
          </div>
          <div
            v-for="artist in library.artists"
            :key="artist.artist"
            class="artist-item"
            @click="filterByArtist(artist.artist)"
          >
            <span class="artist-name">{{ artist.artist || 'Неизвестный' }}</span>
            <span class="artist-count">{{ artist.count }} треков</span>
          </div>
        </div>

        <!-- Genres -->
        <div v-if="activeTab === 'genres'" class="genre-list">
          <div v-if="library.genres.length === 0" class="empty">
            <p>🎸 Нет жанров</p>
            <p class="hint">Жанры определяются из метаданных треков</p>
          </div>
          <div
            v-for="genre in library.genres"
            :key="genre.genre"
            class="genre-item"
            @click="filterByGenre(genre.genre)"
          >
            <span class="genre-name">{{ genre.genre }}</span>
            <span class="genre-count">{{ genre.count }} треков</span>
          </div>
        </div>
      </div>

      <!-- Playlist view -->
      <div v-if="currentView === 'playlist'" class="playlist-view">
        <div class="playlist-header">
          <h2>{{ currentPlaylist?.name }}</h2>
          <p class="playlist-info">
            {{ currentPlaylist?.track_count }} треков • 
            {{ formatDuration(currentPlaylist?.total_duration) }}
          </p>
        </div>
        <TrackItem 
          v-for="track in currentPlaylist?.tracks" 
          :key="track.id"
          :track="track"
          :isPlaying="player.currentTrack?.id === track.id && player.isPlaying"
          @click="playTrack(track, currentPlaylist?.tracks)"
        />
      </div>
    </main>

    <!-- Mini Player -->
    <MiniPlayer 
      v-if="player.currentTrack"
      :track="player.currentTrack"
      :isPlaying="player.isPlaying"
      :progress="player.progress"
      @toggle="player.toggle()"
      @next="player.next()"
      @expand="showFullPlayer = true"
    />

    <!-- Full Player Modal -->
    <Transition name="slide-up">
      <FullPlayer 
        v-if="showFullPlayer"
        :track="player.currentTrack"
        :isPlaying="player.isPlaying"
        :progress="player.progress"
        :duration="player.duration"
        :volume="player.volume"
        :isMuted="player.isMuted"
        :shuffle="player.shuffle"
        :repeat="player.repeat"
        @close="showFullPlayer = false"
        @toggle="player.toggle()"
        @next="player.next()"
        @prev="player.prev()"
        @seek="player.seek($event)"
        @setVolume="player.setVolume($event)"
        @toggleMute="player.toggleMute()"
        @toggleShuffle="player.toggleShuffle()"
        @toggleRepeat="player.toggleRepeat()"
      />
    </Transition>

    <!-- Track Context Menu -->
    <TrackMenu
      :show="showTrackMenuModal"
      :track="selectedTrack"
      @close="showTrackMenuModal = false"
      @addToPlaylist="handleAddToPlaylist"
      @edit="handleEditTrack"
      @delete="handleDeleteTrack"
    />

    <!-- Edit Track Modal -->
    <EditTrackModal
      :show="showEditModal"
      :track="editingTrack"
      @close="showEditModal = false"
      @saved="library.fetchTracks()"
    />

    <!-- Delete Confirmation -->
    <ConfirmDialog
      :show="showConfirmDelete"
      type="danger"
      title="Удалить трек?"
      :message="`Трек «${deletingTrack?.title || 'Без названия'}» будет удалён из библиотеки.`"
      confirmText="Удалить"
      @confirm="confirmDeleteTrack"
      @cancel="showConfirmDelete = false"
    />

    <!-- Playlist Picker -->
    <PlaylistPicker
      :show="showPlaylistPicker"
      :track="trackForPlaylist"
      @close="showPlaylistPicker = false"
      @createNew="showPlaylistPicker = false; createPlaylist()"
    />

    <!-- Create Playlist Modal -->
    <Transition name="fade">
      <div v-if="showCreatePlaylist" class="modal-overlay" @click.self="showCreatePlaylist = false">
        <div class="modal">
          <h3>Новый плейлист</h3>
          <input 
            v-model="newPlaylistName"
            type="text"
            placeholder="Название плейлиста"
            class="modal-input"
          />
          <div class="modal-actions">
            <button @click="showCreatePlaylist = false" class="btn-secondary">Отмена</button>
            <button @click="submitCreatePlaylist" class="btn-primary">Создать</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { usePlayerStore } from './stores/player'
import { useLibraryStore } from './stores/library'
import TrackItem from './components/TrackItem.vue'
import TrackSkeleton from './components/TrackSkeleton.vue'
import PlaylistItem from './components/PlaylistItem.vue'
import MiniPlayer from './components/MiniPlayer.vue'
import FullPlayer from './components/FullPlayer.vue'
import TrackMenu from './components/TrackMenu.vue'
import EditTrackModal from './components/EditTrackModal.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'
import PlaylistPicker from './components/PlaylistPicker.vue'
import EnrichmentStatus from './components/EnrichmentStatus.vue'

const telegram = inject('telegram')

// Stores
const player = usePlayerStore()
const library = useLibraryStore()

// State
const currentView = ref('library')
const activeTab = ref('tracks')
const showSearch = ref(false)
const searchQuery = ref('')
const showFullPlayer = ref(false)
const showCreatePlaylist = ref(false)
const newPlaylistName = ref('')
const currentPlaylist = ref(null)

// Track menu state
const showTrackMenuModal = ref(false)
const selectedTrack = ref(null)

// Edit modal state
const showEditModal = ref(false)
const editingTrack = ref(null)

// Confirm dialog state
const showConfirmDelete = ref(false)
const deletingTrack = ref(null)

// Playlist picker state
const showPlaylistPicker = ref(false)
const trackForPlaylist = ref(null)

// Computed
const headerTitle = computed(() => {
  switch (currentView.value) {
    case 'library': return 'TG Player'
    case 'playlist': return currentPlaylist.value?.name || 'Плейлист'
    default: return 'TG Player'
  }
})

// Methods
const goBack = () => {
  currentView.value = 'library'
  currentPlaylist.value = null
}

const playTrack = async (track, queue = null) => {
  await player.play(track, queue || library.tracks)
}

const showTrackMenu = (track) => {
  selectedTrack.value = track
  showTrackMenuModal.value = true
}

// Track menu handlers
const handleAddToPlaylist = (track) => {
  trackForPlaylist.value = track
  showPlaylistPicker.value = true
}

const handleEditTrack = (track) => {
  editingTrack.value = track
  showEditModal.value = true
}

const handleDeleteTrack = (track) => {
  deletingTrack.value = track
  showConfirmDelete.value = true
}

const confirmDeleteTrack = async () => {
  if (deletingTrack.value) {
    await library.deleteTrack(deletingTrack.value.id)
    telegram?.HapticFeedback?.notificationOccurred?.('success')
  }
  showConfirmDelete.value = false
  deletingTrack.value = null
}

const openPlaylist = async (playlist) => {
  currentPlaylist.value = await library.fetchPlaylist(playlist.id)
  currentView.value = 'playlist'
}

const createPlaylist = () => {
  newPlaylistName.value = ''
  showCreatePlaylist.value = true
}

const submitCreatePlaylist = async () => {
  if (!newPlaylistName.value.trim()) return
  await library.createPlaylist(newPlaylistName.value)
  showCreatePlaylist.value = false
}

const filterByArtist = (artist) => {
  searchQuery.value = artist
  activeTab.value = 'tracks'
  library.fetchTracks({ artist })
}

const filterByGenre = (genre) => {
  searchQuery.value = genre
  activeTab.value = 'tracks'
  library.fetchTracks({ genre })
}

const formatDuration = (seconds) => {
  if (!seconds) return '0 мин'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) return `${hours} ч ${minutes} мин`
  return `${minutes} мин`
}

let searchTimeout = null
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    library.fetchTracks({ search: searchQuery.value })
  }, 300)
}

// Lifecycle
onMounted(async () => {
  await library.init()
})
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--tg-theme-bg-color);
}

.header {
  flex-shrink: 0;
  padding: 12px 16px;
  background: var(--tg-theme-bg-color);
  border-bottom: 1px solid var(--tg-theme-secondary-bg-color);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  flex: 1;
  font-size: 20px;
  font-weight: 600;
}

.back-btn, .search-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 4px 8px;
}

.search-bar {
  margin-top: 12px;
}

.search-input {
  width: 100%;
  padding: 10px 14px;
  border: none;
  border-radius: 10px;
  background: var(--tg-theme-secondary-bg-color);
  color: var(--tg-theme-text-color);
  font-size: 15px;
}

.search-input::placeholder {
  color: var(--tg-theme-hint-color);
}

.content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 80px; /* Space for mini player */
}

.tabs {
  display: flex;
  padding: 8px 16px;
  gap: 8px;
  background: var(--tg-theme-bg-color);
  position: sticky;
  top: 0;
  z-index: 10;
}

.tab {
  flex: 1;
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  background: var(--tg-theme-secondary-bg-color);
  color: var(--tg-theme-hint-color);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab.active {
  background: var(--tg-theme-button-color);
  color: var(--tg-theme-button-text-color);
}

.loading, .empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty p {
  font-size: 18px;
  margin-bottom: 8px;
}

.empty .hint {
  font-size: 14px;
  color: var(--tg-theme-hint-color);
}

.artist-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--tg-theme-secondary-bg-color);
  cursor: pointer;
}

.artist-name {
  font-weight: 500;
}

.artist-count {
  color: var(--tg-theme-hint-color);
  font-size: 13px;
}

.genre-list {
  padding: 0;
}

.genre-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--tg-theme-secondary-bg-color);
  cursor: pointer;
}

.genre-item:active {
  background: var(--tg-theme-secondary-bg-color);
}

.genre-name {
  font-weight: 500;
}

.genre-count {
  color: var(--tg-theme-hint-color);
  font-size: 13px;
}

.create-playlist-btn {
  display: block;
  width: calc(100% - 32px);
  margin: 16px;
  padding: 14px;
  border: 2px dashed var(--tg-theme-hint-color);
  border-radius: 12px;
  background: transparent;
  color: var(--tg-theme-hint-color);
  font-size: 15px;
  cursor: pointer;
}

.playlist-view {
  padding: 16px;
}

.playlist-header {
  margin-bottom: 16px;
}

.playlist-header h2 {
  font-size: 24px;
  margin-bottom: 4px;
}

.playlist-info {
  color: var(--tg-theme-hint-color);
  font-size: 14px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: var(--tg-theme-bg-color);
  padding: 24px;
  border-radius: 16px;
  width: 90%;
  max-width: 320px;
}

.modal h3 {
  margin-bottom: 16px;
  font-size: 18px;
}

.modal-input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--tg-theme-secondary-bg-color);
  border-radius: 8px;
  background: var(--tg-theme-secondary-bg-color);
  color: var(--tg-theme-text-color);
  font-size: 15px;
  margin-bottom: 16px;
}

.modal-actions {
  display: flex;
  gap: 12px;
}

.btn-primary, .btn-secondary {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
}

.btn-primary {
  background: var(--tg-theme-button-color);
  color: var(--tg-theme-button-text-color);
}

.btn-secondary {
  background: var(--tg-theme-secondary-bg-color);
  color: var(--tg-theme-text-color);
}

/* Header improvements */
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.skeleton-list {
  padding: 0;
}

/* List animation */
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.list-move {
  transition: transform 0.3s ease;
}

/* Slide down animation */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Slide up animation */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}

/* Fade animation */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
