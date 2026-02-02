<template>
  <Teleport to="body">
    <Transition name="fade">
      <div 
        v-if="isOpen" 
        class="menu-overlay" 
        :class="{ desktop: isDesktop }" 
        @click="closeMenu"
        @contextmenu.prevent="closeMenu"
      >
        <Transition :name="isDesktop ? 'scale' : 'slide-up'">
          <div 
            v-if="isOpen" 
            ref="menuSheet"
            class="menu-sheet" 
            :class="{ desktop: isDesktop }"
            :style="isDesktop && adjustedPosition.x ? { left: adjustedPosition.x + 'px', top: adjustedPosition.y + 'px' } : {}"
            @click.stop
          >
            <!-- Header -->
            <div class="menu-header">
              <div class="menu-cover" :style="coverStyle">
                <component :is="coverIcon" v-if="!hasCover" :size="20" />
              </div>
              <div class="menu-info">
                <div class="menu-title">{{ title }}</div>
                <div class="menu-subtitle">{{ subtitle }}</div>
              </div>
              <button class="menu-close" @click="closeMenu">
                <X :size="20" />
              </button>
            </div>

            <!-- Menu Items -->
            <div class="menu-items">
              <!-- ═══ TRACK MENU ═══ -->
              <template v-if="menuType === 'track'">
                <!-- Navigation -->
                <button v-if="hasArtist" class="menu-item" @click="exec('goToArtist')">
                  <User :size="18" />
                  <span>Перейти к артисту</span>
                </button>
                <button v-if="hasAlbum" class="menu-item" @click="exec('goToAlbum')">
                  <Disc3 :size="18" />
                  <span>Перейти к альбому</span>
                </button>
                <div v-if="hasArtist || hasAlbum" class="menu-divider" />

                <!-- Queue (hide for current track in player) -->
                <template v-if="menuContext !== 'player'">
                  <button class="menu-item" @click="exec('playNext')">
                    <Play :size="18" fill="currentColor" />
                    <span>Включить следующим</span>
                  </button>
                  <button class="menu-item" @click="exec('addToQueue')">
                    <ListMusic :size="18" />
                    <span>Добавить в очередь</span>
                  </button>
                </template>

                <button class="menu-item" @click="exec('addToPlaylist')">
                  <Plus :size="18" />
                  <span>Добавить в плейлист</span>
                </button>
                <div class="menu-divider" />

                <button class="menu-item" @click="exec('edit')">
                  <Pencil :size="18" />
                  <span>Редактировать</span>
                </button>
                <button class="menu-item" @click="exec('download')">
                  <Download :size="18" />
                  <span>Скачать в Telegram</span>
                </button>
                <button v-if="hasHDVersion" class="menu-item" @click="exec('downloadHD')">
                  <Disc3 :size="18" />
                  <span>Скачать HD версию</span>
                </button>
                <button v-if="isTrackHD" class="menu-item" @click="exec('downloadTrackHD')">
                  <Download :size="18" />
                  <span>Скачать HD файл</span>
                </button>
                <div class="menu-divider" />

                <!-- Remove from playlist (in playlist context) -->
                <button v-if="inPlaylistContext" class="menu-item danger" @click="exec('removeFromPlaylist', playlistId)">
                  <Minus :size="18" />
                  <span>Убрать из плейлиста</span>
                </button>

                <!-- Owner can delete -->
                <button v-if="isTrackOwner" class="menu-item danger" @click="exec('delete')">
                  <Trash2 :size="18" />
                  <span>Удалить полностью</span>
                </button>
                <!-- In library but not owner - remove from library -->
                <button v-else-if="isInLibrary" class="menu-item" @click="exec('removeFromLibrary')">
                  <Minus :size="18" />
                  <span>Убрать из библиотеки</span>
                </button>
                <!-- Not in library - add -->
                <button v-else class="menu-item" @click="exec('addToLibrary')">
                  <Plus :size="18" />
                  <span>Добавить в библиотеку</span>
                </button>
              </template>

              <!-- ═══ PLAYLIST MENU ═══ -->
              <template v-else-if="menuType === 'playlist'">
                <button class="menu-item" @click="exec('open')">
                  <FolderOpen :size="18" />
                  <span>Открыть</span>
                </button>
                <button class="menu-item" @click="exec('playAll')">
                  <Play :size="18" fill="currentColor" />
                  <span>Воспроизвести все</span>
                </button>
                <button class="menu-item" @click="exec('shuffle')">
                  <Shuffle :size="18" />
                  <span>Перемешать</span>
                </button>
                <button class="menu-item" @click="exec('addToQueue')">
                  <ListMusic :size="18" />
                  <span>Добавить в очередь</span>
                </button>

                <!-- Only for user playlists that user owns (not auto-albums) -->
                <template v-if="!isAutoAlbum && isPlaylistOwner">
                  <div class="menu-divider" />
                  <button class="menu-item" @click="exec('edit')">
                    <Pencil :size="18" />
                    <span>Редактировать</span>
                  </button>
                </template>
              </template>

              <!-- ═══ ALBUM MENU ═══ -->
              <template v-else-if="menuType === 'album'">
                <button class="menu-item" @click="exec('open')">
                  <FolderOpen :size="18" />
                  <span>Открыть альбом</span>
                </button>
                <button class="menu-item" @click="exec('playAll')">
                  <Play :size="18" fill="currentColor" />
                  <span>Воспроизвести все</span>
                </button>
                <button class="menu-item" @click="exec('shuffle')">
                  <Shuffle :size="18" />
                  <span>Перемешать</span>
                </button>
                <button class="menu-item" @click="exec('addToQueue')">
                  <ListMusic :size="18" />
                  <span>Добавить в очередь</span>
                </button>
                <div class="menu-divider" />
                <button v-if="hasAlbumArtist" class="menu-item" @click="exec('goToArtist')">
                  <User :size="18" />
                  <span>Перейти к артисту</span>
                </button>
              </template>

              <!-- ═══ ARTIST MENU ═══ -->
              <template v-else-if="menuType === 'artist'">
                <button class="menu-item" @click="exec('open')">
                  <User :size="18" />
                  <span>Открыть артиста</span>
                </button>
                <button class="menu-item" @click="exec('playAll')">
                  <Play :size="18" fill="currentColor" />
                  <span>Воспроизвести все</span>
                </button>
                <button class="menu-item" @click="exec('shuffle')">
                  <Shuffle :size="18" />
                  <span>Перемешать</span>
                </button>
                <button class="menu-item" @click="exec('addToQueue')">
                  <ListMusic :size="18" />
                  <span>Добавить в очередь</span>
                </button>
              </template>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>

  <!-- Playlist Picker Modal -->
  <PlaylistPicker
    :show="showPlaylistPicker"
    :track="editingItem"
    @close="closePlaylistPicker"
    @createNew="closePlaylistPicker"
    @added="onPlaylistAdded"
  />

  <!-- Edit Track Modal -->
  <EditTrackModal
    :show="showEditModal"
    :track="editingItem"
    @close="closeEditModal"
    @saved="onTrackSaved"
  />

  <!-- Rename Playlist Modal -->
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="showRenameModal" class="modal-overlay" @click="closeRenameModal">
        <div class="modal-content" @click.stop>
          <h3>Переименовать плейлист</h3>
          <input 
            v-model="renameValue" 
            type="text" 
            class="modal-input"
            placeholder="Название плейлиста"
            @keyup.enter="confirmRename"
            ref="renameInput"
          />
          <div class="modal-actions">
            <button class="modal-btn cancel" @click="closeRenameModal">Отмена</button>
            <button class="modal-btn confirm" @click="confirmRename">Сохранить</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, watch, nextTick, ref, onMounted, onUnmounted } from 'vue'
import { useContextMenu } from '@/composables/useContextMenu'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import PlaylistPicker from '@/components/PlaylistPicker.vue'
import EditTrackModal from '@/components/EditTrackModal.vue'
import { 
  X, User, Disc3, Play, ListMusic, Plus, Minus, Pencil, 
  Download, Trash2, FolderOpen, Shuffle, Music, Mic2
} from 'lucide-vue-next'

const authStore = useAuthStore()
const renameInput = ref(null)
const menuSheet = ref(null)
const isDesktop = ref(false)
const adjustedPosition = ref({ x: 0, y: 0 })

// Detect desktop
const checkDesktop = () => {
  isDesktop.value = window.innerWidth >= 768 && !('ontouchstart' in window)
}

// Handle keyboard events
const handleKeyDown = (e) => {
  if (e.key === 'Escape') {
    closeMenu()
  }
}

onMounted(() => {
  checkDesktop()
  window.addEventListener('resize', checkDesktop)
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkDesktop)
  window.removeEventListener('keydown', handleKeyDown)
})

const {
  isOpen,
  menuType,
  menuData,
  menuContext,
  menuPosition,
  closeMenu,
  executeAction,
  showPlaylistPicker,
  showEditModal,
  showRenameModal,
  editingItem,
  renameValue,
  closePlaylistPicker,
  onPlaylistAdded,
  closeEditModal,
  onTrackSaved,
  closeRenameModal,
  confirmRename,
} = useContextMenu()

// Auto-focus rename input
watch(showRenameModal, (show) => {
  if (show) {
    nextTick(() => renameInput.value?.focus())
  }
})

// Execute action shorthand
const exec = (action, extra = null) => {
  executeAction(action, extra)
}

// Calculate position for desktop mode (under cursor, within screen bounds)
watch([isOpen, menuPosition], ([open, pos]) => {
  if (open && isDesktop.value && pos.x > 0) {
    nextTick(() => {
      const menu = menuSheet.value
      if (!menu) return
      
      const menuWidth = menu.offsetWidth || 280
      const menuHeight = menu.offsetHeight || 400
      const padding = 8
      
      let x = pos.x
      let y = pos.y
      
      // Adjust if menu goes beyond right edge
      if (x + menuWidth + padding > window.innerWidth) {
        x = window.innerWidth - menuWidth - padding
      }
      
      // Adjust if menu goes beyond bottom edge
      if (y + menuHeight + padding > window.innerHeight) {
        y = window.innerHeight - menuHeight - padding
      }
      
      // Ensure minimum offset from edges
      x = Math.max(padding, x)
      y = Math.max(padding, y)
      
      adjustedPosition.value = { x, y }
    })
  }
})

// ═══════════════════════════════════════════════════════════
// COMPUTED HELPERS
// ═══════════════════════════════════════════════════════════

const hasCover = computed(() => {
  return menuData.value?.cover_url || menuData.value?.image_url
})

const coverStyle = computed(() => {
  const url = menuData.value?.cover_url || menuData.value?.image_url
  if (url) {
    return {
      backgroundImage: `url(${url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  return {}
})

const coverIcon = computed(() => {
  switch (menuType.value) {
    case 'track': return Music
    case 'playlist': return ListMusic
    case 'album': return Disc3
    case 'artist': return Mic2
    default: return Music
  }
})

const title = computed(() => {
  const data = menuData.value
  if (!data) return ''
  
  switch (menuType.value) {
    case 'track': return data.title || 'Без названия'
    case 'playlist': return data.name || 'Плейлист'
    case 'album': return data.name || data.album_name || 'Альбом'
    case 'artist': return typeof data === 'string' ? data : data.name || 'Артист'
    default: return ''
  }
})

const subtitle = computed(() => {
  const data = menuData.value
  if (!data) return ''
  
  switch (menuType.value) {
    case 'track': return data.artist || 'Неизвестный исполнитель'
    case 'playlist': return `${data.track_count || 0} ${getTracksWord(data.track_count || 0)}`
    case 'album': return data.album_artist || data.artist || ''
    case 'artist': return `${data.track_count || ''} ${data.track_count ? getTracksWord(data.track_count) : ''}`
    default: return ''
  }
})

// Track-specific
const hasArtist = computed(() => {
  return menuData.value?.artist && menuData.value.artist !== 'Неизвестный исполнитель'
})

const hasAlbum = computed(() => {
  const data = menuData.value
  return data?.album_id || data?.album?.id || data?.album_name
})

const isTrackOwner = computed(() => {
  const userId = authStore.user?.id
  return menuData.value?.uploader?.id === userId
})

const isInLibrary = computed(() => {
  const data = menuData.value
  if (data?.in_library !== undefined) return data.in_library
  if (data?.library_source && data.library_source !== 'global') return true
  if (['library', 'liked', 'playlist'].includes(menuContext.value)) return true
  return false
})

const inPlaylistContext = computed(() => {
  return menuContext.value?.startsWith('playlist:')
})

const playlistId = computed(() => {
  if (inPlaylistContext.value) {
    return menuContext.value.split(':')[1]
  }
  return null
})

// Playlist-specific
const isAutoAlbum = computed(() => {
  return menuData.value?.is_auto_album
})

const isPlaylistOwner = computed(() => {
  const userId = authStore.user?.id
  // Check if playlist has owner_id or user_id field
  return menuData.value?.owner_id === userId || 
         menuData.value?.user_id === userId ||
         menuData.value?.is_owner === true
})

// Track HD version (only available in player context)
const hasHDVersion = computed(() => {
  if (menuContext.value !== 'player') return false
  // Get from playerStore since HD info is only available for current track
  const playerStore = usePlayerStore()
  return !!playerStore.hdTrackInfo
})

// HD MIME types for track detection
const HD_MIME_TYPES = [
  'audio/flac', 'audio/x-flac',
  'audio/wav', 'audio/x-wav',
  'audio/aiff', 'audio/x-aiff',
  'audio/x-m4a', 'audio/mp4',
  'audio/alac', 'audio/x-alac'
]
const MAX_STREAMABLE_SIZE = 20 * 1024 * 1024

// Check if current track is HD/large file (show download HD option)
const isTrackHD = computed(() => {
  if (menuType.value !== 'track') return false
  const track = menuData.value
  if (!track) return false
  // HD format check
  if (track.mime_type && HD_MIME_TYPES.includes(track.mime_type.toLowerCase())) return true
  // Large file check
  if (track.file_size && track.file_size > MAX_STREAMABLE_SIZE) return true
  return false
})

// Album-specific
const hasAlbumArtist = computed(() => {
  return menuData.value?.album_artist || menuData.value?.artist
})

// Helpers
const getTracksWord = (count) => {
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod100 >= 11 && mod100 <= 14) return 'треков'
  if (mod10 === 1) return 'трек'
  if (mod10 >= 2 && mod10 <= 4) return 'трека'
  return 'треков'
}
</script>

<style scoped>
.menu-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

/* Desktop overlay - transparent, just for catching clicks */
.menu-overlay.desktop {
  background: transparent;
  backdrop-filter: none;
}

.menu-sheet {
  width: 100%;
  max-width: 400px;
  max-height: 80vh;
  background: #1a1a1a;
  border-radius: 16px 16px 0 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Desktop menu - floating under cursor */
.menu-sheet.desktop {
  position: fixed;
  width: 280px;
  max-width: none;
  max-height: 70vh;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.1);
}

.menu-sheet.desktop .menu-header {
  padding: 12px;
}

.menu-sheet.desktop .menu-cover {
  width: 40px;
  height: 40px;
}

.menu-sheet.desktop .menu-item {
  padding: 10px 14px;
  font-size: 14px;
}

.menu-sheet.desktop .menu-close {
  display: none;
}

.menu-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.menu-cover {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: linear-gradient(135deg, #333, #222);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.5);
  flex-shrink: 0;
}

.menu-info {
  flex: 1;
  min-width: 0;
}

.menu-title {
  font-weight: 600;
  color: white;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.menu-subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.menu-close {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.menu-items {
  padding: 8px 0;
  overflow-y: auto;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 14px 16px;
  background: none;
  border: none;
  color: white;
  font-size: 15px;
  cursor: pointer;
  text-align: left;
}

.menu-item:active {
  background: rgba(255, 255, 255, 0.1);
}

.menu-item.danger {
  color: #ff4444;
}

.menu-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
  margin: 8px 16px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-content {
  background: #1a1a1a;
  border-radius: 12px;
  padding: 20px;
  width: 100%;
  max-width: 320px;
}

.modal-content h3 {
  margin: 0 0 16px;
  color: white;
  font-size: 18px;
}

.modal-input {
  width: 100%;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
  color: white;
  font-size: 15px;
  outline: none;
}

.modal-input:focus {
  border-color: #1DB954;
}

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.modal-btn {
  flex: 1;
  padding: 12px;
  border-radius: 8px;
  border: none;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.modal-btn.cancel {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.modal-btn.confirm {
  background: #1DB954;
  color: white;
}

/* Animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}

/* Desktop scale animation */
.scale-enter-active,
.scale-leave-active {
  transition: transform 0.15s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.15s ease;
  transform-origin: top left;
}

.scale-enter-from,
.scale-leave-to {
  transform: scale(0.9);
  opacity: 0;
}
</style>
