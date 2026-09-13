<template>
  <div class="grid-skeleton" :class="`type-${type}`">
    <div class="skeleton-image" :class="{ circular: type === 'artist' }" />
    <div class="skeleton-content">
      <div class="skeleton-title" />
      <div class="skeleton-subtitle" />
      <div class="skeleton-extra" v-if="type === 'album'" />
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
  min-width: 0;
}

.skeleton-image {
  aspect-ratio: 1;
  width: 100%;
  border-radius: var(--r-md, 8px);
  background: var(--c-bg-3, #242424);
  box-shadow: 
    4px 4px 8px var(--sh-dark, rgba(0, 0, 0, 0.4)),
    -2px -2px 4px var(--sh-light, rgba(255, 255, 255, 0.03));
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-image.circular {
  border-radius: 50%;
}

.skeleton-content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* ─── Type-specific exact content heights ─── */

/* Artist: exactly 32px content + 8px gap = 40px */
.grid-skeleton.type-artist .skeleton-content {
  gap: 2px;
  align-items: center;
}

.grid-skeleton.type-artist .skeleton-title {
  height: 16px;
  width: 75%;
  background: var(--c-bg-3, #242424);
  border-radius: 4px;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.1s;
}

.grid-skeleton.type-artist .skeleton-subtitle {
  height: 14px;
  width: 55%;
  background: var(--c-bg-3, #242424);
  border-radius: 4px;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.2s;
}

/* Album: exactly 48px content + 8px gap = 56px */
.grid-skeleton.type-album .skeleton-content {
  gap: 2px;
}

.grid-skeleton.type-album .skeleton-title {
  height: 16px;
  width: 85%;
  background: var(--c-bg-3, #242424);
  border-radius: 4px;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.1s;
}

.grid-skeleton.type-album .skeleton-subtitle {
  height: 14px;
  width: 60%;
  background: var(--c-bg-3, #242424);
  border-radius: 4px;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.2s;
}

.grid-skeleton.type-album .skeleton-extra {
  height: 14px;
  width: 40%;
  background: var(--c-bg-3, #242424);
  border-radius: 4px;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.3s;
}

/* Playlist: exactly 37px content + 8px gap = 45px */
.grid-skeleton.type-playlist .skeleton-content {
  gap: 4px;
}

.grid-skeleton.type-playlist .skeleton-title {
  height: 18px;
  width: 80%;
  background: var(--c-bg-3, #242424);
  border-radius: 4px;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.1s;
}

.grid-skeleton.type-playlist .skeleton-subtitle {
  height: 15px;
  width: 45%;
  background: var(--c-bg-3, #242424);
  border-radius: 4px;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.2s;
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
