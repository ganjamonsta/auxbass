<template>
  <div class="track-list">
    <!-- Skeleton on initial load -->
    <div v-if="loading && tracks.length === 0" class="skeleton-list">
      <TrackSkeleton v-for="i in 6" :key="i" />
    </div>
    
    <!-- Empty state -->
    <div v-else-if="tracks.length === 0" class="empty">
      <div class="empty-icon">🎵</div>
      <p class="empty-title">{{ isGlobal ? 'Треки не найдены' : 'Библиотека пуста' }}</p>
      <p class="empty-hint">{{ isGlobal ? 'Попробуйте другого артиста' : 'Отправь аудиофайлы боту, чтобы добавить музыку' }}</p>
    </div>
    
    <!-- Track list -->
    <template v-else>
      <TrackItem 
        v-for="track in tracks" 
        :key="track.id"
        :track="track"
        :isPlaying="currentTrackId === track.id && isPlaying"
        :isLiked="isTrackLiked(track.id)"
        @click="$emit('play', track, tracks)"
        @menu="$emit('menu', track)"
        @like="$emit('like', track.id)"
      />
      
      <!-- Load more button -->
      <button 
        v-if="hasMore && !loading" 
        class="load-more-btn"
        :disabled="loading"
        @click="$emit('loadMore')"
      >
        Загрузить ещё
      </button>
      
      <!-- Loading indicator -->
      <div v-if="loading" class="loading-more">
        <div class="loading-spinner"></div>
        <span>Загрузка...</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import TrackItem from './TrackItem.vue'
import TrackSkeleton from './TrackSkeleton.vue'

defineProps({
  tracks: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  hasMore: { type: Boolean, default: false },
  isGlobal: { type: Boolean, default: false },
  currentTrackId: { type: [Number, String], default: null },
  isPlaying: { type: Boolean, default: false },
  isTrackLiked: { type: Function, required: true },
})

defineEmits(['play', 'menu', 'like', 'loadMore'])
</script>
