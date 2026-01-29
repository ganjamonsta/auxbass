<template>
  <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal edit-playlist-modal">
      <!-- Header -->
      <div class="edit-header">
        <h2>Редактирование</h2>
        <button class="close-modal-btn" @click="$emit('close')"><X :size="20" /></button>
      </div>
      
      <!-- Playlist name and settings -->
      <div class="edit-settings">
        <input
          v-model="name"
          type="text"
          placeholder="Название плейлиста"
          class="edit-name-input"
        />
        <div class="edit-options">
          <label class="checkbox-label compact">
            <input type="checkbox" v-model="isPublic" />
            <span>Публичный</span>
          </label>
        </div>
      </div>
      
      <!-- Search input -->
      <div class="search-input-wrapper">
        <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
          <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Поиск треков для добавления..."
          @input="debouncedSearch"
        />
        <div v-if="searching" class="search-spinner"></div>
      </div>
      
      <!-- Content area -->
      <div class="edit-content">
        <!-- Search results -->
        <div v-if="searchQuery && searchResults.length" class="search-results">
          <div class="section-label">Результаты поиска</div>
          <TrackSearchItem
            v-for="track in searchResults"
            :key="'search-' + track.id"
            :track="track"
            :isInPlaylist="isTrackInPlaylist(track.id)"
            :isAdding="addingTrackId === track.id"
            :isRemoving="removingTrackId === track.id"
            @add="addTrack"
            @remove="removeTrack"
          />
        </div>
        
        <div v-else-if="searchQuery && !searching" class="no-results">
          Ничего не найдено
        </div>
        
        <!-- Current playlist tracks -->
        <div v-else class="current-tracks">
          <div class="section-label">Треки в плейлисте ({{ tracks.length }})</div>
          <div v-if="tracks.length" class="tracks-editor">
            <EditableTrackItem
              v-for="(track, index) in tracks"
              :key="'edit-' + track.id"
              :track="track"
              :index="index"
              :isDragging="dragIndex === index"
              :isDragOver="dragOverIndex === index"
              @dragstart="handleDragStart($event, index)"
              @dragend="handleDragEnd"
              @dragover="handleDragOver($event, index)"
              @drop="onDrop($event, index)"
              @remove="removeTrackFromList(track, index)"
            />
          </div>
          <div v-else class="empty-playlist-hint">
            <span><Music :size="32" /></span>
            <p>Плейлист пуст</p>
            <p class="hint">Найдите треки через поиск выше</p>
          </div>
        </div>
      </div>
      
      <!-- Footer -->
      <div class="edit-footer">
        <button class="delete-playlist-btn" @click="$emit('delete')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
          </svg>
          Удалить плейлист
        </button>
        <button 
          class="save-btn" 
          @click="save"
          :disabled="!name.trim() || saving"
        >
          <span v-if="saving">Сохранение...</span>
          <span v-else>Сохранить</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { useDragReorder } from '@/composables/useDragReorder'
import api from '@/api/client'
import TrackSearchItem from './TrackSearchItem.vue'
import EditableTrackItem from './EditableTrackItem.vue'
import { X, Music } from 'lucide-vue-next'

const props = defineProps({
  show: Boolean,
  playlist: Object
})

const emit = defineEmits(['close', 'save', 'delete', 'update:tracks'])

const playerStore = usePlayerStore()

// Form state
const name = ref('')
const isPublic = ref(false)
const tracks = ref([])
const saving = ref(false)

// Search state
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const addingTrackId = ref(null)
const removingTrackId = ref(null)
let searchTimeout = null

// Drag & drop
const onTracksReorder = async (reordered) => {
  tracks.value = reordered
  emit('update:tracks', reordered)
  try {
    await api.put(`/playlists/${props.playlist.id}/reorder`, {
      track_ids: reordered.map(t => t.id)
    })
  } catch (error) {
    console.error('Failed to reorder tracks:', error)
  }
}

const { dragIndex, dragOverIndex, handleDragStart, handleDragEnd, handleDragOver, handleDrop } = useDragReorder()

const onDrop = async (event, toIndex) => {
  const reordered = await handleDrop(event, toIndex, tracks.value)
  if (reordered) {
    await onTracksReorder(reordered)
  }
}

// Watch for playlist changes
watch(() => props.playlist, (pl) => {
  if (pl) {
    name.value = pl.name || ''
    isPublic.value = pl.is_public || false
    tracks.value = [...(pl.tracks || [])]
  }
}, { immediate: true })

watch(() => props.show, (show) => {
  if (!show) {
    searchQuery.value = ''
    searchResults.value = []
  }
})

// Search
const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(search, 300)
}

const search = async () => {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  
  searching.value = true
  try {
    const [libraryRes, globalRes] = await Promise.all([
      api.get('/library', { params: { search: searchQuery.value, per_page: 20 } }),
      api.get('/tracks/global', { params: { search: searchQuery.value, per_page: 20 } })
    ])
    
    const libraryTracks = libraryRes.data.items || []
    const globalTracks = globalRes.data.items || []
    const seenIds = new Set(libraryTracks.map(t => t.id))
    const uniqueGlobal = globalTracks.filter(t => !seenIds.has(t.id))
    
    searchResults.value = [...libraryTracks, ...uniqueGlobal].slice(0, 30)
  } catch (error) {
    console.error('Failed to search:', error)
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

// Track management
const isTrackInPlaylist = (trackId) => tracks.value.some(t => t.id === trackId)

const addTrack = async (track) => {
  if (addingTrackId.value) return
  addingTrackId.value = track.id
  try {
    await api.post(`/playlists/${props.playlist.id}/tracks`, { track_id: track.id })
    tracks.value.push(track)
    emit('update:tracks', tracks.value)
  } catch (error) {
    console.error('Failed to add track:', error)
  } finally {
    addingTrackId.value = null
  }
}

const removeTrack = async (track) => {
  if (removingTrackId.value) return
  removingTrackId.value = track.id
  try {
    await api.delete(`/playlists/${props.playlist.id}/tracks/${track.id}`)
    tracks.value = tracks.value.filter(t => t.id !== track.id)
    emit('update:tracks', tracks.value)
  } catch (error) {
    console.error('Failed to remove track:', error)
  } finally {
    removingTrackId.value = null
  }
}

const removeTrackFromList = async (track, index) => {
  try {
    await api.delete(`/playlists/${props.playlist.id}/tracks/${track.id}`)
    tracks.value.splice(index, 1)
    emit('update:tracks', tracks.value)
  } catch (error) {
    console.error('Failed to remove track:', error)
  }
}

// Save
const save = async () => {
  if (!name.value.trim() || saving.value) return
  saving.value = true
  try {
    await api.put(`/playlists/${props.playlist.id}`, {
      name: name.value.trim(),
      is_public: isPublic.value
    })
    emit('save', { name: name.value.trim(), isPublic: isPublic.value })
  } catch (error) {
    console.error('Failed to save:', error)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.edit-playlist-modal {
  background: var(--bg-elevated);
  border-radius: 16px;
  height: 85vh;
  max-height: 700px;
  min-height: 400px;
  width: calc(100% - 32px);
  max-width: 480px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

@media (min-width: 600px) {
  .edit-playlist-modal {
    width: 85vw;
    max-width: 520px;
  }
}

@media (min-width: 900px) {
  .edit-playlist-modal {
    width: 50vw;
    max-width: 760px;
    height: 80vh;
    max-height: 750px;
  }
}

.edit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 20px 16px;
  border-bottom: 1px solid var(--border-color, rgba(255,255,255,0.1));
}

.edit-header h2 {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.close-modal-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--bg-highlight);
  border: none;
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit-settings {
  padding: 16px 20px;
  display: flex;
  gap: 12px;
  align-items: center;
  border-bottom: 1px solid var(--border-color, rgba(255,255,255,0.1));
}

.edit-name-input {
  flex: 1;
  padding: 10px 14px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color, rgba(255,255,255,0.1));
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 15px;
}

.edit-name-input:focus {
  outline: none;
  border-color: var(--accent);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
}

.checkbox-label.compact input[type="checkbox"] {
  appearance: none;
  width: 36px;
  height: 20px;
  background: var(--bg-highlight);
  border-radius: 10px;
  position: relative;
  cursor: pointer;
}

.checkbox-label.compact input[type="checkbox"]::before {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
}

.checkbox-label.compact input[type="checkbox"]:checked {
  background: var(--accent);
}

.checkbox-label.compact input[type="checkbox"]:checked::before {
  transform: translateX(16px);
}

.search-input-wrapper {
  position: relative;
  padding: 16px 20px;
}

.search-input-wrapper input {
  width: 100%;
  padding: 12px 40px 12px 40px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color, rgba(255,255,255,0.1));
  border-radius: 10px;
  color: var(--text-primary);
  font-size: 15px;
}

.search-icon {
  position: absolute;
  left: 32px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-tertiary);
}

.search-spinner {
  position: absolute;
  right: 32px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  border: 2px solid var(--bg-highlight);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.edit-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 20px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
  padding-top: 8px;
}

.search-results, .current-tracks {
  padding-bottom: 16px;
}

.tracks-editor {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.no-results {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  color: var(--text-tertiary);
}

.empty-playlist-hint {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-tertiary);
}

.empty-playlist-hint span {
  font-size: 36px;
  display: block;
  margin-bottom: 12px;
}

.empty-playlist-hint p { margin: 0; }
.empty-playlist-hint .hint { font-size: 13px; margin-top: 4px; }

.edit-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color, rgba(255,255,255,0.1));
  background: var(--bg-elevated);
}

.delete-playlist-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  background: transparent;
  border: 1px solid var(--text-tertiary);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.delete-playlist-btn:hover {
  border-color: var(--danger, #e53935);
  color: var(--danger, #e53935);
}

.save-btn {
  padding: 12px 24px;
  background: var(--accent);
  border: none;
  border-radius: 8px;
  color: #000;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes spin {
  to { transform: translateY(-50%) rotate(360deg); }
}
</style>
