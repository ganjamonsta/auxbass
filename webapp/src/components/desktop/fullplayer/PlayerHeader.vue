<template>
  <header class="player-header">
    <div class="header-left">
      <div class="playing-badge" :class="{ active: isPlaying }">
        <div class="equalizer" v-if="isPlaying">
          <span class="equalizer-bar"></span>
          <span class="equalizer-bar"></span>
          <span class="equalizer-bar"></span>
        </div>
        <span class="status-dot" v-else></span>
        <span class="badge-text">{{ isPlaying ? 'СЕЙЧАС ИГРАЕТ' : 'ПАУЗА' }}</span>
      </div>

      <div v-if="contextTitle" class="context-pill" :title="contextTitle">
        <span class="context-type">{{ contextTypeLabel }}</span>
        <span class="context-name">{{ contextTitle }}</span>
      </div>
    </div>

    <div class="header-right">
      <button 
        class="neu-btn-icon sm close-btn" 
        @click="$emit('close')" 
        title="Свернуть (Esc)"
        aria-label="Закрыть"
      >
        <X :size="18" />
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { X } from 'lucide-vue-next'

const props = defineProps({
  isPlaying: Boolean,
  contextInfo: Object,
  track: Object
})

defineEmits(['close'])

const contextTypeLabel = computed(() => {
  if (!props.contextInfo?.type) return ''
  const typeMap = {
    playlist: 'ПЛЕЙЛИСТ',
    album: 'АЛЬБОМ',
    artist: 'АРТИСТ',
    favorites: 'ИЗБРАННОЕ',
    channel: 'КАНАЛ',
    history: 'ИСТОРИЯ'
  }
  return typeMap[props.contextInfo.type.toLowerCase()] || props.contextInfo.type.toUpperCase()
})

const contextTitle = computed(() => {
  if (props.contextInfo?.name) return props.contextInfo.name
  if (props.track?.album_title) return props.track.album_title
  return ''
})
</script>

<style scoped>
.player-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 32px 14px;
  width: 100%;
  flex-shrink: 0;
  position: relative;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.playing-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: var(--r-full);
  background: var(--c-bg-1);
  border: 1px solid rgba(255, 255, 255, 0.04);
  box-shadow: inset 1px 1px 2px var(--sh-inset-dark), inset -1px -1px 2px var(--sh-inset-light);
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--c-text-3);
  transition: all 0.2s ease;
}

.playing-badge.active .status-dot {
  background: var(--c-accent);
  box-shadow: 0 0 8px var(--c-accent-glow);
}

.badge-text {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.2px;
  color: var(--c-text-2);
}

.playing-badge.active .badge-text {
  color: var(--c-accent);
}

.context-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: var(--r-full);
  background: var(--c-bg-2);
  border: 1px solid rgba(255, 255, 255, 0.04);
  max-width: 320px;
}

.context-type {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--c-text-3);
}

.context-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.close-btn {
  color: var(--c-text-2);
  transition: all 0.2s ease;
}

.close-btn:hover {
  color: var(--c-text-1);
  transform: scale(1.05);
}
</style>
