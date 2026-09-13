<template>
  <div class="overview-pane">
    <!-- Loading overview skeletons -->
    <div v-if="loadingOverview" class="overview-loading">
      <section class="profile-section">
        <div class="section-header">
          <div class="skeleton-section-title"></div>
        </div>
        <div class="overview-grid">
          <div v-for="i in 6" :key="i" class="feed-card-skeleton">
            <div class="skeleton-feed-cover"></div>
            <div class="skeleton-feed-title"></div>
            <div class="skeleton-feed-sub"></div>
          </div>
        </div>
      </section>
    </div>

    <template v-else>
      <!-- Section 1: Playlists Grid -->
      <section v-if="overviewPlaylists.length > 0" class="profile-section">
        <div class="section-header">
          <h2 class="section-title clickable" @click="$emit('selectTab', 'playlists')" title="Перейти в плейлисты">Плейлисты</h2>
          <button class="section-link" @click="$emit('selectTab', 'playlists')">Все {{ user.playlist_count || overviewPlaylists.length }}</button>
        </div>
        <div class="overview-grid">
          <div 
            v-for="pl in overviewPlaylists.slice(0, 12)" 
            :key="pl.id" 
            class="feed-card"
            @click="goToPlaylist(pl)"
            @contextmenu.prevent="handlePlaylistContextMenu(pl, $event)"
            v-longpress="(e) => handlePlaylistContextMenu(pl, e)"
          >
            <div class="feed-card-cover" :style="getPlaylistCoverStyle(pl)">
              <img 
                v-if="pl.covers?.length" 
                :src="getCoverUrl(pl.covers[0], CoverSize.MEDIUM)" 
                alt=""
                loading="lazy"
              />
              <Folder v-else :size="36" />
              <button 
                v-if="pl.track_count > 0" 
                class="play-overlay" 
                @click.stop="shufflePlaylist(pl)"
                title="Слушать"
              >
                <Play :size="18" fill="currentColor" />
              </button>
            </div>
            <div class="feed-card-info">
              <div class="feed-card-title">{{ pl.name }}</div>
              <div class="feed-card-subtitle">{{ pl.track_count }} {{ getTracksWord(pl.track_count) }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Section 2: Albums Grid -->
      <section v-if="overviewAlbums.length > 0" class="profile-section">
        <div class="section-header">
          <h2 class="section-title clickable" @click="$emit('selectTab', 'albums')" title="Перейти в альбомы">Альбомы</h2>
          <button class="section-link" @click="$emit('selectTab', 'albums')">Все {{ overviewAlbums.length }}</button>
        </div>
        <div class="overview-grid">
          <div 
            v-for="album in overviewAlbums.slice(0, 12)" 
            :key="album.id" 
            class="feed-card"
            @click="goToAlbum(album)"
            @contextmenu.prevent="handleAlbumContextMenu(album, $event)"
            v-longpress="(e) => handleAlbumContextMenu(album, e)"
          >
            <div class="feed-card-cover">
              <img 
                v-if="album.cover_url" 
                :src="getCoverUrl(album.cover_url, CoverSize.MEDIUM)" 
                alt=""
                loading="lazy"
              />
              <Disc3 v-else :size="36" />
              <button 
                class="play-overlay" 
                @click.stop="shuffleAlbum(album)"
                title="Слушать"
              >
                <Play :size="18" fill="currentColor" />
              </button>
            </div>
            <div class="feed-card-info">
              <div class="feed-card-title">{{ album.name || album.title }}</div>
              <div class="feed-card-subtitle">{{ album.artist || 'Альбом' }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Section 3: Popular / Top Tracks -->
      <section v-if="overviewTracks.length > 0" class="profile-section">
        <div class="section-header">
          <h2 class="section-title clickable" @click="$emit('selectTab', 'tracks')" title="Перейти в треки">Треки</h2>
          <button class="section-link" @click="$emit('selectTab', 'tracks')">Все {{ user.track_count || overviewTracks.length }}</button>
        </div>
        <div class="profile-tracks-list">
          <TrackItem
            v-for="(track, index) in overviewTracks.slice(0, 5)"
            :key="track.id"
            :track="track"
            :trackNumber="index + 1"
            :isPlaying="playerStore.currentTrack?.id === track.id"
            :isLiked="libraryStore.isTrackLiked(track.id)"
            @click="handleTrackClick(track, index)"
            @like="handleLikeTrack(track)"
            @menu="(e) => handleTrackMenu(track, index, e)"
            @download="handleDirectDownload(track)"
            @addToLibrary="handleAddToLibrary(track)"
          />
        </div>
        <button 
          v-if="(user.track_count || overviewTracks.length) > 5" 
          class="profile-view-more-btn"
          @click="$emit('selectTab', 'tracks')"
        >
          <span>Показать все {{ user.track_count }} треков</span>
          <ChevronRight :size="16" />
        </button>
      </section>

      <!-- Section 4: SoundCloud Playlists (Overview preview) -->
      <section v-if="scPlaylists.length > 0" class="profile-section sc-section">
        <div class="section-header">
          <div class="section-title-with-badge clickable" @click="$emit('selectTab', 'soundcloud')" title="Перейти в SoundCloud">
            <span class="sc-badge-inline">SC</span>
            <h2 class="section-title">Плейлисты SoundCloud</h2>
          </div>
          <button class="section-link" @click="$emit('selectTab', 'soundcloud')">Все {{ scPlaylists.length }}</button>
        </div>
        <div class="overview-grid">
          <div 
            v-for="pl in scPlaylists.slice(0, 6)" 
            :key="pl.id" 
            class="feed-card ext-card sc-card"
            @click="$emit('openScPlaylist', pl)"
          >
            <div class="feed-card-cover sc-cover-box">
              <img 
                v-if="pl.artwork_url" 
                :src="pl.artwork_url" 
                alt=""
                loading="lazy"
                referrerpolicy="no-referrer"
              />
              <Folder v-else :size="36" />
              <div class="play-overlay" title="Открыть плейлист">
                <Play :size="18" fill="currentColor" />
              </div>
            </div>
            <div class="feed-card-info">
              <div class="feed-card-title">{{ pl.title }}</div>
              <div class="feed-card-subtitle">{{ pl.track_count }} {{ getTracksWord(pl.track_count) }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Section 5: SoundCloud Releases (Overview preview) -->
      <section v-if="scTracks.length > 0" class="profile-section sc-section">
        <div class="section-header">
          <div class="section-title-with-badge clickable" @click="$emit('selectTab', 'soundcloud')" title="Перейти в SoundCloud">
            <span class="sc-badge-inline">SC</span>
            <h2 class="section-title">Релизы SoundCloud</h2>
          </div>
          <button class="section-link" @click="$emit('selectTab', 'soundcloud')">Все {{ scTracks.length }}</button>
        </div>
        <div class="ext-tracks-overview-list">
          <ExternalTrackItem
            v-for="item in scTracks.slice(0, 5)"
            :key="item.url"
            :item="item"
            variant="soundcloud"
            :showBadges="true"
            :isImporting="importingTrackUrl === item.url"
            :isDownloading="tasksStore.isTrackDownloading(item.url)"
            :isQueued="tasksStore.isTrackQueued(item.url)"
            :isInLibrary="isTrackInLibrary(item)"
            @play="$emit('quickPlay', $event)"
            @add="$emit('quickAdd', $event)"
          />
        </div>
      </section>

      <!-- Empty State if user has no public content -->
      <div 
        v-if="overviewPlaylists.length === 0 && overviewTracks.length === 0 && overviewAlbums.length === 0 && scPlaylists.length === 0 && scTracks.length === 0" 
        class="empty-state"
      >
        <div class="empty-icon"><Music :size="48" /></div>
        <h2>Медиатека пуста</h2>
        <p>У пользователя пока нет публичных треков или плейлистов</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useTasksStore } from '@/stores/tasks'
import { useContextMenu } from '@/composables/useContextMenu'
import { useTrackActions } from '@/composables'
import { getCoverUrl, CoverSize } from '@/utils'
import { getTracksWord, computePlaylistCoverGradient } from './profileUtils'
import TrackItem from '@/components/TrackItem.vue'
import ExternalTrackItem from '@/components/ExternalTrackItem.vue'
import {
  Music,
  Folder,
  Disc3,
  Play,
  ChevronRight,
} from 'lucide-vue-next'

const props = defineProps({
  user: { type: Object, required: true },
  isSelf: { type: Boolean, default: false },
  loadingOverview: { type: Boolean, default: false },
  overviewTracks: { type: Array, default: () => [] },
  overviewPlaylists: { type: Array, default: () => [] },
  overviewAlbums: { type: Array, default: () => [] },
  scAccount: { type: Object, default: null },
  scPlaylists: { type: Array, default: () => [] },
  scTracks: { type: Array, default: () => [] },
  importingTrackUrl: { type: String, default: null },
})

defineEmits(['selectTab', 'openScPlaylist', 'quickPlay', 'quickAdd'])

const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const tasksStore = useTasksStore()
const { openMenu } = useContextMenu()
const { handleDirectDownload, handleLikeTrack, handleAddToLibrary } = useTrackActions()

const isTrackInLibrary = (item) => {
  if (!item) return false
  return item.in_library || tasksStore.isTrackCompleted(item.url)
}

const getPlaylistCoverStyle = (playlist) => {
  if (playlist?.covers?.length) return {}
  return computePlaylistCoverGradient(playlist?.name)
}

// Navigation
const goToPlaylist = (playlist) => {
  router.push(`/playlist/${playlist.id}`)
}

const goToAlbum = (album) => {
  router.push(`/album/${album.id}`)
}

// Playback
const shufflePlaylist = async (playlist) => {
  await playerStore.playShuffleAll('playlist', playlist.id, playlist.name)
}

const shuffleAlbum = async (album) => {
  await playerStore.playShuffleAll('album', album.id, album.name)
}

const handleTrackClick = (track, index) => {
  if (props.overviewTracks?.length) {
    playerStore.play(track, props.overviewTracks)
  } else {
    playerStore.play(track)
  }
}

// Context menus
const handleTrackMenu = (track, index, event) => {
  openMenu('track', track, 'social', event)
}

const handlePlaylistContextMenu = (playlist, event) => {
  openMenu('playlist', playlist, 'social', event)
}

const handleAlbumContextMenu = (album, event) => {
  openMenu('album', album, 'social', event)
}
</script>

<style scoped>
.empty-state {
  text-align: center;
  padding: 60px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon {
  color: var(--c-accent);
  opacity: 0.8;
  margin-bottom: 8px;
}

.empty-state h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
}

.empty-state p {
  color: var(--c-text-2);
  font-size: 14px;
  max-width: 320px;
}

/* Sections */
.profile-section {
  margin-bottom: 36px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  width: 100%;
}

.section-title {
  font-size: 20px;
  font-weight: 800;
  color: var(--c-text-1, #fff);
  letter-spacing: -0.015em;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.section-title.clickable {
  cursor: pointer;
  transition: color 0.15s ease;
  user-select: none;
}

.section-title.clickable:hover {
  color: var(--c-accent, #1db954);
}

.section-link {
  background: none;
  border: none;
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  cursor: pointer;
  transition: color 0.15s ease;
  flex-shrink: 0;
  white-space: nowrap;
}

.section-link:hover {
  color: var(--c-accent, #1db954);
}

.section-title-with-badge {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-title-with-badge.clickable {
  cursor: pointer;
}

.section-title-with-badge.clickable:hover .section-title {
  color: var(--c-accent, #1db954);
}

.sp-icon-title {
  color: #1db954;
}

/* Grid */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 18px;
  width: 100%;
}

@media (min-width: 1200px) {
  .overview-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 20px;
  }
}

/* Feed Cards */
.feed-card {
  width: 100%;
  min-width: 0;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 12px;
  padding: 12px;
  transition: all 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
  box-sizing: border-box;
}

.feed-card:hover {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.1);
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.4);
}

.feed-card-cover {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
  position: relative;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
}

.feed-card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.feed-card-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.feed-card-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feed-card-subtitle {
  font-size: 12px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.play-overlay {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--c-accent, #1db954);
  color: #000;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.5);
  opacity: 0;
  transform: translateY(8px) scale(0.9);
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
  z-index: 2;
}

.feed-card:hover .play-overlay {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.play-overlay:hover {
  transform: scale(1.08) !important;
  background: #1ed760;
}

/* SC/SP Cover variants */
.sc-cover-box {
  background: linear-gradient(135deg, rgba(255, 85, 0, 0.2) 0%, rgba(20, 20, 20, 0.8) 100%) !important;
}

.sc-badge-inline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #ff5500;
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  border-radius: 4px;
  padding: 1px 5px;
  line-height: 1.2;
  letter-spacing: 0.5px;
}

/* Track List */
.profile-tracks-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.profile-view-more-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 12px;
}

.profile-view-more-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-1, #fff);
  border-color: rgba(255, 255, 255, 0.12);
}

.ext-tracks-overview-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* Skeletons */
.feed-card-skeleton {
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 12px;
}

.skeleton-feed-cover {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  margin-bottom: 10px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-feed-title {
  height: 14px;
  width: 80%;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  margin-bottom: 6px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-feed-sub {
  height: 12px;
  width: 50%;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-section-title {
  height: 20px;
  width: 120px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 0.3; }
}

/* Responsive */
@media (max-width: 768px) {
  .profile-section {
    margin-bottom: 28px;
  }

  .overview-grid {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 12px;
  }

  .feed-card {
    padding: 10px;
  }

  .play-overlay {
    opacity: 0.9;
    transform: translateY(0);
    width: 32px;
    height: 32px;
    right: 6px;
    bottom: 6px;
  }
}

@media (max-width: 480px) {
  .section-title {
    font-size: 18px;
  }

  .profile-section {
    margin-bottom: 22px;
  }

  .overview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .feed-card {
    padding: 8px;
    border-radius: 10px;
  }

  .feed-card-cover {
    margin-bottom: 8px;
    border-radius: 7px;
  }

  .feed-card-title {
    font-size: 13px;
  }

  .feed-card-subtitle {
    font-size: 11px;
  }
}
</style>
