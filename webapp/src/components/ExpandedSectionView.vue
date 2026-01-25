<script setup>
import PlaylistItem from './PlaylistItem.vue'

const props = defineProps({
  section: { type: String, default: null }, // 'albums', 'sources', 'playlists'
  albumPlaylists: { type: Array, default: () => [] },
  sourcePlaylists: { type: Array, default: () => [] },
  userPlaylists: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'openPlaylist', 'createPlaylist'])

const sectionTitle = {
  'albums': 'Альбомы',
  'sources': 'Источники',
  'playlists': 'Мои плейлисты',
}

const currentPlaylists = computed(() => {
  switch (props.section) {
    case 'albums': return props.albumPlaylists
    case 'sources': return props.sourcePlaylists
    case 'playlists': return props.userPlaylists
    default: return []
  }
})
</script>

<template>
  <Transition name="slide-up">
    <div v-if="section" class="expanded-section">
      <div class="expanded-header">
        <button @click="$emit('close')" class="icon-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
        </button>
        <h2 class="expanded-title">{{ sectionTitle[section] }}</h2>
        <button v-if="section === 'playlists'" @click="$emit('createPlaylist')" class="icon-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
          </svg>
        </button>
        <div v-else class="spacer"></div>
      </div>
      
      <div class="expanded-grid">
        <PlaylistItem
          v-for="playlist in currentPlaylists"
          :key="playlist.id"
          :playlist="playlist"
          @click="$emit('openPlaylist', playlist)"
        />
        <div v-if="section === 'playlists' && userPlaylists.length === 0" class="empty-section">
          <span class="empty-icon">📁</span>
          <p>Нет плейлистов</p>
          <button @click="$emit('createPlaylist')" class="create-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
            </svg>
            Создать
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script>
import { computed } from 'vue'
</script>

<style scoped>
.expanded-section {
  position: fixed;
  inset: 0;
  background: var(--spotify-black);
  z-index: 60;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.expanded-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--spotify-gray-dark);
  flex-shrink: 0;
}

.expanded-title {
  flex: 1;
  font-size: 18px;
  font-weight: 600;
  color: var(--spotify-text);
}

.expanded-grid {
  flex: 1;
  overflow-y: overlay;
  scrollbar-gutter: auto;
  padding: 12px;
  padding-bottom: 120px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  gap: 12px;
  align-content: start;
}

.empty-section {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  color: var(--spotify-text-secondary);
}

.empty-section .empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-section p {
  margin-bottom: 16px;
}

.icon-btn {
  width: 44px;
  height: 44px;
  border: none;
  background: var(--neu-bg);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--spotify-text);
  transition: all 0.2s ease;
  box-shadow: 
    5px 5px 10px var(--neu-shadow-dark),
    -2px -2px 6px var(--neu-shadow-light);
}

.icon-btn:active {
  box-shadow: 
    inset 3px 3px 6px var(--neu-shadow-dark),
    inset -2px -2px 4px var(--neu-shadow-light);
  transform: scale(0.95);
}

.spacer {
  width: 44px;
}

.create-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  border: 1px dashed var(--spotify-gray-light);
  border-radius: 8px;
  background: transparent;
  color: var(--spotify-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.create-btn svg {
  width: 18px;
  height: 18px;
}

.create-btn:active {
  background: var(--spotify-gray);
  border-color: var(--spotify-green);
  color: var(--spotify-green);
}

/* Slide up transition */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>
