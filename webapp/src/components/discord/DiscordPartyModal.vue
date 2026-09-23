<template>
  <Teleport to="body">
    <Transition name="fade">
      <div 
        v-if="discordStore.showPartyModal" 
        class="discord-modal-overlay"
        @click.self="closeModal"
      >
        <Transition name="scale">
          <div v-if="discordStore.showPartyModal" class="discord-modal-dialog" @click.stop>
            <!-- ═══ Modal Header ═══ -->
            <div class="modal-header">
              <div class="header-left">
                <div class="discord-logo-icon">
                  <svg width="20" height="20" viewBox="0 0 127.14 96.36" fill="currentColor">
                    <path d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,45.91,53.88,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,45.91,96.12,53,91.08,65.69,84.69,65.69Z"/>
                  </svg>
                </div>
                <div class="header-titles">
                  <h3 class="modal-title">Тусовка в Discord</h3>
                  <span class="modal-subtitle">
                    {{ discordStore.guildName ? `${discordStore.guildName} • #${discordStore.channelName}` : 'Управление трансляцией' }}
                  </span>
                </div>
              </div>
              <button class="close-btn" @click="closeModal" title="Закрыть">
                <X :size="20" />
              </button>
            </div>

            <!-- ═══ Modal Body ═══ -->
            <div class="modal-body">
              <!-- Active Playback Section -->
              <div v-if="discordStore.hasParty" class="party-player-box">
                <!-- Track row -->
                <div class="player-track-row">
                  <div class="track-cover-box">
                    <img 
                      v-if="trackCoverUrl" 
                      :src="trackCoverUrl" 
                      alt="Cover" 
                      class="cover-img"
                    />
                    <div v-else class="cover-fallback">
                      <Disc :size="26" />
                    </div>
                  </div>
                  <div class="track-text-box">
                    <div class="track-title">{{ discordStore.currentTrack?.title || 'Ничего не играет' }}</div>
                    <div class="track-artist">{{ discordStore.currentTrack?.artist || 'Очередь пуста' }}</div>
                    <div v-if="discordStore.hostUser" class="host-pill">
                      <Crown :size="12" class="crown-icon" />
                      <span>DJ: {{ discordStore.hostUser.display_name }}</span>
                    </div>
                  </div>
                </div>

                <!-- Progress Slider -->
                <div class="progress-bar-container">
                  <input 
                    type="range"
                    class="neu-slider progress-slider"
                    :value="discordStore.position"
                    :max="discordStore.duration || 100"
                    :disabled="!discordStore.canControl"
                    @input="handleSeek(Number($event.target.value))"
                  />
                  <div class="time-row">
                    <span>{{ formatTime(discordStore.position) }}</span>
                    <span>{{ formatTime(discordStore.duration) }}</span>
                  </div>
                </div>

                <!-- Playback Controls -->
                <div class="controls-row">
                  <button 
                    class="control-btn" 
                    :disabled="!discordStore.canControl"
                    @click="handleSkip"
                    title="Следующий трек"
                  >
                    <SkipForward :size="20" />
                  </button>
                  <button 
                    class="control-btn play-btn" 
                    :disabled="!discordStore.canControl"
                    @click="togglePlayPause"
                    title="Воспроизведение / Пауза"
                  >
                    <Pause v-if="discordStore.isPlaying" :size="24" />
                    <Play v-else :size="24" />
                  </button>
                  <button 
                    class="control-btn" 
                    :disabled="!discordStore.canControl"
                    @click="handleStop"
                    title="Остановить"
                  >
                    <Square :size="18" />
                  </button>
                </div>

                <!-- Volume Slider -->
                <div class="volume-row">
                  <Volume2 :size="16" class="volume-icon" />
                  <input 
                    type="range" 
                    class="neu-slider volume-slider"
                    :value="discordStore.volume"
                    min="0"
                    max="100"
                    @input="discordStore.setVolume(Number($event.target.value))"
                  />
                  <span class="volume-label">{{ discordStore.volume }}%</span>
                </div>

                <!-- Mode Toggles (DJ Lock & Listen Along) -->
                <div class="toggles-grid">
                  <!-- DJ Lock (only host can toggle) -->
                  <div 
                    class="neu-toggle-card"
                    :class="{ active: discordStore.djLock, disabled: !discordStore.isHost }"
                    @click="toggleDjLock"
                    title="Только DJ может переключать треки и ставить на паузу"
                  >
                    <div class="toggle-icon-wrap">
                      <Lock v-if="discordStore.djLock" :size="16" />
                      <Unlock v-else :size="16" />
                    </div>
                    <div class="toggle-info">
                      <span class="toggle-title">Режим DJ Lock</span>
                      <span class="toggle-sub">{{ discordStore.djLock ? 'Только DJ управляет' : 'Все могут управлять' }}</span>
                    </div>
                  </div>

                  <!-- Listen Along -->
                  <div 
                    class="neu-toggle-card"
                    :class="{ active: discordStore.listenAlong }"
                    @click="discordStore.toggleListenAlong"
                    title="Слушать аудио синхронно в плеере браузера"
                  >
                    <div class="toggle-icon-wrap">
                      <Headphones :size="16" />
                    </div>
                    <div class="toggle-info">
                      <span class="toggle-title">Слушать в браузере</span>
                      <span class="toggle-sub">{{ discordStore.listenAlong ? 'Включено' : 'Только в Discord' }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Channel Selector (If bot not connected or switching channels) -->
              <div v-else class="party-connect-box">
                <div class="connect-prompt-title">Подключить бота к голосовому каналу</div>
                <div class="connect-prompt-desc">
                  Выберите сервер и канал, чтобы запустить музыку для друзей:
                </div>
                
                <div v-if="discordStore.availableChannels.length > 0" class="guilds-select-list">
                  <div 
                    v-for="guild in discordStore.availableChannels" 
                    :key="guild.guild_id"
                    class="guild-group"
                  >
                    <div class="guild-group-header">
                      <img v-if="guild.guild_icon" :src="guild.guild_icon" class="guild-icon-small" alt="" />
                      <span>{{ guild.guild_name }}</span>
                    </div>
                    <div class="channels-chips">
                      <button 
                        v-for="ch in guild.channels" 
                        :key="ch.id"
                        class="channel-chip"
                        @click="handleConnect(ch.id)"
                      >
                        <Volume2 :size="14" />
                        <span>{{ ch.name }}</span>
                        <span v-if="ch.user_count > 0" class="chip-count">({{ ch.user_count }})</span>
                      </button>
                    </div>
                  </div>
                </div>
                <div v-else class="no-channels-box">
                  <p>Бот не найден ни на одном сервере с правами подключения к голосовым каналам.</p>
                  <a 
                    v-if="discordStore.inviteUrl" 
                    :href="discordStore.inviteUrl" 
                    target="_blank" 
                    class="neu-invite-btn"
                  >
                    <ExternalLink :size="15" />
                    <span>Пригласить бота на свой Discord сервер</span>
                  </a>
                </div>
              </div>

              <!-- Tabs: Members / Queue -->
              <div v-if="discordStore.hasParty" class="party-tabs-row">
                <button 
                  class="party-tab-btn" 
                  :class="{ active: activeTab === 'members' }"
                  @click="activeTab = 'members'"
                >
                  <Users :size="15" />
                  <span>Участники ({{ discordStore.activePartyMembers.length }})</span>
                </button>
                <button 
                  class="party-tab-btn" 
                  :class="{ active: activeTab === 'queue' }"
                  @click="activeTab = 'queue'"
                >
                  <ListMusic :size="15" />
                  <span>Очередь ({{ discordStore.queue.length }})</span>
                </button>
              </div>

              <!-- Tab 1: Members List -->
              <div v-if="discordStore.hasParty && activeTab === 'members'" class="members-tab-content">
                <div 
                  v-for="member in discordStore.activePartyMembers" 
                  :key="member.id"
                  class="member-list-item"
                >
                  <div class="member-left">
                    <div class="member-avatar">
                      <img v-if="member.avatar_url" :src="member.avatar_url" alt="" />
                      <div v-else class="avatar-fallback">{{ member.display_name?.charAt(0) }}</div>
                    </div>
                    <div class="member-name-box">
                      <div class="member-name">
                        {{ member.display_name }}
                        <span v-if="isMemberDJ(member)" class="dj-crown-badge">
                          <Crown :size="12" /> DJ
                        </span>
                      </div>
                      <div class="member-status-text">
                        <span v-if="member.is_deaf" class="status-warn">Глухой</span>
                        <span v-else-if="member.is_muted" class="status-muted">Микрофон выкл.</span>
                        <span v-else class="status-live">Слушает</span>
                      </div>
                    </div>
                  </div>
                  <div class="member-actions">
                    <button 
                      v-if="discordStore.isHost && !isMemberDJ(member)"
                      class="transfer-dj-btn"
                      @click="handleTransferDj(member.id)"
                      title="Передать роль DJ"
                    >
                      <Crown :size="14" />
                      <span>Сделать DJ</span>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Tab 2: Collaborative Queue -->
              <div v-if="discordStore.hasParty && activeTab === 'queue'" class="queue-tab-content">
                <div v-if="discordStore.queue.length === 0" class="empty-queue-hint">
                  Очередь пуста. Выберите любой трек в поиске или медиатеке и нажмите «Добавить в тусовку Discord»!
                </div>
                <div 
                  v-for="(item, idx) in discordStore.queue" 
                  :key="idx"
                  class="queue-item"
                  :class="{ 'current-playing': idx === discordStore.queueIndex }"
                >
                  <span class="queue-pos">{{ idx + 1 }}</span>
                  <div class="queue-info">
                    <div class="queue-title">{{ item.title }}</div>
                    <div class="queue-sub">
                      <span>{{ item.artist }}</span>
                      <span v-if="item.added_by" class="added-by-badge">
                        👤 {{ item.added_by.display_name || item.added_by.username }}
                      </span>
                    </div>
                  </div>
                  <button 
                    v-if="canRemoveTrack(item)"
                    class="remove-queue-btn"
                    @click="discordStore.removeFromQueue(idx)"
                    title="Удалить из очереди"
                  >
                    <Trash2 :size="14" />
                  </button>
                </div>
              </div>

              <!-- Bottom Actions: Disconnect / Invite -->
              <div v-if="discordStore.hasParty" class="party-bottom-actions">
                <button class="disconnect-btn" @click="handleDisconnect">
                  <Power :size="15" />
                  <span>Отключить бота</span>
                </button>
                <a 
                  v-if="discordStore.inviteUrl" 
                  :href="discordStore.inviteUrl" 
                  target="_blank" 
                  class="invite-link-btn"
                  title="Пригласить бота на другой сервер"
                >
                  <ExternalLink :size="14" />
                  <span>Ссылка на бота</span>
                </a>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  X, Disc, Crown, Play, Pause, SkipForward, Square,
  Volume2, Lock, Unlock, Headphones, Users, ListMusic,
  Trash2, Power, ExternalLink
} from 'lucide-vue-next'
import { useDiscordStore } from '@/stores/discord'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'

const discordStore = useDiscordStore()
const authStore = useAuthStore()
const playerStore = usePlayerStore()

const activeTab = ref('members') // 'members' | 'queue'

onMounted(() => {
  if (discordStore.availableChannels.length === 0) {
    discordStore.fetchAvailableChannels()
  }
})

const trackCoverUrl = computed(() => {
  const track = discordStore.currentTrack
  if (!track || !track.cover_url) return null
  if (track.cover_url.startsWith('http') || track.cover_url.startsWith('/api')) {
    return track.cover_url
  }
  return `/api/images/${track.cover_url}`
})

function closeModal() {
  discordStore.closePartyModal()
}

function formatTime(seconds) {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function isMemberDJ(member) {
  if (!discordStore.hostUser) return false
  return (
    String(member.id) === String(discordStore.hostUser.discord_id) ||
    member.display_name === discordStore.hostUser.display_name
  )
}

function canRemoveTrack(item) {
  if (discordStore.isHost) return true
  if (item.added_by && authStore.user) {
    return item.added_by.id === authStore.user.id
  }
  return false
}

async function handleConnect(channelId) {
  try {
    await discordStore.connectToChannel(channelId)
    if (playerStore.currentTrack) {
      await discordStore.play(playerStore.currentTrack, playerStore.queue, playerStore.progress)
    }
  } catch (e) {
    console.error('Failed to connect:', e)
  }
}

async function handleDisconnect() {
  try {
    await discordStore.disconnect()
    closeModal()
  } catch (e) {
    console.error('Failed to disconnect:', e)
  }
}

async function togglePlayPause() {
  if (discordStore.isPlaying) {
    await discordStore.pause()
  } else {
    await discordStore.resume()
  }
}

async function handleSkip() {
  await discordStore.skip()
}

async function handleStop() {
  await discordStore.stop()
}

async function handleSeek(pos) {
  await discordStore.seek(pos)
}

async function toggleDjLock() {
  if (!discordStore.isHost) return
  await discordStore.setDjLock(!discordStore.djLock)
}

async function handleTransferDj(memberId) {
  await discordStore.transferDj(memberId)
}
</script>

<style scoped>
.discord-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  z-index: var(--z-modal, 1200);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.discord-modal-dialog {
  background: var(--c-bg-1, #121212);
  border-radius: var(--r-xl, 20px);
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6), 0 0 30px rgba(88, 101, 242, 0.15);
  border: 1px solid rgba(88, 101, 242, 0.25);
  overflow: hidden;
}

/* Header */
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--c-bg-2, #1a1a1a);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.discord-logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #5865f2 0%, #4752c4 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 3px 10px rgba(88, 101, 242, 0.35);
}

.modal-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  margin: 0;
}

.modal-subtitle {
  font-size: 11.5px;
  color: var(--c-text-2, #b0b0b0);
}

.close-btn {
  background: none;
  border: none;
  color: var(--c-text-2);
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.15s;
}

.close-btn:hover {
  color: var(--c-text-1);
}

/* Body */
.modal-body {
  padding: 16px 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* Player Box */
.party-player-box {
  background: var(--c-bg-2);
  border-radius: var(--r-lg, 16px);
  padding: 14px;
  box-shadow: 4px 4px 10px var(--sh-dark), -2px -2px 6px var(--sh-light);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.player-track-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.track-cover-box {
  width: 52px;
  height: 52px;
  border-radius: 10px;
  overflow: hidden;
  background: var(--c-bg-3);
  flex-shrink: 0;
  box-shadow: 2px 2px 6px rgba(0, 0, 0, 0.4);
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-2);
}

.track-text-box {
  flex: 1;
  min-width: 0;
}

.track-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-artist {
  font-size: 12px;
  color: var(--c-text-2);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.host-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 215, 0, 0.12);
  border: 1px solid rgba(255, 215, 0, 0.25);
  border-radius: 10px;
  padding: 2px 6px;
  font-size: 10.5px;
  color: #ffd700;
  font-weight: 600;
  margin-top: 4px;
}

.crown-icon {
  color: #ffd700;
}

/* Sliders */
.progress-bar-container {
  margin-bottom: 12px;
}

.neu-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: var(--c-bg-1);
  box-shadow: inset 1px 1px 3px var(--sh-inset-dark), inset -1px -1px 2px var(--sh-inset-light);
  outline: none;
  appearance: none;
  accent-color: #5865f2;
}

.time-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--c-text-2);
  margin-top: 4px;
}

.controls-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 12px;
}

.control-btn {
  background: var(--c-bg-3);
  border: 1px solid rgba(255, 255, 255, 0.04);
  color: var(--c-text-1);
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 3px 3px 8px var(--sh-dark), -2px -2px 6px var(--sh-light);
  transition: all 0.15s ease;
}

.control-btn:active:not(:disabled) {
  transform: scale(0.95);
  box-shadow: inset 2px 2px 4px var(--sh-inset-dark);
}

.control-btn.play-btn {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #5865f2 0%, #4752c4 100%);
  color: #fff;
  border: none;
  box-shadow: 0 4px 14px rgba(88, 101, 242, 0.4);
}

.control-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.volume-row {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--c-bg-1);
  padding: 8px 12px;
  border-radius: var(--r-md, 12px);
  box-shadow: inset 2px 2px 4px var(--sh-inset-dark);
  margin-bottom: 12px;
}

.volume-icon {
  color: var(--c-text-2);
}

.volume-slider {
  flex: 1;
}

.volume-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--c-text-2);
  width: 32px;
  text-align: right;
}

.toggles-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.neu-toggle-card {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--c-bg-1);
  border-radius: var(--r-md, 12px);
  padding: 8px 10px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.03);
  transition: all 0.15s ease;
}

.neu-toggle-card.active {
  border-color: rgba(88, 101, 242, 0.4);
  background: rgba(88, 101, 242, 0.1);
}

.neu-toggle-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toggle-icon-wrap {
  color: var(--c-text-2);
}

.neu-toggle-card.active .toggle-icon-wrap {
  color: #7289da;
}

.toggle-info {
  display: flex;
  flex-direction: column;
}

.toggle-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--c-text-1);
}

.toggle-sub {
  font-size: 9.5px;
  color: var(--c-text-2);
}

/* Tabs */
.party-tabs-row {
  display: flex;
  gap: 8px;
  background: var(--c-bg-2);
  padding: 4px;
  border-radius: var(--r-md, 12px);
  box-shadow: inset 2px 2px 4px var(--sh-inset-dark);
}

.party-tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 7px 12px;
  border-radius: 8px;
  background: none;
  border: none;
  color: var(--c-text-2);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.party-tab-btn.active {
  background: var(--c-bg-3);
  color: var(--c-text-1);
  box-shadow: 2px 2px 6px var(--sh-dark);
}

/* Members Tab */
.members-tab-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 180px;
  overflow-y: auto;
}

.member-list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: var(--c-bg-2);
  border-radius: var(--r-md, 12px);
  border: 1px solid rgba(255, 255, 255, 0.03);
}

.member-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.member-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--c-bg-4);
  flex-shrink: 0;
}

.member-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  color: var(--c-text-1);
}

.member-name {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--c-text-1);
  display: flex;
  align-items: center;
  gap: 5px;
}

.dj-crown-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 9.5px;
  color: #ffd700;
  background: rgba(255, 215, 0, 0.15);
  border-radius: 6px;
  padding: 1px 4px;
}

.member-status-text {
  font-size: 10.5px;
}

.status-live { color: var(--c-accent, #1db954); }
.status-muted { color: var(--c-text-2); }
.status-warn { color: #f44336; }

.transfer-dj-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--c-bg-3);
  border: 1px solid rgba(255, 215, 0, 0.3);
  color: #ffd700;
  font-size: 10.5px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 8px;
  cursor: pointer;
}

/* Queue Tab */
.queue-tab-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 180px;
  overflow-y: auto;
}

.empty-queue-hint {
  font-size: 12px;
  color: var(--c-text-2);
  text-align: center;
  padding: 16px;
  line-height: 1.4;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  background: var(--c-bg-2);
  border-radius: var(--r-md, 12px);
  border: 1px solid rgba(255, 255, 255, 0.03);
}

.queue-item.current-playing {
  border-color: rgba(29, 185, 84, 0.4);
  background: rgba(29, 185, 84, 0.06);
}

.queue-pos {
  font-size: 12px;
  font-weight: bold;
  color: var(--c-text-2);
  width: 16px;
  text-align: center;
}

.queue-info {
  flex: 1;
  min-width: 0;
}

.queue-title {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-sub {
  font-size: 10.5px;
  color: var(--c-text-2);
  display: flex;
  align-items: center;
  gap: 8px;
}

.added-by-badge {
  color: #7289da;
}

.remove-queue-btn {
  background: none;
  border: none;
  color: var(--c-text-2);
  cursor: pointer;
  padding: 4px;
}

.remove-queue-btn:hover {
  color: #f44336;
}

/* Bottom Actions */
.party-bottom-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}

.disconnect-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(244, 67, 54, 0.12);
  border: 1px solid rgba(244, 67, 54, 0.3);
  color: #f44336;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: var(--r-md, 12px);
  cursor: pointer;
}

.invite-link-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  color: #7289da;
  text-decoration: none;
}

/* Channel Picker Prompt */
.party-connect-box {
  background: var(--c-bg-2);
  border-radius: var(--r-lg, 16px);
  padding: 16px;
}

.connect-prompt-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--c-text-1);
  margin-bottom: 4px;
}

.connect-prompt-desc {
  font-size: 12px;
  color: var(--c-text-2);
  margin-bottom: 14px;
}

.guild-group {
  margin-bottom: 12px;
}

.guild-group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #7289da;
  margin-bottom: 6px;
}

.guild-icon-small {
  width: 18px;
  height: 18px;
  border-radius: 50%;
}

.channels-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.channel-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: var(--c-bg-3);
  border: 1px solid rgba(255, 255, 255, 0.04);
  color: var(--c-text-1);
  font-size: 12px;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: var(--r-md, 12px);
  cursor: pointer;
  box-shadow: 2px 2px 5px var(--sh-dark);
}

.channel-chip:hover {
  border-color: rgba(88, 101, 242, 0.4);
}

.chip-count {
  font-size: 10px;
  color: var(--c-accent, #1db954);
}

.neu-invite-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, #5865f2 0%, #4752c4 100%);
  color: #fff;
  padding: 8px 14px;
  border-radius: var(--r-md, 12px);
  text-decoration: none;
  font-size: 12px;
  font-weight: 600;
  margin-top: 8px;
}

/* Animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.scale-enter-active,
.scale-leave-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.scale-enter-from,
.scale-leave-to {
  opacity: 0;
  transform: scale(0.94);
}
</style>
