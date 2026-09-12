import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ingestionApi } from '@/api/client'
import { useUIStore } from './ui'
import { useLibraryStore } from './library'

export const useTasksStore = defineStore('tasks', () => {
  const uiStore = useUIStore()
  const libraryStore = useLibraryStore()

  // Map of jobId -> job object
  const jobs = ref(new Map())
  
  // Map of jobId -> metadata: { type: 'exportify' | 'import', title: string, previewData?: any }
  const jobMetas = ref(new Map())

  // Set of minimized job IDs
  const minimizedJobIds = ref(new Set())

  // Modal visibility states
  const showExportifyModal = ref(false)
  const showImportModal = ref(false)

  // Current active job for modals
  const currentExportifyJob = ref(null)
  const currentImportJob = ref(null)

  // Polling timers map
  const pollTimers = new Map()

  /**
   * Register a new job and begin background polling
   */
  const registerJob = (job, meta = {}) => {
    if (!job || !job.id) return

    // Clone to ensure reactivity
    const nextJobs = new Map(jobs.value)
    nextJobs.set(job.id, job)
    jobs.value = nextJobs

    const nextMetas = new Map(jobMetas.value)
    nextMetas.set(job.id, {
      type: meta.type || 'exportify',
      title: job.title || meta.title || 'Импорт медиатеки',
      ...meta,
    })
    jobMetas.value = nextMetas

    if (meta.type === 'exportify') {
      currentExportifyJob.value = job
    } else if (meta.type === 'import') {
      currentImportJob.value = job
    }

    startPolling(job.id)
  }

  /**
   * Start polling job status
   */
  const startPolling = (jobId) => {
    stopPolling(jobId)

    const timer = setInterval(async () => {
      try {
        const res = await ingestionApi.getJob(jobId)
        const updated = res.data

        const nextJobs = new Map(jobs.value)
        nextJobs.set(jobId, updated)
        jobs.value = nextJobs

        // Sync with active modal ref
        const meta = jobMetas.value.get(jobId)
        if (meta?.type === 'exportify' && currentExportifyJob.value?.id === jobId) {
          currentExportifyJob.value = updated
        } else if (meta?.type === 'import' && currentImportJob.value?.id === jobId) {
          currentImportJob.value = updated
        }

        if (['completed', 'failed', 'cancelled'].includes(updated.status)) {
          stopPolling(jobId)
          libraryStore.fetchTracks({ refresh: true })

          if (updated.status === 'completed') {
            if (minimizedJobIds.value.has(jobId)) {
              uiStore.toast?.success(
                'Импорт завершён!',
                `Успешно обработано треков: ${updated.processed_tracks}`
              )
            }
          } else if (updated.status === 'failed') {
            if (minimizedJobIds.value.has(jobId)) {
              uiStore.toast?.error('Ошибка импорта', updated.error_message || 'Не удалось завершить задачу')
            }
          }

          // Auto-remove finished job from minimized widget after 4 seconds
          setTimeout(() => {
            if (minimizedJobIds.value.has(jobId)) {
              const nextMin = new Set(minimizedJobIds.value)
              nextMin.delete(jobId)
              minimizedJobIds.value = nextMin
            }
          }, 4000)
        }
      } catch (err) {
        console.error(`[TasksStore] Polling error for job ${jobId}:`, err)
      }
    }, 1500)

    pollTimers.set(jobId, timer)
  }

  /**
   * Stop polling for a specific job
   */
  const stopPolling = (jobId) => {
    if (pollTimers.has(jobId)) {
      clearInterval(pollTimers.get(jobId))
      pollTimers.delete(jobId)
    }
  }

  /**
   * Minimize an active job into floating widget
   */
  const minimizeJob = (jobId) => {
    if (!jobId) return

    const nextMin = new Set(minimizedJobIds.value)
    nextMin.add(jobId)
    minimizedJobIds.value = nextMin

    const meta = jobMetas.value.get(jobId)
    if (meta?.type === 'exportify') {
      showExportifyModal.value = false
    } else if (meta?.type === 'import') {
      showImportModal.value = false
    }

    uiStore.toast?.info(
      'Процесс свернут',
      'Импорт продолжается в фоне. Вы можете продолжать слушать музыку!'
    )
  }

  /**
   * Restore a minimized job back into its full modal
   */
  const restoreJob = (jobId) => {
    if (!jobId) return

    const nextMin = new Set(minimizedJobIds.value)
    nextMin.delete(jobId)
    minimizedJobIds.value = nextMin

    const job = jobs.value.get(jobId)
    const meta = jobMetas.value.get(jobId)

    if (meta?.type === 'exportify') {
      currentExportifyJob.value = job
      showExportifyModal.value = true
    } else if (meta?.type === 'import') {
      currentImportJob.value = job
      showImportModal.value = true
    }
  }

  /**
   * Cancel an ongoing job
   */
  const cancelJob = async (jobId) => {
    if (!jobId) return
    try {
      await ingestionApi.cancelJob(jobId)
      stopPolling(jobId)

      const job = jobs.value.get(jobId)
      if (job) {
        const nextJobs = new Map(jobs.value)
        nextJobs.set(jobId, { ...job, status: 'cancelled' })
        jobs.value = nextJobs
      }

      const nextMin = new Set(minimizedJobIds.value)
      nextMin.delete(jobId)
      minimizedJobIds.value = nextMin

      uiStore.toast?.info('Отменено', 'Импорт был отменен')
    } catch (err) {
      console.error('[TasksStore] Cancel job error:', err)
    }
  }

  /**
   * Modal opening shortcuts
   */
  const openExportifyModal = () => {
    showExportifyModal.value = true
  }

  const closeExportifyModal = () => {
    // If active job is in progress, minimize it instead of killing!
    if (currentExportifyJob.value && currentExportifyJob.value.status === 'in_progress') {
      minimizeJob(currentExportifyJob.value.id)
      return
    }
    showExportifyModal.value = false
    currentExportifyJob.value = null
  }

  const openImportModal = () => {
    showImportModal.value = true
  }

  const closeImportModal = () => {
    if (currentImportJob.value && currentImportJob.value.status === 'in_progress') {
      minimizeJob(currentImportJob.value.id)
      return
    }
    showImportModal.value = false
    currentImportJob.value = null
  }

  /**
   * List of all currently minimized active tasks
   */
  const activeMinimizedJobs = computed(() => {
    const list = []
    for (const jobId of minimizedJobIds.value) {
      const job = jobs.value.get(jobId)
      const meta = jobMetas.value.get(jobId)
      if (job) {
        list.push({ job, meta })
      }
    }
    return list
  })

  return {
    jobs,
    jobMetas,
    minimizedJobIds,
    showExportifyModal,
    showImportModal,
    currentExportifyJob,
    currentImportJob,
    activeMinimizedJobs,
    registerJob,
    minimizeJob,
    restoreJob,
    cancelJob,
    openExportifyModal,
    closeExportifyModal,
    openImportModal,
    closeImportModal,
  }
})
