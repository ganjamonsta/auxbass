<template>
  <div
    class="playlist-card"
    @click="handleClick"
    @contextmenu.prevent="$emit('contextmenu', $event)"
    @touchstart="handleTouchStart"
    @touchmove="handleTouchMove"
    @touchend="handleTouchEnd"
    @touchcancel="handleTouchEnd"
  >
    <div class="playlist-cover">
      <!-- Special cover for Liked Songs -->
      <div v-if="playlist.id === 'liked' || playlist.is_liked" class="liked-cover">
        <Heart :size="38" fill="currentColor" />
      </div>
      <div class="cover-grid" :class="{ 'single-cover': playlist.covers?.length === 1 }" v-else-if="playlist.covers?.length">
        <img
          v-for="(cover, i) in playlist.covers.slice(0, 4)"
          :key="`${i}-${cover}`"
          :src="getCoverUrl(cover, playlist.covers?.length === 1 ? CoverSize.MEDIUM : CoverSize.SMALL)"
          loading="lazy"
          alt=""
        />
      </div>
      <div v-else class="cover-placeholder"><Music :size="24" /></div>
      
      <!-- Play button -->
      <button 
        class="play-btn" 
        :class="{ 'is-playing': isPlaying }"
        @click.stop="handlePlay"
        :title="isPlaying ? 'Пауза' : 'Слушать'"
      >
        <Pause v-if="isPlaying" :size="20" fill="currentColor" />
        <Play v-else :size="20" fill="currentColor" />
      </button>
      
      <!-- Owner badge for created playlists -->
      <div v-if="playlist.is_owner" class="owner-badge creator-badge">
        <Crown :size="12" /> Ваш
      </div>
      
      <!-- Subscribed badge for added playlists -->
      <div v-else-if="playlist.is_subscribed" class="owner-badge subscribed-badge">
        <UserPlus :size="12" /> {{ playlist.owner_name || 'Добавлен' }}
      </div>
    </div>
    
    <div class="playlist-info">
      <div class="playlist-name">{{ playlist.name }}</div>
      <div class="playlist-meta">
        {{ playlist.track_count }} треков
        <span v-if="playlist.is_public" class="public-badge">
          <Globe :size="12" />
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Music, Globe, Crown, UserPlus, Play, Pause, Heart } from 'lucide-vue-next'
import { getCoverUrl, CoverSize, triggerHaptic, suppressNextClick, suppressNextContextMenu } from '@/utils'
import { usePlayerStore } from '@/stores/player'
import { computed } from 'vue'

const playerStore = usePlayerStore()

const props = defineProps({
  playlist: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click', 'play', 'contextmenu'])

const isPlaying = computed(() => {
  if (!playerStore.isPlaying) return false
  const playlistId = props.playlist?.id
  if (!playlistId) return false
  if (playlistId === 'liked' || props.playlist.is_liked) {
    const ctx = playerStore.playbackContext || playerStore.lazyShuffleContext
    return ctx?.type === 'liked' || ctx?.type === 'library'
  }
  if (playerStore.currentPlaylistId === Number(playlistId)) return true
  const ctx = playerStore.playbackContext || playerStore.lazyShuffleContext
  if (ctx?.type === 'playlist' && String(ctx.id) === String(playlistId)) return true
  return false
})

const handlePlay = () => {
  if (isPlaying.value) {
    playerStore.togglePlay()
  } else {
    emit('play', props.playlist)
  }
}

let longPressTimer = null
let touchMoved = false
let touchStartX = 0
let touchStartY = 0
let isLongPressTriggered = false

const handleTouchStart = (e) => {
  touchMoved = false
  isLongPressTriggered = false
  if (e.touches.length === 1) {
    touchStartX = e.touches[0].clientX
    touchStartY = e.touches[0].clientY
    longPressTimer = setTimeout(() => {
      if (!touchMoved) {
        isLongPressTriggered = true
        triggerHaptic()
        suppressNextClick()
        suppressNextContextMenu()
        emit('contextmenu', e)
      }
    }, 450)
  }
}

const handleTouchMove = (e) => {
  if (e.touches.length === 1) {
    const dx = Math.abs(e.touches[0].clientX - touchStartX)
    const dy = Math.abs(e.touches[0].clientY - touchStartY)
    if (dx > 10 || dy > 10) {
      touchMoved = true
      clearTimeout(longPressTimer)
    }
  }
}

const handleTouchEnd = () => {
  clearTimeout(longPressTimer)
}

const handleClick = (e) => {
  if (isLongPressTriggered) {
    isLongPressTriggered = false
    e?.preventDefault?.()
    e?.stopPropagation?.()
    return
  }
  emit('click', props.playlist)
}
</script>

<style scoped>
.playlist-card {
  cursor: pointer;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 8px;
  border-radius: var(--r-lg);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
}

.playlist-card:hover {
  background: var(--c-bg-2);
  border: var(--border-neu);
  box-shadow: 
    4px 4px 12px var(--sh-dark),
    -2px -2px 6px var(--sh-light);
  transform: translateY(-2px);
}

.playlist-card:active {
  transform: translateY(0) scale(0.98);
}

.playlist-cover {
  width: 100%;
  aspect-ratio: 1;
  background: var(--c-bg-3);
  border-radius: var(--r-md);
  overflow: hidden;
  margin-bottom: 8px;
  position: relative;
  box-shadow: 
    4px 4px 10px var(--sh-dark),
    -2px -2px 5px var(--sh-light);
  border: var(--border-neu);
}

.cover-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  width: 100%;
  height: 100%;
}

.cover-grid.single-cover {
  display: block;
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
  color: var(--c-text-2);
}

.playlist-info {
  min-width: 0;
}

.playlist-name {
  font-weight: 600;
  font-size: 14px;
  line-height: 18px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
  color: var(--c-text-1);
}

.playlist-meta {
  font-size: 12px;
  line-height: 15px;
  color: var(--c-text-2);
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.public-badge {
  display: flex;
  color: var(--c-text-2);
}

.owner-badge {
  position: absolute;
  bottom: 0px;
  right: 0px;
  background: rgba(0,0,0,0.75);
  color: white;
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  border-top-left-radius: 6px;
  display: flex;
  align-items: center;
  gap: 3px;
  backdrop-filter: blur(4px);
}

.creator-badge {
  background: rgba(255, 215, 0, 0.9);
  color: #000;
}

.subscribed-badge {
  background: rgba(59, 130, 246, 0.9);
  color: #fff;
}

.play-btn {
  position: absolute;
  right: 10px;
  bottom: 10px;
  width: 40px;
  height: 40px;
  border-radius: var(--r-full);
  background: linear-gradient(145deg, var(--c-accent-light), var(--c-accent-dark));
  border: none;
  color: #000;
  font-size: 14px;
  cursor: pointer;
  opacity: 0;
  transform: translateY(8px);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  box-shadow: 
    3px 3px 8px rgba(0, 0, 0, 0.6),
    0 0 12px var(--c-accent-glow);
}

.playlist-card:hover .play-btn,
.play-btn.is-playing {
  opacity: 1;
  transform: translateY(0);
}

.play-btn:hover {
  transform: translateY(0) scale(1.08);
  box-shadow: 
    4px 4px 12px rgba(0, 0, 0, 0.7),
    0 0 18px var(--c-accent-glow);
}

.play-btn:active {
  transform: translateY(0) scale(0.95);
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.6);
}

.play-btn svg.lucide-play {
  margin-left: 2px;
}

/* Hide play button on mobile devices */
@media (max-width: 768px) {
  .play-btn {
    display: none;
  }
}

/* Liked songs cover styling */
.liked-cover {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #450af5 0%, #7c3aed 50%, #c084fc 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  box-shadow: inset 0 0 24px rgba(255, 255, 255, 0.18);
  transition: filter 0.25s cubic-bezier(0.2, 0, 0, 1);
}

.liked-cover svg {
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.35));
}

.playlist-card:hover .liked-cover {
  filter: brightness(1.08);
}
</style>
