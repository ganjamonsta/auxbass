<template>
  <div class="track-info-section" v-if="track">
    <!-- Meta badges (HD, Year, Bitrate) -->
    <div class="meta-badges">
      <span v-if="hdTrackInfo" class="badge-hd" title="Доступна HD версия">HD</span>
      <span v-if="track.bitrate" class="badge-pill">{{ track.bitrate }} kbps</span>
      <span v-if="track.year" class="badge-pill">{{ track.year }}</span>
      <span v-if="track.genre" class="badge-pill genre">{{ track.genre }}</span>
    </div>

    <!-- Title and Artists -->
    <div class="title-block">
      <h1 class="track-title" :title="track.title || 'Без названия'">
        {{ track.title || 'Без названия' }}
      </h1>

      <div class="artists-row">
        <template v-if="parsedArtists.length > 0">
          <template v-for="(artist, index) in parsedArtists" :key="artist">
            <button 
              class="artist-link"
              @click="$emit('goToArtist', artist)"
              @contextmenu.prevent="openArtistMenu(artist, $event)"
              :title="`Перейти к ${artist}`"
            >
              {{ artist }}
            </button>
            <span v-if="index < parsedArtists.length - 1" class="artist-separator">, </span>
          </template>
        </template>
        <span v-else class="artist-unknown">Неизвестный исполнитель</span>
      </div>

      <!-- Album link -->
      <button 
        v-if="track.album_title || track.album?.name" 
        class="album-link"
        @click="$emit('goToAlbum')"
        :title="`Альбом: ${track.album_title || track.album?.name}`"
      >
        <Disc3 :size="14" class="album-icon" />
        <span class="album-title">{{ track.album_title || track.album?.name }}</span>
      </button>
    </div>

    <!-- Interactive tags with upvoting -->
    <div class="tags-container" v-if="track.id">
      <TrackTags
        :trackId="track.id"
        :tags="track.tags || []"
        :interactive="true"
        :max="6"
        @tagClick="(tag) => $emit('tagClick', tag)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { splitArtists } from '@/utils/formatters'
import { useContextMenu } from '@/composables/useContextMenu'
import { Disc3 } from 'lucide-vue-next'
import TrackTags from '@/components/TrackTags.vue'

const props = defineProps({
  track: Object,
  hdTrackInfo: Object,
  isLiked: Boolean
})

const emit = defineEmits(['goToAlbum', 'goToArtist', 'tagClick'])

const { openMenu } = useContextMenu()

const parsedArtists = computed(() => {
  if (!props.track?.artist) return []
  return splitArtists(props.track.artist)
})

const openArtistMenu = (artistName, event) => {
  openMenu('artist', { name: artistName }, 'player', event)
}
</script>

<style scoped>
.track-info-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  width: 100%;
  gap: 10px;
  padding: 0 16px;
}

.meta-badges {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.badge-hd {
  padding: 2px 8px;
  border-radius: var(--r-xs);
  background: linear-gradient(135deg, #ffd700 0%, #ffb700 100%);
  color: #000;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.8px;
  box-shadow: 0 2px 6px rgba(255, 215, 0, 0.3);
}

.badge-pill {
  padding: 3px 10px;
  border-radius: var(--r-full);
  background: var(--c-bg-2);
  color: var(--c-text-3);
  font-size: 11px;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.badge-pill.genre {
  color: var(--c-accent);
  background: rgba(29, 185, 84, 0.08);
  border-color: rgba(29, 185, 84, 0.2);
}

.title-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 100%;
  max-width: 500px;
}

.track-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--c-text-1);
  line-height: 1.25;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.artists-row {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 4px;
  max-width: 100%;
}

.artist-link {
  background: none;
  border: none;
  padding: 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--c-text-2);
  cursor: pointer;
  transition: color 0.18s ease;
  line-height: 1.4;
}

.artist-link:hover {
  color: var(--c-accent);
  text-decoration: underline;
}

.artist-separator {
  color: var(--c-text-3);
  font-size: 14px;
}

.artist-unknown {
  font-size: 15px;
  color: var(--c-text-3);
}

.album-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  padding: 4px 10px;
  border-radius: var(--r-full);
  color: var(--c-text-3);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 2px;
}

.album-link:hover {
  color: var(--c-text-1);
  background: var(--c-bg-2);
}

.album-icon {
  color: var(--c-accent);
}

.album-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 320px;
}

.tags-container {
  margin-top: 4px;
  display: flex;
  justify-content: center;
  max-width: 500px;
}
</style>
