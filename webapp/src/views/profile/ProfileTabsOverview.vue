<template>
  <div class="overview-pane">
    <!-- Loading overview skeletons -->
    <div v-if="loadingOverview" class="overview-loading">
      <section class="profile-section">
        <div class="section-header">
          <div class="skeleton-section-title"></div>
        </div>
        <div class="horizontal-scroll">
          <div v-for="i in 6" :key="i" class="feed-card-skeleton">
            <div class="skeleton-feed-cover"></div>
            <div class="skeleton-feed-title"></div>
            <div class="skeleton-feed-sub"></div>
          </div>
        </div>
      </section>
      <section class="profile-section">
        <div class="section-header">
          <div class="skeleton-section-title"></div>
        </div>
        <div class="horizontal-scroll">
          <div v-for="i in 6" :key="i" class="feed-card-skeleton">
            <div class="skeleton-feed-cover"></div>
            <div class="skeleton-feed-title"></div>
            <div class="skeleton-feed-sub"></div>
          </div>
        </div>
      </section>
    </div>

    <template v-else>
      <!-- Section 1: Playlists (Horizontal Scroll) -->
      <section v-if="overviewPlaylists.length > 0" class="profile-section">
        <div class="section-header">
          <h2 class="section-title clickable" @click="$emit('selectTab', 'playlists')" title="Перейти в плейлисты">Плейлисты</h2>
          <div class="section-actions">
            <button class="section-link" @click="$emit('selectTab', 'playlists')">Все {{ user.playlist_count || overviewPlaylists.length }}</button>
            <button 
              class="scroll-arrow-btn" 
              :disabled="!playlistsScroll.canScrollLeft.value"
              @click="playlistsScroll.scroll('left')"
              title="Назад"
              aria-label="Назад"
            >
              <ChevronLeft :size="16" />
            </button>
            <button 
              class="scroll-arrow-btn" 
              :disabled="!playlistsScroll.canScrollRight.value"
              @click="playlistsScroll.scroll('right')"
              title="Вперед"
              aria-label="Вперед"
            >
              <ChevronRight :size="16" />
            </button>
          </div>
        </div>
        <div 
          class="horizontal-scroll"
          :ref="playlistsScroll.containerRef"
        >
          <div 
            v-for="pl in overviewPlaylists.slice(0, 20)" 
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
              <Folder v-else :size="32" />
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

      <!-- Section 2: Albums (Horizontal Scroll) -->
      <section v-if="overviewAlbums.length > 0" class="profile-section">
        <div class="section-header">
          <h2 class="section-title clickable" @click="$emit('selectTab', 'albums')" title="Перейти в альбомы">Альбомы</h2>
          <div class="section-actions">
            <button class="section-link" @click="$emit('selectTab', 'albums')">Все {{ user.album_count || overviewAlbums.length }}</button>
            <button 
              class="scroll-arrow-btn" 
              :disabled="!albumsScroll.canScrollLeft.value"
              @click="albumsScroll.scroll('left')"
              title="Назад"
              aria-label="Назад"
            >
              <ChevronLeft :size="16" />
            </button>
            <button 
              class="scroll-arrow-btn" 
              :disabled="!albumsScroll.canScrollRight.value"
              @click="albumsScroll.scroll('right')"
              title="Вперед"
              aria-label="Вперед"
            >
              <ChevronRight :size="16" />
            </button>
          </div>
        </div>
        <div 
          class="horizontal-scroll"
          :ref="albumsScroll.containerRef"
        >
          <div 
            v-for="album in overviewAlbums.slice(0, 20)" 
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
              <Disc3 v-else :size="32" />
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
          <div class="section-actions">
            <button class="section-link" @click="$emit('selectTab', 'soundcloud')">Все {{ scPlaylists.length }}</button>
            <button 
              class="scroll-arrow-btn" 
              :disabled="!scPlaylistsScroll.canScrollLeft.value"
              @click="scPlaylistsScroll.scroll('left')"
              title="Назад"
              aria-label="Назад"
            >
              <ChevronLeft :size="16" />
            </button>
            <button 
              class="scroll-arrow-btn" 
              :disabled="!scPlaylistsScroll.canScrollRight.value"
              @click="scPlaylistsScroll.scroll('right')"
              title="Вперед"
              aria-label="Вперед"
            >
              <ChevronRight :size="16" />
            </button>
          </div>
        </div>
        <div 
          class="horizontal-scroll"
          :ref="scPlaylistsScroll.containerRef"
        >
          <div 
            v-for="pl in scPlaylists.slice(0, 20)" 
            :key="pl.id" 
            class="feed-card ext-card sc-card"
            @click="$emit('openScPlaylist', pl)"
          >
            <div class="feed-card-cover sc-cover-box">
              <img 
                v-if="pl.artwork_url" 
                :src="getCoverUrl(pl.artwork_url, CoverSize.MEDIUM)" 
                alt=""
                loading="lazy"
                referrerpolicy="no-referrer"
              />
              <Folder v-else :size="32" />
              <button class="play-overlay" title="Открыть плейлист" @click.stop="$emit('openScPlaylist', pl)">
                <Play :size="18" fill="currentColor" />
              </button>
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
import { ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useTasksStore } from '@/stores/tasks'
import { useContextMenu } from '@/composables/useContextMenu'
import { useTrackActions } from '@/composables'
import { useHorizontalScroll } from '@/composables/useHorizontalScroll'
import { getCoverUrl, CoverSize } from '@/utils'
import { getTracksWord, computePlaylistCoverGradient } from './profileUtils'
import TrackItem from '@/components/TrackItem.vue'
import ExternalTrackItem from '@/components/ExternalTrackItem.vue'
import {
  Music,
  Folder,
  Disc3,
  Play,
  ChevronLeft,
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

// Horizontal scroll instances
const playlistsScroll = useHorizontalScroll()
const albumsScroll = useHorizontalScroll()
const scPlaylistsScroll = useHorizontalScroll()

watch(
  () => [props.overviewPlaylists, props.overviewAlbums, props.scPlaylists],
  () => {
    nextTick(() => {
      playlistsScroll.updateScrollState()
      albumsScroll.updateScrollState()
      scPlaylistsScroll.updateScrollState()
    })
  },
  { deep: true }
)

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
  margin-bottom: 32px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  width: 100%;
  padding-right: var(--content-padding, 24px);
  box-sizing: border-box;
}

@media (min-width: 1024px) {
  .section-header {
    padding-right: var(--content-padding, 32px);
  }
}

@media (max-width: 768px) {
  .section-header {
    padding-right: var(--content-padding, 16px);
  }
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

.section-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.scroll-arrow-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--c-text-1, #fff);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  padding: 0;
  user-select: none;
}

.scroll-arrow-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.12);
  transform: scale(1.06);
}

.scroll-arrow-btn:active:not(:disabled) {
  transform: scale(0.94);
  background: rgba(255, 255, 255, 0.22);
}

.scroll-arrow-btn:disabled {
  opacity: 0.2;
  cursor: default;
  pointer-events: none;
}

@media (max-width: 768px) {
  .scroll-arrow-btn {
    display: none;
  }
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

/* Horizontal Scroll */
.horizontal-scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 8px;
  padding-right: var(--content-padding, 24px);
  width: 100%;
  box-sizing: border-box;
  scrollbar-width: thin;
  scrollbar-color: transparent transparent;
  transition: scrollbar-color 0.2s ease;
}

@media (min-width: 1024px) {
  .horizontal-scroll {
    padding-right: var(--content-padding, 32px);
  }
}

@media (max-width: 768px) {
  .horizontal-scroll {
    padding-right: var(--content-padding, 16px);
  }
}

.horizontal-scroll:hover {
  scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
}

.horizontal-scroll::-webkit-scrollbar {
  height: 5px;
}

.horizontal-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.horizontal-scroll::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 3px;
  transition: background 0.2s ease;
}

.horizontal-scroll:hover::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
}

.horizontal-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.38);
}

/* Feed Cards */
.feed-card {
  flex: 0 0 var(--card-min-width, 136px);
  width: var(--card-min-width, 136px);
  min-width: 0;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  user-select: none;
}

@media (min-width: 1024px) {
  .feed-card {
    flex: 0 0 var(--card-min-width, 160px);
    width: var(--card-min-width, 160px);
  }
}

.feed-card-cover {
  width: var(--card-min-width, 136px);
  height: var(--card-min-width, 136px);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
  position: relative;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s ease;
}

@media (min-width: 1024px) {
  .feed-card-cover {
    border-radius: 12px;
    margin-bottom: 10px;
    width: var(--card-min-width, 160px);
    height: var(--card-min-width, 160px);
  }

  .feed-card:hover .feed-card-cover {
    transform: translateY(-4px);
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.55);
  }
}

.feed-card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.feed-card-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.feed-card-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

@media (min-width: 1024px) {
  .feed-card-title {
    font-size: 14px;
    margin-top: 2px;
  }
}

.feed-card-subtitle {
  font-size: 11px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}

@media (min-width: 1024px) {
  .feed-card-subtitle {
    font-size: 12.5px;
  }
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
  cursor: pointer;
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.5);
  opacity: 0;
  pointer-events: none;
  transform: translateY(6px);
  transition: all 0.2s ease;
  z-index: 2;
}

@media (min-width: 1024px) {
  .feed-card .play-overlay {
    width: 42px;
    height: 42px;
    bottom: 10px;
    right: 10px;
  }
}

.feed-card:hover .play-overlay {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0);
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
  max-width: var(--content-max-width, 1400px);
  margin-right: var(--content-padding, 24px);
  box-sizing: border-box;
}

@media (min-width: 1024px) {
  .profile-tracks-list {
    margin-right: var(--content-padding, 32px);
  }
}

@media (max-width: 768px) {
  .profile-tracks-list {
    margin-right: var(--content-padding, 16px);
  }
}

.profile-view-more-btn {
  width: 100%;
  max-width: var(--content-max-width, 1400px);
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
  margin-right: var(--content-padding, 24px);
  box-sizing: border-box;
}

@media (min-width: 1024px) {
  .profile-view-more-btn {
    margin-right: var(--content-padding, 32px);
  }
}

@media (max-width: 768px) {
  .profile-view-more-btn {
    margin-right: var(--content-padding, 16px);
  }
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
  max-width: var(--content-max-width, 1400px);
  margin-right: var(--content-padding, 24px);
  box-sizing: border-box;
}

@media (min-width: 1024px) {
  .ext-tracks-overview-list {
    margin-right: var(--content-padding, 32px);
  }
}

@media (max-width: 768px) {
  .ext-tracks-overview-list {
    margin-right: var(--content-padding, 16px);
  }
}

/* Skeletons */
.feed-card-skeleton {
  flex: 0 0 var(--card-min-width, 136px);
  width: var(--card-min-width, 136px);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

@media (min-width: 1024px) {
  .feed-card-skeleton {
    flex: 0 0 var(--card-min-width, 160px);
    width: var(--card-min-width, 160px);
  }
}

.skeleton-feed-cover {
  width: var(--card-min-width, 136px);
  height: var(--card-min-width, 136px);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
  animation: pulse 1.5s ease-in-out infinite;
}

@media (min-width: 1024px) {
  .skeleton-feed-cover {
    width: var(--card-min-width, 160px);
    height: var(--card-min-width, 160px);
    border-radius: 12px;
  }
}

.skeleton-feed-title {
  height: 13px;
  width: 80%;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.1s;
}

.skeleton-feed-sub {
  height: 10px;
  width: 50%;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.05);
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.2s;
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

  .feed-card {
    flex: 0 0 128px;
    width: 128px;
  }

  .feed-card-cover {
    width: 128px;
    height: 128px;
  }

  .feed-card .play-overlay {
    opacity: 0.9;
    pointer-events: auto;
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

  .feed-card {
    flex: 0 0 118px;
    width: 118px;
  }

  .feed-card-cover {
    width: 118px;
    height: 118px;
    margin-bottom: 6px;
    border-radius: 8px;
  }

  .feed-card-title {
    font-size: 12px;
  }

  .feed-card-subtitle {
    font-size: 10.5px;
  }
}
</style>
