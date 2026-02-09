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
        <SearchBar
          v-model="searchQuery"
          placeholder="Поиск треков для добавления..."
          :loading="searching"
          @input="debouncedSearch"
          @clear="clearSearch"
        />
      </div>
      
      <!-- Content area -->
      <div class="edit-content" ref="scrollContentRef">
        <!-- Search results -->
        <div v-if="searchQuery && hasAnyResults" class="search-results">
          <!-- Section: My Library -->
          <template v-if="libraryResults.length">
            <div class="section-label">Моя библиотека</div>
            <TrackSearchItem
              v-for="track in libraryResults"
              :key="'lib-' + track.id"
              :track="track"
              :isInPlaylist="isTrackInPlaylist(track.id)"
              :isAdding="addingTrackId === track.id"
              :isRemoving="removingTrackId === track.id"
              @add="addTrack"
              @remove="removeTrack"
            />
          </template>

          <!-- Section: Friends -->
          <template v-if="friendsResults.length">
            <div class="section-label friends-label"><Users :size="14" /> У друзей</div>
            <TrackSearchItem
              v-for="track in friendsResults"
              :key="'friend-' + track.id"
              :track="track"
              :isInPlaylist="isTrackInPlaylist(track.id)"
              :isAdding="addingTrackId === track.id"
              :isRemoving="removingTrackId === track.id"
              @add="addTrack"
              @remove="removeTrack"
            />
          </template>

          <!-- Loading friends -->
          <div v-if="friendsLoading" class="search-section-loading">
            <div class="search-spinner-inline"></div>
            <span>Поиск у друзей...</span>
          </div>

          <!-- Section: Global -->
          <template v-if="globalResults.length">
            <div class="section-label global-label"><Globe :size="14" /> Общая сеть</div>
            <TrackSearchItem
              v-for="track in globalResults"
              :key="'global-' + track.id"
              :track="track"
              :isInPlaylist="isTrackInPlaylist(track.id)"
              :isAdding="addingTrackId === track.id"
              :isRemoving="removingTrackId === track.id"
              @add="addTrack"
              @remove="removeTrack"
            />
          </template>

          <!-- Loading global -->
          <div v-if="globalLoading" class="search-section-loading">
            <div class="search-spinner-inline"></div>
            <span>Поиск в общей сети...</span>
          </div>
        </div>
        
        <div v-else-if="searchQuery && !searching && !friendsLoading && !globalLoading" class="no-results">
          Ничего не найдено
        </div>
        
        <!-- Current playlist tracks -->
        <div v-else class="current-tracks">
          <div class="section-label">Треки в плейлисте ({{ tracks.length }})</div>
          <div v-if="tracks.length" class="tracks-editor">
            <EditableTrackItem
              v-for="(track, index) in virtualTracks"
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
            <!-- Infinite scroll trigger -->
            <div ref="loadTriggerRef" v-if="hasMoreTracks" class="load-trigger"></div>
            <!-- Loading skeletons -->
            <TrackSkeleton v-for="i in loadingSkeletonCount" :key="'skel-' + i" />
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
        <button 
          class="delete-playlist-btn" 
          :class="{ 'confirm-state': deleteConfirmPending }"
          @click="handleDeleteClick"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
          </svg>
          <span class="delete-text">{{ deleteConfirmPending ? 'Точно удалить?' : 'Удалить плейлист' }}</span>
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
import { ref, computed, watch, nextTick } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useDragReorder } from '@/composables/useDragReorder'
import { useTrackSearch } from '@/composables/useTrackSearch'
import { useVirtualScroll } from '@/composables/useVirtualScroll'
import { playlistsApi } from '@/api/client'
import api from '@/api/client'
import TrackSearchItem from './TrackSearchItem.vue'
import EditableTrackItem from './EditableTrackItem.vue'
import TrackSkeleton from './TrackSkeleton.vue'
import SearchBar from './ui/SearchBar.vue'
import { X, Music, Users, Globe } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'

const props = defineProps({
  show: Boolean,
  playlist: Object
})

const emit = defineEmits(['close', 'save', 'delete', 'update:tracks'])

const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const authStore = useAuthStore()
const uiStore = useUIStore()

// Form state
const name = ref('')
const isPublic = ref(false)
const tracks = ref([])
const saving = ref(false)

// Infinite scroll for playlist tracks
const scrollContentRef = ref(null)

const {
  items: virtualTracks,
  hasMore: hasMoreTracks,
  loadTriggerRef,
  loadingMore: virtualLoadingMore,
  loadingSkeletonCount,
  reset: resetVirtualScroll,
  clear: clearVirtualScroll,
} = useVirtualScroll({
  fetchFn: async ({ offset, limit }) => ({
    items: tracks.value.slice(offset, offset + limit),
    total: tracks.value.length
  }),
  limit: 50,
  immediate: false,
  scrollContainer: scrollContentRef,
  skeletonCount: 6
})

// Delete confirmation (double-click pattern)
const deleteConfirmPending = ref(false)
let deleteConfirmTimer = null

const handleDeleteClick = () => {
  if (deleteConfirmPending.value) {
    // Second click — confirm deletion
    clearTimeout(deleteConfirmTimer)
    deleteConfirmPending.value = false
    emit('delete')
  } else {
    // First click — enter confirm state
    deleteConfirmPending.value = true
    deleteConfirmTimer = setTimeout(() => {
      deleteConfirmPending.value = false
    }, 3000)
  }
}

// Search (unified three-tier: library → friends → global)
const {
  searchQuery,
  libraryResults,
  friendsResults,
  globalResults,
  isSearching: searching,
  isFriendsLoading: friendsLoading,
  isGlobalLoading: globalLoading,
  hasAnyResults,
  debouncedSearch,
  clearSearch,
} = useTrackSearch({ perPage: 20 })

const addingTrackId = ref(null)
const removingTrackId = ref(null)

// Drag & drop
const onTracksReorder = async (reordered) => {
  tracks.value = reordered
  emit('update:tracks', reordered)
  nextTick(() => resetVirtualScroll())
  try {
    await api.put(`/playlists/${props.playlist.id}/reorder`, {
      track_ids: reordered.map(t => t.id)
    })
    await libraryStore.notifyPlaylistChange(props.playlist.id)
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
    if (props.show) {
      nextTick(() => resetVirtualScroll())
    }
  }
}, { immediate: true })

watch(() => props.show, (show) => {
  if (show && tracks.value.length) {
    nextTick(() => resetVirtualScroll())
  }
  if (!show) {
    clearSearch()
    clearVirtualScroll()
    deleteConfirmPending.value = false
    if (deleteConfirmTimer) clearTimeout(deleteConfirmTimer)
  }
})

// Track management
const isTrackInPlaylist = (trackId) => tracks.value.some(t => t.id === trackId)

const addTrack = async (track) => {
  if (addingTrackId.value) return
  addingTrackId.value = track.id
  try {
    await playlistsApi.addTrack(props.playlist.id, track.id)
    tracks.value.push(track)
    emit('update:tracks', tracks.value)
    nextTick(() => resetVirtualScroll())
    await libraryStore.notifyPlaylistChange(props.playlist.id)
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
    await playlistsApi.removeTrack(props.playlist.id, track.id)
    tracks.value = tracks.value.filter(t => t.id !== track.id)
    emit('update:tracks', tracks.value)
    nextTick(() => resetVirtualScroll())
    await libraryStore.notifyPlaylistChange(props.playlist.id)
  } catch (error) {
    console.error('Failed to remove track:', error)
  } finally {
    removingTrackId.value = null
  }
}

const removeTrackFromList = async (track, index) => {
  try {
    await playlistsApi.removeTrack(props.playlist.id, track.id)
    const idx = tracks.value.findIndex(t => t.id === track.id)
    if (idx !== -1) tracks.value.splice(idx, 1)
    emit('update:tracks', tracks.value)
    nextTick(() => resetVirtualScroll())
    await libraryStore.notifyPlaylistChange(props.playlist.id)
  } catch (error) {
    console.error('Failed to remove track:', error)
  }
}

// Save
const save = async () => {
  if (!name.value.trim() || saving.value) return
  saving.value = true
  try {
    const response = await libraryStore.updatePlaylist(props.playlist.id, {
      name: name.value.trim(),
      is_public: isPublic.value
    })
    
    emit('save', { 
      name: name.value.trim(), 
      isPublic: isPublic.value, 
      covers: response?.covers || []
    })
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

/* Mobile fullscreen mode */
@media (max-width: 480px) {
  .modal-overlay {
    padding: 0;
  }
  
  .edit-playlist-modal {
    width: 100%;
    height: 100%;
    max-height: none;
    min-height: 100%;
    border-radius: 0;
  }
}

/* Small height screens - compact mode */
@media (max-height: 600px) {
  .modal-overlay {
    padding: 0;
  }
  
  .edit-playlist-modal {
    height: 100%;
    max-height: none;
    min-height: 100%;
    border-radius: 0;
  }
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
  padding: 20px;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color, rgba(255,255,255,0.1));
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 15px;
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
  padding: 16px 20px;
}

.search-input-wrapper :deep(.search-bar) {
  margin-bottom: 0;
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

.section-label.friends-label,
.section-label.global-label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 16px;
}

.search-section-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 0;
  color: var(--text-tertiary);
  font-size: 13px;
}

.search-spinner-inline {
  width: 16px;
  height: 16px;
  border: 2px solid var(--bg-highlight);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.tracks-editor {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.load-trigger {
  height: 1px;
  width: 100%;
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

.delete-playlist-btn.confirm-state {
  border-color: var(--danger, #e53935);
  color: #fff;
  background: var(--danger, #e53935);
  animation: pulse-danger 0.3s ease;
}

@keyframes pulse-danger {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
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
  to { transform: rotate(360deg); }
}

/* Mobile compact styles */
@media (max-width: 480px) {
  .edit-header {
    padding: 12px 12px 10px;
  }
  
  .edit-header h2 {
    font-size: 16px;
  }
  
  .edit-settings {
    padding: 12px;
    margin: 0 12px;
    gap: 10px;
  }
  
  .search-input-wrapper {
    padding: 10px 12px;
  }
  
  .edit-content {
    padding: 0 12px;
  }
  
  .edit-footer {
    padding: 12px;
    gap: 8px;
  }
  
  .delete-playlist-btn {
    padding: 8px 10px;
    font-size: 12px;
  }
  
  .save-btn {
    padding: 10px 18px;
    font-size: 13px;
  }
}

/* Very small screens (old phones) */
@media (max-width: 360px) {
  .edit-settings {
    flex-wrap: wrap;
    padding: 10px;
    margin: 0 8px;
  }
  
  .edit-name-input {
    order: 2;
    width: 100%;
    flex: none;
  }
  
  .edit-options {
    order: 3;
    margin-left: auto;
  }
  
  .edit-header {
    padding: 10px 8px;
  }
  
  .edit-content {
    padding: 0 8px;
  }
  
  .edit-footer {
    padding: 10px 8px;
  }
  
  .delete-playlist-btn .delete-text {
    display: none;
  }
}
</style>
