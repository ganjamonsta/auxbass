<template>
  <div class="sc-pane">
    <!-- If viewing a selected SoundCloud Playlist drawer/detail -->
    <div v-if="selectedScPlaylist" class="sc-playlist-detail-view">
      <div class="sc-playlist-detail-header">
        <button class="btn-back-pill" @click="closeScPlaylist">
          <ArrowLeft :size="16" />
          <span>Назад ко всем плейлистам</span>
        </button>
        <div class="sc-playlist-detail-meta">
          <div class="sc-playlist-detail-cover">
            <img 
              v-if="selectedScPlaylist.artwork_url" 
              :src="getCoverUrl(selectedScPlaylist.artwork_url, CoverSize.MEDIUM)" 
              alt="" 
              referrerpolicy="no-referrer" 
            />
            <Folder v-else :size="48" />
          </div>
          <div class="sc-playlist-detail-text">
            <span class="sc-badge-inline">Плейлист SoundCloud</span>
            <h2 class="sc-detail-title">{{ selectedScPlaylist.title }}</h2>
            <div class="sc-detail-sub">
              <span>{{ scPlaylistTracks.length || selectedScPlaylist.track_count }} {{ getTracksWord(scPlaylistTracks.length || selectedScPlaylist.track_count) }}</span>
              <span v-if="selectedScPlaylist.permalink_url" class="stat-separator">•</span>
              <a 
                v-if="selectedScPlaylist.permalink_url" 
                :href="selectedScPlaylist.permalink_url" 
                target="_blank" 
                rel="noopener noreferrer" 
                class="ext-strip-link"
              >
                <span>SoundCloud</span>
                <ExternalLink :size="12" />
              </a>
            </div>
            <div v-if="isSelf" class="sc-detail-actions-row">
              <button 
                class="sc-sync-btn"
                :disabled="isSyncingScPlaylist || loadingScPlaylistTracks || scPlaylistTracks.length === 0"
                @click="$emit('syncPlaylist', selectedScPlaylist)"
                title="Создать плейлист в TG Player и загрузить треки в Telegram-канал"
              >
                <div v-if="isSyncingScPlaylist" class="spinner small"></div>
                <CloudDownload v-else :size="15" />
                <span>{{ isSyncingScPlaylist ? 'Синхронизация плейлиста...' : `Синхронизировать в TG Player (${scPlaylistTracks.length || selectedScPlaylist.track_count})` }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading playlist tracks -->
      <div v-if="loadingScPlaylistTracks" class="loading-container">
        <div class="spinner"></div>
      </div>

      <!-- Playlist tracklist -->
      <div v-else class="sc-playlist-tracks-list">
        <ExternalTrackItem
          v-for="item in scPlaylistTracks"
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
        <div v-if="scPlaylistTracks.length === 0" class="empty-state">
          <div class="empty-icon"><Music :size="40" /></div>
          <p>В этом плейлисте нет треков</p>
        </div>
      </div>
    </div>

    <!-- Normal Subtabs: Playlists vs Releases vs Likes -->
    <div v-else class="sc-main-content">
      <div class="sc-subtabs-bar">
        <div class="sc-subtabs-group">
          <button 
            class="sc-subtab-btn" 
            :class="{ active: scSubTab === 'playlists' }"
            @click="scSubTab = 'playlists'"
          >
            <Folder :size="15" />
            <span>Плейлисты</span>
            <span class="subtab-count">{{ scPlaylists.length }}</span>
          </button>
          <button 
            class="sc-subtab-btn" 
            :class="{ active: scSubTab === 'tracks' }"
            @click="scSubTab = 'tracks'"
          >
            <Music :size="15" />
            <span>Релизы и треки</span>
            <span class="subtab-count">{{ scTracks.length }}</span>
          </button>
          <button 
            v-if="isSelf"
            class="sc-subtab-btn sc-likes-tab-btn" 
            :class="{ active: scSubTab === 'likes' }"
            @click="selectLikesSubTab"
          >
            <Heart :size="15" />
            <span>Лайки</span>
            <span v-if="scAccount?.likes_count || scLikes.length" class="subtab-count">{{ scAccount?.likes_count || scLikes.length }}</span>
          </button>
        </div>

        <div class="sc-subtabs-actions">
          <a 
            v-if="scAccountUrl" 
            :href="scAccountUrl" 
            target="_blank" 
            rel="noopener noreferrer" 
            class="sc-open-external-btn"
            title="Открыть профиль на SoundCloud"
          >
            <span class="sc-badge-inline">SC</span>
            <span>В SoundCloud</span>
            <ExternalLink :size="12" />
          </a>
        </div>
      </div>

      <!-- Subtab 1: Playlists -->
      <div v-if="scSubTab === 'playlists'" class="sc-subtab-content">
        <div v-if="loadingScPlaylists" class="loading-container">
          <div class="spinner"></div>
        </div>
        <div v-else-if="scPlaylists.length > 0" class="overview-grid">
          <div 
            v-for="pl in scPlaylists" 
            :key="pl.id" 
            class="feed-card ext-card sc-card"
            @click="openScPlaylist(pl)"
          >
            <div class="feed-card-cover sc-cover-box">
              <img 
                v-if="pl.artwork_url" 
                :src="getCoverUrl(pl.artwork_url, CoverSize.MEDIUM)" 
                alt=""
                loading="lazy"
                referrerpolicy="no-referrer"
              />
              <Folder v-else :size="36" />
              <div class="play-overlay" title="Смотреть треки">
                <Play :size="18" fill="currentColor" />
              </div>
            </div>
            <div class="feed-card-info">
              <div class="feed-card-title">{{ pl.title }}</div>
              <div class="feed-card-subtitle">{{ pl.track_count }} {{ getTracksWord(pl.track_count) }}</div>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <div class="empty-icon"><Folder :size="44" /></div>
          <h3>Нет плейлистов SoundCloud</h3>
          <p>Пользователь не создал или скрыл свои плейлисты на SoundCloud</p>
        </div>
      </div>

      <!-- Subtab 2: Releases / Tracks -->
      <div v-if="scSubTab === 'tracks'" class="sc-subtab-content">
        <div v-if="loadingScTracks" class="loading-container">
          <div class="spinner"></div>
        </div>
        <div v-else-if="scTracks.length > 0" class="sc-tracks-wrapper">
          <div class="ext-tracks-list">
            <ExternalTrackItem
              v-for="item in scTracks"
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
          <div v-if="scTracksCursor" class="load-more-box">
            <button 
              class="btn-pill-secondary" 
              :disabled="loadingMoreScTracks" 
              @click="$emit('loadMore')"
            >
              <div v-if="loadingMoreScTracks" class="spinner small"></div>
              <span v-else>Загрузить ещё релизы</span>
            </button>
          </div>
        </div>
        <div v-else class="empty-state">
          <div class="empty-icon"><Music :size="44" /></div>
          <h3>Нет релизов на SoundCloud</h3>
          <p>Пользователь ещё не загружал собственные авторские треки на SoundCloud</p>
        </div>
      </div>

      <!-- Subtab 3: Likes (when viewing self) -->
      <div v-if="scSubTab === 'likes'" class="sc-subtab-content">
        <div v-if="loadingScLikes && scLikes.length === 0" class="loading-container">
          <div class="spinner"></div>
        </div>
        <div v-else-if="scLikes.length > 0" class="sc-tracks-wrapper">
          <div class="sc-likes-top-bar">
            <span class="sc-likes-title-hint">Понравившиеся треки на SoundCloud ({{ scLikes.length }})</span>
            <button class="btn-pill-secondary sc-open-search-btn" @click="goToLikesInSearch">
              <Search :size="14" />
              <span>Открыть в поиске / импорте</span>
            </button>
          </div>
          <div class="ext-tracks-list">
            <ExternalTrackItem
              v-for="item in scLikes"
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
          <div v-if="scLikesCursor" class="load-more-box">
            <button 
              class="btn-pill-secondary" 
              :disabled="loadingMoreScLikes" 
              @click="loadMoreScLikes"
            >
              <div v-if="loadingMoreScLikes" class="spinner small"></div>
              <span v-else>Загрузить ещё лайки</span>
            </button>
          </div>
        </div>
        <div v-else class="empty-state">
          <div class="empty-icon"><Heart :size="44" /></div>
          <h3>Нет лайкнутых треков</h3>
          <p>В вашем профиле SoundCloud пока нет лайкнутых треков</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTasksStore } from '@/stores/tasks'
import { socialApi, ingestionApi } from '@/api/client'
import { useUIStore } from '@/stores/ui'
import { getTracksWord } from './profileUtils'
import { getCoverUrl, CoverSize } from '@/utils'
import ExternalTrackItem from '@/components/ExternalTrackItem.vue'
import {
  Folder,
  Music,
  Play,
  Heart,
  Search,
  ExternalLink,
  ArrowLeft,
  CloudDownload,
} from 'lucide-vue-next'

const props = defineProps({
  userId: { type: Number, required: true },
  isSelf: { type: Boolean, default: false },
  scAccount: { type: Object, default: null },
  scPlaylists: { type: Array, default: () => [] },
  scTracks: { type: Array, default: () => [] },
  loadingScPlaylists: { type: Boolean, default: false },
  loadingScTracks: { type: Boolean, default: false },
  scTracksCursor: { type: String, default: null },
  loadingMoreScTracks: { type: Boolean, default: false },
  importingTrackUrl: { type: String, default: null },
  isSyncingScPlaylist: { type: Boolean, default: false },
})

defineEmits(['loadMore', 'syncPlaylist', 'quickPlay', 'quickAdd'])

const tasksStore = useTasksStore()
const uiStore = useUIStore()
const router = useRouter()

// Local SC-tab state
const scSubTab = ref('playlists')
const selectedScPlaylist = ref(null)
const scPlaylistTracks = ref([])
const loadingScPlaylistTracks = ref(false)

const scAccountUrl = computed(() => {
  if (!props.scAccount) return null
  const raw = props.scAccount.profile_url || props.scAccount.permalink_url || (props.scAccount.username ? `https://soundcloud.com/${props.scAccount.username}` : null)
  if (!raw) return null
  if (raw.startsWith('http://') || raw.startsWith('https://')) return raw
  return `https://${raw}`
})

// Likes state
const scLikes = ref([])
const loadingScLikes = ref(false)
const scLikesCursor = ref(null)
const loadingMoreScLikes = ref(false)
const hasFetchedLikes = ref(false)

const loadScLikes = async (reset = true) => {
  if (!props.isSelf) return
  loadingScLikes.value = true
  if (reset) {
    scLikesCursor.value = null
    scLikes.value = []
  }
  try {
    const res = await ingestionApi.getSoundCloudLikes({ limit: 40 })
    scLikes.value = res.data?.items || []
    scLikesCursor.value = res.data?.next_cursor || null
    hasFetchedLikes.value = true
  } catch (err) {
    console.error('Failed to load SC likes:', err)
  } finally {
    loadingScLikes.value = false
  }
}

const loadMoreScLikes = async () => {
  if (!scLikesCursor.value || loadingMoreScLikes.value) return
  loadingMoreScLikes.value = true
  try {
    const res = await ingestionApi.getSoundCloudLikes({ cursor: scLikesCursor.value, limit: 40 })
    const more = res.data?.items || []
    scLikes.value = [...scLikes.value, ...more]
    scLikesCursor.value = res.data?.next_cursor || null
  } catch (err) {
    console.error('Failed to load more SC likes:', err)
  } finally {
    loadingMoreScLikes.value = false
  }
}

const selectLikesSubTab = () => {
  scSubTab.value = 'likes'
  if (!hasFetchedLikes.value) {
    loadScLikes(true)
  }
}

const goToLikesInSearch = () => {
  router.push({ path: '/search', query: { tab: 'soundcloud', mode: 'likes' } })
}

const isTrackInLibrary = (item) => {
  if (!item) return false
  return item.in_library || tasksStore.isTrackCompleted(item.url)
}

const openScPlaylist = async (pl) => {
  selectedScPlaylist.value = pl
  scPlaylistTracks.value = []
  loadingScPlaylistTracks.value = true
  try {
    const res = await socialApi.getUserExternalPlaylistTracks(props.userId, pl.id)
    scPlaylistTracks.value = res.data?.tracks || []
  } catch (err) {
    console.error('Failed to load SC playlist tracks:', err)
    uiStore.toast?.error('Ошибка', 'Не удалось загрузить треки плейлиста')
  } finally {
    loadingScPlaylistTracks.value = false
  }
}

const closeScPlaylist = () => {
  selectedScPlaylist.value = null
  scPlaylistTracks.value = []
}

// Expose for parent access if needed
defineExpose({ scPlaylistTracks, openScPlaylist, closeScPlaylist })
</script>

<style scoped>
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 80px 0;
}

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

.empty-state h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
}

.empty-state p {
  color: var(--c-text-2);
  font-size: 14px;
  max-width: 320px;
}

/* Subtabs */
.sc-subtabs-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 22px;
  flex-wrap: wrap;
}

.sc-subtabs-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.sc-subtab-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.sc-subtab-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-1, #fff);
  border-color: rgba(255, 255, 255, 0.16);
  transform: translateY(-1px);
}

.sc-subtab-btn.active {
  background: rgba(255, 85, 0, 0.14);
  border-color: rgba(255, 85, 0, 0.45);
  color: #fff;
  box-shadow: 0 4px 14px rgba(255, 85, 0, 0.15);
}

.subtab-count {
  font-size: 11px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.08);
  padding: 1.5px 7px;
  border-radius: 9999px;
  transition: background 0.2s, color 0.2s;
}

.sc-subtab-btn.active .subtab-count {
  background: #ff5500;
  color: #fff;
}

.sc-subtabs-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sc-open-external-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 36px;
  padding: 0 14px;
  border-radius: var(--r-full, 9999px);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 85, 0, 0.25);
  color: var(--c-text-2, rgba(255, 255, 255, 0.85));
  font-size: 12.5px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.sc-open-external-btn:hover {
  background: rgba(255, 85, 0, 0.12);
  border-color: #ff5500;
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(255, 85, 0, 0.2);
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

/* Grid & Cards */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 18px;
}

.feed-card {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 12px;
  padding: 12px;
  transition: all 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
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

.sc-cover-box {
  background: linear-gradient(135deg, rgba(255, 85, 0, 0.2) 0%, rgba(20, 20, 20, 0.8) 100%) !important;
}

/* Playlist Detail */
.sc-playlist-detail-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sc-playlist-detail-header {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.btn-back-pill {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--c-text-1, #fff);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-back-pill:hover {
  background: rgba(255, 255, 255, 0.14);
  transform: translateX(-2px);
}

.sc-playlist-detail-meta {
  display: flex;
  align-items: center;
  gap: 20px;
}

.sc-playlist-detail-cover {
  width: 100px;
  height: 100px;
  min-width: 100px;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.sc-playlist-detail-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sc-playlist-detail-text {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sc-detail-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  margin: 0;
}

.sc-detail-sub {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
}

.sc-detail-actions-row {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.sc-sync-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #ff5500 0%, #cc4400 100%);
  color: #fff;
  border: none;
  padding: 10px 18px;
  border-radius: 9999px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(255, 85, 0, 0.35);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.sc-sync-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #ff6600 0%, #dd4400 100%);
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(255, 85, 0, 0.45);
}

.sc-sync-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Lists */
.ext-tracks-list,
.sc-playlist-tracks-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.load-more-box {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.btn-pill-secondary {
  padding: 10px 24px;
  border-radius: var(--r-full, 9999px);
  background: var(--c-bg-3, #222);
  color: var(--c-text-1, #fff);
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.sc-likes-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 4px 8px;
  gap: 16px;
}

.sc-likes-title-hint {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
}

.sc-open-search-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 9999px;
  color: var(--c-text-1, #fff);
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-open-search-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 85, 0, 0.4);
}

.sc-likes-tab-btn.active {
  background: rgba(255, 85, 0, 0.18);
  border-color: #ff5500;
  color: #ff5500;
}
</style>
