import { ref, watch, computed } from 'vue'

/**
 * Sort options configuration
 */
export const SORT_OPTIONS = {
  // For tracks/library
  library: [
    { key: 'added_at', label: 'Дата', icon: '📅' },
    { key: 'title', label: 'Название', icon: '🔤' },
    { key: 'artist', label: 'Артист', icon: '👤' },
    { key: 'duration', label: 'Время', icon: '⏱' },
  ],
  // For artists
  artists: [
    { key: 'name', label: 'Имя', icon: '🔤' },
    { key: 'track_count', label: 'Треки', icon: '🎵' },
    { key: 'album_count', label: 'Альбомы', icon: '💿' },
    { key: 'latest_release', label: 'Релиз', icon: '📅' },
  ],
  // For albums
  albums: [
    { key: 'name', label: 'Название', icon: '🔤' },
    { key: 'artist', label: 'Артист', icon: '👤' },
    { key: 'release_date', label: 'Дата', icon: '📅' },
    { key: 'track_count', label: 'Треки', icon: '🎵' },
  ],
}

/**
 * Default sort orders for each sort key
 * true = desc preferred, false = asc preferred
 */
const DEFAULT_DESC = {
  added_at: true,
  latest_release: true,
  release_date: true,
  track_count: true,
  album_count: true,
  duration: true,
  // These prefer ascending
  name: false,
  title: false,
  artist: false,
}

/**
 * Universal sort composable with localStorage persistence
 * 
 * @param {string} storageKey - Key for localStorage (e.g., 'library-sort', 'artists-sort')
 * @param {string} optionsType - Type of sort options ('library', 'artists', 'albums')
 * @param {Object} defaults - Default values { sortBy, sortOrder }
 * 
 * @returns {Object} Sort state and methods
 */
export function useSort(storageKey, optionsType = 'library', defaults = {}) {
  const options = SORT_OPTIONS[optionsType] || SORT_OPTIONS.library
  
  // Load from localStorage or use defaults
  const savedSort = localStorage.getItem(storageKey)
  let initialSortBy = defaults.sortBy || options[0].key
  let initialSortOrder = defaults.sortOrder || 'desc'
  
  if (savedSort) {
    try {
      const parsed = JSON.parse(savedSort)
      if (parsed.sortBy && options.some(o => o.key === parsed.sortBy)) {
        initialSortBy = parsed.sortBy
      }
      if (parsed.sortOrder === 'asc' || parsed.sortOrder === 'desc') {
        initialSortOrder = parsed.sortOrder
      }
    } catch (e) {
      console.warn('Failed to parse saved sort:', e)
    }
  }
  
  const sortBy = ref(initialSortBy)
  const sortOrder = ref(initialSortOrder)
  
  // Current option object
  const currentOption = computed(() => 
    options.find(o => o.key === sortBy.value) || options[0]
  )
  
  // Current option index
  const currentIndex = computed(() => 
    options.findIndex(o => o.key === sortBy.value)
  )
  
  // Save to localStorage on change
  watch([sortBy, sortOrder], () => {
    localStorage.setItem(storageKey, JSON.stringify({
      sortBy: sortBy.value,
      sortOrder: sortOrder.value
    }))
  })
  
  /**
   * Cycle to next sort option
   */
  const nextSort = () => {
    const nextIndex = (currentIndex.value + 1) % options.length
    const nextOption = options[nextIndex]
    sortBy.value = nextOption.key
    // Set default order for this sort type
    sortOrder.value = DEFAULT_DESC[nextOption.key] ? 'desc' : 'asc'
  }
  
  /**
   * Toggle sort order
   */
  const toggleOrder = () => {
    sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
  }
  
  /**
   * Set specific sort
   */
  const setSort = (key, order = null) => {
    if (options.some(o => o.key === key)) {
      sortBy.value = key
      if (order) {
        sortOrder.value = order
      } else {
        sortOrder.value = DEFAULT_DESC[key] ? 'desc' : 'asc'
      }
    }
  }
  
  return {
    sortBy,
    sortOrder,
    options,
    currentOption,
    currentIndex,
    nextSort,
    toggleOrder,
    setSort,
  }
}

export default useSort
