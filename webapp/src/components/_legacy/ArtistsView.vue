<template>
  <div class="list-section">
    <!-- Scope toggle -->
    <div class="scope-toggle">
      <button 
        :class="['scope-btn', { active: scope === 'library' }]"
        @click="$emit('changeScope', 'library')"
      >
        Моя библиотека
      </button>
      <button 
        :class="['scope-btn', { active: scope === 'global' }]"
        @click="$emit('changeScope', 'global')"
      >
        Вся музыка
      </button>
    </div>
    
    <!-- Empty state -->
    <div v-if="artists.length === 0" class="empty">
      <div class="empty-icon">👤</div>
      <p class="empty-title">Нет артистов</p>
    </div>
    
    <!-- Artist list -->
    <div
      v-for="artist in artists"
      :key="artist.artist"
      class="list-item"
      @click="$emit('filterArtist', artist.artist)"
    >
      <div class="list-item-avatar artist-avatar" :style="getArtistStyle(artist.artist)">
        <img 
          v-if="artistImages[artist.artist]" 
          :src="artistImages[artist.artist]" 
          alt=""
          class="avatar-image"
          @error="$event.target.style.display = 'none'"
        />
        <span v-else class="avatar-initials">{{ getArtistInitials(artist.artist) }}</span>
      </div>
      <div class="list-item-content">
        <span class="list-item-title">{{ artist.artist || 'Неизвестный' }}</span>
        <span class="list-item-subtitle">{{ artist.count }} треков</span>
      </div>
      <svg class="list-item-arrow" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
      </svg>
    </div>
  </div>
</template>

<script setup>
import { getArtistInitials, getArtistAvatarStyle } from '@/utils/styles'

const props = defineProps({
  artists: { type: Array, default: () => [] },
  artistImages: { type: Object, default: () => ({}) },
  scope: { type: String, default: 'library' },
})

defineEmits(['changeScope', 'filterArtist'])

const getArtistStyle = (name) => {
  return getArtistAvatarStyle(name, props.artistImages[name])
}
</script>
