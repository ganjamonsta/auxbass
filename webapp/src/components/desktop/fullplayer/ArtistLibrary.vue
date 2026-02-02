<template>
  <div class="artist-library-section" v-if="track">
    <div class="library-header">
      <div class="library-title-section">
        <span class="library-label">ARTIST MEDIA</span>
        <span class="library-count">{{ sortedArtistTracks.length }} tracks</span>
      </div>
      <div class="sort-controls">
        <button 
          class="sort-btn" 
          :class="{ active: artistSort === 'title' }"
          @click="artistSort = 'title'"
          title="По названию"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 18h6v-2H3v2zM3 6v2h18V6H3zm0 7h12v-2H3v2z"/>
          </svg>
        </button>
        <button 
          class="sort-btn" 
          :class="{ active: artistSort === 'year' }"
          @click="artistSort = 'year'"
          title="По году"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 11H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2zm2-7h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V9h14v11z"/>
          </svg>
        </button>
        <button 
          class="sort-btn" 
          :class="{ active: artistSort === 'plays' }"
          @click="artistSort = 'plays'"
          title="По популярности"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z"/>
          </svg>
        </button>
        <button 
          class="sort-btn" 
          :class="{ active: artistSort === 'duration' }"
          @click="artistSort = 'duration'"
          title="По длительности"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/>
          </svg>
        </button>
      </div>
    </div>
    
    <div class="artist-tracks-list">
      <div v-if="isLoadingArtistTracks" class="artist-tracks-empty">
        <span>Загрузка...</span>
      </div>
      <template v-else>
        <div 
          v-for="(t, idx) in sortedArtistTracks" 
          :key="`artist-${t.id}-${idx}`"
          class="artist-track-item"
          :class="{ active: t.id === track?.id }"
          @click="handlePlayArtistTrack(t)"
        >
          <div class="artist-track-number">{{ idx + 1 }}</div>
          <div class="artist-track-cover" :style="getTrackCoverStyle(t)">
            <img v-if="t.cover_url" :src="getCoverUrl(t.cover_url, CoverSize.SMALL)" alt="" />
            <span v-else>{{ getTrackInitials(t) }}</span>
          </div>
          <div class="artist-track-info">
            <div class="artist-track-title">{{ t.title || 'Unknown' }}</div>
            <div class="artist-track-meta">
              <span v-if="t.album_title">{{ t.album_title }}</span>
              <span v-if="t.year" class="track-year">{{ t.year }}</span>
            </div>
          </div>
          <div class="artist-track-stats">
            <span v-if="t.play_count" class="plays" title="Прослушиваний">{{ t.play_count }}</span>
            <span class="duration">{{ formatTime(t.duration) }}</span>
          </div>
        </div>
        
        <div v-if="!sortedArtistTracks.length" class="artist-tracks-empty">
          <span v-if="!track?.artist">Нет информации об артисте</span>
          <span v-else>Треки {{ track.artist }} не найдены в библиотеке</span>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { tracksApi } from '@/api/client'
import { getTrackCoverStyle, getTrackInitials, getCoverUrl, CoverSize } from '@/utils'

const props = defineProps({
  track: Object
})

const emit = defineEmits(['play'])

const artistTracks = ref([])
const isLoadingArtistTracks = ref(false)
const artistSort = ref('plays')

const loadArtistTracks = async () => {
  if (!props.track?.artist) {
    artistTracks.value = []
    return
  }
  
  isLoadingArtistTracks.value = true
  try {
    const { data } = await tracksApi.getArtistDetail(props.track.artist, 'library')
    artistTracks.value = data.tracks || []
  } catch (e) {
    console.error('Failed to load artist tracks:', e)
    artistTracks.value = []
  } finally {
    isLoadingArtistTracks.value = false
  }
}

watch(() => props.track?.artist, (newVal) => {
  if (newVal) {
    loadArtistTracks()
  } else {
    artistTracks.value = []
  }
}, { immediate: true })

const sortedArtistTracks = computed(() => {
  const tracks = [...artistTracks.value]
  
  switch (artistSort.value) {
    case 'title':
      return tracks.sort((a, b) => (a.title || '').localeCompare(b.title || ''))
    case 'year':
      return tracks.sort((a, b) => (b.year || 0) - (a.year || 0))
    case 'plays':
      return tracks.sort((a, b) => (b.play_count || 0) - (a.play_count || 0))
    case 'duration':
      return tracks.sort((a, b) => (b.duration || 0) - (a.duration || 0))
    default:
      return tracks
  }
})

const handlePlayArtistTrack = (t) => {
  emit('play', t)
}

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.artist-library-section {
  margin-top: 15px;
  background: #12121e;
  border-radius: 24px;
  padding: 18px;
  box-shadow: 
    inset 6px 6px 12px #08080f,
    inset -6px -6px 12px #1a1a28;
  min-height: 250px;
  max-height: 400px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.library-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(232, 92, 124, 0.1);
}

.library-title-section {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.library-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.5px;
  color: #e85c7c;
  font-family: 'Segoe UI', sans-serif;
}

.library-count {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1px;
  color: #9ca3af;
  font-family: 'Segoe UI', sans-serif;
}

.sort-controls {
  display: flex;
  gap: 8px;
}

.sort-btn {
  width: 32px;
  height: 32px;
  background: #12121e;
  border: none;
  border-radius: 10px;
  color: #9ca3af;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 
    4px 4px 8px #08080f,
    -4px -4px 8px #1a1a28;
}

.sort-btn:hover {
  color: #e85c7c;
  box-shadow: 
    2px 2px 6px #08080f,
    -2px -2px 6px #1a1a28;
}

.sort-btn.active {
  color: #e85c7c;
  box-shadow: 
    inset 3px 3px 6px #08080f,
    inset -3px -3px 6px #1a1a28;
}

.artist-tracks-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 8px;
}

.artist-tracks-list::-webkit-scrollbar {
  width: 6px;
}

.artist-tracks-list::-webkit-scrollbar-track {
  background: transparent;
}

.artist-tracks-list::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #e85c7c 0%, #ff8ba8 100%);
  border-radius: 3px;
}

.artist-track-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: #12121e;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 
    4px 4px 8px #08080f,
    -4px -4px 8px #1a1a28;
}

.artist-track-item:hover {
  box-shadow: 
    2px 2px 6px #08080f,
    -2px -2px 6px #1a1a28;
  transform: translateY(-1px);
}

.artist-track-item.active {
  background: linear-gradient(135deg, rgba(232, 92, 124, 0.15) 0%, rgba(255, 139, 168, 0.1) 100%);
  box-shadow: 
    inset 3px 3px 6px #08080f,
    inset -3px -3px 6px #1a1a28,
    0 0 20px rgba(232, 92, 124, 0.2);
}

.artist-track-number {
  width: 24px;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: #9ca3af;
  font-family: 'Segoe UI', sans-serif;
}

.artist-track-item.active .artist-track-number {
  color: #e85c7c;
}

.artist-track-cover {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a28 0%, #0f0f1a 100%);
  box-shadow: 
    inset 2px 2px 4px #08080f,
    inset -2px -2px 4px #1a1a28;
}

.artist-track-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.artist-track-cover span {
  font-size: 14px;
  font-weight: 600;
  color: #e85c7c;
}

.artist-track-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.artist-track-title {
  font-size: 13px;
  font-weight: 600;
  color: #e8ecf1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.artist-track-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #9ca3af;
}

.track-year {
  color: #ff8ba8;
  font-weight: 600;
}

.artist-track-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 11px;
  color: #9ca3af;
}

.artist-track-stats .plays {
  color: #ff8ba8;
  font-weight: 600;
}

.artist-track-stats .duration {
  font-weight: 600;
  color: #e8ecf1;
}

.artist-tracks-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: #9ca3af;
  font-size: 13px;
}
</style>
