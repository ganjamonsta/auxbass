<template>
  <div class="playlist-detail-view" v-if="playlist">
    <!-- Playlist header -->
    <div class="playlist-header">
      <div class="playlist-cover">
        <div class="cover-grid" v-if="coverImages.length">
          <img
            v-for="(cover, i) in coverImages"
            :key="i"
            :src="cover"
          />
        </div>
        <div v-else class="cover-placeholder">🎵</div>
      </div>
      <div class="playlist-info">
        <h1>{{ playlist.name }}</h1>
        <p class="meta">{{ playlist.track_count }} треков</p>
      </div>
    </div>

    <!-- Actions -->
    <div class="playlist-actions">
      <button class="play-all-btn" @click="playAll" :disabled="!playlist.tracks?.length">
        <span>▶</span>
        Слушать
      </button>
      <button class="shuffle-btn" @click="shufflePlay" :disabled="!playlist.tracks?.length">
        🔀
      </button>
      <button class="edit-btn" @click="showEditModal = true">
        ✏️
      </button>
      <button class="delete-btn" @click="showDeleteConfirm = true">
        🗑️
      </button>
    </div>

    <!-- Track list -->
    <div class="track-list" v-if="playlist.tracks?.length">
      <div
        v-for="(track, index) in playlist.tracks"
        :key="track.id"
        class="track-item"
        :class="{ playing: playerStore.currentTrack?.id === track.id }"
        @click="playTrack(track, index)"
      >
        <div class="track-cover">
          <img v-if="track.cover_url" :src="track.cover_url" :alt="track.title" />
          <div v-else class="cover-placeholder">🎵</div>
        </div>
        <div class="track-info">
          <span class="track-title">{{ track.title }}</span>
          <span class="track-artist">{{ track.artist }}</span>
        </div>
        <button class="remove-btn" @click.stop="removeTrack(track)">
          ✕
        </button>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <span class="empty-icon">🎵</span>
      <p>Плейлист пуст</p>
      <p class="hint">Добавляйте треки из библиотеки</p>
    </div>

    <!-- Edit modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal">
        <h2>Редактировать плейлист</h2>
        <input
          v-model="editName"
          type="text"
          placeholder="Название плейлиста"
          @keyup.enter="savePlaylist"
        />
        <div class="modal-actions">
          <button class="cancel-btn" @click="showEditModal = false">Отмена</button>
          <button 
            class="confirm-btn" 
            @click="savePlaylist"
            :disabled="!editName.trim()"
          >
            Сохранить
          </button>
        </div>
      </div>
    </div>

    <!-- Delete confirm -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
      <div class="modal">
        <h2>Удалить плейлист?</h2>
        <p>Вы уверены, что хотите удалить "{{ playlist.name }}"?</p>
        <div class="modal-actions">
          <button class="cancel-btn" @click="showDeleteConfirm = false">Отмена</button>
          <button class="delete-confirm-btn" @click="deletePlaylist">
            Удалить
          </button>
        </div>
      </div>
    </div>
  </div>

  <div v-else-if="loading" class="loading">
    <div class="spinner"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import api from '@/api/client'

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()

const playlist = ref(null)
const loading = ref(true)
const showEditModal = ref(false)
const showDeleteConfirm = ref(false)
const editName = ref('')

const coverImages = computed(() => {
  if (!playlist.value?.tracks) return []
  const covers = playlist.value.tracks
    .filter(t => t.cover_url)
    .slice(0, 4)
    .map(t => t.cover_url)
  return covers
})

const loadPlaylist = async () => {
  loading.value = true
  try {
    const response = await api.get(`/playlists/${route.params.id}`)
    playlist.value = response.data
    editName.value = playlist.value.name
  } finally {
    loading.value = false
  }
}

const playAll = () => {
  if (playlist.value?.tracks?.length) {
    playerStore.playTrack(playlist.value.tracks[0], playlist.value.tracks)
  }
}

const shufflePlay = () => {
  if (playlist.value?.tracks?.length) {
    const shuffled = [...playlist.value.tracks].sort(() => Math.random() - 0.5)
    playerStore.playTrack(shuffled[0], shuffled)
  }
}

const playTrack = (track, index) => {
  playerStore.playTrack(track, playlist.value.tracks, index)
}

const removeTrack = async (track) => {
  try {
    await api.delete(`/playlists/${playlist.value.id}/tracks/${track.id}`)
    playlist.value.tracks = playlist.value.tracks.filter(t => t.id !== track.id)
    playlist.value.track_count--
  } catch (error) {
    console.error('Failed to remove track:', error)
  }
}

const savePlaylist = async () => {
  if (!editName.value.trim()) return
  
  try {
    await api.patch(`/playlists/${playlist.value.id}`, {
      name: editName.value.trim()
    })
    playlist.value.name = editName.value.trim()
    showEditModal.value = false
  } catch (error) {
    console.error('Failed to update playlist:', error)
  }
}

const deletePlaylist = async () => {
  try {
    await api.delete(`/playlists/${playlist.value.id}`)
    router.push('/playlists')
  } catch (error) {
    console.error('Failed to delete playlist:', error)
  }
}

onMounted(() => {
  loadPlaylist()
})
</script>

<style scoped>
.playlist-detail-view {
  padding: 16px;
  padding-bottom: 120px;
}

.playlist-header {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.playlist-cover {
  width: 140px;
  height: 140px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-elevated);
  flex-shrink: 0;
}

.cover-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  width: 100%;
  height: 100%;
}

.cover-grid img {
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
  font-size: 48px;
}

.playlist-info {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.playlist-info h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.meta {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0;
}

.playlist-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.play-all-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--accent);
  color: #000;
  border: none;
  border-radius: 20px;
  padding: 12px 32px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}

.play-all-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.shuffle-btn,
.edit-btn,
.delete-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--bg-elevated);
  border: none;
  font-size: 18px;
  cursor: pointer;
}

.shuffle-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.track-list {
  display: flex;
  flex-direction: column;
}

.track-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.track-item:hover {
  background: var(--bg-elevated);
}

.track-item.playing {
  background: var(--bg-highlight);
}

.track-item.playing .track-title {
  color: var(--accent);
}

.track-cover {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  overflow: hidden;
  background: var(--bg-elevated);
  flex-shrink: 0;
}

.track-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.track-cover .cover-placeholder {
  font-size: 20px;
}

.track-info {
  flex: 1;
  min-width: 0;
}

.track-title {
  display: block;
  color: var(--text-primary);
  font-size: 15px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.track-artist {
  display: block;
  color: var(--text-secondary);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  font-size: 14px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
}

.track-item:hover .remove-btn {
  opacity: 1;
}

.remove-btn:hover {
  color: var(--danger);
}

.empty-state {
  text-align: center;
  padding: 48px 16px;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.hint {
  color: var(--text-tertiary);
  font-size: 14px;
  margin-top: 8px;
}

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

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.modal {
  background: var(--bg-elevated);
  border-radius: 16px;
  padding: 24px;
  width: 100%;
  max-width: 360px;
}

.modal h2 {
  margin: 0 0 16px 0;
  font-size: 20px;
  color: var(--text-primary);
}

.modal p {
  color: var(--text-secondary);
  margin: 0 0 20px 0;
}

.modal input {
  width: 100%;
  padding: 14px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text-primary);
  font-size: 16px;
  margin-bottom: 20px;
}

.modal input::placeholder {
  color: var(--text-tertiary);
}

.modal input:focus {
  outline: none;
  border-color: var(--accent);
}

.modal-actions {
  display: flex;
  gap: 12px;
}

.cancel-btn {
  flex: 1;
  padding: 12px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text-primary);
  font-weight: 500;
  cursor: pointer;
}

.confirm-btn {
  flex: 1;
  padding: 12px;
  background: var(--accent);
  border: none;
  border-radius: 10px;
  color: #000;
  font-weight: 600;
  cursor: pointer;
}

.confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.delete-confirm-btn {
  flex: 1;
  padding: 12px;
  background: var(--danger);
  border: none;
  border-radius: 10px;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}
</style>
