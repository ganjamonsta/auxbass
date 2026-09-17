<template>
  <div 
    class="user-social-card" 
    :class="[`layout-${layout}`, { 'is-self': isSelf }]"
    @click="$emit('click', user)"
    :title="`Открыть профиль ${displayName}`"
  >
    <!-- Card Ambient Glow Backdrop -->
    <div class="card-ambient-glow"></div>

    <!-- Main Content Area -->
    <div class="card-inner">
      <!-- Avatar with Glow Ring -->
      <div class="user-avatar-wrapper">
        <div class="user-avatar">
          <img 
            v-if="avatarUrl" 
            :src="avatarUrl" 
            class="avatar-img" 
            :alt="displayName" 
            loading="lazy"
          />
          <span v-else class="avatar-initials">{{ initials }}</span>
        </div>
        <span v-if="isMutual && layout === 'grid'" class="avatar-mutual-dot" title="Взаимная подписка"></span>
      </div>

      <!-- Identity & Info -->
      <div class="user-info">
        <div class="user-name-row">
          <h4 class="user-display-name" :title="displayName">
            {{ displayName }}
          </h4>
          <span v-if="isSelf" class="badge-tag self-tag">Вы</span>
          <span v-else-if="isMutual" class="badge-tag mutual-tag" title="Вы подписаны друг на друга">
            <Users :size="11" />
            <span>Взаимно</span>
          </span>
        </div>

        <div v-if="user.username" class="user-handle-row">
          <span class="user-handle">@{{ user.username }}</span>
        </div>

        <!-- Stats Chips -->
        <div class="user-stats">
          <span class="stat-pill" :title="`${user.track_count || 0} треков в медиатеке`">
            <Music :size="12" class="stat-icon" />
            <span>{{ user.track_count || 0 }} {{ getTracksWord(user.track_count || 0) }}</span>
          </span>

          <span 
            v-if="user.playlist_count > 0" 
            class="stat-pill"
            :title="`${user.playlist_count} публичных плейлистов`"
          >
            <Folder :size="12" class="stat-icon" />
            <span>{{ user.playlist_count }} плейл.</span>
          </span>

          <span 
            v-if="user.followers_count > 0" 
            class="stat-pill"
            :title="`${user.followers_count} подписчиков`"
          >
            <User :size="12" class="stat-icon" />
            <span>{{ user.followers_count }} подп.</span>
          </span>
        </div>
      </div>

      <!-- Actions Area -->
      <div class="card-actions" @click.stop>
        <!-- Listen / Play Library Button -->
        <button 
          v-if="showPlay && (user.track_count > 0)"
          class="btn-listen"
          @click="$emit('play', user)"
          title="Слушать медиатеку пользователя"
          aria-label="Слушать медиатеку"
        >
          <Play :size="13" fill="currentColor" />
          <span>Слушать</span>
        </button>

        <!-- Follow / Unfollow Toggle (only if not self) -->
        <template v-if="showFollow && !isSelf">
          <!-- Follow Button -->
          <button 
            v-if="!user.is_following"
            class="btn-follow-action"
            :disabled="isLoading"
            @click="$emit('follow', user)"
            title="Подписаться"
          >
            <UserPlus :size="14" />
            <span>Подписаться</span>
          </button>

          <!-- Unfollow Button with Hover Warning State -->
          <button 
            v-else
            class="btn-following-action"
            :disabled="isLoading"
            @click="$emit('unfollow', user)"
            title="Отписаться"
          >
            <span class="status-default">
              <Check :size="14" />
              <span>Подписан</span>
            </span>
            <span class="status-hover">
              <UserMinus :size="14" />
              <span>Отписаться</span>
            </span>
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { 
  Users, 
  User, 
  Music, 
  Folder, 
  Play, 
  Check, 
  UserPlus, 
  UserMinus 
} from 'lucide-vue-next'

const props = defineProps({
  user: {
    type: Object,
    required: true
  },
  layout: {
    type: String,
    default: 'grid', // 'grid' or 'list'
    validator: (val) => ['grid', 'list'].includes(val)
  },
  isSelf: {
    type: Boolean,
    default: false
  },
  isMutual: {
    type: Boolean,
    default: false
  },
  showFollow: {
    type: Boolean,
    default: true
  },
  showPlay: {
    type: Boolean,
    default: true
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click', 'play', 'follow', 'unfollow'])

const displayName = computed(() => {
  return props.user.custom_nickname || props.user.display_name || props.user.first_name || 'Пользователь'
})

const avatarUrl = computed(() => {
  const u = props.user
  return u.avatar_url || u.custom_avatar_url || u.photo_url || null
})

const initials = computed(() => {
  if (props.user.custom_nickname) return props.user.custom_nickname.charAt(0).toUpperCase()
  if (props.user.display_name) return props.user.display_name.charAt(0).toUpperCase()
  if (props.user.first_name) return props.user.first_name.charAt(0).toUpperCase()
  if (props.user.username) return props.user.username.charAt(0).toUpperCase()
  return '?'
})

const getTracksWord = (count) => {
  const n = Math.abs(count) % 100
  const n1 = n % 10
  if (n > 10 && n < 20) return 'треков'
  if (n1 > 1 && n1 < 5) return 'трека'
  if (n1 === 1) return 'трек'
  return 'треков'
}
</script>

<style scoped>
.user-social-card {
  position: relative;
  background: var(--c-bg-2);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: var(--r-xl);
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1),
              box-shadow 0.22s cubic-bezier(0.16, 1, 0.3, 1),
              border-color 0.22s cubic-bezier(0.16, 1, 0.3, 1),
              background 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 
    3px 3px 10px var(--sh-dark),
    -2px -2px 5px var(--sh-light);
}

.user-social-card:hover {
  background: var(--c-bg-3);
  border-color: rgba(34, 197, 94, 0.25);
  box-shadow: 
    4px 6px 16px var(--sh-dark),
    -2px -2px 6px var(--sh-light),
    0 0 16px rgba(34, 197, 94, 0.12);
  transform: translateY(-2px);
}

.user-social-card:active {
  transform: scale(0.99);
}

/* Ambient glow accent */
.card-ambient-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(34, 197, 94, 0.4), transparent);
  opacity: 0;
  transition: opacity 0.25s ease;
}

.user-social-card:hover .card-ambient-glow {
  opacity: 1;
}

/* ══════════════════════════════════════════════
   GRID LAYOUT
   ══════════════════════════════════════════════ */
.user-social-card.layout-grid {
  display: flex;
  flex-direction: column;
}

.user-social-card.layout-grid .card-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 20px 16px 16px;
  gap: 14px;
  height: 100%;
}

.user-social-card.layout-grid .user-avatar-wrapper {
  position: relative;
  margin-bottom: 2px;
}

.user-social-card.layout-grid .user-avatar {
  width: 68px;
  height: 68px;
  border-radius: var(--r-full);
  background: linear-gradient(135deg, #10b981 0%, #3b82f6 50%, #8b5cf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  overflow: hidden;
  border: 2px solid rgba(255, 255, 255, 0.08);
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.35),
    inset 0 0 8px rgba(255, 255, 255, 0.15);
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.user-social-card.layout-grid:hover .user-avatar {
  transform: scale(1.04);
  border-color: rgba(34, 197, 94, 0.4);
}

.avatar-mutual-dot {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 14px;
  height: 14px;
  border-radius: var(--r-full);
  background: var(--c-accent);
  border: 2px solid var(--c-bg-2);
  box-shadow: 0 0 8px var(--c-accent-glow);
}

.user-social-card.layout-grid .user-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  min-width: 0;
  gap: 6px;
  flex: 1;
}

.user-social-card.layout-grid .user-name-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  max-width: 100%;
  flex-wrap: wrap;
}

.user-social-card.layout-grid .user-display-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 160px;
}

.user-social-card.layout-grid .user-handle {
  font-size: 12px;
  color: var(--c-text-3);
  font-weight: 500;
}

.user-social-card.layout-grid .user-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.user-social-card.layout-grid .card-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  margin-top: auto;
  padding-top: 6px;
}

.user-social-card.layout-grid .card-actions button {
  flex: 1;
}

/* ══════════════════════════════════════════════
   LIST LAYOUT
   ══════════════════════════════════════════════ */
.user-social-card.layout-list {
  border-radius: var(--r-lg);
}

.user-social-card.layout-list .card-inner {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  gap: 14px;
}

.user-social-card.layout-list .user-avatar {
  width: 46px;
  height: 46px;
  border-radius: var(--r-full);
  background: linear-gradient(135deg, #10b981 0%, #3b82f6 50%, #8b5cf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  overflow: hidden;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 2px 2px 6px var(--sh-dark);
}

.user-social-card.layout-list .user-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.user-social-card.layout-list .user-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.user-social-card.layout-list .user-display-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text-1);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-social-card.layout-list .user-handle {
  font-size: 13px;
  color: var(--c-text-3);
}

.user-social-card.layout-list .user-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.user-social-card.layout-list .card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  margin-left: auto;
}

/* ══════════════════════════════════════════════
   SHARED ELEMENTS & BADGES
   ══════════════════════════════════════════════ */
.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-initials {
  font-size: 20px;
  font-weight: 700;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

.layout-list .avatar-initials {
  font-size: 16px;
}

/* Badges */
.badge-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: var(--r-full);
  line-height: 1;
  letter-spacing: 0.02em;
}

.self-tag {
  background: var(--c-accent);
  color: #fff;
  box-shadow: 0 0 8px var(--c-accent-glow);
}

.mutual-tag {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

/* Stat Pills */
.stat-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--c-text-2);
  background: rgba(255, 255, 255, 0.03);
  padding: 2px 7px;
  border-radius: var(--r-sm);
  border: 1px solid rgba(255, 255, 255, 0.03);
}

.stat-icon {
  color: var(--c-text-3);
}

/* Action Buttons */
.btn-listen {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 7px 13px;
  border-radius: var(--r-full);
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.28);
  color: var(--c-accent);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
  white-space: nowrap;
}

.btn-listen:hover {
  background: var(--c-accent);
  color: #ffffff;
  box-shadow: 0 0 12px var(--c-accent-glow);
  transform: translateY(-1px);
}

.btn-listen:active {
  transform: scale(0.96);
}

.btn-follow-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 7px 15px;
  border-radius: var(--r-full);
  background: var(--c-accent);
  border: none;
  color: #ffffff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
  box-shadow: 
    2px 2px 6px var(--sh-dark),
    0 0 10px var(--c-accent-glow);
  white-space: nowrap;
}

.btn-follow-action:hover {
  background: var(--c-accent-light);
  transform: translateY(-1px);
}

.btn-follow-action:active {
  transform: scale(0.96);
}

/* Following Action with smooth hover flip to Unfollow */
.btn-following-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 7px 14px;
  border-radius: var(--r-full);
  background: var(--c-bg-3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-2);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 2px 2px 5px var(--sh-dark);
  position: relative;
  white-space: nowrap;
  min-width: 104px;
}

.btn-following-action .status-default {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.btn-following-action .status-hover {
  display: none;
  align-items: center;
  gap: 5px;
}

.btn-following-action:hover {
  background: rgba(239, 68, 68, 0.14);
  border-color: rgba(239, 68, 68, 0.35);
  color: #f87171;
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.25);
  transform: translateY(-1px);
}

.btn-following-action:hover .status-default {
  display: none;
}

.btn-following-action:hover .status-hover {
  display: inline-flex;
}

.btn-following-action:active {
  transform: scale(0.96);
}
</style>
