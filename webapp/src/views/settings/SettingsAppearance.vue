<template>
  <div class="settings-appearance-group">
    <!-- Interface Section -->
    <section id="interface" class="settings-section">
      <div class="section-header">
        <h2>
          <Sliders :size="18" />
          <span>Интерфейс</span>
        </h2>
      </div>

      <div class="settings-card">
        <div class="setting-row slider-setting-block">
          <div class="slider-row-top">
            <div class="slider-label-group">
              <span class="setting-name">Масштаб интерфейса</span>
              <button 
                v-if="Math.round(playerStore.uiScale * 100) !== 100"
                class="scale-reset-btn"
                @click="playerStore.uiScale = 1.0"
                title="Сбросить на 100%"
              >
                Сброс
              </button>
            </div>
            <span class="setting-value">{{ Math.round(playerStore.uiScale * 100) }}%</span>
          </div>

          <input 
            type="range" 
            min="0.7" 
            max="1.3" 
            step="0.05"
            v-model.number="playerStore.uiScale"
            class="range-slider"
          />

          <div class="scale-presets-wrap">
            <div class="scale-presets">
              <button 
                v-for="preset in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]" 
                :key="preset"
                class="scale-preset-chip"
                :class="{ active: Math.round(playerStore.uiScale * 100) === Math.round(preset * 100) }"
                @click="playerStore.uiScale = preset"
              >
                {{ Math.round(preset * 100) }}%
              </button>
            </div>
          </div>
          <span class="setting-desc scale-desc">Измените размер интерфейса плеера под экран устройства</span>
        </div>
      </div>
    </section>

    <!-- App (PWA) Section -->
    <section id="storage" class="settings-section">
      <div class="section-header">
        <h2>
          <Smartphone :size="18" />
          <span>Приложение</span>
        </h2>
      </div>

      <div class="settings-card">
        <div v-if="pwaInstall.isInstalled" class="pwa-status-installed">
          <div class="pwa-status-icon"><Check :size="20" /></div>
          <div class="pwa-status-text">
            <span class="pwa-status-title">Приложение установлено</span>
            <span class="pwa-status-desc">AuxBass работает в полноэкранном режиме Web App</span>
          </div>
        </div>

        <div v-else class="pwa-install-card">
          <div class="setting-info">
            <span class="setting-name">Установить как Web App</span>
            <span class="setting-desc">Быстрый запуск с домашнего экрана, фоновое воспроизведение и медиаклавиши</span>
          </div>
          <button class="action-btn primary pwa-install-btn" @click="handleInstallClick">
            <Download :size="16" />
            <span>{{ pwaInstall.isIOS ? 'Как установить' : 'Установить' }}</span>
          </button>
        </div>

        <div class="setting-divider"></div>

        <!-- App Version & Force Refresh -->
        <div class="setting-row app-version-row">
          <div class="setting-info">
            <div class="app-version-header">
              <span class="setting-name">Версия и кэш</span>
              <span class="version-badge">v{{ clientVersion }}</span>
            </div>
            <span class="setting-desc">
              Сборка: <code class="build-code">{{ clientBuildIdShort }}</code>
              <span v-if="updateAvailable" class="update-pending-tag"> • Доступно обновление!</span>
            </span>
          </div>
          <button 
            class="action-btn secondary update-action-btn"
            :class="{ 'highlight': updateAvailable }"
            :disabled="isUpdating"
            @click="handleForceUpdate"
            title="Очистить кэш браузера и перезагрузить свежий интерфейс"
          >
            <RefreshCw :size="14" :class="{ 'spin-anim': isUpdating }" />
            <span>{{ isUpdating ? 'Обновление…' : (updateAvailable ? 'Обновить' : 'Сбросить кэш') }}</span>
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Sliders, Smartphone, Check, Download, RefreshCw } from 'lucide-vue-next'
import { usePlayerStore } from '@/stores/player'
import { usePwaInstall } from '@/composables/usePwaInstall'
import { useAppUpdate } from '@/composables/useAppUpdate'

const playerStore = usePlayerStore()
const pwaInstall = usePwaInstall()

const {
  clientBuildId,
  clientVersion,
  updateAvailable,
  isUpdating,
  forceAppRefresh,
} = useAppUpdate()

const clientBuildIdShort = computed(() => {
  const id = clientBuildId?.value
  return typeof id === 'string' && id ? id.substring(0, 16) : 'актуальная'
})

const handleForceUpdate = async () => {
  await forceAppRefresh()
}

const handleInstallClick = () => {
  pwaInstall.promptInstall()
}
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

.slider-label-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.scale-reset-btn {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: var(--r-xs, 4px);
  background: var(--c-bg-3);
  color: var(--c-text-2);
  border: 1px solid rgba(255, 255, 255, 0.08);
  cursor: pointer;
  transition: all 0.15s ease;
}

.scale-reset-btn:hover {
  color: var(--c-accent);
  background: var(--c-bg-4);
  border-color: var(--c-accent-glow);
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

.scale-presets-wrap {
  overflow-x: auto;
  width: 100%;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  padding: 2px 0;
}

.scale-presets-wrap::-webkit-scrollbar {
  display: none;
}

.scale-presets {
  display: flex;
  gap: 6px;
  width: 100%;
  min-width: 320px;
}

.scale-preset-chip {
  flex: 1;
  min-width: 36px;
  padding: 6px 0;
  text-align: center;
  border-radius: var(--r-sm);
  background: var(--c-bg-3);
  color: var(--c-text-2);
  border: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.scale-preset-chip:hover {
  background: var(--c-bg-4);
  color: var(--c-text-1);
}

.scale-preset-chip.active {
  background: var(--c-accent);
  color: #000000;
  font-weight: 600;
  border-color: var(--c-accent);
  box-shadow: 0 0 8px var(--c-accent-glow);
}

.scale-desc {
  margin-top: 2px;
}

.pwa-status-installed {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(29, 185, 84, 0.1);
  border: 1px solid rgba(29, 185, 84, 0.25);
  border-radius: var(--r-md);
}

.pwa-status-icon {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--c-accent);
  color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.pwa-status-title {
  display: block;
  font-weight: 600;
  color: var(--c-text-1);
  font-size: 14px;
}

.pwa-status-desc {
  display: block;
  font-size: 12px;
  color: var(--c-text-2);
  margin-top: 1px;
}

.pwa-install-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.pwa-install-btn {
  flex-shrink: 0;
}

.app-version-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.app-version-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.version-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.build-code {
  font-family: monospace;
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.85);
}

.update-pending-tag {
  color: #1ed760;
  font-weight: 600;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: var(--r-full, 9999px);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.action-btn.primary {
  background: var(--c-accent);
  color: #000;
}

.action-btn.secondary {
  background: var(--c-bg-3);
  color: var(--c-text-1);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.update-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  white-space: nowrap;
  flex-shrink: 0;
}

.update-action-btn.highlight {
  background: rgba(29, 185, 84, 0.2);
  border-color: rgba(29, 185, 84, 0.5);
  color: #1ed760;
}

.update-action-btn.highlight:hover {
  background: rgba(29, 185, 84, 0.3);
}

.spin-anim {
  animation: spin 1s linear infinite;
}

/* @keyframes spin — defined in design-system.css */

@media (max-width: 540px) {
  .pwa-install-card {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .pwa-install-btn {
    width: 100%;
  }
}
</style>
