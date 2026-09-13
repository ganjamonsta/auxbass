import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ingestionApi } from '@/api/client'

const SC_ACCOUNT_STORAGE_KEY = 'tg_player_sc_account'
const SP_ACCOUNT_STORAGE_KEY = 'tg_player_sp_account'

const loadCachedAccount = (key) => {
  try {
    const raw = localStorage.getItem(key)
    if (raw) return JSON.parse(raw)
  } catch (_) {}
  return null
}

export const useExternalAccountsStore = defineStore('externalAccounts', () => {
  const scAccount = ref(loadCachedAccount(SC_ACCOUNT_STORAGE_KEY))
  const spAccount = ref(loadCachedAccount(SP_ACCOUNT_STORAGE_KEY))

  const loadingSc = ref(false)
  const loadingSp = ref(false)

  const isScConnected = computed(() => !!scAccount.value?.connected)
  const isSpConnected = computed(() => !!spAccount.value?.connected)

  async function fetchSoundCloud(force = false) {
    if (loadingSc.value && !force) return scAccount.value
    loadingSc.value = true
    try {
      const res = await ingestionApi.getSoundCloudAccount()
      scAccount.value = res.data
      if (res.data) {
        localStorage.setItem(SC_ACCOUNT_STORAGE_KEY, JSON.stringify(res.data))
      }
    } catch (e) {
      console.error('Failed to fetch SoundCloud account:', e)
    } finally {
      loadingSc.value = false
    }
    return scAccount.value
  }

  async function connectSoundCloud(params) {
    const res = await ingestionApi.connectSoundCloudAccount(params)
    scAccount.value = res.data
    if (res.data) {
      localStorage.setItem(SC_ACCOUNT_STORAGE_KEY, JSON.stringify(res.data))
    }
    return res.data
  }

  async function disconnectSoundCloud() {
    await ingestionApi.disconnectSoundCloudAccount()
    scAccount.value = { connected: false }
    try {
      localStorage.removeItem(SC_ACCOUNT_STORAGE_KEY)
    } catch (_) {}
  }

  async function fetchSpotify(force = false) {
    if (loadingSp.value && !force) return spAccount.value
    loadingSp.value = true
    try {
      const res = await ingestionApi.getSpotifyAccount()
      spAccount.value = res.data
      if (res.data) {
        localStorage.setItem(SP_ACCOUNT_STORAGE_KEY, JSON.stringify(res.data))
      }
    } catch (e) {
      console.error('Failed to fetch Spotify account:', e)
    } finally {
      loadingSp.value = false
    }
    return spAccount.value
  }

  async function connectSpotify(params) {
    const res = await ingestionApi.connectSpotifyAccount(params)
    spAccount.value = res.data
    if (res.data) {
      localStorage.setItem(SP_ACCOUNT_STORAGE_KEY, JSON.stringify(res.data))
    }
    return res.data
  }

  async function disconnectSpotify() {
    await ingestionApi.disconnectSpotifyAccount()
    spAccount.value = { connected: false }
    try {
      localStorage.removeItem(SP_ACCOUNT_STORAGE_KEY)
    } catch (_) {}
  }

  function setSoundCloudAccount(account) {
    if (account) {
      scAccount.value = account
      try {
        localStorage.setItem(SC_ACCOUNT_STORAGE_KEY, JSON.stringify(account))
      } catch (_) {}
    }
  }

  function setSpotifyAccount(account) {
    if (account) {
      spAccount.value = account
      try {
        localStorage.setItem(SP_ACCOUNT_STORAGE_KEY, JSON.stringify(account))
      } catch (_) {}
    }
  }

  function reset() {
    scAccount.value = null
    spAccount.value = null
    try {
      localStorage.removeItem(SC_ACCOUNT_STORAGE_KEY)
      localStorage.removeItem(SP_ACCOUNT_STORAGE_KEY)
    } catch (_) {}
  }

  return {
    scAccount,
    spAccount,
    loadingSc,
    loadingSp,
    isScConnected,
    isSpConnected,
    fetchSoundCloud,
    connectSoundCloud,
    disconnectSoundCloud,
    fetchSpotify,
    connectSpotify,
    disconnectSpotify,
    setSoundCloudAccount,
    setSpotifyAccount,
    reset,
  }
})
