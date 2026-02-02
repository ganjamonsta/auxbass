/**
 * useLayoutScroll - Composable for managing scroll behavior in mobile layout
 * 
 * Provides scroll state tracking and control for hiding/showing UI elements
 * like sub-headers based on scroll direction.
 */
import { ref, onMounted, onUnmounted } from 'vue'

export function useLayoutScroll(options = {}) {
  const {
    threshold = 50,        // Minimum scroll before direction detection
    hideOffset = 100,      // Scroll amount before hiding elements
    element = null         // Optional: specific element to track (else uses window)
  } = options

  const scrollTop = ref(0)
  const scrollDirection = ref('none') // 'up', 'down', 'none'
  const isScrolled = ref(false)       // True when scrolled past threshold
  const shouldHide = ref(false)       // True when elements should be hidden
  
  let lastScrollTop = 0
  let ticking = false

  const updateScroll = () => {
    const currentScroll = element?.value?.scrollTop ?? 
                          window.scrollY ?? 
                          document.documentElement.scrollTop

    // Update scroll position
    scrollTop.value = currentScroll

    // Detect scroll direction
    if (currentScroll > lastScrollTop + 5) {
      scrollDirection.value = 'down'
    } else if (currentScroll < lastScrollTop - 5) {
      scrollDirection.value = 'up'
    }

    // Update isScrolled state
    isScrolled.value = currentScroll > threshold

    // Update shouldHide state
    if (currentScroll > hideOffset && scrollDirection.value === 'down') {
      shouldHide.value = true
    } else if (scrollDirection.value === 'up' || currentScroll < threshold) {
      shouldHide.value = false
    }

    lastScrollTop = currentScroll
    ticking = false
  }

  const onScroll = () => {
    if (!ticking) {
      window.requestAnimationFrame(updateScroll)
      ticking = true
    }
  }

  const scrollToTop = (smooth = true) => {
    const target = element?.value ?? window
    if (target.scrollTo) {
      target.scrollTo({ top: 0, behavior: smooth ? 'smooth' : 'auto' })
    }
  }

  const resetState = () => {
    scrollTop.value = 0
    scrollDirection.value = 'none'
    isScrolled.value = false
    shouldHide.value = false
    lastScrollTop = 0
  }

  onMounted(() => {
    const target = element?.value ?? window
    target.addEventListener('scroll', onScroll, { passive: true })
  })

  onUnmounted(() => {
    const target = element?.value ?? window
    target.removeEventListener('scroll', onScroll)
  })

  return {
    scrollTop,
    scrollDirection,
    isScrolled,
    shouldHide,
    scrollToTop,
    resetState
  }
}

export default useLayoutScroll
