<template>
  <div class="settings-view">
    <h1>Настройки</h1>

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

    <!-- Playback settings -->
    <section class="section">
      <h2>Воспроизведение</h2>
      
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Перемешивание</span>
          <span class="setting-desc">Случайный порядок воспроизведения</span>
        </div>
        <label class="toggle">
          <input type="checkbox" v-model="playerStore.shuffle" />
          <span class="toggle-slider"></span>
        </label>
      </div>

      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Повтор</span>
          <span class="setting-desc">
            {{ repeatModeText }}
          </span>
        </div>
        <button class="repeat-btn" @click="toggleRepeat">
          {{ repeatModeIcon }}
        </button>
      </div>
    </section>

    <!-- Appearance -->
    <section class="section">
      <h2>Оформление</h2>
      
      <div class="setting-row">
        <div class="setting-info">
          <span class="setting-name">Тёмная тема</span>
          <span class="setting-desc">Включена по умолчанию</span>
        </div>
        <label class="toggle">
          <input type="checkbox" v-model="darkMode" />
          <span class="toggle-slider"></span>
        </label>
      </div>
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
      <p>TG Player v2.0</p>
      <p class="about-desc">
        Музыкальный плеер с хранением в Telegram
      </p>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import api from '@/api/client'

const router = useRouter()
const authStore = useAuthStore()
const playerStore = usePlayerStore()

const stats = ref(null)
const darkMode = ref(true)

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

const logout = () => {
  authStore.logout()
  router.push('/login')
}

const clearCache = () => {
  // Clear any cached data
  localStorage.removeItem('tracks_cache')
  localStorage.removeItem('albums_cache')
  alert('Кэш очищен')
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.settings-view {
  padding: 16px;
  padding-bottom: 120px;
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
}

.setting-row:last-child {
  border-bottom: none;
}

.setting-info {
  display: flex;
  flex-direction: column;
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
</style>
