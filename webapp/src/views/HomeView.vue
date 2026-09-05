<template>
  <div class="home-view">
    <!-- Header Greeting -->
    <header class="home-greeting">
      <h1 class="greeting-title">{{ greetingText }}</h1>
      <p class="greeting-subtitle" v-if="authStore.user">
        Рады видеть вас, {{ userFirstName }}!
      </p>
    </header>

    <!-- Top Quick-Access Grid (Spotify 2x3 / 3x2) -->
    <section class="quick-access-grid">
      <!-- Liked Songs Tile (Always First) -->
      <div class="quick-card liked-card" @click="goTo('/liked')">
        <div class="quick-card-cover liked-cover-gradient">
          <Heart :size="24" fill="currentColor" />
        </div>
        <div class="quick-card-info">
          <span class="quick-card-title">Понравившиеся</span>
          <span class="quick-card-meta">{{ likedCount }} треков</span>
        </div>
        <button 
          v-if="likedCount > 0" 
          class="quick-play-btn" 
          @click.stop="handlePlayLiked"
          title="Слушать любимые"
        >
          <Play :size="18" fill="currentColor" />
        </button>
      </div>

      <!-- User Top Playlists -->
      <div 
        v-for="playlist in topPlaylists" 
        :key="playlist.id"
        class="quick-card"
        @click="goTo(`/playlist/${playlist.id}`)"
      >
        <div class="quick-card-cover" :style="getPlaylistCoverStyle(playlist)">
          <img 
            v-if="playlist.covers?.length" 
            :src="getCoverUrl(playlist.covers[0], CoverSize.SMALL)" 
            alt="" 
            loading="lazy"
          />
          <Music v-else :size="22" />
        </div>
        <div class="quick-card-info">
          <span class="quick-card-title">{{ playlist.name }}</span>
          <span class="quick-card-meta">{{ playlist.track_count }} треков</span>
        </div>
        <button 
          v-if="playlist.track_count > 0" 
          class="quick-play-btn" 
          @click.stop="handlePlayPlaylist(playlist)"
          title="Слушать плейлист"
        >
          <Play :size="18" fill="currentColor" />
        </button>
      </div>

      <!-- Quick Add Playlist Tile if fewer than 5 playlists -->
      <div 
        v-if="topPlaylists.length < 5" 
        class="quick-card create-card" 
        @click="handleCreatePlaylist"
      >
        <div class="quick-card-cover create-cover">
          <Plus :size="24" />
        </div>
        <div class="quick-card-info">
          <span class="quick-card-title">Создать плейлист</span>
          <span class="quick-card-meta">Новая подборка</span>
        </div>
      </div>
    </section>

    <!-- Section: Недавно прослушано (History) -->
    <section v-if="recentHistoryTracks.length > 0" class="home-section">
      <div class="section-header">
        <h2 class="section-title">Недавно прослушано</h2>
      </div>
      <div class="horizontal-scroll">
        <div 
          v-for="track in recentHistoryTracks" 
          :key="track.id" 
          class="feed-card"
          @click="handlePlayTrack(track, recentHistoryTracks)"
          @contextmenu.prevent="openMenu('track', track, 'history', $event)"
        >
          <div class="feed-card-cover">
            <img 
              v-if="track.cover_url" 
              :src="getCoverUrl(track.cover_url, CoverSize.SMALL)" 
              alt=""
              loading="lazy"
            />
            <div v-else class="feed-card-placeholder">
              {{ track.title?.charAt(0) || '♪' }}
            </div>
            <button class="play-overlay" title="Слушать">
              <Play :size="18" fill="currentColor" />
            </button>
          </div>
          <div class="feed-card-title">{{ track.title }}</div>
          <div class="feed-card-subtitle">{{ track.artist || 'Неизвестен' }}</div>
        </div>
      </div>
    </section>

    <!-- Section: Ваши плейлисты -->
    <section v-if="allPlaylists.length > 0" class="home-section">
      <div class="section-header">
        <h2 class="section-title">Ваши плейлисты</h2>
        <button class="section-link" @click="goToLibraryPlaylists">Все</button>
      </div>
      <div class="horizontal-scroll">
        <div 
          v-for="pl in allPlaylists.slice(0, 10)" 
          :key="pl.id" 
          class="feed-card"
          @click="goTo(`/playlist/${pl.id}`)"
          @contextmenu.prevent="openMenu('playlist', pl, 'home', $event)"
        >
          <div class="feed-card-cover" :style="getPlaylistCoverStyle(pl)">
            <img 
              v-if="pl.covers?.length" 
              :src="getCoverUrl(pl.covers[0], CoverSize.SMALL)" 
              alt=""
              loading="lazy"
            />
            <Music v-else :size="32" />
            <button 
              v-if="pl.track_count > 0" 
              class="play-overlay" 
              @click.stop="handlePlayPlaylist(pl)"
              title="Слушать"
            >
              <Play :size="18" fill="currentColor" />
            </button>
          </div>
          <div class="feed-card-title">{{ pl.name }}</div>
          <div class="feed-card-subtitle">{{ pl.track_count }} треков</div>
        </div>
      </div>
    </section>

    <!-- Section: Свежее в сообществе (Recent Uploads) -->
    <section v-if="recentUploads.length > 0" class="home-section">
      <div class="section-header">
        <h2 class="section-title">Новинки сообщества</h2>
      </div>
      <div class="horizontal-scroll">
        <div 
          v-for="track in recentUploads.slice(0, 12)" 
          :key="track.id" 
          class="feed-card"
          @click="handlePlayTrack(track, recentUploads)"
          @contextmenu.prevent="openMenu('track', track, 'recent_uploads', $event)"
        >
          <div class="feed-card-cover">
            <img 
              v-if="track.cover_url" 
              :src="getCoverUrl(track.cover_url, CoverSize.SMALL)" 
              alt=""
              loading="lazy"
            />
            <div v-else class="feed-card-placeholder">
              {{ track.title?.charAt(0) || '♪' }}
            </div>
            <button class="play-overlay" title="Слушать">
              <Play :size="18" fill="currentColor" />
            </button>
          </div>
          <div class="feed-card-title">{{ track.title }}</div>
          <div class="feed-card-subtitle">{{ track.artist || 'Неизвестен' }}</div>
        </div>
      </div>
    </section>

    <!-- Section: Рекомендации (Spotify Discovery Placeholder) -->
    <section class="home-section">
      <div class="discovery-banner">
        <div class="discovery-badge">
          <Sparkles :size="16" />
          <span>Персональная волна</span>
        </div>
        <h3 class="discovery-title">Умные рекомендации на основе вашего вкуса</h3>
        <p class="discovery-text">
          Слушайте треки, ставьте лайки и сохраняйте альбомы. Скоро здесь появится автоматически сгенерированная лента новинок под ваши предпочтения.
        </p>
        <button class="discovery-btn" @click="handleRandomMix">
          <Shuffle :size="16" />
          <span>Включить случайный микс</span>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useLibraryStore } from '@/stores/library'
import { usePlayerStore } from '@/stores/player'
import { useUIStore } from '@/stores/ui'
import { useContextMenu } from '@/composables/useContextMenu'
import { getCoverUrl, CoverSize } from '@/utils'
import { 
  Heart, 
  Play, 
  Plus, 
  Music, 
  Sparkles, 
  Shuffle 
} from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()
const libraryStore = useLibraryStore()
const playerStore = usePlayerStore()
const uiStore = useUIStore()
const { openMenu } = useContextMenu()

// Greeting by time of day
const greetingText = computed(() => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 12) return 'Доброе утро'
  if (hour >= 12 && hour < 18) return 'Добрый день'
  if (hour >= 18 && hour < 23) return 'Добрый вечер'
  return 'Доброй ночи'
})

const userFirstName = computed(() => {
  const u = authStore.user
  if (!u) return ''
  return u.first_name || u.username || ''
})

const likedCount = computed(() => libraryStore.likedTracks?.length || 0)
const allPlaylists = computed(() => libraryStore.playlists || [])
const topPlaylists = computed(() => allPlaylists.value.slice(0, 5))
const recentHistoryTracks = computed(() => libraryStore.history || [])
const recentUploads = computed(() => libraryStore.recentUploads || [])

const goTo = (path) => {
  router.push(path)
}

const goToLibraryPlaylists = () => {
  uiStore.setLibraryTab('playlists')
  router.push('/library')
}

const handlePlayLiked = async () => {
  if (libraryStore.likedTracks?.length > 0) {
    playerStore.playTrack(libraryStore.likedTracks[0], libraryStore.likedTracks, 0)
  }
}

const handlePlayPlaylist = async (playlist) => {
  try {
    await playerStore.playShuffleAll('playlist', playlist.id)
  } catch (e) {
    console.error('Failed to play playlist:', e)
  }
}

const handlePlayTrack = (track, list) => {
  const idx = list.findIndex(t => t.id === track.id)
  playerStore.playTrack(track, list, idx >= 0 ? idx : 0)
}

const handleRandomMix = async () => {
  try {
    await playerStore.playShuffleAll('library')
  } catch (e) {
    console.error('Failed to start random mix:', e)
  }
}

const handleCreatePlaylist = async () => {
  if (!authStore.hasChannel) {
    authStore.promptChannelSetup()
    return
  }
  const name = prompt('Название нового плейлиста:')
  if (!name || !name.trim()) return
  const pl = await libraryStore.createPlaylist(name.trim())
  if (pl?.id) {
    router.push(`/playlist/${pl.id}`)
  }
}

const getPlaylistCoverStyle = (playlist) => {
  if (playlist.covers?.length) return {}
  const str = playlist.name || 'Playlist'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash % 360)
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 55%, 35%) 0%, hsl(${(hue + 40) % 360}, 45%, 25%) 100%)`
  }
}

onMounted(async () => {
  // Ensure background data is loaded for home page
  if (!libraryStore.playlists?.length) {
    libraryStore.fetchPlaylists()
  }
  if (!libraryStore.likedTracks?.length) {
    libraryStore.fetchLikedTracks()
  }
  if (!libraryStore.history?.length) {
    libraryStore.fetchHistory(20)
  }
  if (!libraryStore.recentUploads?.length) {
    libraryStore.fetchRecentUploads(15)
  }
})
</script>

<style scoped>
.home-view {
  padding: 16px 16px 32px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Greeting */
.home-greeting {
  margin-bottom: 20px;
}

.greeting-title {
  font-size: 26px;
  font-weight: 800;
  color: var(--c-text-1, #fff);
  letter-spacing: -0.02em;
  margin: 0;
}

.greeting-subtitle {
  font-size: 14px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  margin-top: 4px;
}

/* Quick Access Grid (Spotify style) */
.quick-access-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 28px;
}

@media (min-width: 768px) {
  .quick-access-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }
}

.quick-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  overflow: hidden;
  height: 56px;
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
  user-select: none;
  backdrop-filter: blur(8px);
}

.quick-card:hover {
  background: rgba(255, 255, 255, 0.13);
  transform: translateY(-1px);
}

.quick-card:active {
  transform: scale(0.98);
}

.quick-card-cover {
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-bg-3, #222);
  color: rgba(255, 255, 255, 0.7);
  overflow: hidden;
}

.quick-card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.liked-cover-gradient {
  background: linear-gradient(135deg, #450af5 0%, #8b5cf6 50%, #c084fc 100%);
  color: #fff;
  box-shadow: inset 0 0 12px rgba(255, 255, 255, 0.2);
}

.create-cover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--c-accent, #1db954);
}

.quick-card-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-right: 8px;
}

.quick-card-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-card-meta {
  font-size: 11px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.45));
  margin-top: 2px;
}

.quick-play-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--c-accent, #1db954);
  color: #000;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  margin-right: 10px;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  opacity: 0;
  transform: scale(0.85);
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.quick-card:hover .quick-play-btn {
  opacity: 1;
  transform: scale(1);
}

.quick-play-btn:hover {
  transform: scale(1.08) !important;
  background: #1ed760;
}

/* Show play buttons always on mobile for accessibility */
@media (max-width: 768px) {
  .quick-play-btn {
    opacity: 0.9;
    transform: scale(0.85);
    width: 32px;
    height: 32px;
    margin-right: 8px;
  }
}

/* Sections */
.home-section {
  margin-bottom: 28px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  letter-spacing: -0.01em;
}

.section-link {
  background: none;
  border: none;
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  cursor: pointer;
  transition: color 0.15s ease;
}

.section-link:hover {
  color: var(--c-accent, #1db954);
}

/* Horizontal Scroll */
.horizontal-scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 4px;
}

.horizontal-scroll::-webkit-scrollbar {
  display: none;
}

/* Feed Cards */
.feed-card {
  width: 128px;
  flex-shrink: 0;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.feed-card-cover {
  width: 128px;
  height: 128px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
  position: relative;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.feed-card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.feed-card-placeholder {
  font-size: 38px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.25);
}

.feed-card .play-overlay {
  position: absolute;
  bottom: 8px;
  right: 8px;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--c-accent, #1db954);
  color: #000;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transform: translateY(6px);
  transition: all 0.2s ease;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
}

.feed-card:hover .play-overlay {
  opacity: 1;
  transform: translateY(0);
}

.feed-card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.feed-card-subtitle {
  font-size: 11px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Discovery Banner */
.discovery-banner {
  background: linear-gradient(135deg, rgba(30, 27, 75, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
  border: 1px solid rgba(139, 92, 246, 0.25);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), inset 0 0 24px rgba(139, 92, 246, 0.08);
}

.discovery-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #a78bfa;
  margin-bottom: 8px;
}

.discovery-title {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 6px;
}

.discovery-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.4;
  margin-bottom: 14px;
}

.discovery-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(139, 92, 246, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.4);
  color: #fff;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.discovery-btn:hover {
  background: rgba(139, 92, 246, 0.35);
  transform: translateY(-1px);
}

.discovery-btn:active {
  transform: scale(0.97);
}
</style>
