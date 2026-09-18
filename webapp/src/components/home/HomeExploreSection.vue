<template>
  <section class="home-explore-section">
    <!-- Header -->
    <div class="explore-section-header">
      <div class="header-left">
        <div class="header-icon-box">
          <Compass :size="20" class="explore-main-icon" />
        </div>
        <div>
          <h2 class="explore-title">Обзор по жанрам</h2>
          <p class="explore-subtitle">Открывайте новое звучание или запускайте мгновенный микс</p>
        </div>
      </div>

      <!-- Scope Switcher (My Library vs Global) -->
      <div class="scope-toggle">
        <button 
          class="scope-btn" 
          :class="{ active: currentScope === 'library' }"
          @click="setScope('library')"
        >
          Моя музыка
        </button>
        <button 
          class="scope-btn" 
          :class="{ active: currentScope === 'global' }"
          @click="setScope('global')"
        >
          Каталог AuxBass
        </button>
      </div>
    </div>

    <!-- Quick Vibes / Mood Pills Row -->
    <div class="mood-pills-row">
      <button 
        v-for="mood in moodPresets" 
        :key="mood.id"
        class="mood-pill"
        @click="handleMoodClick(mood)"
      >
        <span class="mood-emoji">{{ mood.emoji }}</span>
        <span class="mood-label">{{ mood.label }}</span>
        <Play :size="12" class="mood-play-icon" fill="currentColor" />
      </button>
    </div>

    <!-- Skeletons when loading genres -->
    <div v-if="loadingGenres && displayGenres.length === 0" class="genres-grid">
      <div v-for="i in 8" :key="i" class="genre-card-skeleton">
        <div class="skeleton-title"></div>
        <div class="skeleton-sub"></div>
      </div>
    </div>

    <!-- Genres Cards Grid -->
    <div v-else class="genres-grid">
      <div 
        v-for="genre in displayGenres" 
        :key="genre.name"
        class="genre-card"
        :style="{ background: getGenreGradient(genre.name) }"
        @click="goToGenreSearch(genre.name)"
      >
        <!-- Card Text Info -->
        <div class="genre-info">
          <h3 class="genre-name">{{ formatGenreTitle(genre.name) }}</h3>
          <span v-if="genre.track_count > 0" class="genre-count">
            {{ genre.track_count }} {{ formatTrackCount(genre.track_count) }}
          </span>
        </div>

        <!-- Rotated Cover Artwork (Spotify style) -->
        <div class="genre-artwork-wrap">
          <img 
            v-if="genre.cover_url"
            :src="getCoverUrl(genre.cover_url, CoverSize.MEDIUM)" 
            class="genre-artwork-img"
            alt=""
            loading="lazy"
          />
          <div v-else class="genre-artwork-placeholder">
            <Music :size="28" />
          </div>
        </div>

        <!-- Quick Play Mix Button -->
        <button 
          class="genre-play-btn"
          @click.stop="handlePlayGenre(genre.name)"
          title="Слушать микс"
          aria-label="Слушать микс"
        >
          <Play :size="18" fill="currentColor" />
        </button>
      </div>
    </div>

    <!-- Popular Tags Pills (Compact secondary exploration) -->
    <div v-if="cleanTags.length > 0" class="popular-tags-block">
      <div class="tags-block-header">
        <div class="title-with-hash">
          <Hash :size="15" class="hash-icon" />
          <span class="tags-block-title">Популярные теги каталога</span>
        </div>
      </div>
      <div class="tag-chips-list">
        <button 
          v-for="tag in cleanTags" 
          :key="tag.name"
          class="tag-chip-btn"
          @click="goToTagSearch(tag.name)"
        >
          <span class="tag-chip-prefix">#</span>
          <span class="tag-chip-text">{{ tag.name }}</span>
          <span v-if="tag.track_count > 0" class="tag-chip-badge">{{ tag.track_count }}</span>
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Compass, Music, Play, Hash } from 'lucide-vue-next'
import { tracksApi } from '@/api/client'
import { usePlayerStore } from '@/stores/player'
import { useUIStore } from '@/stores/ui'
import { getCoverUrl, CoverSize } from '@/utils'
import api from '@/api/client'

const router = useRouter()
const playerStore = usePlayerStore()
const uiStore = useUIStore()

const currentScope = ref('global')
const loadingGenres = ref(false)
const rawGenres = ref([])
const rawTags = ref([])

// Curated mood presets for quick vibes
const moodPresets = [
  { id: 'drive', emoji: '⚡', label: 'Драйв', tags: ['dubstep', 'phonk', 'dnb'] },
  { id: 'night', emoji: '🌙', label: 'Ночной чилл', tags: ['ambient', 'lo-fi', 'chill'] },
  { id: 'focus', emoji: '🎧', label: 'Фокус & Работа', tags: ['electronic', 'synthwave', 'house'] },
  { id: 'gaming', emoji: '🎮', label: 'Gaming Bass', tags: ['trap', 'riddim', 'breakcore'] },
  { id: 'trends', emoji: '🔥', label: 'Тренды AuxBass', tags: ['popular'] }
]

// Specific curated gradients for well-known genres
const GENRE_GRADIENTS = {
  'dubstep': 'linear-gradient(135deg, #7c3aed 0%, #4f46e5 50%, #1e1b4b 100%)',
  'dnb': 'linear-gradient(135deg, #f59e0b 0%, #d97706 50%, #451a03 100%)',
  'drum & bass': 'linear-gradient(135deg, #f59e0b 0%, #d97706 50%, #451a03 100%)',
  'drum and bass': 'linear-gradient(135deg, #f59e0b 0%, #d97706 50%, #451a03 100%)',
  'phonk': 'linear-gradient(135deg, #c026d3 0%, #86198f 50%, #3b0764 100%)',
  'electronic': 'linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #082f49 100%)',
  'electronica': 'linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #082f49 100%)',
  'edm': 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 50%, #0f172a 100%)',
  'hip-hop': 'linear-gradient(135deg, #e11d48 0%, #9f1239 50%, #4c0519 100%)',
  'hip hop': 'linear-gradient(135deg, #e11d48 0%, #9f1239 50%, #4c0519 100%)',
  'rap': 'linear-gradient(135deg, #e11d48 0%, #9f1239 50%, #4c0519 100%)',
  'cloud rap': 'linear-gradient(135deg, #9333ea 0%, #7e22ce 50%, #3b0764 100%)',
  'rock': 'linear-gradient(135deg, #dc2626 0%, #991b1b 50%, #450a0a 100%)',
  'house': 'linear-gradient(135deg, #059669 0%, #047857 50%, #022c22 100%)',
  'dance': 'linear-gradient(135deg, #10b981 0%, #059669 50%, #064e3b 100%)',
  'ambient': 'linear-gradient(135deg, #0d9488 0%, #0f766e 50%, #134e4a 100%)',
  'lo-fi': 'linear-gradient(135deg, #0284c7 0%, #0e7490 50%, #164e63 100%)',
  'trap': 'linear-gradient(135deg, #ea580c 0%, #c2410c 50%, #431407 100%)',
  'synthwave': 'linear-gradient(135deg, #db2777 0%, #9333ea 50%, #311042 100%)',
  'breakcore': 'linear-gradient(135deg, #475569 0%, #334155 50%, #0f172a 100%)',
  'riddim': 'linear-gradient(135deg, #f97316 0%, #c2410c 50%, #3b0764 100%)',
  'brostep': 'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 50%, #2e1065 100%)',
  'neurofunk': 'linear-gradient(135deg, #d97706 0%, #b45309 50%, #1c1917 100%)',
}

const getGenreGradient = (name) => {
  const norm = (name || '').toLowerCase().trim()
  if (GENRE_GRADIENTS[norm]) {
    return GENRE_GRADIENTS[norm]
  }
  // Dynamic harmonious fallback
  let hash = 0
  for (let i = 0; i < norm.length; i++) {
    hash = norm.charCodeAt(i) + ((hash << 5) - hash)
  }
  const h1 = Math.abs(hash % 360)
  const h2 = (h1 + 35) % 360
  return `linear-gradient(135deg, hsl(${h1}, 75%, 42%) 0%, hsl(${h2}, 80%, 26%) 50%, hsl(${h2}, 90%, 14%) 100%)`
}

const formatGenreTitle = (str) => {
  if (!str) return ''
  // Capitalize nicely
  return str.charAt(0).toUpperCase() + str.slice(1)
}

const formatTrackCount = (count) => {
  if (!count) return 'треков'
  const num = count % 100
  if (num >= 11 && num <= 19) return 'треков'
  const last = num % 10
  if (last === 1) return 'трек'
  if (last >= 2 && last <= 4) return 'трека'
  return 'треков'
}

// Fallback top genres if database has very few enrichments yet
const FALLBACK_GENRES = [
  { name: 'electronic', track_count: 0 },
  { name: 'dubstep', track_count: 0 },
  { name: 'phonk', track_count: 0 },
  { name: 'dnb', track_count: 0 },
  { name: 'hip-hop', track_count: 0 },
  { name: 'rock', track_count: 0 },
  { name: 'ambient', track_count: 0 },
  { name: 'house', track_count: 0 }
]

const displayGenres = computed(() => {
  if (rawGenres.value.length > 0) {
    // Return top 8-10 genres
    return rawGenres.value.slice(0, 10)
  }
  return FALLBACK_GENRES
})

// Ignored non-musical tags (e.g. countries or duplicate forms)
const IGNORED_TAGS = new Set(['russian', 'british', 'usa', 'uk', 'american', 'german', 'japanese'])

const cleanTags = computed(() => {
  const seen = new Set()
  const result = []

  for (const t of rawTags.value) {
    if (!t || !t.name) continue
    const norm = t.name.toLowerCase().replace(/[\s\-_]+/g, '')
    if (IGNORED_TAGS.has(norm) || seen.has(norm)) continue
    seen.add(norm)
    result.push(t)
    if (result.length >= 14) break
  }

  return result
})

// Loading data
const loadExploreData = async () => {
  loadingGenres.value = true
  try {
    const [genresRes, tagsRes] = await Promise.allSettled([
      tracksApi.getGenres(currentScope.value),
      tracksApi.getTags(currentScope.value, 40)
    ])

    if (genresRes.status === 'fulfilled' && genresRes.value.data?.length) {
      rawGenres.value = genresRes.value.data
    } else if (currentScope.value === 'library') {
      // Fallback to global genres if library has few enriched tracks
      const globalRes = await tracksApi.getGenres('global').catch(() => null)
      if (globalRes?.data?.length) {
        rawGenres.value = globalRes.data
      }
    }

    if (tagsRes.status === 'fulfilled' && tagsRes.value.data?.length) {
      rawTags.value = tagsRes.value.data
    } else if (currentScope.value === 'library') {
      const globalTags = await tracksApi.getTags('global', 40).catch(() => null)
      if (globalTags?.data?.length) {
        rawTags.value = globalTags.data
      }
    }
  } catch (e) {
    console.error('Failed to load explore data for home:', e)
  } finally {
    loadingGenres.value = false
  }
}

const setScope = (scope) => {
  if (currentScope.value === scope) return
  currentScope.value = scope
  loadExploreData()
}

// Actions
const goToGenreSearch = (genreName) => {
  router.push(`/search?q=%23${encodeURIComponent(genreName)}`)
}

const goToTagSearch = (tagName) => {
  router.push(`/search?q=%23${encodeURIComponent(tagName)}`)
}

const handlePlayGenre = async (genreName) => {
  try {
    // 1. Try library mix first
    const libRes = await api.get('/library', { params: { search: `#${genreName}`, per_page: 5 } }).catch(() => null)
    if (libRes?.data?.items?.length) {
      await playerStore.playShuffleAll('library', null, null, { search: `#${genreName}` })
      return
    }

    // 2. Otherwise play from global results for this genre
    const globalRes = await tracksApi.getGlobal({ search: `#${genreName}`, per_page: 30 })
    const items = globalRes.data?.items || []
    if (items.length > 0) {
      playerStore.playTrack(items[0], items, 0)
    } else {
      uiStore.toast?.info('Жанр', `По направлению «${genreName}» треков пока нет`)
    }
  } catch (e) {
    console.error('Failed to play genre mix:', e)
  }
}

const handleMoodClick = async (mood) => {
  if (mood.id === 'trends') {
    try {
      const popRes = await tracksApi.getPopular(30)
      const items = popRes.data || []
      if (items.length > 0) {
        playerStore.playTrack(items[0], items, 0)
      } else {
        router.push('/search')
      }
    } catch (e) {
      router.push('/search')
    }
    return
  }

  // Pick first tag from preset
  const tag = mood.tags[0]
  await handlePlayGenre(tag)
}

onMounted(() => {
  loadExploreData()
})
</script>

<style scoped>
.home-explore-section {
  margin-top: 36px;
  margin-bottom: 36px;
  max-width: var(--content-max-width, 1400px);
  padding-right: var(--content-padding, 16px);
  box-sizing: border-box;
}

/* Header */
.explore-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon-box {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: rgba(29, 185, 84, 0.12);
  border: 1px solid rgba(29, 185, 84, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-accent, #1db954);
}

.explore-title {
  font-size: 22px;
  font-weight: 800;
  color: var(--c-text-1, #fff);
  margin: 0;
  letter-spacing: -0.02em;
}

.explore-subtitle {
  font-size: 13px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  margin: 2px 0 0;
}

/* Scope Toggle */
.scope-toggle {
  display: flex;
  background: rgba(255, 255, 255, 0.06);
  padding: 3px;
  border-radius: 10px;
  gap: 2px;
}

.scope-btn {
  background: transparent;
  border: none;
  color: var(--c-text-3, rgba(255, 255, 255, 0.6));
  font-size: 12px;
  font-weight: 600;
  padding: 5px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.scope-btn.active {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

/* Mood Pills Row */
.mood-pills-row {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scrollbar-width: none;
  padding-bottom: 12px;
  margin-bottom: 12px;
}

.mood-pills-row::-webkit-scrollbar {
  display: none;
}

.mood-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-1, #fff);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.18s ease;
  font-family: inherit;
  user-select: none;
}

.mood-pill:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.mood-pill:hover .mood-play-icon {
  opacity: 1;
  transform: scale(1);
}

.mood-emoji {
  font-size: 14px;
}

.mood-play-icon {
  color: var(--c-accent, #1db954);
  opacity: 0;
  transform: scale(0.6);
  transition: all 0.18s ease;
  margin-left: 2px;
}

/* Genres Grid */
.genres-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

@media (min-width: 640px) {
  .genres-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
  }
}

@media (min-width: 960px) {
  .genres-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }
}

@media (min-width: 1280px) {
  .genres-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
  }
}

/* Genre Card (Spotify Browse Style) */
.genre-card {
  height: 125px;
  border-radius: 12px;
  padding: 16px;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease;
  user-select: none;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.genre-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
}

.genre-card:active {
  transform: scale(0.98);
}

.genre-info {
  z-index: 2;
  position: relative;
  max-width: 65%;
}

.genre-name {
  font-size: 19px;
  font-weight: 800;
  color: #fff;
  margin: 0;
  letter-spacing: -0.02em;
  line-height: 1.15;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  word-break: break-word;
}

.genre-count {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 4px;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
}

/* Rotated Cover Artwork */
.genre-artwork-wrap {
  position: absolute;
  right: -8px;
  bottom: -8px;
  width: 76px;
  height: 76px;
  transform: rotate(20deg);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: -4px 4px 14px rgba(0, 0, 0, 0.45);
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease;
  pointer-events: none;
}

.genre-card:hover .genre-artwork-wrap {
  transform: rotate(14deg) scale(1.08);
  box-shadow: -6px 6px 20px rgba(0, 0, 0, 0.6);
}

.genre-artwork-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.genre-artwork-placeholder {
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.6);
}

/* Quick Play Button */
.genre-play-btn {
  position: absolute;
  left: 14px;
  bottom: 14px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #fff;
  color: #000;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transform: scale(0.8) translateY(6px);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  z-index: 3;
}

.genre-card:hover .genre-play-btn {
  opacity: 1;
  transform: scale(1) translateY(0);
}

.genre-play-btn:hover {
  background: var(--c-accent, #1db954);
  color: #000;
  transform: scale(1.1) !important;
}

/* Skeletons */
.genre-card-skeleton {
  height: 125px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  gap: 8px;
}

.skeleton-title {
  height: 20px;
  width: 60%;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  animation: pulse 1.5s infinite ease-in-out;
}

.skeleton-sub {
  height: 12px;
  width: 35%;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.05);
  animation: pulse 1.5s infinite ease-in-out;
  animation-delay: 0.15s;
}

@keyframes pulse {
  0%, 100% { opacity: 0.35; }
  50% { opacity: 0.75; }
}

/* Popular Tags Block */
.popular-tags-block {
  margin-top: 18px;
  padding: 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.tags-block-header {
  margin-bottom: 12px;
}

.title-with-hash {
  display: flex;
  align-items: center;
  gap: 6px;
}

.hash-icon {
  color: var(--c-accent, #1db954);
}

.tags-block-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--c-text-2, rgba(255, 255, 255, 0.75));
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.tag-chips-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-2, rgba(255, 255, 255, 0.85));
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
  font-family: inherit;
}

.tag-chip-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.18);
  color: #fff;
  transform: translateY(-1px);
}

.tag-chip-prefix {
  color: var(--c-accent, #1db954);
  font-weight: 700;
}

.tag-chip-badge {
  font-size: 10px;
  background: rgba(255, 255, 255, 0.1);
  padding: 1px 5px;
  border-radius: 8px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.6));
}
</style>
