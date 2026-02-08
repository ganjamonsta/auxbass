<template>
  <div class="library-playlists">
    <!-- Info banner for global scope -->
    <InfoBanner
      v-if="scope === 'global'"
      :icon="FileText"
      title="Общая коллекция плейлистов"
      description="Все плейлисты, доступные в системе"
    />

    <!-- Actions header -->
    <div class="actions-header">
      <div class="stats">
        {{ filteredPlaylists.length }} плейлистов
      </div>
      <button class="create-btn" @click="handleCreatePlaylist">
        <Plus :size="16" /> Создать
      </button>
    </div>

    <!-- Loading state with skeletons -->
    <div v-if="loading" class="playlists-grid">
      <GridSkeleton v-for="i in 9" :key="i" type="playlist" />
    </div>

    <!-- Playlists grid -->
    <MediaGrid
      v-else
      type="playlist"
      :items="filteredPlaylists"
      :loading="false"
      @click="goToPlaylist"
      @contextmenu="handleContextMenu"
    >
      <template #prepend-grid>
        <!-- Liked tracks special card -->
        <div class="playlist-card liked-card" @click="goToLiked">
          <div class="playlist-cover liked-cover">
            <span class="liked-icon"><Heart :size="24" class="heart-icon" /></span>
          </div>
          <div class="playlist-name">Понравившиеся</div>
          <div class="playlist-meta">{{ likedCount }} треков</div>
        </div>
      </template>

      <template #empty>
        <div class="empty-state">
          <span class="empty-icon"><FileText :size="48" /></span>
          <h3 v-if="searchQuery">Плейлисты не найдены</h3>
          <template v-else>
            <p>У вас пока нет плейлистов</p>
            <button class="create-first-btn" @click="handleCreatePlaylist">
              Создать плейлист
            </button>
          </template>
        </div>
      </template>
    </MediaGrid>

    <!-- Create modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <h2>Новый плейлист</h2>
        <input
          v-model="newPlaylistName"
          type="text"
          placeholder="Название плейлиста"
          ref="nameInput"
          @keyup.enter="createPlaylist"
        />
        <div class="modal-actions">
          <button type="button" class="cancel-btn" @click="closeModal">Отмена</button>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { useAuthStore } from '@/stores/auth'
import { useContextMenu } from '@/composables/useContextMenu'
import api from '@/api/client'
import { Heart, Plus, FileText } from 'lucide-vue-next'
import MediaGrid from '@/components/MediaGrid.vue'
import GridSkeleton from '@/components/GridSkeleton.vue'
import InfoBanner from '@/components/InfoBanner.vue'

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

const playlists = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const newPlaylistName = ref('')
const nameInput = ref(null)
const likedCount = ref(0)

// Filtered playlists based on search
const filteredPlaylists = computed(() => {
  if (!props.searchQuery) return playlists.value
  const query = props.searchQuery.toLowerCase()
  return playlists.value.filter(p => p.name.toLowerCase().includes(query))
})

// Context menu
const handleContextMenu = ({ item, event }) => {
  openMenu('playlist', item, props.scope, event)
}

// Handle create playlist - check for channel
const handleCreatePlaylist = () => {
  if (!authStore.hasChannel) {
    authStore.promptChannelSetup()
    return
  }
  showCreateModal.value = true
}

// Load playlists — with cache busting for covers
const loadPlaylists = async () => {
  loading.value = true
  try {
    const response = await api.get('/playlists')
    const raw = response.data.items || response.data
    const stamp = Date.now()
    const bust = (url) => {
      if (!url) return null
      const sep = url.includes('?') ? '&' : '?'
      return `${url}${sep}_cb=${stamp}`
    }
    playlists.value = raw.map(p => ({
      ...p,
      cover_url: bust(p.cover_url),
      covers: (p.covers || (p.cover_url ? [p.cover_url] : [])).map(bust)
    }))

    // Update library store cache
    libraryStore.playlists = playlists.value
  } finally {
    loading.value = false
  }
}

// Load liked count
const loadLikedCount = async () => {
  try {
    await libraryStore.fetchLikedTracks()
    likedCount.value = libraryStore.likedTracks?.length || 0
  } catch (e) {
    console.error('Failed to load liked count:', e)
  }
}

// Navigation
const goToPlaylist = (playlist) => {
  router.push(`/playlist/${playlist.id}`)
}

const goToLiked = () => {
  router.push('/liked')
}

// Modal
const closeModal = () => {
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
    playlists.value.unshift(response.data)
    closeModal()
    router.push(`/playlist/${response.data.id}`)
  } catch (error) {
    console.error('Failed to create playlist:', error)
  }
}

// Sync cover updates from libraryStore
watch(
  () => libraryStore.playlists,
  (storePlaylists) => {
    if (!storePlaylists?.length || !playlists.value?.length) return
    for (const sp of storePlaylists) {
      const local = playlists.value.find(p => p.id === sp.id)
      if (!local) continue
      if (JSON.stringify(sp.covers) !== JSON.stringify(local.covers)) {
        local.covers = sp.covers
      }
      if (sp.name !== local.name) {
        local.name = sp.name
      }
    }
  },
  { deep: true }
)

// Focus input when modal opens
watch(showCreateModal, (val) => {
  if (val) {
    nextTick(() => nameInput.value?.focus())
  }
})

onMounted(() => {
  loadPlaylists()
  loadLikedCount()
})

// Reload on keep-alive re-enter
onActivated(() => {
  loadPlaylists()
})

// Expose for parent reset
defineExpose({
  reset: () => loadPlaylists(),
  refresh: () => loadPlaylists()
})
</script>

<style scoped>
.library-playlists {
  padding-bottom: 20px;
}

.actions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 12px;
}

.stats {
  color: var(--text-secondary);
  font-size: 14px;
}

.create-btn {
  padding: 10px 16px;
  background: var(--accent);
  border: none;
  border-radius: 20px;
  color: #000;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, opacity 0.2s;
  width: auto !important;
  max-width: fit-content;
  display: flex;
  align-items: center;
  gap: 4px;
}

.create-btn:hover {
  opacity: 0.9;
}

.create-btn:active {
  transform: scale(0.97);
}

/* Liked card */
.liked-card {
  cursor: pointer;
}

.liked-cover {
  background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
  display: flex;
  align-items: center;
  justify-content: center;
}

.liked-icon {
  font-size: 40px;
}

.playlist-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 2px;
}

.playlist-meta {
  font-size: 11px;
  color: var(--text-secondary);
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

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
</style>
