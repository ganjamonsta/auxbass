<template>
  <div class="profile-hero-card" :class="{ 'has-avatar-backdrop': !!userAvatar }">
    <div class="hero-ambient-glow" :style="ambientGlowStyle"></div>

    <!-- Tiled Avatar Backdrop across the entire card (Windows wallpaper tile style) -->
    <div v-if="userAvatar" class="hero-tiled-backdrop">
      <div 
        class="hero-tiled-bg" 
        :style="{ backgroundImage: `url(${userAvatar})` }"
      ></div>
      <div class="hero-tiled-overlay"></div>
    </div>
    <div v-else class="hero-fallback-backdrop" :style="avatarGradientStyle">
      <span class="fallback-backdrop-initials">{{ initials }}</span>
    </div>

    <!-- Top-right absolute share button -->
    <button class="hero-share-corner-btn" @click="$emit('share')" title="Поделиться профилем">
      <Share2 :size="18" />
    </button>

    <!-- ═══ 1. LEFT COLUMN: Monolithic Unified Tabs Unit ═══ -->
    <nav class="hero-monolith-tabs" aria-label="Разделы профиля">
      <!-- Overview -->
      <button
        class="monolith-tab-btn"
        :class="{ active: activeTab === 'overview' }"
        @click="$emit('selectTab', 'overview')"
        title="Обзор медиатеки"
      >
        <span class="tab-edge-icon"><Sparkles :size="16" /></span>
        <span class="tab-edge-divider"></span>
        <span class="tab-edge-label">Обзор</span>
      </button>

      <!-- Tracks -->
      <button
        class="monolith-tab-btn"
        :class="{ active: activeTab === 'tracks' }"
        @click="$emit('selectTab', 'tracks')"
        title="Треки"
      >
        <span class="tab-edge-icon"><Music :size="16" /></span>
        <span class="tab-edge-divider"></span>
        <span class="tab-edge-label">Треки</span>
        <span v-if="user.track_count > 0" class="tab-edge-badge">{{ user.track_count }}</span>
      </button>

      <!-- Playlists -->
      <button
        class="monolith-tab-btn"
        :class="{ active: activeTab === 'playlists' }"
        @click="$emit('selectTab', 'playlists')"
        title="Плейлисты"
      >
        <span class="tab-edge-icon"><Folder :size="16" /></span>
        <span class="tab-edge-divider"></span>
        <span class="tab-edge-label">Плейлисты</span>
        <span v-if="user.playlist_count > 0" class="tab-edge-badge">{{ user.playlist_count }}</span>
      </button>

      <!-- Albums -->
      <button
        v-if="overviewAlbumsCount > 0 || activeTab === 'albums'"
        class="monolith-tab-btn"
        :class="{ active: activeTab === 'albums' }"
        @click="$emit('selectTab', 'albums')"
        title="Альбомы"
      >
        <span class="tab-edge-icon"><Disc3 :size="16" /></span>
        <span class="tab-edge-divider"></span>
        <span class="tab-edge-label">Альбомы</span>
        <span v-if="overviewAlbumsCount > 0" class="tab-edge-badge">{{ overviewAlbumsCount }}</span>
      </button>

      <!-- SoundCloud Tab -->
      <button
        v-if="scAccount && (scAccount.show_playlists || scAccount.show_tracks || isSelf)"
        class="monolith-tab-btn sc-tab"
        :class="{ active: activeTab === 'soundcloud' }"
        @click="$emit('selectTab', 'soundcloud')"
        title="SoundCloud"
      >
        <span class="tab-edge-icon sc-badge-inline">SC</span>
        <span class="tab-edge-divider"></span>
        <span class="tab-edge-label">SoundCloud</span>
        <span v-if="scPlaylistsCount + scTracksCount > 0" class="tab-edge-badge sc-badge-num">
          {{ scPlaylistsCount + scTracksCount }}
        </span>
      </button>
    </nav>

    <!-- ═══ 2. CENTER COLUMN: User Identity & Actions ═══ -->
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
        <span v-if="user.username && (scAccount || spAccount)" class="stat-separator">•</span>

        <!-- External Connected Accounts Badges -->
        <template v-if="scAccount && (isSelf || scAccount.show_on_profile !== false)">
          <a 
            class="hero-ext-badge sc-badge" 
            :href="getSoundCloudUrl(scAccount)" 
            target="_blank" 
            rel="noopener noreferrer" 
            :title="`SoundCloud: @${scAccount.username}${scAccount.likes_count ? ' • ' + scAccount.likes_count + ' лайков' : ''}`"
          >
            <span class="sc-badge-inline">SC</span>
            <span class="ext-badge-name">{{ scAccount.username }}</span>
            <ExternalLink :size="10" class="ext-badge-direct-link" />
          </a>
        </template>

        <template v-if="spAccount && (isSelf || spAccount.show_on_profile !== false)">
          <span v-if="scAccount && (isSelf || scAccount.show_on_profile !== false)" class="stat-separator">•</span>
          <a 
            class="hero-ext-badge sp-badge" 
            :href="getSpotifyUrl(spAccount)" 
            target="_blank" 
            rel="noopener noreferrer" 
            title="Открыть профиль на Spotify"
          >
            <Radio :size="12" class="sp-icon-inline" />
            <span class="ext-badge-name">Spotify</span>
            <ExternalLink :size="10" class="ext-badge-direct-link" />
          </a>
        </template>
      </div>

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

    <!-- ═══ 3. RIGHT COLUMN: Informative Tab Details Panel ═══ -->
    <aside class="hero-tab-details-panel" aria-label="Детали раздела">
      <!-- Overview Tab Details -->
      <div v-if="activeTab === 'overview'" class="tab-panel-inner tab-panel-overview">
        <div class="panel-header">
          <Sparkles :size="13" class="panel-header-icon" />
          <span class="panel-header-title">Сводка медиатеки</span>
        </div>
        <div class="panel-stats-grid">
          <button class="panel-stat-cell" @click="$emit('selectTab', 'tracks')" title="Смотреть треки">
            <span class="panel-stat-num">{{ user.track_count }}</span>
            <span class="panel-stat-lbl">{{ getTracksWord(user.track_count) }}</span>
          </button>
          <button class="panel-stat-cell" @click="$emit('selectTab', 'playlists')" title="Смотреть плейлисты">
            <span class="panel-stat-num">{{ user.playlist_count }}</span>
            <span class="panel-stat-lbl">{{ getPlaylistsWord(user.playlist_count) }}</span>
          </button>
          <button v-if="overviewAlbumsCount > 0" class="panel-stat-cell" @click="$emit('selectTab', 'albums')" title="Смотреть альбомы">
            <span class="panel-stat-num">{{ overviewAlbumsCount }}</span>
            <span class="panel-stat-lbl">альбомов</span>
          </button>
          <div 
            class="panel-stat-cell" 
            :class="{ 'is-clickable': isSelf }"
            @click="isSelf && $router.push('/friends')"
            :title="isSelf ? 'Перейти к кентам' : ''"
          >
            <span class="panel-stat-num">{{ user.followers_count }}</span>
            <span class="panel-stat-lbl">подписчиков</span>
          </div>
        </div>
      </div>

      <!-- Tracks Tab Details -->
      <div v-else-if="activeTab === 'tracks'" class="tab-panel-inner tab-panel-tracks">
        <div class="panel-header">
          <Music :size="13" class="panel-header-icon" />
          <span class="panel-header-title">Медиатека треков</span>
        </div>
        <div class="panel-highlight-row">
          <span class="panel-big-num">{{ user.track_count }}</span>
          <span class="panel-big-lbl">{{ getTracksWord(user.track_count) }} в базе</span>
        </div>
        <div class="panel-quick-actions" v-if="user.track_count > 0">
          <button class="panel-action-btn primary" @click="$emit('play')" title="Слушать с начала">
            <Play :size="13" fill="currentColor" />
            <span>Слушать</span>
          </button>
          <button v-if="user.track_count > 1" class="panel-action-btn" @click="$emit('shuffle')" title="Перемешать">
            <Shuffle :size="13" />
            <span>Микс</span>
          </button>
        </div>
      </div>

      <!-- Playlists Tab Details -->
      <div v-else-if="activeTab === 'playlists'" class="tab-panel-inner tab-panel-playlists">
        <div class="panel-header">
          <Folder :size="13" class="panel-header-icon" />
          <span class="panel-header-title">Плейлисты</span>
        </div>
        <div class="panel-highlight-row">
          <span class="panel-big-num">{{ user.playlist_count }}</span>
          <span class="panel-big-lbl">{{ getPlaylistsWord(user.playlist_count) }} профиля</span>
        </div>
        <div class="panel-sub-desc">
          <span>Персональные и публичные подборки треков</span>
        </div>
      </div>

      <!-- Albums Tab Details -->
      <div v-else-if="activeTab === 'albums'" class="tab-panel-inner tab-panel-albums">
        <div class="panel-header">
          <Disc3 :size="13" class="panel-header-icon" />
          <span class="panel-header-title">Альбомы</span>
        </div>
        <div class="panel-highlight-row">
          <span class="panel-big-num">{{ overviewAlbumsCount }}</span>
          <span class="panel-big-lbl">сохраненных релизов</span>
        </div>
        <div class="panel-sub-desc">
          <span>Дискография и релизы исполнителей</span>
        </div>
      </div>

      <!-- SoundCloud Tab Details -->
      <div v-else-if="activeTab === 'soundcloud'" class="tab-panel-inner tab-panel-sc">
        <div class="panel-header sc-color">
          <span class="sc-badge-inline">SC</span>
          <span class="panel-header-title">SoundCloud</span>
        </div>
        <div class="panel-highlight-row" v-if="scAccount">
          <span class="panel-sc-user">@{{ scAccount.username }}</span>
        </div>
        <div class="panel-sc-counts">
          <span>{{ scTracksCount }} треков</span>
          <span class="stat-separator">•</span>
          <span>{{ scPlaylistsCount }} плейлистов</span>
        </div>
        <a 
          v-if="scAccount" 
          :href="getSoundCloudUrl(scAccount)" 
          target="_blank" 
          rel="noopener noreferrer" 
          class="panel-sc-link-btn"
          title="Открыть профиль SoundCloud"
        >
          <span>В SoundCloud</span>
          <ExternalLink :size="11" />
        </a>
      </div>
    </aside>
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
  ExternalLink,
  Sparkles,
  Music,
  Folder,
  Disc3,
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
  activeTab: { type: String, default: 'overview' },
  overviewAlbumsCount: { type: Number, default: 0 },
  scPlaylistsCount: { type: Number, default: 0 },
  scTracksCount: { type: Number, default: 0 },
})

defineEmits(['play', 'shuffle', 'follow', 'edit', 'share', 'selectTab'])

const ensureAbsoluteUrl = (url, fallback) => {
  if (!url) return fallback
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  return `https://${url}`
}

const getSoundCloudUrl = (acc) => {
  if (!acc) return '#'
  const raw = acc.profile_url || acc.permalink_url || (acc.username ? `https://soundcloud.com/${acc.username}` : 'https://soundcloud.com')
  return ensureAbsoluteUrl(raw, 'https://soundcloud.com')
}

const getSpotifyUrl = (acc) => {
  if (!acc) return '#'
  const raw = acc.profile_url || acc.permalink_url || (acc.username ? `https://open.spotify.com/user/${acc.username}` : 'https://open.spotify.com')
  return ensureAbsoluteUrl(raw, 'https://open.spotify.com')
}
</script>

<style scoped>
/* ─── Profile Hero Card Container ─── */
.profile-hero-card {
  position: relative;
  overflow: hidden;
  border-radius: var(--r-xl, 24px);
  background: var(--c-bg-2, #181818);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 0 28px 0 0;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 28px;
}

/* Ambient glow */
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

/* ─── Tiled Avatar Backdrop (Windows Wallpaper Tile Style) ─── */
.hero-tiled-backdrop {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.hero-tiled-bg {
  position: absolute;
  inset: 0;
  background-repeat: repeat;
  background-size: 160px 160px;
  background-position: center center;
  filter: brightness(0.72) saturate(1.15);
  opacity: 0.95;
}

.hero-tiled-overlay {
  position: absolute;
  inset: 0;
  background: 
    radial-gradient(
      ellipse 70% 70% at center,
      rgba(15, 15, 20, 0.06) 0%,
      rgba(15, 15, 20, 0.32) 50%,
      rgba(15, 15, 20, 0.8) 100%
    ),
    linear-gradient(
      180deg,
      rgba(18, 18, 24, 0.1) 0%,
      transparent 35%,
      transparent 65%,
      rgba(18, 18, 24, 0.45) 100%
    );
}

.hero-fallback-backdrop {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.3;
}

.fallback-backdrop-initials {
  font-size: 96px;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.12);
  user-select: none;
}

/* Top-right share button */
.hero-share-corner-btn {
  position: absolute;
  top: 18px;
  right: 18px;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: rgba(22, 22, 26, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--c-text-2, #aaa);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 4;
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.hero-share-corner-btn:hover {
  color: #fff;
  background: rgba(40, 40, 48, 0.85);
  border-color: rgba(255, 255, 255, 0.25);
  transform: scale(1.06);
}

/* ═══════════════════════════════════════════════════════════
   1. LEFT COLUMN: Monolithic Unified Control Unit (Stretched to Edges)
   ═══════════════════════════════════════════════════════════ */
.hero-monolith-tabs {
  position: relative;
  z-index: 2;
  width: 215px;
  min-width: 215px;
  max-width: 215px;
  flex: 0 0 215px;
  align-self: stretch;
  display: flex;
  flex-direction: column;
  background: rgba(10, 10, 14, 0.82);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: var(--r-xl, 24px) 0 0 var(--r-xl, 24px);
  border: none;
  border-right: 1px solid rgba(255, 255, 255, 0.09);
  padding: 0;
  gap: 0;
  overflow: hidden;
  box-shadow: 
    6px 0 20px rgba(0, 0, 0, 0.4),
    inset -1px 0 0 rgba(255, 255, 255, 0.03);
}

.monolith-tab-btn {
  display: flex;
  align-items: center;
  flex: 1;
  width: 100%;
  min-height: 40px;
  padding: 0 16px 0 14px;
  border-radius: 0;
  background: transparent;
  border: none;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  border-left: 4px solid transparent;
  color: var(--c-text-2, #aaa);
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  text-align: left;
  user-select: none;
  transition: all 0.18s cubic-bezier(0.2, 0.8, 0.2, 1);
  position: relative;
  outline: none;
  -webkit-tap-highlight-color: transparent;
}

.monolith-tab-btn:focus,
.monolith-tab-btn:focus-visible {
  outline: none;
}

.monolith-tab-btn:last-child {
  border-bottom: none;
}

.monolith-tab-btn:hover:not(.active) {
  background: rgba(255, 255, 255, 0.04);
  color: var(--c-text-1, #ffffff);
  border-left-color: rgba(255, 255, 255, 0.3);
}

.monolith-tab-btn.active {
  background: linear-gradient(90deg, rgba(29, 185, 84, 0.16) 0%, rgba(24, 24, 30, 0.85) 50%, rgba(14, 14, 18, 0.85) 100%);
  border-left: 4px solid var(--c-accent, #1db954);
  color: #ffffff;
  font-weight: 600;
  box-shadow: 
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    inset 0 -1px 0 rgba(0, 0, 0, 0.4);
}

.tab-edge-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: var(--c-text-3, #888);
  transition: color 0.15s, transform 0.15s;
}

.monolith-tab-btn.active .tab-edge-icon {
  color: var(--c-accent, #1db954);
  transform: scale(1.05);
}

.tab-edge-divider {
  width: 1px;
  height: 16px;
  background: rgba(255, 255, 255, 0.08);
  margin: 0 10px;
  flex-shrink: 0;
  transition: background 0.15s, box-shadow 0.15s;
}

.monolith-tab-btn.active .tab-edge-divider {
  background: var(--c-accent, #1db954);
  box-shadow: 0 0 8px var(--c-accent-glow, rgba(29, 185, 84, 0.5));
}

.tab-edge-label {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tab-edge-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 1.5px 7px;
  border-radius: var(--r-full, 9999px);
  background: rgba(255, 255, 255, 0.07);
  color: var(--c-text-3, #999);
  margin-left: 6px;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.monolith-tab-btn.active .tab-edge-badge {
  background: rgba(29, 185, 84, 0.18);
  color: var(--c-accent, #1db954);
  border-color: rgba(29, 185, 84, 0.35);
}

/* SoundCloud Tab Accent */
.monolith-tab-btn.sc-tab.active {
  background: linear-gradient(90deg, rgba(255, 85, 0, 0.18) 0%, rgba(28, 22, 22, 0.85) 50%, rgba(14, 14, 18, 0.85) 100%);
  border-left-color: #ff5500;
  box-shadow: 
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    inset 0 -1px 0 rgba(0, 0, 0, 0.4);
}

.monolith-tab-btn.sc-tab.active .tab-edge-divider {
  background: #ff5500;
  box-shadow: 0 0 8px rgba(255, 85, 0, 0.6);
}

.monolith-tab-btn.sc-tab.active .tab-edge-icon {
  color: #ff5500;
}

.monolith-tab-btn.sc-tab.active .tab-edge-badge {
  background: rgba(255, 85, 0, 0.2);
  color: #ff5500;
  border-color: rgba(255, 85, 0, 0.4);
}

/* ═══════════════════════════════════════════════════════════
   2. CENTER COLUMN: User Info, Links & Controls
   ═══════════════════════════════════════════════════════════ */
.hero-body {
  position: relative;
  z-index: 2;
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 24px 0;
  gap: 10px;
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
  font-size: 34px;
  font-weight: 800;
  color: var(--c-text-1, #fff);
  margin: 0;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.025em;
  text-shadow: 0 2px 14px rgba(0, 0, 0, 0.95), 0 0 24px rgba(0, 0, 0, 0.85);
}

.hero-subline {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 13.5px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.85));
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.95), 0 0 16px rgba(0, 0, 0, 0.85);
}

.hero-handle {
  font-size: 13.5px;
  color: var(--c-accent, #1db954);
  font-weight: 600;
}

.stat-separator {
  color: rgba(255, 255, 255, 0.25);
  font-size: 11px;
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
  text-decoration: none;
}

.hero-ext-badge:visited {
  color: var(--c-text-1, #fff);
}

.hero-ext-badge:hover {
  background: rgba(255, 255, 255, 0.14);
  transform: translateY(-1px);
  color: var(--c-text-1, #fff);
  text-decoration: none;
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

.ext-badge-direct-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: inherit;
  opacity: 0.65;
  margin-left: 2px;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.ext-badge-direct-link:hover,
.hero-ext-badge:hover .ext-badge-direct-link {
  opacity: 1;
  transform: scale(1.18);
}

/* Action Buttons Bar */
.hero-actions-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.hero-play-capsule {
  flex-shrink: 0;
}

.hero-pill-btn {
  width: 42px;
  height: 42px;
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

/* ═══════════════════════════════════════════════════════════
   3. RIGHT COLUMN: Informative Tab Details Panel
   ═══════════════════════════════════════════════════════════ */
.hero-tab-details-panel {
  position: relative;
  z-index: 2;
  width: 250px;
  min-width: 250px;
  max-width: 250px;
  flex: 0 0 250px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-self: center;
  margin: 20px 0;
  background: rgba(18, 18, 22, 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--r-lg, 16px);
  padding: 14px 16px;
  box-shadow: 
    inset 1px 1px 3px var(--sh-inset-dark, rgba(0, 0, 0, 0.5)), 
    inset -1px -1px 2px var(--sh-inset-light, rgba(255, 255, 255, 0.03));
}

.tab-panel-inner {
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--c-text-3, #777);
  margin-bottom: 8px;
}

.panel-header-icon {
  color: var(--c-accent, #1db954);
  flex-shrink: 0;
}

.panel-header.sc-color .panel-header-icon {
  color: #ff5500;
}

.panel-stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.panel-stat-cell {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: var(--r-sm, 8px);
  padding: 5px 8px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
  cursor: pointer;
  color: inherit;
  transition: all 0.15s ease;
}

.panel-stat-cell:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.12);
  transform: translateY(-1px);
}

.panel-stat-num {
  font-size: 15px;
  font-weight: 800;
  color: var(--c-text-1, #fff);
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.panel-stat-lbl {
  font-size: 10.5px;
  color: var(--c-text-3, #888);
  margin-top: 1px;
}

.panel-highlight-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.panel-big-num {
  font-size: 26px;
  font-weight: 800;
  color: var(--c-text-1, #fff);
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

.panel-big-lbl {
  font-size: 12.5px;
  color: var(--c-text-2, #aaa);
}

.panel-quick-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.panel-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 30px;
  padding: 0 12px;
  border-radius: var(--r-full, 9999px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.06);
  color: var(--c-text-1, #fff);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.panel-action-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.panel-action-btn.primary {
  background: var(--c-accent, #1db954);
  color: #000;
  border-color: var(--c-accent, #1db954);
  font-weight: 700;
}

.panel-action-btn.primary:hover {
  background: var(--c-accent-light, #1ed760);
  box-shadow: 0 2px 10px var(--c-accent-glow, rgba(29, 185, 84, 0.4));
}

.panel-sub-desc {
  font-size: 12px;
  color: var(--c-text-3, #777);
  margin-top: 6px;
  line-height: 1.35;
}

.panel-sc-user {
  font-size: 15px;
  font-weight: 700;
  color: #ff5500;
}

.panel-sc-counts {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--c-text-2, #aaa);
  margin-top: 4px;
}

.panel-sc-link-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 30px;
  padding: 0 12px;
  border-radius: var(--r-full, 9999px);
  background: #ff5500;
  color: #fff;
  font-size: 11.5px;
  font-weight: 700;
  text-decoration: none;
  margin-top: 10px;
  transition: all 0.15s ease;
  width: fit-content;
}

.panel-sc-link-btn:hover {
  opacity: 0.92;
  transform: translateY(-1px);
  color: #fff;
}

/* ═══════════════════════════════════════════════════════════
   RESPONSIVE LAYOUT
   ═══════════════════════════════════════════════════════════ */
@media (max-width: 1080px) {
  .hero-tab-details-panel {
    width: 220px;
    min-width: 220px;
    max-width: 220px;
    flex: 0 0 220px;
    padding: 12px 14px;
  }

  .hero-monolith-tabs {
    width: 185px;
    min-width: 185px;
    max-width: 185px;
    flex: 0 0 185px;
  }

  .hero-name {
    font-size: 28px;
  }
}

@media (max-width: 860px) {
  .profile-hero-card {
    display: grid;
    grid-template-columns: 48px 1fr;
    grid-template-areas:
      "tabs body"
      "details details";
    gap: 0;
    padding: 0;
    align-items: stretch;
  }

  .hero-monolith-tabs {
    grid-area: tabs;
    width: 48px !important;
    min-width: 48px !important;
    max-width: 48px !important;
    flex: 0 0 48px !important;
    height: 100%;
    align-self: stretch;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    border-radius: var(--r-xl, 24px) 0 0 0;
    border: none;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    border-bottom: none;
    padding: 0;
    gap: 0;
    overflow: hidden;
  }

  .monolith-tab-btn {
    flex: 0 0 42px !important;
    width: 100% !important;
    height: 42px !important;
    min-height: 42px !important;
    max-height: 42px !important;
    padding: 0 !important;
    justify-content: center;
    align-items: center;
    border-radius: 0;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    border-left: 3.5px solid transparent;
    box-sizing: border-box;
  }

  .monolith-tab-btn:last-child {
    border-bottom: none;
  }

  .monolith-tab-btn.active {
    border-left: 3.5px solid var(--c-accent, #1db954);
    background: linear-gradient(90deg, rgba(29, 185, 84, 0.2) 0%, rgba(24, 24, 30, 0.8) 100%);
  }

  .monolith-tab-btn.sc-tab.active {
    border-left-color: #ff5500;
    background: linear-gradient(90deg, rgba(255, 85, 0, 0.22) 0%, rgba(28, 22, 22, 0.8) 100%);
  }

  .monolith-tab-btn.sc-tab .tab-edge-icon {
    width: auto;
    height: auto;
  }

  .monolith-tab-btn.sc-tab .sc-badge-inline {
    padding: 1px 4px;
    font-size: 9px;
  }

  .tab-edge-divider,
  .tab-edge-label,
  .tab-edge-badge {
    display: none !important;
  }

  .tab-edge-icon {
    width: 20px;
    height: 20px;
    margin: 0;
  }

  .hero-body {
    grid-area: body;
    min-width: 0;
    align-items: flex-start;
    text-align: left;
    padding: 16px 44px 16px 14px;
    gap: 8px;
  }

  .hero-meta-top,
  .hero-subline,
  .hero-actions-bar {
    justify-content: flex-start;
  }

  .hero-name {
    font-size: 24px;
  }

  /* Mobile details overlay - uniform seamless bottom panel */
  .hero-tab-details-panel {
    grid-area: details;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    flex: none !important;
    margin: 0;
    border: none;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 0 0 var(--r-xl, 24px) var(--r-xl, 24px);
    background: linear-gradient(180deg, rgba(14, 14, 18, 0.82) 0%, rgba(10, 10, 14, 0.94) 100%);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: none;
    padding: 12px 16px;
    align-self: stretch;
    min-height: 84px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .hero-tab-details-panel .tab-panel-inner {
    display: flex;
    flex-direction: column;
    justify-content: center;
    width: 100%;
  }

  .hero-tab-details-panel .panel-header {
    margin-bottom: 6px;
  }

  .hero-tab-details-panel .panel-stats-grid {
    grid-template-columns: repeat(4, 1fr) !important;
    gap: 6px;
  }

  .hero-tab-details-panel .panel-stat-cell {
    padding: 4px 6px;
    align-items: center;
    text-align: center;
  }

  .hero-tab-details-panel .panel-stat-num {
    font-size: 14px;
  }

  .hero-tab-details-panel .panel-stat-lbl {
    font-size: 10px;
  }

  .hero-tab-details-panel .panel-highlight-row {
    flex-direction: row;
    align-items: baseline;
    gap: 8px;
    flex-wrap: wrap;
  }

  .hero-tab-details-panel .panel-big-num {
    font-size: 22px;
  }

  .hero-tab-details-panel .panel-big-lbl {
    font-size: 13px;
  }

  .hero-tab-details-panel .panel-sub-desc {
    margin-top: 3px;
    font-size: 11.5px;
  }

  .hero-tab-details-panel .panel-quick-actions {
    margin-top: 6px;
    gap: 6px;
  }

  .hero-tab-details-panel .panel-action-btn {
    height: 26px;
    padding: 0 10px;
    font-size: 11.5px;
  }

  .hero-tab-details-panel .tab-panel-sc .panel-sc-counts {
    margin-top: 2px;
  }

  .hero-tab-details-panel .panel-sc-link-btn {
    align-self: flex-start;
    height: 26px;
    padding: 0 10px;
    font-size: 11px;
    margin-top: 4px;
  }

  .hero-share-corner-btn {
    top: 14px;
    right: 14px;
    width: 34px;
    height: 34px;
  }

  .hero-actions-bar {
    gap: 8px;
  }
}

@media (max-width: 480px) {
  .profile-hero-card {
    grid-template-columns: 44px 1fr;
  }

  .hero-monolith-tabs {
    width: 44px !important;
    min-width: 44px !important;
    max-width: 44px !important;
    flex: 0 0 44px !important;
    padding: 0;
    gap: 0;
  }

  .monolith-tab-btn {
    flex: 0 0 40px !important;
    height: 40px !important;
    min-height: 40px !important;
    max-height: 40px !important;
    border-radius: 0;
  }

  .hero-name {
    font-size: 22px;
  }

  .hero-body {
    padding: 14px 40px 14px 10px;
    gap: 6px;
  }

  .hero-tab-details-panel {
    padding: 10px 12px;
    min-height: 80px;
  }

  .hero-tab-details-panel .panel-stats-grid {
    grid-template-columns: repeat(4, 1fr) !important;
    gap: 4px;
  }

  .hero-tab-details-panel .panel-stat-cell {
    padding: 3px 4px;
  }

  .hero-tab-details-panel .panel-stat-num {
    font-size: 13px;
  }

  .hero-tab-details-panel .panel-stat-lbl {
    font-size: 9.5px;
  }
}
</style>
