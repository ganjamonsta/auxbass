<template>
  <div class="search-landing-container">
    <!-- 1. Recent Searches (if any exist) -->
    <section v-if="recentSearches && recentSearches.length > 0" class="landing-section recent-section">
      <div class="section-header">
        <div class="title-with-icon">
          <Clock :size="17" class="section-icon text-muted" />
          <h3 class="section-heading">Недавние поиски</h3>
        </div>
        <button class="clear-all-btn" @click="$emit('clearRecent')">
          Очистить
        </button>
      </div>
      <div class="recent-chips">
        <div 
          v-for="item in recentSearches" 
          :key="item"
          class="recent-chip"
          @click="$emit('recentClick', item)"
        >
          <Clock :size="13" class="chip-clock-icon" />
          <span class="chip-text">{{ item }}</span>
          <button 
            class="chip-remove-btn" 
            @click.stop="$emit('removeRecent', item)"
            title="Удалить из истории"
            aria-label="Удалить из истории"
          >
            <X :size="13" />
          </button>
        </div>
      </div>
    </section>

    <!-- 2. Search Sources (Quick Switchers) -->
    <section class="landing-section sources-section">
      <div class="section-header">
        <div class="title-with-icon">
          <Globe :size="17" class="section-icon text-accent" />
          <h3 class="section-heading">Искать в источниках</h3>
        </div>
      </div>
      <div class="sources-grid">
        <!-- SoundCloud -->
        <div class="source-card sc-card" @click="$emit('selectSource', 'soundcloud')">
          <div class="source-icon-wrap sc-icon-wrap">
            <Radio :size="22" />
            <span v-if="scAccount?.connected" class="source-status-badge" title="SoundCloud подключен">
              <Check :size="9" :stroke-width="3.5" />
            </span>
          </div>
          <div class="source-info">
            <div class="source-title-row">
              <span class="source-name">SoundCloud</span>
              <span v-if="scAccount?.connected" class="source-connected-badge" title="Аккаунт подключен">Подключен</span>
            </div>
            <p class="source-desc">
              {{ scAccount?.connected ? 'Поиск, ваши лайки и авторские треки' : 'Поиск по миллионам треков' }}
            </p>
          </div>
          <ArrowRight :size="16" class="source-arrow" />
        </div>

        <!-- Spotify -->
        <div class="source-card sp-card" @click="$emit('selectSource', 'spotify')">
          <div class="source-icon-wrap sp-icon-wrap">
            <Disc3 :size="22" />
            <span v-if="spAccount?.connected" class="source-status-badge" title="Spotify подключен">
              <Check :size="9" :stroke-width="3.5" />
            </span>
          </div>
          <div class="source-info">
            <div class="source-title-row">
              <span class="source-name">Spotify</span>
              <span v-if="spAccount?.connected" class="source-connected-badge" title="Аккаунт подключен">Подключен</span>
            </div>
            <p class="source-desc">
              {{ spAccount?.connected ? 'Поиск и перенос любимых треков' : 'Поиск и импорт треков' }}
            </p>
          </div>
          <ArrowRight :size="16" class="source-arrow" />
        </div>

        <!-- YouTube Music -->
        <div class="source-card yt-card" @click="$emit('selectSource', 'youtube')">
          <div class="source-icon-wrap yt-icon-wrap">
            <Play :size="20" fill="currentColor" />
          </div>
          <div class="source-info">
            <div class="source-title-row">
              <span class="source-name">YouTube Music</span>
            </div>
            <p class="source-desc">Поиск аудиотреков и клипов</p>
          </div>
          <ArrowRight :size="16" class="source-arrow" />
        </div>

        <!-- Library (Local Catalog) -->
        <div class="source-card lib-card" @click="$emit('selectSource', 'tracks')">
          <div class="source-icon-wrap lib-icon-wrap">
            <Folder :size="22" />
          </div>
          <div class="source-info">
            <div class="source-title-row">
              <span class="source-name">Моя медиатека</span>
            </div>
            <p class="source-desc">Искать только среди сохранённых треков</p>
          </div>
          <ArrowRight :size="16" class="source-arrow" />
        </div>
      </div>
    </section>

    <!-- 3. Quick Tag Pills (Compact Row) -->
    <section v-if="cleanDisplayTags.length > 0" class="landing-section tags-section">
      <div class="section-header">
        <div class="title-with-icon">
          <Hash :size="17" class="section-icon text-accent" />
          <h3 class="section-heading">Популярные стили</h3>
        </div>
        <div class="tag-scope-mini">
          <button 
            class="scope-mini-btn" 
            :class="{ active: tagScope === 'library' }"
            @click="$emit('switchScope', 'library')"
          >
            Мои
          </button>
          <button 
            class="scope-mini-btn" 
            :class="{ active: tagScope === 'global' }"
            @click="$emit('switchScope', 'global')"
          >
            Все
          </button>
        </div>
      </div>

      <div class="tag-pills-row">
        <button 
          v-for="tag in cleanDisplayTags" 
          :key="tag.name"
          class="tag-pill-btn"
          @click="$emit('tagClick', tag.name)"
        >
          <span class="tag-hash">#</span>
          <span class="tag-label">{{ tag.name }}</span>
          <span v-if="tag.track_count > 0" class="tag-count-badge">{{ tag.track_count }}</span>
        </button>
      </div>
    </section>

    <!-- 4. Handy Search Hints -->
    <div class="search-hints-banner">
      <div class="hint-item">
        <div class="hint-icon-box">
          <Hash :size="14" />
        </div>
        <div class="hint-text">
          <strong>Поиск по тегам:</strong> начните запрос с символа <code class="hint-code">#</code> (например, <code class="hint-code">#phonk</code> или <code class="hint-code">#dubstep</code>), чтобы найти треки по стилю.
        </div>
      </div>
      <div class="hint-item">
        <div class="hint-icon-box">
          <ExternalLink :size="14" />
        </div>
        <div class="hint-text">
          <strong>Быстрый импорт:</strong> вставьте ссылку на трек, альбом или плейлист из <span class="text-white">SoundCloud</span>, <span class="text-white">YouTube</span> или <span class="text-white">Spotify</span> прямо в поисковую строку.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { 
  Clock, 
  X, 
  Globe, 
  Radio, 
  Disc3, 
  Play, 
  Folder, 
  ArrowRight, 
  Hash, 
  ExternalLink,
  Check 
} from 'lucide-vue-next'

const props = defineProps({
  tagScope: {
    type: String,
    default: 'library'
  },
  loadingTags: {
    type: Boolean,
    default: false
  },
  tags: {
    type: Array,
    default: () => []
  },
  displayTags: {
    type: Array,
    default: () => []
  },
  recentSearches: {
    type: Array,
    default: () => []
  },
  scAccount: {
    type: Object,
    default: null
  },
  spAccount: {
    type: Object,
    default: null
  }
})

const emit = defineEmits([
  'switchScope', 
  'tagClick', 
  'recentClick', 
  'removeRecent', 
  'clearRecent',
  'selectSource'
])

// Filter out duplicate and non-musical tags (e.g. country codes, duplicates)
const ignoredTags = new Set(['russian', 'british', 'usa', 'uk', 'american', 'german', 'japanese'])

const cleanDisplayTags = computed(() => {
  const source = (props.tags && props.tags.length > 0) ? props.tags : props.displayTags
  if (!source || source.length === 0) return []

  const seen = new Set()
  const result = []

  for (const t of source) {
    if (!t || !t.name) continue
    const norm = t.name.toLowerCase().replace(/[\s\-_]+/g, '')
    if (ignoredTags.has(norm) || seen.has(norm)) continue
    seen.add(norm)
    result.push(t)
    if (result.length >= 14) break
  }

  return result
})
</script>

<style scoped>
.search-landing-container {
  container-type: inline-size;
  container-name: searchLanding;
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding: 8px 0 32px;
  animation: fadeIn 0.25s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.landing-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Section Header */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-icon {
  flex-shrink: 0;
}

.text-accent {
  color: var(--c-accent, #1db954);
}

.text-muted {
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
}

.section-heading {
  font-size: 15px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  margin: 0;
  letter-spacing: -0.01em;
}

.clear-all-btn {
  background: transparent;
  border: none;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.clear-all-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

/* 1. Recent Searches Chips */
.recent-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.recent-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 6px 10px 6px 12px;
  cursor: pointer;
  transition: all 0.18s ease;
  user-select: none;
}

.recent-chip:hover {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.18);
  transform: translateY(-1px);
}

.recent-chip:active {
  transform: scale(0.98);
}

.chip-clock-icon {
  color: var(--c-text-3, rgba(255, 255, 255, 0.45));
}

.chip-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1, #fff);
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chip-remove-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  cursor: pointer;
  transition: all 0.15s ease;
  padding: 0;
  margin-left: 2px;
}

.chip-remove-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

/* 2. Source Cards */
.sources-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

/* Fallback for viewports */
@media (min-width: 560px) {
  .sources-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}

@media (min-width: 1440px) {
  .sources-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }
}

/* Container queries: adapts to actual available width regardless of sidebar state */
@container searchLanding (min-width: 440px) {
  .sources-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}

@container searchLanding (min-width: 860px) {
  .sources-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }
}

.source-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  overflow: hidden;
  min-width: 0;
}

.source-card::before {
  content: '';
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.sc-card::before {
  background: radial-gradient(circle at top left, rgba(255, 85, 0, 0.15), transparent 70%);
}

.sp-card::before {
  background: radial-gradient(circle at top left, rgba(29, 185, 84, 0.15), transparent 70%);
}

.yt-card::before {
  background: radial-gradient(circle at top left, rgba(255, 0, 0, 0.15), transparent 70%);
}

.lib-card::before {
  background: radial-gradient(circle at top left, rgba(99, 102, 241, 0.15), transparent 70%);
}

.source-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25);
}

.source-card:hover::before {
  opacity: 1;
}

.source-icon-wrap {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.source-status-badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--c-accent, #1db954);
  color: #0b0e14;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--c-bg-1, #121212);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.45);
  z-index: 2;
}

.source-card:hover .source-icon-wrap {
  transform: scale(1.05);
}

.sc-icon-wrap {
  background: rgba(255, 85, 0, 0.15);
  color: #ff5500;
  border: 1px solid rgba(255, 85, 0, 0.25);
}

.sp-icon-wrap {
  background: rgba(29, 185, 84, 0.15);
  color: #1db954;
  border: 1px solid rgba(29, 185, 84, 0.25);
}

.yt-icon-wrap {
  background: rgba(255, 0, 0, 0.15);
  color: #ff3333;
  border: 1px solid rgba(255, 0, 0, 0.25);
}

.lib-icon-wrap {
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8;
  border: 1px solid rgba(99, 102, 241, 0.25);
}

.source-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.source-title-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.source-name {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.source-connected-badge {
  display: inline-flex;
  align-items: center;
  font-size: 10px;
  font-weight: 700;
  color: var(--c-accent, #1db954);
  background: rgba(29, 185, 84, 0.15);
  padding: 1px 6px;
  border-radius: 6px;
  border: 1px solid rgba(29, 185, 84, 0.25);
  flex-shrink: 0;
  white-space: nowrap;
  line-height: 1.4;
}

.source-desc {
  font-size: 11px;
  line-height: 1.35;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  margin: 2px 0 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-arrow {
  color: var(--c-text-3, rgba(255, 255, 255, 0.3));
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.source-card:hover .source-arrow {
  color: #fff;
  transform: translateX(3px);
}

/* On compact/narrow screens or containers, hide the bulky text badge so it never truncates the title */
@container searchLanding (max-width: 680px) {
  .source-connected-badge {
    display: none !important;
  }
}

@media (max-width: 768px) {
  .source-connected-badge {
    display: none !important;
  }
}

/* On wide containers where text badge is displayed, hide the icon badge */
@container searchLanding (min-width: 681px) {
  .source-status-badge {
    display: none;
  }
}

@container searchLanding (max-width: 520px) {
  .source-card {
    padding: 10px 12px;
    gap: 10px;
  }
  .source-icon-wrap {
    width: 36px;
    height: 36px;
  }
  .source-status-badge {
    width: 13px;
    height: 13px;
    bottom: -2px;
    right: -2px;
  }
  .source-arrow {
    display: none;
  }
}

/* 3. Tag Pills */
.tag-scope-mini {
  display: flex;
  background: rgba(255, 255, 255, 0.06);
  padding: 2px;
  border-radius: 8px;
  gap: 2px;
}

.scope-mini-btn {
  background: transparent;
  border: none;
  color: var(--c-text-3, rgba(255, 255, 255, 0.6));
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.scope-mini-btn.active {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.tag-pills-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 7px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-2, rgba(255, 255, 255, 0.85));
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
  font-family: inherit;
}

.tag-pill-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.2);
  color: #fff;
  transform: translateY(-1px);
}

.tag-pill-btn:active {
  transform: scale(0.97);
}

.tag-hash {
  color: var(--c-accent, #1db954);
  font-weight: 700;
}

.tag-count-badge {
  font-size: 10px;
  background: rgba(255, 255, 255, 0.1);
  padding: 1px 6px;
  border-radius: 10px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.6));
  margin-left: 2px;
}

/* 4. Search Hints Banner */
.search-hints-banner {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.025);
  border: 1px dashed rgba(255, 255, 255, 0.08);
}

.hint-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.hint-icon-box {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-accent, #1db954);
  flex-shrink: 0;
  margin-top: 1px;
}

.hint-text {
  font-size: 12px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.55));
  line-height: 1.5;
}

.hint-code {
  background: rgba(255, 255, 255, 0.1);
  padding: 1px 5px;
  border-radius: 4px;
  color: var(--c-accent, #1db954);
  font-family: monospace;
  font-size: 11px;
}

.text-white {
  color: rgba(255, 255, 255, 0.85);
  font-weight: 600;
}
</style>
