<template>
  <div class="grid-skeleton" :class="`type-${type}`">
    <div class="skeleton-image" :class="{ circular: type === 'artist' }" />
    <div class="skeleton-content">
      <div class="skeleton-title" />
      <div class="skeleton-subtitle" v-if="type !== 'artist'" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: 'album',
    validator: v => ['artist', 'album', 'playlist'].includes(v)
  }
})
</script>

<style scoped>
.grid-skeleton {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-image {
  aspect-ratio: 1;
  width: 100%;
  border-radius: var(--neu-radius-md, 12px);
  background: var(--xm-bg-surface, #222);
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -1px -1px 2px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-image.circular {
  border-radius: 50%;
}

.skeleton-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 0 4px;
}

.skeleton-title {
  height: 14px;
  background: var(--xm-bg-surface, #222);
  border-radius: 4px;
  width: 80%;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.1s;
}

.skeleton-subtitle {
  height: 12px;
  background: var(--xm-bg-surface, #222);
  border-radius: 4px;
  width: 50%;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.2s;
}

/* Type-specific styles */
.grid-skeleton.type-artist .skeleton-content {
  align-items: center;
  text-align: center;
}

.grid-skeleton.type-artist .skeleton-title {
  width: 70%;
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
