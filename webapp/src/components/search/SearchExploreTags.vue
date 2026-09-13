<template>
  <div class="search-explore-container">
    <div class="explore-header">
      <div class="explore-title-row">
        <div class="title-with-icon">
          <Hash :size="20" class="explore-icon" />
          <h2 class="explore-heading">Обзор по тегам</h2>
        </div>
        <!-- Scope switcher -->
        <div class="tag-scope-tabs">
          <button 
            class="scope-tab" 
            :class="{ active: tagScope === 'library' }"
            @click="$emit('switchScope', 'library')"
          >
            Мои теги
          </button>
          <button 
            class="scope-tab" 
            :class="{ active: tagScope === 'global' }"
            @click="$emit('switchScope', 'global')"
          >
            Все теги
          </button>
        </div>
      </div>
      <p class="explore-subheading">Нажмите на любой тег, чтобы открыть подборку музыки</p>
    </div>

    <!-- Loading tags skeleton -->
    <div v-if="loadingTags && tags.length === 0" class="tags-loading-grid">
      <div v-for="n in 8" :key="n" class="tag-tile-skeleton">
        <div class="skeleton-tag-title"></div>
        <div class="skeleton-tag-count"></div>
      </div>
    </div>

    <!-- Tags Grid -->
    <div v-else class="tags-grid">
      <div 
        v-for="tag in displayTags" 
        :key="tag.name"
        class="tag-tile"
        :style="{ background: getTagGradient(tag.name) }"
        @click="$emit('tagClick', tag.name)"
      >
        <div class="tag-info">
          <span class="tag-name">#{{ tag.name }}</span>
          <span v-if="tag.track_count > 0" class="tag-count">
            {{ tag.track_count }} {{ formatTrackCount(tag.track_count) }}
          </span>
        </div>

        <!-- Decorative Hash watermark -->
        <div class="tag-watermark">
          <Hash :size="48" stroke-width="2.5" />
        </div>

        <!-- Quick play mix button -->
        <button 
          v-if="tag.track_count > 0"
          class="tag-play-btn"
          @click.stop="$emit('playTagMix', tag.name)"
          title="Слушать микс по тегу"
        >
          <Play :size="16" fill="currentColor" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Hash, Play } from 'lucide-vue-next'

const props = defineProps({
  tagScope: {
    type: String,
    required: true
  },
  loadingTags: {
    type: Boolean,
    default: false
  },
  tags: {
    type: Array,
    required: true
  },
  displayTags: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['switchScope', 'tagClick', 'playTagMix'])

const formatTrackCount = (count) => {
  if (!count) return 'треков'
  const num = count % 100
  if (num >= 11 && num <= 19) return 'треков'
  const last = num % 10
  if (last === 1) return 'трек'
  if (last >= 2 && last <= 4) return 'трека'
  return 'треков'
}

// Visual generator for tag backgrounds
const getTagGradient = (tagName) => {
  let hash = 0
  for (let i = 0; i < tagName.length; i++) {
    hash = tagName.charCodeAt(i) + ((hash << 5) - hash)
  }
  const h = Math.abs(hash) % 360
  // Generate a vibrant but soft gradient using HSL
  return `linear-gradient(135deg, hsl(${h}, 70%, 55%), hsl(${(h + 40) % 360}, 80%, 45%))`
}
</script>

<style scoped>
/* Explore: Tags Header */
.explore-header {
  margin-bottom: 16px;
}

.explore-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.explore-icon {
  color: var(--c-accent, #1db954);
}

.explore-heading {
  font-size: 20px;
  font-weight: 800;
  color: var(--c-text-1, #fff);
  margin: 0;
  letter-spacing: -0.01em;
}

.explore-subheading {
  font-size: 13px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  margin-top: 4px;
}

/* Scope tabs */
.tag-scope-tabs {
  display: flex;
  background: rgba(255, 255, 255, 0.08);
  padding: 3px;
  border-radius: 12px;
  gap: 2px;
}

.scope-tab {
  background: transparent;
  border: none;
  color: var(--c-text-3, rgba(255, 255, 255, 0.6));
  font-size: 12px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 9px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.scope-tab.active {
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
}

/* Tags Grid */
.tags-grid, .tags-loading-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

@media (min-width: 640px) {
  .tags-grid, .tags-loading-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }
}

@media (min-width: 1024px) {
  .tags-grid, .tags-loading-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
  }
}

.tag-tile {
  height: 96px;
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  user-select: none;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.tag-tile:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
}

.tag-tile:active {
  transform: scale(0.97);
}

.tag-info {
  display: flex;
  flex-direction: column;
  z-index: 1;
}

.tag-name {
  font-size: 16px;
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
}

.tag-count {
  font-size: 11px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.75);
  margin-top: 3px;
}

.tag-watermark {
  position: absolute;
  right: -8px;
  bottom: -8px;
  opacity: 0.18;
  transform: rotate(-15deg);
  color: #fff;
  pointer-events: none;
}

.tag-play-btn {
  position: absolute;
  right: 10px;
  bottom: 10px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transform: scale(0.85);
  transition: all 0.2s ease;
  z-index: 2;
  backdrop-filter: blur(4px);
}

.tag-tile:hover .tag-play-btn {
  opacity: 1;
  transform: scale(1);
}

.tag-play-btn:hover {
  background: var(--c-accent, #1db954);
  color: #000;
  border-color: transparent;
  transform: scale(1.1) !important;
}

/* Loading skeletons */
.tag-tile-skeleton {
  height: 96px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  padding: 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-sizing: border-box;
}

.skeleton-tag-title {
  height: 16px;
  width: 60%;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-tag-count {
  height: 10px;
  width: 35%;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.05);
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.15s;
}

@keyframes pulse {
  0%, 100% { opacity: 0.35; }
  50% { opacity: 0.75; }
}
</style>
