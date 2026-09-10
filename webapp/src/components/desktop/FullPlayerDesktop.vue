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
import { useContextMenu } from '@/composables/useContextMenu'
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

const handleGoToAlbum = () => {
  const albumId = props.track?.album?.id || props.track?.album_id
  if (!albumId) return
  emit('close')
  router.push(`/album/${albumId}`)
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

<style scoped>
/* Backdrop */
.dj-console-backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal, 1200);
  background: rgba(5, 6, 8, 0.92);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  overflow: hidden;
}

/* Ambient glow behind console */
.dj-ambient-glow {
  position: absolute;
  inset: -40px;
  pointer-events: none;
  z-index: 0;
  transform: translateZ(0);
  transition: opacity 0.4s ease;
}

/* Monolithic DJ Hardware Chassis */
.dj-chassis-unit {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1380px;
  height: 86vh;
  min-height: 600px;
  max-height: 820px;
  background: #111215;
  border-radius: 16px;
  border: 2px solid #22252e;
  box-shadow: 
    0 32px 80px rgba(0, 0, 0, 0.95),
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    0 0 0 1px #090a0c;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Corner Hex Bolts */
.chassis-bolt {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: radial-gradient(circle, #4a505f 0%, #1e2129 80%);
  border: 1px solid #090a0d;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
  pointer-events: none;
}

.hex-slot {
  width: 6px;
  height: 2px;
  background: #090a0d;
}

.chassis-bolt.tl { top: 6px; left: 6px; }
.chassis-bolt.tr { top: 6px; right: 6px; }
.chassis-bolt.bl { bottom: 6px; left: 6px; }
.chassis-bolt.br { bottom: 6px; right: 6px; }

/* Main Console Workstation Grid */
.dj-workstation {
  display: grid;
  grid-template-columns: 460px 1fr;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: #0e0f12;
}

/* LEFT: DECK A (STRICTLY NO SCROLLBARS, FIT 100%) */
.deck-a-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-right: 2px solid #07080a;
  box-shadow: 2px 0 0 rgba(255, 255, 255, 0.04);
  background: linear-gradient(180deg, #13151a 0%, #0d0e11 100%);
  overflow: hidden; /* ABSOLUTELY NO SCROLLBAR */
  height: 100%;
}

/* RIGHT: DECK B (DIGITAL CRATE & SAMPLER) */
.deck-b-section {
  display: flex;
  flex-direction: column;
  background: #0b0c0f;
  padding: 14px 18px;
  min-height: 0;
  overflow: hidden;
}

/* Hardware Channel Selector Bar (NO DUPLICATE TABS) */
.channel-selector-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  background: #07080a;
  border: 1px solid #1c1f28;
  border-radius: var(--r-xs);
  margin-bottom: 12px;
  flex-shrink: 0;
  user-select: none;
}

.channel-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid transparent;
  border-radius: 3px;
  background: transparent;
  color: var(--c-text-3);
  font-size: 11px;
  font-weight: 800;
  font-family: var(--font-mono, monospace);
  letter-spacing: 0.8px;
  cursor: pointer;
  transition: all 0.12s ease;
}

.channel-led {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #232731;
  transition: all 0.15s ease;
}

.channel-btn:hover {
  color: #ffffff;
  background: #14171e;
}

.channel-btn.active {
  background: #181c24;
  color: #ffffff;
  border-color: #2b3140;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
}

.channel-btn.active .channel-led {
  background: var(--c-accent);
  box-shadow: 0 0 6px var(--c-accent);
}

.channel-count {
  font-size: 9px;
  padding: 1px 5px;
  border-radius: 2px;
  background: #07080a;
  color: var(--c-text-3);
}

.channel-btn.active .channel-count {
  color: var(--c-accent);
  background: rgba(29, 185, 84, 0.15);
}

/* Deck B Screen (STRICTLY HIDDEN SCROLLBARS) */
.deck-b-screen {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #0e1014;
  border-radius: var(--r-xs);
  border: 1px solid #1a1d25;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.9);
  padding: 10px;
  overflow: hidden;
}

/* Ensure any nested scrollable pane has ZERO visible scrollbar */
.deck-b-screen * {
  scrollbar-width: none !important;
  -ms-overflow-style: none !important;
}

.deck-b-screen *::-webkit-scrollbar {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
}

/* Lyrics Monitor */
.lyrics-monitor {
  flex: 1;
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.deck-empty-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  height: 100%;
  color: var(--c-text-4);
  font-size: 13px;
}

.empty-icon {
  opacity: 0.3;
}

/* Fade transitions */
.dj-console-fade-enter-active,
.dj-console-fade-leave-active {
  transition: opacity 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.dj-console-fade-enter-active .dj-chassis-unit,
.dj-console-fade-leave-active .dj-chassis-unit {
  transition: transform 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.dj-console-fade-enter-from,
.dj-console-fade-leave-to {
  opacity: 0;
}

.dj-console-fade-enter-from .dj-chassis-unit {
  transform: scale(0.96) translateY(12px);
}

.dj-console-fade-leave-to .dj-chassis-unit {
  transform: scale(0.98) translateY(6px);
}

/* Responsive adjustments */
@media (max-width: 1200px) {
  .dj-workstation {
    grid-template-columns: 420px 1fr;
  }
}
</style>
