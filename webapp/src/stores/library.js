import { defineStore } from 'pinia'
import { ref } from 'vue'
import { tracksApi, playlistsApi, playerApi } from '../api/client'

export const useLibraryStore = defineStore('library', () => {
  // State
  const tracks = ref([])
  const playlists = ref([])
  const artists = ref([])
  const artistImages = ref({})  // Cache for artist images
  const genres = ref([])
  const history = ref([])
  const likedTracks = ref([])  // Liked tracks
  const loading = ref(false)
  const refreshing = ref(false)
  const total = ref(0)
  const page = ref(1)
  const hasMore = ref(true)

  // Initialize
  const init = async () => {
    await Promise.all([
      fetchTracks(),
      fetchPlaylists(),
      fetchArtists(),
      fetchGenres(),    // For home feed genres
      fetchHistory(),   // For home feed
      fetchLikedTracks(),  // Liked tracks
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
      ])
    } finally {
      refreshing.value = false
    }
  }

  // Fetch tracks
  const fetchTracks = async (params = {}) => {
    loading.value = true
    try {
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
        
        // Prefetch file paths for first 10 tracks (speeds up first play)
        if (data.items.length > 0) {
          const trackIds = data.items.slice(0, 10).map(t => t.id)
          playerApi.prefetch(trackIds).catch(() => {})  // Fire and forget
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

  // Load more tracks
  const loadMore = async (params = {}) => {
    if (!hasMore.value || loading.value) return
    await fetchTracks({ ...params, page: page.value + 1 })
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

  // Fetch artists
  const fetchArtists = async () => {
    try {
      const response = await tracksApi.getArtists()
      artists.value = response.data
      
      // Fetch images for top 20 artists in background
      fetchArtistImages(response.data.slice(0, 20))
    } catch (error) {
      console.error('Failed to fetch artists:', error)
    }
  }

  // Fetch artist images from Last.fm
  const fetchArtistImages = async (artistList) => {
    for (const artist of artistList) {
      const name = artist.artist
      if (artistImages.value[name]) continue
      
      try {
        const response = await tracksApi.getArtistImage(name)
        if (response.data.image_url) {
          artistImages.value[name] = response.data.image_url
        }
      } catch (error) {
        // Ignore errors, just skip this artist
      }
    }
  }

  // Get artist image (from cache or placeholder)
  const getArtistImage = (artistName) => {
    return artistImages.value[artistName] || null
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
      const response = await tracksApi.getAll({ genre, limit: 100 })
      return response.data.tracks || response.data
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
    const track = tracks.value.find(t => t.id === trackId)
    if (track && track.is_liked !== undefined) return track.is_liked
    return likedTracks.value.some(t => t.id === trackId)
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

  return {
    tracks,
    playlists,
    artists,
    artistImages,
    genres,
    history,
    likedTracks,
    loading,
    refreshing,
    total,
    hasMore,
    init,
    refresh,
    fetchTracks,
    fetchTracksByGenre,
    loadMore,
    fetchPlaylists,
    fetchPlaylist,
    fetchArtists,
    fetchGenres,
    fetchHistory,
    fetchLikedTracks,
    getArtistImage,
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
  }
})
