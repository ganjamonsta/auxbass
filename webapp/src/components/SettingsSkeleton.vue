<template>
  <div class="settings-skeleton">
    <!-- Title skeleton -->
    <div class="skeleton-title-main" />

    <!-- Channel section skeleton -->
    <section class="skeleton-section">
      <div class="skeleton-section-title" />
      <div class="skeleton-channel-box">
        <div class="skeleton-channel-header">
          <div class="skeleton-channel-icon" />
          <div class="skeleton-channel-info">
            <div class="skeleton-line medium" />
            <div class="skeleton-line short" />
          </div>
        </div>
        <div class="skeleton-features">
          <div class="skeleton-feature-item" />
          <div class="skeleton-feature-item" />
          <div class="skeleton-feature-item" />
        </div>
      </div>
    </section>

    <!-- User section skeleton -->
    <section class="skeleton-section">
      <div class="skeleton-section-title" />
      <div class="skeleton-user-info">
        <div class="skeleton-avatar" />
        <div class="skeleton-user-details">
          <div class="skeleton-line medium" />
          <div class="skeleton-line short" />
        </div>
      </div>
      <div class="skeleton-button" />
    </section>

    <!-- Library stats skeleton -->
    <section class="skeleton-section">
      <div class="skeleton-section-title" />
      <div class="skeleton-stats-grid">
        <div class="skeleton-stat-item">
          <div class="skeleton-stat-value" />
          <div class="skeleton-stat-label" />
        </div>
        <div class="skeleton-stat-item">
          <div class="skeleton-stat-value" />
          <div class="skeleton-stat-label" />
        </div>
        <div class="skeleton-stat-item">
          <div class="skeleton-stat-value" />
          <div class="skeleton-stat-label" />
        </div>
        <div class="skeleton-stat-item">
          <div class="skeleton-stat-value" />
          <div class="skeleton-stat-label" />
        </div>
      </div>
    </section>

    <!-- Privacy section skeleton -->
    <section class="skeleton-section">
      <div class="skeleton-section-title" />
      <div class="skeleton-setting-row">
        <div class="skeleton-setting-info">
          <div class="skeleton-line medium" />
          <div class="skeleton-line long" />
        </div>
        <div class="skeleton-toggle" />
      </div>
      <div class="skeleton-setting-row">
        <div class="skeleton-setting-info">
          <div class="skeleton-line medium" />
          <div class="skeleton-line long" />
        </div>
        <div class="skeleton-toggle" />
      </div>
    </section>

    <!-- Notifications section skeleton -->
    <section class="skeleton-section">
      <div class="skeleton-section-title" />
      <div class="skeleton-setting-row">
        <div class="skeleton-setting-info">
          <div class="skeleton-line medium" />
          <div class="skeleton-line long" />
        </div>
        <div class="skeleton-toggle" />
      </div>
    </section>

    <!-- Interface section skeleton -->
    <section class="skeleton-section">
      <div class="skeleton-section-title" />
      <div class="skeleton-setting-row">
        <div class="skeleton-setting-info">
          <div class="skeleton-line short" />
          <div class="skeleton-line tiny" />
        </div>
        <div class="skeleton-slider" />
      </div>
    </section>
  </div>
</template>

<script setup>
// Visual skeleton, no logic needed
</script>

<style scoped>
.settings-skeleton {
  padding: 16px;
}

/* Animation */
@keyframes pulse {
  0%, 100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.7;
  }
}

/* Base skeleton styles */
.skeleton-title-main {
  height: 32px;
  width: 140px;
  background: var(--c-bg-3);
  border-radius: 8px;
  margin-bottom: 24px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-section {
  margin-bottom: 32px;
}

.skeleton-section-title {
  height: 14px;
  width: 100px;
  background: var(--c-bg-3);
  border-radius: 6px;
  margin-bottom: 16px;
  animation: pulse 1.5s ease-in-out infinite;
}

/* Channel skeleton */
.skeleton-channel-box {
  background: var(--c-bg-2);
  border-radius: 12px;
  padding: 16px;
}

.skeleton-channel-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.skeleton-channel-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--c-bg-3);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-channel-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-features {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-feature-item {
  height: 16px;
  width: 60%;
  background: var(--c-bg-3);
  border-radius: 6px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-feature-item:nth-child(2) {
  width: 55%;
  animation-delay: 0.1s;
}

.skeleton-feature-item:nth-child(3) {
  width: 50%;
  animation-delay: 0.2s;
}

/* User skeleton */
.skeleton-user-info {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.skeleton-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--c-bg-3);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-user-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-button {
  height: 44px;
  width: 100%;
  background: var(--c-bg-3);
  border-radius: 10px;
  animation: pulse 1.5s ease-in-out infinite;
}

/* Stats grid skeleton */
.skeleton-stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.skeleton-stat-item {
  background: var(--c-bg-2);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.skeleton-stat-value {
  height: 28px;
  width: 50px;
  background: var(--c-bg-3);
  border-radius: 6px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-stat-label {
  height: 12px;
  width: 60px;
  background: var(--c-bg-3);
  border-radius: 4px;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.1s;
}

/* Settings row skeleton */
.skeleton-setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--c-bg-4));
}

.skeleton-setting-row:last-child {
  border-bottom: none;
}

.skeleton-setting-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.skeleton-toggle {
  width: 44px;
  height: 24px;
  background: var(--c-bg-3);
  border-radius: 12px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-slider {
  width: 100%;
  height: 6px;
  background: var(--c-bg-3);
  border-radius: 3px;
  margin-top: 8px;
  animation: pulse 1.5s ease-in-out infinite;
}

/* Line sizes */
.skeleton-line {
  height: 14px;
  background: var(--c-bg-3);
  border-radius: 6px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-line.tiny {
  width: 40px;
  height: 12px;
}

.skeleton-line.short {
  width: 80px;
}

.skeleton-line.medium {
  width: 140px;
}

.skeleton-line.long {
  width: 85%;
  height: 12px;
  animation-delay: 0.1s;
}
</style>
