<template>
  <div 
    class="galaxy-mini-player" 
    @click="$emit('expand')" 
    @contextmenu.prevent="openMenu('track', track, 'player', $event)"
  >
    <!-- ══ GALAXY FOLD METALLIC HINGE SPINE ══ -->
    <div class="fold-hinge">
      <!-- Left antenna insulator band -->
      <div class="antenna-band left"></div>

      <!-- Left Laser Engraving / Sound Branding -->
      <div class="hinge-brand">
        <span class="brand-text">GALAXY SOUND</span>
      </div>

      <!-- Center: Signature 5-Pill Speaker Grille Audio Visualizer (Galaxy Fold reference) -->
      <div class="speaker-grille" :class="{ 'playing': isPlaying }">
        <div 
          v-for="i in 5" 
          :key="i" 
          class="speaker-port"
          :class="`port-${i}`"
        >
          <div class="speaker-led"></div>
        </div>
      </div>

      <!-- Right: Dolby Atmos & Galaxy Status Micro-LED -->
      <div class="hinge-status">
        <span class="atmos-text">ATMOS</span>
        <div 
          class="status-led" 
          :class="statusLedClass"
          :title="statusLedTitle"
        ></div>
      </div>

      <!-- Right antenna insulator band -->
      <div class="antenna-band right"></div>
    </div>

    <!-- ══ GALAXY AMOLED DISPLAY SCREEN ══ -->
    <div class="fold-screen">
      <!-- Ambient screen glare -->
      <div class="screen-glare"></div>

      <!-- Main Row: Cover Art + Track Info + Galaxy Controls -->
      <div class="screen-main-row">
        <!-- Album Art Squircle (Samsung One UI style) -->
        <div class="fold-cover" :class="{ 'playing': isPlaying }">
          <img 
            v-if="track?.cover_url" 
            :src="getCoverUrl(track.cover_url, CoverSize.SMALL)" 
            :alt="track.title"
            class="cover-img"
            loading="lazy"
          />
          <div v-else class="cover-fallback" :style="getTrackCoverStyle(track)">
            <span>{{ getTrackInitials(track) }}</span>
          </div>
          <!-- Playing overlay aura ring -->
          <div v-if="isPlaying" class="cover-aura"></div>
        </div>

        <!-- Track Info (Title marquee + Artist + Badges) -->
        <div class="fold-info">
          <div class="title-container">
            <div class="title-track" :class="{ 'marquee': shouldMarquee }">
              <span class="track-title">{{ displayTextTitle }}</span>
              <span v-if="shouldMarquee" class="track-title clone">{{ displayTextTitle }}</span>
            </div>
          </div>
          <div class="artist-row">
            <span class="track-artist">{{ displayTextArtist }}</span>
            <!-- HD Badge if available -->
            <span v-if="playerStore.hdTrackInfo" class="badge-hd" title="HD Audio 24-bit">HD</span>
            <!-- Network issue warning -->
            <span 
              v-if="networkMonitor.hasIssues.value" 
              class="badge-net"
              :class="{ 'pulse': networkMonitor.connectionState.value === 'reconnecting' }"
              :title="networkTooltip"
            >
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="1" y1="1" x2="23" y2="23"/>
                <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/>
                <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/>
                <path d="M10.71 5.05A16 16 0 0 1 22.56 9"/>
                <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/>
              </svg>
            </span>
          </div>
        </div>

        <!-- Media Controls Cluster ("с кнопками управления") -->
        <div class="fold-controls" @click.stop>
          <!-- Like Button -->
          <button 
            class="control-btn btn-like" 
            :class="{ 'liked': isLiked }" 
            @click.stop="handleLike"
            title="Нравится"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" :fill="isLiked ? '#ff3366' : 'none'" :stroke="isLiked ? '#ff3366' : 'currentColor'" stroke-width="2">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
          </button>

          <!-- Prev Button -->
          <button 
            class="control-btn btn-prev" 
            @click.stop="handlePrev" 
            title="Предыдущий трек"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
            </svg>
          </button>

          <!-- Play / Pause Main Galaxy Button -->
          <button 
            class="control-btn btn-play" 
            :class="{ 'is-playing': isPlaying }"
            @click.stop="handleToggle" 
            title="Воспроизведение / Пауза"
          >
            <!-- Loading Spinner -->
            <svg v-if="loading" class="spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <path d="M12 2a10 10 0 0 1 10 10"/>
            </svg>
            <!-- Pause Icon -->
            <svg v-else-if="isPlaying" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
            </svg>
            <!-- Play Icon -->
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor" class="play-icon">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </button>

          <!-- Next Button -->
          <button 
            class="control-btn btn-next" 
            @click.stop="handleNext" 
            title="Следующий трек"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Laser Progress Bar & Time ("и индикаторами") -->
      <div class="screen-progress-row">
        <span class="time-text time-current">{{ formatTime(progress) }}</span>

        <!-- Scrubbable laser progress bar -->
        <div 
          class="progress-track-wrapper" 
          @click.stop="handleSeek"
          title="Перемотка"
        >
          <div class="progress-track">
            <!-- Buffered bar -->
            <div class="progress-buffered" :style="{ width: `${bufferedPercent}%` }"></div>
            <!-- Played active bar -->
            <div class="progress-played" :style="{ width: `${progressPercent}%` }">
              <div class="progress-glow-dot"></div>
            </div>
          </div>
        </div>

        <span class="time-text time-duration">{{ formatTime(duration || track.duration) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { useContextMenu } from '@/composables/useContextMenu'
import { 
  getDisplayTitle, 
  getDisplayArtist, 
  getCoverUrl, 
  CoverSize, 
  getTrackInitials, 
  getTrackCoverStyle 
} from '@/utils'
import { useNetworkMonitor } from '@/composables/useNetworkMonitor'

const playerStore = usePlayerStore()
const { openMenu } = useContextMenu()
const networkMonitor = useNetworkMonitor()

const props = defineProps({
  track: {
    type: Object,
    required: true
  },
  isPlaying: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  progress: {
    type: Number,
    default: 0
  },
  duration: {
    type: Number,
    default: 0
  },
  buffered: {
    type: Number,
    default: 0
  },
  isLiked: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'expand', 
  'toggle', 
  'next', 
  'prev', 
  'toggleShuffle', 
  'toggleRepeat', 
  'like', 
  'seek'
])

// Progress calculations
const progressPercent = computed(() => {
  const dur = props.duration || props.track?.duration
  if (!dur) return 0
  return Math.min(100, Math.max(0, (props.progress / dur) * 100))
})

const bufferedPercent = computed(() => {
  const dur = props.duration || props.track?.duration
  if (!dur) return 0
  return Math.min(100, Math.max(0, (props.buffered / dur) * 100))
})

// Track title & artist
const displayTextTitle = computed(() => {
  return getDisplayTitle(props.track) || 'Неизвестный трек'
})

const displayTextArtist = computed(() => {
  return getDisplayArtist(props.track) || 'Неизвестный исполнитель'
})

const shouldMarquee = computed(() => {
  return displayTextTitle.value.length > 24
})

// Status LED
const statusLedClass = computed(() => {
  if (networkMonitor.hasIssues.value) {
    return networkMonitor.connectionState.value === 'offline' ? 'led-offline' : 'led-reconnecting'
  }
  if (props.loading) return 'led-buffering'
  if (props.isPlaying) return 'led-playing'
  return 'led-paused'
})

const statusLedTitle = computed(() => {
  if (networkMonitor.connectionState.value === 'offline') return 'Сеть недоступна'
  if (networkMonitor.connectionState.value === 'reconnecting') return 'Восстановление сети...'
  if (props.loading) return 'Буферизация...'
  if (props.isPlaying) return 'Воспроизведение (Galaxy Hi-Fi)'
  return 'Пауза'
})

const networkTooltip = computed(() => {
  if (networkMonitor.connectionState.value === 'offline') return 'Нет сети'
  if (networkMonitor.connectionState.value === 'reconnecting') return 'Восстановление...'
  return 'Медленная сеть'
})

// Formatting
const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds) || seconds < 0) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// Action Handlers with direct playerStore fallback
const handlePrev = () => {
  emit('prev')
  if (playerStore?.prev) playerStore.prev()
}

const handleNext = () => {
  emit('next')
  if (playerStore?.next) playerStore.next()
}

const handleToggle = () => {
  emit('toggle')
  if (playerStore?.togglePlay) playerStore.togglePlay()
}

const handleLike = () => {
  emit('like')
}

const handleSeek = (event) => {
  const bar = event.currentTarget
  const rect = bar.getBoundingClientRect()
  const clickX = event.clientX - rect.left
  const percent = Math.max(0, Math.min(1, clickX / rect.width))
  const dur = props.duration || props.track?.duration || 0
  if (dur > 0) {
    const targetTime = percent * dur
    emit('seek', targetTime)
    if (playerStore?.seek) {
      playerStore.seek(targetTime)
    }
  }
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   🌌 SAMSUNG GALAXY FOLD MINI PLAYER - Flagship Hardware UI
   ═══════════════════════════════════════════════════════════ */

.galaxy-mini-player {
  display: flex;
  flex-direction: column;
  margin: 3px 10px 6px;
  border-radius: 16px;
  cursor: pointer;
  overflow: hidden;
  position: relative;
  box-shadow: 
    0 12px 32px rgba(0, 0, 0, 0.65),
    0 2px 8px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.12);
  transition: transform 0.18s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.18s ease;
  user-select: none;
  -webkit-user-select: none;
}

.galaxy-mini-player:active {
  transform: scale(0.985);
  box-shadow: 
    0 6px 18px rgba(0, 0, 0, 0.7),
    0 0 0 1px rgba(255, 255, 255, 0.16);
}

/* ─── 1. GALAXY FOLD METALLIC HINGE SPINE ─── */
.fold-hinge {
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  position: relative;
  background: linear-gradient(
    180deg, 
    #f8fafc 0%, 
    #e2e8f0 14%, 
    #94a3b8 38%, 
    #475569 68%, 
    #334155 88%, 
    #1e293b 100%
  );
  box-shadow: 
    inset 0 1px 1px rgba(255, 255, 255, 0.95),
    inset 0 -1px 1px rgba(0, 0, 0, 0.5),
    0 1px 3px rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(0, 0, 0, 0.45);
}

/* Metallic specular glare running along the curved hinge */
.fold-hinge::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.1) 0%,
    rgba(255, 255, 255, 0.85) 25%,
    rgba(255, 255, 255, 0.95) 50%,
    rgba(255, 255, 255, 0.85) 75%,
    rgba(255, 255, 255, 0.1) 100%
  );
  pointer-events: none;
}

/* Antenna insulator bands (vertical slits across metal chassis) */
.antenna-band {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2.5px;
  background: #334155;
  box-shadow: 1px 0 0 rgba(255, 255, 255, 0.35);
  pointer-events: none;
}

.antenna-band.left {
  left: 36px;
}

.antenna-band.right {
  right: 36px;
}

/* Hinge Brand Laser Engraving */
.hinge-brand {
  display: flex;
  align-items: center;
}

.brand-text {
  font-size: 8.5px;
  font-weight: 700;
  letter-spacing: 1.2px;
  color: #1e293b;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.6);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  opacity: 0.85;
}

/* ─── Center: 5-Pill Speaker Grille Visualizer (Image 2) ─── */
.speaker-grille {
  display: flex;
  align-items: center;
  gap: 3.5px;
  padding: 0 4px;
}

.speaker-port {
  width: 3.5px;
  height: 11px;
  border-radius: 9999px;
  background: #090e17;
  box-shadow: 
    inset 0 1px 2px rgba(0, 0, 0, 0.95), 
    0 1px 0 rgba(255, 255, 255, 0.45);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.speaker-led {
  width: 100%;
  height: 20%;
  border-radius: 9999px;
  background: #38bdf8;
  opacity: 0.25;
  transition: all 0.2s ease;
}

/* Active audio visualizer animation when playing */
.speaker-grille.playing .speaker-led {
  opacity: 1;
  background: linear-gradient(180deg, #38bdf8 0%, #00f2fe 100%);
  box-shadow: 0 0 5px rgba(0, 242, 254, 0.8);
}

.speaker-grille.playing .port-1 .speaker-led {
  animation: eq-pulse 0.75s ease-in-out infinite alternate 0.15s;
}

.speaker-grille.playing .port-2 .speaker-led {
  animation: eq-pulse 0.65s ease-in-out infinite alternate 0.35s;
}

.speaker-grille.playing .port-3 .speaker-led {
  animation: eq-pulse 0.55s ease-in-out infinite alternate 0.0s;
}

.speaker-grille.playing .port-4 .speaker-led {
  animation: eq-pulse 0.7s ease-in-out infinite alternate 0.4s;
}

.speaker-grille.playing .port-5 .speaker-led {
  animation: eq-pulse 0.8s ease-in-out infinite alternate 0.2s;
}

@keyframes eq-pulse {
  0% {
    height: 25%;
    opacity: 0.5;
  }
  50% {
    height: 65%;
    opacity: 0.85;
  }
  100% {
    height: 100%;
    opacity: 1;
  }
}

/* Hinge Right Status Group */
.hinge-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.atmos-text {
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 1px;
  color: #1e293b;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.6);
  opacity: 0.8;
}

/* Galaxy Status Micro-LED */
.status-led {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  transition: all 0.25s ease;
  box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.4);
}

.status-led.led-playing {
  background: #00f2fe;
  box-shadow: 0 0 8px #00f2fe, 0 0 2px #ffffff;
  animation: led-glow 2s ease-in-out infinite;
}

.status-led.led-paused {
  background: #64748b;
  box-shadow: none;
  opacity: 0.6;
}

.status-led.led-buffering {
  background: #fbbf24;
  box-shadow: 0 0 6px #fbbf24;
  animation: led-blink 0.7s ease-in-out infinite;
}

.status-led.led-reconnecting {
  background: #f59e0b;
  box-shadow: 0 0 6px #f59e0b;
  animation: led-blink 0.5s ease-in-out infinite;
}

.status-led.led-offline {
  background: #ef4444;
  box-shadow: 0 0 6px #ef4444;
}

@keyframes led-glow {
  0%, 100% { opacity: 0.85; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.15); box-shadow: 0 0 10px #00f2fe; }
}

@keyframes led-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

/* ─── 2. GALAXY AMOLED DISPLAY SCREEN ─── */
.fold-screen {
  background: linear-gradient(180deg, rgba(14, 20, 30, 0.96) 0%, rgba(8, 12, 18, 0.98) 100%);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  padding: 8px 12px 9px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-top: none;
}

/* Subtle glass glare sweep across AMOLED display */
.screen-glare {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.04) 0%, transparent 50%);
  pointer-events: none;
}

/* ─── Main Row: Art + Info + Controls ─── */
.screen-main-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  position: relative;
  z-index: 1;
}

/* Squircle Cover Art */
.fold-cover {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  overflow: hidden;
  flex-shrink: 0;
  position: relative;
  box-shadow: 
    0 4px 10px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.15);
  background: #111827;
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.cover-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
  color: #ffffff;
}

.cover-aura {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  box-shadow: inset 0 0 0 1.5px rgba(0, 242, 254, 0.55);
  pointer-events: none;
}

/* Track Info */
.fold-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.title-container {
  overflow: hidden;
  mask-image: linear-gradient(90deg, black 88%, transparent 100%);
  -webkit-mask-image: linear-gradient(90deg, black 88%, transparent 100%);
}

.title-track {
  display: inline-flex;
  white-space: nowrap;
}

.title-track.marquee {
  animation: marquee-scroll 12s linear infinite;
}

.track-title {
  color: #f8fafc;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.1px;
  white-space: nowrap;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Samsung Sans', sans-serif;
}

.track-title.clone {
  margin-left: 50px;
}

@keyframes marquee-scroll {
  0%, 5% { transform: translateX(0); }
  95%, 100% { transform: translateX(calc(-50% - 25px)); }
}

.artist-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.track-artist {
  color: #94a3b8;
  font-size: 11px;
  font-weight: 400;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Badges */
.badge-hd {
  font-size: 8px;
  font-weight: 800;
  line-height: 1;
  padding: 1.5px 4px;
  border-radius: 4px;
  color: #ffd700;
  background: rgba(255, 215, 0, 0.14);
  border: 1px solid rgba(255, 215, 0, 0.35);
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

.badge-net {
  color: #ef4444;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.badge-net.pulse {
  animation: led-blink 1s ease-in-out infinite;
}

/* ─── Media Controls Cluster ("с кнопками управления") ─── */
.fold-controls {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
}

.control-btn {
  border: none;
  background: rgba(255, 255, 255, 0.07);
  color: #e2e8f0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.15s cubic-bezier(0.2, 0.8, 0.2, 1);
  position: relative;
  box-shadow: 
    0 2px 5px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.1);
  -webkit-tap-highlight-color: transparent;
}

.control-btn:hover {
  background: rgba(255, 255, 255, 0.13);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.25);
}

.control-btn:active {
  transform: scale(0.9);
  background: rgba(255, 255, 255, 0.04);
}

/* Like Button */
.btn-like {
  width: 27px;
  height: 27px;
  color: #94a3b8;
}

.btn-like.liked {
  color: #ff3366;
  background: rgba(255, 51, 102, 0.15);
  border-color: rgba(255, 51, 102, 0.35);
  box-shadow: 0 0 10px rgba(255, 51, 102, 0.35);
  animation: heart-pop 0.3s ease-out;
}

@keyframes heart-pop {
  0% { transform: scale(1); }
  50% { transform: scale(1.28); }
  100% { transform: scale(1); }
}

/* Prev / Next Buttons */
.btn-prev,
.btn-next {
  width: 27px;
  height: 27px;
}

/* Central Galaxy Play/Pause Button */
.btn-play {
  width: 33px;
  height: 33px;
  background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
  color: #06111f;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 
    0 3px 10px rgba(0, 242, 254, 0.45),
    inset 0 1px 1px rgba(255, 255, 255, 0.7);
}

.btn-play:hover {
  filter: brightness(1.08);
  box-shadow: 
    0 4px 14px rgba(0, 242, 254, 0.6),
    inset 0 1px 1px rgba(255, 255, 255, 0.9);
}

.btn-play:active {
  transform: scale(0.92);
  box-shadow: 0 2px 6px rgba(0, 242, 254, 0.3);
}

.play-icon {
  margin-left: 1.5px;
}

/* ─── 3. LASER PROGRESS BAR & TIME ─── */
.screen-progress-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.time-text {
  font-size: 10px;
  font-weight: 600;
  color: #94a3b8;
  font-family: 'Consolas', 'Roboto Mono', 'Segoe UI', monospace;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.2px;
  min-width: 26px;
  flex-shrink: 0;
}

.time-current {
  text-align: left;
}

.time-duration {
  text-align: right;
}

/* Interactive Laser Progress Track */
.progress-track-wrapper {
  flex: 1;
  padding: 4px 0;
  cursor: pointer;
}

.progress-track {
  height: 3.5px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 9999px;
  position: relative;
  overflow: visible;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.6);
}

.progress-buffered {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  background: rgba(0, 242, 254, 0.2);
  border-radius: 9999px;
  transition: width 0.2s ease;
}

.progress-played {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  background: linear-gradient(90deg, #00c6ff 0%, #0072ff 50%, #00f2fe 100%);
  border-radius: 9999px;
  box-shadow: 0 0 6px rgba(0, 242, 254, 0.6);
  transition: width 0.1s linear;
}

.progress-glow-dot {
  position: absolute;
  right: -3px;
  top: 50%;
  transform: translateY(-50%);
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 0 6px #00f2fe, 0 0 10px #00f2fe;
}

/* Spinner helper */
.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
