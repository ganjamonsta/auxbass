<template>
  <Transition name="dj-console-fade">
    <div 
      v-if="show" 
      class="dj-console-backdrop" 
      @click.self="handleBackdropClick"
    >
      <!-- Ambient light from current track -->
      <div class="dj-ambient-glow" :style="ambientGlowStyle"></div>

      <!-- Monolithic DJ Hardware Console Unit -->
      <div class="dj-chassis-unit">
        <!-- Corner Hex Bolts (DJ Hardware aesthetic) -->
        <div class="chassis-bolt tl"><div class="hex-slot"></div></div>
        <div class="chassis-bolt tr"><div class="hex-slot"></div></div>
        <div class="chassis-bolt bl"><div class="hex-slot"></div></div>
        <div class="chassis-bolt br"><div class="hex-slot"></div></div>

        <!-- Master Console Top Bar -->
        <PlayerHeader 
          :isPlaying="isPlaying"
          :contextInfo="contextInfo"
          :track="track"
          @close="$emit('close')" 
        />

        <!-- Main Console Workstation (Deck A + Deck B) -->
        <div class="dj-workstation" @contextmenu.prevent="openTrackContextMenu">
          <!-- LEFT: DECK A (Turntable + LCD + Transport + Fader) - STRICTLY NO SCROLL -->
          <div class="deck-a-section">
            <!-- Turntable Platter with Vinyl -->
            <CoverSection 
              :track="track" 
              :loading="loading" 
              :isPlaying="isPlaying" 
            />

            <!-- LCD Rack Monitor -->
            <TrackInfo 
              :track="track"
              :hdTrackInfo="hdTrackInfo"
              :isLiked="isLiked"
              @goToAlbum="handleGoToAlbum"
              @goToArtist="handleGoToArtist"
              @tagClick="handleTagClick"
            />

            <!-- Transport Buttons & Scrubber & Volume Fader -->
            <PlayerControls 
              :isPlaying="isPlaying"
              :progress="progress"
              :duration="duration"
              :buffered="buffered"
              :shuffle="shuffle"
              :repeat="repeat"
              :isLiked="isLiked"
              :hdTrackInfo="hdTrackInfo"
              :volume="volume"
              :isMuted="isMuted"
              @seek="$emit('seek', $event)"
              @toggle="$emit('toggle')"
              @prev="$emit('prev')"
              @next="$emit('next')"
              @toggleShuffle="$emit('toggleShuffle')"
              @toggleRepeat="$emit('toggleRepeat')"
              @like="$emit('like')"
              @addToPlaylist="handleAddToPlaylist"
              @downloadHD="handleDownloadHD"
              @toggleLyrics="handleToggleLyrics"
              @setVolume="$emit('setVolume', $event)"
              @toggleMute="$emit('toggleMute')"
            />
          </div>

          <!-- RIGHT: DECK B (Digital Sampler / Crate / Lyrics / Artist / Specs) -->
          <div class="deck-b-section">
            <!-- Hardware Channel Selector (NO DUPLICATE TABS) -->
            <div class="channel-selector-bar">
              <button 
                class="channel-btn" 
                :class="{ active: activeDeckChannel === 'queue' }"
                @click="activeDeckChannel = 'queue'"
              >
                <span class="channel-led"></span>
                <ListMusic :size="13" />
                <span>ОЧЕРЕДЬ</span>
                <span class="channel-count" v-if="queueLength">{{ queueLength }}</span>
              </button>

              <button 
                class="channel-btn" 
                :class="{ active: activeDeckChannel === 'history' }"
                @click="activeDeckChannel = 'history'"
              >
                <span class="channel-led"></span>
                <History :size="13" />
                <span>ИСТОРИЯ</span>
                <span class="channel-count" v-if="historyTracks?.length">{{ historyTracks.length }}</span>
              </button>

              <button 
                class="channel-btn" 
                :class="{ active: activeDeckChannel === 'lyrics' }"
                @click="activeDeckChannel = 'lyrics'"
              >
                <span class="channel-led"></span>
                <Mic2 :size="13" />
                <span>ТЕКСТ</span>
              </button>

              <button 
                class="channel-btn" 
                :class="{ active: activeDeckChannel === 'artist' }"
                @click="activeDeckChannel = 'artist'"
              >
                <span class="channel-led"></span>
                <User :size="13" />
                <span>АРТИСТ</span>
              </button>

              <button 
                class="channel-btn" 
                :class="{ active: activeDeckChannel === 'stats' }"
                @click="activeDeckChannel = 'stats'"
              >
                <span class="channel-led"></span>
                <Cpu :size="13" />
                <span>ИНФО</span>
              </button>
            </div>

            <!-- Deck B Screen Container (HIDDEN SCROLLBARS) -->
            <div class="deck-b-screen">
              <!-- Upcoming Queue -->
              <QueuePanel 
                v-if="activeDeckChannel === 'queue'"
                :track="track"
                :upcomingQueue="upcomingQueue"
                :historyTracks="historyTracks"
                :isPlaying="isPlaying"
                :contextInfo="contextInfo"
                :lazyShuffleMode="lazyShuffleMode"
                :lazyShuffleIndex="lazyShuffleIndex"
                :lazyShuffleTotal="lazyShuffleTotal"
                activeSubMode="upcoming"
                @playFromQueue="$emit('playFromQueue', $event)"
              />

              <!-- History Queue -->
              <QueuePanel 
                v-else-if="activeDeckChannel === 'history'"
                :track="track"
                :upcomingQueue="upcomingQueue"
                :historyTracks="historyTracks"
                :isPlaying="isPlaying"
                :contextInfo="contextInfo"
                :lazyShuffleMode="lazyShuffleMode"
                :lazyShuffleIndex="lazyShuffleIndex"
                :lazyShuffleTotal="lazyShuffleTotal"
                activeSubMode="history"
                @playFromHistory="$emit('playFromHistory', $event)"
              />

              <!-- Live Lyrics Karaoke Monitor -->
              <div v-else-if="activeDeckChannel === 'lyrics'" class="lyrics-monitor">
                <LyricsViewer
                  v-if="track"
                  :track="track"
                  :currentTime="progress"
                  :isPlaying="isPlaying"
                  :embedded="true"
                  @seek="$emit('seek', $event)"
                />
                <div v-else class="deck-empty-display">
                  <Mic2 :size="32" class="empty-icon" />
                  <p>Нет активного трека</p>
                </div>
              </div>

              <!-- Artist Library -->
              <ArtistLibrary 
                v-else-if="activeDeckChannel === 'artist'"
                :track="track" 
                @play="handlePlayArtistTrack" 
              />

              <!-- Track Technical Specifications -->
              <PlayerStats 
                v-else-if="activeDeckChannel === 'stats'"
                :bufferedPercent="bufferedPercent"
                :bitrate="track?.bitrate"
                :playCount="track?.play_count"
                :playModeText="playModeText"
                :track="track"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useUIStore } from '@/stores/ui'
import { useContextMenu } from '@/composables/useContextMenu'
import { albumsApi } from '@/api/client'
import { getCoverUrl, CoverSize } from '@/utils'
import { ListMusic, History, Mic2, User, Cpu } from 'lucide-vue-next'

import PlayerHeader from './fullplayer/PlayerHeader.vue'
import CoverSection from './fullplayer/CoverSection.vue'
import TrackInfo from './fullplayer/TrackInfo.vue'
import PlayerControls from './fullplayer/PlayerControls.vue'
import QueuePanel from './fullplayer/QueuePanel.vue'
import ArtistLibrary from './fullplayer/ArtistLibrary.vue'
import PlayerStats from './fullplayer/PlayerStats.vue'
import LyricsViewer from '@/components/LyricsViewer.vue'

const props = defineProps({
  show: Boolean,
  track: Object,
  isPlaying: Boolean,
  loading: Boolean,
  progress: Number,
  duration: Number,
  buffered: Number,
  volume: Number,
  isMuted: Boolean,
  shuffle: Boolean,
  repeat: String,
  isLiked: Boolean,
  upcomingQueue: Array,
  queueLength: Number,
  historyTracks: {
    type: Array,
    default: () => []
  },
  hdTrackInfo: Object,
  lazyShuffleMode: Boolean,
  lazyShuffleIndex: Number,
  lazyShuffleTotal: Number,
  contextInfo: Object
})

const emit = defineEmits([
  'close', 'toggle', 'next', 'prev', 'seek', 'setVolume',
  'toggleMute', 'toggleShuffle', 'toggleRepeat', 'like',
  'playFromQueue', 'playFromHistory'
])

const router = useRouter()
const playerStore = usePlayerStore()
const uiStore = useUIStore()
const { openMenu } = useContextMenu()

// Dedicated Channel on Deck B: 'queue' | 'history' | 'lyrics' | 'artist' | 'stats'
const activeDeckChannel = ref('queue')

const bufferedPercent = computed(() => {
  if (!props.duration) return 0
  return Math.round((props.buffered / props.duration) * 100)
})

const playModeText = computed(() => {
  if (props.shuffle) return 'СЛУЧАЙНО'
  if (props.repeat === 'one') return 'ПОВТОР 1'
  if (props.repeat === 'all') return 'ПОВТОР ВСЕ'
  return 'СТАНДАРТ'
})

const ambientGlowStyle = computed(() => {
  if (props.track?.cover_url) {
    return {
      backgroundImage: `url(${getCoverUrl(props.track.cover_url, CoverSize.MEDIUM)})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      filter: 'blur(70px) saturate(1.4) brightness(0.35)',
      opacity: props.isPlaying ? 0.35 : 0.18
    }
  }
  return {
    background: 'radial-gradient(circle at 40% 40%, var(--c-accent-glow) 0%, transparent 70%)',
    opacity: props.isPlaying ? 0.25 : 0.12
  }
})

// Keyboard shortcuts
const handleKeydown = (e) => {
  if (!props.show) return

  const target = e.target
  if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) {
    return
  }

  if (e.key === 'Escape') {
    e.preventDefault()
    emit('close')
  } else if (e.key === ' ' || e.code === 'Space') {
    e.preventDefault()
    emit('toggle')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

const handleBackdropClick = () => {
  emit('close')
}

const openTrackContextMenu = (event) => {
  openMenu('track', props.track, 'player', event)
}

const handleDownloadHD = () => {
  if (props.hdTrackInfo) {
    playerStore.downloadTrack(props.hdTrackInfo)
  }
}

const handlePlayArtistTrack = (track) => {
  playerStore.playTrack(track, { type: 'artist', artist: props.track.artist })
}

const handleGoToAlbum = async () => {
  const albumId = props.track?.album?.id || props.track?.album_id
  if (albumId) {
    emit('close')
    router.push(`/album/${albumId}`)
    return
  }
  const t = props.track
  const albumName = t?.album?.name || t?.album_name || (typeof t?.album === 'string' ? t.album : null)
  if (t?.id || albumName) {
    emit('close')
    try {
      const res = await albumsApi.resolve({
        track_id: t?.id,
        album_name: albumName,
        artist: t?.artist
      })
      if (res?.data?.album_id) {
        router.push(`/album/${res.data.album_id}`)
      } else {
        uiStore.toast.info('Альбом', 'Альбом не найден')
      }
    } catch (err) {
      console.error('Failed to resolve album:', err)
      uiStore.toast.error('Ошибка', 'Не удалось открыть альбом')
    }
  }
}

const handleGoToArtist = (artistName) => {
  if (!artistName) return
  emit('close')
  router.push(`/artist/${encodeURIComponent(artistName)}`)
}

const handleAddToPlaylist = () => {
  openMenu('track', props.track, 'player')
}

const handleToggleLyrics = () => {
  activeDeckChannel.value = activeDeckChannel.value === 'lyrics' ? 'queue' : 'lyrics'
}

const handleTagClick = (tag) => {
  if (!tag) return
  emit('close')
  const cleanTag = tag.replace(/^#/, '')
  router.push({ path: '/search', query: { tag: cleanTag } })
}
</script>

<style scoped src="./FullPlayerDesktop.css"></style>
