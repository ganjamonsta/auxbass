<template>
  <div class="stats-module">
    <div class="module-header">
      <span class="module-label">STATISTICS</span>
    </div>
    <div class="stats-grid">
      <div class="stat-item">
        <span class="stat-label">BUFFER</span>
        <span class="stat-value">{{ bufferedPercent }}%</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">BITRATE</span>
        <span class="stat-value">{{ bitrate || '---' }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">PLAYS</span>
        <span class="stat-value">{{ playCount || 0 }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">MODE</span>
        <span class="stat-value">{{ playModeText }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  bufferedPercent: Number,
  bitrate: [String, Number],
  playCount: Number,
  playModeText: String
})
</script>

<style scoped>
.stats-module {
  background: #12121e;
  border-radius: 20px;
  padding: 18px;
  box-shadow: 
    6px 6px 12px #000000,
    -6px -6px 12px #1a1a28;
}

.module-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.module-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #db2220;
  font-family: 'Segoe UI', sans-serif;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background: #12121e;
  border-radius: 12px;
  box-shadow: 
    inset 3px 3px 6px #08080f,
    inset -3px -3px 6px #1a1a28;
}

.stat-label {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 1.2px;
  color: #e85c7c;
  font-family: 'Segoe UI', sans-serif;
}

.stat-value {
  font-size: 14px;
  font-weight: 700;
  color: #e8ecf1;
  font-family: 'Segoe UI', monospace;
}
</style>
