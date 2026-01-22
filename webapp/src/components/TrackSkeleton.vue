<template>
  <div class="track-skeleton animate-pulse flex items-center gap-3 p-3 rounded-xl">
    <!-- Cover placeholder -->
    <div class="w-12 h-12 bg-white/10 rounded-lg flex-shrink-0" />
    
    <!-- Text placeholders -->
    <div class="flex-1 min-w-0 space-y-2">
      <div class="h-4 bg-white/10 rounded w-3/4" />
      <div class="h-3 bg-white/10 rounded w-1/2" />
    </div>
    
    <!-- Duration placeholder -->
    <div class="h-3 bg-white/10 rounded w-8" />
  </div>
</template>

<script setup>
// Just a visual skeleton, no logic needed
</script>

<style scoped>
.track-skeleton {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.03) 0%,
    rgba(255, 255, 255, 0.05) 50%,
    rgba(255, 255, 255, 0.03) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
