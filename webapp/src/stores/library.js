import { defineStore } from 'pinia'
import { ref } from 'vue'
import { tracksApi, playlistsApi } from '../api/client'

export const useLibraryStore = defineStore('library', () => {
  // State
  const tracks = ref([])
  const playlists = ref([])
  const artists = ref([])
  const genres = ref([])
  const history = ref([])
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
    } catch (error) {
      console.error('Failed to fetch artists:', error)
    }
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
  const fetchHistory = async (limit = 50) => {
    try {
      const response = await tracksApi.getHistory(limit)
      history.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch history:', error)
      return []
    }
  }

  return {
    tracks,
    playlists,
    artists,
    genres,
    history,
    loading,
    refreshing,
    total,
    hasMore,
    init,
    refresh,
    fetchTracks,
    loadMore,
    fetchPlaylists,
    fetchPlaylist,
    fetchArtists,
    fetchGenres,
    fetchHistory,
    createPlaylist,
    deletePlaylist,
    addTrackToPlaylist,
    removeTrackFromPlaylist,
    updateTrack,
    deleteTrack,
  }
})
