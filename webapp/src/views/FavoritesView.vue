<template>
  <div class="favorites-view">
    <div class="view-header">
      <h1>Любимое</h1>
    </div>

    <!-- Liked Tracks Section -->
    <div class="likes-section">
      <div class="liked-card" @click="goToLikedTracks">
        <div class="liked-content">
          <div class="liked-icon-box">
            <Heart :size="32" fill="currentColor" />
          </div>
          <div class="liked-info">
            <h3>Понравившиеся треки</h3>
            <p>{{ likedCount }} треков</p>
          </div>
        </div>
        <div class="play-action" @click.stop="playLikedTracks">
           <Play :size="24" fill="currentColor" />
        </div>
      </div>
    </div>

    <!-- Added Playlists (Foreign) -->
    <MediaGrid
      type="playlist"
      title="Добавленные плейлисты"
      :items="addedPlaylists"
      :loading="loading"
      @click="goToPlaylist"
      @contextmenu="handleContextMenu"
    >
      <template #empty>
        <p>Вы еще не добавили чужие плейлисты</p>
      </template>
    </MediaGrid>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { usePlayerStore } from '@/stores/player'
import { useContextMenu } from '@/composables/useContextMenu'
import api from '@/api/client'
import MediaGrid from '@/components/MediaGrid.vue'
import { Heart, Play } from 'lucide-vue-next'

const router = useRouter()
const libraryStore = useLibraryStore()
const playerStore = usePlayerStore()
const { openMenu } = useContextMenu()

const allPlaylists = ref([])
const loading = ref(false)

const likedCount = computed(() => libraryStore.likedTracks?.length || 0)

const addedPlaylists = computed(() => {
  return allPlaylists.value.filter(p => !p.is_owner)
})

const fetchPlaylists = async () => {
  loading.value = true
  try {
    const response = await api.get('/playlists')
    allPlaylists.value = response.data.items || response.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const goToLikedTracks = () => {
  router.push('/liked')
}

const playLikedTracks = async () => {
  if (libraryStore.likedTracks?.length) {
    playerStore.playTracks(libraryStore.likedTracks)
  }
}

const goToPlaylist = (playlist) => {
  router.push(`/playlist/${playlist.id}`)
}

const handleContextMenu = ({ item, type, event }) => {
  openMenu(type, item, 'library', event)
}

onMounted(() => {
  libraryStore.fetchLikedTracks()
  fetchPlaylists()
})
</script>

<style scoped>
.favorites-view {
  padding: 24px;
  padding-bottom: 120px;
}

.view-header {
  margin-bottom: 32px;
}

.view-header h1 {
  font-size: 32px;
  font-weight: 800;
  margin: 0;
}

.likes-section {
  margin-bottom: 40px;
}

.liked-card {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: transform 0.2s;
  box-shadow: 0 8px 16px rgba(0,0,0,0.2);
}

.liked-card:hover {
  transform: scale(1.01);
}

.liked-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.liked-icon-box {
  width: 64px;
  height: 64px;
  background: rgba(255,255,255,0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.liked-info h3 {
  margin: 0 0 4px 0;
  color: white;
  font-size: 20px;
}

.liked-info p {
  margin: 0;
  color: rgba(255,255,255,0.8);
}

.play-action {
  width: 48px;
  height: 48px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
  opacity: 0;
  transform: translateX(10px);
  transition: all 0.3s ease;
}

.liked-card:hover .play-action {
  opacity: 1;
  transform: translateX(0);
}
</style>
