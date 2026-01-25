<template>
  <div 
    class="track-item" 
    :class="{ playing: isPlaying, compact: compact, unavailable: track.is_unavailable, 'too-large': isLargeFile && !track.is_unavailable }" 
    @click="handleClick"
    @contextmenu.prevent="$emit('menu')"
  >
    <!-- Cover with generated gradient -->
    <div class="track-cover" :style="coverStyle">
      <img 
        v-if="track.cover_url && !track.is_unavailable" 
        :src="track.cover_url" 
        alt=""
        class="cover-image"
        loading="lazy"
      />
      <span v-else class="cover-text">{{ track.is_unavailable ? '✕' : coverInitials }}</span>
      
      <!-- Playing indicator -->
      <div v-if="isPlaying" class="playing-indicator">
        <div class="bar"></div>
        <div class="bar"></div>
        <div class="bar"></div>
      </div>
      
      <!-- Large file indicator (not unavailable, just too big for streaming) -->
      <div v-if="isLargeFile && !track.is_unavailable" class="large-file-overlay" title="Файл слишком большой для стриминга. Используйте Скачать.">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
        </svg>
      </div>
      
      <!-- Unavailable overlay -->
      <div v-if="track.is_unavailable" class="unavailable-overlay">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
        </svg>
      </div>
    </div>
    
    <div class="track-info">
      <div class="track-title">{{ track.title || 'Без названия' }}</div>
      <div class="track-meta">
        <span class="track-artist">{{ track.artist || 'Неизвестный' }}</span>
        <span v-if="isLargeFile" class="large-file-badge">{{ fileSizeMB }} MB</span>
        <span v-else-if="track.play_count" class="play-count">• {{ track.play_count }} прослушиваний</span>
      </div>
    </div>
    
    <div class="track-duration">
      {{ formatDuration(track.duration) }}
    </div>
    
    <button 
      class="track-like" 
      :class="{ liked: isLiked }" 
      @click.stop="$emit('like')"
    >
      <svg v-if="isLiked" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
      </svg>
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3zm-4.4 15.55l-.1.1-.1-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04.99 3.57 2.36h1.87C13.46 5.99 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05z"/>
      </svg>
    </button>
    
    <button v-if="!compact" class="track-menu" @click.stop="$emit('menu')">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatDuration, getTrackCoverStyle, getTrackInitials } from '@/utils'

const props = defineProps({
  track: {
    type: Object,
    required: true
  },
  isPlaying: {
    type: Boolean,
    default: false
  },
  isLiked: {
    type: Boolean,
    default: false
  },
  compact: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click', 'menu', 'like'])

const handleClick = () => {
  if (props.track.is_unavailable) {
    // Don't play unavailable tracks, just emit for potential action
    emit('menu')
    return
  }
  emit('click')
}

const coverStyle = computed(() => getTrackCoverStyle(props.track))

const coverInitials = computed(() => getTrackInitials(props.track))

// Check if file is too large for streaming (>20MB)
const isLargeFile = computed(() => {
  return props.track?.file_size && props.track.file_size > 20 * 1024 * 1024
})

const fileSizeMB = computed(() => {
  if (!props.track?.file_size) return 0
  return (props.track.file_size / (1024 * 1024)).toFixed(1)
})
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   🎵 TRACK ITEM - Neumorphic Style
   Individual track row with soft shadows
   ═══════════════════════════════════════════════════════════ */

.track-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 6px 8px 12px; /* Less right padding, scrollbar is there */
  margin: 4px 0 4px 8px; /* No right margin - scrollbar takes that space */
  border-radius: var(--neu-radius-md);
  cursor: pointer;
  transition: all 0.15s ease;
  background: transparent;
}

.track-item:active {
  background: var(--xm-bg-surface);
  transform: scale(0.98);
}

.track-item.playing {
  background: var(--xm-bg-surface);
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark),
    inset -1px -1px 3px var(--neu-shadow-inset-light);
}

.track-item.compact {
  padding: 6px 4px 6px 10px;
  margin: 2px 0 2px 6px;
}

/* ─── Track Cover ─── */
.track-cover {
  width: 48px;
  height: 48px;
  border-radius: var(--neu-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light);
  transition: box-shadow 0.2s ease;
}

.track-item.playing .track-cover {
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light);
}

.compact .track-cover {
  width: 40px;
  height: 40px;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-text {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.8);
}

.compact .cover-text {
  font-size: 14px;
}

/* ─── Playing Indicator (Equalizer) ─── */
.playing-indicator {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 3px;
  padding-bottom: 12px;
}

.playing-indicator .bar {
  width: 4px;
  background: var(--xm-accent);
  border-radius: 2px;
  animation: equalizer 0.8s ease-in-out infinite;
  box-shadow: 0 0 6px var(--xm-accent-glow);
}

.playing-indicator .bar:nth-child(1) {
  height: 10px;
  animation-delay: 0s;
}

.playing-indicator .bar:nth-child(2) {
  height: 18px;
  animation-delay: 0.2s;
}

.playing-indicator .bar:nth-child(3) {
  height: 14px;
  animation-delay: 0.4s;
}

@keyframes equalizer {
  0%, 100% { transform: scaleY(1); }
  50% { transform: scaleY(0.4); }
}

/* ─── Track Info ─── */
.track-info {
  flex: 1;
  min-width: 0;
}

.track-title {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--xm-text-primary);
  transition: color 0.15s ease;
}

.compact .track-title {
  font-size: 13px;
}

.track-item.playing .track-title {
  color: var(--xm-accent);
}

.track-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
}

.track-artist {
  font-size: 12px;
  color: var(--xm-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.compact .track-artist {
  font-size: 11px;
}

.play-count {
  font-size: 10px;
  color: var(--xm-text-muted);
  white-space: nowrap;
}

/* ─── Duration ─── */
.track-duration {
  font-size: 12px;
  font-weight: 500;
  color: var(--xm-text-muted);
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

/* ─── Like Button ─── */
.track-like {
  width: 32px;
  height: 32px;
  background: none;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-text-muted);
  cursor: pointer;
  opacity: 0.5;
  transition: all 0.2s ease;
  flex-shrink: 0;
  border-radius: var(--neu-radius-full);
}

.track-like:hover,
.track-like:active {
  opacity: 1;
  background: var(--xm-bg-surface);
}

.track-like.liked {
  color: var(--xm-accent);
  opacity: 1;
}

.track-like.liked svg {
  filter: drop-shadow(0 0 6px var(--xm-accent-glow));
}

/* ─── Menu Button ─── */
.track-menu {
  width: 28px;
  height: 32px;
  background: none;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-text-muted);
  cursor: pointer;
  opacity: 0.6;
  transition: all 0.2s ease;
  border-radius: var(--neu-radius-full);
  margin-right: -4px; /* Pull closer to edge, let scrollbar use that space */
}

.track-menu:active {
  opacity: 1;
  background: var(--xm-bg-surface);
}

/* ─── Unavailable Track Styles ─── */
.track-item.unavailable {
  opacity: 0.4;
}

.track-item.unavailable .track-title {
  text-decoration: line-through;
  color: var(--xm-text-muted);
}

.track-item.unavailable .track-cover {
  filter: grayscale(100%);
}

.unavailable-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-accent);
}

/* ─── Large File (too big for streaming, but downloadable) ─── */
.track-item.too-large {
  opacity: 0.7;
}

.large-file-overlay {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFA000;
}

/* ─── Large File Badge ─── */
.large-file-badge {
  font-size: 10px;
  color: #FFA000;
  background: rgba(255, 160, 0, 0.15);
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: 4px;
}
</style>
