<template>
  <div class="library-playlists">
    <!-- Info banner for global scope -->
    <InfoBanner
      v-if="scope === 'global'"
      :icon="FileText"
      title="Общая коллекция плейлистов"
      description="Все плейлисты, доступные в системе"
    />

    <!-- Liked tracks card (library scope only) -->
    <div v-if="scope === 'library'" class="liked-section" @click="goToLiked">
      <div class="liked-card-inline">
        <div class="liked-icon-box">
          <Heart :size="20" fill="currentColor" />
        </div>
        <div class="liked-info">
          <span class="liked-title">Понравившиеся</span>
          <span class="liked-count">{{ likedCount }} треков</span>
        </div>
      </div>
    </div>

    <!-- Sort options (Stats + SortChips + Action) -->
    <div class="sort-options">
      <div class="stats">
        {{ virtualGridRef?.total ?? 0 }} плейлистов
      </div>
      <div class="sort-actions">
        <SortChips
          :currentOption="currentOption"
          :sortOrder="sortOrder"
          @next="onNextSort"
          @toggle-order="onToggleOrder"
        />
        <button v-if="scope === 'global'" class="action-btn" @click="showManageModal = true">
          <Plus :size="16" /> Добавить
        </button>
        <button v-else class="action-btn" @click="handleCreatePlaylist">
          <Plus :size="16" /> Создать
        </button>
      </div>
    </div>

    <!-- Spotify-style virtual grid -->
    <VirtualGrid
      ref="virtualGridRef"
      type="playlist"
      :fetchFn="fetchPlaylists"
      :pageSize="30"
      :skeletonCount="12"
      @click="goToPlaylist"
      @play="shufflePlaylist"
      @contextmenu="handleContextMenu"
    >
      <template #empty>
        <span class="empty-icon"><FileText :size="48" /></span>
        <h3 v-if="searchQuery">Плейлисты не найдены</h3>
        <template v-else>
          <p>{{ scope === 'global' ? 'Нет публичных плейлистов' : 'У вас пока нет плейлистов' }}</p>
          <button v-if="scope !== 'global'" class="create-first-btn" @click="handleCreatePlaylist">
            Создать плейлист
          </button>
        </template>
      </template>
    </VirtualGrid>

    <!-- Create modal (library scope) -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeCreateModal">
      <div class="modal">
        <h2>Новый плейлист</h2>
        <input
          v-model="newPlaylistName"
          type="text"
          placeholder="Название плейлиста"
          ref="createNameInput"
          @keyup.enter="createPlaylist"
        />
        <div class="modal-actions">
          <button type="button" class="cancel-btn" @click="closeCreateModal">Отмена</button>
          <button 
            type="button"
            class="confirm-btn" 
            @click="createPlaylist"
            :disabled="!newPlaylistName.trim()"
          >
            Создать
          </button>
        </div>
      </div>
    </div>

    <!-- Manage modal (global scope) — toggle public status -->
    <div v-if="showManageModal" class="modal-overlay" @click.self="closeManageModal">
      <div class="modal manage-modal">
        <h2>Добавить в коллекции</h2>
        <p class="hint-text">Выберите плейлисты для отображения в общей коллекции</p>
        
        <div class="playlists-manage-list">
          <div 
            v-for="playlist in ownPlaylists" 
            :key="playlist.id"
            class="playlist-manage-item"
            @click="togglePlaylistStatus(playlist)"
          >
            <div class="playlist-manage-info">
              <div class="playlist-manage-cover">
                <img v-if="playlist.covers?.length" :src="getCoverUrl(playlist.covers[0], CoverSize.SMALL)" />
                <div v-else class="playlist-manage-placeholder"><Music :size="20" /></div>
              </div>
              <div class="playlist-manage-text">
                <div class="playlist-manage-name">{{ playlist.name }}</div>
                <div class="playlist-manage-count">{{ playlist.track_count }} треков</div>
              </div>
            </div>
            <label class="checkbox-label compact">
              <input 
                type="checkbox" 
                :checked="playlist.is_public"
                @click.stop="togglePlaylistStatus(playlist)"
              />
            </label>
          </div>
        </div>
        
        <div class="modal-actions">
          <button class="cancel-btn" @click="closeManageModal">Закрыть</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import { useUIStore } from '@/stores/ui'
import { useSort } from '@/composables'
import { useContextMenu } from '@/composables/useContextMenu'
import SortChips from '@/components/SortChips.vue'
import VirtualGrid from '@/components/VirtualGrid.vue'
import InfoBanner from '@/components/InfoBanner.vue'
import api from '@/api/client'
import { Heart, Plus, FileText, Music } from 'lucide-vue-next'
import { getCoverUrl, CoverSize } from '@/utils'

// Universal context menu
const { openMenu } = useContextMenu()

const props = defineProps({
  searchQuery: {
    type: String,
    default: ''
  },
  scope: {
    type: String,
    default: 'library',
    validator: v => ['library', 'global'].includes(v)
  }
})

const router = useRouter()
const libraryStore = useLibraryStore()
const authStore = useAuthStore()
const playerStore = usePlayerStore()
const uiStore = useUIStore()
const virtualGridRef = ref(null)

// Sort state (persisted to localStorage) - separate key per scope
const sortStorageKey = computed(() => 
  props.scope === 'global' ? 'global-playlists-sort' : 'library-playlists-sort'
)

const { 
  sortBy, 
  sortOrder, 
  currentOption, 
  nextSort, 
  toggleOrder 
} = useSort(sortStorageKey.value, 'playlists', { sortBy: 'created_at', sortOrder: 'desc' })

// Liked tracks count (library scope only)
const likedCount = ref(0)

// Create modal state
const showCreateModal = ref(false)
const newPlaylistName = ref('')
const createNameInput = ref(null)

// Manage modal state (global scope)
const showManageModal = ref(false)
const ownPlaylists = ref([])

// Fetch function for virtual grid
const fetchPlaylists = async ({ offset, limit }) => {
  const params = { 
    offset, 
    limit,
    sort_by: sortBy.value,
    sort_order: sortOrder.value
  }
  if (props.searchQuery) {
    params.search = props.searchQuery
  }
  const endpoint = props.scope === 'global' ? '/playlists/global' : '/playlists'
  const response = await api.get(endpoint, { params })
  return response.data
}

// Sort handlers
const onNextSort = () => {
  nextSort()
  virtualGridRef.value?.reset()
}

const onToggleOrder = () => {
  toggleOrder()
  virtualGridRef.value?.reset()
}

// Watch search query to reload
watch(() => props.searchQuery, () => {
  virtualGridRef.value?.reset()
})

// Navigation
const goToPlaylist = (playlist) => {
  router.push(`/playlist/${playlist.id}`)
}

const goToLiked = () => {
  router.push('/liked')
}

// Context menu
const handleContextMenu = ({ item, event }) => {
  openMenu('playlist', item, props.scope, event)
}

// Shuffle playlist
const shufflePlaylist = async (playlist) => {
  try {
    await playerStore.playShuffleAll('playlist', playlist.id)
  } catch (error) {
    console.error('Failed to shuffle playlist:', error)
  }
}

// === Create modal (library scope) ===
const handleCreatePlaylist = () => {
  if (!authStore.hasChannel) {
    authStore.promptChannelSetup()
    return
  }
  showCreateModal.value = true
}

const closeCreateModal = () => {
  showCreateModal.value = false
  newPlaylistName.value = ''
}

const createPlaylist = async () => {
  if (!newPlaylistName.value.trim()) return
  try {
    const response = await api.post('/playlists', {
      name: newPlaylistName.value.trim(),
      is_public: props.scope === 'global'
    })
    closeCreateModal()
    router.push(`/playlist/${response.data.id}`)
    // Refresh grid after creating
    virtualGridRef.value?.reset()
  } catch (error) {
    console.error('Failed to create playlist:', error)
  }
}

watch(showCreateModal, (val) => {
  if (val) nextTick(() => createNameInput.value?.focus())
})

// === Manage modal (global scope) ===
const loadOwnPlaylists = async () => {
  try {
    const response = await api.get('/playlists/manage/all')
    ownPlaylists.value = response.data.items || response.data || []
  } catch (error) {
    console.error('Failed to load own playlists:', error)
  }
}

const closeManageModal = () => {
  showManageModal.value = false
}

const togglePlaylistStatus = async (playlist) => {
  try {
    const newStatus = !playlist.is_public
    await api.put(`/playlists/${playlist.id}`, { is_public: newStatus })
    playlist.is_public = newStatus
    
    // Update in library store
    const libraryPlaylist = libraryStore.playlists.find(p => p.id === playlist.id)
    if (libraryPlaylist) {
      libraryPlaylist.is_public = newStatus
    }
    
    uiStore.toast.success('Сохранено', `Плейлист ${newStatus ? 'добавлен в коллекции' : 'удален из коллекций'}`)
    
    // Refresh grid to reflect changes
    virtualGridRef.value?.reset()
  } catch (error) {
    console.error('Failed to toggle playlist status:', error)
    uiStore.toast.error('Ошибка', 'Не удалось обновить статус')
  }
}

watch(showManageModal, (val) => {
  if (val) loadOwnPlaylists()
})

// Load liked count for library scope
const loadLikedCount = async () => {
  if (props.scope !== 'library') return
  try {
    await libraryStore.fetchLikedTracks()
    likedCount.value = libraryStore.likedTracks?.length || 0
  } catch (e) {
    console.error('Failed to load liked count:', e)
  }
}

onMounted(() => {
  loadLikedCount()
})

// Watch scope changes to reload
watch(() => props.scope, () => {
  virtualGridRef.value?.reset()
})

// Expose for parent
defineExpose({
  reset: () => virtualGridRef.value?.reset(),
  refresh: () => virtualGridRef.value?.reset()
})
</script>

<style scoped>
.library-playlists {
  padding-bottom: 20px;
}

.sort-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 12px;
}

.sort-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stats {
  color: var(--text-secondary);
  font-size: 14px;
}

.action-btn {
  padding: 8px 14px;
  background: var(--accent);
  border: none;
  border-radius: 20px;
  color: #000;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, opacity 0.2s;
  width: auto !important;
  max-width: fit-content;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.action-btn:hover {
  opacity: 0.9;
}

.action-btn:active {
  transform: scale(0.97);
}

/* Liked card (inline, above grid) */
.liked-section {
  margin-bottom: 16px;
  cursor: pointer;
}

.liked-card-inline {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(168, 85, 247, 0.1));
  border-radius: 12px;
  transition: background 0.2s;
}

.liked-card-inline:hover {
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.25), rgba(168, 85, 247, 0.15));
}

.liked-icon-box {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.liked-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.liked-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.liked-count {
  font-size: 12px;
  color: var(--text-secondary);
}

/* Liked card -- end above -- */

/* Create first button */
.create-first-btn {
  margin-top: 16px;
  background: var(--accent);
  color: #000;
  border: none;
  border-radius: 20px;
  padding: 12px 24px;
  font-weight: 600;
  cursor: pointer;
}

/* Modal */
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
  background: var(--bg-elevated, var(--c-bg-2));
  border-radius: 16px;
  padding: 24px;
  width: 100%;
  max-width: 360px;
}

.modal h2 {
  margin: 0 0 20px 0;
  font-size: 20px;
  color: var(--text-primary);
}

.modal input {
  width: 100%;
  padding: 14px 16px;
  background: var(--bg-primary, var(--c-bg-1));
  border: 1px solid var(--border-color, var(--c-bg-3));
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
  border-radius: 10px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid var(--border-color, var(--c-bg-3));
  background: transparent;
  color: var(--text-primary);
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

/* Manage modal */
.manage-modal {
  max-width: 480px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.hint-text {
  font-size: 12px;
  color: var(--c-text-3, var(--text-tertiary));
  margin-bottom: 16px;
}

.playlists-manage-list {
  flex: 1;
  overflow-y: auto;
  margin: 16px 0;
  max-height: 50vh;
}

.playlist-manage-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: var(--c-bg-3, var(--bg-elevated));
  border-radius: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.playlist-manage-item:hover {
  background: var(--c-bg-4, var(--bg-highlight));
}

.playlist-manage-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.playlist-manage-cover {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--c-bg-1, var(--bg-primary));
  flex-shrink: 0;
}

.playlist-manage-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.playlist-manage-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-3, var(--text-tertiary));
}

.playlist-manage-text {
  flex: 1;
  min-width: 0;
}

.playlist-manage-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text-1, var(--text-primary));
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.playlist-manage-count {
  font-size: 13px;
  color: var(--c-text-3, var(--text-tertiary));
  margin-top: 2px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--c-text-2, var(--text-secondary));
  font-size: 14px;
  margin-bottom: 12px;
  cursor: pointer;
  user-select: none;
}

.checkbox-label input[type="checkbox"] {
  appearance: none;
  -webkit-appearance: none;
  width: 44px;
  height: 24px;
  background: var(--c-bg-3, var(--bg-elevated));
  border-radius: 12px;
  position: relative;
  cursor: pointer;
  transition: background 0.2s;
}

.checkbox-label input[type="checkbox"]::before {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
}

.checkbox-label input[type="checkbox"]:checked {
  background: var(--accent);
}

.checkbox-label input[type="checkbox"]:checked::before {
  transform: translateX(20px);
}

.checkbox-label.compact {
  margin-bottom: 0;
  gap: 0;
}
</style>
