<template>
  <div class="info-module primary">
    <div class="module-header">
      <div class="header-left">
        <span class="module-label">TRACK DATA</span>
        <div class="header-tags" v-if="track">
          <div class="header-tag" v-if="track.genre">
            <span class="tag-label">GENRE</span>
            <span class="tag-value">{{ track.genre }}</span>
          </div>
          <div class="header-tag" v-if="track.duration">
            <span class="tag-label">DURATION</span>
            <span class="tag-value">{{ formatTime(track.duration) }}</span>
          </div>
          <div class="header-tag" v-if="track.play_count !== undefined">
            <span class="tag-label">PLAYS</span>
            <span class="tag-value">{{ track.play_count }}</span>
          </div>
        </div>
      </div>
      <div class="module-indicators">
        <span v-if="hdTrackInfo" class="indicator hd" title="HD версия доступна">HD</span>
        <span v-if="isLiked" class="indicator liked">♥</span>
      </div>
    </div>
    
    <div class="track-display">
      <h2 class="track-title-main">{{ track?.title || 'UNKNOWN TRACK' }}</h2>
      <p class="track-artist-main">
        <template v-if="parsedArtists.length > 0">
          <template v-for="(artist, index) in parsedArtists" :key="artist">
            <span 
              class="artist-link"
              @click="$emit('goToArtist', artist)"
            >{{ artist }}</span>
            <span v-if="index < parsedArtists.length - 1" class="artist-sep">, </span>
          </template>
        </template>
        <span v-else>UNKNOWN ARTIST</span>
      </p>
    </div>

    <!-- Track metadata grid -->
    <div class="metadata-grid">
      <div class="meta-item" v-if="track?.album_title">
        <span class="meta-label">ALBUM</span>
        <span class="meta-value clickable" @click="$emit('goToAlbum')">{{ track.album_title }}</span>
      </div>
      <div class="meta-item" v-if="track?.year">
        <span class="meta-label">YEAR</span>
        <span class="meta-value">{{ track.year }}</span>
      </div>
      <div class="meta-item" v-if="track?.bitrate">
        <span class="meta-label">QUALITY</span>
        <span class="meta-value">{{ track.bitrate }} kbps</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { splitArtists } from '@/utils/formatters'

const props = defineProps({
  track: Object,
  hdTrackInfo: Object,
  isLiked: Boolean
})

defineEmits(['goToAlbum', 'goToArtist'])

// Parse artists into separate names
const parsedArtists = computed(() => {
  if (!props.track?.artist) return []
  return splitArtists(props.track.artist)
})

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.info-module {
  background: #12121e;
  border-radius: 25px;
  padding: 25px;
  @apply shadow-neu-raised;
}

.module-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  padding-bottom: 12px;
  border-bottom: 1px solid #1a1a28;
}

.module-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #db2220;
  font-family: 'Segoe UI', sans-serif;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.header-tags {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-tag {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tag-label {
  font-size: 10px;
  font-weight: 700;
  color: #e85c7c;
  letter-spacing: 0.5px;
  opacity: 0.8;
  text-transform: uppercase;
}

.tag-label::after {
  content: ":";
}

.tag-value {
  font-size: 11px;
  font-weight: 600;
  color: #cbd5e0;
}

.module-indicators {
  display: flex;
  gap: 8px;
}

.indicator {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  font-family: 'Segoe UI', sans-serif;
  @apply shadow-neu-raised-sm;
}
.indicator.hd {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #8b7300;
}

.indicator.liked {
  background: linear-gradient(135deg, #ff6b9d 0%, #ff8bb3 100%);
  color: #9a0036;
}

.track-display {
  margin-bottom: 20px;
  text-align: center;
  width: 100%;
}

.track-title-main {
  font-size: 36px;
  font-weight: 700;
  color: #e8ecf1;
  margin: 0 0 10px 0;
  line-height: 1.3;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.6);
  width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.track-artist-main {
  font-size: 22px;
  color: #a0aec0;
  margin: 0;
  font-weight: 500;
  width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.track-artist-main .artist-link {
  cursor: pointer;
  transition: color 0.2s ease;
}

.track-artist-main .artist-link:hover {
  color: #1DB954;
  text-decoration: underline;
}

.track-artist-main .artist-sep {
  color: #6b7a8c;
}

.metadata-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.meta-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: #12121e;
  border-radius: 8px;
  @apply shadow-neu-inset;
}

.meta-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1px;
  color: #e85c7c;
  font-family: 'Segoe UI', sans-serif;
  opacity: 0.8;
}

.meta-label::after {
  content: ":";
}

.meta-value {
  font-size: 14px;
  color: #e8ecf1;
  font-weight: 600;
}

.meta-value.clickable {
  cursor: pointer;
  color: #db2220;
  transition: all 0.2s ease;
}

.meta-value.clickable:hover {
  color: #e85c7c;
  text-shadow: 0 2px 4px rgba(232, 92, 124, 0.3);
}
</style>
