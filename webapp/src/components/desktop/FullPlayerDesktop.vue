<template>
  <Transition name="fullplayer-fade">
    <div 
      v-if="show" 
      class="fullplayer-backdrop" 
      @click.self="handleBackdropClick"
    >
      <!-- Ambient background glow (GPU accelerated, 0% CPU overhead) -->
      <div class="ambient-glow" :style="ambientGlowStyle"></div>

      <!-- Main Player Window -->
      <div class="fullplayer-window neu-panel">
        <!-- Top Header (context & close button) -->
        <PlayerHeader 
          :isPlaying="isPlaying"
          :contextInfo="contextInfo"
          :track="track"
          @close="$emit('close')" 
        />

        <!-- Main Body: 2-Column Split -->
        <div class="player-body" @contextmenu.prevent="openTrackContextMenu">
          <!-- Left Column: Hero (Cover, Meta, Seekbar, Controls, Volume) -->
          <div class="hero-column">
            <!-- Cover Art & Vinyl -->
            <CoverSection 
              :track="track" 
              :loading="loading" 
              :isPlaying="isPlaying" 
            />

            <!-- Track Info & Badges -->
            <TrackInfo 
              :track="track"
              :hdTrackInfo="hdTrackInfo"
              :isLiked="isLiked"
              @goToAlbum="handleGoToAlbum"
              @goToArtist="handleGoToArtist"
              @tagClick="handleTagClick"
            />

            <!-- Playback Controls & Seekbar -->
            <PlayerControls 
              :isPlaying="isPlaying"
              :progress="progress"
              :duration="duration"
              :buffered="buffered"
              :shuffle="shuffle"
              :repeat="repeat"
              :isLiked="isLiked"
              :hdTrackInfo="hdTrackInfo"
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
            />

            <!-- Volume Control -->
            <VolumeControl 
              :volume="volume"
              :isMuted="isMuted"
              @toggleMute="$emit('toggleMute')"
              @setVolume="$emit('setVolume', $event)"
            />
          </div>

          <!-- Right Column: Interactive Content Deck -->
          <div class="deck-column neu-surface">
            <!-- Deck Tab Bar -->
            <div class="deck-tab-bar">
              <button 
                class="deck-tab-btn" 
                :class="{ active: activeDeckTab === 'queue' }"
                @click="activeDeckTab = 'queue'"
              >
                <ListMusic :size="15" />
                <span>Очередь</span>
                <span class="tab-badge" v-if="queueLength">{{ queueLength }}</span>
              </button>

              <button 
                class="deck-tab-btn" 
                :class="{ active: activeDeckTab === 'lyrics' }"
                @click="activeDeckTab = 'lyrics'"
              >
                <Mic2 :size="15" />
                <span>Текст</span>
              </button>

              <button 
                class="deck-tab-btn" 
                :class="{ active: activeDeckTab === 'artist' }"
                @click="activeDeckTab = 'artist'"
              >
                <User :size="15" />
                <span>Артист</span>
              </button>

              <button 
                class="deck-tab-btn" 
                :class="{ active: activeDeckTab === 'stats' }"
                @click="activeDeckTab = 'stats'"
              >
                <Info :size="15" />
                <span>О треке</span>
              </button>
            </div>

            <!-- Deck Content Panes -->
            <div class="deck-body">
              <!-- Queue Pane -->
              <QueuePanel 
                v-if="activeDeckTab === 'queue'"
                :track="track"
                :progress="progress"
                :isPlaying="isPlaying"
                :contextInfo="contextInfo"
                :queueLength="queueLength"
                :upcomingQueue="upcomingQueue"
                :historyTracks="historyTracks"
                :lazyShuffleMode="lazyShuffleMode"
                :lazyShuffleIndex="lazyShuffleIndex"
                :lazyShuffleTotal="lazyShuffleTotal"
                @seek="$emit('seek', $event)"
                @playFromQueue="$emit('playFromQueue', $event)"
                @playFromHistory="$emit('playFromHistory', $event)"
              />

              <!-- Full Height Lyrics Pane -->
              <div v-else-if="activeDeckTab === 'lyrics'" class="deck-lyrics-wrapper">
                <LyricsViewer
                  v-if="track"
                  :track="track"
                  :currentTime="progress"
                  :isPlaying="isPlaying"
                  :embedded="true"
                  @seek="$emit('seek', $event)"
                />
                <div v-else class="deck-empty-state">
                  <Mic2 :size="36" class="empty-icon" />
                  <p>Нет активного трека</p>
                </div>
              </div>

              <!-- Artist Tracks Pane -->
              <ArtistLibrary 
                v-else-if="activeDeckTab === 'artist'"
                :track="track" 
                @play="handlePlayArtistTrack" 
              />

              <!-- Track Stats / Info Pane -->
              <PlayerStats 
                v-else-if="activeDeckTab === 'stats'"
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
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useContextMenu } from '@/composables/useContextMenu'
import { getCoverUrl, CoverSize } from '@/utils'
import { ListMusic, Mic2, User, Info } from 'lucide-vue-next'

import PlayerHeader from './fullplayer/PlayerHeader.vue'
import CoverSection from './fullplayer/CoverSection.vue'
import TrackInfo from './fullplayer/TrackInfo.vue'
import PlayerControls from './fullplayer/PlayerControls.vue'
import VolumeControl from './fullplayer/VolumeControl.vue'
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

// Active deck tab: 'queue' | 'lyrics' | 'artist' | 'stats'
const activeDeckTab = ref('queue')

const bufferedPercent = computed(() => {
  if (!props.duration) return 0
  return Math.round((props.buffered / props.duration) * 100)
})

const playModeText = computed(() => {
  if (props.shuffle) return 'Случайно'
  if (props.repeat === 'one') return 'Повтор 1'
  if (props.repeat === 'all') return 'Повтор всех'
  return 'Обычный'
})

const ambientGlowStyle = computed(() => {
  if (props.track?.cover_url) {
    return {
      backgroundImage: `url(${getCoverUrl(props.track.cover_url, CoverSize.MEDIUM)})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      filter: 'blur(80px) saturate(1.4) brightness(0.4)',
      opacity: props.isPlaying ? 0.35 : 0.2
    }
  }
  return {
    background: 'radial-gradient(circle at 40% 40%, var(--c-accent-glow) 0%, transparent 70%)',
    opacity: props.isPlaying ? 0.3 : 0.15
  }
})

// Keyboard navigation
const handleKeydown = (e) => {
  if (!props.show) return

  // Don't trigger if user is typing in an input or textarea
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
  activeDeckTab.value = activeDeckTab.value === 'lyrics' ? 'queue' : 'lyrics'
}

const handleTagClick = (tag) => {
  if (!tag) return
  emit('close')
  const cleanTag = tag.replace(/^#/, '')
  router.push({ path: '/search', query: { tag: cleanTag } })
}
</script>

<style scoped>
/* Full player backdrop overlay */
.fullplayer-backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal, 1200);
  background: rgba(8, 8, 8, 0.88);
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  overflow: hidden;
}

/* Ambient glow layer */
.ambient-glow {
  position: absolute;
  inset: -60px;
  pointer-events: none;
  z-index: 0;
  transform: translateZ(0);
  transition: opacity 0.5s ease;
}

/* Main window container */
.fullplayer-window {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1460px;
  height: 90vh;
  min-height: 640px;
  max-height: 880px;
  background: var(--c-bg-1);
  border-radius: var(--r-xl);
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 
    0 24px 72px rgba(0, 0, 0, 0.8),
    0 0 1px rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 2-Column Split Body */
.player-body {
  display: grid;
  grid-template-columns: minmax(420px, 480px) 1fr;
  gap: 32px;
  padding: 0 36px 28px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* Left Hero Column */
.hero-column {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 4px;
}

.hero-column::-webkit-scrollbar {
  width: 4px;
}

.hero-column::-webkit-scrollbar-thumb {
  background: var(--c-bg-4);
  border-radius: var(--r-full);
}

/* Right Deck Column */
.deck-column {
  display: flex;
  flex-direction: column;
  background: var(--c-bg-2);
  border-radius: var(--r-xl);
  border: 1px solid rgba(255, 255, 255, 0.03);
  padding: 16px 20px;
  min-height: 0;
  overflow: hidden;
}

/* Deck Tab Bar */
.deck-tab-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  border-radius: var(--r-full);
  background: var(--c-bg-1);
  margin-bottom: 16px;
  flex-shrink: 0;
  align-self: center;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.deck-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 18px;
  border-radius: var(--r-full);
  border: none;
  background: transparent;
  color: var(--c-text-3);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
  user-select: none;
}

.deck-tab-btn:hover {
  color: var(--c-text-1);
}

.deck-tab-btn.active {
  background: var(--c-bg-3);
  color: var(--c-accent);
  box-shadow: 
    2px 2px 6px var(--sh-dark),
    -1px -1px 3px var(--sh-light);
}

.tab-badge {
  padding: 1px 6px;
  border-radius: var(--r-full);
  font-size: 10px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-2);
}

.deck-tab-btn.active .tab-badge {
  background: rgba(29, 185, 84, 0.2);
  color: var(--c-accent);
}

/* Deck Content Pane */
.deck-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.deck-lyrics-wrapper {
  flex: 1;
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.deck-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px 24px;
  color: var(--c-text-3);
  font-size: 14px;
}

.empty-icon {
  opacity: 0.3;
}

/* Transitions */
.fullplayer-fade-enter-active,
.fullplayer-fade-leave-active {
  transition: opacity 0.28s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.fullplayer-fade-enter-active .fullplayer-window,
.fullplayer-fade-leave-active .fullplayer-window {
  transition: transform 0.28s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.fullplayer-fade-enter-from,
.fullplayer-fade-leave-to {
  opacity: 0;
}

.fullplayer-fade-enter-from .fullplayer-window {
  transform: scale(0.96) translateY(8px);
}

.fullplayer-fade-leave-to .fullplayer-window {
  transform: scale(0.97) translateY(4px);
}

/* Responsive breakpoint adjustments */
@media (max-width: 1280px) {
  .player-body {
    grid-template-columns: 380px 1fr;
    gap: 24px;
    padding: 0 24px 20px;
  }
}

@media (max-height: 740px) {
  .fullplayer-window {
    height: 94vh;
  }
  .player-body {
    padding: 0 24px 16px;
  }
}
</style>
