<template>
  <div class="info-banner">
    <div class="banner-icon">
      <component :is="icon" :size="20" />
    </div>
    <div class="banner-text">
      <div class="banner-title">{{ title }}</div>
      <div class="banner-description">{{ description }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  icon: {
    type: [Object, Function],
    required: true
  },
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.info-banner {
  display: flex;
  align-items: start;
  gap: 12px;
  padding: 16px;
  background: var(--c-bg-2);
  border-radius: 12px;
  margin-bottom: 16px;
  border: 1px solid var(--c-bg-3);
}

.banner-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-accent);
  color: #000;
  border-radius: 10px;
}

.banner-text {
  flex: 1;
}

.banner-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text-1);
  margin-bottom: 4px;
}

.banner-description {
  font-size: 13px;
  color: var(--c-text-2);
  line-height: 1.4;
}

@media (max-width: 1023px) {
  .info-banner {
    padding: 12px;
    gap: 10px;
  }

  .banner-title {
    font-size: 14px;
    margin-bottom: 2px;
  }

  .banner-description {
    font-size: 12px;
  }
}
</style>
