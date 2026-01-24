<template>
  <div 
    v-if="hasWork" 
    class="enrichment-status"
  >
    <div class="spinner-wrap">
      <svg 
        class="spinner" 
        viewBox="0 0 24 24" 
        fill="none"
      >
        <circle 
          class="spinner-bg" 
          cx="12" cy="12" r="10" 
          stroke="currentColor" 
          stroke-width="3"
        />
        <path 
          class="spinner-fill" 
          fill="currentColor" 
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>
    <span class="status-text">
      Обогащение: {{ status.completed }}/{{ status.total }}
    </span>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { tracksApi } from '@/api/client'

const status = ref({
  pending: 0,
  processing: 0,
  completed: 0,
  failed: 0,
  total: 0,
  progress: 100
})

const hasWork = computed(() => {
  return status.value.pending > 0 || status.value.processing > 0
})

let intervalId = null

async function fetchStatus() {
  try {
    const res = await tracksApi.getEnrichmentStatus()
    status.value = res.data
  } catch (e) {
    console.error('Failed to fetch enrichment status:', e)
  }
}

onMounted(() => {
  fetchStatus()
  // Poll every 30 seconds
  intervalId = setInterval(fetchStatus, 30000)
})

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

<style scoped>
.enrichment-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  background: var(--xm-bg-elevated, #1A1A1A);
  border-radius: var(--neu-radius-full, 9999px);
  font-size: 12px;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -2px -2px 4px var(--neu-shadow-light, rgba(255, 255, 255, 0.03));
  backdrop-filter: blur(10px);
}

.spinner-wrap {
  position: relative;
  width: 18px;
  height: 18px;
}

.spinner {
  width: 100%;
  height: 100%;
  animation: spin 1s linear infinite;
  color: var(--xm-secondary, #00BCD4);
}

.spinner-bg {
  opacity: 0.2;
}

.spinner-fill {
  opacity: 0.9;
}

.status-text {
  color: var(--xm-text-secondary, #ccc);
  font-weight: 500;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
