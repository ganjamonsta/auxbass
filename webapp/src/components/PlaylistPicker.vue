<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
        <div class="modal" @click.stop>
          <!-- Modal Header -->
          <div class="modal-header">
            <div class="header-title">
              <ListPlus :size="20" class="header-icon" />
              <h3>Добавить в плейлист</h3>
            </div>
            <button class="modal-close" @click="$emit('close')" title="Закрыть">
              <X :size="18" />
            </button>
          </div>

          <!-- Target Track Preview -->
          <div v-if="track" class="target-track">
            <div class="track-thumb" :style="getTrackCoverStyle(track)">
              <img v-if="track.cover_url" :src="getCoverUrl(track.cover_url, CoverSize.SMALL)" alt="" />
              <Music v-else :size="16" />
            </div>
            <div class="track-info">
              <span class="track-label">Выбранный трек</span>
              <span class="track-title" :title="getDisplayTitle(track)">{{ getDisplayTitle(track) }}</span>
              <span class="track-artist" :title="getDisplayArtist(track)">{{ getDisplayArtist(track) }}</span>
            </div>
          </div>

          <!-- Search filter for 5+ playlists -->
          <div v-if="playlists.length > 4" class="search-wrapper">
            <SearchBar
              v-model="searchQuery"
              placeholder="Поиск плейлиста..."
            />
          </div>

          <!-- Playlist List -->
          <div class="playlist-list">
            <!-- Empty Library State -->
            <div v-if="playlists.length === 0" class="empty-state">
              <div class="empty-icon-wrap">
                <FolderPlus :size="32" />
              </div>
              <p class="empty-title">Нет плейлистов</p>
              <p class="empty-desc">Создайте свой первый плейлист и сохраняйте любимую музыку</p>
              <button class="create-first-btn" @click="handleCreateNew">
                <Plus :size="16" />
                <span>Создать плейлист</span>
              </button>
            </div>

            <template v-else>
              <!-- "New Playlist" Option -->
              <button class="playlist-option create-option" @click="handleCreateNew">
                <div class="playlist-avatar create-avatar">
                  <Plus :size="20" />
                </div>
                <div class="playlist-info">
                  <span class="playlist-name create-name">Новый плейлист</span>
                  <span class="playlist-count">Создать и добавить</span>
                </div>
              </button>

              <!-- No search results -->
              <div v-if="filteredPlaylists.length === 0" class="search-empty">
                <span>Плейлисты не найдены</span>
              </div>

              <!-- Existing Playlists -->
              <button
                v-for="playlist in filteredPlaylists"
                :key="playlist.id"
                class="playlist-option"
                :class="{ adding: addingId === playlist.id }"
                :disabled="addingId !== null"
                @click="handleSelect(playlist)"
              >
                <!-- Playlist Cover / Avatar -->
                <div class="playlist-avatar" :style="getPlaylistCoverStyle(playlist)">
                  <!-- 4+ Covers Collage Grid -->
                  <div v-if="playlist.covers?.length >= 4" class="cover-grid">
                    <img
                      v-for="(cover, i) in playlist.covers.slice(0, 4)"
                      :key="`${i}-${cover}`"
                      :src="getCoverUrl(cover, CoverSize.SMALL)"
                      loading="lazy"
                    />
                  </div>
                  <!-- Single Cover -->
                  <img
                    v-else-if="playlist.covers?.length"
                    :src="getCoverUrl(playlist.covers[0], CoverSize.SMALL)"
                    class="cover-single"
                    loading="lazy"
                  />
                  <!-- Fallback Placeholder -->
                  <div v-else class="cover-placeholder">
                    <Music :size="18" />
                  </div>
                </div>

                <!-- Playlist Meta -->
                <div class="playlist-info">
                  <span class="playlist-name">{{ playlist.name }}</span>
                  <span class="playlist-count">
                    {{ formatCount(playlist.track_count) }}
                    <span v-if="playlist.is_public" class="public-badge" title="Публичный плейлист">
                      <Globe :size="11" />
                    </span>
                  </span>
                </div>

                <!-- Action / Loading indicator -->
                <div class="action-icon">
                  <div v-if="addingId === playlist.id" class="mini-spinner"></div>
                  <Plus v-else :size="16" />
                </div>
              </button>
            </template>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, inject } from 'vue'
import { useLibraryStore } from '@/stores/library'
import { useAuthStore } from '@/stores/auth'
import {
  getCoverUrl,
  CoverSize,
  getDisplayTitle,
  getDisplayArtist,
  getTrackCoverStyle,
  getPlaylistCoverStyle
} from '@/utils'
import SearchBar from '@/components/ui/SearchBar.vue'
import { X, Plus, Music, Globe, FolderPlus, ListPlus } from 'lucide-vue-next'

const props = defineProps({
  show: Boolean,
  track: Object
})

const emit = defineEmits(['close', 'createNew', 'added'])

const library = useLibraryStore()
const authStore = useAuthStore()
const telegram = inject('telegram', null)

const searchQuery = ref('')
const addingId = ref(null)

const playlists = computed(() => library.playlists || [])

const filteredPlaylists = computed(() => {
  if (!searchQuery.value.trim()) return playlists.value
  const q = searchQuery.value.toLowerCase().trim()
  return playlists.value.filter(p => p.name?.toLowerCase().includes(q))
})

const formatCount = (count) => {
  const n = Math.abs(count || 0) % 100
  const n1 = n % 10
  if (n > 10 && n < 20) return `${count || 0} треков`
  if (n1 > 1 && n1 < 5) return `${count || 0} трека`
  if (n1 === 1) return `${count || 0} трек`
  return `${count || 0} треков`
}

watch(() => props.show, async (isOpen) => {
  if (isOpen) {
    searchQuery.value = ''
    addingId.value = null
    await library.fetchPlaylists()
  }
})

const handleCreateNew = () => {
  if (!authStore.requireChannel('создания плейлиста')) {
    emit('close')
    return
  }
  emit('createNew')
}

const handleSelect = async (playlist) => {
  if (!props.track || addingId.value) return

  if (!authStore.requireChannel('добавления трека в плейлист')) {
    emit('close')
    return
  }

  addingId.value = playlist.id
  telegram?.HapticFeedback?.impactOccurred?.('light')

  const success = await library.addTrackToPlaylist(playlist.id, props.track.id)
  if (success) {
    telegram?.HapticFeedback?.notificationOccurred?.('success')
    emit('added', playlist)
  } else {
    telegram?.HapticFeedback?.notificationOccurred?.('error')
  }

  addingId.value = null
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal, 1200);
  padding: 16px;
}

.modal {
  background: var(--c-bg-2);
  border-radius: var(--r-xl);
  border: 1px solid rgba(255, 255, 255, 0.08);
  width: 100%;
  max-width: 420px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow:
    0 24px 48px rgba(0, 0, 0, 0.7),
    0 0 0 1px rgba(255, 255, 255, 0.05);
  animation: modal-enter 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modal-enter {
  from {
    opacity: 0;
    transform: scale(0.96) translateY(6px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  color: var(--c-accent);
}

.modal-header h3 {
  font-size: 17px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--c-bg-3);
  border-radius: var(--r-full);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-3);
  transition: all 0.15s ease;
}

.modal-close:hover {
  background: var(--c-bg-4);
  color: var(--c-text-1);
}

/* Target Track Preview */
.target-track {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin: 12px 16px 4px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: var(--r-lg);
}

.track-thumb {
  width: 42px;
  height: 42px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-bg-3);
  color: var(--c-text-3);
}

.track-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.track-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.track-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--c-accent);
  font-weight: 700;
  margin-bottom: 2px;
}

.track-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-artist {
  font-size: 12px;
  color: var(--c-text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Search Wrapper */
.search-wrapper {
  padding: 8px 16px 4px;
}

.search-wrapper :deep(.search-bar) {
  margin-bottom: 0;
}

/* Playlists List */
.playlist-list {
  flex: 1;
  min-height: 120px;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 10px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.playlist-list::-webkit-scrollbar {
  width: 5px;
}

.playlist-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
}

/* Playlist Options */
.playlist-option {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--c-bg-3);
  border: 1px solid transparent;
  border-radius: var(--r-md);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
}

.playlist-option:hover:not(:disabled) {
  background: var(--c-bg-4);
  border-color: rgba(255, 255, 255, 0.05);
}

.playlist-option:active:not(:disabled) {
  transform: scale(0.985);
}

.playlist-option.adding {
  opacity: 0.7;
}

/* Playlist Avatar */
.playlist-avatar {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  position: relative;
  background: var(--c-bg-4);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

.cover-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  width: 100%;
  height: 100%;
}

.cover-grid img,
.cover-single {
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
  color: rgba(255, 255, 255, 0.85);
}

/* Create Option */
.create-option {
  background: rgba(29, 185, 84, 0.08);
  border: 1px dashed rgba(29, 185, 84, 0.3);
}

.create-option:hover:not(:disabled) {
  background: rgba(29, 185, 84, 0.14);
  border-color: rgba(29, 185, 84, 0.5);
}

.create-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(29, 185, 84, 0.2);
  color: var(--c-accent);
}

.create-name {
  color: var(--c-accent);
}

/* Playlist Info */
.playlist-info {
  flex: 1;
  min-width: 0;
}

.playlist-name {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.playlist-count {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--c-text-3);
  margin-top: 3px;
}

.public-badge {
  display: inline-flex;
  align-items: center;
  color: var(--c-text-3);
}

.action-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-3);
  border-radius: 50%;
  flex-shrink: 0;
  transition: all 0.15s;
}

.playlist-option:hover .action-icon {
  color: var(--c-accent);
  background: rgba(255, 255, 255, 0.05);
}

.mini-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: var(--c-accent);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

/* @keyframes spin — defined in design-system.css */

/* Empty States */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 32px 16px;
  gap: 8px;
}

.empty-icon-wrap {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(29, 185, 84, 0.12);
  color: var(--c-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4px;
}

.empty-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0;
}

.empty-desc {
  font-size: 13px;
  color: var(--c-text-3);
  margin: 0 0 12px;
  max-width: 240px;
}

.create-first-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: var(--c-accent);
  color: #000;
  border: none;
  border-radius: var(--r-full);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.create-first-btn:hover {
  opacity: 0.9;
}

.search-empty {
  text-align: center;
  padding: 24px 16px;
  color: var(--c-text-3);
  font-size: 13px;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
