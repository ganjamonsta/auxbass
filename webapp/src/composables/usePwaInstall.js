import { ref, computed } from 'vue'

const DISMISS_STORAGE_KEY = 'auxbass_pwa_dismissed_at'
const DISMISS_DURATION_MS = 7 * 24 * 60 * 60 * 1000 // 7 days

// Shared singleton reactive state
const deferredPrompt = ref(null)
const isInstalled = ref(false)
const showBanner = ref(false)
const showModal = ref(false)
const isInitialized = ref(false)

// Platform detection
const isStandalone = () => {
  if (typeof window === 'undefined') return false
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator?.standalone === true ||
    document.referrer.includes('android-app://')
  )
}

const checkIsIOS = () => {
  if (typeof navigator === 'undefined') return false
  return (
    /iPad|iPhone|iPod/.test(navigator.userAgent) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
  )
}

const checkIsSafari = () => {
  if (typeof navigator === 'undefined') return false
  const ua = navigator.userAgent
  return /Safari/i.test(ua) && !/Chrome|CriOS|FxiOS|OPiOS|EdgiOS|Android/i.test(ua)
}

const checkIsAndroid = () => {
  if (typeof navigator === 'undefined') return false
  return /Android/i.test(navigator.userAgent)
}

const checkIsTelegram = () => {
  if (typeof window === 'undefined') return false
  const tg = window.Telegram?.WebApp
  if (!tg) return false
  
  // Must have real initData with actual user/query parameters, or webview proxy
  const hasRealInitData = typeof tg.initData === 'string' && tg.initData.trim().length > 0
  const hasProxy = Boolean(window.TelegramWebviewProxy)
  const isKnownTgPlatform = tg.platform && tg.platform !== 'unknown' && tg.platform !== ''

  return Boolean(hasRealInitData || (isKnownTgPlatform && hasProxy))
}

// Global initialization
if (typeof window !== 'undefined') {
  // Pick up early prompt if already captured in index.html
  if (window.__pwaDeferredPrompt) {
    deferredPrompt.value = window.__pwaDeferredPrompt
  }

  // Check initial standalone mode
  if (isStandalone()) {
    isInstalled.value = true
  }

  // Listen for beforeinstallprompt
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()
    window.__pwaDeferredPrompt = e
    deferredPrompt.value = e
    if (!isInstalled.value) {
      checkAndScheduleBanner()
    }
  })

  // Listen for custom event from index.html
  window.addEventListener('pwa-prompt-captured', () => {
    if (window.__pwaDeferredPrompt) {
      deferredPrompt.value = window.__pwaDeferredPrompt
      if (!isInstalled.value) {
        checkAndScheduleBanner()
      }
    }
  })

  // Listen for appinstalled
  window.addEventListener('appinstalled', () => {
    isInstalled.value = true
    deferredPrompt.value = null
    window.__pwaDeferredPrompt = null
    showBanner.value = false
    showModal.value = false
    try {
      localStorage.removeItem(DISMISS_STORAGE_KEY)
    } catch {
      // ignore
    }
  })

  // Listen for display-mode change
  window.matchMedia('(display-mode: standalone)').addEventListener('change', (e) => {
    if (e.matches) {
      isInstalled.value = true
      showBanner.value = false
      showModal.value = false
    }
  })
}

function isDismissedRecently() {
  try {
    const saved = localStorage.getItem(DISMISS_STORAGE_KEY)
    if (!saved) return false
    const time = parseInt(saved, 10)
    if (isNaN(time)) return false
    return Date.now() - time < DISMISS_DURATION_MS
  } catch {
    return false
  }
}

function checkAndScheduleBanner() {
  if (isStandalone() || isInstalled.value) return
  if (isDismissedRecently()) return

  // Show banner with a small delay for smooth entry
  setTimeout(() => {
    if (!isStandalone() && !isInstalled.value && !isDismissedRecently()) {
      showBanner.value = true
    }
  }, 2500)
}

export function usePwaInstall() {
  const isIOS = ref(checkIsIOS())
  const isSafari = ref(checkIsSafari())
  const isAndroid = ref(checkIsAndroid())
  const isTelegram = ref(checkIsTelegram())

  const canPromptDirectly = computed(() => {
    if (deferredPrompt.value) return true
    if (isTelegram.value && typeof window.Telegram?.WebApp?.addToHomeScreen === 'function') return true
    return false
  })

  const isInstallable = computed(() => {
    if (isInstalled.value || isStandalone()) return false
    return true
  })

  const platform = computed(() => {
    if (isTelegram.value) return 'telegram'
    if (isIOS.value) return 'ios'
    if (isAndroid.value) return 'android'
    return 'desktop'
  })

  const init = () => {
    if (isInitialized.value) return
    isInitialized.value = true

    if (isStandalone()) {
      isInstalled.value = true
      return
    }

    // Pick up global prompt if available
    if (typeof window !== 'undefined' && window.__pwaDeferredPrompt) {
      deferredPrompt.value = window.__pwaDeferredPrompt
    }

    // Check Telegram addToHomeScreen support
    if (isTelegram.value && window.Telegram?.WebApp?.checkHomeScreenStatus) {
      try {
        window.Telegram.WebApp.checkHomeScreenStatus((status) => {
          if (status === 'added') {
            isInstalled.value = true
          } else if (status === 'missed' || status === 'unknown') {
            checkAndScheduleBanner()
          }
        })
      } catch {
        checkAndScheduleBanner()
      }
    } else {
      checkAndScheduleBanner()
    }
  }

  const promptInstall = async () => {
    // 1. Direct browser prompt if available
    if (deferredPrompt.value) {
      try {
        deferredPrompt.value.prompt()
        const choice = await deferredPrompt.value.userChoice
        if (choice?.outcome === 'accepted') {
          isInstalled.value = true
          showBanner.value = false
          showModal.value = false
        }
        deferredPrompt.value = null
        window.__pwaDeferredPrompt = null
        return
      } catch (err) {
        console.warn('[PWA] Direct prompt error:', err)
      }
    }

    // 2. Telegram WebApp addToHomeScreen
    if (isTelegram.value && typeof window.Telegram?.WebApp?.addToHomeScreen === 'function') {
      try {
        window.Telegram.WebApp.addToHomeScreen()
        showBanner.value = false
        return
      } catch (err) {
        console.warn('[PWA] Telegram addToHomeScreen error:', err)
      }
    }

    // 3. Fallback to platform-specific instruction modal
    showModal.value = true
  }

  const dismissBanner = () => {
    showBanner.value = false
    try {
      localStorage.setItem(DISMISS_STORAGE_KEY, Date.now().toString())
    } catch {
      // ignore
    }
  }

  const openGuide = () => {
    showModal.value = true
  }

  const closeGuide = () => {
    showModal.value = false
  }

  return {
    deferredPrompt,
    isInstalled,
    isInstallable,
    canPromptDirectly,
    isIOS,
    isSafari,
    isAndroid,
    isTelegram,
    platform,
    showBanner,
    showModal,
    init,
    promptInstall,
    dismissBanner,
    openGuide,
    closeGuide
  }
}
