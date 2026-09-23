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
  const linkedDiscordUsername = ref('')
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
      linkedDiscordUsername.value = data.discord_username || ''
      detectedUserChannel.value = data.channel || null
      return data
    } catch (e) {
      console.error('Failed to fetch user Discord state:', e)
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
    linkedDiscordUsername.value = res.data.username
    await fetchUserState()
    return res.data
  }

  async function unlinkAccount() {
    await discordApi.unlinkAccount()
    isLinked.value = false
    linkedDiscordUsername.value = ''
    detectedUserChannel.value = null
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
    linkedDiscordUsername,
    detectedUserChannel,
    availableChannels,
    inviteUrl,
    showPartyModal,
    listenAlong,
    
    // Actions
    init,
    fetchParty,
    fetchUserState,
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
    toggleListenAlong,
    openPartyModal,
    closePartyModal,
  }
})
