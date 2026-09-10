<template>
  <div class="queue-panel-container">
    <!-- Tab Selector -->
    <div class="deck-tabs-header">
      <div class="segmented-tabs neu-surface">
        <button 
          class="tab-btn" 
          :class="{ active: activeQueueTab === 'upcoming' }"
          @click="activeQueueTab = 'upcoming'"
        >
          <ListMusic :size="15" />
          <span>Очередь</span>
          <span class="tab-count" v-if="queueLength">{{ queueLength }}</span>
        </button>

        <button 
          class="tab-btn" 
          :class="{ active: activeQueueTab === 'history' }"
          @click="activeQueueTab = 'history'"
        >
          <History :size="15" />
          <span>История</span>
          <span class="tab-count" v-if="historyTracks?.length">{{ historyTracks.length }}</span>
        </button>

        <button 
          class="tab-btn" 
          :class="{ active: activeQueueTab === 'lyrics' }"
          @click="activeQueueTab = 'lyrics'"
        >
          <Mic2 :size="15" />
          <span>Текст</span>
        </button>
      </div>
    </div>

    <!-- Tab Content Area -->
    <div class="deck-tab-content">
      <!-- UPCOMING QUEUE TAB -->
      <div v-if="activeQueueTab === 'upcoming'" class="tab-scroll-pane">
        <!-- Lazy Shuffle Banner -->
        <div v-if="lazyShuffleMode" class="lazy-shuffle-card neu-surface">
          <Shuffle :size="18" class="lazy-icon" />
          <div class="lazy-text">
            <span class="lazy-title">Умное перемешивание</span>
            <span class="lazy-counter">Трек {{ (lazyShuffleIndex || 0) + 1 }} из {{ lazyShuffleTotal }}</span>
          </div>
        </div>

        <!-- Upcoming list -->
        <div class="queue-track-list" v-if="upcomingQueue?.length">
          <div 
            v-for="(t, idx) in upcomingQueue" 
            :key="`q-${t.id}-${idx}`"
            class="queue-item"
            :class="{ 'now-playing': idx === 0 }"
            @click="$emit('playFromQueue', idx)"
            @contextmenu.prevent="openMenu('track', t, 'queue', $event)"
          >
            <!-- Track Number or Playing icon -->
            <div class="item-index">
              <div v-if="idx === 0 && isPlaying" class="equalizer">
                <span class="equalizer-bar"></span>
                <span class="equalizer-bar"></span>
                <span class="equalizer-bar"></span>
              </div>
              <span v-else>{{ idx + 1 }}</span>
            </div>

            <!-- Cover -->
            <div class="item-cover" :style="getTrackCoverStyle(t)">
              <img 
                v-if="t.cover_url" 
                :src="getCoverUrl(t.cover_url, CoverSize.SMALL)" 
                alt="" 
                class="cover-img"
              />
              <span v-else class="initials">{{ getTrackInitials(t) }}</span>
            </div>

            <!-- Meta info -->
            <div class="item-info">
              <span class="item-title">{{ t.title || 'Без названия' }}</span>
              <span class="item-artist">{{ t.artist || 'Неизвестный исполнитель' }}</span>
            </div>

            <!-- Duration -->
            <span class="item-duration">{{ formatTime(t.duration) }}</span>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else-if="!lazyShuffleMode" class="empty-deck-state">
          <ListMusic :size="36" class="empty-icon" />
          <p class="empty-text">Очередь воспроизведения пуста</p>
        </div>
      </div>

      <!-- HISTORY TAB -->
      <div v-else-if="activeQueueTab === 'history'" class="tab-scroll-pane">
        <div class="queue-track-list" v-if="historyTracks?.length">
          <div 
            v-for="(t, idx) in historyTracks" 
            :key="`h-${t.id}-${idx}`"
            class="queue-item history-item"
            @click="$emit('playFromHistory', idx)"
            @contextmenu.prevent="openMenu('track', t, 'history', $event)"
          >
            <div class="item-index history">
              <span>-{{ historyTracks.length - idx }}</span>
            </div>

            <div class="item-cover" :style="getTrackCoverStyle(t)">
              <img 
                v-if="t.cover_url" 
                :src="getCoverUrl(t.cover_url, CoverSize.SMALL)" 
                alt="" 
                class="cover-img"
              />
              <span v-else class="initials">{{ getTrackInitials(t) }}</span>
            </div>

            <div class="item-info">
              <span class="item-title">{{ t.title || 'Без названия' }}</span>
              <span class="item-artist">{{ t.artist || 'Неизвестный исполнитель' }}</span>
            </div>

            <span class="item-duration">{{ formatTime(t.duration) }}</span>
          </div>
        </div>

        <div v-else class="empty-deck-state">
          <History :size="36" class="empty-icon" />
          <p class="empty-text">История прослушивания пуста</p>
        </div>
      </div>

      <!-- LYRICS TAB -->
      <div v-else-if="activeQueueTab === 'lyrics'" class="lyrics-container">
        <LyricsViewer
          v-if="track"
          :track="track"
          :currentTime="progress"
          :isPlaying="isPlaying"
          :embedded="true"
          @seek="$emit('seek', $event)"
        />
        <div v-else class="empty-deck-state">
          <Mic2 :size="36" class="empty-icon" />
          <p class="empty-text">Нет активного трека для показа текста</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ListMusic, History, Mic2, Shuffle } from 'lucide-vue-next'
import { getTrackCoverStyle, getTrackInitials, getCoverUrl, CoverSize } from '@/utils'
import { useContextMenu } from '@/composables/useContextMenu'
import LyricsViewer from '@/components/LyricsViewer.vue'

const props = defineProps({
  track: Object,
  progress: Number,
  isPlaying: Boolean,
  contextInfo: Object,
  queueLength: Number,
  upcomingQueue: {
    type: Array,
    default: () => []
  },
  historyTracks: {
    type: Array,
    default: () => []
  },
  lazyShuffleMode: Boolean,
  lazyShuffleIndex: Number,
  lazyShuffleTotal: Number
})

defineEmits(['playFromQueue', 'playFromHistory', 'seek'])

const { openMenu } = useContextMenu()

const activeQueueTab = ref('upcoming')

function setTab(tab) {
  activeQueueTab.value = tab
}

defineExpose({
  setTab,
  activeQueueTab
})

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds) || seconds < 0) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.queue-panel-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

/* Tab Header */
.deck-tabs-header {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 0 16px;
  flex-shrink: 0;
}

.segmented-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  border-radius: var(--r-full);
  background: var(--c-bg-1);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  border-radius: var(--r-full);
  border: none;
  background: transparent;
  color: var(--c-text-3);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  color: var(--c-text-1);
}

.tab-btn.active {
  background: var(--c-bg-3);
  color: var(--c-accent);
  box-shadow: 
    2px 2px 6px var(--sh-dark),
    -1px -1px 3px var(--sh-light);
}

.tab-count {
  padding: 1px 6px;
  border-radius: var(--r-full);
  font-size: 10px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-2);
}

.tab-btn.active .tab-count {
  background: rgba(29, 185, 84, 0.2);
  color: var(--c-accent);
}

/* Content Area */
.deck-tab-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.tab-scroll-pane {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 16px 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tab-scroll-pane::-webkit-scrollbar {
  width: 6px;
}

.tab-scroll-pane::-webkit-scrollbar-track {
  background: transparent;
}

.tab-scroll-pane::-webkit-scrollbar-thumb {
  background: var(--c-bg-4);
  border-radius: var(--r-full);
}

.tab-scroll-pane::-webkit-scrollbar-thumb:hover {
  background: var(--c-text-3);
}

/* Lazy shuffle card */
.lazy-shuffle-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--r-lg);
  background: var(--c-bg-2);
  border: 1px solid rgba(29, 185, 84, 0.2);
  margin-bottom: 8px;
}

.lazy-icon {
  color: var(--c-accent);
}

.lazy-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.lazy-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--c-text-1);
}

.lazy-counter {
  font-size: 11px;
  font-family: var(--font-mono, monospace);
  color: var(--c-accent);
}

/* Track list */
.queue-track-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: var(--r-md);
  background: var(--c-bg-2);
  border: 1px solid rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}

.queue-item:hover {
  background: var(--c-bg-3);
  transform: translateX(3px);
  border-color: rgba(255, 255, 255, 0.06);
}

.queue-item.now-playing {
  background: rgba(29, 185, 84, 0.1);
  border-color: rgba(29, 185, 84, 0.3);
}

.queue-item.now-playing .item-title {
  color: var(--c-accent);
}

.queue-item.history-item {
  opacity: 0.75;
}

.queue-item.history-item:hover {
  opacity: 1;
}

.item-index {
  width: 24px;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  font-family: var(--font-mono, monospace);
  color: var(--c-text-3);
  flex-shrink: 0;
}

.item-index.history {
  color: var(--c-text-4);
}

.item-cover {
  width: 40px;
  height: 40px;
  border-radius: var(--r-sm);
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-bg-3);
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.initials {
  font-size: 13px;
  font-weight: 700;
  color: var(--c-accent);
}

.item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-artist {
  font-size: 12px;
  color: var(--c-text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-duration {
  font-size: 11px;
  font-family: var(--font-mono, monospace);
  color: var(--c-text-3);
  flex-shrink: 0;
}

/* Empty state */
.empty-deck-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px 24px;
  color: var(--c-text-3);
}

.empty-icon {
  opacity: 0.4;
}

.empty-text {
  font-size: 14px;
  font-weight: 500;
  margin: 0;
}

/* Lyrics container */
.lyrics-container {
  flex: 1;
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
