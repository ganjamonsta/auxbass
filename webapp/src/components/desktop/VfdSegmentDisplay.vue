<template>
  <div 
    class="vfd-display" 
    ref="displayRef"
    @click="cycleMode"
    :title="modeTooltip"
  >
    <!-- VFD Glass Face Effects -->
    <div class="vfd-glass-overlay">
      <div class="vfd-filament-wire top"></div>
      <div class="vfd-filament-wire bottom"></div>
      <div class="vfd-specular-glare"></div>
      <div class="vfd-mesh-texture"></div>
    </div>

    <!-- Active Mode Indicator Badge (Car Stereo style DISP) -->
    <div class="vfd-status-bar">
      <span class="vfd-disp-badge" :class="{ active: isUserModeActive }">
        {{ currentModeBadge }}
      </span>
      <span v-if="isPlaying" class="vfd-play-indicator">
        <span class="vfd-spin-disc">
          <svg viewBox="0 0 16 22" class="vfd-disc-svg">
            <g transform="skewX(-7.5)">
              <path 
                v-for="(pathD, segKey) in SEGMENT_PATHS" 
                :key="segKey"
                :d="pathD"
                :class="getSegmentClass(discFrameMask, segKey)"
              />
            </g>
          </svg>
        </span>
      </span>
    </div>

    <!-- 16-Segment Alphanumeric Starburst Cells Grid -->
    <div class="vfd-cells-row">
      <div 
        v-for="(cellMask, idx) in renderedMasks" 
        :key="idx" 
        class="vfd-cell"
        :class="{ 'audio-pulsing': isPlaying && isBeatPulse }"
      >
        <svg viewBox="0 0 16 22" class="vfd-cell-svg">
          <g transform="skewX(-7.5)">
            <!-- 16 Segments -->
            <path 
              v-for="(pathD, segKey) in SEGMENT_PATHS" 
              :key="segKey"
              :d="pathD"
              :class="getSegmentClass(cellMask, segKey)"
            />
            <!-- Decimal Point / Dot -->
            <circle 
              cx="15.2" 
              cy="20.0" 
              r="0.9" 
              :class="getSegmentClass(cellMask, 'DP')" 
            />
          </g>
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { 
  SEGMENTS, 
  getCharMask, 
  encodeString, 
  DISC_FRAMES, 
  getLarsonMasks, 
  getRandomGlitchMask 
} from '@/utils/segmentFont16'

const props = defineProps({
  track: {
    type: Object,
    default: null
  },
  displayText: {
    type: String,
    default: ''
  },
  isPlaying: {
    type: Boolean,
    default: false
  },
  volume: {
    type: Number,
    default: 1
  },
  hdTrackInfo: {
    type: Object,
    default: null
  },
  progress: {
    type: Number,
    default: 0
  },
  duration: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['click'])

// Exact SVG Vector Paths for 16-Segment Starburst Display
const SEGMENT_PATHS = {
  // Top horizontal segments
  A1: 'M 2.2 1.5 L 7.4 1.5 L 6.6 3.2 L 3.2 3.2 Z',
  A2: 'M 8.6 1.5 L 13.8 1.5 L 12.8 3.2 L 9.4 3.2 Z',
  // Upper outer verticals
  F:  'M 1.5 2.2 L 3.2 3.8 L 3.2 9.6 L 1.5 10.4 Z',
  B:  'M 14.5 2.2 L 14.5 10.4 L 12.8 9.6 L 12.8 3.8 Z',
  // Middle horizontal segments
  G1: 'M 2.6 11.0 L 3.6 10.3 L 7.4 10.3 L 6.8 11.7 L 3.6 11.7 Z',
  G2: 'M 8.6 10.3 L 12.4 10.3 L 13.4 11.0 L 12.4 11.7 L 9.2 11.7 Z',
  // Lower outer verticals
  E:  'M 1.5 11.6 L 3.2 12.4 L 3.2 18.2 L 1.5 19.8 Z',
  C:  'M 14.5 11.6 L 14.5 19.8 L 12.8 18.2 L 12.8 12.4 Z',
  // Bottom horizontal segments
  D1: 'M 3.2 18.8 L 6.6 18.8 L 7.4 20.5 L 2.2 20.5 Z',
  D2: 'M 9.4 18.8 L 12.8 18.8 L 13.8 20.5 L 8.6 20.5 Z',
  // Upper and lower center verticals
  J:  'M 7.4 3.8 L 8.6 3.8 L 8.6 9.8 L 7.4 9.8 Z',
  M:  'M 7.4 12.2 L 8.6 12.2 L 8.6 18.2 L 7.4 18.2 Z',
  // Diagonals (h, k, l, n)
  H:  'M 3.8 4.2 L 4.9 3.8 L 7.2 9.4 L 6.1 9.8 Z',
  K:  'M 11.1 3.8 L 12.2 4.2 L 9.9 9.8 L 8.8 9.4 Z',
  L:  'M 6.1 12.2 L 7.2 12.6 L 4.9 18.2 L 3.8 17.8 Z',
  N:  'M 8.8 12.6 L 9.9 12.2 L 12.2 17.8 L 11.1 18.2 Z'
}

// Display Modes: 'auto' (track when playing/paused, idle when stopped), 'clock', 'specs', 'viz'
const userMode = ref('auto')
const displayRef = ref(null)
const cellCount = ref(24)

// Calculate dynamic cell count to fit container width
const updateCellCount = () => {
  if (!displayRef.value) return
  const width = displayRef.value.clientWidth
  if (width <= 0) return
  // Each cell is ~14px wide + 2px gap = 16px
  const count = Math.max(14, Math.min(48, Math.floor((width - 40) / 15.5)))
  cellCount.value = count
}

let resizeObserver = null

// Marquee state
const marqueeIndex = ref(0)
const marqueeDwell = ref(0) // Pause at start / end
const isGlitching = ref(false)
const glitchMasks = ref([])
const glitchProgress = ref(0)

// Disc spin animation
const discFrame = ref(0)
const discFrameMask = computed(() => DISC_FRAMES[discFrame.value % DISC_FRAMES.length])

// Idle animation state
const idleMode = ref(0) // 0: Spec show, 1: Clock, 2: Larson, 3: Standby disc
const larsonPos = ref(0)
const larsonDir = ref(1)
const idleTimer = ref(0)

// Clock state
const currentTimeStr = ref('')
const updateClock = () => {
  const now = new Date()
  const hh = String(now.getHours()).padStart(2, '0')
  const mm = String(now.getMinutes()).padStart(2, '0')
  const ss = String(now.getSeconds()).padStart(2, '0')
  const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
  const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
  const day = days[now.getDay()]
  const date = String(now.getDate()).padStart(2, '0')
  const mon = months[now.getMonth()]
  currentTimeStr.value = `[ ${hh}:${mm}:${ss} ]  ${day} ${date} ${mon}`
}

// Audio-reactive beat pulse
const isBeatPulse = ref(false)

// Mode Badge & Tooltip
const currentModeBadge = computed(() => {
  if (userMode.value === 'clock') return 'CLK'
  if (userMode.value === 'specs') return 'DSP'
  if (userMode.value === 'viz') return 'VIZ'
  if (!props.track) return 'IDLE'
  return 'TRK'
})

const isUserModeActive = computed(() => userMode.value !== 'auto')

const modeTooltip = computed(() => {
  return 'VFD Режим: ' + currentModeBadge.value + ' (Нажмите для переключения: Трек / Часы / Спецификации / Спектр)'
})

const cycleMode = (e) => {
  // Cycle modes on click
  if (userMode.value === 'auto') {
    userMode.value = 'clock'
  } else if (userMode.value === 'clock') {
    userMode.value = 'specs'
  } else if (userMode.value === 'specs') {
    userMode.value = 'viz'
  } else {
    userMode.value = 'auto'
  }
  triggerGlitch()
}

// Trigger decode glitch transition
const triggerGlitch = () => {
  isGlitching.value = true
  glitchProgress.value = 0
  const count = cellCount.value
  glitchMasks.value = Array.from({ length: count }, () => getRandomGlitchMask())
}

// Get string for Specs mode
const getSpecsString = () => {
  const isHd = !!props.hdTrackInfo
  const volPct = Math.round((props.volume || 1) * 100)
  const format = isHd ? '24-BIT 96kHz HI-RES' : 'STEREO 16-BIT 44.1kHz'
  return `${format}  *  VOL ${volPct}%  *  DIRECT DSP`
}

// Get string for Demo / Idle mode
const IDLE_DEMO_TEXTS = [
  'AUX BASS HIGH END REFERENCE STEREO',
  '24-BIT 96kHz DIRECT D/A CONVERTER',
  'DSP MASTER EQUALIZER ENGAGED',
  'NO DISC  -  INSERT AUDIO MEDIA'
]

// Determine target text string
const activeString = computed(() => {
  if (userMode.value === 'clock') {
    return currentTimeStr.value
  }
  if (userMode.value === 'specs') {
    return getSpecsString()
  }
  if (userMode.value === 'viz') {
    return '' // Larson or VU bars handle masks directly
  }

  // Auto mode
  if (props.track) {
    const artist = props.track.artist || 'UNKNOWN ARTIST'
    const title = props.track.title || props.track.file_name || 'UNTITLED'
    return `${artist} - ${title}`.toUpperCase()
  }

  // Idle mode when no track
  if (idleMode.value === 0) {
    return IDLE_DEMO_TEXTS[0]
  } else if (idleMode.value === 1) {
    return currentTimeStr.value
  } else if (idleMode.value === 2) {
    return '' // Handled by Larson scanner
  } else {
    return IDLE_DEMO_TEXTS[3]
  }
})

// Compute masks to display across all cells
const renderedMasks = computed(() => {
  const count = cellCount.value
  const fullText = activeString.value

  // Special mode: Larson wave visualizer
  if (userMode.value === 'viz' || (!props.track && idleMode.value === 2)) {
    return getLarsonMasks(count, larsonPos.value)
  }

  // Text encoding
  let displayedText = fullText
  if (!fullText) {
    return new Array(count).fill(0)
  }

  // Marquee handling if text exceeds cell count
  if (fullText.length > count) {
    const loopStr = fullText + '   ///   '
    const startIndex = marqueeIndex.value % loopStr.length
    let slice = ''
    for (let i = 0; i < count; i++) {
      slice += loopStr[(startIndex + i) % loopStr.length]
    }
    displayedText = slice
  } else {
    // Pad or center text
    const pad = Math.floor((count - fullText.length) / 2)
    displayedText = ' '.repeat(pad) + fullText
  }

  const baseMasks = encodeString(displayedText, count)

  // Apply glitch transition if active
  if (isGlitching.value && glitchMasks.value.length === count) {
    const resolvedIndex = Math.floor((glitchProgress.value / 100) * count)
    return baseMasks.map((mask, idx) => {
      if (idx < resolvedIndex) {
        return mask
      }
      return glitchMasks.value[idx] || mask
    })
  }

  return baseMasks
})

// Helper to determine segment CSS class
const getSegmentClass = (cellMask, segKey) => {
  const bit = SEGMENTS[segKey]
  if (!bit) return 'seg-off'
  const isOn = (cellMask & bit) !== 0
  return isOn ? 'seg-on' : 'seg-off'
}

// Watchers
watch(() => props.displayText, () => {
  marqueeIndex.value = 0
  marqueeDwell.value = 14 // 14 ticks ~ 2.8s dwell pause
  triggerGlitch()
})

watch(() => props.track?.id, () => {
  marqueeIndex.value = 0
  marqueeDwell.value = 14
  triggerGlitch()
})

// Main animation loop intervals
let marqueeTimer = null
let fastAnimationTimer = null
let clockTimer = null

onMounted(() => {
  updateClock()
  updateCellCount()

  if (displayRef.value && window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      updateCellCount()
    })
    resizeObserver.observe(displayRef.value)
  }

  triggerGlitch()

  // Marquee & idle ticker (every 200ms)
  marqueeTimer = setInterval(() => {
    const fullText = activeString.value
    const count = cellCount.value

    // Dwell handling
    if (marqueeDwell.value > 0) {
      marqueeDwell.value--
    } else {
      if (fullText && fullText.length > count) {
        marqueeIndex.value++
        const loopLen = fullText.length + 9
        if (marqueeIndex.value >= loopLen) {
          marqueeIndex.value = 0
          marqueeDwell.value = 12 // Pause again at start
        }
      }
    }

    // Disc spin
    if (props.isPlaying) {
      discFrame.value = (discFrame.value + 1) % DISC_FRAMES.length
      isBeatPulse.value = !isBeatPulse.value
    }

    // Idle cycle (every 30 ticks ~ 6 seconds)
    if (!props.track && userMode.value === 'auto') {
      idleTimer.value++
      if (idleTimer.value > 30) {
        idleTimer.value = 0
        idleMode.value = (idleMode.value + 1) % 4
        triggerGlitch()
      }
    }
  }, 200)

  // Fast animation ticker (every 50ms) for Glitch and Larson wave
  fastAnimationTimer = setInterval(() => {
    // Glitch progression
    if (isGlitching.value) {
      glitchProgress.value += 16
      // Randomize unsolved glitch cells
      for (let i = 0; i < glitchMasks.value.length; i++) {
        if (Math.random() > 0.4) {
          glitchMasks.value[i] = getRandomGlitchMask()
        }
      }
      if (glitchProgress.value >= 100) {
        isGlitching.value = false
      }
    }

    // Larson Scanner movement
    if (userMode.value === 'viz' || (!props.track && idleMode.value === 2)) {
      const count = cellCount.value
      larsonPos.value += larsonDir.value
      if (larsonPos.value >= count - 1) {
        larsonPos.value = count - 1
        larsonDir.value = -1
      } else if (larsonPos.value <= 0) {
        larsonPos.value = 0
        larsonDir.value = 1
      }
    }
  }, 50)

  // 1-second Clock updater
  clockTimer = setInterval(updateClock, 1000)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  if (marqueeTimer) clearInterval(marqueeTimer)
  if (fastAnimationTimer) clearInterval(fastAnimationTimer)
  if (clockTimer) clearInterval(clockTimer)
})
</script>

<style scoped>
.vfd-display {
  position: relative;
  width: 100%;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(ellipse at center, rgba(3, 16, 26, 0.95) 0%, rgba(1, 6, 12, 0.98) 100%);
  border-radius: 3px;
  padding: 1px 8px;
  user-select: none;
  cursor: pointer;
  overflow: hidden;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.9);
}

/* Glass Overlays */
.vfd-glass-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 5;
}

/* Authentic Horizontal Cathode Filament Wires */
.vfd-filament-wire {
  position: absolute;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(140, 240, 255, 0.15) 15%, 
    rgba(220, 255, 255, 0.35) 50%, 
    rgba(140, 240, 255, 0.15) 85%, 
    transparent 100%
  );
  box-shadow: 0 0 3px rgba(0, 240, 255, 0.2);
}

.vfd-filament-wire.top {
  top: 32%;
}

.vfd-filament-wire.bottom {
  top: 68%;
}

/* Specular Glare / Chamfer sheen */
.vfd-specular-glare {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 40%;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.06) 0%, transparent 100%);
}

/* Optical Filter Micro-Mesh Texture */
.vfd-mesh-texture {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(0, 240, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 240, 255, 0.02) 1px, transparent 1px);
  background-size: 3px 3px;
  opacity: 0.7;
}

/* Status bar & indicators */
.vfd-status-bar {
  position: absolute;
  left: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
  z-index: 6;
}

.vfd-disp-badge {
  font-family: 'Courier New', monospace;
  font-size: 7.5px;
  font-weight: 800;
  color: rgba(0, 240, 255, 0.4);
  letter-spacing: 0.5px;
  padding: 1px 3px;
  border-radius: 2px;
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.15);
  transition: all 0.2s ease;
}

.vfd-disp-badge.active,
.vfd-display:hover .vfd-disp-badge {
  color: #00f0ff;
  border-color: rgba(0, 240, 255, 0.6);
  box-shadow: 0 0 6px rgba(0, 240, 255, 0.5);
  background: rgba(0, 240, 255, 0.12);
}

.vfd-play-indicator {
  display: flex;
  align-items: center;
}

.vfd-spin-disc {
  width: 9px;
  height: 12px;
  display: inline-block;
}

.vfd-disc-svg {
  width: 100%;
  height: 100%;
}

/* Cells Grid */
.vfd-cells-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.8px;
  width: 100%;
  height: 100%;
  z-index: 2;
}

.vfd-cell {
  position: relative;
  flex-shrink: 0;
  width: 13.5px;
  height: 19px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.05s ease;
}

.vfd-cell.audio-pulsing {
  filter: brightness(1.08);
}

.vfd-cell-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

/* 16-Segment Styles */

/* Inactive Ghost Segment - faint, translucent, physical depth */
.seg-off {
  fill: rgba(0, 240, 255, 0.055);
  stroke: rgba(0, 240, 255, 0.02);
  stroke-width: 0.2;
  transition: fill 0.1s ease;
}

/* Active Segment - Glowing Neon Phosphor Core & Bloom */
.seg-on {
  fill: #8fefff;
  stroke: #ffffff;
  stroke-width: 0.15;
  filter: 
    drop-shadow(0 0 1px #ffffff) 
    drop-shadow(0 0 3.5px #00f0ff) 
    drop-shadow(0 0 8px rgba(0, 240, 255, 0.85));
  transition: fill 0.06s ease, filter 0.06s ease;
}

.vfd-display:hover .seg-on {
  fill: #ffffff;
  filter: 
    drop-shadow(0 0 1.5px #ffffff) 
    drop-shadow(0 0 4.5px #00f0ff) 
    drop-shadow(0 0 11px rgba(0, 240, 255, 0.95));
}
</style>
