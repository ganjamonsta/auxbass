<template>
  <div class="app spotify-theme">
    <!-- One UI Style Header -->
    <header class="oneui-header" v-if="currentView === 'library'">
      <div class="header-top">
        <EnrichmentStatus />
        <button @click="showSearch = !showSearch" class="icon-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
          </svg>
        </button>
      </div>
      <h1>{{ headerTitle }}</h1>
      
      <!-- Search bar -->
      <Transition name="slide-down">
        <div v-if="showSearch" class="search-container">
          <input 
            v-model="searchQuery"
            type="text"
            placeholder="Поиск треков, артистов..."
            class="search-input"
            @input="debouncedSearch"
          />
        </div>
      </Transition>
    </header>

    <!-- Compact Header for other views -->
    <header v-else class="compact-header">
      <button @click="goBack" class="icon-btn">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </button>
      <span class="header-title">{{ headerTitle }}</span>
      <div class="spacer"></div>
    </header>

    <!-- Main content -->
    <main class="content">
      <!-- Library view -->
      <div v-if="currentView === 'library'" class="library">
        <!-- Track list -->
        <div v-if="activeTab === 'tracks'" class="track-list">
          <div v-if="library.loading" class="skeleton-list">
            <TrackSkeleton v-for="i in 6" :key="i" />
          </div>
          <div v-else-if="library.tracks.length === 0" class="empty">
            <div class="empty-icon">🎵</div>
            <p class="empty-title">Библиотека пуста</p>
            <p class="empty-hint">Отправь аудиофайлы боту,<br/>чтобы добавить музыку</p>
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
        <div v-if="activeTab === 'playlists'" class="playlist-section">
          <button @click="createPlaylist" class="create-btn">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
            </svg>
            <span>Создать плейлист</span>
          </button>
          <div v-if="library.playlists.length === 0" class="empty">
            <div class="empty-icon">📁</div>
            <p class="empty-title">Нет плейлистов</p>
          </div>
          <PlaylistItem
            v-for="playlist in library.playlists"
            :key="playlist.id"
            :playlist="playlist"
            @click="openPlaylist(playlist)"
          />
        </div>

        <!-- Artists -->
        <div v-if="activeTab === 'artists'" class="list-section">
          <div v-if="library.artists.length === 0" class="empty">
            <div class="empty-icon">👤</div>
            <p class="empty-title">Нет артистов</p>
          </div>
          <div
            v-for="artist in library.artists"
            :key="artist.artist"
            class="list-item"
            @click="filterByArtist(artist.artist)"
          >
            <div class="list-item-avatar">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
              </svg>
            </div>
            <div class="list-item-content">
              <span class="list-item-title">{{ artist.artist || 'Неизвестный' }}</span>
              <span class="list-item-subtitle">{{ artist.count }} треков</span>
            </div>
            <svg class="list-item-arrow" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
            </svg>
          </div>
        </div>

        <!-- Genres -->
        <div v-if="activeTab === 'genres'" class="list-section">
          <div v-if="library.genres.length === 0" class="empty">
            <div class="empty-icon">🎸</div>
            <p class="empty-title">Нет жанров</p>
            <p class="empty-hint">Жанры определяются из метаданных</p>
          </div>
          <div
            v-for="genre in library.genres"
            :key="genre.genre"
            class="list-item"
            @click="filterByGenre(genre.genre)"
          >
            <div class="list-item-avatar genre">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
              </svg>
            </div>
            <div class="list-item-content">
              <span class="list-item-title">{{ genre.genre }}</span>
              <span class="list-item-subtitle">{{ genre.count }} треков</span>
            </div>
            <svg class="list-item-arrow" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
            </svg>
          </div>
        </div>

        <!-- Queue tab -->
        <div v-if="activeTab === 'queue'" class="queue-section">
          <div v-if="!player.queue.length" class="empty">
            <div class="empty-icon">📋</div>
            <p class="empty-title">Очередь пуста</p>
            <p class="empty-hint">Начни воспроизведение</p>
          </div>
          <div v-else class="queue-list">
            <div v-if="player.currentTrack" class="queue-now-playing">
              <span class="queue-label">Сейчас играет</span>
              <TrackItem 
                :track="player.currentTrack"
                :isPlaying="player.isPlaying"
                compact
              />
            </div>
            <div v-if="upcomingTracks.length" class="queue-upcoming">
              <span class="queue-label">Далее</span>
              <TrackItem 
                v-for="(track, idx) in upcomingTracks" 
                :key="`queue-${idx}-${track.id}`"
                :track="track"
                compact
                @click="player.playFromQueue(idx)"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Playlist view -->
      <div v-if="currentView === 'playlist'" class="playlist-view">
        <div class="playlist-header-section">
          <div class="playlist-cover">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
            </svg>
          </div>
          <div class="playlist-meta">
            <h2>{{ currentPlaylist?.name }}</h2>
            <p>{{ currentPlaylist?.track_count }} треков • {{ formatDuration(currentPlaylist?.total_duration) }}</p>
          </div>
          <button class="play-all-btn" @click="playPlaylist">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </button>
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

    <!-- Bottom Tab Bar (One UI style) -->
    <nav v-if="currentView === 'library'" class="tab-bar">
      <button 
        :class="['tab-item', { active: activeTab === 'tracks' }]"
        @click="activeTab = 'tracks'"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
        </svg>
        <span>Треки</span>
      </button>
      <button 
        :class="['tab-item', { active: activeTab === 'playlists' }]"
        @click="activeTab = 'playlists'"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
        </svg>
        <span>Плейлисты</span>
      </button>
      <button 
        :class="['tab-item', { active: activeTab === 'artists' }]"
        @click="activeTab = 'artists'; library.fetchArtists()"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>
        <span>Артисты</span>
      </button>
      <button 
        :class="['tab-item', { active: activeTab === 'queue' }]"
        @click="activeTab = 'queue'"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M4 10h12v2H4zm0-4h12v2H4zm0 8h8v2H4zm10 0v6l5-3z"/>
        </svg>
        <span>Очередь</span>
      </button>
    </nav>

    <!-- Mini Player -->
    <MiniPlayer 
      v-if="player.currentTrack"
      :track="player.currentTrack"
      :isPlaying="player.isPlaying"
      :progress="player.progress"
      :duration="player.duration"
      @toggle="player.toggle()"
      @next="player.next()"
      @expand="showFullPlayer = true"
    />

    <!-- Full Player Modal with swipe -->
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
        :queue="player.queue"
        :queueIndex="player.queueIndex"
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
      :message="`Трек «${deletingTrack?.title || 'Без названия'}» будет удалён.`"
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

const upcomingTracks = computed(() => {
  if (!player.queue.length || player.queueIndex < 0) return []
  return player.queue.slice(player.queueIndex + 1, player.queueIndex + 11)
})

// Methods
const goBack = () => {
  currentView.value = 'library'
  currentPlaylist.value = null
}

const playTrack = async (track, queue = null) => {
  await player.play(track, queue || library.tracks)
}

const playPlaylist = async () => {
  if (currentPlaylist.value?.tracks?.length) {
    await player.play(currentPlaylist.value.tracks[0], currentPlaylist.value.tracks)
  }
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

// Apply Spotify theme on mount
onMounted(async () => {
  document.body.classList.add('spotify-theme')
  await library.init()
})
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--spotify-black);
  color: var(--spotify-text);
}

/* One UI Large Header */
.oneui-header {
  flex-shrink: 0;
  padding: 16px 20px 20px;
  background: linear-gradient(180deg, var(--spotify-gray-dark) 0%, var(--spotify-black) 100%);
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.oneui-header h1 {
  font-size: 34px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.icon-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: var(--spotify-gray);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--spotify-text);
  transition: background 0.2s;
}

.icon-btn:active {
  background: var(--spotify-gray-light);
}

/* Compact Header */
.compact-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: var(--spotify-gray-dark);
  gap: 12px;
}

.header-title {
  flex: 1;
  font-size: 18px;
  font-weight: 600;
}

.spacer {
  width: 40px;
}

/* Search */
.search-container {
  margin-top: 16px;
}

.search-input {
  width: 100%;
  padding: 14px 16px;
  border: none;
  border-radius: 8px;
  background: var(--spotify-gray);
  color: var(--spotify-text);
  font-size: 16px;
}

.search-input::placeholder {
  color: var(--spotify-text-muted);
}

/* Content */
.content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 160px; /* Space for mini player + tab bar */
}

/* Empty state */
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 14px;
  color: var(--spotify-text-muted);
  line-height: 1.4;
}

/* List items */
.list-section {
  padding: 8px 0;
}

.list-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  gap: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.list-item:active {
  background: var(--spotify-gray);
}

.list-item-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--spotify-gray);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--spotify-text-secondary);
}

.list-item-avatar.genre {
  border-radius: 8px;
  background: linear-gradient(135deg, var(--spotify-green) 0%, #1e3a5f 100%);
  color: white;
}

.list-item-content {
  flex: 1;
  min-width: 0;
}

.list-item-title {
  display: block;
  font-size: 16px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-item-subtitle {
  display: block;
  font-size: 13px;
  color: var(--spotify-text-muted);
  margin-top: 2px;
}

.list-item-arrow {
  color: var(--spotify-text-muted);
}

/* Playlist section */
.playlist-section {
  padding: 16px;
}

.create-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  padding: 16px;
  border: 2px dashed var(--spotify-gray-light);
  border-radius: 12px;
  background: transparent;
  color: var(--spotify-text-secondary);
  font-size: 15px;
  cursor: pointer;
  margin-bottom: 16px;
  transition: all 0.2s;
}

.create-btn:active {
  background: var(--spotify-gray);
  border-color: var(--spotify-green);
  color: var(--spotify-green);
}

/* Playlist view */
.playlist-view {
  padding: 20px;
}

.playlist-header-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.playlist-cover {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--spotify-gray) 0%, var(--spotify-gray-dark) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--spotify-text-secondary);
}

.playlist-meta {
  flex: 1;
}

.playlist-meta h2 {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 4px;
}

.playlist-meta p {
  font-size: 14px;
  color: var(--spotify-text-muted);
}

.play-all-btn {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--spotify-green);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: black;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
  transition: transform 0.2s, box-shadow 0.2s;
}

.play-all-btn:active {
  transform: scale(0.95);
}

/* Queue section */
.queue-section {
  padding: 16px;
}

.queue-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--spotify-text-muted);
  padding: 16px 0 8px;
}

.queue-now-playing {
  background: var(--spotify-gray);
  border-radius: 12px;
  padding: 4px;
  margin-bottom: 16px;
}

/* Bottom Tab Bar */
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  background: var(--spotify-gray-dark);
  border-top: 1px solid var(--spotify-gray);
  padding: 8px 0 max(8px, env(safe-area-inset-bottom));
  z-index: 50;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 0;
  border: none;
  background: none;
  color: var(--spotify-text-muted);
  font-size: 11px;
  cursor: pointer;
  transition: color 0.2s;
}

.tab-item.active {
  color: var(--spotify-green);
}

.tab-item svg {
  width: 24px;
  height: 24px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.modal {
  background: var(--spotify-gray);
  padding: 24px;
  border-radius: 16px;
  width: 90%;
  max-width: 320px;
}

.modal h3 {
  margin-bottom: 16px;
  font-size: 20px;
  font-weight: 700;
}

.modal-input {
  width: 100%;
  padding: 14px 16px;
  border: none;
  border-radius: 8px;
  background: var(--spotify-gray-dark);
  color: var(--spotify-text);
  font-size: 16px;
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  gap: 12px;
}

.btn-primary, .btn-secondary {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 24px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary {
  background: var(--spotify-green);
  color: black;
}

.btn-secondary {
  background: transparent;
  color: var(--spotify-text);
  border: 1px solid var(--spotify-text-muted);
}

/* Skeleton list */
.skeleton-list {
  padding: 0;
}

/* Animations */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

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
</style>
