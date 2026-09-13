import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'

/**
 * Composable for horizontal scroll carousels.
 * Provides:
 * - Reactive canScrollLeft / canScrollRight state for arrow buttons
 * - Smooth scrollLeft / scrollRight actions
 * - Mouse wheel vertical-to-horizontal conversion with boundary pass-through
 * - Auto-updates on resize, scroll, and content changes
 */
export function useHorizontalScroll() {
  const containerRef = ref(null)
  const canScrollLeft = ref(false)
  const canScrollRight = ref(false)

  let resizeObserver = null

  const updateScrollState = () => {
    const el = containerRef.value
    if (!el) {
      canScrollLeft.value = false
      canScrollRight.value = false
      return
    }

    const scrollLeft = el.scrollLeft
    const maxScroll = el.scrollWidth - el.clientWidth

    canScrollLeft.value = scrollLeft > 4
    canScrollRight.value = maxScroll > 4 && scrollLeft < maxScroll - 4
  }

  const scroll = (direction) => {
    const el = containerRef.value
    if (!el) return

    // Scroll by 2-3 cards or ~70% of visible container width
    const firstCard = el.querySelector('.feed-card, .quick-card, .album-card, .artist-card')
    const cardWidth = firstCard ? (firstCard.getBoundingClientRect().width + 12) : 180
    const visibleCards = Math.max(1, Math.floor(el.clientWidth / cardWidth))
    const step = Math.min(cardWidth * Math.max(2, visibleCards - 1), el.clientWidth * 0.8)

    el.scrollBy({
      left: direction === 'right' ? step : -step,
      behavior: 'smooth'
    })

    // Give browser time to finish smooth scroll, then update
    setTimeout(updateScrollState, 350)
  }

  const onWheel = (e) => {
    const el = containerRef.value
    if (!el) return

    // Only intercept when vertical wheel is dominant and Shift is not held
    if (!e.shiftKey && Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
      const scrollLeft = el.scrollLeft
      const maxScroll = el.scrollWidth - el.clientWidth

      if (maxScroll <= 2) return // Content doesn't overflow horizontally

      const atStart = scrollLeft <= 2
      const atEnd = scrollLeft >= maxScroll - 2

      // If scrolling right and we have room, OR scrolling left and we have room:
      if ((e.deltaY > 0 && !atEnd) || (e.deltaY < 0 && !atStart)) {
        e.preventDefault()
        el.scrollBy({
          left: e.deltaY * 1.3,
          behavior: 'auto'
        })
        updateScrollState()
      }
    }
  }

  const attachListeners = (el) => {
    if (!el) return
    el.addEventListener('scroll', updateScrollState, { passive: true })

    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => {
        updateScrollState()
      })
      resizeObserver.observe(el)
      // Also observe first child if present to detect content loads
      if (el.firstElementChild) {
        resizeObserver.observe(el.firstElementChild)
      }
    }

    nextTick(() => {
      updateScrollState()
    })
  }

  const detachListeners = (el) => {
    if (el) {
      el.removeEventListener('scroll', updateScrollState)
    }
    if (resizeObserver) {
      resizeObserver.disconnect()
      resizeObserver = null
    }
  }

  watch(containerRef, (newEl, oldEl) => {
    if (oldEl) detachListeners(oldEl)
    if (newEl) attachListeners(newEl)
  })

  onMounted(() => {
    if (containerRef.value) {
      attachListeners(containerRef.value)
    }
  })

  onUnmounted(() => {
    if (containerRef.value) {
      detachListeners(containerRef.value)
    }
  })

  return {
    containerRef,
    canScrollLeft,
    canScrollRight,
    updateScrollState,
    scroll,
    onWheel
  }
}
