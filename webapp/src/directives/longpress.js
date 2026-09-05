/**
 * Universal Long-Press Directive for Vue 3
 * 
 * Provides consistent touch-and-hold (long-press) behavior on mobile / touch screens
 * with:
 * - 400ms hold delay
 * - 10px scroll tolerance (cancels if user is scrolling)
 * - Click suppression after long-press (prevents accidental track play on release)
 * - Haptic feedback integration (Telegram WebApp & Navigator)
 * - Clean cleanup on unmount
 * 
 * Usage:
 *   v-longpress="handleLongPress"
 *   v-longpress="{ handler: handleLongPress, delay: 450 }"
 */

function triggerHaptic() {
  try {
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.impactOccurred('medium')
    } else if (navigator?.vibrate) {
      navigator.vibrate(35)
    }
  } catch (_) {}
}

export const longpress = {
  mounted(el, binding) {
    if (!binding.value) return

    const handler = typeof binding.value === 'function' 
      ? binding.value 
      : binding.value?.handler

    if (typeof handler !== 'function') return

    const delay = binding.value?.delay || 400

    const state = {
      timer: null,
      startX: 0,
      startY: 0,
      moved: false,
      triggered: false,
      lastTouch: null
    }

    const start = (e) => {
      if (e.touches && e.touches.length > 1) return
      
      state.moved = false
      state.triggered = false
      
      const touch = e.touches ? e.touches[0] : e
      state.startX = touch.clientX
      state.startY = touch.clientY
      state.lastTouch = touch

      state.timer = setTimeout(() => {
        if (!state.moved) {
          state.triggered = true
          triggerHaptic()
          handler(e)
        }
      }, delay)
    }

    const move = (e) => {
      if (!state.timer) return
      const touch = e.touches ? e.touches[0] : e
      const dx = Math.abs(touch.clientX - state.startX)
      const dy = Math.abs(touch.clientY - state.startY)
      
      if (dx > 10 || dy > 10) {
        state.moved = true
        clearTimeout(state.timer)
        state.timer = null
      }
    }

    const cancel = () => {
      if (state.timer) {
        clearTimeout(state.timer)
        state.timer = null
      }
    }

    const clickCapture = (e) => {
      if (state.triggered) {
        e.preventDefault()
        e.stopPropagation()
        e.stopImmediatePropagation?.()
        state.triggered = false
      }
    }

    el._longpress = { start, move, cancel, clickCapture }

    el.addEventListener('touchstart', start, { passive: true })
    el.addEventListener('touchmove', move, { passive: true })
    el.addEventListener('touchend', cancel, { passive: true })
    el.addEventListener('touchcancel', cancel, { passive: true })
    // Capture click to suppress click immediately following a long-press
    el.addEventListener('click', clickCapture, true)
    
    // Prevent iOS callout
    el.style.webkitTouchCallout = 'none'
  },

  unmounted(el) {
    if (!el._longpress) return
    const { start, move, cancel, clickCapture } = el._longpress

    el.removeEventListener('touchstart', start)
    el.removeEventListener('touchmove', move)
    el.removeEventListener('touchend', cancel)
    el.removeEventListener('touchcancel', cancel)
    el.removeEventListener('click', clickCapture, true)

    delete el._longpress
  }
}

export default longpress
