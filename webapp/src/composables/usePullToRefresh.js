/**
 * Pull-to-refresh composable
 * Handles touch gestures for refreshing content
 */
import { ref } from 'vue'

export function usePullToRefresh(libraryStore, telegram = null) {
  const pullStartY = ref(0)
  const pullDistance = ref(0)
  const isPulling = ref(false)
  const contentRef = ref(null)

  // Minimum pull distance to trigger refresh
  const PULL_THRESHOLD = 60
  const MAX_PULL = 80

  /**
   * Handle touch start
   */
  const handleTouchStart = (e) => {
    // Only start pull if at top of scroll
    if (contentRef.value?.scrollTop > 0) return
    pullStartY.value = e.touches[0].clientY
  }

  /**
   * Handle touch move
   */
  const handleTouchMove = (e) => {
    if (!pullStartY.value) return
    if (libraryStore.refreshing) return
    
    const currentY = e.touches[0].clientY
    const diff = currentY - pullStartY.value
    
    // Only track downward pull from top
    if (diff > 0 && contentRef.value?.scrollTop === 0) {
      pullDistance.value = Math.min(diff * 0.5, MAX_PULL)
      isPulling.value = pullDistance.value >= PULL_THRESHOLD
    }
  }

  /**
   * Handle touch end
   */
  const handleTouchEnd = async () => {
    if (isPulling.value && pullDistance.value >= PULL_THRESHOLD) {
      // Trigger refresh
      telegram?.HapticFeedback?.impactOccurred?.('medium')
      await libraryStore.refresh()
    }
    
    // Reset state
    pullStartY.value = 0
    pullDistance.value = 0
    isPulling.value = false
  }

  return {
    // State
    pullStartY,
    pullDistance,
    isPulling,
    contentRef,
    
    // Methods
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
  }
}
