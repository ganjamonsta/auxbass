import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ingestionApi } from '@/api/client'

const SC_ACCOUNT_STORAGE_KEY = 'tg_player_sc_account'
const SP_ACCOUNT_STORAGE_KEY = 'tg_player_sp_account'
const SP_LAST_IMPORT_KEY = 'tg_player_sp_last_import'

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
  const lastSpotifyImport = ref(loadCachedAccount(SP_LAST_IMPORT_KEY))

  const loadingSc = ref(false)
  const loadingSp = ref(false)
  const loadingLastImport = ref(false)

  const isScConnected = computed(() => !!scAccount.value?.connected)
  const isSpConnected = computed(() => !!spAccount.value?.connected)
  const hasLastSpotifyImport = computed(() => !!lastSpotifyImport.value && (lastSpotifyImport.value.found !== false) && !!lastSpotifyImport.value.file_id)

  const recentSpotifyImports = computed(() => {
    if (!lastSpotifyImport.value) return []
    if (Array.isArray(lastSpotifyImport.value.recent_files) && lastSpotifyImport.value.recent_files.length > 0) {
      return lastSpotifyImport.value.recent_files.slice(0, 3)
    }
    if (lastSpotifyImport.value.file_id) {
      return [lastSpotifyImport.value]
    }
    return []
  })

  const hasImportSubitems = computed(() => {
    return isScConnected.value || recentSpotifyImports.value.length > 0
  })

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

  async function fetchLastSpotifyImport(force = false) {
    if (loadingLastImport.value && !force) return lastSpotifyImport.value
    loadingLastImport.value = true
    try {
      const res = await ingestionApi.getLastSpotifyImport()
      if (res.data && res.data.found) {
        lastSpotifyImport.value = res.data
        localStorage.setItem(SP_LAST_IMPORT_KEY, JSON.stringify(res.data))
      } else {
        lastSpotifyImport.value = null
        localStorage.removeItem(SP_LAST_IMPORT_KEY)
      }
    } catch (e) {
      console.error('Failed to fetch last Spotify import:', e)
    } finally {
      loadingLastImport.value = false
    }
    return lastSpotifyImport.value
  }

  function setLastSpotifyImport(data) {
    if (data && data.file_id) {
      lastSpotifyImport.value = { found: true, ...data }
      try {
        localStorage.setItem(SP_LAST_IMPORT_KEY, JSON.stringify(lastSpotifyImport.value))
      } catch (_) {}
    } else {
      lastSpotifyImport.value = null
      try {
        localStorage.removeItem(SP_LAST_IMPORT_KEY)
      } catch (_) {}
    }
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
    lastSpotifyImport.value = null
    try {
      localStorage.removeItem(SC_ACCOUNT_STORAGE_KEY)
      localStorage.removeItem(SP_ACCOUNT_STORAGE_KEY)
      localStorage.removeItem(SP_LAST_IMPORT_KEY)
    } catch (_) {}
  }

  return {
    scAccount,
    spAccount,
    lastSpotifyImport,
    loadingSc,
    loadingSp,
    loadingLastImport,
    isScConnected,
    isSpConnected,
    hasLastSpotifyImport,
    recentSpotifyImports,
    hasImportSubitems,
    fetchSoundCloud,
    connectSoundCloud,
    disconnectSoundCloud,
    fetchSpotify,
    connectSpotify,
    disconnectSpotify,
    fetchLastSpotifyImport,
    setLastSpotifyImport,
    setSoundCloudAccount,
    setSpotifyAccount,
    reset,
  }
})

