<template>
  <div
    class="sc-track-item"
    :class="{ 'sp-item': variant === 'spotify' }"
    @click="$emit('play', item)"
  >
    <div class="sc-track-cover" :class="{ 'sp-cover': variant === 'spotify' }">
      <img v-if="item.cover_url" :src="item.cover_url" alt="" loading="lazy" referrerpolicy="no-referrer" />
      <Music v-else :size="20" />
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
        <span class="sc-track-artist">{{ item.artist }}</span>
        <!-- Badges -->
        <div v-if="item.in_library || item.in_channel || item.already_in_tg" class="sc-track-badges">
          <span v-if="item.in_library" class="sc-badge-pill in-lib" title="Уже в вашей медиатеке">
            <Check :size="10" /> В медиатеке
          </span>
          <span v-if="item.in_channel" class="sc-badge-pill in-chan" title="Забэкаплен в Telegram-канал">
            <CloudDownload :size="10" /> В канале
          </span>
          <span v-else-if="item.already_in_tg" class="sc-badge-pill in-tg" title="Уже есть на сервере Telegram">
            В базе TG
          </span>
        </div>
      </div>
      <div v-else class="sc-track-artist">{{ item.artist }}</div>
    </div>
    
    <div class="sc-track-actions">
      <span v-if="item.duration" class="sc-track-duration">{{ formatDuration(item.duration) }}</span>
      <button 
        v-if="!isInLibrary"
        class="sc-add-btn" 
        :class="{ 
          'sp-add': variant === 'spotify',
          loading: isDownloading,
          queued: isQueued
        }"
        :disabled="isDownloading || isQueued"
        @click.stop="$emit('add', item)"
        :title="isDownloading ? 'Загружается...' : isQueued ? 'В очереди на добавление' : 'Добавить в медиатеку'"
      >
        <div v-if="isDownloading" class="spinner micro"></div>
        <Clock v-else-if="isQueued" :size="14" />
        <Plus v-else :size="16" />
      </button>
      <span v-else class="sc-added-indicator" title="Уже в медиатеке">
        <Check :size="16" />
      </span>
    </div>
  </div>
</template>

<script setup>
import { Music, Play, Check, CloudDownload, Clock, Plus } from 'lucide-vue-next'
import { formatDuration } from '@/utils'

defineProps({
  item: {
    type: Object,
    required: true
  },
  variant: {
    type: String,
    default: 'soundcloud', // 'soundcloud' | 'spotify'
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
</script>
