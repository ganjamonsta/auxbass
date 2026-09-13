<template>
  <div class="all-results-mode">
    <!-- Matching Tracks Overview -->
    <section v-if="topTracks.length > 0" class="result-section">
      <div class="result-header">
        <div class="header-left">
          <Music :size="18" class="header-icon" />
          <h3 class="result-title">Треки</h3>
          <span class="result-count">{{ totalTracksCount }}</span>
        </div>
        <button 
          v-if="totalTracksCount > topTracks.length" 
          class="section-view-all" 
          @click="$emit('switchFilter', 'tracks')"
        >
          <span>Все треки</span>
          <ArrowRight :size="14" />
        </button>
      </div>
      <div class="track-results-list">
        <TrackItem
          v-for="(track, index) in topTracks"
          :key="track.id"
          :track="track"
          :isPlaying="playerStore.currentTrack?.id === track.id"
          :isLiked="libraryStore.isTrackLiked(track.id)"
          :showAddToLibrary="!track.in_library && !libraryStore.isInLibrary(track.id)"
          :inLibrary="Boolean(track.in_library || libraryStore.isInLibrary(track.id))"
          @click="$emit('playTrack', track, topTracks, index)"
          @like="$emit('likeTrack', track)"
          @menu="(e) => $emit('menu', e, 'track', track)"
          @download="$emit('downloadTrack', track)"
          @hdNotice="$emit('hdNotice')"
          @addToLibrary="$emit('addToLibrary', track)"
        />
      </div>
    </section>

    <!-- Matching SoundCloud Global Search Overview -->
    <section v-if="soundcloudResults.length > 0" class="result-section soundcloud-section">
      <div class="result-header">
        <div class="header-left">
          <span class="sc-badge">SC</span>
          <h3 class="result-title">SoundCloud (Найдено в мире)</h3>
          <span class="result-count">{{ soundcloudResults.length }}</span>
        </div>
        <button 
          v-if="soundcloudResults.length > 5" 
          class="section-view-all" 
          @click="$emit('switchFilter', 'soundcloud')"
        >
          <span>Все {{ soundcloudResults.length }}</span>
          <ArrowRight :size="14" />
        </button>
      </div>
      
      <div class="sc-results-list">
        <ExternalTrackItem
          v-for="item in soundcloudResults.slice(0, 5)"
          :key="item.url"
          :item="item"
          variant="soundcloud"
          :is-importing="importingTrackUrl === item.url"
          :is-downloading="tasksStore.isTrackDownloading(item.url)"
          :is-queued="tasksStore.isTrackQueued(item.url)"
          :is-in-library="isTrackInLibrary(item)"
          @play="$emit('quickPlaySoundCloud', item)"
          @add="$emit('quickAddSoundCloud', item)"
        />
      </div>
    </section>

    <!-- Matching Spotify Global Search Overview -->
    <section v-if="spotifyResults.length > 0" class="result-section spotify-section">
      <div class="result-header">
        <div class="header-left">
          <span class="sp-badge">SP</span>
          <h3 class="result-title">Spotify (Каталог)</h3>
          <span class="result-count">{{ spotifyResults.length }}</span>
        </div>
        <button 
          v-if="spotifyResults.length > 5" 
          class="section-view-all" 
          @click="$emit('switchFilter', 'spotify')"
        >
          <span>Все {{ spotifyResults.length }}</span>
          <ArrowRight :size="14" />
        </button>
      </div>
      
      <div class="sc-results-list">
        <ExternalTrackItem
          v-for="item in spotifyResults.slice(0, 5)"
          :key="item.url"
          :item="item"
          variant="spotify"
          :is-importing="importingTrackUrl === item.url"
          :is-downloading="tasksStore.isTrackDownloading(item.url)"
          :is-queued="tasksStore.isTrackQueued(item.url)"
          :is-in-library="isTrackInLibrary(item)"
          @play="$emit('quickPlaySpotify', item)"
          @add="$emit('quickAddSpotify', item)"
        />
      </div>
    </section>

    <!-- Matching Artists Overview -->
    <section v-if="artistsResults.length > 0" class="result-section">
      <div class="result-header">
        <div class="header-left">
          <Users :size="18" class="header-icon" />
          <h3 class="result-title">Артисты</h3>
          <span class="result-count">{{ artistsResults.length }}</span>
        </div>
        <button 
          v-if="artistsResults.length > 6" 
          class="section-view-all" 
          @click="$emit('switchFilter', 'artists')"
        >
          <span>Все артисты</span>
          <ArrowRight :size="14" />
        </button>
      </div>
      <div class="horizontal-scroll">
        <div 
          v-for="artist in artistsResults.slice(0, 10)" 
          :key="artist.name || artist.artist"
          class="feed-card artist-card"
          @click="$emit('goToArtist', artist.name || artist.artist)"
        >
          <div class="feed-card-cover artist-cover" :style="getArtistCoverStyle(artist)">
            <img 
              v-if="artist.image_url" 
              :src="getCoverUrl(artist.image_url, CoverSize.MEDIUM)" 
              alt="" 
              loading="lazy"
            />
            <span v-else class="artist-initials">
              {{ getArtistInitials(artist) }}
            </span>
          </div>
          <div class="feed-card-title">{{ artist.name || artist.artist }}</div>
          <div class="feed-card-subtitle">
            <template v-if="artist.track_count">{{ artist.track_count }} {{ formatTrackCount(artist.track_count) }}</template>
            <template v-else>Исполнитель</template>
          </div>
          <div v-if="artist.tags?.length" class="card-tags center">
            <span v-for="t in artist.tags.slice(0, 2)" :key="t" class="card-tag">#{{ t }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Matching Albums Overview -->
    <section v-if="albumsResults.length > 0" class="result-section">
      <div class="result-header">
        <div class="header-left">
          <Disc3 :size="18" class="header-icon" />
          <h3 class="result-title">Альбомы</h3>
          <span class="result-count">{{ albumsResults.length }}</span>
        </div>
        <button 
          v-if="albumsResults.length > 6" 
          class="section-view-all" 
          @click="$emit('switchFilter', 'albums')"
        >
          <span>Все альбомы</span>
          <ArrowRight :size="14" />
        </button>
      </div>
      <div class="horizontal-scroll">
        <div 
          v-for="album in albumsResults.slice(0, 10)" 
          :key="album.id"
          class="feed-card"
          @click="$emit('goToAlbum', album.id)"
          @contextmenu.prevent="(e) => $emit('menu', e, 'album', album)"
        >
          <div class="feed-card-cover">
            <img 
              v-if="album.cover_url" 
              :src="getCoverUrl(album.cover_url, CoverSize.MEDIUM)" 
              alt="" 
              loading="lazy"
            />
            <Disc3 v-else :size="32" />
          </div>
          <div class="feed-card-title">{{ album.name }}</div>
          <div class="feed-card-subtitle">{{ album.artist }}</div>
          <div v-if="album.tags?.length" class="card-tags">
            <span v-for="t in album.tags.slice(0, 2)" :key="t" class="card-tag">#{{ t }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Matching Playlists Overview -->
    <section v-if="playlistsResults.length > 0" class="result-section">
      <div class="result-header">
        <div class="header-left">
          <Folder :size="18" class="header-icon" />
          <h3 class="result-title">Плейлисты</h3>
          <span class="result-count">{{ playlistsResults.length }}</span>
        </div>
        <button 
          v-if="playlistsResults.length > 6" 
          class="section-view-all" 
          @click="$emit('switchFilter', 'playlists')"
        >
          <span>Все плейлисты</span>
          <ArrowRight :size="14" />
        </button>
      </div>
      <div class="horizontal-scroll">
        <div 
          v-for="pl in playlistsResults.slice(0, 10)" 
          :key="pl.id"
          class="feed-card"
          @click="$emit('goToPlaylist', pl.id)"
          @contextmenu.prevent="(e) => $emit('menu', e, 'playlist', pl)"
        >
          <div class="feed-card-cover" :style="getPlaylistCoverStyle(pl)">
            <img 
              v-if="pl.covers?.length" 
              :src="getCoverUrl(pl.covers[0], CoverSize.MEDIUM)" 
              alt=""
              loading="lazy"
            />
            <Music v-else :size="32" />
          </div>
          <div class="feed-card-title">{{ pl.name }}</div>
          <div class="feed-card-subtitle">{{ pl.track_count || 0 }} {{ formatTrackCount(pl.track_count || 0) }}</div>
          <div v-if="pl.tags?.length" class="card-tags">
            <span v-for="t in pl.tags.slice(0, 2)" :key="t" class="card-tag">#{{ t }}</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { Music, ArrowRight, Users, Disc3, Folder } from 'lucide-vue-next'
import TrackItem from '@/components/TrackItem.vue'
import ExternalTrackItem from '@/components/ExternalTrackItem.vue'
import { getCoverUrl, CoverSize } from '@/utils'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useTasksStore } from '@/stores/tasks'

const props = defineProps({
  topTracks: { type: Array, required: true },
  totalTracksCount: { type: Number, required: true },
  soundcloudResults: { type: Array, required: true },
  spotifyResults: { type: Array, required: true },
  artistsResults: { type: Array, required: true },
  albumsResults: { type: Array, required: true },
  playlistsResults: { type: Array, required: true },
  importingTrackUrl: { type: String, default: null }
})

const emit = defineEmits([
  'switchFilter',
  'playTrack',
  'likeTrack',
  'menu',
  'downloadTrack',
  'hdNotice',
  'addToLibrary',
  'quickPlaySoundCloud',
  'quickAddSoundCloud',
  'quickPlaySpotify',
  'quickAddSpotify',
  'goToArtist',
  'goToAlbum',
  'goToPlaylist'
])

const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const tasksStore = useTasksStore()

const isTrackInLibrary = (item) => {
  if (!item) return false
  return item.in_library || tasksStore.isTrackCompleted(item.url)
}

const formatTrackCount = (count) => {
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod100 >= 11 && mod100 <= 19) return 'треков'
  if (mod10 === 1) return 'трек'
  if (mod10 >= 2 && mod10 <= 4) return 'трека'
  return 'треков'
}

const getArtistInitials = (artist) => {
  const name = artist?.name || artist?.artist || ''
  return name.slice(0, 2).toUpperCase() || '♪'
}

const getArtistCoverStyle = (artist) => {
  const str = artist?.name || artist?.artist || 'Artist'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash % 360)
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 50%, 30%) 0%, hsl(${(hue + 50) % 360}, 40%, 20%) 100%)`
  }
}

const getPlaylistCoverStyle = (playlist) => {
  if (playlist.covers?.length) return {}
  const str = playlist.name || 'Playlist'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash % 360)
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 55%, 35%) 0%, hsl(${(hue + 40) % 360}, 45%, 25%) 100%)`
  }
}
</script>
