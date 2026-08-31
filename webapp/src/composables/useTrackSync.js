import { onMounted, onUnmounted, isRef } from 'vue'

/**
 * Composable that syncs a local tracks array with global track:changed / track:removed / track:removed:library events.
 * 
 * @param {import('vue').Ref<Array>|Function} tracksRef - A ref or getter returning the tracks array to sync.
 * @param {Object} [options] - Options
 * @param {boolean} [options.isLibraryList=false] - Whether this list represents the user's library
 */
export function useTrackSync(tracksRef, options = {}) {
  const getList = () => {
    if (isRef(tracksRef)) return tracksRef.value
    if (typeof tracksRef === 'function') return tracksRef()
    return null
  }

  const onTrackChanged = (e) => {
    const { trackId, data } = e.detail || {}
    if (!trackId || !data) return
    const list = getList()
    if (!list) return
    const idx = list.findIndex(t => t.id === trackId)
    if (idx !== -1) {
      Object.assign(list[idx], data)
    }
  }

  const onTrackRemoved = (e) => {
    const { trackId } = e.detail || {}
    if (!trackId) return
    const list = getList()
    if (!list) return
    const idx = list.findIndex(t => t.id === trackId)
    if (idx !== -1) {
      list.splice(idx, 1)
    }
  }

  const onLibraryTrackRemoved = (e) => {
    if (options.isLibraryList) {
      onTrackRemoved(e)
    }
  }

  onMounted(() => {
    window.addEventListener('track:changed', onTrackChanged)
    window.addEventListener('track:removed', onTrackRemoved)
    window.addEventListener('track:removed:library', onLibraryTrackRemoved)
  })

  onUnmounted(() => {
    window.removeEventListener('track:changed', onTrackChanged)
    window.removeEventListener('track:removed', onTrackRemoved)
    window.removeEventListener('track:removed:library', onLibraryTrackRemoved)
  })
}
