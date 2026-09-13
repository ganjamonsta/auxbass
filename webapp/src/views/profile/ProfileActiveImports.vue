<template>
  <div v-if="tasksStore.hasActiveImports" class="profile-active-imports-panel">
    <div class="panel-section-header">
      <div class="panel-section-title">
        <CloudDownload :size="15" class="section-icon-pulse" />
        <span>Импорт медиатеки</span>
        <span class="panel-section-count">{{ tasksStore.activeMinimizedJobs.length }}</span>
      </div>
      <span class="panel-overall-progress">Общий прогресс: {{ tasksStore.overallProgress }}%</span>
    </div>

    <div class="panel-import-cards">
      <div
        v-for="item in tasksStore.activeMinimizedJobs"
        :key="item.job.id"
        class="profile-import-card"
        :class="[item.meta?.type || 'generic', item.job.status, { 'is-queue': item.meta?.isQueue }]"
        @click="$emit('restore', item.job.id)"
        :title="item.meta?.isQueue ? 'Очередь загрузки треков' : 'Нажмите, чтобы развернуть окно импорта'"
      >
        <!-- Top row: icon + title + progress + actions -->
        <div class="import-card-top">
          <div class="import-icon-badge">
            <div v-if="item.job.status === 'in_progress'" class="import-spinner"></div>
            <Check v-else-if="item.job.status === 'completed'" :size="14" class="import-status-glyph success" />
            <AlertCircle v-else :size="14" class="import-status-glyph error" />

            <Music2 v-if="item.meta?.type === 'exportify'" :size="13" class="import-type-glyph" />
            <CloudDownload v-else :size="13" class="import-type-glyph" />
          </div>

          <div class="import-main-info">
            <div class="import-name-row">
              <span class="import-name" :title="item.job.title">{{ item.job.title }}</span>
              <span class="import-pct-badge">
                {{ item.job.progress_percent }}%
              </span>
            </div>
            <div class="import-stats-row">
              <span class="import-tracks-count">
                {{ item.job.processed_tracks }} / {{ item.job.total_tracks }} треков
              </span>
            </div>
          </div>

          <div class="import-actions" @click.stop>
            <button
              v-if="!item.meta?.isQueue"
              class="import-action-btn restore"
              @click="$emit('restore', item.job.id)"
              title="Развернуть"
            >
              <Maximize2 :size="13" />
            </button>
            <button
              v-if="item.job.status === 'in_progress'"
              class="import-action-btn cancel"
              @click="$emit('cancel', item.job.id)"
              :title="item.meta?.isQueue ? 'Отменить очередь' : 'Отменить импорт'"
            >
              <X :size="13" />
            </button>
          </div>
        </div>

        <!-- Subtext row -->
        <div class="import-subtext" :title="subtextFor(item.job)">
          {{ subtextFor(item.job) }}
        </div>

        <!-- Mini download bar if currently downloading audio file -->
        <div 
          v-if="item.job.download_percent !== null && item.job.download_percent !== undefined && item.job.status === 'in_progress'"
          class="import-download-bar"
        >
          <div class="import-download-fill" :style="{ width: `${item.job.download_percent}%` }"></div>
        </div>

        <!-- Overall progress line -->
        <div class="import-progress-bar">
          <div 
            class="import-progress-fill"
            :style="{ width: `${item.job.progress_percent}%` }"
            :class="{ completed: item.job.status === 'completed' }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useTasksStore } from '@/stores/tasks'
import { subtextFor } from './profileUtils'
import {
  CloudDownload,
  Check,
  AlertCircle,
  Music2,
  Maximize2,
  X,
} from 'lucide-vue-next'

const tasksStore = useTasksStore()

defineEmits(['restore', 'cancel'])
</script>

<style scoped>
.profile-active-imports-panel {
  background: rgba(20, 24, 33, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(16px);
  border-radius: 16px;
  padding: 16px 20px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  animation: panelFadeIn 0.3s ease;
}

@keyframes panelFadeIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.panel-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.panel-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-text-1, #fff);
}

.section-icon-pulse {
  color: #ff6600;
  animation: iconPulse 2s infinite ease-in-out;
}

@keyframes iconPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.15); opacity: 0.75; }
}

.panel-section-count {
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
  padding: 1px 7px;
  border-radius: 12px;
}

.panel-overall-progress {
  font-size: 12px;
  font-weight: 600;
  color: var(--c-accent, #1db954);
}

.panel-import-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.profile-import-card {
  position: relative;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 12px 14px 14px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.profile-import-card:hover {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.16);
}

.profile-import-card.exportify {
  border-color: rgba(29, 185, 84, 0.3);
  background: rgba(29, 185, 84, 0.06);
}

.profile-import-card.import {
  border-color: rgba(255, 85, 0, 0.3);
  background: rgba(255, 85, 0, 0.06);
}

.profile-import-card.completed {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(16, 28, 22, 0.6);
}

.import-card-top {
  display: flex;
  align-items: center;
  gap: 12px;
}

.import-icon-badge {
  position: relative;
  width: 32px;
  height: 32px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.profile-import-card.exportify .import-icon-badge {
  background: linear-gradient(135deg, #1db954 0%, #15883e 100%);
}

.profile-import-card.import .import-icon-badge {
  background: linear-gradient(135deg, #ff6600 0%, #cc4400 100%);
}

.import-spinner {
  position: absolute;
  inset: -2px;
  border: 2px solid transparent;
  border-top-color: #fff;
  border-radius: 11px;
  animation: spin 0.9s linear infinite;
}

.import-status-glyph.success {
  color: #22c55e;
}

.import-status-glyph.error {
  color: #ef4444;
}

.import-main-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.import-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.import-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.import-pct-badge {
  font-size: 11px;
  font-weight: 700;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 6px;
  border-radius: 6px;
  flex-shrink: 0;
}

.import-stats-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.import-tracks-count {
  font-size: 11px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
}

.import-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.import-action-btn {
  background: transparent;
  border: none;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  padding: 5px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.import-action-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: var(--c-text-1, #fff);
}

.import-action-btn.cancel:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
}

.import-subtext {
  font-size: 11px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.55));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 8px;
  margin-bottom: 6px;
}

.import-download-bar {
  height: 2px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 4px;
}

.import-download-fill {
  height: 100%;
  background: #3b82f6;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.import-progress-bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  overflow: hidden;
}

.import-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6600, #ff8533);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.profile-import-card.exportify .import-progress-fill {
  background: linear-gradient(90deg, #1db954, #1ed760);
}

.import-progress-fill.completed {
  background: #22c55e;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
