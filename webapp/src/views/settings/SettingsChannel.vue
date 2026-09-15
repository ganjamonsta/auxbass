<template>
  <section id="channel" class="settings-section">
    <div class="section-header">
      <h2>
        <Megaphone :size="18" />
        <span>Канал для бэкапа</span>
      </h2>
      <span class="status-pill" :class="{ connected: authStore.hasChannel }">
        <Check v-if="authStore.hasChannel" :size="12" />
        {{ authStore.hasChannel ? 'Подключён' : 'Не привязан' }}
      </span>
    </div>

    <div class="settings-card channel-card" :class="{ 'not-connected': !authStore.hasChannel }">
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
            <button 
              class="action-btn secondary check-access-btn" 
              :disabled="isRefreshingChannel" 
              @click="refreshStatus" 
              title="Проверить права бота в канале"
            >
              <RefreshCw :size="12" :class="{ 'spin-anim': isRefreshingChannel }" />
              <span>{{ isRefreshingChannel ? 'Проверка...' : 'Проверить' }}</span>
            </button>
          </div>
          <div class="channel-features">
            <div class="feature-item"><Check :size="13" /> Сохранение треков</div>
            <div class="feature-item"><Check :size="13" /> Создание плейлистов</div>
            <div class="feature-item"><Check :size="13" /> Автобэкап в канал</div>
          </div>
        </div>
      </template>

      <template v-else>
        <div class="channel-not-connected">
          <p class="channel-desc">
            Подключите Telegram-канал, чтобы разблокировать все функции:
          </p>
          <ul class="feature-list">
            <li><Folder :size="15" /> Загрузка и сохранение треков</li>
            <li><Heart :size="15" /> Лайки и избранное</li>
            <li><ListMusic :size="15" /> Создание плейлистов</li>
            <li><Cloud :size="15" /> Автоматический бэкап музыки</li>
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
          <p v-if="authStore.channelError" class="channel-error-msg">
            <AlertCircle :size="14" />
            <span>{{ authStore.channelError }}</span>
          </p>
          <button class="action-btn primary channel-refresh-btn" :disabled="isRefreshingChannel" @click="refreshStatus">
            <RefreshCw :size="15" :class="{ 'spin-anim': isRefreshingChannel }" />
            <span>{{ isRefreshingChannel ? 'Проверка прав...' : 'Обновить статус' }}</span>
          </button>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Megaphone, Check, Folder, Heart, ListMusic, Cloud, RefreshCw, AlertCircle } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { authApi } from '@/api/client'

const authStore = useAuthStore()
const uiStore = useUIStore()

const botUsername = ref('tg_player_bot')
const isRefreshingChannel = ref(false)

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
  if (isRefreshingChannel.value) return
  isRefreshingChannel.value = true
  try {
    const res = await authStore.verifyChannel()
    if (res.has_channel) {
      uiStore.toast.success('Канал активен', `Бот подключён к «${res.channel_info?.channel_title || 'каналу'}»`)
    } else {
      uiStore.toast.warning('Канал недоступен', res.error || 'Бот не имеет прав администратора в канале')
    }
  } catch (err) {
    uiStore.toast.error('Ошибка проверки', 'Не удалось проверить статус канала')
  } finally {
    isRefreshingChannel.value = false
  }
}

onMounted(() => {
  loadBotConfig()
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

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: var(--r-full);
  background: rgba(255, 255, 255, 0.05);
  color: var(--c-text-3);
  border: 1px solid rgba(255, 255, 255, 0.04);
  line-height: 1.2;
  flex-shrink: 0;
}

.status-pill.connected {
  background: rgba(29, 185, 84, 0.12);
  color: #1db954;
  border-color: rgba(29, 185, 84, 0.25);
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
  background: rgba(29, 185, 84, 0.1);
  color: #1db954;
  display: flex;
  align-items: center;
  justify-content: center;
}

.channel-details {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.channel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text-1);
}

.channel-username {
  font-size: 13px;
  color: var(--c-text-2);
}

.channel-features {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background: var(--c-bg-3);
  border-radius: var(--r-md);
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--c-text-2);
}

.feature-item svg {
  color: #1db954;
}

.channel-not-connected {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.channel-desc {
  font-size: 14px;
  color: var(--c-text-2);
  margin: 0;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--c-text-1);
}

.feature-list svg {
  color: var(--c-accent);
}

.setup-steps {
  background: var(--c-bg-3);
  padding: 16px;
  border-radius: var(--r-md);
}

.setup-steps h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text-1);
  margin: 0 0 10px 0;
}

.setup-steps ol {
  margin: 0;
  padding-left: 20px;
  color: var(--c-text-2);
  font-size: 13px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.channel-error-msg {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ff4d4f;
  font-size: 13px;
  margin: 0;
  padding: 10px;
  background: rgba(255, 77, 79, 0.1);
  border-radius: var(--r-sm);
}

.spin-anim {
  animation: spin 1s linear infinite;
}

/* @keyframes spin — defined in design-system.css */

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: var(--r-full, 9999px);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.action-btn.primary {
  background: var(--c-accent);
  color: #000;
}

.action-btn.secondary {
  background: var(--c-bg-3);
  color: var(--c-text-1);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
