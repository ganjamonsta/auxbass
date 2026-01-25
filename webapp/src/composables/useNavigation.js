/**
 * Navigation composable
 * Handles view navigation, tabs, history stack
 */
import { ref, computed } from 'vue'

export function useNavigation() {
  // Current view: 'library' | 'playlist' | 'artist'
  const currentView = ref('library')
  
  // Current tab within library view
  const activeTab = ref('home')
  
  // Navigation history stack for back button
  const navigationStack = ref([])
  
  // Fullscreen section view
  const expandedSection = ref(null) // 'albums', 'sources', 'playlists' or null
  
  // Current playlist when viewing playlist detail
  const currentPlaylist = ref(null)

  /**
   * Tab display names
   */
  const tabNames = {
    'home': 'Главная',
    'tracks': 'Треки',
    'playlists': 'Плейлисты',
    'artists': 'Артисты',
    'genres': 'Жанры',
    'explore': 'Обзор',
    'queue': 'Очередь',
    'history': 'Недавнее',
    'liked': 'Любимое',
    'search': 'Поиск'
  }

  /**
   * Current tab name for header
   */
  const currentTabName = computed(() => {
    return tabNames[activeTab.value] || 'Музыка'
  })

  /**
   * Header title based on current view
   */
  const headerTitle = computed(() => {
    switch (currentView.value) {
      case 'library': return 'TG Player'
      case 'playlist': return currentPlaylist.value?.name || 'Плейлист'
      case 'artist': return 'Артист'
      default: return 'TG Player'
    }
  })

  /**
   * Push current state to navigation stack
   */
  const pushNavigation = () => {
    navigationStack.value.push({
      view: currentView.value,
      tab: activeTab.value,
      filter: null, // Can be extended
      playlist: currentPlaylist.value,
      section: expandedSection.value,
    })
  }

  /**
   * Navigate back using history stack
   */
  const goBack = () => {
    // If we have navigation history, use it
    if (navigationStack.value.length > 0) {
      const prev = navigationStack.value.pop()
      currentView.value = prev.view
      activeTab.value = prev.tab
      currentPlaylist.value = prev.playlist
      expandedSection.value = prev.section
      return true
    }
    
    // Default fallback behavior
    if (expandedSection.value) {
      expandedSection.value = null
      return true
    }
    
    if (currentView.value !== 'library') {
      currentView.value = 'library'
      return true
    }
    
    if (activeTab.value !== 'home') {
      activeTab.value = 'home'
      return true
    }
    
    return false
  }

  /**
   * Navigate to home
   */
  const goToHome = () => {
    currentView.value = 'library'
    activeTab.value = 'home'
    expandedSection.value = null
    navigationStack.value = []
  }

  /**
   * Open playlist detail view
   */
  const openPlaylist = (playlist) => {
    pushNavigation()
    currentPlaylist.value = playlist
    currentView.value = 'playlist'
  }

  /**
   * Open artist detail view
   */
  const openArtist = (artistName, libraryStore) => {
    pushNavigation()
    currentView.value = 'artist'
    libraryStore.fetchArtistDetail(artistName)
  }

  /**
   * Expand a section (albums, sources, etc.)
   */
  const expandSection = (section) => {
    pushNavigation()
    expandedSection.value = section
  }

  /**
   * Handle sidebar navigation
   */
  const handleSidebarNavigate = (tab) => {
    if (currentView.value !== 'library') {
      pushNavigation()
    }
    currentView.value = 'library'
    activeTab.value = tab
    expandedSection.value = null
  }

  return {
    // State
    currentView,
    activeTab,
    navigationStack,
    expandedSection,
    currentPlaylist,
    
    // Computed
    currentTabName,
    headerTitle,
    
    // Methods
    pushNavigation,
    goBack,
    goToHome,
    openPlaylist,
    openArtist,
    expandSection,
    handleSidebarNavigate,
  }
}
