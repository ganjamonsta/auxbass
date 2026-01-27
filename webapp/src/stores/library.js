import { defineStore } from 'pinia'
import { ref } from 'vue'
import { tracksApi, playlistsApi, playerApi } from '../api/client'

export const useLibraryStore = defineStore('library', () => {
  // State - My Library
  const tracks = ref([])
  const playlists = ref([])
  const artists = ref([])
  const globalArtists = ref([])  // All artists from global library
  const artistScope = ref('library')  // 'library' or 'global'
  // LocalStorage key and TTL for artist images cache
  const ARTIST_IMAGES_CACHE_KEY = 'tg_player_artist_images'
  const ARTIST_IMAGES_CACHE_TTL = 24 * 60 * 60 * 1000 // 24 hours
  
  // Load artist images from localStorage
  const loadArtistImagesFromCache = () => {
    try {
      const cached = localStorage.getItem(ARTIST_IMAGES_CACHE_KEY)
      if (cached) {
        const { data, timestamp } = JSON.parse(cached)
        // Check if cache is still valid
        if (Date.now() - timestamp < ARTIST_IMAGES_CACHE_TTL) {
          return data
        }
      }
    } catch (e) {
      // Ignore cache errors
    }
    return {}
  }
  
  // Save artist images to localStorage
  const saveArtistImagesToCache = (images) => {
    try {
      localStorage.setItem(ARTIST_IMAGES_CACHE_KEY, JSON.stringify({
        data: images,
        timestamp: Date.now()
      }))
    } catch (e) {
      // Ignore cache errors (e.g., quota exceeded)
    }
  }
  
  const artistImages = ref(loadArtistImagesFromCache())  // Cache for artist images with persistence
  const genres = ref([])
  const history = ref([])
  const likedTracks = ref([])  // Liked tracks
  const loading = ref(false)
  const refreshing = ref(false)
  const total = ref(0)
  const page = ref(1)
  const hasMore = ref(true)
  const currentSearchParams = ref({})  // Store current search/filter params for loadMore
  
  // State - Global Library
  const globalTracks = ref([])
  const globalLoading = ref(false)
  const globalTotal = ref(0)
  const globalPage = ref(1)
  const globalHasMore = ref(true)
  const globalSearchParams = ref({})  // Store current search/filter params for global loadMore
  const recentUploads = ref([])
  const popularTracks = ref([])
  const globalStats = ref(null)
  const topUsers = ref([])
  const selectedUser = ref(null)
  const selectedUserTracks = ref([])

  // Initialize
  const init = async () => {
    await Promise.all([
      fetchTracks(),
      fetchPlaylists(),
      fetchArtists(),
      fetchGenres(),    // For home feed genres
      fetchHistory(),   // For home feed
      fetchLikedTracks(),  // Liked tracks
      fetchGlobalStats(), // Global library stats
      fetchRecentUploads(), // Recent uploads from all users
    ])
  }

  // Refresh all data (pull-to-refresh)
  const refresh = async () => {
    refreshing.value = true
    try {
      await Promise.all([
        fetchTracks(),
        fetchPlaylists(),
        fetchArtists(),
        fetchGenres(),
        fetchHistory(),
        fetchLikedTracks(),
        fetchGlobalStats(),
        fetchRecentUploads(),
      ])
    } finally {
      refreshing.value = false
    }
  }

  // Fetch tracks
  const fetchTracks = async (params = {}) => {
    loading.value = true
    try {
      // Save search params for loadMore (exclude page)
      const { page: pageParam, ...searchParams } = params
      if (!pageParam || pageParam === 1) {
        currentSearchParams.value = searchParams
      }
      
      const response = await tracksApi.getAll({
        page: params.page || 1,
        per_page: 50,
        ...params,
      })
      
      const data = response.data
      
      if (params.page && params.page > 1) {
        tracks.value = [...tracks.value, ...data.items]
      } else {
        tracks.value = data.items
        
        // Aggressive prefetch: Get both file paths AND stream URLs for first 5 tracks
        // This ensures the first track can start almost instantly
        if (data.items.length > 0) {
          const firstTrackIds = data.items.slice(0, 5).map(t => t.id)
          
          // 1. Prefetch file paths on server (parallel Telegram API calls)
          playerApi.prefetch(firstTrackIds).catch(() => {})
          
          // 2. Pre-generate stream URL tokens for first 3 tracks
          // This saves ~200-400ms on first play
          playerApi.getBatchUrls(firstTrackIds.slice(0, 3))
            .then(response => {
              const urlData = response.data.urls || []
              for (const item of urlData) {
                if (item.url && !item.error) {
                  // Store in a way player.js can access (via window for simplicity)
                  window._prefetchedUrls = window._prefetchedUrls || new Map()
                  window._prefetchedUrls.set(item.track_id, {
                    url: item.url,
                    expires_at: item.expires_at
                  })
                }
              }
              console.log(`[Prefetch] Pre-generated ${urlData.filter(u => u.url).length} stream URLs`)
            })
            .catch(() => {})  // Fire and forget
        }
      }
      
      total.value = data.total
      page.value = data.page
      hasMore.value = tracks.value.length < data.total
    } catch (error) {
      console.error('Failed to fetch tracks:', error)
    } finally {
      loading.value = false
    }
  }

  // Load more tracks (preserves current search/filter params)
  const loadMore = async () => {
    if (!hasMore.value || loading.value) return
    await fetchTracks({ ...currentSearchParams.value, page: page.value + 1 })
  }

  // Fetch playlists
  const fetchPlaylists = async () => {
    try {
      const response = await playlistsApi.getAll()
      playlists.value = response.data
    } catch (error) {
      console.error('Failed to fetch playlists:', error)
    }
  }

  // Fetch single playlist with tracks
  const fetchPlaylist = async (id) => {
    try {
      const response = await playlistsApi.getOne(id)
      return response.data
    } catch (error) {
      console.error('Failed to fetch playlist:', error)
      return null
    }
  }

  // Fetch artists (with scope: 'library' or 'global')
  const fetchArtists = async (scope = 'library') => {
    try {
      artistScope.value = scope
      const response = await tracksApi.getArtists(scope)
      
      if (scope === 'global') {
        globalArtists.value = response.data
        // Fetch images for ALL global artists in background
        fetchArtistImages(response.data)
      } else {
        artists.value = response.data
        // Fetch images for ALL artists in background
        fetchArtistImages(response.data)
      }
    } catch (error) {
      console.error('Failed to fetch artists:', error)
    }
  }
  
  // Get current artists based on scope
  const currentArtists = () => {
    return artistScope.value === 'global' ? globalArtists.value : artists.value
  }

  // Current artist detail for ArtistCard view
  const currentArtist = ref(null)
  const artistLoading = ref(false)

  // Fetch artist detail with tracks, albums and playlists
  const fetchArtistDetail = async (artistName, scope = 'library') => {
    artistLoading.value = true
    try {
      const response = await tracksApi.getArtistDetail(artistName, scope)
      currentArtist.value = response.data
      
      // Sync artist image to cache to avoid desync between main page and artist card
      if (response.data.image_url) {
        artistImages.value[artistName] = response.data.image_url
      }
      
      return response.data
    } catch (error) {
      console.error('Failed to fetch artist detail:', error)
      currentArtist.value = null
      return null
    } finally {
      artistLoading.value = false
    }
  }

  // Clear current artist
  const clearCurrentArtist = () => {
    currentArtist.value = null
  }

  // Set current artist (for navigation history restore)
  const setCurrentArtist = (artist) => {
    currentArtist.value = artist
  }

  // Fetch artist images from Last.fm (in batches to not overload)
  const fetchArtistImages = async (artistList) => {
    const BATCH_SIZE = 5  // Load 5 at a time
    const DELAY_MS = 100  // Small delay between batches
    let hasNewImages = false
    
    // Filter out artists we already have cached (including null = no image)
    // Support both {artist: "..."} and {name: "..."} formats
    const uncachedArtists = artistList.filter(artist => {
      const artistName = artist.artist || artist.name
      return artistName && artistImages.value[artistName] === undefined
    })
    
    if (uncachedArtists.length === 0) return  // All cached, skip API calls
    
    for (let i = 0; i < uncachedArtists.length; i += BATCH_SIZE) {
      const batch = uncachedArtists.slice(i, i + BATCH_SIZE)
      
      // Process batch in parallel
      await Promise.all(batch.map(async (artist) => {
        const name = artist.artist || artist.name
        if (!name) return  // Skip if no name
        
        try {
          const response = await tracksApi.getArtistImage(name)
          if (response.data.image_url) {
            artistImages.value[name] = response.data.image_url
            hasNewImages = true
          } else {
            // Cache null result to avoid re-fetching
            artistImages.value[name] = null
            hasNewImages = true
          }
        } catch (error) {
          // Ignore errors, just skip this artist
        }
      }))
      
      // Small delay to not overload API
      if (i + BATCH_SIZE < uncachedArtists.length) {
        await new Promise(resolve => setTimeout(resolve, DELAY_MS))
      }
    }
    
    // Persist to localStorage after batch fetch
    if (hasNewImages) {
      saveArtistImagesToCache(artistImages.value)
    }
  }

  // Get artist image (from cache or placeholder)
  const getArtistImage = (artistName) => {
    return artistImages.value[artistName] || null
  }
  
  // Clear artist images cache (for forced refresh)
  const clearArtistImagesCache = () => {
    artistImages.value = {}
    localStorage.removeItem(ARTIST_IMAGES_CACHE_KEY)
  }

  // Fetch genres
  const fetchGenres = async () => {
    try {
      const response = await tracksApi.getGenres()
      genres.value = response.data
    } catch (error) {
      console.error('Failed to fetch genres:', error)
    }
  }

  // Create playlist
  const createPlaylist = async (name, description = '') => {
    try {
      const response = await playlistsApi.create({ name, description })
      playlists.value.unshift(response.data)
      return response.data
    } catch (error) {
      console.error('Failed to create playlist:', error)
      return null
    }
  }

  // Delete playlist
  const deletePlaylist = async (id) => {
    try {
      await playlistsApi.delete(id)
      playlists.value = playlists.value.filter(p => p.id !== id)
    } catch (error) {
      console.error('Failed to delete playlist:', error)
    }
  }

  // Add track to playlist
  const addTrackToPlaylist = async (playlistId, trackId) => {
    try {
      await playlistsApi.addTrack(playlistId, trackId)
      return true
    } catch (error) {
      console.error('Failed to add track to playlist:', error)
      return false
    }
  }

  // Remove track from playlist
  const removeTrackFromPlaylist = async (playlistId, trackId) => {
    try {
      await playlistsApi.removeTrack(playlistId, trackId)
      return true
    } catch (error) {
      console.error('Failed to remove track from playlist:', error)
      return false
    }
  }

  // Update track
  const updateTrack = async (id, data) => {
    try {
      const response = await tracksApi.update(id, data)
      const index = tracks.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tracks.value[index] = response.data
      }
      // Refresh artists list if artist was changed
      if (data.artist !== undefined) {
        fetchArtists(artistScope.value)
      }
      return response.data
    } catch (error) {
      console.error('Failed to update track:', error)
      return null
    }
  }

  // Delete track
  const deleteTrack = async (id) => {
    try {
      await tracksApi.delete(id)
      tracks.value = tracks.value.filter(t => t.id !== id)
      total.value--
    } catch (error) {
      console.error('Failed to delete track:', error)
    }
  }

  // Fetch listening history
  const fetchHistory = async (limit = 30) => {
    try {
      const response = await tracksApi.getHistory(limit)
      history.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch history:', error)
      return []
    }
  }

  // Fetch tracks by genre (for shuffle play)
  const fetchTracksByGenre = async (genre) => {
    try {
      const response = await tracksApi.getAll({ genre, per_page: 100 })
      return response.data.items || []
    } catch (error) {
      console.error('Failed to fetch tracks by genre:', error)
      return []
    }
  }

  // Fetch liked tracks
  const fetchLikedTracks = async () => {
    try {
      const response = await tracksApi.getLiked()
      likedTracks.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch liked tracks:', error)
      return []
    }
  }

  // Toggle like on track
  const toggleLike = async (trackId) => {
    // Find track in tracks list
    const track = tracks.value.find(t => t.id === trackId)
    const isLiked = track?.is_liked || likedTracks.value.some(t => t.id === trackId)
    
    try {
      if (isLiked) {
        await tracksApi.unlike(trackId)
        // Update local state
        if (track) track.is_liked = false
        likedTracks.value = likedTracks.value.filter(t => t.id !== trackId)
      } else {
        await tracksApi.like(trackId)
        // Update local state
        if (track) track.is_liked = true
        // Refetch liked tracks to get proper order
        await fetchLikedTracks()
      }
      return !isLiked
    } catch (error) {
      console.error('Failed to toggle like:', error)
      return isLiked
    }
  }

  // Check if track is liked
  const isTrackLiked = (trackId) => {
    // First check likedTracks array (source of truth)
    if (likedTracks.value.some(t => t.id === trackId)) return true
    // Fallback to track's is_liked property
    const track = tracks.value.find(t => t.id === trackId)
    return track?.is_liked === true
  }

  // Get unavailable tracks count
  const unavailableCount = () => {
    return tracks.value.filter(t => t.is_unavailable).length
  }

  // Delete all unavailable tracks
  const deleteUnavailableTracks = async () => {
    try {
      const result = await tracksApi.deleteAllUnavailable()
      // Remove from local state
      tracks.value = tracks.value.filter(t => !t.is_unavailable)
      likedTracks.value = likedTracks.value.filter(t => !t.is_unavailable)
      return result.data.count || 0
    } catch (error) {
      console.error('Failed to delete unavailable tracks:', error)
      return 0
    }
  }

  // ============== GLOBAL LIBRARY ==============
  
  // Fetch global tracks
  const fetchGlobalTracks = async (params = {}) => {
    globalLoading.value = true
    try {
      // Save search params for loadMoreGlobal (exclude page)
      const { page: pageParam, ...searchParams } = params
      if (!pageParam || pageParam === 1) {
        globalSearchParams.value = searchParams
      }
      
      const response = await tracksApi.getGlobal({
        page: params.page || 1,
        per_page: 50,
        ...params,
      })
      
      const data = response.data
      
      if (params.page && params.page > 1) {
        globalTracks.value = [...globalTracks.value, ...data.items]
      } else {
        globalTracks.value = data.items
      }
      
      globalTotal.value = data.total
      globalPage.value = data.page
      globalHasMore.value = globalTracks.value.length < data.total
    } catch (error) {
      console.error('Failed to fetch global tracks:', error)
    } finally {
      globalLoading.value = false
    }
  }
  
  // Load more global tracks (preserves current search/filter params)
  const loadMoreGlobal = async () => {
    if (!globalHasMore.value || globalLoading.value) return
    await fetchGlobalTracks({ ...globalSearchParams.value, page: globalPage.value + 1 })
  }
  
  // Fetch recent uploads from all users
  const fetchRecentUploads = async (limit = 20) => {
    try {
      const response = await tracksApi.getRecentUploads(limit)
      recentUploads.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch recent uploads:', error)
      return []
    }
  }
  
  // Fetch popular tracks globally
  const fetchPopularTracks = async (limit = 20) => {
    try {
      const response = await tracksApi.getPopular(limit)
      popularTracks.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch popular tracks:', error)
      return []
    }
  }
  
  // Fetch global stats
  const fetchGlobalStats = async () => {
    try {
      const response = await tracksApi.getGlobalStats()
      globalStats.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch global stats:', error)
      return null
    }
  }
  
  // Add track to my library from global
  const addToLibrary = async (trackId) => {
    try {
      await tracksApi.addToLibrary(trackId)
      // Update local state - check all possible track sources
      const updateTrackInLibrary = (list) => {
        const track = list.find(t => t.id === trackId)
        if (track) {
          track.in_library = true
        }
        return track
      }
      
      // Update in_library flag in all lists where track might exist
      const track = updateTrackInLibrary(globalTracks.value) ||
                    updateTrackInLibrary(recentUploads.value) ||
                    updateTrackInLibrary(popularTracks.value) ||
                    updateTrackInLibrary(selectedUserTracks.value)
      
      if (track) {
        // Also add to tracks list
        if (!tracks.value.find(t => t.id === trackId)) {
          tracks.value.unshift({ ...track, in_library: true })
        }
      }
      return true
    } catch (error) {
      console.error('Failed to add to library:', error)
      return false
    }
  }
  
  // Remove track from my library
  const removeFromLibrary = async (trackId) => {
    try {
      await tracksApi.removeFromLibrary(trackId)
      // Update local state
      tracks.value = tracks.value.filter(t => t.id !== trackId)
      // Update in_library flag in global lists
      const updateInLibrary = (list) => {
        const track = list.find(t => t.id === trackId)
        if (track) track.in_library = false
      }
      updateInLibrary(globalTracks.value)
      updateInLibrary(recentUploads.value)
      updateInLibrary(popularTracks.value)
      updateInLibrary(selectedUserTracks.value)
      return true
    } catch (error) {
      console.error('Failed to remove from library:', error)
      return false
    }
  }
  
  // Check if track is in my library
  const isInLibrary = (trackId) => {
    return tracks.value.some(t => t.id === trackId)
  }
  
  // Fetch top users
  const fetchTopUsers = async () => {
    try {
      const response = await tracksApi.getTopUsers(20)
      topUsers.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch top users:', error)
      return []
    }
  }
  
  // Fetch tracks by specific user
  const fetchUserTracks = async (userId) => {
    try {
      const user = topUsers.value.find(u => u.id === userId)
      selectedUser.value = user || { id: userId }
      const response = await tracksApi.getUserTracks(userId, 50)
      selectedUserTracks.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch user tracks:', error)
      return []
    }
  }
  
  // Clear selected user
  const clearSelectedUser = () => {
    selectedUser.value = null
    selectedUserTracks.value = []
  }

  return {
    // My library
    tracks,
    playlists,
    artists,
    globalArtists,
    artistScope,
    artistImages,
    genres,
    history,
    likedTracks,
    loading,
    refreshing,
    total,
    hasMore,
    
    // Global library
    globalTracks,
    globalLoading,
    globalTotal,
    globalHasMore,
    recentUploads,
    popularTracks,
    globalStats,
    topUsers,
    selectedUser,
    selectedUserTracks,
    
    // Artist detail
    currentArtist,
    artistLoading,
    
    // Methods
    init,
    refresh,
    fetchTracks,
    fetchTracksByGenre,
    loadMore,
    fetchPlaylists,
    fetchPlaylist,
    fetchArtists,
    fetchArtistDetail,
    clearCurrentArtist,
    setCurrentArtist,
    fetchGenres,
    fetchHistory,
    fetchLikedTracks,
    getArtistImage,
    clearArtistImagesCache,
    createPlaylist,
    deletePlaylist,
    addTrackToPlaylist,
    removeTrackFromPlaylist,
    updateTrack,
    deleteTrack,
    toggleLike,
    isTrackLiked,
    unavailableCount,
    deleteUnavailableTracks,
    
    // Global library methods
    fetchGlobalTracks,
    loadMoreGlobal,
    fetchRecentUploads,
    fetchPopularTracks,
    fetchGlobalStats,
    fetchTopUsers,
    fetchUserTracks,
    clearSelectedUser,
    addToLibrary,
    removeFromLibrary,
    isInLibrary,
  }
})
