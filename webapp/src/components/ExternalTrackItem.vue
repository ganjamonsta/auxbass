<template>
  <div
    class="sc-track-item"
    :class="{ 'sp-item': variant === 'spotify', 'yt-item': variant === 'youtube' }"
    @click="$emit('play', item)"
  >
    <div class="sc-track-cover" :class="{ 'sp-cover': variant === 'spotify', 'yt-cover': variant === 'youtube' }">
      <img
        v-if="item.cover_url && !coverError"
        :src="getCoverUrl(item.cover_url, CoverSize.SMALL)"
        alt=""
        loading="lazy"
        referrerpolicy="no-referrer"
        @error="coverError = true"
      />
      <Music v-else :size="20" class="sc-cover-placeholder" />
      <div v-if="isImporting" class="sc-track-loading">
        <div class="spinner small"></div>
      </div>
      <div v-else class="sc-track-play">
        <Play :size="14" fill="currentColor" />
      </div>
    </div>
    
    <div class="sc-track-info">
      <div class="sc-track-title" :title="item.title">{{ item.title }}</div>
      <div v-if="showBadges" class="sc-track-artist-row">
        <span class="sc-track-artist" :title="item.artist">{{ item.artist }}</span>
        <!-- Badges -->
        <div v-if="isInLibrary || item.in_library || item.in_channel || item.is_chunk || item.already_in_tg" class="sc-track-badges">
          <span v-if="isInLibrary || item.in_library" class="sc-badge-pill in-lib" title="Уже в вашей медиатеке">
            <Check :size="10" /> В медиатеке
          </span>
          <span v-if="item.in_channel" class="sc-badge-pill in-chan" title="Забэкаплен в Telegram-канал">
            <CloudDownload :size="10" /> В канале
          </span>
          <span v-else-if="item.is_chunk" class="sc-badge-pill in-chunk" title="Быстрое 30-секундное превью">
            ✂️ 30s превью
          </span>
          <span v-else-if="item.already_in_tg" class="sc-badge-pill in-tg" title="Уже есть на сервере Telegram">
            В базе TG
          </span>
        </div>
      </div>
      <div v-else class="sc-track-artist" :title="item.artist">{{ item.artist }}</div>
    </div>
    
    <div class="sc-track-actions">
      <span v-if="item.duration" class="sc-track-duration">{{ formatDuration(item.duration) }}</span>
      <button 
        v-if="!isInLibrary"
        class="sc-add-btn" 
        :class="{ 
          'sp-add': variant === 'spotify',
          'yt-add': variant === 'youtube',
          loading: isDownloading,
          queued: isQueued
        }"
        :disabled="isDownloading || isQueued"
        @click.stop="$emit('add', item)"
        :title="isDownloading ? 'Загружается...' : isQueued ? 'В очереди на добавление' : 'Добавить в медиатеку'"
      >
        <div v-if="isDownloading" class="spinner micro"></div>
        <Clock v-else-if="isQueued" :size="15" />
        <Plus v-else :size="15" />
      </button>
      <span v-else class="sc-added-badge" title="Уже в медиатеке">
        <Check :size="16" />
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Music, Play, Check, CloudDownload, Clock, Plus } from 'lucide-vue-next'
import { formatDuration, getCoverUrl, CoverSize } from '@/utils'

defineProps({
  item: {
    type: Object,
    required: true
  },
  variant: {
    type: String,
    default: 'soundcloud', // 'soundcloud' | 'spotify' | 'youtube'
  },
  showBadges: {
    type: Boolean,
    default: false
  },
  isImporting: {
    type: Boolean,
    default: false
  },
  isDownloading: {
    type: Boolean,
    default: false
  },
  isQueued: {
    type: Boolean,
    default: false
  },
  isInLibrary: {
    type: Boolean,
    default: false
  }
})

defineEmits(['play', 'add'])

const coverError = ref(false)
</script>

<style scoped>
.sc-track-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  user-select: none;
  min-width: 0;
}

.sc-track-item:hover {
  background: rgba(255, 85, 0, 0.08);
  border-color: rgba(255, 85, 0, 0.25);
  transform: translateX(2px);
}

.sc-track-item.sp-item:hover {
  background: rgba(29, 185, 84, 0.08);
  border-color: rgba(29, 185, 84, 0.25);
}

.sc-track-item.yt-item:hover {
  background: rgba(255, 0, 51, 0.08);
  border-color: rgba(255, 0, 51, 0.25);
}

.sc-track-cover {
  position: relative;
  width: 44px;
  height: 44px;
  min-width: 44px;
  min-height: 44px;
  border-radius: 8px;
  overflow: hidden;
  background: #18181c;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.4);
}

.sc-track-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.sc-cover-placeholder {
  color: rgba(255, 255, 255, 0.35);
}

.sc-track-play {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
  color: #ff5500;
}

.sc-track-item.sp-item .sc-track-play {
  color: #1db954;
}

.sc-track-item:hover .sc-track-play {
  opacity: 1;
}

.sc-track-loading {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
}

.sc-track-loading .spinner {
  border-top-color: #ff5500;
}

.sp-item .sc-track-loading .spinner {
  border-top-color: #1db954;
}

.sc-track-info {
  flex: 1;
  min-width: 0;
}

.sc-track-title {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.sc-track-artist-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 2px;
  min-width: 0;
}

.sc-track-artist {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.sc-track-badges {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.sc-badge-pill {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  letter-spacing: 0.2px;
  line-height: 1.4;
  white-space: nowrap;
}

.sc-badge-pill.in-lib {
  background: rgba(30, 215, 96, 0.15);
  color: #1ed760;
  border: 1px solid rgba(30, 215, 96, 0.3);
}

.sc-badge-pill.in-chan {
  background: rgba(0, 136, 204, 0.15);
  color: #29b6f6;
  border: 1px solid rgba(0, 136, 204, 0.3);
}

.sc-badge-pill.in-chunk {
  background: rgba(234, 179, 8, 0.15);
  color: #facc15;
  border: 1px solid rgba(234, 179, 8, 0.3);
}

.sc-badge-pill.in-tg {
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-3, rgba(255, 255, 255, 0.6));
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.sc-track-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.sc-track-duration {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  font-variant-numeric: tabular-nums;
}

.sc-add-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  padding: 0;
}

.sc-add-btn:hover:not(:disabled) {
  background: #ff5500;
  border-color: #ff5500;
  color: #fff;
  transform: scale(1.05);
}

.sc-add-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.sc-add-btn.loading {
  background: rgba(255, 85, 0, 0.18);
  border-color: rgba(255, 85, 0, 0.45);
  cursor: wait;
}

.sc-add-btn.queued {
  background: rgba(56, 189, 248, 0.16);
  border-color: rgba(56, 189, 248, 0.4);
  color: #38bdf8;
  cursor: default;
}

.sc-add-btn.sp-add:hover:not(:disabled) {
  background: #1db954;
  border-color: #1db954;
  color: #000;
}

.sc-add-btn.sp-add.loading {
  background: rgba(29, 185, 84, 0.18);
  border-color: rgba(29, 185, 84, 0.45);
  cursor: wait;
}

.sc-add-btn.sp-add.queued {
  background: rgba(56, 189, 248, 0.16);
  border-color: rgba(56, 189, 248, 0.4);
  color: #38bdf8;
  cursor: default;
}

.sc-add-btn.yt-add:hover:not(:disabled) {
  background: #ff0033;
  border-color: #ff0033;
  color: #fff;
}

.sc-add-btn.yt-add.loading {
  background: rgba(255, 0, 51, 0.18);
  border-color: rgba(255, 0, 51, 0.45);
  cursor: wait;
}

.sc-add-btn.yt-add.queued {
  background: rgba(56, 189, 248, 0.16);
  border-color: rgba(56, 189, 248, 0.4);
  color: #38bdf8;
  cursor: default;
}

.sc-add-btn .spinner {
  border-color: rgba(255, 255, 255, 0.2);
  border-top-color: #fff;
}

.sc-added-indicator {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1ed760;
  flex-shrink: 0;
}

.spinner.micro {
  width: 14px;
  height: 14px;
  border-width: 1.5px;
}
</style>
