<template>
  <section id="discord" class="settings-section">
    <div class="section-header">
      <h2>
        <svg width="18" height="18" viewBox="0 0 127.14 96.36" fill="currentColor" class="discord-header-icon">
          <path d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,45.91,53.88,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,45.91,96.12,53,91.08,65.69,84.69,65.69Z"/>
        </svg>
        <span>Интеграция с Discord</span>
      </h2>
      <span class="status-pill discord-status" :class="{ connected: isBotOnline }">
        <Check v-if="isBotOnline" :size="12" />
        {{ !discordStore.configured ? 'Не настроен' : (isBotOnline ? 'Бот онлайн' : 'Подключение...') }}
      </span>
    </div>

    <div class="settings-card discord-card">
      <p class="service-desc">
        Транслируйте музыку прямо в голосовой канал Discord для совместных посиделок с друзьями в высоком Hi-Fi качестве. 
        Управляйте громкостью, очередью и скипами треков прямо из плеера AuxBass.
      </p>

      <!-- Bot Invite Banner -->
      <div v-if="discordStore.inviteUrl" class="bot-invite-box">
        <div class="invite-info">
          <div class="invite-icon-wrap">
            <Radio :size="22" />
          </div>
          <div class="invite-text-wrap">
            <span class="invite-title">Добавить бота на свой сервер Discord</span>
            <span class="invite-desc">Бот сможет подключаться к голосовым комнатам вашей компании</span>
          </div>
        </div>
        <a 
          :href="discordStore.inviteUrl" 
          target="_blank" 
          rel="noopener noreferrer" 
          class="action-btn primary discord-invite-btn"
        >
          <ExternalLink :size="14" />
          <span>Пригласить бота</span>
        </a>
      </div>

      <!-- Account Linking Section -->
      <div class="linking-box">
        <div class="sub-header">
          <UserCheck :size="16" />
          <span>Привязка Discord аккаунта</span>
        </div>
        <p class="sub-desc">
          Укажите ваш Discord User ID, чтобы бот автоматически определял, в каком голосовом канале вы сидите, и подключался в один клик.
        </p>

        <!-- If linked -->
        <div v-if="discordStore.isLinked" class="linked-row">
          <div class="linked-info">
            <CheckCircle2 :size="16" class="check-icon" />
            <div class="linked-details">
              <span class="linked-id">ID: {{ linkedIdDisplay }}</span>
              <span v-if="discordStore.linkedDiscordUsername" class="linked-name">
                @{{ discordStore.linkedDiscordUsername }}
              </span>
            </div>
          </div>
          <button class="unlink-btn" @click="handleUnlink" :disabled="isSaving">
            <Trash2 :size="14" />
            <span>Отвязать</span>
          </button>
        </div>

        <!-- Form if not linked -->
        <div v-else class="link-form">
          <div class="input-row">
            <input 
              v-model="inputDiscordId" 
              type="text" 
              class="neu-input"
              placeholder="Например: 123456789012345678"
              @keydown.enter="handleLink"
            />
            <button 
              class="action-btn primary save-btn" 
              :disabled="!inputDiscordId.trim() || isSaving"
              @click="handleLink"
            >
              <span>{{ isSaving ? 'Сохранение...' : 'Привязать' }}</span>
            </button>
          </div>
          <div class="hint-text">
            💡 Как узнать свой Discord ID: В настройках Discord включите <b>«Режим разработчика»</b> (Настройки -> Расширенные), затем кликните правой кнопкой по своему профилю и нажмите <b>«Копировать ID пользователя»</b>.
          </div>
        </div>
      </div>

      <!-- Detected Voice Channel Status -->
      <div v-if="discordStore.detectedUserChannel" class="detected-channel-box">
        <div class="detected-left">
          <div class="live-dot"></div>
          <div>
            <div class="detected-title">Вы сейчас в голосовом канале:</div>
            <div class="detected-meta">
              #{{ discordStore.detectedUserChannel.channel_name }} ({{ discordStore.detectedUserChannel.guild_name }})
            </div>
          </div>
        </div>
        <button class="action-btn secondary test-connect-btn" @click="discordStore.openPartyModal()">
          <span>Открыть пульт</span>
        </button>
      </div>

      <!-- Available Guilds List -->
      <div v-if="discordStore.availableChannels.length > 0" class="servers-list-box">
        <div class="sub-header">
          <Shield :size="16" />
          <span>Серверы, где подключен бот ({{ discordStore.availableChannels.length }}):</span>
        </div>
        <div class="servers-chips-grid">
          <div 
            v-for="guild in discordStore.availableChannels" 
            :key="guild.guild_id"
            class="server-chip"
          >
            <img v-if="guild.guild_icon" :src="guild.guild_icon" class="server-icon" alt="" />
            <div v-else class="server-icon fallback">{{ guild.guild_name.charAt(0) }}</div>
            <span class="server-name">{{ guild.guild_name }}</span>
            <span class="server-ch-count">{{ guild.channels.length }} комнат</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Check, Radio, ExternalLink, UserCheck, CheckCircle2,
  Trash2, Shield
} from 'lucide-vue-next'
import { useDiscordStore } from '@/stores/discord'

const discordStore = useDiscordStore()

const inputDiscordId = ref('')
const isSaving = ref(false)

const isBotOnline = computed(() => {
  return discordStore.configured && discordStore.botReady
})

const linkedIdDisplay = computed(() => {
  return discordStore.linkedDiscordUsername || 'Привязан'
})

onMounted(async () => {
  await Promise.allSettled([
    discordStore.fetchUserState(),
    discordStore.fetchAvailableChannels(),
    discordStore.fetchInvite(),
  ])
})

async function handleLink() {
  const raw = inputDiscordId.value.trim()
  if (!raw || !raw.match(/^\d+$/)) {
    alert('Discord ID должен состоять только из цифр (17-19 знаков).')
    return
  }
  isSaving.value = true
  try {
    await discordStore.linkAccount(raw)
    inputDiscordId.value = ''
  } catch (e) {
    alert(e.response?.data?.detail || 'Ошибка при привязке Discord ID')
  } finally {
    isSaving.value = false
  }
}

async function handleUnlink() {
  if (!confirm('Отвязать ваш Discord аккаунт?')) return
  isSaving.value = true
  try {
    await discordStore.unlinkAccount()
  } catch (e) {
    console.error('Failed to unlink:', e)
  } finally {
    isSaving.value = false
  }
}
</script>

<style scoped>
.settings-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-header h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  margin: 0;
}

.discord-header-icon {
  color: #5865f2;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
  background: var(--c-bg-3);
  color: var(--c-text-2);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.status-pill.connected {
  background: rgba(29, 185, 84, 0.12);
  color: var(--c-accent, #1db954);
  border-color: rgba(29, 185, 84, 0.3);
}

.settings-card {
  background: var(--c-bg-2, #1a1a1a);
  border-radius: var(--r-lg, 16px);
  padding: 18px;
  box-shadow: 4px 4px 10px var(--sh-dark), -2px -2px 6px var(--sh-light);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.service-desc {
  font-size: 13px;
  color: var(--c-text-2, #b0b0b0);
  line-height: 1.5;
  margin: 0 0 16px 0;
}

/* Invite Banner */
.bot-invite-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(88, 101, 242, 0.1);
  border: 1px solid rgba(88, 101, 242, 0.25);
  border-radius: var(--r-md, 12px);
  padding: 12px 14px;
  margin-bottom: 16px;
  gap: 12px;
}

.invite-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.invite-icon-wrap {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: #5865f2;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 10px rgba(88, 101, 242, 0.35);
}

.invite-text-wrap {
  display: flex;
  flex-direction: column;
}

.invite-title {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--c-text-1);
}

.invite-desc {
  font-size: 11.5px;
  color: var(--c-text-2);
}

.discord-invite-btn {
  background: linear-gradient(135deg, #5865f2 0%, #4752c4 100%) !important;
  color: #fff !important;
  border: none !important;
  box-shadow: 0 4px 12px rgba(88, 101, 242, 0.3) !important;
  text-decoration: none;
  white-space: nowrap;
}

/* Linking Box */
.linking-box {
  background: var(--c-bg-1);
  border-radius: var(--r-md, 12px);
  padding: 14px;
  box-shadow: inset 2px 2px 5px var(--sh-inset-dark), inset -1px -1px 3px var(--sh-inset-light);
  margin-bottom: 16px;
}

.sub-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--c-text-1);
  margin-bottom: 4px;
}

.sub-desc {
  font-size: 12px;
  color: var(--c-text-2);
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.linked-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--c-bg-2);
  padding: 10px 12px;
  border-radius: var(--r-md, 12px);
  border: 1px solid rgba(29, 185, 84, 0.2);
}

.linked-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.check-icon {
  color: var(--c-accent, #1db954);
}

.linked-details {
  display: flex;
  flex-direction: column;
}

.linked-id {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1);
}

.linked-name {
  font-size: 11px;
  color: var(--c-text-2);
}

.unlink-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  background: none;
  border: 1px solid rgba(244, 67, 54, 0.3);
  color: #f44336;
  font-size: 11.5px;
  font-weight: 600;
  padding: 5px 10px;
  border-radius: 8px;
  cursor: pointer;
}

.input-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.neu-input {
  flex: 1;
  background: var(--c-bg-2);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: var(--r-md, 12px);
  padding: 9px 12px;
  font-size: 13px;
  color: var(--c-text-1);
  outline: none;
  box-shadow: inset 2px 2px 4px var(--sh-inset-dark);
}

.neu-input:focus {
  border-color: #5865f2;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: var(--r-md, 12px);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.action-btn.primary {
  background: linear-gradient(135deg, #5865f2 0%, #4752c4 100%);
  color: #fff;
  border: none;
}

.action-btn.secondary {
  background: var(--c-bg-3);
  color: var(--c-text-1);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.hint-text {
  font-size: 11px;
  color: var(--c-text-2);
  line-height: 1.4;
}

/* Detected Channel Box */
.detected-channel-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(29, 185, 84, 0.08);
  border: 1px solid rgba(29, 185, 84, 0.25);
  border-radius: var(--r-md, 12px);
  padding: 10px 14px;
  margin-bottom: 16px;
}

.detected-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--c-accent, #1db954);
  box-shadow: 0 0 8px var(--c-accent, #1db954);
}

.detected-title {
  font-size: 11px;
  color: var(--c-text-2);
}

.detected-meta {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-accent, #1db954);
}

/* Servers List */
.servers-chips-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.server-chip {
  display: flex;
  align-items: center;
  gap: 7px;
  background: var(--c-bg-1);
  padding: 6px 10px;
  border-radius: var(--r-md, 12px);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.server-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  object-fit: cover;
}

.server-icon.fallback {
  background: var(--c-bg-3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: bold;
  color: var(--c-text-1);
}

.server-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-1);
}

.server-ch-count {
  font-size: 10px;
  color: var(--c-text-2);
}
</style>
