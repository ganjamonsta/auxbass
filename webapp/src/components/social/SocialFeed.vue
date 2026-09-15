<template>
  <div class="social-feed">
    <!-- Scope & Filter Header Bar -->
    <div class="feed-header-bar">
      <!-- Neumorphic Scope Switcher -->
      <div class="neu-tab-bar feed-scope-tabs">
        <button 
          class="neu-tab"
          :class="{ active: currentScope === 'following' }"
          @click="setScope('following')"
          title="Обновления друзей, на которых вы подписаны"
        >
          <Users :size="15" />
          <span class="neu-tab-content" data-text="Подписки">Подписки</span>
        </button>

        <button 
          class="neu-tab"
          :class="{ active: currentScope === 'global' }"
          @click="setScope('global')"
          title="Свежие загрузки всех пользователей AuxBass"
        >
          <Globe :size="15" />
          <span class="neu-tab-content" data-text="Глобально">Глобально</span>
        </button>
      </div>

      <!-- Refresh button -->
      <button 
        class="feed-refresh-btn" 
        :class="{ refreshing: loading && !loadingMore }"
        @click="refreshFeed"
        title="Обновить ленту"
      >
        <RefreshCw :size="15" />
      </button>
    </div>

    <!-- Feed Content -->
    <div class="feed-content">
      <!-- Initial Loading Skeleton -->
      <div v-if="loading && feedItems.length === 0" class="feed-skeletons">
        <div v-for="i in 4" :key="i" class="feed-skeleton-card">
          <div class="skeleton-header">
            <div class="skeleton-avatar pulse"></div>
            <div class="skeleton-header-info">
              <div class="skeleton-line-1 pulse"></div>
              <div class="skeleton-line-2 pulse"></div>
            </div>
          </div>
          <TrackSkeleton />
        </div>
      </div>

      <!-- Empty State: Following -->
      <div v-else-if="!loading && feedItems.length === 0 && currentScope === 'following'" class="feed-empty-state">
        <div class="empty-icon-box">
          <Radio :size="46" />
        </div>
        <h3>В ленте подписок пока пусто</h3>
        <p>Пользователи, на которых вы подписаны, ещё ничего не загрузили, или у вас пока нет подписок.</p>
        <div class="empty-actions">
          <button class="btn-pill-primary" @click="setScope('global')">
            <Globe :size="16" />
            <span>Глобальные аплоуды</span>
          </button>
          <button class="btn-pill-secondary" @click="$emit('navigate-tab', 'search')">
            <UserPlus :size="16" />
            <span>Найти друзей</span>
          </button>
        </div>
      </div>

      <!-- Empty State: Global -->
      <div v-else-if="!loading && feedItems.length === 0 && currentScope === 'global'" class="feed-empty-state">
        <div class="empty-icon-box">
          <Music :size="46" />
        </div>
        <h3>Пока нет глобальных загрузок</h3>
        <p>Здесь будут появляться все новые треки, загружаемые пользователями в Telegram.</p>
      </div>

      <!-- Feed Drops List -->
      <div v-else class="feed-drops-list">
        <div 
          v-for="drop in groupedDrops" 
          :key="drop.id"
          class="feed-drop-card"
        >
          <!-- Drop Header: Uploader Info & Actions -->
          <div class="drop-header">
            <div 
              class="uploader-avatar-box" 
              @click="goToUserProfile(drop.uploader.id)"
              :title="`Открыть профиль ${drop.uploader.display_name}`"
            >
              <img 
                v-if="drop.uploader.avatar_url" 
                :src="drop.uploader.avatar_url" 
                class="uploader-avatar-img" 
                alt="Avatar"
              />
              <span v-else class="uploader-initials">
                {{ getInitials(drop.uploader) }}
              </span>
            </div>

            <div class="uploader-info" @click="goToUserProfile(drop.uploader.id)">
              <div class="uploader-name-row">
                <span class="uploader-name">{{ drop.uploader.display_name }}</span>
                <span v-if="drop.uploader.id === authStore.user?.id" class="self-tag">Вы</span>
              </div>
              <div class="drop-meta-row">
                <span v-if="drop.uploader.username" class="uploader-handle">@{{ drop.uploader.username }} • </span>
                <span class="drop-action-text">{{ getActionText(drop.tracks.length) }}</span>
                <span class="meta-dot">•</span>
                <span class="drop-time" :title="drop.rawTimestamp">{{ drop.formattedTime }}</span>
              </div>
            </div>

            <!-- Play All / Play Drop Button (if drop has multiple tracks) -->
            <button 
              v-if="drop.tracks.length > 1"
              class="btn-play-drop"
              @click="handlePlayDrop(drop)"
              title="Слушать всю пачку треков"
            >
              <Play :size="15" fill="currentColor" />
              <span>Слушать всё</span>
            </button>
          </div>

          <!-- Drop Tracks Container -->
          <div class="drop-tracks-box">
            <TrackItem
              v-for="track in getVisibleTracks(drop)"
              :key="track.id"
              :track="track"
              :isPlaying="isCurrentlyPlaying(track)"
              :isLiked="track.is_liked"
              :showAddToLibrary="true"
              :inLibrary="track.in_library"
              @click="handlePlayTrack(track, drop.tracks)"
              @like="handleLikeTrack(track)"
              @addToLibrary="handleAddToLibrary(track)"
              @menu="openMenu('track', track, 'feed', $event)"
              @download="handleDirectDownload(track)"
            />

            <!-- Expand / Collapse Button if more than 3 tracks in drop -->
            <button 
              v-if="drop.tracks.length > 3" 
              class="btn-expand-drop"
              @click="toggleDropExpand(drop)"
            >
              <ChevronDown 
                :size="16" 
                class="expand-icon" 
                :class="{ rotated: drop.isExpanded }" 
              />
              <span>
                {{ drop.isExpanded ? 'Свернуть' : `Показать ещё ${drop.tracks.length - 3} ${getTracksWord(drop.tracks.length - 3)}` }}
              </span>
            </button>
          </div>
        </div>

        <!-- Load More Section -->
        <div v-if="hasMore" class="feed-load-more">
          <button 
            class="btn-load-more" 
            :disabled="loadingMore"
            @click="loadMore"
          >
            <div v-if="loadingMore" class="spinner-sm"></div>
            <span v-else>Загрузить ещё</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { socialApi } from '@/api/client'
import { usePlayerStore } from '@/stores/player'
import { useAuthStore } from '@/stores/auth'
import { useTrackActions } from '@/composables/useTrackActions'
import { useContextMenu } from '@/composables/useContextMenu'
import { useTrackSync } from '@/composables/useTrackSync'
import { formatFeedTimestamp } from '@/utils/formatters'
import TrackItem from '@/components/TrackItem.vue'
import TrackSkeleton from '@/components/TrackSkeleton.vue'
import { 
  Users, 
  Globe, 
  RefreshCw, 
  Radio, 
  UserPlus, 
  Music, 
  Play, 
  ChevronDown 
} from 'lucide-vue-next'

const emit = defineEmits(['navigate-tab'])

const router = useRouter()
const playerStore = usePlayerStore()
const authStore = useAuthStore()
const { handleDirectDownload, handleLikeTrack, handleAddToLibrary } = useTrackActions()
const { openMenu } = useContextMenu()

// State
const currentScope = ref('following')
const feedItems = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const hasMore = ref(false)
const expandedDrops = ref(new Set())

// Sync feed tracks with global like/delete events
useTrackSync(feedItems)

// All feed tracks flattened for queue playback
const allFeedTracks = computed(() => feedItems.value)

// Group consecutive tracks from the same uploader within 15 minutes into Release Drops
const groupedDrops = computed(() => {
  const drops = []
  let currentDrop = null
  const FIFTEEN_MIN_MS = 15 * 60 * 1000

  for (const track of feedItems.value) {
    const trackTime = track.created_at ? new Date(track.created_at).getTime() : Date.now()
    const uploaderId = track.uploader?.id

    if (
      currentDrop && 
      currentDrop.uploader?.id === uploaderId && 
      Math.abs(currentDrop.latestTimestamp - trackTime) <= FIFTEEN_MIN_MS
    ) {
      currentDrop.tracks.push(track)
      // Keep earliest/latest consistent
      if (trackTime > currentDrop.latestTimestamp) {
        currentDrop.latestTimestamp = trackTime
      }
    } else {
      currentDrop = {
        id: `drop-${uploaderId}-${track.id}`,
        uploader: track.uploader || { id: 0, display_name: 'Пользователь' },
        latestTimestamp: trackTime,
        rawTimestamp: track.created_at,
        formattedTime: formatFeedTimestamp(track.created_at),
        tracks: [track],
      }
      drops.push(currentDrop)
    }
  }

  // Bind reactive isExpanded state from Set
  return drops.map(d => ({
    ...d,
    isExpanded: expandedDrops.value.has(d.id),
  }))
})

const getVisibleTracks = (drop) => {
  if (drop.tracks.length <= 3 || drop.isExpanded) {
    return drop.tracks
  }
  return drop.tracks.slice(0, 3)
}

const toggleDropExpand = (drop) => {
  if (expandedDrops.value.has(drop.id)) {
    expandedDrops.value.delete(drop.id)
  } else {
    expandedDrops.value.add(drop.id)
  }
}

const isCurrentlyPlaying = (track) => {
  return playerStore.currentTrack?.id === track.id && playerStore.isPlaying
}

const getInitials = (user) => {
  if (!user) return '?'
  if (user.display_name) return user.display_name.charAt(0).toUpperCase()
  if (user.username) return user.username.charAt(0).toUpperCase()
  return '?'
}

const getActionText = (count) => {
  if (count <= 1) return 'загрузил трек'
  return `загрузил ${count} ${getTracksWord(count)}`
}

const getTracksWord = (count) => {
  const n = Math.abs(count) % 100
  const n1 = n % 10
  if (n > 10 && n < 20) return 'треков'
  if (n1 > 1 && n1 < 5) return 'трека'
  if (n1 === 1) return 'трек'
  return 'треков'
}

// Fetch feed from backend
const fetchFeed = async (scope, targetPage = 1, append = false) => {
  if (targetPage === 1) {
    loading.value = true
  } else {
    loadingMore.value = true
  }

  try {
    const res = await socialApi.getFeed(scope, targetPage, 30)
    const items = res.data?.items || []
    
    if (append) {
      feedItems.value = [...feedItems.value, ...items]
    } else {
      feedItems.value = items
    }
    
    page.value = targetPage
    hasMore.value = Boolean(res.data?.has_more)
  } catch (error) {
    console.error('Failed to load activity feed:', error)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const setScope = (scope) => {
  if (currentScope.value === scope) return
  currentScope.value = scope
  feedItems.value = []
  page.value = 1
  fetchFeed(scope, 1)
}

const refreshFeed = () => {
  fetchFeed(currentScope.value, 1)
}

const loadMore = () => {
  if (!loadingMore.value && hasMore.value) {
    fetchFeed(currentScope.value, page.value + 1, true)
  }
}

// Playback handlers
const handlePlayTrack = (track, queue) => {
  playerStore.playTrack(track, queue && queue.length ? queue : allFeedTracks.value)
}

const handlePlayDrop = (drop) => {
  if (!drop.tracks.length) return
  playerStore.playTrack(drop.tracks[0], drop.tracks)
}


const goToUserProfile = (userId) => {
  if (userId) {
    router.push(`/user/${userId}`)
  }
}

onMounted(() => {
  fetchFeed(currentScope.value, 1)
})
</script>

<style scoped>
.social-feed {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

/* Header bar with Scope Switcher */
.feed-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.feed-scope-tabs {
  margin-bottom: 0;
}

.feed-refresh-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--r-full);
  background: var(--c-bg-2);
  border: 1px solid rgba(255, 255, 255, 0.04);
  color: var(--c-text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 
    3px 3px 6px var(--sh-dark),
    -2px -2px 4px var(--sh-light);
  transition: all 0.2s ease;
}

.feed-refresh-btn:hover {
  color: var(--c-text-1);
  background: var(--c-bg-3);
  transform: translateY(-1px);
}

.feed-refresh-btn:active {
  transform: scale(0.95);
}

.feed-refresh-btn.refreshing svg {
  animation: spin 1s linear infinite;
}

/* @keyframes spin — defined in design-system.css */

/* Empty states */
.feed-empty-state {
  text-align: center;
  padding: 56px 20px;
  background: var(--c-bg-2);
  border-radius: var(--r-xl);
  box-shadow: 
    3px 3px 10px var(--sh-dark),
    -2px -2px 5px var(--sh-light);
  border: 1px solid rgba(255, 255, 255, 0.03);
  margin-top: 8px;
}

.empty-icon-box {
  width: 72px;
  height: 72px;
  border-radius: var(--r-full);
  background: var(--c-bg-3);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 18px;
  color: var(--c-accent);
  box-shadow: 
    inset 2px 2px 5px var(--sh-dark),
    inset -1px -1px 3px var(--sh-light);
}

.feed-empty-state h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0 0 8px;
}

.feed-empty-state p {
  font-size: 14px;
  color: var(--c-text-2);
  max-width: 420px;
  margin: 0 auto 24px;
  line-height: 1.5;
}

.empty-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

/* Skeletons */
.feed-skeletons {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feed-skeleton-card {
  background: var(--c-bg-2);
  border-radius: var(--r-lg);
  padding: 14px;
  border: 1px solid rgba(255, 255, 255, 0.02);
}

.skeleton-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.skeleton-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--r-full);
  background: var(--c-bg-3);
}

.skeleton-header-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.skeleton-line-1 {
  width: 140px;
  height: 14px;
  background: var(--c-bg-3);
  border-radius: 4px;
}

.skeleton-line-2 {
  width: 190px;
  height: 11px;
  background: var(--c-bg-3);
  border-radius: 4px;
}

.pulse {
  animation: pulseAnim 1.5s ease-in-out infinite;
}

@keyframes pulseAnim {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

/* Drops List */
.feed-drops-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feed-drop-card {
  background: var(--c-bg-2);
  border-radius: var(--r-xl);
  padding: 14px 16px;
  border: 1px solid rgba(255, 255, 255, 0.03);
  box-shadow: 
    3px 3px 10px var(--sh-dark),
    -2px -2px 5px var(--sh-light);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.feed-drop-card:hover {
  border-color: rgba(255, 255, 255, 0.06);
}

/* Drop Header */
.drop-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

.uploader-avatar-box {
  width: 42px;
  height: 42px;
  border-radius: var(--r-full);
  background: linear-gradient(135deg, var(--c-accent), #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow: 2px 2px 6px var(--sh-dark);
  transition: transform 0.15s ease;
}

.uploader-avatar-box:hover {
  transform: scale(1.05);
}

.uploader-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.uploader-initials {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.uploader-info {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.uploader-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.uploader-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.uploader-name:hover {
  color: var(--c-accent);
}

.self-tag {
  font-size: 10px;
  font-weight: 700;
  background: var(--c-accent);
  color: #fff;
  padding: 1px 6px;
  border-radius: var(--r-full);
}

.drop-meta-row {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--c-text-2);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.uploader-handle {
  color: var(--c-text-3);
}

.drop-action-text {
  color: var(--c-text-2);
}

.meta-dot {
  color: var(--c-text-3);
  font-size: 10px;
}

.drop-time {
  color: var(--c-text-3);
}

/* Play Drop Button */
.btn-play-drop {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--r-full);
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.25);
  color: var(--c-accent);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.btn-play-drop:hover {
  background: var(--c-accent);
  color: #fff;
  transform: translateY(-1px);
}

.btn-play-drop:active {
  transform: scale(0.96);
}

/* Drop tracks */
.drop-tracks-box {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.btn-expand-drop {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 8px 12px;
  margin-top: 4px;
  background: var(--c-bg-3);
  border: 1px solid rgba(255, 255, 255, 0.02);
  border-radius: var(--r-md);
  color: var(--c-text-2);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-expand-drop:hover {
  background: var(--c-bg-4);
  color: var(--c-text-1);
}

.expand-icon {
  transition: transform 0.2s ease;
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

/* Load more */
.feed-load-more {
  display: flex;
  justify-content: center;
  padding: 16px 0 8px;
}

.btn-load-more {
  padding: 10px 24px;
  border-radius: var(--r-full);
  background: var(--c-bg-2);
  border: 1px solid rgba(255, 255, 255, 0.04);
  color: var(--c-text-1);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 
    3px 3px 8px var(--sh-dark),
    -2px -2px 4px var(--sh-light);
  transition: all 0.15s ease;
}

.btn-load-more:hover {
  background: var(--c-bg-3);
  transform: translateY(-1px);
}

.btn-load-more:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: var(--c-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
</style>
