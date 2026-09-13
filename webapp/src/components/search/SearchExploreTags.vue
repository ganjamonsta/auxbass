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
