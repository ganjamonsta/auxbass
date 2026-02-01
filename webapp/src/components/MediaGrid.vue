<template>
  <div class="media-section">
    <div v-if="title" class="section-header">
      <h2>{{ title }}</h2>
      <slot name="actions"></slot>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
    </div>

    <!-- Empty State -->
    <div v-else-if="(!items || items.length === 0) && !$slots['prepend-grid']" class="empty-state">
      <slot name="empty">
        <p>Нет элементов</p>
      </slot>
    </div>

    <!-- Grid -->
    <div v-else class="media-grid" :class="`type-${type}`">
      <slot name="prepend-grid"></slot>
      <component
        :is="getComponent(type)"
        v-for="item in items"
        :key="getKey(item)"
        :[type]="item"
        @click="handleItemClick(item)"
        @play="handleItemPlay(item)"
        @contextmenu.prevent="(e) => $emit('contextmenu', { item, type, event: e })"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AlbumGridCard from './AlbumGridCard.vue'
import ArtistGridCard from './ArtistGridCard.vue'
import PlaylistGridCard from './PlaylistGridCard.vue'

const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    required: true,
    validator: (value) => ['artist', 'album', 'playlist'].includes(value)
  },
  items: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click', 'play', 'contextmenu'])

const getComponent = (type) => {
  switch (type) {
    case 'artist': return ArtistGridCard
    case 'album': return AlbumGridCard
    case 'playlist': return PlaylistGridCard
    default: return null
  }
}

const getKey = (item) => {
  return item.id || item.name // Artists usually have unique names in this app
}

const handleItemClick = (item) => {
  emit('click', item)
}

const handleItemPlay = (item) => {
  emit('play', item)
}
</script>

<style scoped>
.media-section {
  width: 100%;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h2 {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
}

.media-grid {
  display: grid;
  gap: 24px;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
}

.media-grid.type-artist {
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); /* Artists are smaller/circles */
  gap: 24px; 
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .media-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 16px;
  }
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 40px;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top-color: var(--accent);
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}
</style>
