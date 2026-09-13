<template>
  <div class="settings-about-group">
    <!-- 5. Library Stats -->
    <section id="stats" class="settings-section">
      <div class="section-header">
        <h2>
          <Library :size="18" />
          <span>Библиотека</span>
        </h2>
      </div>

      <div class="settings-card stats-card">
        <div class="stats-grid" v-if="stats">
          <div class="stat-item">
            <span class="stat-value">{{ stats.total_tracks }}</span>
            <span class="stat-label">треков</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.album_count }}</span>
            <span class="stat-label">альбомов</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.artist_count }}</span>
            <span class="stat-label">исполнителей</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ formatDuration(stats.total_duration_seconds) }}</span>
            <span class="stat-label">общее время</span>
          </div>
        </div>
        <div class="stats-grid" v-else>
          <div class="stat-item stat-skeleton" v-for="i in 4" :key="i">
            <div class="skeleton-stat-value"></div>
            <div class="skeleton-stat-label"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- 7. Notification settings -->
    <section id="notifications" class="settings-section">
      <div class="section-header">
        <h2>
          <Bell :size="18" />
          <span>Уведомления</span>
        </h2>
      </div>

      <div class="settings-card">
        <div class="setting-row">
          <div class="setting-info">
            <span class="setting-name">Уведомления о подписках</span>
            <span class="setting-desc">Получать уведомления, когда кто-то подписывается на вас или ваши плейлисты</span>
          </div>
          <label class="toggle">
            <input 
              type="checkbox" 
              v-model="privacySettings.notify_subscription" 
              @change="updatePrivacy('notify_subscription', $event.target.checked)"
            />
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>
    </section>

    <!-- 11. Cache & Storage Section -->
    <section id="cache" class="settings-section">
      <div class="section-header">
        <h2>
          <HardDrive :size="18" />
          <span>Кэш и память</span>
        </h2>
      </div>

      <div class="settings-card cache-card">
        <!-- Auto-cache toggle -->
        <div class="setting-row">
          <div class="setting-info">
            <span class="setting-name">Автокэширование треков</span>
            <span class="setting-desc">Автоматически сохранять треки на устройство для мгновенного старта и офлайн-прослушивания</span>
          </div>
          <label class="toggle">
            <input 
              type="checkbox" 
              v-model="playerStore.autoCacheEnabled" 
            />
            <span class="toggle-slider"></span>
          </label>
        </div>

        <!-- Max Cache Size -->
        <template v-if="playerStore.autoCacheEnabled">
          <div class="setting-divider"></div>

          <div class="setting-row slider-setting-block">
            <div class="slider-row-top">
              <span class="setting-name">Лимит размера кэша</span>
              <span class="setting-value">{{ formatCacheLimit(playerStore.cacheMaxBytes) }}</span>
            </div>
            <div class="scale-presets-wrap">
              <div class="scale-presets cache-limits-presets">
                <button 
                  v-for="limit in cacheLimits" 
                  :key="limit.value"
                  class="scale-preset-chip"
                  :class="{ active: playerStore.cacheMaxBytes === limit.value }"
                  @click="playerStore.cacheMaxBytes = limit.value"
                >
                  {{ limit.label }}
                </button>
              </div>
            </div>
            <span class="setting-desc">При заполнении кэша старые треки удаляются автоматически (LRU)</span>
          </div>
        </template>

        <div class="setting-divider"></div>

        <!-- Cache stats bar -->
        <div class="cache-storage-bar-box">
          <div class="cache-stats-header">
            <div class="cache-stat-item">
              <span class="cache-stat-label">Занято кэшем</span>
              <span class="cache-stat-val">{{ formatBytes(cacheStats.totalBytes) }} <span class="cache-stat-count">({{ cacheStats.trackCount }} треков)</span></span>
            </div>
            <div v-if="cacheStats.quotaBytes > 0" class="cache-stat-item align-right">
              <span class="cache-stat-label">Доступно</span>
              <span class="cache-stat-val">{{ formatBytes(cacheStats.quotaBytes - cacheStats.usageBytes) }}</span>
            </div>
          </div>

          <div class="cache-progress-bar">
            <div 
              class="cache-progress-fill" 
              :style="{ width: `${cacheFillPercent}%` }"
            ></div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="cache-actions-grid">
          <button 
            v-if="cacheStats.trackCount > 0"
            class="action-btn success-soft view-downloaded-btn"
            @click="router.push('/downloaded')"
          >
            <HardDrive :size="15" />
            <span>Открыть скачанные ({{ cacheStats.trackCount }})</span>
          </button>

          <button 
            class="action-btn danger-soft clear-cache-btn" 
            :disabled="clearingCache || cacheStats.trackCount === 0"
            @click="handleClearCache"
          >
            <Trash2 :size="15" />
            <span>{{ clearingCache ? 'Очистка...' : 'Очистить кэш треков' }}</span>
          </button>
        </div>
      </div>
    </section>

    <!-- 12. About Section -->
    <section id="about" class="settings-section about-section">
      <div class="settings-card about-card">
        <h3 class="about-title">{{ authStore.appName }} <span class="about-ver">v2.0</span></h3>
        <p class="about-desc">Музыкальный плеер с хранением и стримингом в Telegram</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Library, Bell, HardDrive, Trash2 } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import api from '@/api/client'
import { getCacheStats, getCachedAudioStats } from '@/utils/audioCacheDb'
import { clearAudioCache } from '@/stores/playerCache'
import { formatDurationLong as formatDuration } from '@/utils'

const router = useRouter()
const authStore = useAuthStore()
const playerStore = usePlayerStore()

const STATS_STORAGE_KEY = 'tg_player_library_stats'

const getCachedStats = () => {
  try {
    const raw = localStorage.getItem(STATS_STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch (_) {}
  return null
}

const stats = ref(getCachedStats())
const statsLoading = ref(!stats.value)

const privacySettings = ref({
  notify_subscription: true,
})

const cachedAudioStats = getCachedAudioStats()
const cacheStats = ref({
  totalBytes: cachedAudioStats?.totalBytes || 0,
  trackCount: cachedAudioStats?.trackCount || 0,
  quotaBytes: 0,
  usageBytes: 0
})
const clearingCache = ref(false)

const cacheLimits = [
  { label: '500 МБ', value: 500 * 1024 * 1024 },
  { label: '1 ГБ', value: 1024 * 1024 * 1024 },
  { label: '2 ГБ', value: 2048 * 1024 * 1024 },
  { label: '5 ГБ', value: 5120 * 1024 * 1024 },
  { label: 'Без лимита', value: 0 },
]

const formatCacheLimit = (bytes) => {
  if (!bytes || bytes === 0) return 'Без ограничений'
  const gb = bytes / (1024 * 1024 * 1024)
  if (gb >= 1) return `${gb.toFixed(0)} ГБ`
  return `${(bytes / (1024 * 1024)).toFixed(0)} МБ`
}

const formatBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0 МБ'
  const mb = bytes / (1024 * 1024)
  if (mb < 1024) return `${mb.toFixed(1)} МБ`
  return `${(mb / 1024).toFixed(1)} ГБ`
}

const cacheFillPercent = computed(() => {
  if (!playerStore.cacheMaxBytes || playerStore.cacheMaxBytes === 0) {
    if (!cacheStats.value.quotaBytes) return 0
    return Math.min(100, Math.max(2, (cacheStats.value.totalBytes / cacheStats.value.quotaBytes) * 100))
  }
  if (cacheStats.value.totalBytes === 0) return 0
  return Math.min(100, Math.max(2, (cacheStats.value.totalBytes / playerStore.cacheMaxBytes) * 100))
})

const loadStats = async () => {
  statsLoading.value = true
  try {
    const response = await api.get('/library/stats')
    stats.value = response.data
    try {
      localStorage.setItem(STATS_STORAGE_KEY, JSON.stringify(response.data))
    } catch (_) {}
  } catch (error) {
    console.error('Failed to load stats:', error)
  } finally {
    statsLoading.value = false
  }
}

const loadPrivacySettings = async () => {
  try {
    const response = await api.get('/auth/privacy')
    if (response.data) {
      privacySettings.value.notify_subscription = response.data.notify_subscription
    }
  } catch (error) {
    console.error('Failed to load privacy settings:', error)
  }
}

const updatePrivacy = async (field, value) => {
  try {
    await api.put('/auth/privacy', { [field]: value })
  } catch (error) {
    console.error('Failed to update privacy:', error)
    privacySettings.value[field] = !value
  }
}

const refreshCacheStats = async () => {
  try {
    cacheStats.value = await getCacheStats()
  } catch (e) {
    console.warn('Failed to get cache stats:', e)
  }
}

const handleClearCache = async () => {
  if (!confirm('Очистить весь локальный кэш треков?')) return
  clearingCache.value = true
  try {
    await clearAudioCache()
    localStorage.removeItem('tracks_cache')
    localStorage.removeItem('albums_cache')
    await refreshCacheStats()
  } catch (e) {
    console.error('Error clearing cache:', e)
  } finally {
    clearingCache.value = false
  }
}

onMounted(() => {
  loadStats()
  loadPrivacySettings()
  refreshCacheStats()
  window.addEventListener('cache-updated', refreshCacheStats)
})

onUnmounted(() => {
  window.removeEventListener('cache-updated', refreshCacheStats)
})
</script>

<style scoped>
.settings-section {
  margin-bottom: var(--sp-5);
  width: 100%;
  transition: all 0.3s ease;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  margin-bottom: 8px;
  padding: 0 2px;
}

.section-header h2 {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
  line-height: 1.4;
}

.settings-card {
  background: var(--c-bg-2);
  border-radius: var(--r-lg);
  border: 1px solid rgba(255, 255, 255, 0.04);
  box-shadow: 
    3px 3px 10px var(--sh-dark),
    -1px -1px 2px var(--sh-light);
  padding: 16px;
  width: 100%;
  box-sizing: border-box;
}

.setting-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.05);
  margin: 12px 0;
  width: 100%;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  padding: 2px 0;
}

.setting-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  gap: 2px;
}

.setting-name {
  color: var(--c-text-1);
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
}

.setting-desc {
  color: var(--c-text-3);
  font-size: 12px;
  line-height: 1.4;
}

.toggle {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--c-bg-4);
  transition: .3s cubic-bezier(0.4, 0.0, 0.2, 1);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 2px;
  bottom: 2px;
  background-color: var(--c-text-2);
  transition: .3s cubic-bezier(0.4, 0.0, 0.2, 1);
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

input:checked + .toggle-slider {
  background-color: var(--c-accent);
  border-color: var(--c-accent);
}

input:checked + .toggle-slider:before {
  transform: translateX(20px);
  background-color: #fff;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-item {
  background: var(--c-bg-3);
  border-radius: var(--r-md);
  padding: 12px 8px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 76px;
  border: 1px solid rgba(255, 255, 255, 0.02);
}

.stat-value {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: var(--c-text-1);
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.stat-label {
  display: block;
  color: var(--c-text-3);
  font-size: 12px;
  margin-top: 3px;
  line-height: 1.2;
}

.stat-item.stat-skeleton {
  min-height: 76px;
}

.skeleton-stat-value {
  height: 24px;
  width: 50px;
  background: var(--c-bg-4);
  border-radius: var(--r-sm);
  animation: pulse-skeleton 1.5s ease-in-out infinite;
}

.skeleton-stat-label {
  height: 10px;
  width: 40px;
  background: var(--c-bg-4);
  border-radius: var(--r-xs);
  margin-top: 6px;
  animation: pulse-skeleton 1.5s ease-in-out infinite;
  animation-delay: 0.1s;
}

@keyframes pulse-skeleton {
  0%, 100% { opacity: 0.35; }
  50% { opacity: 0.75; }
}

.slider-setting-block {
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  width: 100%;
}

.slider-row-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  width: 100%;
}

.setting-value {
  color: var(--c-accent);
  font-weight: 600;
  font-size: 14px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.scale-presets-wrap {
  overflow-x: auto;
  width: 100%;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  padding: 2px 0;
}

.scale-presets-wrap::-webkit-scrollbar {
  display: none;
}

.scale-presets {
  display: flex;
  gap: 6px;
  width: 100%;
  min-width: 320px;
}

.scale-preset-chip {
  flex: 1;
  min-width: 36px;
  padding: 6px 0;
  text-align: center;
  border-radius: var(--r-sm);
  background: var(--c-bg-3);
  color: var(--c-text-2);
  border: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.scale-preset-chip:hover {
  background: var(--c-bg-4);
  color: var(--c-text-1);
}

.scale-preset-chip.active {
  background: var(--c-accent);
  color: #000000;
  font-weight: 600;
  border-color: var(--c-accent);
  box-shadow: 0 0 8px var(--c-accent-glow);
}

.cache-storage-bar-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 4px 0 12px;
}

.cache-stats-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.cache-stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.cache-stat-item.align-right {
  align-items: flex-end;
  text-align: right;
}

.cache-stat-label {
  font-size: 11px;
  color: var(--c-text-3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.cache-stat-val {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text-1);
}

.cache-stat-count {
  font-size: 12px;
  font-weight: 400;
  color: var(--c-text-2);
}

.cache-progress-bar {
  width: 100%;
  height: 6px;
  background: var(--c-bg-4);
  border-radius: 3px;
  overflow: hidden;
}

.cache-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--c-accent) 0%, #00e676 100%);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.cache-actions-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  margin-top: 8px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  border-radius: var(--r-full, 9999px);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
  width: 100%;
}

.action-btn.success-soft {
  background: rgba(29, 185, 84, 0.1);
  color: #1db954;
  border: 1px solid rgba(29, 185, 84, 0.2);
}

.action-btn.success-soft:hover:not(:disabled) {
  background: rgba(29, 185, 84, 0.15);
}

.action-btn.danger-soft {
  background: rgba(255, 77, 79, 0.1);
  color: #ff4d4f;
  border: 1px solid rgba(255, 77, 79, 0.2);
}

.action-btn.danger-soft:hover:not(:disabled) {
  background: rgba(255, 77, 79, 0.15);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.about-card {
  text-align: center;
  padding: 18px;
}

.about-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0;
}

.about-ver {
  font-size: 12px;
  color: var(--c-accent);
  font-weight: 600;
  margin-left: 4px;
}

.about-desc {
  font-size: 12px;
  color: var(--c-text-3);
  margin: 4px 0 0 0;
}

@media (max-width: 540px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
}
</style>
