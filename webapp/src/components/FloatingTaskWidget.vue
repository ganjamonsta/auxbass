<template>
  <Teleport to="body">
    <TransitionGroup 
      name="task-widget-slide" 
      tag="div" 
      class="floating-tasks-container"
      :class="{ 'has-now-playing': hasNowPlaying }"
    >
      <div
        v-for="item in tasksStore.activeMinimizedJobs"
        :key="item.job.id"
        class="floating-task-card"
        :class="[item.meta?.type || 'generic', item.job.status, { 'is-queue': item.meta?.isQueue }]"
        @click="handleRestore(item.job.id)"
        :title="item.meta?.isQueue ? 'Фоновая очередь добавления треков' : 'Нажмите, чтобы развернуть окно импорта'"
      >
        <!-- Task type icon badge with spinner -->
        <div class="task-icon-badge">
          <div v-if="item.job.status === 'in_progress'" class="task-spinner"></div>
          <Check v-else-if="item.job.status === 'completed'" :size="16" class="task-success-icon" />
          <AlertCircle v-else :size="16" class="task-error-icon" />

          <Music2 v-if="item.meta?.type === 'exportify'" :size="14" class="task-type-glyph" />
          <CloudDownload v-else :size="14" class="task-type-glyph" />
        </div>

        <!-- Content info -->
        <div class="task-info">
          <div class="task-header-row">
            <span class="task-title" :title="item.job.title">{{ item.job.title }}</span>
            <span class="task-progress-badge">
              {{ item.job.processed_tracks }} / {{ item.job.total_tracks }} ({{ item.job.progress_percent }}%)
            </span>
          </div>

          <div class="task-subtext-row">
            <span class="task-subtext" :title="subtextFor(item.job)">
              {{ subtextFor(item.job) }}
            </span>
          </div>

          <!-- Mini download bar if currently downloading audio -->
          <div 
            v-if="item.job.download_percent !== null && item.job.download_percent !== undefined && item.job.status === 'in_progress'"
            class="task-download-bar"
          >
            <div class="task-download-fill" :style="{ width: `${item.job.download_percent}%` }"></div>
          </div>
        </div>

        <!-- Action buttons -->
        <div class="task-actions" @click.stop>
          <button
            v-if="!item.meta?.isQueue"
            class="task-action-btn restore"
            @click="handleRestore(item.job.id)"
            title="Развернуть"
          >
            <Maximize2 :size="14" />
          </button>
          <button
            v-if="item.job.status === 'in_progress'"
            class="task-action-btn cancel"
            @click="handleCancel(item.job.id)"
            :title="item.meta?.isQueue ? 'Отменить очередь' : 'Отменить импорт'"
          >
            <X :size="14" />
          </button>
        </div>

        <!-- Global bottom progress strip -->
        <div
          class="task-bottom-strip"
          :style="{ width: `${item.job.progress_percent}%` }"
          :class="{ completed: item.job.status === 'completed' }"
        ></div>
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Check, AlertCircle, Music2, CloudDownload, Maximize2, X } from 'lucide-vue-next'
import { useTasksStore } from '@/stores/tasks'
import { usePlayerStore } from '@/stores/player'
import { useAuthStore } from '@/stores/auth'

const tasksStore = useTasksStore()
const playerStore = usePlayerStore()
const authStore = useAuthStore()

const isDesktop = ref(typeof window !== 'undefined' ? window.innerWidth >= 768 : false)

const handleResize = () => {
  isDesktop.value = window.innerWidth >= 768
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

const hasNowPlaying = computed(() => {
  return isDesktop.value && !!playerStore.currentTrack && authStore.isAuthenticated
})

const subtextFor = (job) => {
  if (job.status === 'completed') return job.current_step || 'Импорт завершён'
  if (job.status === 'failed') return job.error_message || 'Ошибка'
  if (job.status === 'cancelled') return 'Отменено'

  if (job.current_step && job.current_track_title) {
    return `${job.current_track_title} • ${job.current_step}`
  }
  if (job.current_track_title) {
    return job.current_track_title
  }
  return job.current_step || 'Синхронизация...'
}

const handleRestore = (jobId) => {
  tasksStore.restoreJob(jobId)
}

const handleCancel = (jobId) => {
  tasksStore.cancelJob(jobId)
}
</script>

<style scoped>
.floating-tasks-container {
  position: fixed;
  z-index: 10001;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;

  /* Desktop positioning */
  right: 24px;
  bottom: 96px;
  max-width: 380px;
  width: calc(100vw - 48px);
  transition: right 0.25s ease, bottom 0.25s ease;
}

/* If Now Playing desktop right sidebar is active, shift widget so it's directly visible next to main tracklist */
.floating-tasks-container.has-now-playing {
  right: calc(320px + 24px);
}

@media (max-width: 768px) {
  .floating-tasks-container {
    right: 12px;
    left: 12px;
    bottom: 76px;
    max-width: none;
    width: auto;
  }
}

.floating-task-card {
  pointer-events: auto;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px 12px 12px;
  background: rgba(18, 20, 24, 0.94);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 14px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.6), 0 0 24px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.floating-task-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.25);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7);
}

/* Spotify Theme Accent */
.floating-task-card.exportify {
  border-color: rgba(29, 185, 84, 0.35);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55), 0 0 24px rgba(29, 185, 84, 0.15);
}

.floating-task-card.exportify .task-icon-badge {
  background: linear-gradient(135deg, #1db954 0%, #15883e 100%);
  color: #fff;
  box-shadow: 0 2px 10px rgba(29, 185, 84, 0.35);
}

/* SoundCloud Theme Accent */
.floating-task-card.import {
  border-color: rgba(255, 85, 0, 0.35);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55), 0 0 24px rgba(255, 85, 0, 0.15);
}

.floating-task-card.import .task-icon-badge {
  background: linear-gradient(135deg, #ff6600 0%, #cc4400 100%);
  color: #fff;
  box-shadow: 0 2px 10px rgba(255, 85, 0, 0.35);
}

/* Completed State */
.floating-task-card.completed {
  border-color: rgba(34, 197, 94, 0.4);
  background: rgba(16, 28, 22, 0.96);
}

/* Icon badge */
.task-icon-badge {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.task-spinner {
  position: absolute;
  inset: -3px;
  border: 2px solid transparent;
  border-top-color: #fff;
  border-radius: 13px;
  animation: spin 0.9s linear infinite;
}

.task-type-glyph {
  position: relative;
  z-index: 1;
}

/* Task details */
.task-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.task-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.task-title {
  font-size: 13px;
  font-weight: 600;
  color: #f1f3f5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-progress-badge {
  font-size: 11px;
  font-weight: 700;
  color: #1ed760;
  background: rgba(29, 185, 84, 0.12);
  padding: 1px 6px;
  border-radius: 6px;
  white-space: nowrap;
}

.floating-task-card.import .task-progress-badge {
  color: #ff8833;
  background: rgba(255, 85, 0, 0.12);
}

.task-subtext-row {
  display: flex;
  align-items: center;
}

.task-subtext {
  font-size: 11px;
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Track mini download bar */
.task-download-bar {
  width: 100%;
  height: 3px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 3px;
}

.task-download-fill {
  height: 100%;
  background: #38bdf8;
  border-radius: 2px;
  transition: width 0.2s ease;
}

/* Action buttons */
.task-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.task-action-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.06);
  border: none;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.15s ease;
}

.task-action-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.task-action-btn.cancel:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
}

/* Bottom Progress Strip */
.task-bottom-strip {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: linear-gradient(90deg, #1db954 0%, #38bdf8 100%);
  transition: width 0.3s ease;
}

.task-bottom-strip.completed {
  background: #22c55e;
}

/* @keyframes spin — defined in design-system.css */

/* Animations */
.task-widget-slide-enter-active,
.task-widget-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.task-widget-slide-enter-from {
  opacity: 0;
  transform: translateY(24px) scale(0.95);
}

.task-widget-slide-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.95);
}
</style>
