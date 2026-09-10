<template>
  <div class="artist-library-container" v-if="track">
    <!-- Header with count & sort options -->
    <div class="library-toolbar">
      <div class="library-heading">
        <span class="toolbar-title">ТРЕКИ АРТИСТА</span>
        <span class="toolbar-count" v-if="sortedArtistTracks.length">{{ sortedArtistTracks.length }}</span>
      </div>

      <div class="sort-segmented neu-surface">
        <button 
          class="sort-pill" 
          :class="{ active: artistSort === 'plays' }"
          @click="artistSort = 'plays'"
          title="По популярности"
        >
          <Flame :size="13" />
          <span>Топ</span>
        </button>
        <button 
          class="sort-pill" 
          :class="{ active: artistSort === 'year' }"
          @click="artistSort = 'year'"
          title="По году"
        >
          <Calendar :size="13" />
          <span>Год</span>
        </button>
        <button 
          class="sort-pill" 
          :class="{ active: artistSort === 'title' }"
          @click="artistSort = 'title'"
          title="По названию"
        >
          <ArrowDownAZ :size="13" />
          <span>А-Я</span>
        </button>
      </div>
    </div>

    <!-- Tracks list -->
    <div class="artist-tracks-scroll">
      <!-- Loading state -->
      <div v-if="isLoadingArtistTracks" class="loading-state">
        <div class="spinner"></div>
        <span>Загрузка треков...</span>
      </div>

      <!-- Loaded track items -->
      <template v-else-if="sortedArtistTracks.length > 0">
        <div 
          v-for="(t, idx) in sortedArtistTracks" 
          :key="`artist-${t.id}-${idx}`"
          class="artist-track-item"
          :class="{ 'is-current': t.id === track?.id }"
          @click="$emit('play', t)"
        >
          <div class="track-number">
            <span v-if="t.id === track?.id" class="now-playing-dot"></span>
            <span v-else>{{ idx + 1 }}</span>
          </div>

          <div class="track-cover" :style="getTrackCoverStyle(t)">
            <img 
              v-if="t.cover_url" 
              :src="getCoverUrl(t.cover_url, CoverSize.SMALL)" 
              alt="" 
              class="cover-img"
            />
            <span v-else class="initials">{{ getTrackInitials(t) }}</span>
          </div>

          <div class="track-info">
            <span class="track-name">{{ t.title || 'Без названия' }}</span>
            <div class="track-meta">
              <span v-if="t.album_title" class="album-name">{{ t.album_title }}</span>
              <span v-if="t.year" class="year-tag">{{ t.year }}</span>
            </div>
          </div>

          <div class="track-stats">
            <span v-if="t.play_count" class="play-count" title="Прослушиваний">
              <Headphones :size="11" />
              {{ t.play_count }}
            </span>
            <span class="duration">{{ formatTime(t.duration) }}</span>
          </div>
        </div>
      </template>

      <!-- Empty state -->
      <div v-else class="empty-state">
        <Music2 :size="32" class="empty-icon" />
        <span v-if="!track?.artist">Имя исполнителя не указано</span>
        <span v-else>Другие треки {{ track.artist }} не найдены</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Flame, Calendar, ArrowDownAZ, Headphones, Music2 } from 'lucide-vue-next'
import { tracksApi } from '@/api/client'
import { useTrackSync } from '@/composables/useTrackSync'
import { getTrackCoverStyle, getTrackInitials, getCoverUrl, CoverSize } from '@/utils'

const props = defineProps({
  track: Object
})

defineEmits(['play'])

const artistTracks = ref([])
const isLoadingArtistTracks = ref(false)
const artistSort = ref('plays')

useTrackSync(artistTracks)

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
    default:
      return tracks
  }
})

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds) || seconds < 0) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.artist-library-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.library-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-shrink: 0;
  padding-right: 6px;
}

.library-heading {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.2px;
  color: var(--c-text-3);
}

.toolbar-count {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: var(--r-full);
  background: var(--c-bg-2);
  color: var(--c-text-2);
}

.sort-segmented {
  display: flex;
  gap: 2px;
  padding: 2px;
  border-radius: var(--r-full);
  background: var(--c-bg-1);
}

.sort-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: none;
  border-radius: var(--r-full);
  background: transparent;
  color: var(--c-text-3);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.sort-pill:hover {
  color: var(--c-text-1);
}

.sort-pill.active {
  background: var(--c-bg-3);
  color: var(--c-accent);
}

.artist-tracks-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.artist-tracks-scroll::-webkit-scrollbar {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
}

.artist-track-item {
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

.artist-track-item:hover {
  background: var(--c-bg-3);
  transform: translateX(3px);
  border-color: rgba(255, 255, 255, 0.06);
}

.artist-track-item.is-current {
  background: rgba(29, 185, 84, 0.1);
  border-color: rgba(29, 185, 84, 0.3);
}

.artist-track-item.is-current .track-name {
  color: var(--c-accent);
}

.track-number {
  width: 20px;
  text-align: center;
  font-size: 11px;
  font-weight: 600;
  font-family: var(--font-mono, monospace);
  color: var(--c-text-3);
  flex-shrink: 0;
}

.now-playing-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--c-accent);
  box-shadow: 0 0 8px var(--c-accent-glow);
}

.track-cover {
  width: 36px;
  height: 36px;
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
  font-size: 12px;
  font-weight: 700;
  color: var(--c-accent);
}

.track-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.track-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--c-text-3);
}

.album-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.year-tag {
  color: var(--c-text-4);
  font-family: var(--font-mono, monospace);
}

.track-stats {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 11px;
  color: var(--c-text-3);
  flex-shrink: 0;
}

.play-count {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  color: var(--c-text-3);
}

.duration {
  font-family: var(--font-mono, monospace);
  color: var(--c-text-2);
}

/* Loading & Empty */
.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 48px 16px;
  color: var(--c-text-3);
  font-size: 13px;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 2px solid var(--c-bg-3);
  border-top-color: var(--c-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  opacity: 0.3;
}
</style>
