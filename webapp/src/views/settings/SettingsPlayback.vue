<template>
  <section id="playback" class="settings-section">
    <div class="section-header">
      <h2>
        <Headphones :size="18" />
        <span>Аудио (Enhancer)</span>
      </h2>
      <span class="status-pill" :class="{ connected: playerStore.enhancerEnabled }">
        {{ playerStore.enhancerEnabled ? 'Включён' : 'Выключен' }}
      </span>
    </div>

    <div class="settings-card">
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Включить обработку</span>
          <span class="setting-desc">Улучшение звука в реальном времени (Bass, Treble, Auto Gain)</span>
        </div>
        <label class="toggle">
          <input 
            type="checkbox" 
            v-model="playerStore.enhancerEnabled" 
          />
          <span class="toggle-slider"></span>
        </label>
      </div>

      <template v-if="playerStore.enhancerEnabled">
        <div class="setting-divider"></div>

        <div class="setting-row slider-setting-block">
          <div class="slider-row-top">
            <span class="setting-name">Bass (Низкие)</span>
            <span class="setting-value">{{ playerStore.bassGain }} dB</span>
          </div>
          <input 
            type="range" 
            min="-10" 
            max="10" 
            step="1"
            v-model.number="playerStore.bassGain"
            class="range-slider"
          />
        </div>

        <div class="setting-divider"></div>

        <div class="setting-row slider-setting-block">
          <div class="slider-row-top">
            <span class="setting-name">Treble (Высокие)</span>
            <span class="setting-value">{{ playerStore.trebleGain }} dB</span>
          </div>
          <input 
            type="range" 
            min="-10" 
            max="10" 
            step="1"
            v-model.number="playerStore.trebleGain"
            class="range-slider"
          />
        </div>

        <div class="setting-divider"></div>

        <div class="setting-row">
          <div class="setting-info">
            <span class="setting-name">Auto Gain (Компрессор)</span>
            <span class="setting-desc">Автоматическое выравнивание громкости между треками</span>
          </div>
          <label class="toggle">
            <input 
              type="checkbox" 
              v-model="playerStore.autoGain" 
            />
            <span class="toggle-slider"></span>
          </label>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup>
import { Headphones } from 'lucide-vue-next'
import { usePlayerStore } from '@/stores/player'

const playerStore = usePlayerStore()
</script>

<style scoped>
.settings-section {
  margin-bottom: var(--sp-5);
  width: 100%;
  transition: all 0.3s ease;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  margin-bottom: 8px;
  padding: 0 2px;
}

.section-header h2 {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
  line-height: 1.4;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: var(--r-full);
  background: rgba(255, 255, 255, 0.05);
  color: var(--c-text-3);
  border: 1px solid rgba(255, 255, 255, 0.04);
  line-height: 1.2;
  flex-shrink: 0;
}

.status-pill.connected {
  background: rgba(29, 185, 84, 0.12);
  color: #1db954;
  border-color: rgba(29, 185, 84, 0.25);
}

.settings-card {
  background: var(--c-bg-2);
  border-radius: var(--r-lg);
  border: 1px solid rgba(255, 255, 255, 0.04);
  box-shadow: 
    3px 3px 10px var(--sh-dark),
    -1px -1px 2px var(--sh-light);
  padding: 16px;
  width: 100%;
  box-sizing: border-box;
}

.setting-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.05);
  margin: 12px 0;
  width: 100%;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  padding: 2px 0;
}

.setting-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  gap: 2px;
}

.setting-name {
  color: var(--c-text-1);
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
}

.setting-desc {
  color: var(--c-text-3);
  font-size: 12px;
  line-height: 1.4;
}

.toggle {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--c-bg-4);
  transition: .3s cubic-bezier(0.4, 0.0, 0.2, 1);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 2px;
  bottom: 2px;
  background-color: var(--c-text-2);
  transition: .3s cubic-bezier(0.4, 0.0, 0.2, 1);
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

input:checked + .toggle-slider {
  background-color: var(--c-accent);
  border-color: var(--c-accent);
}

input:checked + .toggle-slider:before {
  transform: translateX(20px);
  background-color: #fff;
}

.slider-setting-block {
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  width: 100%;
}

.slider-row-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  width: 100%;
}

.setting-value {
  color: var(--c-accent);
  font-weight: 600;
  font-size: 14px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.range-slider {
  width: 100%;
  height: 6px;
  background: var(--c-bg-4);
  border-radius: 3px;
  outline: none;
  -webkit-appearance: none;
  margin: 4px 0;
}

.range-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--c-accent);
  cursor: pointer;
  transition: transform 0.15s ease;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
}

.range-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

.range-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--c-accent);
  cursor: pointer;
  border: none;
}
</style>
