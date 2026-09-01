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
  gap: 10px;
  padding: 8px 6px 8px 12px;
  margin: 0 0 0 8px;
  border-radius: var(--r-md);
  background: transparent;
  height: 64px;
  box-sizing: border-box;
}

.skeleton-cover {
  width: 48px;
  height: 48px;
  border-radius: var(--r-md);
  background: var(--c-bg-3);
  flex-shrink: 0;
  box-shadow: 
    4px 4px 8px var(--sh-dark),
    -2px -2px 4px var(--sh-light);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.skeleton-title {
  height: 14px;
  background: var(--c-bg-3);
  border-radius: 4px;
  width: 65%;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.1s;
}

.skeleton-subtitle {
  height: 12px;
  background: var(--c-bg-3);
  border-radius: 4px;
  width: 40%;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.2s;
}

.skeleton-duration {
  width: 36px;
  height: 12px;
  background: var(--c-bg-3);
  border-radius: 4px;
  margin-right: 8px;
  flex-shrink: 0;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.3s;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.35;
  }
  50% {
    opacity: 0.75;
  }
}
</style>
