<template>
  <div 
    class="vfd-display" 
    ref="displayRef"
    @click="advanceSlide"
    @mouseenter="onHover(true)"
    @mouseleave="onHover(false)"
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
      <span class="vfd-disp-badge" :class="{ active: isPlaying || !!track }">
        {{ currentModeBadge }}
      </span>
      <span v-if="isPlaying" class="vfd-play-indicator">
        <span class="vfd-spin-disc">
          <canvas ref="discCanvas" class="vfd-disc-canvas" width="16" height="22"></canvas>
        </span>
      </span>
    </div>

    <!-- High-Performance 2D Canvas for all 16-Segment Cells -->
    <canvas ref="canvasRef" class="vfd-canvas"></canvas>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { 
  SEGMENTS, 
  encodeString, 
  DISC_FRAMES, 
  getRandomGlitchMask 
} from '@/utils/segmentFont16'

const props = defineProps({
  track: {
    type: Object,
    default: null
  },
  nextTrack: {
    type: Object,
    default: null
  },
  queueIndex: {
    type: Number,
    default: 0
  },
  queueLength: {
    type: Number,
    default: 0
  },
  isPlaying: {
    type: Boolean,
    default: false
  },
  volume: {
    type: Number,
    default: 1
  }
})

// 16-Segment Vector Path coordinates (viewBox 0 0 16 22)
const SEGMENT_PATHS = {
  A1: 'M 2.2 1.5 L 7.4 1.5 L 6.6 3.2 L 3.2 3.2 Z',
  A2: 'M 8.6 1.5 L 13.8 1.5 L 12.8 3.2 L 9.4 3.2 Z',
  F:  'M 1.5 2.2 L 3.2 3.8 L 3.2 9.6 L 1.5 10.4 Z',
  B:  'M 14.5 2.2 L 14.5 10.4 L 12.8 9.6 L 12.8 3.8 Z',
  G1: 'M 2.6 11.0 L 3.6 10.3 L 7.4 10.3 L 6.8 11.7 L 3.6 11.7 Z',
  G2: 'M 8.6 10.3 L 12.4 10.3 L 13.4 11.0 L 12.4 11.7 L 9.2 11.7 Z',
  E:  'M 1.5 11.6 L 3.2 12.4 L 3.2 18.2 L 1.5 19.8 Z',
  C:  'M 14.5 11.6 L 14.5 19.8 L 12.8 18.2 L 12.8 12.4 Z',
  D1: 'M 3.2 18.8 L 6.6 18.8 L 7.4 20.5 L 2.2 20.5 Z',
  D2: 'M 9.4 18.8 L 12.8 18.8 L 13.8 20.5 L 8.6 20.5 Z',
  J:  'M 7.4 3.8 L 8.6 3.8 L 8.6 9.8 L 7.4 9.8 Z',
  M:  'M 7.4 12.2 L 8.6 12.2 L 8.6 18.2 L 7.4 18.2 Z',
  H:  'M 3.8 4.2 L 4.9 3.8 L 7.2 9.4 L 6.1 9.8 Z',
  K:  'M 11.1 3.8 L 12.2 4.2 L 9.9 9.8 L 8.8 9.4 Z',
  L:  'M 6.1 12.2 L 7.2 12.6 L 4.9 18.2 L 3.8 17.8 Z',
  N:  'M 8.8 12.6 L 9.9 12.2 L 12.2 17.8 L 11.1 18.2 Z'
}

let SEG_ENTRIES = null
let ALL_SEG_ENTRIES = null

const initPathObjects = () => {
  if (SEG_ENTRIES || typeof Path2D === 'undefined') return
  SEG_ENTRIES = Object.entries(SEGMENT_PATHS).map(([key, d]) => [
    SEGMENTS[key],
    new Path2D(d)
  ])
  const dp = new Path2D()
  dp.arc(15.2, 20.0, 0.9, 0, Math.PI * 2)
  ALL_SEG_ENTRIES = [...SEG_ENTRIES, [SEGMENTS.DP, dp]]
}

// DOM & Canvas elements
const displayRef = ref(null)
const canvasRef = ref(null)
const discCanvas = ref(null)
const cellCount = ref(24)
const isHovered = ref(false)

// Disc spin animation
const discFrame = ref(0)
const discFrameMask = computed(() => DISC_FRAMES[discFrame.value % DISC_FRAMES.length])

// Audio-reactive pulse
const isBeatPulse = ref(false)

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

// Helper: Extract release year from dates (YYYY, YYYY-MM-DD, ISO string, etc.)
const extractYear = (val) => {
  if (!val) return ''
  const str = String(val).trim()
  const match = str.match(/\b(19\d\d|20\d\d)\b/)
  if (match) return match[1]
  const d = new Date(val)
  return isNaN(d.getFullYear()) ? '' : String(d.getFullYear())
}

// Track Slides Generator — only includes fields that exist
const trackSlides = computed(() => {
  const t = props.track
  if (!t) return []

  const slides = []

  // 1. Track Title
  const title = (t.title || t.file_name || 'UNTITLED').trim()
  slides.push({
    badge: 'TRK',
    text: title.toUpperCase()
  })

  // 2. Artist / Authors
  const artist = (t.artist || 'UNKNOWN ARTIST').trim()
  slides.push({
    badge: 'ART',
    text: artist.toUpperCase()
  })

  // 3. Album (if present)
  const albumTitle = (t.album?.title || t.album_name || '').trim()
  if (albumTitle) {
    slides.push({
      badge: 'ALB',
      text: albumTitle.toUpperCase()
    })
  }

  // 4. Release Date / Year (if present)
  const rawDate = t.release_date || t.album?.release_date
  const year = extractYear(rawDate)
  if (year) {
    slides.push({
      badge: 'YEAR',
      text: `RELEASED ${year}`
    })
  }

  // 5. Next Track in Queue (if present)
  if (props.nextTrack) {
    const nextArt = (props.nextTrack.artist || '').trim()
    const nextTitle = (props.nextTrack.title || props.nextTrack.file_name || '').trim()
    const nextStr = nextArt && nextTitle ? `${nextArt} - ${nextTitle}` : (nextTitle || nextArt)
    if (nextStr) {
      slides.push({
        badge: 'NEXT',
        text: `NEXT: ${nextStr.toUpperCase()}`
      })
    }
  }

  // 6. Genre / Style (if present)
  const genre = (t.genre || (Array.isArray(t.tags) && t.tags[0]) || '').trim()
  if (genre) {
    slides.push({
      badge: 'GEN',
      text: `GENRE: ${genre.toUpperCase()}`
    })
  }

  // 7. Position in Queue (if queue length > 1)
  if (props.queueLength > 1 && props.queueIndex >= 0) {
    slides.push({
      badge: 'POS',
      text: `TRACK ${props.queueIndex + 1} OF ${props.queueLength}`
    })
  }

  return slides
})

// Idle Slides (when no track is playing)
const IDLE_SLIDES = computed(() => [
  { badge: 'TG', text: 'TG PLAYER REFERENCE STEREO' },
  { badge: 'CLK', text: currentTimeStr.value },
  { badge: 'IDLE', text: 'NO DISC  -  INSERT MEDIA' }
])

// Current active slide index
const currentSlideIndex = ref(0)
const slideTicks = ref(0)

const activeSlide = computed(() => {
  if (props.track) {
    const list = trackSlides.value
    if (list.length === 0) return { badge: 'TRK', text: 'NO MEDIA' }
    const idx = currentSlideIndex.value % list.length
    return list[idx]
  }
  const idleList = IDLE_SLIDES.value
  const idx = currentSlideIndex.value % idleList.length
  return idleList[idx]
})

const currentModeBadge = computed(() => activeSlide.value.badge)
const activeString = computed(() => activeSlide.value.text)

const modeTooltip = computed(() => {
  if (props.track) {
    return `VFD [${currentModeBadge.value}]: ${activeString.value} (кликните для следующего слайда)`
  }
  return 'TG Player Reference Stereo'
})

// Marquee & Glitch Animation state
const marqueeIndex = ref(0)
const marqueeDwell = ref(14)
const isGlitching = ref(false)
const glitchMasks = ref([])
const glitchProgress = ref(0)

// Glitch loop for authentic VFD segment decrypt/decode transition
let glitchAnimId = null
let lastGlitchTime = 0

const stepGlitch = (now) => {
  if (!isGlitching.value) {
    glitchAnimId = null
    return
  }
  if (now - lastGlitchTime >= 35) {
    lastGlitchTime = now
    glitchProgress.value += 16
    for (let i = 0; i < glitchMasks.value.length; i++) {
      if (Math.random() > 0.35) {
        glitchMasks.value[i] = getRandomGlitchMask()
      }
    }
    if (glitchProgress.value >= 100) {
      isGlitching.value = false
      glitchAnimId = null
      scheduleDraw()
      return
    }
    scheduleDraw()
  }
  glitchAnimId = requestAnimationFrame(stepGlitch)
}

const startGlitchLoop = () => {
  lastGlitchTime = performance.now()
  if (!glitchAnimId) {
    glitchAnimId = requestAnimationFrame(stepGlitch)
  }
}

const triggerGlitch = () => {
  isGlitching.value = true
  glitchProgress.value = 0
  const count = cellCount.value
  glitchMasks.value = Array.from({ length: count }, () => getRandomGlitchMask())
  startGlitchLoop()
}

// Advance slide method (called automatically or on user click)
const advanceSlide = () => {
  const list = props.track ? trackSlides.value : IDLE_SLIDES.value
  if (list.length <= 1) return
  currentSlideIndex.value = (currentSlideIndex.value + 1) % list.length
  marqueeIndex.value = 0
  marqueeDwell.value = 14
  slideTicks.value = 0
  triggerGlitch()
  scheduleDraw()
}

const onHover = (hovering) => {
  isHovered.value = hovering
  scheduleDraw()
}

// Rendered segment masks
const renderedMasks = computed(() => {
  const count = cellCount.value
  const fullText = activeString.value

  let displayedText = fullText
  if (!fullText) return new Array(count).fill(0)

  if (fullText.length > count) {
    const loopStr = fullText + '   ///   '
    const startIndex = marqueeIndex.value % loopStr.length
    let slice = ''
    for (let i = 0; i < count; i++) {
      slice += loopStr[(startIndex + i) % loopStr.length]
    }
    displayedText = slice
  } else {
    const pad = Math.floor((count - fullText.length) / 2)
    displayedText = ' '.repeat(pad) + fullText
  }

  const baseMasks = encodeString(displayedText, count)

  if (isGlitching.value && glitchMasks.value.length === count) {
    const resolvedIndex = Math.floor((glitchProgress.value / 100) * count)
    return baseMasks.map((mask, idx) => {
      if (idx < resolvedIndex) return mask
      return glitchMasks.value[idx] || mask
    })
  }

  return baseMasks
})

// Calculate dynamic cell count to fit container width
const updateCellCount = () => {
  if (!displayRef.value) return
  const width = displayRef.value.clientWidth
  if (width <= 0) return
  const count = Math.max(14, Math.min(48, Math.floor((width - 44) / 15.5)))
  if (cellCount.value !== count) {
    cellCount.value = count
  }
}

// High performance requestAnimationFrame drawing
let drawScheduled = false
const scheduleDraw = () => {
  if (drawScheduled) return
  drawScheduled = true
  requestAnimationFrame(() => {
    drawScheduled = false
    drawVfd()
  })
}

const drawVfd = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  initPathObjects()
  if (!ALL_SEG_ENTRIES) return

  const dpr = window.devicePixelRatio || 1
  const w = canvas.clientWidth
  const h = canvas.clientHeight
  if (w <= 0 || h <= 0) return

  const targetW = Math.round(w * dpr)
  const targetH = Math.round(h * dpr)
  if (canvas.width !== targetW || canvas.height !== targetH) {
    canvas.width = targetW
    canvas.height = targetH
  }

  ctx.save()
  ctx.scale(dpr, dpr)
  ctx.clearRect(0, 0, w, h)

  const masks = renderedMasks.value
  const count = masks.length
  if (count === 0) {
    ctx.restore()
    return
  }

  const cellH = Math.min(18.5, h - 2)
  const scale = cellH / 22
  const cellW = 16 * scale
  const gap = 1.8
  const pitch = cellW + gap
  const totalW = count * pitch - gap
  const leftReserved = 42
  const startX = Math.max(leftReserved, (w - totalW) / 2)
  const startY = (h - cellH) / 2
  const skewTan = -0.13165 // skewX(-7.5deg)

  // PASS 1: Ghost / Inactive segments
  ctx.fillStyle = 'rgba(0, 240, 255, 0.055)'
  ctx.strokeStyle = 'rgba(0, 240, 255, 0.02)'
  ctx.lineWidth = 0.2

  for (let i = 0; i < count; i++) {
    const mask = masks[i]
    ctx.save()
    ctx.translate(startX + i * pitch, startY)
    ctx.transform(1, 0, skewTan, 1, 0, 0)
    ctx.scale(scale, scale)
    for (let s = 0; s < ALL_SEG_ENTRIES.length; s++) {
      const [bit, path] = ALL_SEG_ENTRIES[s]
      if ((mask & bit) === 0) {
        ctx.fill(path)
        ctx.stroke(path)
      }
    }
    ctx.restore()
  }

  // PASS 2: Glowing phosphor layer for active segments
  const hovered = isHovered.value
  const pulse = isBeatPulse.value && props.isPlaying
  ctx.shadowColor = hovered ? 'rgba(0, 240, 255, 0.95)' : 'rgba(0, 240, 255, 0.8)'
  ctx.shadowBlur = (hovered ? 6.5 : (pulse ? 5.2 : 4)) * dpr
  ctx.fillStyle = hovered ? '#ffffff' : (pulse ? '#a5f5ff' : '#8fefff')
  ctx.strokeStyle = '#ffffff'
  ctx.lineWidth = 0.15

  for (let i = 0; i < count; i++) {
    const mask = masks[i]
    if (!mask) continue
    ctx.save()
    ctx.translate(startX + i * pitch, startY)
    ctx.transform(1, 0, skewTan, 1, 0, 0)
    ctx.scale(scale, scale)
    for (let s = 0; s < ALL_SEG_ENTRIES.length; s++) {
      const [bit, path] = ALL_SEG_ENTRIES[s]
      if ((mask & bit) !== 0) {
        ctx.fill(path)
        ctx.stroke(path)
      }
    }
    ctx.restore()
  }

  // PASS 3: Crisp high-white center core for true vacuum tube luminescence
  ctx.shadowBlur = 0
  ctx.fillStyle = '#f0fdff'
  for (let i = 0; i < count; i++) {
    const mask = masks[i]
    if (!mask) continue
    ctx.save()
    ctx.translate(startX + i * pitch, startY)
    ctx.transform(1, 0, skewTan, 1, 0, 0)
    ctx.scale(scale, scale)
    for (let s = 0; s < ALL_SEG_ENTRIES.length; s++) {
      const [bit, path] = ALL_SEG_ENTRIES[s]
      if ((mask & bit) !== 0) {
        ctx.fill(path)
      }
    }
    ctx.restore()
  }

  ctx.restore()
}

// Spinning disc rendering on tiny status canvas
const drawDisc = () => {
  const canvas = discCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  initPathObjects()
  if (!SEG_ENTRIES) return

  const mask = discFrameMask.value
  ctx.clearRect(0, 0, 16, 22)
  ctx.save()
  ctx.transform(1, 0, -0.13165, 1, 0, 0)

  // off
  ctx.fillStyle = 'rgba(0, 240, 255, 0.055)'
  for (let s = 0; s < SEG_ENTRIES.length; s++) {
    const [bit, path] = SEG_ENTRIES[s]
    if ((mask & bit) === 0) ctx.fill(path)
  }

  // on
  ctx.shadowColor = 'rgba(0, 240, 255, 0.85)'
  ctx.shadowBlur = 4
  ctx.fillStyle = '#8fefff'
  ctx.strokeStyle = '#ffffff'
  ctx.lineWidth = 0.15
  for (let s = 0; s < SEG_ENTRIES.length; s++) {
    const [bit, path] = SEG_ENTRIES[s]
    if ((mask & bit) !== 0) {
      ctx.fill(path)
      ctx.stroke(path)
    }
  }
  ctx.restore()
}

// Watchers
watch(() => props.track?.id, () => {
  currentSlideIndex.value = 0
  marqueeIndex.value = 0
  marqueeDwell.value = 14
  slideTicks.value = 0
  triggerGlitch()
})

watch(() => props.isPlaying, (playing) => {
  if (playing) {
    nextTick(() => drawDisc())
  }
  scheduleDraw()
})

watch(() => renderedMasks.value, () => {
  scheduleDraw()
})

let resizeObserver = null
let tickerTimer = null
let clockTimer = null

onMounted(() => {
  initPathObjects()
  updateClock()
  updateCellCount()

  if (displayRef.value && window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      updateCellCount()
      scheduleDraw()
    })
    resizeObserver.observe(displayRef.value)
  }

  triggerGlitch()
  scheduleDraw()
  if (props.isPlaying) {
    drawDisc()
  }

  // Unified Ticker (every 200ms) - handles marquee, dwell, and slide advancement
  tickerTimer = setInterval(() => {
    const fullText = activeString.value
    const count = cellCount.value
    const isLongText = fullText && fullText.length > count

    if (!isHovered.value) {
      slideTicks.value++

      if (isLongText) {
        if (marqueeDwell.value > 0) {
          marqueeDwell.value--
        } else {
          marqueeIndex.value++
          const loopLen = fullText.length + 9
          if (marqueeIndex.value >= loopLen) {
            advanceSlide()
            return
          }
        }
      } else {
        // Short text: stays for 22 ticks (~4.4s) before advancing to next slide
        if (slideTicks.value >= 22) {
          advanceSlide()
          return
        }
      }
    }

    if (props.isPlaying) {
      discFrame.value = (discFrame.value + 1) % DISC_FRAMES.length
      isBeatPulse.value = !isBeatPulse.value
      drawDisc()
    }

    scheduleDraw()
  }, 200)

  // Clock ticker (1 second) - updates clock string
  clockTimer = setInterval(() => {
    updateClock()
    if (!props.track) {
      scheduleDraw()
    }
  }, 1000)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  if (tickerTimer) clearInterval(tickerTimer)
  if (clockTimer) clearInterval(clockTimer)
  if (glitchAnimId) cancelAnimationFrame(glitchAnimId)
})
</script>

<style scoped>
.vfd-display {
  position: relative;
  flex: 1;
  min-width: 0;
  width: 100%;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(ellipse at center, rgba(3, 16, 26, 0.95) 0%, rgba(1, 6, 12, 0.98) 100%);
  border-radius: 3px;
  padding: 1px 6px;
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
  color: rgba(0, 240, 255, 0.65);
  letter-spacing: 0.5px;
  padding: 1px 3px;
  border-radius: 2px;
  background: rgba(0, 240, 255, 0.07);
  border: 1px solid rgba(0, 240, 255, 0.25);
  transition: all 0.25s ease;
}

.vfd-disp-badge.active,
.vfd-display:hover .vfd-disp-badge {
  color: #00f0ff;
  border-color: rgba(0, 240, 255, 0.7);
  box-shadow: 0 0 6px rgba(0, 240, 255, 0.45);
  background: rgba(0, 240, 255, 0.14);
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

.vfd-disc-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.vfd-canvas {
  width: 100%;
  height: 100%;
  display: block;
  z-index: 2;
}
</style>
