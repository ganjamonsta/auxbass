<template>
  <div class="track-skeleton">
    <!-- Cover placeholder -->
    <div class="skeleton-cover" />
    
    <!-- Text placeholders -->
    <div class="skeleton-content">
      <div class="skeleton-title" />
      <div class="skeleton-subtitle" />
    </div>
    
    <!-- Duration placeholder -->
    <div class="skeleton-duration" />
  </div>
</template>

<script setup>
// Just a visual skeleton, no logic needed
</script>

<style scoped>
.track-skeleton {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: var(--neu-radius-md, 12px);
  background: var(--xm-bg-elevated, #1A1A1A);
}

.skeleton-cover {
  width: 52px;
  height: 52px;
  border-radius: var(--neu-radius-sm, 8px);
  background: var(--xm-bg-surface, #222);
  flex-shrink: 0;
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -1px -1px 2px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-title {
  height: 14px;
  background: var(--xm-bg-surface, #222);
  border-radius: var(--neu-radius-sm, 8px);
  width: 75%;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.1s;
}

.skeleton-subtitle {
  height: 12px;
  background: var(--xm-bg-surface, #222);
  border-radius: var(--neu-radius-sm, 8px);
  width: 50%;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.2s;
}

.skeleton-duration {
  width: 32px;
  height: 12px;
  background: var(--xm-bg-surface, #222);
  border-radius: var(--neu-radius-sm, 8px);
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.3s;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.8;
  }
}
</style>
