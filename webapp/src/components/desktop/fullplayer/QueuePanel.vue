<template>
  <div class="dj-crate-panel">
    <!-- Lazy Shuffle Header Banner (if active) -->
    <div v-if="lazyShuffleMode && activeSubMode === 'upcoming'" class="crate-shuffle-banner">
      <div class="shuffle-badge">
        <Shuffle :size="13" />
        <span>SMART SHUFFLE</span>
      </div>
      <span class="shuffle-progress">
        ТРЕК {{ (lazyShuffleIndex || 0) + 1 }} / {{ lazyShuffleTotal }}
      </span>
    </div>

    <!-- UPCOMING TRACKS CRATE -->
    <div v-if="activeSubMode === 'upcoming'" class="crate-scroll-body">
      <div class="crate-list" v-if="upcomingQueue?.length">
        <div 
          v-for="(t, idx) in upcomingQueue" 
          :key="`q-${t.id}-${idx}`"
          class="crate-row"
          :class="{ 'is-deck-loaded': idx === 0 }"
          @click="$emit('playFromQueue', idx)"
          @contextmenu.prevent="openMenu('track', t, 'queue', $event)"
        >
          <!-- Track Cue Number or Active Indicator -->
          <div class="row-cue">
            <div v-if="idx === 0 && isPlaying" class="cue-playing-bars">
              <span></span><span></span><span></span>
            </div>
            <span v-else class="cue-num">{{ idx + 1 }}</span>
          </div>

          <!-- Cover Art Mini -->
          <div class="row-cover" :style="getTrackCoverStyle(t)">
            <img 
              v-if="t.cover_url" 
              :src="getCoverUrl(t.cover_url, CoverSize.SMALL)" 
              alt="" 
              class="cover-img"
            />
            <span v-else class="initials">{{ getTrackInitials(t) }}</span>
          </div>

          <!-- Title & Artist -->
          <div class="row-meta">
            <span class="row-title">{{ t.title || 'Без названия' }}</span>
            <span class="row-artist">{{ t.artist || 'Неизвестный исполнитель' }}</span>
          </div>

          <!-- Bitrate / Duration -->
          <div class="row-stats">
            <span v-if="t.bitrate" class="row-bitrate">{{ t.bitrate }}K</span>
            <span class="row-time">{{ formatTime(t.duration) }}</span>
          </div>
        </div>
      </div>

      <div v-else-if="!lazyShuffleMode" class="crate-empty">
        <ListMusic :size="32" class="empty-icon" />
        <p>Очередь треков пуста</p>
      </div>
    </div>

    <!-- HISTORY TRACKS CRATE -->
    <div v-else-if="activeSubMode === 'history'" class="crate-scroll-body">
      <div class="crate-list" v-if="historyTracks?.length">
        <div 
          v-for="(t, idx) in historyTracks" 
          :key="`h-${t.id}-${idx}`"
          class="crate-row history"
          @click="$emit('playFromHistory', idx)"
          @contextmenu.prevent="openMenu('track', t, 'history', $event)"
        >
          <div class="row-cue history">
            <span class="cue-num">-{{ historyTracks.length - idx }}</span>
          </div>

          <div class="row-cover" :style="getTrackCoverStyle(t)">
            <img 
              v-if="t.cover_url" 
              :src="getCoverUrl(t.cover_url, CoverSize.SMALL)" 
              alt="" 
              class="cover-img"
            />
            <span v-else class="initials">{{ getTrackInitials(t) }}</span>
          </div>

          <div class="row-meta">
            <span class="row-title">{{ t.title || 'Без названия' }}</span>
            <span class="row-artist">{{ t.artist || 'Неизвестный исполнитель' }}</span>
          </div>

          <div class="row-stats">
            <span class="row-time">{{ formatTime(t.duration) }}</span>
          </div>
        </div>
      </div>

      <div v-else class="crate-empty">
        <History :size="32" class="empty-icon" />
        <p>История воспроизведения пуста</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ListMusic, History, Shuffle } from 'lucide-vue-next'
import { getTrackCoverStyle, getTrackInitials, getCoverUrl, CoverSize } from '@/utils'
import { useContextMenu } from '@/composables/useContextMenu'

const props = defineProps({
  track: Object,
  upcomingQueue: { type: Array, default: () => [] },
  historyTracks: { type: Array, default: () => [] },
  isPlaying: Boolean,
  contextInfo: Object,
  lazyShuffleMode: Boolean,
  lazyShuffleIndex: Number,
  lazyShuffleTotal: Number,
  activeSubMode: { type: String, default: 'upcoming' }
})

defineEmits(['playFromQueue', 'playFromHistory'])

const { openMenu } = useContextMenu()

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds) || seconds < 0) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.dj-crate-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
  user-select: none;
}

/* Shuffle Banner */
.crate-shuffle-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: #090a0d;
  border-radius: var(--r-xs);
  border: 1px solid rgba(29, 185, 84, 0.2);
  margin-bottom: 8px;
  flex-shrink: 0;
}

.shuffle-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--c-accent);
  font-size: 10px;
  font-weight: 800;
  font-family: var(--font-mono, monospace);
  letter-spacing: 0.5px;
}

.shuffle-progress {
  font-size: 10px;
  font-weight: 800;
  font-family: var(--font-mono, monospace);
  color: var(--c-text-3);
}

/* Scroll body with NO SCROLLBARS */
.crate-scroll-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

.crate-scroll-body::-webkit-scrollbar {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
}

.crate-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.crate-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  border-radius: var(--r-xs);
  background: #121419;
  border: 1px solid #1c1f27;
  cursor: pointer;
  transition: all 0.12s ease;
}

.crate-row:hover {
  background: #1a1d25;
  border-color: #2b303d;
  transform: translateX(2px);
}

.crate-row.is-deck-loaded {
  background: #0f1c13;
  border-color: rgba(29, 185, 84, 0.35);
}

.crate-row.is-deck-loaded .row-title {
  color: var(--c-accent);
}

.crate-row.history {
  opacity: 0.7;
}

.crate-row.history:hover {
  opacity: 1;
}

.row-cue {
  width: 22px;
  text-align: center;
  font-size: 10px;
  font-weight: 800;
  font-family: var(--font-mono, monospace);
  color: var(--c-text-4);
  flex-shrink: 0;
}

.row-cue.history {
  color: var(--c-text-4);
}

.cue-playing-bars {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 2px;
  height: 12px;
}

.cue-playing-bars span {
  width: 2px;
  background: var(--c-accent);
  border-radius: 1px;
  animation: cueAnim 0.6s infinite alternate;
}

.cue-playing-bars span:nth-child(1) { height: 6px; }
.cue-playing-bars span:nth-child(2) { height: 12px; animation-delay: 0.2s; }
.cue-playing-bars span:nth-child(3) { height: 8px; animation-delay: 0.4s; }

@keyframes cueAnim {
  0% { height: 4px; }
  100% { height: 12px; }
}

.row-cover {
  width: 32px;
  height: 32px;
  border-radius: 3px;
  overflow: hidden;
  background: #090a0d;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.initials {
  font-size: 11px;
  font-weight: 800;
  color: var(--c-accent);
}

.row-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.row-title {
  font-size: 12px;
  font-weight: 700;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row-artist {
  font-size: 11px;
  color: var(--c-text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row-stats {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.row-bitrate {
  font-size: 9px;
  font-weight: 700;
  font-family: var(--font-mono, monospace);
  color: var(--c-text-4);
  padding: 1px 4px;
  border-radius: 2px;
  background: #0d0e12;
}

.row-time {
  font-size: 11px;
  font-weight: 700;
  font-family: var(--font-mono, monospace);
  color: var(--c-text-3);
}

.crate-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  height: 240px;
  color: var(--c-text-4);
  font-size: 13px;
}

.empty-icon {
  opacity: 0.3;
}
</style>
