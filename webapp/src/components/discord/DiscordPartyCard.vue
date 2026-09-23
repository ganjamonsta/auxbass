<template>
  <div 
    v-if="shouldShow" 
    class="discord-party-card"
    :class="{ 'in-party': discordStore.isUserInVoice }"
  >
    <!-- Background Ambient Glow -->
    <div class="party-ambient-glow"></div>

    <!-- Active Party Content -->
    <div v-if="discordStore.hasParty" class="party-content">
      <!-- Top Row: Server Badge + Live Pulse Indicator -->
      <div class="party-top-row">
        <div class="party-badge">
          <div class="live-dot-pulse"></div>
          <span class="badge-text">
            {{ discordStore.guildName || 'Discord Сервер' }} • #{{ discordStore.channelName || 'Голосовой' }}
          </span>
        </div>
        <div v-if="discordStore.isUserInVoice" class="party-user-status in-voice">
          <span class="status-indicator-dot"></span>
          <span>Вы в канале</span>
        </div>
      </div>

      <!-- Main Row: Playing Track + Equalizer -->
      <div class="party-track-info" @click="openModal">
        <div class="party-track-cover">
          <img 
            v-if="trackCoverUrl" 
            :src="trackCoverUrl" 
            alt="Track Cover" 
            class="cover-img"
          />
          <div v-else class="cover-fallback">
            <Disc :size="22" />
          </div>
          <div v-if="discordStore.isPlaying" class="mini-eq-bars">
            <span class="bar bar-1"></span>
            <span class="bar bar-2"></span>
            <span class="bar bar-3"></span>
          </div>
        </div>

        <div class="party-track-meta">
          <div class="party-track-title">
            {{ discordStore.currentTrack?.title || 'Без названия' }}
          </div>
          <div class="party-track-artist">
            {{ discordStore.currentTrack?.artist || 'Воспроизведение в Discord' }}
          </div>
        </div>

        <!-- DJ Crown / Playback Status -->
        <div class="party-dj-pill" v-if="discordStore.hostUser" :title="`DJ: ${discordStore.hostUser.display_name}`">
          <Crown :size="13" class="dj-crown-icon" />
          <span class="dj-name">{{ discordStore.hostUser.display_name }}</span>
        </div>
      </div>

      <!-- Bottom Row: Avatars of Members + Action Button -->
      <div class="party-bottom-row">
        <!-- Members Avatars Stack -->
        <div class="party-members-stack" @click="openModal" title="Участники голосового канала">
          <div 
            v-for="(member, idx) in visibleMembers" 
            :key="member.id"
            class="member-avatar-wrapper"
            :style="{ zIndex: 10 - idx }"
            :title="member.display_name"
          >
            <img 
              v-if="member.avatar_url" 
              :src="member.avatar_url" 
              class="member-avatar-img" 
              alt="Avatar"
            />
            <div v-else class="member-avatar-fallback">
              {{ member.display_name?.charAt(0) || '?' }}
            </div>
          </div>
          <div v-if="extraMembersCount > 0" class="member-extra-badge">
            +{{ extraMembersCount }}
          </div>
          <span class="members-label">
            {{ membersLabel }}
          </span>
        </div>

        <!-- Action Button -->
        <div class="party-actions">
          <button 
            v-if="discordStore.isUserInVoice"
            class="neu-btn-party dj-btn"
            @click="openModal"
          >
            <Sliders :size="15" />
            <span>DJ-пульт</span>
          </button>
          <button 
            v-else
            class="neu-btn-party join-btn"
            @click="openModal"
          >
            <Headphones :size="15" />
            <span>Присоединиться</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Idle / Detected Voice Prompt (If user is in voice but bot is not playing yet) -->
    <div v-else-if="discordStore.detectedUserChannel" class="party-content prompt-content">
      <div class="party-top-row">
        <div class="party-badge idle-badge">
          <Volume2 :size="14" class="idle-icon" />
          <span class="badge-text">
            Обнаружен канал: #{{ discordStore.detectedUserChannel.channel_name }} ({{ discordStore.detectedUserChannel.guild_name }})
          </span>
        </div>
      </div>
      <div class="prompt-body">
        <div class="prompt-text">
          Вы сидите в Discord с друзьями! Хотите запустить музыку прямо в канал?
        </div>
        <button class="neu-btn-party summon-btn" @click="handleSummonBot">
          <Radio :size="15" />
          <span>Запустить музыку</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Disc, Crown, Headphones, Sliders, Volume2, Radio } from 'lucide-vue-next'
import { useDiscordStore } from '@/stores/discord'
import { usePlayerStore } from '@/stores/player'

const discordStore = useDiscordStore()
const playerStore = usePlayerStore()

const shouldShow = computed(() => {
  // Show if there is an active party OR if the user is currently sitting in a voice channel
  return discordStore.hasParty || !!discordStore.detectedUserChannel
})

const trackCoverUrl = computed(() => {
  const track = discordStore.currentTrack
  if (!track || !track.cover_url) return null
  if (track.cover_url.startsWith('http') || track.cover_url.startsWith('/api')) {
    return track.cover_url
  }
  return `/api/images/${track.cover_url}`
})

const visibleMembers = computed(() => {
  return discordStore.activePartyMembers.slice(0, 4)
})

const extraMembersCount = computed(() => {
  return Math.max(0, discordStore.activePartyMembers.length - 4)
})

const membersLabel = computed(() => {
  const count = discordStore.memberCount
  if (count === 1) return '1 друг в канале'
  if (count >= 2 && count <= 4) return `${count} друга в канале`
  return `${count} друзей в канале`
})

function openModal() {
  discordStore.openPartyModal()
}

async function handleSummonBot() {
  const ch = discordStore.detectedUserChannel
  if (!ch) return
  try {
    await discordStore.connectToChannel(ch.channel_id)
    // If player has a current track, stream it
    if (playerStore.currentTrack) {
      await discordStore.play(playerStore.currentTrack, playerStore.queue, playerStore.progress)
    }
    discordStore.openPartyModal()
  } catch (e) {
    console.error('Failed to summon Discord bot:', e)
  }
}
</script>

<style scoped>
.discord-party-card {
  position: relative;
  background: var(--c-bg-2);
  border-radius: var(--r-lg, 16px);
  padding: 14px 16px;
  margin: 12px 0 18px 0;
  box-shadow: 5px 5px 12px var(--sh-dark), -3px -3px 8px var(--sh-light);
  border: 1px solid rgba(88, 101, 242, 0.2);
  overflow: hidden;
  transition: all 0.2s ease;
}

.discord-party-card:hover {
  border-color: rgba(88, 101, 242, 0.4);
}

.discord-party-card.in-party {
  border-color: rgba(29, 185, 84, 0.4);
  box-shadow: 5px 5px 14px var(--sh-dark), -3px -3px 8px var(--sh-light), 0 0 16px rgba(29, 185, 84, 0.15);
}

.party-ambient-glow {
  position: absolute;
  top: -40px;
  right: -40px;
  width: 140px;
  height: 140px;
  background: radial-gradient(circle, rgba(88, 101, 242, 0.18) 0%, transparent 70%);
  pointer-events: none;
  filter: blur(20px);
}

.discord-party-card.in-party .party-ambient-glow {
  background: radial-gradient(circle, rgba(29, 185, 84, 0.22) 0%, transparent 70%);
}

.party-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.party-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: rgba(88, 101, 242, 0.12);
  border: 1px solid rgba(88, 101, 242, 0.25);
  border-radius: 20px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 600;
  color: #7289da;
  letter-spacing: 0.2px;
}

.party-badge.idle-badge {
  background: rgba(0, 188, 212, 0.12);
  border-color: rgba(0, 188, 212, 0.3);
  color: var(--c-secondary, #00bcd4);
}

.live-dot-pulse {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #1db954;
  box-shadow: 0 0 8px #1db954;
  animation: pulse-glow 1.8s infinite;
}

@keyframes pulse-glow {
  0% { transform: scale(0.9); opacity: 0.8; }
  50% { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.8; }
}

.party-user-status.in-voice {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 600;
  color: var(--c-accent, #1db954);
}

.status-indicator-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--c-accent, #1db954);
}

/* Track Info */
.party-track-info {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--c-bg-1);
  border-radius: var(--r-md, 12px);
  padding: 8px 10px;
  margin-bottom: 12px;
  cursor: pointer;
  box-shadow: inset 2px 2px 5px var(--sh-inset-dark), inset -2px -2px 4px var(--sh-inset-light);
  border: 1px solid rgba(255, 255, 255, 0.03);
  transition: background 0.15s ease;
}

.party-track-info:hover {
  background: var(--c-bg-3);
}

.party-track-cover {
  position: relative;
  width: 44px;
  height: 44px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--c-bg-3);
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

.mini-eq-bars {
  position: absolute;
  bottom: 4px;
  right: 4px;
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 12px;
}

.mini-eq-bars .bar {
  width: 2.5px;
  background: var(--c-accent, #1db954);
  border-radius: 1px;
  animation: eq-bounce 0.8s ease-in-out infinite alternate;
}

.bar-1 { height: 40%; animation-delay: 0.1s; }
.bar-2 { height: 90%; animation-delay: 0.3s; }
.bar-3 { height: 60%; animation-delay: 0.2s; }

@keyframes eq-bounce {
  0% { transform: scaleY(0.3); }
  100% { transform: scaleY(1); }
}

.party-track-meta {
  flex: 1;
  min-width: 0;
}

.party-track-title {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.party-track-artist {
  font-size: 11.5px;
  color: var(--c-text-2, #b0b0b0);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.party-dj-pill {
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 215, 0, 0.12);
  border: 1px solid rgba(255, 215, 0, 0.3);
  border-radius: 12px;
  padding: 3px 8px;
  font-size: 11px;
  color: #ffd700;
  font-weight: 600;
  flex-shrink: 0;
}

.dj-crown-icon {
  color: #ffd700;
}

/* Bottom Row */
.party-bottom-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.party-members-stack {
  display: flex;
  align-items: center;
  gap: -6px;
  cursor: pointer;
}

.member-avatar-wrapper {
  margin-right: -8px;
  position: relative;
}

.member-avatar-img,
.member-avatar-fallback {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 2px solid var(--c-bg-2);
  object-fit: cover;
  box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
}

.member-avatar-fallback {
  background: var(--c-bg-4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: bold;
  color: var(--c-text-1);
}

.member-extra-badge {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--c-bg-4);
  border: 2px solid var(--c-bg-2);
  font-size: 10px;
  font-weight: bold;
  color: var(--c-text-2);
  display: flex;
  align-items: center;
  justify-content: center;
}

.members-label {
  font-size: 11.5px;
  color: var(--c-text-2);
  margin-left: 14px;
  font-weight: 500;
}

.neu-btn-party {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: var(--r-md, 12px);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.04);
  transition: all 0.15s ease;
}

.neu-btn-party.dj-btn {
  background: var(--c-bg-3);
  color: var(--c-text-1);
  box-shadow: 3px 3px 7px var(--sh-dark), -2px -2px 5px var(--sh-light);
}

.neu-btn-party.dj-btn:active {
  box-shadow: inset 2px 2px 4px var(--sh-inset-dark), inset -2px -2px 4px var(--sh-inset-light);
  transform: scale(0.97);
}

.neu-btn-party.join-btn,
.neu-btn-party.summon-btn {
  background: linear-gradient(135deg, #5865f2 0%, #4752c4 100%);
  color: #fff;
  border: none;
  box-shadow: 0 4px 12px rgba(88, 101, 242, 0.35);
}

.neu-btn-party.join-btn:active,
.neu-btn-party.summon-btn:active {
  transform: scale(0.97);
  box-shadow: 0 2px 6px rgba(88, 101, 242, 0.5);
}

/* Prompt state */
.prompt-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 4px;
}

.prompt-text {
  font-size: 12px;
  color: var(--c-text-2);
  line-height: 1.4;
}
</style>
