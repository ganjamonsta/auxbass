<template>
  <div
    class="playlist-card"
    @click="$emit('click', playlist)"
    @contextmenu.prevent="$emit('contextmenu', $event)"
  >
    <div class="playlist-cover">
      <div class="cover-grid" :class="{ 'single-cover': playlist.covers?.length === 1 }" v-if="playlist.covers?.length">
        <img
          v-for="(cover, i) in playlist.covers.slice(0, 4)"
          :key="i"
          :src="cover"
        />
      </div>
      <div v-else class="cover-placeholder"><Music :size="24" /></div>
      
      <!-- Play button -->
      <button class="play-btn" @click.stop="$emit('play', playlist)"><Play :size="20" fill="currentColor" /></button>
      
      <!-- Owner badge for created playlists -->
      <div v-if="playlist.is_owner" class="owner-badge creator-badge">
        <Crown :size="12" /> Ваш
      </div>
      
      <!-- Subscribed badge for added playlists -->
      <div v-else-if="playlist.is_subscribed" class="owner-badge subscribed-badge">
        <UserPlus :size="12" /> {{ playlist.owner_name || 'Добавлен' }}
      </div>
    </div>
    
    <div class="playlist-info">
      <div class="playlist-name">{{ playlist.name }}</div>
      <div class="playlist-meta">
        {{ playlist.track_count }} треков
        <span v-if="playlist.is_public" class="public-badge">
          <Globe :size="12" />
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Music, Globe, Crown, UserPlus, Play } from 'lucide-vue-next'

defineProps({
  playlist: {
    type: Object,
    required: true
  }
})

defineEmits(['click', 'play', 'contextmenu'])
</script>

<style scoped>
.playlist-card {
  cursor: pointer;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.playlist-cover {
  width: 100%;
  aspect-ratio: 1;
  background: var(--bg-elevated);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 8px;
  position: relative;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.cover-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  width: 100%;
  height: 100%;
}

.cover-grid.single-cover {
  display: block;
}

.cover-grid img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: var(--text-secondary);
}

.playlist-info {
  min-width: 0;
}

.playlist-name {
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.playlist-meta {
  font-size: 12px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.public-badge {
  display: flex;
  color: var(--text-secondary);
}

.owner-badge {
  position: absolute;
  bottom: 0px;
  right: 0px;
  background: rgba(0,0,0,0.75);
  color: white;
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  border-top-left-radius: 6px;
  display: flex;
  align-items: center;
  gap: 3px;
  backdrop-filter: blur(4px);
}

.creator-badge {
  background: rgba(255, 215, 0, 0.9);
  color: #000;
}

.subscribed-badge {
  background: rgba(59, 130, 246, 0.9);
  color: #fff;
}

.play-btn {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent);
  border: none;
  color: #000;
  font-size: 14px;
  cursor: pointer;
  opacity: 0;
  transform: translateY(8px);
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.playlist-card:hover .play-btn {
  opacity: 1;
  transform: translateY(0);
}

/* Hide play button on mobile devices */
@media (max-width: 768px) {
  .play-btn {
    display: none;
  }
}
</style>
