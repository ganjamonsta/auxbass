<template>
  <div class="lyrics-viewer" :class="{ 'embedded': embedded, 'synced-mode': isSyncedView }">
    <!-- Header Controls -->
    <div class="lyrics-header" v-if="!embedded || showHeaderInEmbedded">
      <div class="lyrics-header-left">
        <span class="lyrics-badge" :class="badgeClass">
          <span v-if="lyricsData?.is_instrumental">🎵 Инструментал</span>
          <span v-else-if="parsedLines.length > 0">⚡ Синхронизировано</span>
          <span v-else-if="lyricsData?.plain_lyrics">📝 Обычный текст</span>
          <span v-else>Текст песни</span>
        </span>

        <!-- View Switcher (Synced / Plain) if both or synced available -->
        <div v-if="parsedLines.length > 0 && lyricsData?.plain_lyrics" class="mode-switch">
          <button 
            class="switch-btn" 
            :class="{ active: viewMode === 'synced' }"
            @click="viewMode = 'synced'"
            title="Караоке (синхронизированный текст)"
          >
            Караоке
          </button>
          <button 
            class="switch-btn" 
            :class="{ active: viewMode === 'plain' }"
            @click="viewMode = 'plain'"
            title="Текст целиком"
          >
            Текст
          </button>
        </div>
      </div>

      <div class="lyrics-header-right">
        <!-- Offset adjustment controls for synced mode -->
        <div v-if="isSyncedView && parsedLines.length > 0" class="offset-controls" title="Подстройка синхронизации">
          <button class="offset-btn" @click="adjustOffset(-500)" title="Сдвинуть текст раньше на 0.5с">-0.5s</button>
          <span class="offset-val" v-if="userOffset !== 0">{{ formatOffset(userOffset) }}</span>
          <button class="offset-btn" @click="adjustOffset(500)" title="Сдвинуть текст позже на 0.5с">+0.5s</button>
        </div>

        <!-- Action dropdown / buttons -->
        <button class="action-icon-btn" @click="fetchLyrics(true)" :disabled="loading" title="Обновить текст из сети">
          <svg class="icon" :class="{ 'spin': loading }" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
          </svg>
        </button>
        <button class="action-icon-btn" @click="openSearchModal" title="Поиск текста в сети">
          <svg class="icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
        </button>
        <button class="action-icon-btn" @click="openEditModal" title="Редактировать / добавить вручную">
          <svg class="icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
        </button>
        <button v-if="!embedded" class="action-icon-btn close-btn" @click="$emit('close')" title="Закрыть текст">
          <svg class="icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="lyrics-body" ref="containerRef" @scroll="handleUserScroll" @touchstart="handleTouchStart">
      <!-- Loading State -->
      <div v-if="loading && !lyricsData" class="lyrics-state loading-state">
        <div class="lyrics-spinner">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
            <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
          </svg>
        </div>
        <p class="state-text">Поиск текста песни...</p>
      </div>

      <!-- Instrumental State -->
      <div v-else-if="lyricsData?.is_instrumental" class="lyrics-state instrumental-state">
        <div class="instrumental-icon">
          <div class="note-animation">🎵</div>
          <div class="wave-bars">
            <span v-for="i in 5" :key="i" class="wave-bar" :style="{ animationDelay: `${i * 0.15}s` }"></span>
          </div>
        </div>
        <h3 class="instrumental-title">Инструментальная композиция</h3>
        <p class="state-subtext">Для этого трека не предусмотрен текст</p>
        <button class="secondary-btn" @click="openEditModal">Добавить текст вручную</button>
      </div>

      <!-- Synchronized Karaoke Lyrics -->
      <div v-else-if="isSyncedView && parsedLines.length > 0" class="synced-lyrics-list">
        <div class="lyrics-spacer-top"></div>
        <div 
          v-for="(line, idx) in parsedLines" 
          :key="`line-${idx}`"
          :ref="el => setLineRef(el, idx)"
          class="lyric-line"
          :class="{
            'active': activeLineIndex === idx,
            'passed': activeLineIndex > idx,
            'upcoming': activeLineIndex < idx
          }"
          @click="seekToLine(line)"
        >
          <span class="line-text">{{ line.text || '♪' }}</span>
        </div>
        <div class="lyrics-spacer-bottom"></div>
      </div>

      <!-- Plain Text Lyrics -->
      <div v-else-if="lyricsData?.plain_lyrics" class="plain-lyrics-container">
        <div class="plain-lyrics-text">
          {{ lyricsData.plain_lyrics }}
        </div>
      </div>

      <!-- Not Found / Empty State -->
      <div v-else-if="!loading" class="lyrics-state empty-state">
        <div class="empty-icon">📜</div>
        <h3 class="empty-title">Текст не найден</h3>
        <p class="state-subtext">Вы можете найти его в онлайн-базе или добавить свой текст</p>
        <div class="empty-actions">
          <button class="primary-btn" @click="openSearchModal">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            Найти в сети
          </button>
          <button class="secondary-btn" @click="openEditModal">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 5v14M5 12h14"/>
            </svg>
            Добавить текст
          </button>
        </div>
      </div>
    </div>

    <!-- Floating "Sync" pill when user scrolled away -->
    <Transition name="fade-pill">
      <button 
        v-if="isSyncedView && isUserScrolledAway && activeLineIndex >= 0" 
        class="sync-pill"
        @click="scrollToActiveLine(true)"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/>
        </svg>
        Синхронизировать
      </button>
    </Transition>

    <!-- Manual Edit / Add Modal -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showEditModal" class="lyrics-modal-overlay" @click.self="showEditModal = false">
          <div class="lyrics-modal">
            <div class="modal-header">
              <h3>Редактировать текст</h3>
              <button class="modal-close" @click="showEditModal = false">✕</button>
            </div>
            
            <div class="modal-body">
              <div class="form-checkbox">
                <label>
                  <input type="checkbox" v-model="editForm.is_instrumental" />
                  <span>Инструментальный трек (без слов)</span>
                </label>
              </div>

              <div v-if="!editForm.is_instrumental" class="form-group">
                <div class="label-row">
                  <label>Текст песни (обычный или LRC с таймкодами [mm:ss.xx]):</label>
                  <button type="button" class="text-link-btn" @click="copyEditTemplate">Вставить шаблон</button>
                </div>
                <textarea 
                  v-model="editForm.text" 
                  rows="12" 
                  class="lyrics-textarea"
                  placeholder="Вставьте текст или LRC разметку..."
                ></textarea>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-cancel" @click="showEditModal = false">Отмена</button>
              <button type="button" class="btn-save" :disabled="saving" @click="saveLyrics">
                {{ saving ? 'Сохранение...' : 'Сохранить' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Search in LRCLIB Modal -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showSearchModal" class="lyrics-modal-overlay" @click.self="showSearchModal = false">
          <div class="lyrics-modal search-modal">
            <div class="modal-header">
              <h3>Поиск текста в сети</h3>
              <button class="modal-close" @click="showSearchModal = false">✕</button>
            </div>

            <div class="modal-body">
              <div class="search-input-wrapper">
                <input 
                  v-model="searchQuery" 
                  type="text" 
                  class="search-input" 
                  placeholder="Исполнитель и название трека..."
                  @keyup.enter="performSearch"
                />
                <button class="btn-search" :disabled="searching || !searchQuery.trim()" @click="performSearch">
                  {{ searching ? 'Поиск...' : 'Искать' }}
                </button>
              </div>

              <div class="search-results-list">
                <div v-if="searching" class="results-loading">
                  Поиск в базе LRCLIB...
                </div>
                <div v-else-if="searched && searchResults.length === 0" class="results-empty">
                  Ничего не найдено по запросу
                </div>
                <div 
                  v-for="(res, idx) in searchResults" 
                  :key="`res-${idx}`"
                  class="search-result-item"
                  @click="applySearchResult(res)"
                >
                  <div class="res-info">
                    <div class="res-title">{{ res.trackName || res.name }}</div>
                    <div class="res-artist">{{ res.artistName }} <span v-if="res.albumName">• {{ res.albumName }}</span></div>
                  </div>
                  <div class="res-badges">
                    <span v-if="res.syncedLyrics" class="res-badge synced">LRC Караоке</span>
                    <span v-else-if="res.plainLyrics" class="res-badge plain">Текст</span>
                    <span v-else-if="res.instrumental" class="res-badge inst">Инструментал</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-cancel" @click="showSearchModal = false">Закрыть</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { parseLrc, getActiveLineIndex } from '@/utils/lrcParser'
import { tracksApi } from '@/api/client'
import { useUIStore } from '@/stores/ui'

const props = defineProps({
  track: {
    type: Object,
    required: true,
  },
  currentTime: {
    type: Number,
    default: 0,
  },
  isPlaying: {
    type: Boolean,
    default: false,
  },
  embedded: {
    type: Boolean,
    default: false,
  },
  showHeaderInEmbedded: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['seek', 'close'])

const uiStore = useUIStore()

// State
const loading = ref(false)
const lyricsData = ref(null)
const userOffset = ref(0)
const viewMode = ref('synced') // 'synced' | 'plain'
const containerRef = ref(null)
const lineRefs = ref([])

// User scroll tracking
const isUserScrolledAway = ref(false)
let userScrollTimeout = null

// Modals
const showEditModal = ref(false)
const showSearchModal = ref(false)
const editForm = ref({
  text: '',
  is_instrumental: false,
})
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const searched = ref(false)
const saving = ref(false)

// Offset debounce
let offsetDebounceTimer = null

// Parsed LRC Lines
const parsedLrcData = computed(() => {
  if (!lyricsData.value?.synced_lyrics) {
    return { lines: [], offset: 0 }
  }
  return parseLrc(lyricsData.value.synced_lyrics)
})

const parsedLines = computed(() => parsedLrcData.value.lines)

const isSyncedView = computed(() => {
  return viewMode.value === 'synced' && parsedLines.value.length > 0 && !lyricsData.value?.is_instrumental
})

// Active Line Index Calculation
const activeLineIndex = computed(() => {
  if (!isSyncedView.value || parsedLines.value.length === 0) return -1
  return getActiveLineIndex(parsedLines.value, props.currentTime, userOffset.value)
})

const badgeClass = computed(() => {
  if (lyricsData.value?.is_instrumental) return 'badge-instrumental'
  if (parsedLines.value.length > 0) return 'badge-synced'
  if (lyricsData.value?.plain_lyrics) return 'badge-plain'
  return 'badge-none'
})

function setLineRef(el, idx) {
  if (el) {
    lineRefs.value[idx] = el
  }
}

// Fetch lyrics on-demand
async function fetchLyrics(forceRefresh = false) {
  if (!props.track?.id) return
  loading.value = true
  try {
    const res = await tracksApi.getLyrics(props.track.id, forceRefresh)
    lyricsData.value = res.data
    userOffset.value = res.data?.offset_ms || 0
    
    // Choose initial viewMode
    if (res.data?.synced_lyrics) {
      viewMode.value = 'synced'
    } else {
      viewMode.value = 'plain'
    }
  } catch (err) {
    console.error('Failed to fetch lyrics:', err)
  } finally {
    loading.value = false
  }
}

// Seek directly to a lyric line
function seekToLine(line) {
  if (!line || typeof line.time !== 'number') return
  const targetTime = Math.max(0, line.time - (userOffset.value / 1000))
  emit('seek', targetTime)
  isUserScrolledAway.value = false
}

// Scroll to active line
function scrollToActiveLine(smooth = true) {
  if (!isSyncedView.value || activeLineIndex.value < 0) return
  const container = containerRef.value
  const targetEl = lineRefs.value[activeLineIndex.value]
  if (!container || !targetEl) return

  const containerHeight = container.clientHeight
  const targetTop = targetEl.offsetTop
  const targetHeight = targetEl.clientHeight

  // Target position: ~36% from top
  const scrollGoal = targetTop - (containerHeight * 0.36) + (targetHeight / 2)

  container.scrollTo({
    top: Math.max(0, scrollGoal),
    behavior: smooth ? 'smooth' : 'auto',
  })
  isUserScrolledAway.value = false
}

// Auto-scroll watcher
watch(activeLineIndex, (newIdx) => {
  if (newIdx >= 0 && !isUserScrolledAway.value) {
    scrollToActiveLine(true)
  }
})

// Track change watcher
watch(() => props.track?.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    lyricsData.value = null
    lineRefs.value = []
    isUserScrolledAway.value = false
    fetchLyrics()
  }
}, { immediate: true })

// User Scroll Handling
function handleUserScroll() {
  if (!isSyncedView.value) return
  isUserScrolledAway.value = true
  if (userScrollTimeout) clearTimeout(userScrollTimeout)
  userScrollTimeout = setTimeout(() => {
    isUserScrolledAway.value = false
    scrollToActiveLine(true)
  }, 4500)
}

function handleTouchStart() {
  if (isSyncedView.value) {
    isUserScrolledAway.value = true
  }
}

// Offset adjustment
function adjustOffset(deltaMs) {
  userOffset.value += deltaMs
  if (offsetDebounceTimer) clearTimeout(offsetDebounceTimer)
  offsetDebounceTimer = setTimeout(async () => {
    if (!props.track?.id) return
    try {
      await tracksApi.updateLyricsOffset(props.track.id, userOffset.value)
    } catch (e) {
      console.warn('Failed to save lyrics offset:', e)
    }
  }, 800)
}

function formatOffset(ms) {
  const s = (ms / 1000).toFixed(1)
  return ms > 0 ? `+${s}s` : `${s}s`
}

// Edit Modal
function openEditModal() {
  editForm.value.is_instrumental = !!lyricsData.value?.is_instrumental
  editForm.value.text = lyricsData.value?.synced_lyrics || lyricsData.value?.plain_lyrics || ''
  showEditModal.value = true
}

function copyEditTemplate() {
  editForm.value.text = `[00:00.00] Первая строка\n[00:05.00] Вторая строка`
}

async function saveLyrics() {
  if (!props.track?.id) return
  saving.value = true
  try {
    const text = editForm.value.text.trim()
    const isLrc = /\[\d{1,2}:\d{2}/.test(text)
    
    const payload = {
      is_instrumental: editForm.value.is_instrumental,
      plain_lyrics: isLrc ? text.replace(/\[\d{1,3}:\d{2}(?:\.\d{1,3})?\]/g, '').trim() : text,
      synced_lyrics: isLrc ? text : null,
      offset_ms: userOffset.value,
    }

    const res = await tracksApi.updateLyrics(props.track.id, payload)
    lyricsData.value = res.data
    showEditModal.value = false
    uiStore.toast.success('Текст сохранен', 'Текст успешно обновлен')
  } catch (err) {
    console.error('Failed to save lyrics:', err)
    uiStore.toast.error('Ошибка', 'Не удалось сохранить текст')
  } finally {
    saving.value = false
  }
}

// Search Modal
function openSearchModal() {
  const title = props.track?.title || ''
  const artist = props.track?.artist || ''
  searchQuery.value = `${artist} ${title}`.trim()
  searchResults.value = []
  searched.value = false
  showSearchModal.value = true
  if (searchQuery.value) {
    performSearch()
  }
}

async function performSearch() {
  if (!searchQuery.value.trim() || !props.track?.id) return
  searching.value = true
  searched.value = true
  try {
    const res = await tracksApi.searchLyrics(props.track.id, searchQuery.value.trim())
    searchResults.value = Array.isArray(res.data) ? res.data : []
  } catch (err) {
    console.error('Failed to search lyrics:', err)
    uiStore.toast.error('Ошибка поиска', 'Не удалось выполнить поиск в базе')
  } finally {
    searching.value = false
  }
}

async function applySearchResult(result) {
  if (!props.track?.id) return
  try {
    const payload = {
      plain_lyrics: result.plainLyrics,
      synced_lyrics: result.syncedLyrics,
      is_instrumental: !!result.instrumental,
      offset_ms: 0,
    }
    const res = await tracksApi.updateLyrics(props.track.id, payload)
    lyricsData.value = res.data
    userOffset.value = 0
    showSearchModal.value = false
    uiStore.toast.success('Текст применен', 'Выбранный текст успешно привязан к треку')
  } catch (err) {
    console.error('Failed to apply search result:', err)
    uiStore.toast.error('Ошибка', 'Не удалось применить текст')
  }
}

onUnmounted(() => {
  if (userScrollTimeout) clearTimeout(userScrollTimeout)
  if (offsetDebounceTimer) clearTimeout(offsetDebounceTimer)
})
</script>

<style scoped>
.lyrics-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  position: relative;
  overflow: hidden;
  background: transparent;
  color: #fff;
  user-select: none;
}

/* Header */
.lyrics-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(18, 18, 22, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  z-index: 10;
  gap: 12px;
}

.lyrics-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.lyrics-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge-synced {
  background: rgba(99, 102, 241, 0.25);
  color: #818cf8;
  border: 1px solid rgba(99, 102, 241, 0.4);
}

.badge-plain {
  background: rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
}

.badge-instrumental {
  background: rgba(236, 72, 153, 0.2);
  color: #f472b6;
  border: 1px solid rgba(236, 72, 153, 0.3);
}

.badge-none {
  background: rgba(255, 255, 255, 0.06);
  color: #94a3b8;
}

.mode-switch {
  display: flex;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  padding: 2px;
}

.switch-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.switch-btn.active {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  font-weight: 600;
}

.lyrics-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.offset-controls {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  padding: 2px 4px;
  gap: 4px;
}

.offset-btn {
  background: transparent;
  border: none;
  color: #cbd5e1;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 5px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;
}

.offset-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.offset-val {
  font-size: 11px;
  color: #38bdf8;
  font-weight: 600;
}

.action-icon-btn {
  background: rgba(255, 255, 255, 0.08);
  border: none;
  color: #cbd5e1;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.action-icon-btn:hover {
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  transform: scale(1.05);
}

.action-icon-btn.close-btn {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

.action-icon-btn.close-btn:hover {
  background: rgba(239, 68, 68, 0.3);
  color: #fff;
}

/* Body & Scrolling List */
.lyrics-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px 20px;
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
  mask-image: linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%);
  -webkit-mask-image: linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%);
}

.lyrics-body::-webkit-scrollbar {
  width: 4px;
}

.lyrics-body::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
}

/* Synced Line Styles */
.synced-lyrics-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.lyrics-spacer-top {
  height: 30vh;
}

.lyrics-spacer-bottom {
  height: 45vh;
}

.lyric-line {
  padding: 8px 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.2, 0.8, 0.2, 1);
  transform-origin: left center;
}

.lyric-line .line-text {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.45;
  display: block;
}

.lyric-line.active {
  color: #ffffff;
  opacity: 1;
  transform: scale(1.04);
  text-shadow: 0 0 24px rgba(255, 255, 255, 0.35), 0 0 40px rgba(99, 102, 241, 0.4);
}

.lyric-line.passed {
  color: #94a3b8;
  opacity: 0.4;
  filter: blur(0.3px);
}

.lyric-line.upcoming {
  color: #94a3b8;
  opacity: 0.4;
  filter: blur(0.3px);
}

.lyric-line:hover {
  opacity: 0.85;
  filter: none;
  background: rgba(255, 255, 255, 0.05);
}

/* Plain Lyrics */
.plain-lyrics-container {
  padding: 24px 8px;
}

.plain-lyrics-text {
  font-size: 18px;
  line-height: 1.8;
  color: #e2e8f0;
  white-space: pre-wrap;
  user-select: text;
}

/* States (Loading, Instrumental, Empty) */
.lyrics-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  text-align: center;
  padding: 30px;
}

.lyrics-spinner {
  animation: spin 1s linear infinite;
  color: #818cf8;
  margin-bottom: 16px;
}

.state-text {
  font-size: 16px;
  color: #94a3b8;
}

.instrumental-icon {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;
}

.note-animation {
  font-size: 54px;
  margin-bottom: 12px;
  animation: float 2.5s ease-in-out infinite;
}

.wave-bars {
  display: flex;
  align-items: flex-end;
  gap: 5px;
  height: 24px;
}

.wave-bar {
  width: 4px;
  background: #f472b6;
  border-radius: 2px;
  animation: wave 1.2s ease-in-out infinite alternate;
}

.instrumental-title {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px 0;
}

.state-subtext {
  font-size: 14px;
  color: #94a3b8;
  margin: 0 0 20px 0;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px 0;
}

.empty-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

/* Buttons */
.primary-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #6366f1;
  color: #fff;
  border: none;
  padding: 10px 18px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.primary-btn:hover {
  background: #4f46e5;
  transform: translateY(-1px);
}

.secondary-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.15);
  padding: 10px 18px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.secondary-btn:hover {
  background: rgba(255, 255, 255, 0.18);
}

/* Floating Sync Pill */
.sync-pill {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 6px;
  background: #6366f1;
  color: #fff;
  border: none;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
  cursor: pointer;
  z-index: 20;
  transition: all 0.2s;
}

.sync-pill:hover {
  background: #4f46e5;
  transform: translateX(-50%) scale(1.05);
}

/* Modals */
.lyrics-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 16px;
}

.lyrics-modal {
  background: #18181f;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  width: 100%;
  max-width: 520px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.modal-header h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #fff;
}

.modal-close {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 18px;
  cursor: pointer;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.btn-cancel {
  background: rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
}

.btn-save {
  background: #6366f1;
  color: #fff;
  border: none;
  padding: 8px 18px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.form-checkbox {
  margin-bottom: 14px;
}

.form-checkbox label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #e2e8f0;
  cursor: pointer;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.label-row label {
  font-size: 13px;
  color: #94a3b8;
}

.text-link-btn {
  background: none;
  border: none;
  color: #818cf8;
  font-size: 12px;
  cursor: pointer;
}

.lyrics-textarea {
  width: 100%;
  box-sizing: border-box;
  background: #111116;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  padding: 12px;
  color: #fff;
  font-family: monospace;
  font-size: 13px;
  line-height: 1.5;
  resize: vertical;
}

/* Search Modal Styles */
.search-input-wrapper {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.search-input {
  flex: 1;
  background: #111116;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  padding: 10px 14px;
  color: #fff;
  font-size: 14px;
}

.btn-search {
  background: #6366f1;
  color: #fff;
  border: none;
  padding: 0 16px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.search-results-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 320px;
  overflow-y: auto;
}

.search-result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.search-result-item:hover {
  background: rgba(255, 255, 255, 0.09);
  border-color: rgba(99, 102, 241, 0.4);
}

.res-title {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

.res-artist {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
}

.res-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 6px;
  border-radius: 4px;
}

.res-badge.synced {
  background: rgba(99, 102, 241, 0.25);
  color: #818cf8;
}

.res-badge.plain {
  background: rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
}

.res-badge.inst {
  background: rgba(236, 72, 153, 0.2);
  color: #f472b6;
}

.results-loading, .results-empty {
  text-align: center;
  padding: 24px;
  color: #94a3b8;
  font-size: 14px;
}

/* Animations */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

@keyframes wave {
  0% { height: 6px; }
  100% { height: 24px; }
}

.fade-pill-enter-active, .fade-pill-leave-active {
  transition: all 0.2s ease;
}
.fade-pill-enter-from, .fade-pill-leave-to {
  opacity: 0;
  transform: translate(-50%, 10px);
}

@media (max-width: 600px) {
  .lyric-line .line-text {
    font-size: 20px;
  }
}
</style>
