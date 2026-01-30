<template>
  <div class="queue-panel-wrapper">
    <!-- Context Information -->
    <div class="context-module" v-if="contextInfo">
      <div class="module-header">
        <span class="module-label">CONTEXT</span>
      </div>
      <div class="context-info">
        <div class="context-type">{{ contextType }}</div>
        <div class="context-name">{{ contextInfo.name || 'Unknown' }}</div>
        <div class="context-meta" v-if="contextInfo.tracks_count">
          {{ contextInfo.tracks_count }} tracks
        </div>
      </div>
    </div>

    <!-- Queue Panel -->
    <div class="queue-module">
      <div class="module-header">
        <span class="module-label">QUEUE</span>
        <span class="queue-count">{{ queueLength }} tracks</span>
      </div>
      
      <div class="queue-tabs">
        <button 
          class="queue-tab" 
          :class="{ active: activeQueueTab === 'upcoming' }"
          @click="activeQueueTab = 'upcoming'"
        >
          UP NEXT
        </button>
        <button 
          class="queue-tab" 
          :class="{ active: activeQueueTab === 'history' }"
          @click="activeQueueTab = 'history'"
        >
          HISTORY
        </button>
      </div>

      <div class="queue-list" ref="queueListRef">
        <!-- Upcoming tracks -->
        <template v-if="activeQueueTab === 'upcoming'">
          <div 
            v-for="(t, idx) in upcomingQueue" 
            :key="`q-${t.id}-${idx}`"
            class="queue-track"
            :class="{ active: idx === 0 }"
            @click="$emit('playFromQueue', idx)"
          >
            <div class="queue-track-number">{{ idx + 1 }}</div>
            <div class="queue-track-cover" :style="getTrackCoverStyle(t)">
              <img v-if="t.cover_url" :src="t.cover_url" alt="" />
              <span v-else>{{ getTrackInitials(t) }}</span>
            </div>
            <div class="queue-track-info">
              <div class="queue-track-title">{{ t.title || 'Unknown' }}</div>
              <div class="queue-track-artist">{{ t.artist || 'Unknown' }}</div>
            </div>
            <div class="queue-track-duration">{{ formatTime(t.duration) }}</div>
          </div>
          
          <div v-if="lazyShuffleMode" class="queue-lazy-info">
            <div class="lazy-icon">🔀</div>
            <div class="lazy-text">
              <span>Shuffle Mode</span>
              <span class="lazy-progress">{{ lazyShuffleIndex + 1 }} / {{ lazyShuffleTotal }}</span>
            </div>
          </div>
          
          <div v-if="!upcomingQueue.length && !lazyShuffleMode" class="queue-empty">
            <span>Queue is empty</span>
          </div>
        </template>

        <!-- History -->
        <template v-else>
          <div 
            v-for="(t, idx) in historyTracks" 
            :key="`h-${t.id}-${idx}`"
            class="queue-track history"
            @click="$emit('playFromHistory', idx)"
          >
            <div class="queue-track-number">-{{ historyTracks.length - idx }}</div>
            <div class="queue-track-cover" :style="getTrackCoverStyle(t)">
              <img v-if="t.cover_url" :src="t.cover_url" alt="" />
              <span v-else>{{ getTrackInitials(t) }}</span>
            </div>
            <div class="queue-track-info">
              <div class="queue-track-title">{{ t.title || 'Unknown' }}</div>
              <div class="queue-track-artist">{{ t.artist || 'Unknown' }}</div>
            </div>
            <div class="queue-track-duration">{{ formatTime(t.duration) }}</div>
          </div>
          
          <div v-if="!historyTracks.length" class="queue-empty">
            <span>No history</span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { getTrackCoverStyle, getTrackInitials } from '@/utils'

const props = defineProps({
  contextInfo: Object,
  queueLength: Number,
  upcomingQueue: Array,
  historyTracks: {
    type: Array,
    default: () => []
  },
  lazyShuffleMode: Boolean,
  lazyShuffleIndex: Number,
  lazyShuffleTotal: Number
})

defineEmits(['playFromQueue', 'playFromHistory'])

const activeQueueTab = ref('upcoming')

const contextType = computed(() => {
  if (!props.contextInfo) return ''
  // Basic mapping, assuming simple types or converting to uppercase
  return (props.contextInfo.type || 'CONTEXT').toUpperCase()
})

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.queue-panel-wrapper {
  display: flex;
  flex-direction: column;
  gap: 18px;
  overflow: hidden;
  flex: 1;
  min-height: 0;
}

/* Context Module */
.context-module {
  background: #12121e;
  border-radius: 20px;
  padding: 18px;
  box-shadow: 
    6px 6px 12px #000000,
    -6px -6px 12px #1a1a28;
}

.module-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.module-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #db2220;
  font-family: 'Segoe UI', sans-serif;
}

.context-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.context-type {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #e85c7c;
  font-family: 'Segoe UI', sans-serif;
}

.context-name {
  font-size: 16px;
  font-weight: 600;
  color: #e8ecf1;
}

.context-meta {
  font-size: 12px;
  color: #718096;
}

/* Queue Module */
.queue-module {
  flex: 1;
  background: #12121e;
  border-radius: 20px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  box-shadow: 
    6px 6px 12px #000000,
    -6px -6px 12px #1a1a28;
}

.queue-count {
  font-size: 11px;
  color: #718096;
  font-family: 'Segoe UI', sans-serif;
}

.queue-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.queue-tab {
  flex: 1;
  padding: 10px;
  border: none;
  background: #12121e;
  border-radius: 12px;
  color: #718096;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1.2px;
  font-family: 'Segoe UI', sans-serif;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 
    4px 4px 8px #08080f,
    -4px -4px 8px #1a1a28;
}

.queue-tab:hover {
  box-shadow: 
    3px 3px 6px #08080f,
    -3px -3px 6px #1a1a28;
  color: #db2220;
}

.queue-tab.active {
  background: linear-gradient(135deg, #db2220 0%, #e85c7c 100%);
  color: #ffffff;
  box-shadow: 
    inset 3px 3px 6px rgba(232, 92, 124, 0.4),
    4px 4px 8px #000000,
    -4px -4px 8px #1a1a28;
}

.queue-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.queue-list::-webkit-scrollbar {
  width: 8px;
}

.queue-list::-webkit-scrollbar-track {
  background: #12121e;
  border-radius: 10px;
  box-shadow: 
    inset 2px 2px 4px #08080f,
    inset -2px -2px 4px #1a1a28;
}

.queue-list::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #db2220 0%, #e85c7c 100%);
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(232, 92, 124, 0.4);
}

.queue-list::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #e85c7c 0%, #db2220 100%);
}

.queue-track {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 12px;
  margin-bottom: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #12121e;
}

.queue-track:hover {
  box-shadow: 
    4px 4px 8px #000000,
    -4px -4px 8px #1a1a28;
  transform: translateY(-1px);
}

.queue-track.active {
  background: linear-gradient(135deg, #db2220 0%, #e85c7c 100%);
  box-shadow: 
    6px 6px 12px #000000,
    -6px -6px 12px #1a1a28,
    inset 0 0 20px rgba(232, 92, 124, 0.4);
}

.queue-track.active .queue-track-title,
.queue-track.active .queue-track-artist,
.queue-track.active .queue-track-duration,
.queue-track.active .queue-track-number {
  color: #ffffff;
}

.queue-track.history {
  opacity: 0.8;
}

.queue-track-number {
  width: 28px;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: #db2220;
  font-family: 'Segoe UI', monospace;
  flex-shrink: 0;
}

.queue-track-cover {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a1a28;
  box-shadow: 
    inset 3px 3px 6px #08080f,
    inset -3px -3px 6px #1a1a28;
}

.queue-track-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.queue-track-cover span {
  font-size: 14px;
  font-weight: 600;
  color: #db2220;
}

.queue-track-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.queue-track-title {
  font-size: 13px;
  font-weight: 600;
  color: #e8ecf1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-track-artist {
  font-size: 11px;
  color: #718096;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-track-duration {
  font-size: 11px;
  color: #a0aec0;
  font-family: 'Segoe UI', monospace;
  flex-shrink: 0;
}

.queue-lazy-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #12121e;
  border-radius: 12px;
  margin-top: 8px;
  box-shadow: 
    inset 4px 4px 8px #08080f,
    inset -4px -4px 8px #1a1a28;
}

.lazy-icon {
  font-size: 24px;
}

.lazy-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #db2220;
  font-weight: 600;
}

.lazy-progress {
  font-size: 10px;
  color: #e85c7c;
  font-family: 'Segoe UI', monospace;
}

.queue-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 50px 20px;
  color: #a0aec0;
  font-size: 13px;
  font-family: 'Segoe UI', sans-serif;
}
</style>
