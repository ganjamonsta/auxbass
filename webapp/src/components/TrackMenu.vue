<!--
  @deprecated This component is deprecated. Use ContextMenu.vue with useContextMenu() composable instead.
  This file is kept for legacy compatibility only.
  
  Migration: 
    1. Import: import { useContextMenu } from '@/composables/useContextMenu'
    2. Use: const { openMenu } = useContextMenu()
    3. Call: openMenu('track', track, 'context', $event)
-->
<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="menu-overlay" @click="$emit('close')">
        <Transition name="slide-up">
          <div v-if="show" class="menu-sheet" @click.stop>
            <!-- Track info header with close button -->
            <div class="menu-header">
              <div class="menu-cover"><Music :size="20" /></div>
              <div class="menu-info">
                <div class="menu-title">{{ getDisplayTitle(track) }}</div>
                <div class="menu-artist">{{ getDisplayArtist(track) }}</div>
              </div>
              <button class="menu-close" @click="$emit('close')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
                </svg>
              </button>
            </div>

            <!-- Menu items -->
            <div class="menu-items">
              <!-- Navigation section -->
              <button v-if="showGoToArtist" class="menu-item" @click="handleGoToArtist">
                <span class="menu-icon"><User :size="18" /></span>
                <span>Перейти к артисту</span>
              </button>

              <button v-if="showGoToAlbum" class="menu-item" @click="handleGoToAlbum">
                <span class="menu-icon"><Disc3 :size="18" /></span>
                <span>{{ albumButtonText }}</span>
              </button>

              <div v-if="showGoToArtist || showGoToAlbum" class="menu-divider"></div>

              <!-- Queue actions - hide for current track or in player context -->
              <button v-if="showQueueActions" class="menu-item" @click="handlePlayNext">
                <span class="menu-icon"><Play :size="18" fill="currentColor" /></span>
                <span>Включить следующим</span>
              </button>

              <button v-if="showQueueActions" class="menu-item" @click="handleAddToQueue">
                <span class="menu-icon"><ListMusic :size="18" /></span>
                <span>Добавить в очередь</span>
              </button>

              <button class="menu-item" @click="handleAddToPlaylist">
                <span class="menu-icon"><Plus :size="18" /></span>
                <span>Добавить в плейлист</span>
              </button>

              <div class="menu-divider"></div>

              <button class="menu-item" @click="handleEdit">
                <span class="menu-icon"><Pencil :size="18" /></span>
                <span>Редактировать</span>
              </button>

              <button class="menu-item" @click="handleDownload">
                <span class="menu-icon"><Download :size="18" /></span>
                <span>Скачать</span>
              </button>

              <div class="menu-divider"></div>

              <!-- Remove from playlist (only in playlist context) -->
              <button v-if="inPlaylist" class="menu-item danger" @click="handleRemoveFromPlaylist">
                <span class="menu-icon"><Minus :size="18" /></span>
                <span>Убрать из плейлиста</span>
              </button>

              <!-- Owner can fully delete -->
              <button v-if="isOwner" class="menu-item danger" @click="handleDelete">
                <span class="menu-icon"><Trash2 :size="18" /></span>
                <span>Удалить полностью</span>
              </button>
              <!-- If in library (but not owner) - can remove from library -->
              <button v-else-if="isInLibrary" class="menu-item" @click="handleRemoveFromLibrary">
                <span class="menu-icon"><Minus :size="18" /></span>
                <span>Убрать из библиотеки</span>
              </button>
              <!-- If not in library - can add to library -->
              <button v-else class="menu-item" @click="handleAddToLibrary">
                <span class="menu-icon"><Plus :size="18" /></span>
                <span>Добавить в библиотеку</span>
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { inject, computed } from 'vue'
import { usePlayerStore } from '../stores/player'
import { useAuthStore } from '../stores/auth'
import { getDisplayTitle, getDisplayArtist, getAllTrackArtists } from '@/utils'
import { Music, User, Disc3, Play, ListMusic, Plus, Minus, Pencil, Download, Trash2 } from 'lucide-vue-next'

const props = defineProps({
  show: Boolean,
  track: Object,
  currentUserId: Number,
  inPlaylist: Boolean,
  // Context: 'library' | 'player' | 'album' | 'artist' | 'playlist' | 'liked'
  context: {
    type: String,
    default: 'library'
  }
})

const emit = defineEmits(['close', 'addToPlaylist', 'edit', 'delete', 'removeFromLibrary', 'download', 'goToArtist', 'goToAlbum', 'removeFromPlaylist', 'addToLibrary'])

const player = usePlayerStore()
const authStore = useAuthStore()
const telegram = inject('telegram')

// Computed properties for navigation availability
const hasArtist = computed(() => {
  const track = props.track
  if (!track) return false
  // Check if we have artist metadata
  if (track.artist && track.artist !== 'Неизвестный исполнитель') return true
  // For tracks without metadata, check if we can extract from filename
  if (!track.artist && track.file_name) {
    const extracted = getAllTrackArtists(null, track.title, track.file_name)
    return extracted.length > 0
  }
  return false
})

const hasAlbum = computed(() => {
  const albumName = props.track?.album_name || props.track?.album?.name
  return albumName && albumName.trim() !== ''
})

// Check if current user is the track owner (uploader)
const isOwner = computed(() => {
  if (!props.track || !props.currentUserId) return false
  return props.track.uploader?.id === props.currentUserId
})

// Check if track is in user's library
const isInLibrary = computed(() => {
  // If in_library is explicitly set (e.g. from global/friends search), use it
  if (props.track?.in_library !== undefined) {
    return props.track.in_library
  }
  // If track has library_source set (not null/undefined), it's in library
  if (props.track?.library_source && props.track.library_source !== 'global') {
    return true
  }
  // Fallback: check context, but only if no explicit flag
  // This handles tracks loaded from user's library view directly
  if (props.context === 'library' || props.context === 'liked' || props.context === 'playlist') {
    return true
  }
  return false
})

// Check if this is the currently playing track
const isCurrentTrack = computed(() => {
  return props.track?.id === player.currentTrack?.id
})

// Check if we're in player context (where queue actions don't make sense)
const isPlayerContext = computed(() => {
  return props.context === 'player'
})

// Show queue actions only when not current track and not in player context
const showQueueActions = computed(() => {
  return !isCurrentTrack.value && !isPlayerContext.value
})

// Show navigation to artist (hide if already on artist page)
const showGoToArtist = computed(() => {
  return hasArtist.value && props.context !== 'artist'
})

// Show navigation to album (hide if already on album page)
const showGoToAlbum = computed(() => {
  return hasAlbum.value && props.context !== 'album'
})

// Get album button text - show album name
const albumButtonText = computed(() => {
  const albumName = props.track?.album?.name || props.track?.album_name
  
  if (albumName) {
    return `Перейти к альбому (${albumName})`
  }
  
  return 'Перейти к альбому'
})

// Haptic feedback helper
const haptic = (type = 'light') => {
  telegram?.HapticFeedback?.impactOccurred?.(type)
}

const handleGoToArtist = () => {
  haptic('light')
  // Get all artists including from filename for tracks without metadata
  const artists = getAllTrackArtists(props.track?.artist, props.track?.title, props.track?.file_name)
  const artistName = artists.length > 0 ? artists[0] : props.track?.artist
  emit('goToArtist', artistName)
  emit('close')
}

const handleGoToAlbum = () => {
  haptic('light')
  const album = props.track?.album
  const albumId = album?.id
  if (albumId) {
    emit('goToAlbum', albumId)
  }
  emit('close')
}

const handlePlayNext = () => {
  if (!authStore.hasChannel) {
    authStore.promptChannelSetup()
    emit('close')
    return
  }
  if (props.track) {
    player.playNext(props.track)
    haptic('light')
  }
  emit('close')
}

const handleAddToQueue = () => {
  if (!authStore.hasChannel) {
    authStore.promptChannelSetup()
    emit('close')
    return
  }
  if (props.track) {
    player.addToQueue(props.track)
    haptic('light')
  }
  emit('close')
}

const handleAddToPlaylist = () => {
  if (!authStore.hasChannel) {
    authStore.promptChannelSetup()
    emit('close')
    return
  }
  haptic('light')
  emit('addToPlaylist', props.track)
  emit('close')
}

const handleEdit = () => {
  haptic('light')
  emit('edit', props.track)
  emit('close')
}

const handleDelete = () => {
  haptic('warning')
  emit('delete', props.track)
  emit('close')
}

const handleRemoveFromLibrary = () => {
  haptic('light')
  emit('removeFromLibrary', props.track)
  emit('close')
}

const handleAddToLibrary = () => {
  haptic('light')
  emit('addToLibrary', props.track)
  emit('close')
}

const handleDownload = () => {
  haptic('light')
  emit('download', props.track)
  emit('close')
}

const handleRemoveFromPlaylist = () => {
  haptic('light')
  emit('removeFromPlaylist', props.track)
  emit('close')
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   🎵 TRACK MENU - Compact Bottom Sheet
   Action menu for tracks with soft shadows
   ═══════════════════════════════════════════════════════════ */

.menu-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.menu-sheet {
  width: 100%;
  max-width: 500px;
  background: var(--xm-bg-elevated);
  border-radius: var(--neu-radius-xl) var(--neu-radius-xl) 0 0;
  padding: 12px 16px;
  padding-bottom: max(12px, env(safe-area-inset-bottom));
  box-shadow: 
    0 -8px 24px var(--neu-shadow-dark),
    0 -2px 8px var(--neu-shadow-light);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-bottom: none;
}

/* ─── Header ─── */
.menu-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0 8px;
}

.menu-cover {
  width: 44px;
  height: 44px;
  border-radius: var(--neu-radius-sm);
  background: var(--xm-bg-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 
    3px 3px 6px var(--neu-shadow-dark),
    -1px -1px 3px var(--neu-shadow-light);
}

.menu-info {
  flex: 1;
  min-width: 0;
}

.menu-title {
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--xm-text-primary);
}

.menu-artist {
  font-size: 13px;
  color: var(--xm-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 1px;
}

.menu-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--xm-bg-surface);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.menu-close:active {
  background: var(--xm-bg-hover);
  transform: scale(0.92);
}

/* ─── Divider ─── */
.menu-divider {
  height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    var(--xm-bg-hover) 20%, 
    var(--xm-bg-hover) 80%, 
    transparent 100%);
  margin: 6px 0;
}

/* ─── Menu Items ─── */
.menu-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 11px 10px;
  background: transparent;
  border: none;
  border-radius: var(--neu-radius-sm);
  font-size: 15px;
  font-weight: 500;
  color: var(--xm-text-primary);
  cursor: pointer;
  text-align: left;
  transition: all 0.12s ease;
}

.menu-item:active {
  background: var(--xm-bg-surface);
  transform: scale(0.98);
}

.menu-item.danger {
  color: var(--xm-accent);
}

.menu-item.danger:active {
  background: rgba(229, 57, 53, 0.1);
}

.menu-icon {
  font-size: 18px;
  width: 26px;
  text-align: center;
  flex-shrink: 0;
}

/* ─── Animations ─── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}

/* Desktop styles - dropdown instead of bottom sheet */
@media (min-width: 1024px) {
  .menu-overlay {
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.6);
  }

  .menu-sheet {
    width: auto;
    min-width: 280px;
    max-width: 360px;
    border-radius: 12px;
    padding: 8px;
    box-shadow: 
      0 8px 32px rgba(0, 0, 0, 0.5),
      0 2px 8px rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .menu-header {
    padding: 8px 8px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    margin-bottom: 4px;
  }

  .menu-cover {
    width: 40px;
    height: 40px;
    font-size: 18px;
  }

  .menu-title {
    font-size: 14px;
  }

  .menu-artist {
    font-size: 12px;
  }

  .menu-items {
    gap: 0;
  }

  .menu-item {
    padding: 10px 12px;
    font-size: 14px;
    gap: 12px;
    border-radius: 6px;
  }

  .menu-item:hover {
    background: rgba(255, 255, 255, 0.08);
  }

  .menu-item:active {
    transform: none;
    background: rgba(255, 255, 255, 0.12);
  }

  .menu-item.danger:hover {
    background: rgba(229, 57, 53, 0.15);
  }

  .menu-icon {
    font-size: 16px;
    width: 22px;
  }

  .menu-divider {
    margin: 4px 8px;
  }

  .slide-up-enter-from,
  .slide-up-leave-to {
    transform: translateY(0) scale(0.95);
    opacity: 0;
  }

  .slide-up-enter-active,
  .slide-up-leave-active {
    transition: transform 0.2s ease, opacity 0.2s ease;
  }
}
</style>
