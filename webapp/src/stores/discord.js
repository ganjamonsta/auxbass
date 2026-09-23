import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { discordApi } from '@/api'

const LISTEN_ALONG_KEY = 'tg_player_discord_listen_along'

export const useDiscordStore = defineStore('discord', () => {
  // ===================== STATE =====================
  const configured = ref(false)
  const botReady = ref(false)
  const hasParty = ref(false)
  const guildId = ref(null)
  const guildName = ref(null)
  const guildIcon = ref(null)
  const channelId = ref(null)
  const channelName = ref(null)
  
  const members = ref([])
  const memberCount = ref(0)
  
  const isPlaying = ref(false)
  const isPaused = ref(false)
  const currentTrack = ref(null)
  const position = ref(0)
  const duration = ref(0)
  const volume = ref(100)
  
  const queue = ref([])
  const queueIndex = ref(-1)
  
  const hostUser = ref(null)
  const djLock = ref(false)
  const isHost = ref(false)
  const canControl = ref(true)
  const isUserInVoice = ref(false)
  
  const isLinked = ref(false)
  const linkedDiscordId = ref('')
  const linkedDiscordUsername = ref('')
  const linkedDiscordDisplayName = ref('')
  const linkedDiscordAvatar = ref('')
  const detectedUserChannel = ref(null)
  const availableChannels = ref([])
  const inviteUrl = ref('')
  
  const showPartyModal = ref(false)
  const listenAlong = ref(localStorage.getItem(LISTEN_ALONG_KEY) === 'true')
  
  // WebSocket connection
  let ws = null
  let reconnectTimer = null
  let pingInterval = null
  let positionTicker = null

  // ===================== COMPUTED =====================
  const activePartyMembers = computed(() => {
    return members.value.filter(m => !m.is_bot)
  })

  const isDiscordActive = computed(() => {
    return hasParty.value && (isPlaying.value || isPaused.value)
  })

  // ===================== METHODS =====================
  function applyPartyState(state) {
    if (!state) return
    configured.value = !!state.configured
    botReady.value = !!state.bot_ready
    hasParty.value = !!state.has_party
    guildId.value = state.guild_id || null
    guildName.value = state.guild_name || null
    guildIcon.value = state.guild_icon || null
    channelId.value = state.channel_id || null
    channelName.value = state.channel_name || null
    
    members.value = Array.isArray(state.members) ? state.members : []
    memberCount.value = state.member_count ?? members.value.length
    
    isPlaying.value = !!state.is_playing
    isPaused.value = !!state.is_paused
    currentTrack.value = state.current_track || null
    position.value = state.position || 0
    duration.value = state.duration || 0
    volume.value = state.volume ?? 100
    
    queue.value = Array.isArray(state.queue) ? state.queue : []
    queueIndex.value = state.queue_index ?? -1
    
    hostUser.value = state.host_user || null
    djLock.value = !!state.dj_lock
    isHost.value = !!state.is_host
    canControl.value = state.can_control !== false
    isUserInVoice.value = !!state.is_user_in_voice

    _syncPositionTicker()
  }

  function _syncPositionTicker() {
    if (positionTicker) {
      clearInterval(positionTicker)
      positionTicker = null
    }
    if (isPlaying.value && duration.value > 0) {
      positionTicker = setInterval(() => {
        if (position.value < duration.value) {
          position.value += 1
        }
      }, 1000)
    }
  }

  async function fetchParty() {
    try {
      const res = await discordApi.getParty()
      applyPartyState(res.data)
      return res.data
    } catch (e) {
      console.error('Failed to fetch Discord party state:', e)
    }
  }

  async function fetchUserState() {
    try {
      const res = await discordApi.getUserState()
      const data = res.data
      isLinked.value = !!data.is_linked
      linkedDiscordId.value = data.discord_id || ''
      linkedDiscordUsername.value = data.discord_username || ''
      linkedDiscordDisplayName.value = data.discord_display_name || ''
      linkedDiscordAvatar.value = data.discord_avatar_url || ''
      detectedUserChannel.value = data.channel || null
      return data
    } catch (e) {
      console.error('Failed to fetch user Discord state:', e)
    }
  }

  async function fetchAccount() {
    try {
      const res = await discordApi.getAccount()
      const data = res.data
      if (data && data.linked) {
        isLinked.value = true
        linkedDiscordId.value = data.discord_id || ''
        linkedDiscordUsername.value = data.username || ''
        linkedDiscordDisplayName.value = data.display_name || ''
        linkedDiscordAvatar.value = data.avatar_url || ''
      }
      return data
    } catch (e) {
      console.error('Failed to fetch Discord account:', e)
    }
  }

  async function fetchAvailableChannels() {
    try {
      const res = await discordApi.getChannels()
      availableChannels.value = res.data || []
      return availableChannels.value
    } catch (e) {
      console.error('Failed to fetch available channels:', e)
    }
  }

  async function fetchInvite() {
    try {
      const res = await discordApi.getInvite()
      inviteUrl.value = res.data.invite_url || ''
      return inviteUrl.value
    } catch (e) {
      console.error('Failed to fetch bot invite:', e)
    }
  }

  async function connectToChannel(chId) {
    const res = await discordApi.connect(chId)
    applyPartyState(res.data)
    await fetchUserState()
    return res.data
  }

  async function disconnect() {
    await discordApi.disconnect()
    hasParty.value = false
    isPlaying.value = false
    isPaused.value = false
    currentTrack.value = null
    queue.value = []
    _syncPositionTicker()
  }

  async function play(track, newQueue = null, pos = 0) {
    const res = await discordApi.play(track, newQueue, pos)
    applyPartyState(res.data)
  }

  async function pause() {
    await discordApi.pause()
    isPlaying.value = false
    isPaused.value = true
    _syncPositionTicker()
  }

  async function resume() {
    await discordApi.resume()
    isPlaying.value = true
    isPaused.value = false
    _syncPositionTicker()
  }

  async function stop() {
    await discordApi.stop()
    isPlaying.value = false
    isPaused.value = false
    _syncPositionTicker()
  }

  async function skip() {
    await discordApi.skip()
  }

  async function seek(pos) {
    position.value = pos
    await discordApi.seek(pos)
  }

  async function setVolume(vol) {
    volume.value = vol
    await discordApi.setVolume(vol)
  }

  async function addToQueue(track) {
    const res = await discordApi.addToQueue(track)
    return res.data
  }

  async function removeFromQueue(index) {
    await discordApi.removeFromQueue(index)
  }

  async function setDjLock(locked) {
    const res = await discordApi.setDjLock(locked)
    djLock.value = res.data.dj_lock
  }

  async function transferDj(targetUserId) {
    await discordApi.transferDj(targetUserId)
  }

  async function linkAccount(discordId, username = '', displayName = '') {
    const res = await discordApi.linkAccount(discordId, username, displayName)
    isLinked.value = true
    linkedDiscordId.value = res.data.discord_id || discordId
    linkedDiscordUsername.value = res.data.username || ''
    linkedDiscordDisplayName.value = res.data.display_name || ''
    linkedDiscordAvatar.value = res.data.avatar_url || ''
    await fetchUserState()
    return res.data
  }

  async function unlinkAccount() {
    await discordApi.unlinkAccount()
    isLinked.value = false
    linkedDiscordId.value = ''
    linkedDiscordUsername.value = ''
    linkedDiscordDisplayName.value = ''
    linkedDiscordAvatar.value = ''
    detectedUserChannel.value = null
  }

  async function startOAuth() {
    const res = await discordApi.getOAuthUrl()
    if (!res.data || !res.data.configured || !res.data.url) {
      throw new Error(res.data?.message || 'Discord OAuth2 не настроен на сервере')
    }

    const authUrl = res.data.url
    const width = 500
    const height = 750
    const left = Math.max(0, Math.round(window.screenX + (window.outerWidth - width) / 2))
    const top = Math.max(0, Math.round(window.screenY + (window.outerHeight - height) / 2))

    const popup = window.open(
      authUrl,
      'discord_oauth_popup',
      `width=${width},height=${height},left=${left},top=${top},status=0,menubar=0,toolbar=0`
    )

    if (!popup || popup.closed || typeof popup.closed === 'undefined') {
      // Fallback for browsers / webviews blocking popups
      window.location.href = authUrl
      return
    }

    return new Promise((resolve, reject) => {
      let cleanup = null
      let pollCount = 0
      let resolved = false
      let broadcastChannel = null

      const handleSuccess = async (data = null) => {
        if (resolved) return
        resolved = true
        if (cleanup) cleanup()

        if (data) {
          isLinked.value = true
          if (data.discord_id) linkedDiscordId.value = data.discord_id
          if (data.username) linkedDiscordUsername.value = data.username
          if (data.display_name) linkedDiscordDisplayName.value = data.display_name
          if (data.avatar_url) linkedDiscordAvatar.value = data.avatar_url
        }

        try {
          await Promise.allSettled([
            fetchAccount(),
            fetchUserState(),
            fetchAvailableChannels(),
          ])
        } catch (_) {}

        try {
          if (popup && !popup.closed) popup.close()
        } catch (_) {}

        resolve(data)
      }

      const messageHandler = (event) => {
        if (event.data?.type === 'discord_oauth_success') {
          handleSuccess(event.data)
        } else if (event.data?.type === 'discord_oauth_error') {
          if (resolved) return
          resolved = true
          if (cleanup) cleanup()
          try { if (popup && !popup.closed) popup.close() } catch (_) {}
          reject(new Error(event.data.error || 'Ошибка авторизации Discord'))
        }
      }

      // 1. Window postMessage listener
      window.addEventListener('message', messageHandler)

      // 2. BroadcastChannel listener (if supported)
      try {
        if (typeof BroadcastChannel !== 'undefined') {
          broadcastChannel = new BroadcastChannel('auxbass_discord_auth')
          broadcastChannel.onmessage = (event) => {
            if (event.data?.type === 'discord_oauth_success') {
              handleSuccess(event.data)
            }
          }
        }
      } catch (_) {}

      // 3. Active Polling fallback: checks backend DB every 1.2s
      // Guaranteed to detect success even across different origins or with COOP restrictions
      const pollTimer = setInterval(async () => {
        pollCount++
        try {
          const acc = await fetchAccount()
          if (acc && acc.linked) {
            handleSuccess(acc)
            return
          }
        } catch (_) {}

        if (popup.closed || pollCount >= 100) {
          if (resolved) return
          resolved = true
          if (cleanup) cleanup()
          const finalAcc = await fetchAccount()
          await fetchUserState()
          resolve(finalAcc)
        }
      }, 1200)

      cleanup = () => {
        window.removeEventListener('message', messageHandler)
        if (broadcastChannel) {
          try { broadcastChannel.close() } catch (_) {}
        }
        clearInterval(pollTimer)
      }
    })
  }

  function toggleListenAlong() {
    listenAlong.value = !listenAlong.value
    localStorage.setItem(LISTEN_ALONG_KEY, listenAlong.value.toString())
  }

  function openPartyModal() {
    showPartyModal.value = true
  }

  function closePartyModal() {
    showPartyModal.value = false
  }

  // ===================== WEBSOCKET =====================
  function setupWebSocket() {
    if (ws) {
      try { ws.close() } catch (_) {}
      ws = null
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/discord/ws`

    try {
      ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        if (pingInterval) clearInterval(pingInterval)
        pingInterval = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send('ping')
          }
        }, 25000)
      }

      ws.onmessage = (event) => {
        if (event.data === 'pong') return
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'party_update' && msg.data) {
            applyPartyState(msg.data)
          }
        } catch (e) {
          console.debug('Failed to parse Discord WS message:', e)
        }
      }

      ws.onclose = () => {
        if (pingInterval) clearInterval(pingInterval)
        if (reconnectTimer) clearTimeout(reconnectTimer)
        reconnectTimer = setTimeout(() => {
          setupWebSocket()
        }, 5000)
      }

      ws.onerror = () => {
        try { ws.close() } catch (_) {}
      }
    } catch (e) {
      console.debug('Failed to initialize Discord WebSocket:', e)
    }
  }

  async function init() {
    await Promise.allSettled([
      fetchParty(),
      fetchUserState(),
      fetchInvite(),
    ])
    setupWebSocket()
  }

  return {
    configured,
    botReady,
    hasParty,
    guildId,
    guildName,
    guildIcon,
    channelId,
    channelName,
    members,
    memberCount,
    activePartyMembers,
    isPlaying,
    isPaused,
    isDiscordActive,
    currentTrack,
    position,
    duration,
    volume,
    queue,
    queueIndex,
    hostUser,
    djLock,
    isHost,
    canControl,
    isUserInVoice,
    isLinked,
    linkedDiscordId,
    linkedDiscordUsername,
    linkedDiscordDisplayName,
    linkedDiscordAvatar,
    detectedUserChannel,
    availableChannels,
    inviteUrl,
    showPartyModal,
    listenAlong,
    
    // Actions
    init,
    fetchParty,
    fetchUserState,
    fetchAccount,
    fetchAvailableChannels,
    fetchInvite,
    connectToChannel,
    disconnect,
    play,
    pause,
    resume,
    stop,
    skip,
    seek,
    setVolume,
    addToQueue,
    removeFromQueue,
    setDjLock,
    transferDj,
    linkAccount,
    unlinkAccount,
    startOAuth,
    toggleListenAlong,
    openPartyModal,
    closePartyModal,
  }
})
