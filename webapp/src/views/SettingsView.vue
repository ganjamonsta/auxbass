<template>
  <div class="settings-view">
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
        <div class="avatar">
          {{ authStore.user.first_name?.charAt(0) || '?' }}
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
      <h2>🔔 Уведомления</h2>
      
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
      <h2>� Интерфейс</h2>

      <div class="setting-row slider-row">
        <div class="setting-info">
          <span class="setting-name">Масштаб интерфейса</span>
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
        <span class="setting-desc scale-desc">Измените размер интерфейса плеера для удобства использования</span>
      </div>
    </section>

    <!-- Cache section -->
    <section class="section">
      <h2>�🎛️ Аудио (Enhancer)</h2>

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

    <!-- Cache section -->
    <section class="section">
      <h2>Кэш</h2>
      <button class="clear-cache-btn" @click="clearCache">
        Очистить кэш
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import api, { authApi } from '@/api/client'
import { Megaphone, Check, Folder, Heart, ListMusic, Cloud, RefreshCw, Lock } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const playerStore = usePlayerStore()

const stats = ref(null)
const darkMode = ref(true)
const botUsername = ref('tg_player_bot')  // Default, will be updated from config
const privacySettings = ref({
  hide_from_search: false,
  hide_profile: false,
  notify_subscription: true,
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

const clearCache = () => {
  // Clear any cached data
  localStorage.removeItem('tracks_cache')
  localStorage.removeItem('albums_cache')
  alert('Кэш очищен')
}

// Watch dark mode toggle
watch(darkMode, (isDark) => {
  document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light')
  localStorage.setItem('theme', isDark ? 'dark' : 'light')
})

onMounted(() => {
  loadStats()
  loadBotConfig()
  loadPrivacySettings()
  
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
.settings-view {
  padding: 16px;
  padding-bottom: 180px;
}

h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 24px 0;
}

.section {
  margin-bottom: 32px;
}

.section h2 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 16px 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--accent);
  color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 600;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name {
  color: var(--text-primary);
  font-weight: 500;
  font-size: 16px;
}

.user-id {
  color: var(--text-tertiary);
  font-size: 13px;
}

.logout-btn {
  width: 100%;
  padding: 12px;
  background: transparent;
  border: 1px solid var(--danger);
  border-radius: 10px;
  color: var(--danger);
  font-weight: 500;
  cursor: pointer;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-item {
  background: var(--bg-elevated);
  border-radius: 12px;
  padding: 16px;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  display: block;
  color: var(--text-tertiary);
  font-size: 13px;
  margin-top: 4px;
}

.setting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
  gap: 16px;
}

.setting-row:last-child {
  border-bottom: none;
}

.setting-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.setting-name {
  color: var(--text-primary);
  font-size: 15px;
}

.setting-desc {
  color: var(--text-tertiary);
  font-size: 13px;
  margin-top: 2px;
}

.toggle {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 28px;
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
  background: var(--bg-highlight);
  border-radius: 14px;
  transition: 0.3s;
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
  transition: 0.3s;
}

.toggle input:checked + .toggle-slider {
  background: var(--accent);
}

.toggle input:checked + .toggle-slider::before {
  transform: translateX(20px);
}

.repeat-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--bg-elevated);
  border: none;
  font-size: 20px;
  cursor: pointer;
}

.clear-cache-btn {
  width: 100%;
  padding: 12px;
  background: var(--bg-elevated);
  border: none;
  border-radius: 10px;
  color: var(--text-primary);
  font-weight: 500;
  cursor: pointer;
}

.clear-cache-btn:hover {
  background: var(--bg-highlight);
}

.about {
  text-align: center;
}

.about p {
  color: var(--text-primary);
  margin: 8px 0;
}

.about-desc {
  color: var(--text-tertiary) !important;
  font-size: 14px;
}

/* Channel Section */
.channel-section {
  background: var(--bg-elevated);
  border-radius: 12px;
  padding: 16px;
}

.channel-section.not-connected {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  border: 1px solid rgba(102, 126, 234, 0.3);
}

.channel-connected {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.channel-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.channel-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--accent);
  color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
}

.channel-details {
  display: flex;
  flex-direction: column;
}

.channel-title {
  color: var(--text-primary);
  font-weight: 500;
}

.channel-username {
  color: var(--text-secondary);
  font-size: 13px;
}

.channel-features {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.feature-item {
  background: rgba(29, 185, 84, 0.2);
  color: var(--accent);
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
}

.channel-not-connected {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.channel-desc {
  color: var(--text-secondary);
  margin: 0;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feature-list li {
  color: var(--text-primary);
  font-size: 14px;
}

.setup-steps {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 12px;
  margin-top: 8px;
}

.setup-steps h3 {
  color: var(--text-primary);
  font-size: 14px;
  margin: 0 0 8px 0;
}

.setup-steps ol {
  padding-left: 20px;
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.setup-steps strong {
  color: var(--accent);
}

.setup-steps code {
  background: var(--bg-highlight);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  color: var(--text-primary);
}

.refresh-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  margin-top: 8px;
  transition: opacity 0.2s;
}

.refresh-btn:hover {
  opacity: 0.9;
}

/* Range slider styles */
.slider-row {
  flex-direction: column;
  align-items: stretch !important;
  gap: 15px;
  padding-bottom: 20px;
}

.slider-row .setting-info {
  display: flex;
  justify-content: space-between;
  width: 100%;
}

.range-slider {
  width: 100%;
  height: 6px;
  background: var(--bg-tertiary);
  border-radius: 3px;
  outline: none;
  -webkit-appearance: none;
}

.range-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
  transition: transform 0.1s;
}

.range-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.setting-value {
  color: var(--accent);
  font-weight: 500;
  font-size: 14px;
}

.scale-desc {
  color: var(--text-tertiary);
  font-size: 13px;
  margin-top: 8px;
  display: block;
}
</style>
