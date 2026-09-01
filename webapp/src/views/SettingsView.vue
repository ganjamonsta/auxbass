<template>
  <div class="settings-view">
    <!-- Skeleton while loading -->
    <SettingsSkeleton v-if="loading" />

    <!-- Actual content -->
    <template v-else>
    <h1>Настройки</h1>

    <!-- Channel section (Premium) -->
    <section id="channel" class="section channel-section" :class="{ 'not-connected': !authStore.hasChannel }">
      <h2><Megaphone :size="20" /> Канал для бэкапа</h2>
      
      <template v-if="authStore.hasChannel">
        <div class="channel-connected">
          <div class="channel-info">
            <div class="channel-icon"><Check :size="20" /></div>
            <div class="channel-details">
              <span class="channel-title">{{ authStore.channelInfo?.channel_title || 'Канал подключён' }}</span>
              <span class="channel-username" v-if="authStore.channelInfo?.channel_username">
                @{{ authStore.channelInfo.channel_username }}
              </span>
            </div>
          </div>
          <div class="channel-features">
            <div class="feature-item"><Check :size="14" /> Сохранение треков</div>
            <div class="feature-item"><Check :size="14" /> Создание плейлистов</div>
            <div class="feature-item"><Check :size="14" /> Автобэкап в канал</div>
          </div>
        </div>
      </template>
      
      <template v-else>
        <div class="channel-not-connected">
          <p class="channel-desc">
            Подключите Telegram-канал, чтобы разблокировать все функции:
          </p>
          <ul class="feature-list">
            <li><Folder :size="16" /> Загрузка и сохранение треков</li>
            <li><Heart :size="16" /> Лайки и избранное</li>
            <li><ListMusic :size="16" /> Создание плейлистов</li>
            <li><Cloud :size="16" /> Автоматический бэкап музыки</li>
          </ul>
          <div class="setup-steps">
            <h3>Как подключить:</h3>
            <ol>
              <li>Создайте приватный канал в Telegram</li>
              <li>Добавьте бота <strong>@{{ botUsername }}</strong> админом канала</li>
              <li>Напишите боту команду <code>/channel</code></li>
              <li>Перешлите любое сообщение из канала боту</li>
            </ol>
          </div>
          <button class="refresh-btn" @click="refreshStatus">
            <RefreshCw :size="16" /> Обновить статус
          </button>
        </div>
      </template>
    </section>

    <!-- User section -->
    <section class="section">
      <h2>Аккаунт</h2>
      <div class="user-info" v-if="authStore.user">
        <div class="avatar" :style="avatarGradient">
          <User v-if="!authStore.user.first_name" :size="24" />
          <span v-else class="avatar-letter">{{ authStore.user.first_name.charAt(0) }}</span>
        </div>
        <div class="user-details">
          <span class="user-name">
            {{ authStore.user.first_name }} {{ authStore.user.last_name }}
          </span>
          <span class="user-id">ID: {{ authStore.user.id }}</span>
        </div>
      </div>
      <button class="logout-btn" @click="logout">
        Выйти
      </button>
    </section>

    <!-- Library stats -->
    <section class="section">
      <h2>Библиотека</h2>
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
    </section>

    <!-- Privacy settings -->
    <section class="section">
      <h2><Lock :size="20" /> Приватность</h2>
      
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Скрыть из поиска</span>
          <span class="setting-desc">Вас не найдут другие пользователи, но ваша медиатека останется доступна по прямой ссылке</span>
        </div>
        <label class="toggle">
          <input 
            type="checkbox" 
            v-model="privacySettings.hide_from_search" 
            @change="updatePrivacy('hide_from_search', $event.target.checked)"
          />
          <span class="toggle-slider"></span>
        </label>
      </div>

      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Скрыть профиль полностью</span>
          <span class="setting-desc">Ваша медиатека и альбомы будут скрыты от других. Приватность плейлистов сохранится</span>
        </div>
        <label class="toggle">
          <input 
            type="checkbox" 
            v-model="privacySettings.hide_profile" 
            @change="updatePrivacy('hide_profile', $event.target.checked)"
          />
          <span class="toggle-slider"></span>
        </label>
      </div>
    </section>

    <!-- Notification settings -->
    <section class="section">
      <h2><Bell :size="20" /> Уведомления</h2>
      
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
    </section>

    <!-- Cache section -->
    <section class="section">
      <h2><Sliders :size="20" /> Интерфейс</h2>

      <div class="setting-row slider-row">
        <div class="setting-info">
          <div class="setting-info-title">
            <span class="setting-name">Масштаб интерфейса</span>
            <button 
              v-if="Math.round(playerStore.uiScale * 100) !== 100"
              class="scale-reset-btn"
              @click="playerStore.uiScale = 1.0"
              title="Сбросить на 100%"
            >
              100%
            </button>
          </div>
          <span class="setting-value">{{ Math.round(playerStore.uiScale * 100) }}%</span>
        </div>
        <input 
          type="range" 
          min="0.7" 
          max="1.3" 
          step="0.05"
          v-model.number="playerStore.uiScale"
          class="range-slider"
        />
        <div class="scale-presets">
          <button 
            v-for="preset in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]" 
            :key="preset"
            class="scale-preset-chip"
            :class="{ active: Math.round(playerStore.uiScale * 100) === Math.round(preset * 100) }"
            @click="playerStore.uiScale = preset"
          >
            {{ Math.round(preset * 100) }}%
          </button>
        </div>
        <span class="setting-desc scale-desc">Измените размер интерфейса плеера для удобства использования</span>
      </div>
    </section>

    <!-- Cache section -->
    <section class="section">
      <h2><Headphones :size="20" /> Аудио (Enhancer)</h2>

      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Включить обработку</span>
          <span class="setting-desc">Улучшение звука в реальном времени (Bass, Treble, Compressor)</span>
        </div>
        <label class="toggle">
          <input 
            type="checkbox" 
            v-model="playerStore.enhancerEnabled" 
          />
          <span class="toggle-slider"></span>
        </label>
      </div>

      <template v-if="playerStore.enhancerEnabled">
        <div class="setting-row slider-row">
            <div class="setting-info">
              <span class="setting-name">Bass (Низкие)</span>
              <span class="setting-value">{{ playerStore.bassGain }} dB</span>
            </div>
            <input 
              type="range" 
              min="-10" 
              max="10" 
              step="1"
              v-model.number="playerStore.bassGain"
              class="range-slider"
            />
        </div>

        <div class="setting-row slider-row">
            <div class="setting-info">
              <span class="setting-name">Treble (Высокие)</span>
              <span class="setting-value">{{ playerStore.trebleGain }} dB</span>
            </div>
            <input 
              type="range" 
              min="-10" 
              max="10" 
              step="1"
              v-model.number="playerStore.trebleGain"
              class="range-slider"
            />
        </div>

        <div class="setting-row">
            <div class="setting-info">
              <span class="setting-name">Auto Gain (Компрессор)</span>
              <span class="setting-desc">Автоматическое выравнивание громкости</span>
            </div>
            <label class="toggle">
              <input 
                type="checkbox" 
                v-model="playerStore.autoGain" 
              />
              <span class="toggle-slider"></span>
            </label>
        </div>
      </template>
    </section>

    <!-- App section (PWA) -->
    <section class="section pwa-section">
      <h2><Smartphone :size="20" /> Приложение</h2>
      
      <div v-if="pwaInstall.isInstalled" class="pwa-status-installed">
        <div class="pwa-status-icon"><Check :size="20" /></div>
        <div class="pwa-status-text">
          <span class="pwa-status-title">Приложение установлено</span>
          <span class="pwa-status-desc">AuxBass работает в полноэкранном режиме Web App</span>
        </div>
      </div>

      <div v-else class="pwa-install-card">
        <div class="setting-info">
          <span class="setting-name">Установить как Web App</span>
          <span class="setting-desc">Быстрый запуск с главного экрана, поддержка медиаклавиш и воспроизведение без пауз</span>
        </div>
        <button class="pwa-section-install-btn" @click="handleInstallClick">
          <Download :size="16" />
          <span>{{ pwaInstall.isIOS ? 'Как установить' : 'Установить' }}</span>
        </button>
      </div>
    </section>

    <!-- Cache & Offline section -->
    <section class="section cache-section">
      <h2><HardDrive :size="20" /> Кэш и память</h2>

      <!-- Auto-cache toggle -->
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Автокэширование треков</span>
          <span class="setting-desc">Автоматически сохранять воспроизводимые треки на устройство для мгновенного старта и офлайн-прослушивания</span>
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
      <div v-if="playerStore.autoCacheEnabled" class="setting-row slider-row">
        <div class="setting-info">
          <span class="setting-name">Лимит размера кэша</span>
          <span class="setting-value">{{ formatCacheLimit(playerStore.cacheMaxBytes) }}</span>
        </div>
        <div class="scale-presets">
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
        <span class="setting-desc">При заполнении кэша старые треки удаляются автоматически (LRU)</span>
      </div>

      <!-- Cache stats card -->
      <div class="cache-stats-card">
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

        <!-- Progress bar -->
        <div class="cache-progress-bar">
          <div 
            class="cache-progress-fill" 
            :style="{ width: `${cacheFillPercent}%` }"
          ></div>
        </div>
      </div>

      <button 
        class="clear-cache-btn" 
        :disabled="clearingCache || cacheStats.trackCount === 0"
        @click="handleClearCache"
      >
        <Trash2 :size="16" />
        <span>{{ clearingCache ? 'Очистка...' : 'Очистить кэш треков' }}</span>
      </button>
    </section>

    <!-- About -->
    <section class="section about">
      <h2>О приложении</h2>
      <p>{{ authStore.appName }} v2.0</p>
      <p class="about-desc">
        Музыкальный плеер с хранением в Telegram
      </p>
    </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import api, { authApi } from '@/api/client'
import { Megaphone, Check, Folder, Heart, ListMusic, Cloud, RefreshCw, Lock, User, Bell, Sliders, Headphones, Smartphone, Download, HardDrive, Trash2 } from 'lucide-vue-next'
import SettingsSkeleton from '@/components/SettingsSkeleton.vue'
import { usePwaInstall } from '@/composables/usePwaInstall'
import { getCacheStats } from '@/utils/audioCacheDb'
import { clearAudioCache } from '@/stores/playerCache'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const playerStore = usePlayerStore()
const pwaInstall = usePwaInstall()

const handleInstallClick = () => {
  pwaInstall.promptInstall()
}

const loading = ref(true)
const stats = ref(null)
const darkMode = ref(true)
const botUsername = ref('tg_player_bot')  // Default, will be updated from config
const privacySettings = ref({
  hide_from_search: false,
  hide_profile: false,
  notify_subscription: true,
})

// Avatar gradient based on user ID for unique colors
const avatarGradient = computed(() => {
  const id = authStore.user?.id || 0
  const hue = (id * 137) % 360
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 60%, 45%) 0%, hsl(${(hue + 40) % 360}, 50%, 35%) 100%)`
  }
})

const repeatModeText = computed(() => {
  const modes = {
    none: 'Выключен',
    all: 'Повтор всего',
    one: 'Повтор трека'
  }
  return modes[playerStore.repeatMode] || 'Выключен'
})

const repeatModeIcon = computed(() => {
  const icons = {
    none: '🔁',
    all: '🔁',
    one: '🔂'
  }
  return icons[playerStore.repeatMode] || '🔁'
})

const loadStats = async () => {
  try {
    const response = await api.get('/library/stats')
    stats.value = response.data
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

const loadBotConfig = async () => {
  try {
    const response = await authApi.getConfig()
    if (response.data?.bot_username) {
      botUsername.value = response.data.bot_username
    }
  } catch (error) {
    console.error('Failed to load bot config:', error)
  }
}

const refreshStatus = async () => {
  await authStore.fetchStatus()
}

const loadPrivacySettings = async () => {
  try {
    const response = await api.get('/auth/privacy')
    privacySettings.value = response.data
  } catch (error) {
    console.error('Failed to load privacy settings:', error)
  }
}

const updatePrivacy = async (field, value) => {
  try {
    await api.put('/auth/privacy', { [field]: value })
  } catch (error) {
    console.error('Failed to update privacy:', error)
    // Revert on error
    privacySettings.value[field] = !value
  }
}

const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}ч ${mins}м`
  }
  return `${mins}м`
}

const toggleRepeat = () => {
  const modes = ['none', 'all', 'one']
  const currentIndex = modes.indexOf(playerStore.repeatMode)
  playerStore.repeatMode = modes[(currentIndex + 1) % modes.length]
}

const logout = async () => {
  // Stop playback before logout
  playerStore.stop()
  authStore.logout()
  // Force full page reload to clear all store states
  window.location.href = '/login'
}

const cacheStats = ref({ totalBytes: 0, trackCount: 0, quotaBytes: 0, usageBytes: 0 })
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

// Watch dark mode toggle
watch(darkMode, (isDark) => {
  document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light')
  localStorage.setItem('theme', isDark ? 'dark' : 'light')
})

onMounted(async () => {
  loading.value = true
  
  try {
    // Load all data in parallel
    await Promise.all([
      loadStats(),
      loadBotConfig(),
      loadPrivacySettings(),
      refreshCacheStats()
    ])
  } finally {
    loading.value = false
  }
  
  // Load saved theme preference
  const savedTheme = localStorage.getItem('theme')
  darkMode.value = savedTheme !== 'light'
  
  // Scroll to channel section if hash is #channel
  if (route.hash === '#channel') {
    setTimeout(() => {
      document.getElementById('channel')?.scrollIntoView({ behavior: 'smooth' })
    }, 100)
  }
  
  // Слушаем событие сброса состояния
  window.addEventListener('reset-view-state', handleResetState)
})

onUnmounted(() => {
  window.removeEventListener('reset-view-state', handleResetState)
})

// Обработчик сброса состояния
const handleResetState = (event) => {
  if (event.detail.route === '/settings') {
    // Прокручиваем наверх
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════
   Settings View — Unified spacing & alignment
   Uses design-system tokens: --sp-*, --r-*, --c-*
   ═══════════════════════════════════════════════ */

.settings-view {
  padding: var(--sp-4);
  max-width: 640px;
  margin: 0 auto;
}

h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0 0 var(--sp-6) 0;
}

/* ─── Sections ─── */
.section {
  margin-bottom: var(--sp-6);
}

.section h2 {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text-3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 var(--sp-4) 0;
  line-height: 1.4;
}

/* ─── Account ─── */
.user-info {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: var(--sp-4);
  margin-bottom: var(--sp-4);
}

.avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-letter {
  font-size: 22px;
  font-weight: 700;
  line-height: 1;
  text-transform: uppercase;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.user-name {
  color: var(--c-text-1);
  font-weight: 500;
  font-size: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-id {
  color: var(--c-text-3);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.logout-btn {
  width: 100%;
  padding: var(--sp-3);
  background: transparent;
  border: 1px solid var(--c-error);
  border-radius: var(--r-md);
  color: var(--c-error);
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.logout-btn:hover {
  background: rgba(244, 67, 54, 0.1);
}

/* ─── Library Stats Grid ─── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--sp-3);
}

.stat-item {
  background: var(--c-bg-3);
  border-radius: var(--r-md);
  padding: var(--sp-4);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.stat-value {
  display: block;
  font-size: 26px;
  font-weight: 700;
  color: var(--c-text-1);
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.stat-label {
  display: block;
  color: var(--c-text-3);
  font-size: 13px;
  margin-top: var(--sp-1);
  line-height: 1.3;
}

/* ─── Setting Rows (toggle + description) ─── */
.setting-row {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: var(--sp-3) 0;
  border-bottom: 1px solid var(--c-bg-4);
  gap: var(--sp-4);
}

.setting-row:last-child {
  border-bottom: none;
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
  font-size: 15px;
  line-height: 1.4;
}

.setting-desc {
  color: var(--c-text-3);
  font-size: 13px;
  line-height: 1.4;
  margin-top: 0;
}

/* ─── Toggle Switch ─── */
.toggle {
  position: relative;
  display: inline-flex;
  align-items: center;
  width: 48px;
  height: 28px;
  flex-shrink: 0;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
  position: absolute;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: var(--c-bg-4);
  border-radius: 14px;
  transition: background 0.25s ease;
}

.toggle-slider::before {
  position: absolute;
  content: '';
  height: 22px;
  width: 22px;
  left: 3px;
  bottom: 3px;
  background: white;
  border-radius: 50%;
  transition: transform 0.25s ease;
}

.toggle input:checked + .toggle-slider {
  background: var(--c-accent);
}

.toggle input:checked + .toggle-slider::before {
  transform: translateX(20px);
}

/* ─── Buttons ─── */
.repeat-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--c-bg-3);
  border: none;
  font-size: 20px;
  cursor: pointer;
}

.clear-cache-btn {
  width: 100%;
  padding: var(--sp-3);
  background: var(--c-bg-3);
  border: none;
  border-radius: var(--r-md);
  color: var(--c-text-1);
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.clear-cache-btn:hover {
  background: var(--c-bg-4);
}

/* ─── About ─── */
.about {
  text-align: center;
}

.about p {
  color: var(--c-text-1);
  margin: var(--sp-2) 0;
}

.about-desc {
  color: var(--c-text-3) !important;
  font-size: 14px;
}

/* ═══════════════════════════════════════════════
   Channel Section
   ═══════════════════════════════════════════════ */
.channel-section {
  background: var(--c-bg-3);
  border-radius: var(--r-md);
  padding: var(--sp-4);
}

.channel-section.not-connected {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  border: 1px solid rgba(102, 126, 234, 0.3);
}

.channel-connected {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.channel-info {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: var(--sp-3);
}

.channel-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--c-accent);
  color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.channel-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.channel-title {
  color: var(--c-text-1);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.channel-username {
  color: var(--c-text-2);
  font-size: 13px;
}

.channel-features {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
}

.feature-item {
  display: inline-flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
  background: rgba(29, 185, 84, 0.15);
  color: var(--c-accent);
  padding: 6px 12px;
  border-radius: var(--r-full);
  font-size: 13px;
  line-height: 1;
  white-space: nowrap;
}

.channel-not-connected {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.channel-desc {
  color: var(--c-text-2);
  margin: 0;
  line-height: 1.5;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.feature-list li {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: var(--sp-2);
  color: var(--c-text-1);
  font-size: 14px;
  line-height: 1.4;
}

.setup-steps {
  background: var(--c-bg-2);
  border-radius: var(--r-sm);
  padding: var(--sp-3);
  margin-top: var(--sp-2);
}

.setup-steps h3 {
  color: var(--c-text-1);
  font-size: 14px;
  margin: 0 0 var(--sp-2) 0;
}

.setup-steps ol {
  padding-left: 20px;
  margin: 0;
  color: var(--c-text-2);
  font-size: 13px;
  line-height: 1.6;
}

.setup-steps strong {
  color: var(--c-accent);
}

.setup-steps code {
  background: var(--c-bg-4);
  padding: 2px 6px;
  border-radius: var(--r-xs);
  font-family: monospace;
  color: var(--c-text-1);
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  padding: 12px 24px;
  border-radius: var(--r-sm);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  margin-top: var(--sp-2);
  transition: opacity 0.2s;
}

.refresh-btn:hover {
  opacity: 0.9;
}

/* ═══════════════════════════════════════════════
   Range Slider
   ═══════════════════════════════════════════════ */
.slider-row {
  flex-direction: column;
  align-items: stretch;
  gap: var(--sp-3);
  padding-bottom: var(--sp-5);
}

.slider-row .setting-info {
  flex-direction: row;
  justify-content: space-between;
  align-items: baseline;
  width: 100%;
}

.range-slider {
  width: 100%;
  height: 6px;
  background: var(--bg-tertiary, var(--c-bg-4));
  border-radius: 3px;
  outline: none;
  -webkit-appearance: none;
}

.range-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--c-accent);
  cursor: pointer;
  transition: transform 0.15s ease;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}

.range-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

.range-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--c-accent);
  cursor: pointer;
  border: none;
}

.setting-value {
  color: var(--c-accent);
  font-weight: 600;
  font-size: 14px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.setting-info-title {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.scale-reset-btn {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: var(--r-xs, 4px);
  background: var(--c-bg-3);
  color: var(--c-text-2);
  border: 1px solid rgba(255, 255, 255, 0.08);
  cursor: pointer;
  transition: all 0.15s ease;
}

.scale-reset-btn:hover {
  color: var(--c-accent);
  background: var(--c-bg-4);
  border-color: var(--c-accent-glow);
}

.scale-presets {
  display: flex;
  width: 100%;
  gap: 6px;
  margin-top: 4px;
}

.scale-preset-chip {
  flex: 1;
  min-width: 0;
  padding: 6px 2px;
  text-align: center;
  border-radius: var(--r-sm, 8px);
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
  box-shadow: 0 0 10px var(--c-accent-glow);
}

.scale-desc {
  color: var(--c-text-3);
  font-size: 13px;
  margin-top: 2px;
  display: block;
  line-height: 1.4;
}

/* ═══════════════════════════════════════════════
   PWA Section
   ═══════════════════════════════════════════════ */
.pwa-status-installed {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: rgba(29, 185, 84, 0.1);
  border: 1px solid rgba(29, 185, 84, 0.25);
  border-radius: var(--r-sm);
}

.pwa-status-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--c-accent);
  color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.pwa-status-title {
  display: block;
  font-weight: 600;
  color: var(--c-text-1);
  font-size: 14px;
}

.pwa-status-desc {
  display: block;
  font-size: 12px;
  color: var(--c-text-2);
  margin-top: 2px;
}

.pwa-install-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  flex-wrap: wrap;
}

.pwa-section-install-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  background: var(--c-accent);
  color: #000000;
  border: none;
  border-radius: var(--r-sm);
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(29, 185, 84, 0.3);
}

.pwa-section-install-btn:hover {
  background: var(--c-accent-light);
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(29, 185, 84, 0.45);
}

.pwa-section-install-btn:active {
  transform: translateY(0);
}

.cache-stats-card {
  background: var(--c-bg-3);
  border-radius: var(--r-md);
  padding: var(--sp-4);
  margin: var(--sp-3) 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.cache-stats-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--sp-3);
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
  font-size: 12px;
  color: var(--c-text-3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.cache-stat-val {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text-1);
}

.cache-stat-count {
  font-size: 13px;
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

.clear-cache-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  width: 100%;
  padding: 12px;
  background: transparent;
  border: 1px solid rgba(244, 67, 54, 0.4);
  border-radius: var(--r-sm);
  color: var(--c-error);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.clear-cache-btn:hover:not(:disabled) {
  background: rgba(244, 67, 54, 0.1);
  border-color: var(--c-error);
}

.clear-cache-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ═══════════════════════════════════════════════
   Responsive
   ═══════════════════════════════════════════════ */
@media (max-width: 400px) {
  .settings-view {
    padding: var(--sp-3);
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--sp-2);
  }

  .stat-value {
    font-size: 22px;
  }

  .stat-item {
    padding: var(--sp-3);
  }

  .feature-item {
    font-size: 12px;
    padding: 5px 10px;
  }
}

@media (min-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
</style>
