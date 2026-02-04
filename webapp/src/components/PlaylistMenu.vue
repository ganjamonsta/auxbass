<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="menu-overlay" @click="$emit('close')">
        <Transition name="slide-up">
          <div v-if="show" class="menu-sheet" @click.stop>
            <!-- Playlist info header with close button -->
            <div class="menu-header">
              <div class="menu-cover" :style="getCoverStyle">
                <component :is="coverIcon" v-if="!props.playlist?.cover_url && !props.playlist?.cover_gradient" :size="20" />
              </div>
              <div class="menu-info">
                <div class="menu-title">{{ playlist?.name || 'Плейлист' }}</div>
                <div class="menu-subtitle">{{ subtitle }}</div>
              </div>
              <button class="menu-close" @click="$emit('close')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
                </svg>
              </button>
            </div>

            <!-- Menu items -->
            <div class="menu-items">
              <button class="menu-item" @click="handleOpen">
                <span class="menu-icon"><FolderOpen :size="18" /></span>
                <span>Открыть</span>
              </button>

              <button class="menu-item" @click="handlePlayAll">
                <span class="menu-icon"><Play :size="18" fill="currentColor" /></span>
                <span>Воспроизвести все</span>
              </button>

              <button class="menu-item" @click="handleShuffle">
                <span class="menu-icon"><Shuffle :size="18" /></span>
                <span>Перемешать</span>
              </button>

              <button class="menu-item" @click="handleAddToQueue">
                <span class="menu-icon"><ListMusic :size="18" /></span>
                <span>Добавить в очередь</span>
              </button>

              <div v-if="!isAlbum" class="menu-divider"></div>

              <button v-if="!isAlbum" class="menu-item" @click="handleEdit">
                <span class="menu-icon"><Pencil :size="18" /></span>
                <span>Редактировать</span>
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
import { FolderOpen, Play, Shuffle, ListMusic, Pencil, Music, Disc3 } from 'lucide-vue-next'

const props = defineProps({
  show: Boolean,
  playlist: Object
})

const emit = defineEmits(['close', 'open', 'playAll', 'shuffle', 'addToQueue', 'edit'])

const player = usePlayerStore()
const telegram = inject('telegram')

// Check if this is an album (auto-generated playlist)
const isAlbum = computed(() => props.playlist?.is_auto_album)

// Cover styling
const getCoverStyle = computed(() => {
  if (props.playlist?.covers?.length) {
    return {
      backgroundImage: `url(${props.playlist.covers[0]})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  if (props.playlist?.cover_gradient) {
    return { background: props.playlist.cover_gradient }
  }
  return {}
})

const coverIcon = computed(() => {
  if (props.playlist?.covers?.length || props.playlist?.cover_gradient) return null
  return isAlbum.value ? Disc3 : Music
})

const subtitle = computed(() => {
  const count = props.playlist?.track_count || 0
  if (isAlbum.value) {
    const artist = props.playlist?.artist || 'Неизвестный исполнитель'
    return `${artist} • ${count} ${getTracksWord(count)}`
  }
  return `${count} ${getTracksWord(count)}`
})

const getTracksWord = (count) => {
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod100 >= 11 && mod100 <= 14) return 'треков'
  if (mod10 === 1) return 'трек'
  if (mod10 >= 2 && mod10 <= 4) return 'трека'
  return 'треков'
}

// Haptic feedback helper
const haptic = (type = 'light') => {
  telegram?.HapticFeedback?.impactOccurred?.(type)
}

const handleOpen = () => {
  haptic('light')
  emit('open', props.playlist)
  emit('close')
}

const handlePlayAll = () => {
  haptic('light')
  emit('playAll', props.playlist)
  emit('close')
}

const handleShuffle = () => {
  haptic('light')
  emit('shuffle', props.playlist)
  emit('close')
}

const handleAddToQueue = () => {
  haptic('light')
  emit('addToQueue', props.playlist)
  emit('close')
}

const handleEdit = () => {
  haptic('light')
  emit('edit', props.playlist)
  emit('close')
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   📂 PLAYLIST MENU - Context menu for playlists/albums
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

.menu-subtitle {
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

  .menu-subtitle {
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
