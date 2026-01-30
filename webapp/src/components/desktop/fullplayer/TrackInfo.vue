<template>
  <div class="info-module primary">
    <div class="module-header">
      <span class="module-label">TRACK DATA</span>
      <div class="module-indicators">
        <span v-if="hdTrackInfo" class="indicator hd" title="HD версия доступна">HD</span>
        <span v-if="isLiked" class="indicator liked">♥</span>
      </div>
    </div>
    
    <div class="track-display">
      <h2 class="track-title-main">{{ track?.title || 'UNKNOWN TRACK' }}</h2>
      <p class="track-artist-main">{{ track?.artist || 'UNKNOWN ARTIST' }}</p>
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
      <div class="meta-item" v-if="track?.genre">
        <span class="meta-label">GENRE</span>
        <span class="meta-value">{{ track.genre }}</span>
      </div>
      <div class="meta-item" v-if="track?.duration">
        <span class="meta-label">DURATION</span>
        <span class="meta-value">{{ formatTime(track.duration) }}</span>
      </div>
      <div class="meta-item" v-if="track?.bitrate">
        <span class="meta-label">QUALITY</span>
        <span class="meta-value">{{ track.bitrate }} kbps</span>
      </div>
      <div class="meta-item" v-if="track?.play_count !== undefined">
        <span class="meta-label">PLAYS</span>
        <span class="meta-value">{{ track.play_count }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  track: Object,
  hdTrackInfo: Object,
  isLiked: Boolean
})

defineEmits(['goToAlbum'])

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
  box-shadow: 
    8px 8px 20px #000000,
    -8px -8px 20px #1a1a28;
}

.module-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  padding-bottom: 12px;
  border-bottom: 2px solid #1a1a28;
}

.module-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #db2220;
  font-family: 'Segoe UI', sans-serif;
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
  box-shadow: 
    3px 3px 6px #000000,
    -3px -3px 6px #1a1a28;
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
}

.track-title-main {
  font-size: 32px;
  font-weight: 700;
  color: #e8ecf1;
  margin: 0 0 10px 0;
  line-height: 1.2;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.6);
}

.track-artist-main {
  font-size: 20px;
  color: #a0aec0;
  margin: 0;
  font-weight: 500;
}

.metadata-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background: #12121e;
  border-radius: 12px;
  box-shadow: 
    inset 3px 3px 6px #08080f,
    inset -3px -3px 6px #1a1a28;
}

.meta-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1.5px;
  color: #e85c7c;
  font-family: 'Segoe UI', sans-serif;
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
