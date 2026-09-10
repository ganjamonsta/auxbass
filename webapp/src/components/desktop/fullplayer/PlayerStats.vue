<template>
  <div class="stats-panel">
    <div class="stats-grid">
      <!-- Bitrate / Quality -->
      <div class="stat-card neu-surface">
        <div class="stat-icon-wrapper">
          <Activity :size="16" class="stat-icon" />
        </div>
        <div class="stat-details">
          <span class="stat-label">Качество</span>
          <span class="stat-val">{{ bitrate ? `${bitrate} kbps` : 'Стандарт' }}</span>
        </div>
      </div>

      <!-- Plays count -->
      <div class="stat-card neu-surface">
        <div class="stat-icon-wrapper">
          <Headphones :size="16" class="stat-icon" />
        </div>
        <div class="stat-details">
          <span class="stat-label">Прослушиваний</span>
          <span class="stat-val">{{ playCount || 0 }}</span>
        </div>
      </div>

      <!-- Buffer status -->
      <div class="stat-card neu-surface">
        <div class="stat-icon-wrapper">
          <Radio :size="16" class="stat-icon" />
        </div>
        <div class="stat-details">
          <span class="stat-label">Буферизация</span>
          <span class="stat-val">{{ bufferedPercent || 0 }}%</span>
        </div>
      </div>

      <!-- Playback Mode -->
      <div class="stat-card neu-surface">
        <div class="stat-icon-wrapper">
          <Layers :size="16" class="stat-icon" />
        </div>
        <div class="stat-details">
          <span class="stat-label">Режим</span>
          <span class="stat-val">{{ playModeText || 'Обычный' }}</span>
        </div>
      </div>
    </div>

    <!-- Extra metadata if track is available -->
    <div v-if="track?.uploader || track?.forward_source || track?.file_name" class="extra-info-card neu-surface">
      <h3 class="extra-title">Источник аудио</h3>
      
      <div class="info-rows">
        <div v-if="track?.uploader" class="info-row">
          <span class="row-label">Загружено:</span>
          <span class="row-val">{{ track.uploader }}</span>
        </div>

        <div v-if="track?.forward_source?.forward_from_name" class="info-row">
          <span class="row-label">Переслано из:</span>
          <span class="row-val">{{ track.forward_source.forward_from_name }}</span>
        </div>

        <div v-if="track?.file_name" class="info-row">
          <span class="row-label">Имя файла:</span>
          <span class="row-val mono">{{ track.file_name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Activity, Headphones, Radio, Layers } from 'lucide-vue-next'

defineProps({
  bufferedPercent: Number,
  bitrate: [String, Number],
  playCount: Number,
  playModeText: String,
  track: Object
})
</script>

<style scoped>
.stats-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.stats-panel::-webkit-scrollbar {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--r-lg);
  background: var(--c-bg-2);
  border: 1px solid rgba(255, 255, 255, 0.03);
}

.stat-icon-wrapper {
  width: 36px;
  height: 36px;
  border-radius: var(--r-md);
  background: var(--c-bg-1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: inset 1px 1px 3px var(--sh-inset-dark);
}

.stat-icon {
  color: var(--c-accent);
}

.stat-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 11px;
  color: var(--c-text-3);
  font-weight: 500;
}

.stat-val {
  font-size: 14px;
  font-weight: 700;
  color: var(--c-text-1);
  font-family: var(--font-mono, monospace);
}

.extra-info-card {
  padding: 16px 20px;
  border-radius: var(--r-lg);
  background: var(--c-bg-2);
  border: 1px solid rgba(255, 255, 255, 0.03);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.extra-title {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--c-text-2);
  text-transform: uppercase;
  margin: 0;
}

.info-rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
}

.row-label {
  color: var(--c-text-3);
  flex-shrink: 0;
}

.row-val {
  color: var(--c-text-1);
  font-weight: 500;
  text-align: right;
  word-break: break-all;
}

.row-val.mono {
  font-family: var(--font-mono, monospace);
  font-size: 11px;
  color: var(--c-text-2);
}
</style>
