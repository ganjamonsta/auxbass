<template>
  <header class="dj-console-header">
    <!-- Left: Brand & Model + Power/On Air Status -->
    <div class="header-left">
      <div class="brand-badge">
        <span class="brand-name">AUX-BASS</span>
        <span class="model-name">DJX-4000</span>
      </div>

      <div class="on-air-status" :class="{ active: isPlaying }">
        <span class="status-led"></span>
        <span class="status-label">{{ isPlaying ? 'ON AIR' : 'STANDBY' }}</span>
      </div>

      <!-- Master context badge -->
      <div v-if="contextTitle" class="context-rack-badge" :title="contextTitle">
        <span class="rack-type">{{ contextTypeLabel }}</span>
        <span class="rack-name">{{ contextTitle }}</span>
      </div>
    </div>

    <!-- Center: Master Stereo VU-Meter -->
    <div class="header-center">
      <div class="vu-meter-unit" :class="{ active: isPlaying }" title="Master Output VU Meter">
        <div class="vu-label">L</div>
        <div class="vu-channel">
          <span class="vu-led green" v-for="n in 5" :key="`l-g-${n}`"></span>
          <span class="vu-led yellow" v-for="n in 2" :key="`l-y-${n}`"></span>
          <span class="vu-led red"></span>
        </div>
        <div class="vu-divider">MASTER PEAK</div>
        <div class="vu-channel">
          <span class="vu-led green" v-for="n in 5" :key="`r-g-${n}`"></span>
          <span class="vu-led yellow" v-for="n in 2" :key="`r-y-${n}`"></span>
          <span class="vu-led red"></span>
        </div>
        <div class="vu-label">R</div>
      </div>
    </div>

    <!-- Right: Standby / Power Button -->
    <div class="header-right">
      <button 
        class="power-btn" 
        @click="$emit('close')" 
        title="Свернуть консоль (Esc)"
        aria-label="Свернуть"
      >
        <span class="power-led"></span>
        <span class="btn-text">EJECT</span>
        <span class="key-hint">ESC</span>
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  isPlaying: Boolean,
  contextInfo: Object,
  track: Object
})

defineEmits(['close'])

const contextTypeLabel = computed(() => {
  if (!props.contextInfo?.type) return 'SOURCE'
  const typeMap = {
    playlist: 'CRATE',
    album: 'ALBUM',
    artist: 'ARTIST',
    favorites: 'FAVORITES',
    channel: 'CHANNEL',
    history: 'HISTORY'
  }
  return typeMap[props.contextInfo.type.toLowerCase()] || props.contextInfo.type.toUpperCase()
})

const contextTitle = computed(() => {
  if (props.contextInfo?.name) return props.contextInfo.name
  if (props.track?.album_title) return props.track.album_title
  return ''
})
</script>

<style scoped>
.dj-console-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  background: linear-gradient(180deg, #181a1e 0%, #121316 100%);
  border-bottom: 2px solid #0a0b0d;
  box-shadow: 
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 4px 12px rgba(0, 0, 0, 0.6);
  position: relative;
  z-index: 10;
  flex-shrink: 0;
  user-select: none;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.brand-badge {
  display: flex;
  align-items: baseline;
  gap: 6px;
  padding: 4px 10px;
  background: #0d0e11;
  border-radius: var(--r-xs);
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: inset 1px 1px 3px rgba(0, 0, 0, 0.8);
}

.brand-name {
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 1.5px;
  color: var(--c-accent);
}

.model-name {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--c-text-3);
  font-family: var(--font-mono, monospace);
}

.on-air-status {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 4px 10px;
  border-radius: var(--r-xs);
  background: #0d0e11;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.status-led {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #3a1515;
  transition: all 0.2s ease;
}

.status-label {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1px;
  color: var(--c-text-4);
  font-family: var(--font-mono, monospace);
}

.on-air-status.active {
  border-color: rgba(239, 68, 68, 0.3);
}

.on-air-status.active .status-led {
  background: #ef4444;
  box-shadow: 0 0 10px #ef4444;
  animation: ledPulse 1.2s infinite alternate;
}

.on-air-status.active .status-label {
  color: #ff6b6b;
}

@keyframes ledPulse {
  0% { opacity: 0.7; }
  100% { opacity: 1; }
}

.context-rack-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: #15171b;
  border-radius: var(--r-xs);
  border: 1px solid rgba(255, 255, 255, 0.05);
  max-width: 260px;
}

.rack-type {
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 1px;
  color: var(--c-accent);
  font-family: var(--font-mono, monospace);
}

.rack-name {
  font-size: 11px;
  font-weight: 600;
  color: var(--c-text-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Center: VU Meter */
.header-center {
  display: flex;
  align-items: center;
}

.vu-meter-unit {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 14px;
  background: #090a0d;
  border-radius: var(--r-xs);
  border: 1px solid #1c1f26;
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.9);
}

.vu-label {
  font-size: 10px;
  font-weight: 800;
  color: var(--c-text-4);
  font-family: var(--font-mono, monospace);
}

.vu-divider {
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 1px;
  color: var(--c-text-4);
  font-family: var(--font-mono, monospace);
  padding: 0 4px;
}

.vu-channel {
  display: flex;
  align-items: center;
  gap: 3px;
}

.vu-led {
  width: 5px;
  height: 10px;
  border-radius: 1px;
  background: #1a1d24;
  transition: all 0.1s ease;
}

.vu-meter-unit.active .vu-led.green {
  animation: vuGreen 0.35s infinite alternate ease-in-out;
}

.vu-meter-unit.active .vu-led.yellow {
  animation: vuYellow 0.5s infinite alternate ease-in-out;
}

.vu-meter-unit.active .vu-led.red {
  animation: vuRed 0.8s infinite alternate ease-in-out;
}

.vu-channel .vu-led:nth-child(1) { animation-delay: 0.05s; }
.vu-channel .vu-led:nth-child(2) { animation-delay: 0.12s; }
.vu-channel .vu-led:nth-child(3) { animation-delay: 0.08s; }
.vu-channel .vu-led:nth-child(4) { animation-delay: 0.18s; }
.vu-channel .vu-led:nth-child(5) { animation-delay: 0.22s; }
.vu-channel .vu-led:nth-child(6) { animation-delay: 0.15s; }
.vu-channel .vu-led:nth-child(7) { animation-delay: 0.28s; }

@keyframes vuGreen {
  0% { background: #132417; }
  100% { background: #1db954; box-shadow: 0 0 6px rgba(29, 185, 84, 0.8); }
}

@keyframes vuYellow {
  0% { background: #26210f; }
  100% { background: #ffd700; box-shadow: 0 0 6px rgba(255, 215, 0, 0.8); }
}

@keyframes vuRed {
  0% { background: #291212; }
  100% { background: #ff4444; box-shadow: 0 0 8px rgba(255, 68, 68, 0.9); }
}

/* Right: Power/Eject */
.header-right {
  display: flex;
  align-items: center;
}

.power-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: linear-gradient(180deg, #24272f 0%, #17191e 100%);
  border: 1px solid #333842;
  border-radius: var(--r-xs);
  color: var(--c-text-2);
  cursor: pointer;
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  transition: all 0.15s ease;
}

.power-btn:hover {
  background: linear-gradient(180deg, #2c303a 0%, #1e2027 100%);
  color: #ffffff;
  border-color: #444a57;
}

.power-btn:active {
  transform: translateY(1px);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.8);
}

.power-led {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ff4444;
  box-shadow: 0 0 6px #ff4444;
}

.btn-text {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1px;
}

.key-hint {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 3px;
  background: rgba(0, 0, 0, 0.5);
  color: var(--c-text-3);
  font-family: var(--font-mono, monospace);
  border: 1px solid rgba(255, 255, 255, 0.05);
}
</style>
