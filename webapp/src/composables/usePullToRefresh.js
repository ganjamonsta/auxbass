/**
 * Pull-to-refresh composable
 * Handles touch gestures for refreshing content.
 *
 * Usage:
 *   const { pullDistance, isPulling, isRefreshing, scrollRef, cleanup } =
 *     usePullToRefresh(onRefresh, { telegram })
 *
 * Bind `scrollRef` to the scrollable container via `ref="scrollRef"`.
 * Call `cleanup()` in `onUnmounted`.
 */
import { ref, watch, onUnmounted } from 'vue'

const PULL_THRESHOLD = 60   // px needed to trigger refresh
const MAX_PULL = 120        // visual cap
const RESISTANCE = 0.45     // dampen finger distance

export function usePullToRefresh(onRefresh, { telegram = null } = {}) {
  // --- reactive state ---
  const scrollRef = ref(null)       // template ref for the scroll container
  const pullDistance = ref(0)        // current visual pull distance (px)
  const isPulling = ref(false)       // true when distance >= threshold
  const isRefreshing = ref(false)    // true while refresh() runs

  // --- internal (non-reactive, no need for Vue overhead) ---
  let startY = null                  // touchstart clientY (null = not tracking)
  let tracking = false               // actively tracking a pull gesture
  let attached = false               // listeners are bound
  let el = null                      // cached DOM element

  // ---- handlers ----

  function onTouchStart(e) {
    if (isRefreshing.value) return
    // Only start when scrolled to very top
    if (el && el.scrollTop > 0) return
    startY = e.touches[0].clientY
    tracking = true
  }

  function onTouchMove(e) {
    if (!tracking || startY === null) return
    if (isRefreshing.value) return

    const currentY = e.touches[0].clientY
    const rawDiff = currentY - startY

    // Only care about downward pull while at scroll-top
    if (rawDiff <= 0 || (el && el.scrollTop > 0)) {
      // User scrolled up or container is no longer at top — cancel
      resetPull()
      return
    }

    // Prevent native scroll / native pull-to-refresh
    e.preventDefault()

    const distance = Math.min(rawDiff * RESISTANCE, MAX_PULL)
    pullDistance.value = distance
    isPulling.value = distance >= PULL_THRESHOLD
  }

  async function onTouchEnd() {
    if (!tracking) return

    if (isPulling.value && pullDistance.value >= PULL_THRESHOLD) {
      // Trigger refresh
      isRefreshing.value = true
      telegram?.HapticFeedback?.impactOccurred?.('medium')

      try {
        await onRefresh()
      } catch (err) {
        console.error('[PullToRefresh] refresh failed:', err)
      } finally {
        isRefreshing.value = false
      }
    }

    resetPull()
  }

  function resetPull() {
    startY = null
    tracking = false
    pullDistance.value = 0
    isPulling.value = false
  }

  // ---- listener management ----

  function attachListeners(element) {
    if (attached) detachListeners()
    el = element
    if (!el) return

    // Prevent native overscroll (Chrome / Android)
    el.style.overscrollBehaviorY = 'contain'

    // touchstart & touchend can stay passive (we don't call preventDefault)
    el.addEventListener('touchstart', onTouchStart, { passive: true })
    // touchmove must be non-passive so we can preventDefault to block native refresh
    el.addEventListener('touchmove', onTouchMove, { passive: false })
    el.addEventListener('touchend', onTouchEnd, { passive: true })
    el.addEventListener('touchcancel', onTouchEnd, { passive: true })
    attached = true
  }

  function detachListeners() {
    if (!el) return
    el.style.overscrollBehaviorY = ''
    el.removeEventListener('touchstart', onTouchStart)
    el.removeEventListener('touchmove', onTouchMove)
    el.removeEventListener('touchend', onTouchEnd)
    el.removeEventListener('touchcancel', onTouchEnd)
    attached = false
    el = null
  }

  // Auto-attach when scrollRef changes (template ref resolution)
  watch(scrollRef, (newEl) => {
    if (newEl?.$el) {
      // In case a Vue component is bound instead of a raw element
      attachListeners(newEl.$el)
    } else if (newEl instanceof HTMLElement) {
      attachListeners(newEl)
    } else {
      detachListeners()
    }
  })

  // Cleanup on unmount
  onUnmounted(detachListeners)

  function cleanup() {
    detachListeners()
  }

  return {
    scrollRef,
    pullDistance,
    isPulling,
    isRefreshing,
    cleanup,
  }
}
