<template>
  <div class="profile-hero-card">
    <div class="hero-ambient-glow" :style="ambientGlowStyle"></div>

    <!-- Left: Full-Height Avatar -->
    <div 
      class="hero-avatar" 
      :class="{ 'is-clickable': isSelf }"
      :style="avatarGradientStyle"
      @click="isSelf && $emit('edit')"
      :title="isSelf ? 'Нажмите, чтобы изменить аватарку' : ''"
    >
      <img 
        v-if="userAvatar" 
        :src="userAvatar" 
        alt="Avatar" 
        class="hero-avatar-img" 
      />
      <span v-else class="hero-avatar-initials">{{ initials }}</span>
      <div v-if="isSelf" class="hero-avatar-edit-overlay">
        <Camera :size="26" />
        <span class="edit-avatar-text">Изменить</span>
      </div>
    </div>

    <!-- Right: Info, Nickname, Stats, Actions -->
    <div class="hero-body">
      <div class="hero-meta-top">
        <span class="hero-type-label">ПРОФИЛЬ</span>
        <span v-if="isSelf" class="self-badge">Вы</span>
        <span v-if="isSelf && user.hide_telegram_id" class="hidden-handle-badge" title="Скрыт от других пользователей">
          <EyeOff :size="11" /> скрыт
        </span>
      </div>

      <h1 class="hero-name" :title="user.display_name">{{ user.display_name }}</h1>

      <div class="hero-subline">
        <span v-if="user.username" class="hero-handle">@{{ user.username }}</span>
        <span v-if="user.username" class="stat-separator">•</span>
        <!-- Stats -->
        <button class="hero-stat-pill" @click="$emit('selectTab', 'tracks')" title="Смотреть треки">
          <span class="stat-num">{{ user.track_count }}</span>
          <span class="stat-label">{{ getTracksWord(user.track_count) }}</span>
        </button>
        <span class="stat-separator">•</span>
        <button class="hero-stat-pill" @click="$emit('selectTab', 'playlists')" title="Смотреть плейлисты">
          <span class="stat-num">{{ user.playlist_count }}</span>
          <span class="stat-label">{{ getPlaylistsWord(user.playlist_count) }}</span>
        </button>
        <span class="stat-separator">•</span>
        <div 
          class="hero-stat-pill"
          :class="{ 'clickable-stat': isSelf }"
          @click="isSelf && $router.push('/friends')"
          :title="isSelf ? 'Перейти к кентам' : ''"
        >
          <span class="stat-num">{{ user.followers_count }}</span>
          <span class="stat-label">подписчиков</span>
        </div>

        <!-- External Connected Accounts Badges -->
        <template v-if="scAccount">
          <span class="stat-separator">•</span>
          <button class="hero-ext-badge sc-badge" @click="$emit('selectTab', 'soundcloud')" title="SoundCloud профиль">
            <span class="sc-badge-inline">SC</span>
            <span class="ext-badge-name">{{ scAccount.username }}</span>
          </button>
        </template>

        <template v-if="spAccount">
          <span class="stat-separator">•</span>
          <button class="hero-ext-badge sp-badge" @click="$emit('selectTab', 'spotify')" title="Spotify профиль">
            <Radio :size="12" class="sp-icon-inline" />
            <span class="ext-badge-name">{{ spAccount.display_name || spAccount.username }}</span>
          </button>
        </template>
      </div>

      <!-- Top-right absolute share button -->
      <button class="hero-share-corner-btn" @click="$emit('share')" title="Поделиться профилем">
        <Share2 :size="18" />
      </button>

      <!-- Action Buttons Bar -->
      <div class="hero-actions-bar">
        <!-- Unified Play & Shuffle Capsule -->
        <div class="action-buttons hero-play-capsule" v-if="user.track_count > 0">
          <button 
            class="action-btn play-btn" 
            @click="$emit('play')"
            title="Слушать медиатеку"
          >
            <Play :size="19" fill="currentColor" />
          </button>
          <button 
            v-if="user.track_count > 1"
            class="action-btn shuffle-btn" 
            @click="$emit('shuffle')"
            title="Перемешать медиатеку"
          >
            <Shuffle :size="17" />
          </button>
        </div>

        <!-- Follow button -->
        <button
          v-if="!isSelf"
          class="hero-pill-btn follow-btn"
          :class="{ 'is-following': isFollowing }"
          :disabled="followLoading"
          @click="$emit('follow')"
          :title="isFollowing ? 'Отписаться' : 'Подписаться'"
        >
          <Check v-if="isFollowing" :size="18" />
          <UserPlus v-else :size="18" />
        </button>

        <!-- Edit Profile (if self) -->
        <button
          v-if="isSelf"
          class="hero-pill-btn edit-profile-btn"
          @click="$emit('edit')"
          title="Редактировать профиль"
        >
          <Edit3 :size="18" />
        </button>

        <!-- Settings (if self) -->
        <button
          v-if="isSelf"
          class="hero-pill-btn"
          @click="$router.push('/settings')"
          title="Настройки аккаунта"
        >
          <Settings :size="18" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { getTracksWord, getPlaylistsWord } from './profileUtils'
import {
  UserPlus,
  Check,
  Share2,
  Play,
  Shuffle,
  Settings,
  Camera,
  EyeOff,
  Edit3,
  Radio,
} from 'lucide-vue-next'

defineProps({
  user: { type: Object, required: true },
  isSelf: { type: Boolean, default: false },
  isFollowing: { type: Boolean, default: false },
  followLoading: { type: Boolean, default: false },
  userAvatar: { type: String, default: null },
  initials: { type: String, default: '?' },
  avatarGradientStyle: { type: Object, default: () => ({}) },
  ambientGlowStyle: { type: Object, default: () => ({}) },
  scAccount: { type: Object, default: null },
  spAccount: { type: Object, default: null },
})

defineEmits(['play', 'shuffle', 'follow', 'edit', 'share', 'selectTab'])
</script>

<style scoped>
/* Modern Profile Hero Card */
.profile-hero-card {
  position: relative;
  overflow: hidden;
  border-radius: 24px;
  background: var(--c-bg-2, #181818);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 28px 32px;
  margin-bottom: 28px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  gap: 32px;
}

.hero-ambient-glow {
  position: absolute;
  top: -60px;
  left: -40px;
  right: -40px;
  height: 240px;
  pointer-events: none;
  opacity: 0.95;
  filter: blur(28px);
}

.hero-avatar {
  position: relative;
  width: 176px;
  height: 176px;
  min-width: 176px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 56px;
  font-weight: 800;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  border: 3px solid rgba(255, 255, 255, 0.14);
  overflow: hidden;
  transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
  z-index: 1;
}

.hero-avatar.is-clickable {
  cursor: pointer;
}

.hero-avatar.is-clickable:hover {
  transform: scale(1.02);
  border-color: var(--c-accent, #1db954);
  box-shadow: 0 12px 36px rgba(29, 185, 84, 0.3);
}

.hero-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.hero-avatar-initials {
  user-select: none;
}

.hero-avatar-edit-overlay {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(2px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #fff;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.edit-avatar-text {
  font-size: 12px;
  font-weight: 700;
}

.hero-avatar.is-clickable:hover .hero-avatar-edit-overlay {
  opacity: 1;
}

.hero-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
  z-index: 1;
}

.hero-meta-top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hero-type-label {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  text-transform: uppercase;
}

.self-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--r-full, 9999px);
  background: var(--c-accent, #1db954);
  color: #000;
}

.hidden-handle-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
}

.hero-name {
  font-size: 38px;
  font-weight: 800;
  color: var(--c-text-1, #fff);
  margin: 0;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.025em;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.4);
}

.hero-subline {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 13.5px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
}

.hero-handle {
  font-size: 13.5px;
  color: var(--c-accent, #1db954);
  font-weight: 600;
}

.hero-stat-pill {
  background: none;
  border: none;
  padding: 0;
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
  font-size: 13.5px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.75));
  cursor: pointer;
  transition: color 0.15s ease;
}

.hero-stat-pill:hover {
  color: var(--c-accent, #1db954);
}

.stat-num {
  font-weight: 700;
  color: var(--c-text-1, #fff);
  font-size: 14px;
}

.stat-separator {
  color: rgba(255, 255, 255, 0.25);
  font-size: 11px;
}

.hero-actions-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.hero-share-corner-btn {
  position: absolute;
  top: 24px;
  right: 24px;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--c-text-1, #fff);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 5;
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.hero-share-corner-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.25);
  transform: scale(1.06);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.35);
}

.hero-share-corner-btn:active {
  transform: scale(0.96);
}

.hero-play-capsule {
  flex-shrink: 0;
}

.hero-pill-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--c-text-1, #fff);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  flex-shrink: 0;
  padding: 0;
}

.hero-pill-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.22);
  transform: scale(1.06);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
}

.hero-pill-btn:active:not(:disabled) {
  transform: scale(0.96);
}

.hero-pill-btn.follow-btn.is-following {
  background: rgba(255, 255, 255, 0.06);
  color: var(--c-accent, #1db954);
  border-color: rgba(29, 185, 84, 0.3);
}

/* External Account Badges */
.hero-ext-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 9999px;
  padding: 3px 10px;
  cursor: pointer;
  color: var(--c-text-1, #fff);
  font-size: 12px;
  font-weight: 600;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.hero-ext-badge:hover {
  background: rgba(255, 255, 255, 0.14);
  transform: translateY(-1px);
}

.hero-ext-badge.sc-badge {
  border-color: rgba(255, 85, 0, 0.35);
}

.hero-ext-badge.sc-badge:hover {
  border-color: #ff5500;
  box-shadow: 0 4px 14px rgba(255, 85, 0, 0.25);
}

.hero-ext-badge.sp-badge {
  border-color: rgba(29, 185, 84, 0.35);
}

.hero-ext-badge.sp-badge:hover {
  border-color: #1db954;
  box-shadow: 0 4px 14px rgba(29, 185, 84, 0.25);
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

.sp-icon-inline {
  color: #1db954;
  flex-shrink: 0;
}

.ext-badge-name {
  max-width: 130px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Responsive */
@media (max-width: 768px) {
  .profile-hero-card {
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 24px 20px;
    gap: 18px;
    max-width: 100%;
    box-sizing: border-box;
  }

  .hero-avatar {
    width: 130px;
    height: 130px;
    min-width: 130px;
    font-size: 42px;
  }

  .hero-body {
    align-items: center;
    width: 100%;
    max-width: 100%;
  }

  .hero-meta-top {
    justify-content: center;
  }

  .hero-name {
    font-size: 28px;
    max-width: 100%;
  }

  .hero-subline {
    justify-content: center;
    max-width: 100%;
  }

  .hero-actions-bar {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .hero-avatar {
    width: 108px;
    height: 108px;
    min-width: 108px;
    font-size: 36px;
  }

  .hero-name {
    font-size: 24px;
  }
}

@media (max-width: 600px) {
  .profile-hero-card {
    padding: 14px 16px;
  }
  .hero-avatar {
    width: 56px;
    height: 56px;
    min-width: 56px;
    font-size: 22px;
  }
  .hero-name {
    font-size: 18px;
  }
  .hero-actions-bar {
    gap: 8px;
  }
  .hero-pill-btn {
    padding: 7px 12px;
    font-size: 12px;
  }
}
</style>
