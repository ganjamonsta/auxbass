/**
 * Universal Touch & Gesture Utilities
 * Helps resolve common mobile browser quirks like:
 * - Synthetic click emitted on finger release after a long-press
 * - Browser native contextmenu emitted at ~500ms during touch hold
 * - Telegram WebApp / Navigator haptic feedback
 */

export function triggerHaptic(type = 'medium') {
  try {
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.impactOccurred(type)
    } else if (navigator?.vibrate) {
      navigator.vibrate(type === 'heavy' ? 45 : 30)
    }
  } catch (_) {}
}

let clickSuppressorTimer = null
let clickSuppressorHandler = null

/**
 * Suppress the synthetic 'click' event dispatched by mobile browsers
 * on the touchup/touchend location after a long-press.
 */
export function suppressNextClick(duration = 800) {
  if (clickSuppressorHandler) {
    window.removeEventListener('click', clickSuppressorHandler, true)
    if (clickSuppressorTimer) {
      clearTimeout(clickSuppressorTimer)
      clickSuppressorTimer = null
    }
  }

  clickSuppressorHandler = (e) => {
    e.preventDefault()
    e.stopPropagation()
    e.stopImmediatePropagation?.()
    window.removeEventListener('click', clickSuppressorHandler, true)
    clickSuppressorHandler = null
    if (clickSuppressorTimer) {
      clearTimeout(clickSuppressorTimer)
      clickSuppressorTimer = null
    }
  }

  window.addEventListener('click', clickSuppressorHandler, true)
  clickSuppressorTimer = setTimeout(() => {
    if (clickSuppressorHandler) {
      window.removeEventListener('click', clickSuppressorHandler, true)
      clickSuppressorHandler = null
      clickSuppressorTimer = null
    }
  }, duration)
}

let contextMenuSuppressorTimer = null
let contextMenuSuppressorHandler = null

/**
 * Suppress the native 'contextmenu' event dispatched by mobile browsers
 * at ~500ms during a long-press touch gesture.
 */
export function suppressNextContextMenu(duration = 800) {
  if (contextMenuSuppressorHandler) {
    window.removeEventListener('contextmenu', contextMenuSuppressorHandler, true)
    if (contextMenuSuppressorTimer) {
      clearTimeout(contextMenuSuppressorTimer)
      contextMenuSuppressorTimer = null
    }
  }

  contextMenuSuppressorHandler = (e) => {
    e.preventDefault()
    e.stopPropagation()
    e.stopImmediatePropagation?.()
    window.removeEventListener('contextmenu', contextMenuSuppressorHandler, true)
    contextMenuSuppressorHandler = null
    if (contextMenuSuppressorTimer) {
      clearTimeout(contextMenuSuppressorTimer)
      contextMenuSuppressorTimer = null
    }
  }

  window.addEventListener('contextmenu', contextMenuSuppressorHandler, true)
  contextMenuSuppressorTimer = setTimeout(() => {
    if (contextMenuSuppressorHandler) {
      window.removeEventListener('contextmenu', contextMenuSuppressorHandler, true)
      contextMenuSuppressorHandler = null
      contextMenuSuppressorTimer = null
    }
  }, duration)
}
