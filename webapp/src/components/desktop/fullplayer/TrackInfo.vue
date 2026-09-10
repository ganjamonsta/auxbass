<template>
  <div class="dj-rack-display neu-lcd" v-if="track">
    <!-- Top info bar: Title and HD/Quality -->
    <div class="lcd-header-row">
      <div class="track-title-wrapper" :title="track.title || 'Без названия'">
        <h2 class="lcd-title">{{ track.title || 'Без названия' }}</h2>
      </div>

      <div class="lcd-quality-badges">
        <span v-if="hdTrackInfo" class="badge-hd">HD</span>
        <span v-if="track.bitrate" class="badge-rate">{{ track.bitrate }}K</span>
      </div>
    </div>

    <!-- Middle row: Artist & Album -->
    <div class="lcd-meta-row">
      <div class="artists-box">
        <span class="meta-label">ARTIST:</span>
        <template v-if="parsedArtists.length > 0">
          <template v-for="(artist, index) in parsedArtists" :key="artist">
            <button 
              class="artist-btn"
              @click="$emit('goToArtist', artist)"
              @contextmenu.prevent="openArtistMenu(artist, $event)"
              :title="`Перейти к ${artist}`"
            >
              {{ artist }}
            </button>
            <span v-if="index < parsedArtists.length - 1" class="sep">, </span>
          </template>
        </template>
        <span v-else class="artist-muted">Неизвестно</span>
      </div>

      <button 
        v-if="track.album_title || track.album?.name" 
        class="album-badge-btn"
        @click="$emit('goToAlbum')"
        :title="`Альбом: ${track.album_title || track.album?.name}`"
      >
        <Disc3 :size="12" class="album-icon" />
        <span class="album-text">{{ track.album_title || track.album?.name }}</span>
      </button>
    </div>

    <!-- Bottom row: Tags / Key metadata in single compact row -->
    <div class="lcd-tags-row" v-if="track.tags?.length || track.genre || track.year">
      <span v-if="track.year" class="lcd-tag year">{{ track.year }}</span>
      <span v-if="track.genre" class="lcd-tag genre">{{ track.genre }}</span>
      <template v-for="(tag, idx) in visibleTags" :key="idx">
        <button 
          class="lcd-tag interactive"
          @click="$emit('tagClick', tag)"
          :title="`Искать по тегу #${tag}`"
        >
          #{{ tag.replace(/^#/, '') }}
        </button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { splitArtists } from '@/utils/formatters'
import { useContextMenu } from '@/composables/useContextMenu'
import { Disc3 } from 'lucide-vue-next'

const props = defineProps({
  track: Object,
  hdTrackInfo: Object,
  isLiked: Boolean
})

defineEmits(['goToAlbum', 'goToArtist', 'tagClick'])

const { openMenu } = useContextMenu()

const parsedArtists = computed(() => {
  if (!props.track?.artist) return []
  return splitArtists(props.track.artist)
})

const visibleTags = computed(() => {
  if (!props.track?.tags) return []
  // Keep up to 4 tags to fit in a single line without wrapping
  return props.track.tags.slice(0, 4)
})

const openArtistMenu = (artistName, event) => {
  openMenu('artist', { name: artistName }, 'player', event)
}
</script>

<style scoped>
.dj-rack-display {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  max-width: 440px;
  padding: 10px 14px;
  background: #080d14;
  border-radius: var(--r-sm);
  border: 1px solid #142233;
  box-shadow: 
    inset 0 2px 6px rgba(0, 0, 0, 0.9),
    0 1px 0 rgba(77, 195, 255, 0.08);
  position: relative;
  overflow: hidden;
  user-select: none;
  flex-shrink: 0;
}

/* Subtle CRT Scanline overlay */
.dj-rack-display::before {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.25) 2px,
    rgba(0, 0, 0, 0.25) 4px
  );
  pointer-events: none;
}

.lcd-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.track-title-wrapper {
  flex: 1;
  min-width: 0;
}

.lcd-title {
  font-size: 17px;
  font-weight: 800;
  color: #e6f6ff;
  line-height: 1.2;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: var(--font-sans);
  text-shadow: 0 0 8px rgba(77, 195, 255, 0.4);
}

.lcd-quality-badges {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.badge-hd {
  font-size: 9px;
  font-weight: 900;
  padding: 1px 5px;
  border-radius: 2px;
  background: #ffd700;
  color: #000000;
  font-family: var(--font-mono, monospace);
  box-shadow: 0 0 6px rgba(255, 215, 0, 0.6);
}

.badge-rate {
  font-size: 9px;
  font-weight: 800;
  padding: 1px 5px;
  border-radius: 2px;
  background: rgba(29, 185, 84, 0.2);
  color: var(--c-accent);
  border: 1px solid rgba(29, 185, 84, 0.4);
  font-family: var(--font-mono, monospace);
}

/* Meta row: Artist & Album */
.lcd-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.artists-box {
  display: flex;
  align-items: baseline;
  gap: 4px;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.meta-label {
  font-size: 9px;
  font-weight: 800;
  color: #3b7099;
  font-family: var(--font-mono, monospace);
  flex-shrink: 0;
}

.artist-btn {
  background: none;
  border: none;
  padding: 0;
  color: #8ed6ff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.artist-btn:hover {
  color: #ffffff;
  text-decoration: underline;
  text-shadow: 0 0 8px rgba(77, 195, 255, 0.8);
}

.sep {
  color: #3b7099;
}

.artist-muted {
  font-size: 12px;
  color: #3b7099;
}

.album-badge-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 2px 8px;
  border-radius: var(--r-xs);
  color: #8ed6ff;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  flex-shrink: 0;
  max-width: 160px;
  transition: all 0.15s ease;
}

.album-badge-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.album-icon {
  color: var(--c-accent);
}

.album-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Compact Tags row */
.lcd-tags-row {
  display: flex;
  align-items: center;
  gap: 5px;
  overflow: hidden;
  white-space: nowrap;
}

.lcd-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 2px;
  background: rgba(77, 195, 255, 0.08);
  color: #64b5f6;
  border: 1px solid rgba(77, 195, 255, 0.15);
  font-family: var(--font-mono, monospace);
  flex-shrink: 0;
}

.lcd-tag.year {
  color: var(--c-accent);
  border-color: rgba(29, 185, 84, 0.3);
  background: rgba(29, 185, 84, 0.1);
}

.lcd-tag.genre {
  color: #ffd700;
  border-color: rgba(255, 215, 0, 0.3);
}

.lcd-tag.interactive {
  cursor: pointer;
  background: rgba(255, 255, 255, 0.04);
  color: #8ed6ff;
  transition: all 0.15s ease;
}

.lcd-tag.interactive:hover {
  background: rgba(77, 195, 255, 0.2);
  color: #ffffff;
  border-color: rgba(77, 195, 255, 0.4);
}
</style>
