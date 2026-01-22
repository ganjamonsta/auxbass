<template>
  <div 
    v-if="hasWork" 
    class="enrichment-status flex items-center gap-2 px-3 py-1.5 bg-white/10 rounded-full text-xs"
  >
    <div class="relative w-4 h-4">
      <svg 
        class="animate-spin text-blue-400" 
        viewBox="0 0 24 24" 
        fill="none"
      >
        <circle 
          class="opacity-25" 
          cx="12" cy="12" r="10" 
          stroke="currentColor" 
          stroke-width="3"
        />
        <path 
          class="opacity-75" 
          fill="currentColor" 
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>
    <span class="text-white/70">
      Обогащение: {{ status.completed }}/{{ status.total }}
    </span>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useLibraryStore } from '@/stores/library'

const library = useLibraryStore()

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
    const res = await fetch('/api/library/enrichment/status', {
      headers: library.authHeaders
    })
    if (res.ok) {
      status.value = await res.json()
    }
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
  backdrop-filter: blur(10px);
}
</style>
