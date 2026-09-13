<template>
  <div class="sp-pane">
    <!-- Spotify Profile Strip -->
    <div v-if="spAccount" class="ext-profile-strip sp-profile-strip">
      <div class="ext-strip-avatar sp-avatar">
        <img v-if="spAccount.avatar_url" :src="spAccount.avatar_url" alt="" referrerpolicy="no-referrer" />
        <Radio v-else :size="32" class="sp-icon-large" />
      </div>
      <div class="ext-strip-info">
        <div class="ext-strip-platform">
          <span class="sp-badge-inline">Spotify</span>
          <span class="ext-verified-badge" title="Подключенный аккаунт">Подключен</span>
        </div>
        <h2 class="ext-strip-name">{{ spAccount.display_name || spAccount.username }}</h2>
        <div class="ext-strip-sub">
          <span class="ext-strip-handle">@{{ spAccount.username }}</span>
          <span v-if="spAccount.permalink_url" class="stat-separator">•</span>
          <a 
            v-if="spAccount.permalink_url" 
            :href="spAccount.permalink_url" 
            target="_blank" 
            rel="noopener noreferrer" 
            class="ext-strip-link"
          >
            <span>Открыть на Spotify</span>
            <ExternalLink :size="13" />
          </a>
        </div>
      </div>
      <div class="ext-strip-stats">
        <div class="ext-stat-box">
          <span class="ext-stat-num">{{ spPlaylists.length }}</span>
          <span class="ext-stat-lbl">плейлистов</span>
        </div>
      </div>
    </div>

    <div class="sp-main-content">
      <div class="section-header">
        <h3 class="section-title">Импортированные плейлисты Spotify</h3>
        <span class="section-badge-pill">{{ spPlaylists.length }}</span>
      </div>

      <div v-if="loadingSpPlaylists" class="loading-container">
        <div class="spinner"></div>
      </div>

      <div v-else-if="spPlaylists.length > 0" class="overview-grid">
        <div 
          v-for="pl in spPlaylists" 
          :key="pl.id" 
          class="feed-card ext-card sp-card"
        >
          <div class="feed-card-cover sp-cover-box">
            <FileSpreadsheet :size="36" class="sp-card-icon" />
          </div>
          <div class="feed-card-info">
            <div class="feed-card-title">{{ pl.title }}</div>
            <div class="feed-card-subtitle">
              {{ pl.track_count }} {{ getTracksWord(pl.track_count) }}
              <span v-if="pl.created_at" class="sp-date">• {{ new Date(pl.created_at).toLocaleDateString() }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="empty-icon"><Radio :size="44" /></div>
        <h3>Нет плейлистов Spotify</h3>
        <p>У пользователя пока нет сохраненных плейлистов из Spotify</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { getTracksWord } from './profileUtils'
import { Radio, ExternalLink, FileSpreadsheet } from 'lucide-vue-next'

defineProps({
  spAccount: { type: Object, default: null },
  spPlaylists: { type: Array, default: () => [] },
  loadingSpPlaylists: { type: Boolean, default: false },
})
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

/* Profile Strip */
.ext-profile-strip {
  position: relative;
  overflow: hidden;
  border-radius: 20px;
  background: var(--c-bg-2, #181818);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 24px 28px;
  margin-bottom: 28px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
  display: flex;
  align-items: center;
  gap: 24px;
}

.sp-profile-strip {
  background: linear-gradient(135deg, rgba(29, 185, 84, 0.08) 0%, rgba(20, 20, 20, 0.8) 100%);
  border-color: rgba(29, 185, 84, 0.2);
}

.ext-strip-avatar {
  width: 80px;
  height: 80px;
  min-width: 80px;
  border-radius: 50%;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ext-strip-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sp-avatar {
  background: rgba(29, 185, 84, 0.1);
  border-color: rgba(29, 185, 84, 0.3);
}

.sp-icon-large {
  color: #1db954;
}

.ext-strip-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ext-strip-platform {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sp-badge-inline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #1db954;
  color: #000;
  font-size: 10px;
  font-weight: 800;
  border-radius: 4px;
  padding: 1px 6px;
  line-height: 1.2;
}

.ext-verified-badge {
  font-size: 11px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  font-weight: 500;
}

.ext-strip-name {
  font-size: 22px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ext-strip-sub {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
}

.ext-strip-handle {
  font-weight: 500;
}

.stat-separator {
  color: rgba(255, 255, 255, 0.25);
  font-size: 11px;
}

.ext-strip-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  text-decoration: none;
  font-size: 12px;
  transition: color 0.2s ease;
}

.ext-strip-link:hover {
  color: var(--c-text-1, #fff);
  text-decoration: underline;
}

.ext-strip-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.ext-stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 8px 16px;
  min-width: 70px;
}

.ext-stat-num {
  font-size: 18px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
}

.ext-stat-lbl {
  font-size: 11px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
}

/* Section */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  font-size: 20px;
  font-weight: 800;
  color: var(--c-text-1, #fff);
  letter-spacing: -0.015em;
}

.section-badge-pill {
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.1);
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
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

.sp-cover-box {
  background: linear-gradient(135deg, rgba(29, 185, 84, 0.2) 0%, rgba(20, 20, 20, 0.8) 100%) !important;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sp-card-icon {
  color: #1db954;
  opacity: 0.8;
}

.sp-date {
  color: var(--c-text-3, rgba(255, 255, 255, 0.4));
  font-size: 11px;
}
</style>
