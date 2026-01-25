<template>
  <!-- Auth checking state -->
  <div v-if="authChecking" class="auth-loading">
    <div class="auth-spinner"></div>
  </div>
  
  <!-- Login page for non-authenticated users (browser only) -->
  <LoginPage v-else-if="!isAuthenticated" @login="handleLogin" />
  
  <!-- Main app for authenticated users -->
  <div v-else class="app spotify-theme" :class="{ 'desktop-layout': isDesktop, 'has-now-playing': isDesktop && player.currentTrack }">
    <!-- Desktop Sidebar -->
    <Sidebar 
      v-if="isDesktop"
      :activeTab="activeTab"
      :playlists="library.playlists"
      :trackCount="library.total"
      :artistCount="library.artists.length"
      :likedCount="library.likedTracks.length"
      :historyCount="library.history.length"
      :userName="userDisplayName"
      @navigate="handleSidebarNavigate"
      @openPlaylist="openPlaylist"
      @createPlaylist="createPlaylist"
      @logout="handleLogout"
      @playlistMenu="showPlaylistMenu"
    />

    <!-- Main Content Wrapper -->
    <div class="main-content-wrapper">
    <!-- App Header -->
    <AppHeader
      :isLibraryView="currentView === 'library'"
      :showSearch="showSearch"
      :searchQuery="searchQuery"
      :searchTags="searchTags"
      :searchScope="searchScope"
      :tabName="currentTabName"
      :title="headerTitle"
      @toggleSearch="toggleSearch"
      @closeSearch="closeSearch"
      @toggleScope="toggleSearchScope"
      @update:searchQuery="(val) => { searchQuery = val; debouncedSearch() }"
      @addTag="addTag"
      @removeTag="removeTag"
      @handleBackspace="handleBackspace"
      @goHome="goToHome"
      @goBack="goBack"
    />

    <!-- Main content -->
    <main 
      ref="contentRef"
      class="content"
      @scroll="handleContentScroll"
      @touchstart="handleTouchStartLocal"
      @touchmove="handleTouchMoveLocal"
      @touchend="handleTouchEndLocal"
    >
      <!-- Pull to refresh indicator -->
      <div 
        v-if="pullDistance > 0" 
        class="pull-indicator"
        :style="{ transform: `translateY(${Math.min(pullDistance, 80)}px)` }"
      >
        <div class="pull-spinner" :class="{ active: isPulling }">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" :style="{ transform: `rotate(${pullDistance * 3}deg)` }">
            <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
          </svg>
        </div>
        <span v-if="library.refreshing">Обновление...</span>
        <span v-else-if="pullDistance > 60">Отпустите для обновления</span>
        <span v-else>Потяните для обновления</span>
      </div>

      <!-- Library view -->
      <div v-if="currentView === 'library'" class="library">
        <!-- Active filter indicator -->
        <div v-if="activeFilter" class="active-filter">
          <span v-if="filterScope === 'global'" class="global-badge">🌍</span>
          <span>{{ activeFilter }}</span>
          <button @click="clearFilter" class="clear-filter-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
            </svg>
          </button>
        </div>

        <!-- Home Feed -->
        <HomeFeed
          v-if="activeTab === 'home'"
          :artists="library.artists"
          :artistImages="library.artistImages"
          :genres="library.genres"
          :tracks="library.tracks"
          :totalTracks="library.total"
          :likedCount="library.likedTracks.length"
          :historyCount="library.history.length"
          :playlistCount="library.playlists.length"
          :currentTrackId="player.currentTrack?.id"
          :isPlaying="player.isPlaying"
          :isTrackLiked="library.isTrackLiked"
          @navigate="activeTab = $event"
          @filterArtist="filterByArtist"
          @playGenre="playGenreShuffle"
          @play="playTrack"
          @menu="showTrackMenu"
          @like="toggleLike"
        />

        <!-- Search Results -->
        <SearchResults
          v-if="activeTab === 'search'"
          :artists="searchResultArtists"
          :artistImages="library.artistImages"
          :albums="searchResultAlbums"
          :playlists="searchResultPlaylists"
          :tracks="displayedTracks"
          :totalTracks="filterScope === 'global' ? library.globalTotal : library.total"
          :loading="library.loading || library.globalLoading"
          :hasQuery="!!activeFilter"
          :currentTrackId="player.currentTrack?.id"
          :isPlaying="player.isPlaying"
          :isTrackLiked="library.isTrackLiked"
          @filterArtist="(artist) => filterByArtist(artist, searchScope)"
          @openPlaylist="openPlaylist"
          @play="(track, queue) => playTrack(track, queue || displayedTracks)"
          @menu="showTrackMenu"
          @like="toggleLike"
          @navigate="activeTab = $event"
        />
        
        <!-- Track list -->
        <TrackListView
          v-if="activeTab === 'tracks'"
          :tracks="displayedTracks"
          :loading="library.loading || library.globalLoading"
          :hasMore="library.hasMore"
          :isGlobal="filterScope === 'global'"
          :currentTrackId="player.currentTrack?.id"
          :isPlaying="player.isPlaying"
          :isTrackLiked="library.isTrackLiked"
          @play="(track, queue) => playTrack(track, queue || displayedTracks)"
          @menu="showTrackMenu"
          @like="toggleLike"
          @loadMore="library.loadMore()"
        />

        <!-- Playlists -->
        <PlaylistsView
          v-if="activeTab === 'playlists'"
          :likedCount="library.likedTracks.length"
          :historyCount="library.history.length"
          :sourcePlaylists="sourcePlaylists"
          :albumPlaylists="albumPlaylists"
          :userPlaylists="userPlaylists"
          @navigate="activeTab = $event"
          @openSection="openSection"
          @openPlaylist="openPlaylist"
          @createPlaylist="createPlaylist"
        />

        <!-- Artists -->
        <ArtistsView
          v-if="activeTab === 'artists'"
          :artists="displayedArtists"
          :artistImages="library.artistImages"
          :scope="library.artistScope"
          @changeScope="library.fetchArtists"
          @filterArtist="(artist) => filterByArtist(artist, library.artistScope)"
        />

        <!-- Genres -->
        <div v-if="activeTab === 'genres'" class="list-section">
          <div v-if="library.genres.length === 0" class="empty">
            <div class="empty-icon">🎸</div>
            <p class="empty-title">Нет жанров</p>
            <p class="empty-hint">Жанры определяются из метаданных</p>
          </div>
          <div
            v-for="genre in library.genres"
            :key="genre.genre"
            class="list-item"
            @click="filterByGenre(genre.genre)"
          >
            <div class="list-item-avatar genre">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
              </svg>
            </div>
            <div class="list-item-content">
              <span class="list-item-title">{{ genre.genre }}</span>
              <span class="list-item-subtitle">{{ genre.count }} треков</span>
            </div>
            <svg class="list-item-arrow" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
            </svg>
          </div>
        </div>

        <!-- Queue tab -->
        <div v-if="activeTab === 'queue'" class="queue-section">
          <div v-if="!player.queue.length" class="empty">
            <div class="empty-icon">📋</div>
            <p class="empty-title">Очередь пуста</p>
            <p class="empty-hint">Начни воспроизведение</p>
          </div>
          <div v-else class="queue-list">
            <div v-if="player.currentTrack" class="queue-now-playing">
              <span class="queue-label">Сейчас играет</span>
              <TrackItem 
                :track="player.currentTrack"
                :isPlaying="player.isPlaying"
                compact
              />
            </div>
            <div v-if="upcomingTracks.length" class="queue-upcoming">
              <span class="queue-label">Далее</span>
              <TrackItem 
                v-for="(track, idx) in upcomingTracks" 
                :key="`queue-${idx}-${track.id}`"
                :track="track"
                compact
                @click="player.playFromQueue(idx)"
              />
            </div>
          </div>
        </div>

        <!-- History tab -->
        <div v-if="activeTab === 'history'" class="history-section">
          <div v-if="library.history.length === 0" class="empty">
            <div class="empty-icon">🕐</div>
            <p class="empty-title">История пуста</p>
            <p class="empty-hint">Здесь появятся прослушанные треки</p>
          </div>
          <div v-else class="history-list">
            <TrackItem 
              v-for="track in library.history" 
              :key="`history-${track.id}`"
              :track="track"
              :isPlaying="player.currentTrack?.id === track.id && player.isPlaying"
              @click="playTrack(track)"
              @menu="showTrackMenu(track)"
              showLastPlayed
            />
          </div>
        </div>

        <!-- Liked tab -->
        <div v-if="activeTab === 'liked'" class="liked-section">
          <div class="liked-header">
            <div class="liked-cover">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
              </svg>
            </div>
            <div class="liked-meta">
              <h2>Любимое</h2>
              <p>{{ library.likedTracks.length }} треков</p>
            </div>
            <button v-if="library.likedTracks.length > 0" class="play-all-btn" @click="playLikedTracks">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </button>
          </div>
          <div v-if="library.likedTracks.length === 0" class="empty">
            <div class="empty-icon">💚</div>
            <p class="empty-title">Нет любимых треков</p>
            <p class="empty-hint">Нажмите ❤️ на треке, чтобы добавить</p>
          </div>
          <div v-else class="liked-list">
            <TrackItem 
              v-for="track in library.likedTracks" 
              :key="`liked-${track.id}`"
              :track="track"
              :isPlaying="player.currentTrack?.id === track.id && player.isPlaying"
              :isLiked="true"
              @click="playTrack(track)"
              @menu="showTrackMenu(track)"
              @like="toggleLike(track.id)"
            />
          </div>
        </div>

        <!-- Explore / Global Library -->
        <div v-if="activeTab === 'explore'" class="explore-section">
          <GlobalLibrary @play="playTrack" />
        </div>
      </div>

      <!-- Playlist view -->
      <div v-if="currentView === 'playlist'" class="playlist-view">
        <div class="playlist-header-section">
          <!-- Album cover or track collage -->
          <div class="playlist-cover" :class="{ 'has-cover': currentPlaylist?.cover_url || playlistCollageCovers.length > 0 }">
            <!-- Single album cover -->
            <img v-if="currentPlaylist?.cover_url" :src="currentPlaylist.cover_url" alt="" class="cover-image" />
            <!-- 4-track collage for regular playlists -->
            <div v-else-if="playlistCollageCovers.length > 0" class="cover-collage">
              <img v-for="(cover, i) in playlistCollageCovers" :key="i" :src="cover" alt="" class="collage-img" />
            </div>
            <!-- Fallback icon -->
            <svg v-else width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
            </svg>
          </div>
          <div class="playlist-meta">
            <span v-if="currentPlaylist?.album_artist" class="playlist-artist">{{ currentPlaylist.album_artist }}</span>
            <h2>{{ currentPlaylist?.name }}</h2>
            <p>{{ currentPlaylist?.track_count }} треков • {{ formatDuration(currentPlaylist?.total_duration) }}</p>
          </div>
          <button class="download-playlist-btn" @click="downloadPlaylist" title="Скачать все треки">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
            </svg>
          </button>
          <button class="play-all-btn" @click="playPlaylist">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </button>
        </div>
        <TrackItem 
          v-for="track in currentPlaylist?.tracks" 
          :key="track.id"
          :track="track"
          :isPlaying="player.currentTrack?.id === track.id && player.isPlaying"
          @click="playTrack(track, currentPlaylist?.tracks)"
          @menu="showTrackMenu(track)"
        />
      </div>

      <!-- Artist view -->
      <div v-if="currentView === 'artist'" class="artist-view">
        <div v-if="library.artistLoading" class="loading-view">
          <div class="loading-spinner"></div>
          <span>Загрузка...</span>
        </div>
        <ArtistCard 
          v-else-if="library.currentArtist"
          :artist="library.currentArtist"
          :currentTrackId="player.currentTrack?.id"
          :isPlaying="player.isPlaying"
          @play="playTrack"
          @menu="showTrackMenu"
          @like="toggleLike"
          @openAlbum="openPlaylist"
          @openPlaylist="openPlaylist"
        />
        <div v-else class="empty">
          <div class="empty-icon">👤</div>
          <p class="empty-title">Артист не найден</p>
        </div>
      </div>

      <!-- Expanded Section View (fullscreen vertical list) -->
      <Transition name="slide-up">
        <div v-if="expandedSection" class="expanded-section">
          <div class="expanded-header">
            <button @click="expandedSection = null" class="icon-btn">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
              </svg>
            </button>
            <h2 class="expanded-title">
              {{ expandedSection === 'albums' ? 'Альбомы' : 
                 expandedSection === 'sources' ? 'Источники' : 'Мои плейлисты' }}
            </h2>
            <button v-if="expandedSection === 'playlists'" @click="createPlaylist" class="icon-btn">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
              </svg>
            </button>
            <div v-else class="spacer"></div>
          </div>
          
          <div class="expanded-grid">
            <template v-if="expandedSection === 'albums'">
              <PlaylistItem
                v-for="playlist in albumPlaylists"
                :key="playlist.id"
                :playlist="playlist"
                @click="openPlaylist(playlist); expandedSection = null"
              />
            </template>
            <template v-else-if="expandedSection === 'sources'">
              <PlaylistItem
                v-for="playlist in sourcePlaylists"
                :key="playlist.id"
                :playlist="playlist"
                @click="openPlaylist(playlist); expandedSection = null"
              />
            </template>
            <template v-else-if="expandedSection === 'playlists'">
              <PlaylistItem
                v-for="playlist in userPlaylists"
                :key="playlist.id"
                :playlist="playlist"
                @click="openPlaylist(playlist); expandedSection = null"
              />
              <div v-if="userPlaylists.length === 0" class="empty-section">
                <span class="empty-icon">📁</span>
                <p>Нет плейлистов</p>
                <button @click="createPlaylist" class="create-btn">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                  </svg>
                  Создать
                </button>
              </div>
            </template>
          </div>
        </div>
      </Transition>
    </main>

    <!-- Mini Player (above tab bar in flex layout) - mobile only -->
    <MiniPlayer 
      v-if="player.currentTrack && currentView === 'library' && !isDesktop"
      :track="player.currentTrack"
      :isPlaying="player.isPlaying"
      :loading="player.loading"
      :progress="player.progress"
      :duration="player.duration"
      :buffered="player.buffered"
      @toggle="player.toggle()"
      @next="player.next()"
      @expand="showFullPlayer = true"
    />

    <!-- Bottom Tab Bar (One UI style) - mobile only -->
    <nav v-if="currentView === 'library' && !expandedSection && !isDesktop" class="tab-bar">
      <button 
        :class="['tab-item', { active: activeTab === 'home' }]"
        @click="switchTab('home', () => library.fetchHistory())"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
        </svg>
      </button>
      <button 
        :class="['tab-item', { active: activeTab === 'tracks' }]"
        @click="switchTab('tracks')"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
        </svg>
      </button>
      <button 
        :class="['tab-item', { active: activeTab === 'playlists' }]"
        @click="switchTab('playlists')"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
        </svg>
      </button>
      <button 
        :class="['tab-item', { active: activeTab === 'artists' }]"
        @click="switchTab('artists', () => library.fetchArtists())"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>
      </button>
      <button 
        :class="['tab-item', { active: activeTab === 'explore' }]"
        @click="switchTab('explore', () => library.fetchGlobalStats())"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
        </svg>
      </button>
    </nav>

    <!-- Full Player Modal with swipe -->
    <Transition name="slide-up">
      <FullPlayer 
        v-if="showFullPlayer"
        :track="player.currentTrack"
        :isPlaying="player.isPlaying"
        :loading="player.loading"
        :progress="player.progress"
        :duration="player.duration"
        :buffered="player.buffered"
        :volume="player.volume"
        :isMuted="player.isMuted"
        :shuffle="player.shuffle"
        :repeat="player.repeat"
        :queue="player.queue"
        :queueIndex="player.queueIndex"
        :isLiked="player.currentTrack ? library.isTrackLiked(player.currentTrack.id) : false"
        @close="showFullPlayer = false"
        @toggle="player.toggle()"
        @next="player.next()"
        @prev="player.prev()"
        @seek="player.seek($event)"
        @setVolume="player.setVolume($event)"
        @toggleMute="player.toggleMute()"
        @toggleShuffle="player.toggleShuffle()"
        @toggleRepeat="player.toggleRepeat()"
        @removeFromQueue="player.removeFromQueue($event)"
        @moveInQueue="(from, to) => player.moveInQueue(from, to)"
        @playFromQueue="player.playFromQueue($event)"
        @menu="showTrackMenu(player.currentTrack)"
        @like="toggleLike(player.currentTrack?.id)"
      />
    </Transition>

    <!-- Track Context Menu -->
    <TrackMenu
      :show="showTrackMenuModal"
      :track="selectedTrack"
      :currentUserId="currentUserId"
      @close="showTrackMenuModal = false"
      @addToPlaylist="handleAddToPlaylist"
      @edit="handleEditTrack"
      @delete="handleDeleteTrack"
      @removeFromLibrary="handleRemoveFromLibrary"
      @download="handleDownloadTrack"
      @goToArtist="handleGoToArtist"
      @goToAlbum="handleGoToAlbum"
    />

    <!-- Playlist Context Menu -->
    <PlaylistMenu
      :show="showPlaylistMenuModal"
      :playlist="selectedPlaylist"
      @close="showPlaylistMenuModal = false"
      @open="handlePlaylistMenuOpen"
      @playAll="handlePlaylistPlayAll"
      @shuffle="handlePlaylistShuffle"
      @addToQueue="handlePlaylistAddToQueue"
      @rename="handlePlaylistRename"
      @delete="handlePlaylistDelete"
    />

    <!-- Edit Track Modal -->
    <EditTrackModal
      :show="showEditModal"
      :track="editingTrack"
      @close="showEditModal = false"
      @saved="library.fetchTracks()"
    />

    <!-- Delete Confirmation -->
    <ConfirmDialog
      :show="showConfirmDelete"
      type="danger"
      title="Удалить трек?"
      :message="`Трек «${deletingTrack?.title || 'Без названия'}» будет удалён.`"
      confirmText="Удалить"
      @confirm="confirmDeleteTrack"
      @cancel="showConfirmDelete = false"
    />

    <!-- Playlist Picker -->
    <PlaylistPicker
      :show="showPlaylistPicker"
      :track="trackForPlaylist"
      @close="showPlaylistPicker = false"
      @createNew="showPlaylistPicker = false; createPlaylist()"
    />

    <!-- Create Playlist Modal -->
    <Transition name="fade">
      <div v-if="showCreatePlaylist" class="modal-overlay" @click.self="showCreatePlaylist = false">
        <div class="modal">
          <h3>Новый плейлист</h3>
          <input 
            v-model="newPlaylistName"
            type="text"
            placeholder="Название плейлиста"
            class="modal-input"
          />
          <div class="modal-actions">
            <button @click="showCreatePlaylist = false" class="btn-secondary">Отмена</button>
            <button @click="submitCreatePlaylist" class="btn-primary">Создать</button>
          </div>
        </div>
      </div>
    </Transition>
    </div><!-- End main-content-wrapper -->

    <!-- Right Sidebar - Now Playing (Desktop only) -->
    <NowPlayingSidebar
      v-if="isDesktop && player.currentTrack"
      :track="player.currentTrack"
      :isPlaying="player.isPlaying"
      :isLiked="library.isTrackLiked(player.currentTrack?.id)"
      @goToArtist="handleGoToArtist"
      @goToAlbum="handleGoToAlbum"
      @goToUser="handleGoToUser"
      @like="toggleLike(player.currentTrack?.id)"
      @menu="showTrackMenu(player.currentTrack)"
    />

    <!-- Desktop Bottom Player (Car Stereo Style) -->
    <DesktopPlayer 
      v-if="isDesktop && player.currentTrack"
      :track="player.currentTrack"
      :isPlaying="player.isPlaying"
      :loading="player.loading"
      :progress="player.progress"
      :duration="player.duration"
      :buffered="player.buffered"
      :volume="player.volume"
      :isMuted="player.isMuted"
      :shuffle="player.shuffle"
      :repeat="player.repeat"
      :isLiked="library.isTrackLiked(player.currentTrack.id)"
      @toggle="player.toggle()"
      @prev="player.prev()"
      @next="player.next()"
      @expand="showFullPlayer = true"
      @toggleShuffle="player.toggleShuffle()"
      @toggleRepeat="player.toggleRepeat()"
      @toggleMute="player.toggleMute()"
      @setVolume="player.setVolume($event)"
      @seek="player.seek($event)"
      @menu="showTrackMenu(player.currentTrack)"
      @like="toggleLike(player.currentTrack?.id)"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject, nextTick, watch } from 'vue'
import { usePlayerStore } from './stores/player'
import { useLibraryStore } from './stores/library'
import { playerApi, playlistsApi, authStorage } from './api/client'
// View components
import HomeFeed from './components/HomeFeed.vue'
import SearchResults from './components/SearchResults.vue'
import TrackListView from './components/TrackListView.vue'
import PlaylistsView from './components/PlaylistsView.vue'
import ArtistsView from './components/ArtistsView.vue'
import AppHeader from './components/AppHeader.vue'
// UI components
import TrackItem from './components/TrackItem.vue'
import TrackSkeleton from './components/TrackSkeleton.vue'
import PlaylistItem from './components/PlaylistItem.vue'
import MiniPlayer from './components/MiniPlayer.vue'
import FullPlayer from './components/FullPlayer.vue'
import TrackMenu from './components/TrackMenu.vue'
import PlaylistMenu from './components/PlaylistMenu.vue'
import EditTrackModal from './components/EditTrackModal.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'
import PlaylistPicker from './components/PlaylistPicker.vue'
import GlobalLibrary from './components/GlobalLibrary.vue'
import Sidebar from './components/Sidebar.vue'
import DesktopPlayer from './components/DesktopPlayer.vue'
import NowPlayingSidebar from './components/NowPlayingSidebar.vue'
import ArtistCard from './components/ArtistCard.vue'
import Toast from './components/Toast.vue'
import LoginPage from './components/LoginPage.vue'
import { formatDurationLong } from './utils/formatters'
import { getGenreStyle, getArtistInitials, getArtistAvatarStyle } from './utils/styles'
import { useModals } from './composables/useModals'
import { usePullToRefresh } from './composables/usePullToRefresh'
import { useAuth } from './composables/useAuth'

const telegram = inject('telegram')

// Stores
const player = usePlayerStore()
const library = useLibraryStore()

// ============== Composables ==============
// Authentication
const {
  isAuthenticated,
  currentUser,
  authChecking,
  userDisplayName,
  currentUserId,
  checkAuth,
  handleLogout,
} = useAuth(telegram)

// Handle login from LoginPage (needs access to stores)
const handleLogin = async (user) => {
  isAuthenticated.value = true
  currentUser.value = user
  
  // Initialize the library after successful login
  await library.init()
  
  // Restore player state if available
  if (player.hasSavedState()) {
    await player.restoreState()
  }
}

// Listen for auth:logout events (from API interceptor on 401)
const onAuthLogout = () => {
  handleLogout()
}

// Current tab display name for header
const currentTabName = computed(() => {
  const tabNames = {
    'home': 'Главная',
    'tracks': 'Треки',
    'playlists': 'Плейлисты',
    'artists': 'Артисты',
    'genres': 'Жанры',
    'explore': 'Обзор',
    'queue': 'Очередь',
    'history': 'Недавнее',
    'liked': 'Любимое'
  }
  return tabNames[activeTab.value] || 'Музыка'
})

// Modals - all modal/dialog states
const {
  showTrackMenuModal,
  selectedTrack,
  showTrackMenu,
  closeTrackMenu,
  showPlaylistMenuModal,
  selectedPlaylist,
  showPlaylistMenu,
  closePlaylistMenu,
  showEditModal,
  editingTrack,
  openEditModal,
  closeEditModal,
  showConfirmDelete,
  deletingTrack,
  confirmDelete,
  closeConfirmDelete,
  showPlaylistPicker,
  trackForPlaylist,
  openPlaylistPicker,
  closePlaylistPicker,
  showCreatePlaylist,
  newPlaylistName,
  openCreatePlaylist,
  closeCreatePlaylist,
  showFullPlayer,
  openFullPlayer,
  closeFullPlayer,
  toast,
  showToast,
} = useModals(telegram)

// Pull-to-refresh state only (handlers defined locally for App-specific logic)
const {
  pullStartY,
  pullDistance,
  isPulling,
  contentRef,
} = usePullToRefresh(library, telegram)

// Refs
const searchInput = ref(null)

// Responsive detection
const isDesktop = ref(window.innerWidth >= 1024)
const updateDesktopState = () => {
  isDesktop.value = window.innerWidth >= 1024
}

// State
const currentView = ref('library')
const activeTab = ref('home')
const showSearch = ref(false)
const searchQuery = ref('')
const searchTags = ref([])
const searchScope = ref('library')  // 'library' or 'global' - search scope
// showFullPlayer, showCreatePlaylist, newPlaylistName from useModals
const currentPlaylist = ref(null)
const activeFilter = ref(null) // Active artist/genre filter
const filterScope = ref('library') // 'library' or 'global' - which library we're filtering

// Fullscreen section view
const expandedSection = ref(null) // 'albums', 'sources', 'playlists' or null

// Navigation history stack
const navigationStack = ref([])

// Scroll positions cache (persists during session)
const scrollPositions = ref({
  artistsScroll: 0,
  albumsScroll: 0,
  sourcesScroll: 0,
  playlistsScroll: 0,
  genresScroll: 0,
})

// Track menu, Playlist menu, Edit modal, Confirm dialog, Playlist picker,
// Pull-to-refresh state - all from composables (useModals, usePullToRefresh)

// Computed
const headerTitle = computed(() => {
  switch (currentView.value) {
    case 'library': return 'TG Player'
    case 'playlist': return currentPlaylist.value?.name || 'Плейлист'
    case 'artist': return library.currentArtist?.name || 'Артист'
    default: return 'TG Player'
  }
})

const upcomingTracks = computed(() => {
  if (!player.queue.length || player.queueIndex < 0) return []
  return player.queue.slice(player.queueIndex + 1, player.queueIndex + 11)
})

const displayedArtists = computed(() => {
  return library.artistScope === 'global' ? library.globalArtists : library.artists
})

const displayedTracks = computed(() => {
  return filterScope.value === 'global' ? library.globalTracks : library.tracks
})

// Search results - filtered by current search query
const searchQueryLower = computed(() => {
  const fullQuery = [...searchTags.value, searchQuery.value].filter(Boolean).join(' ')
  return fullQuery.toLowerCase().trim()
})

const searchResultArtists = computed(() => {
  if (!searchQueryLower.value) return []
  const artists = searchScope.value === 'global' ? library.globalArtists : library.artists
  return artists.filter(a => 
    a.artist?.toLowerCase().includes(searchQueryLower.value)
  ).slice(0, 5)
})

const searchResultAlbums = computed(() => {
  if (!searchQueryLower.value) return []
  return library.playlists.filter(p => 
    p.is_auto_album && 
    p.track_count > 0 &&  // Hide empty albums
    (p.name?.toLowerCase().includes(searchQueryLower.value) ||
     p.album_artist?.toLowerCase().includes(searchQueryLower.value))
  ).slice(0, 5)
})

const searchResultPlaylists = computed(() => {
  if (!searchQueryLower.value) return []
  return library.playlists.filter(p => 
    !p.is_auto_album && 
    !p.is_auto_source &&
    p.name?.toLowerCase().includes(searchQueryLower.value)
  ).slice(0, 5)
})

const hasSearchResults = computed(() => {
  return searchResultArtists.value.length > 0 ||
         searchResultAlbums.value.length > 0 ||
         searchResultPlaylists.value.length > 0 ||
         displayedTracks.value.length > 0
})

// Playlist categories
const lastPlaylist = computed(() => {
  // Return most recently updated/created playlist
  if (library.playlists.length === 0) return null
  return library.playlists[0]
})

const sourcePlaylists = computed(() => {
  // Playlists from forwarded sources (bots, channels, users)
  return library.playlists.filter(p => p.is_auto_source)
})

const albumPlaylists = computed(() => {
  // Auto-generated album playlists (exclude empty ones)
  return library.playlists.filter(p => p.is_auto_album && !p.is_auto_source && p.track_count > 0)
})

const userPlaylists = computed(() => {
  // User-created playlists (not auto-generated)
  return library.playlists.filter(p => !p.is_auto_album && !p.is_auto_source)
})

// Get up to 4 unique cover images for playlist collage
const playlistCollageCovers = computed(() => {
  if (!currentPlaylist.value?.tracks) return []
  
  const covers = []
  const seen = new Set()
  
  for (const track of currentPlaylist.value.tracks) {
    if (track.cover_url && !seen.has(track.cover_url)) {
      seen.add(track.cover_url)
      covers.push(track.cover_url)
      if (covers.length >= 4) break
    }
  }
  
  // Only return if we have at least 1 cover
  return covers.length > 0 ? covers : []
})

// Methods

// Handle infinite scroll for tracks
const handleContentScroll = () => {
  if (!contentRef.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = contentRef.value
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight
  
  // Load more when user is within 300px from bottom
  if (distanceFromBottom < 300 && activeTab.value === 'tracks') {
    if (filterScope.value === 'library') {
      library.loadMore()
    } else if (filterScope.value === 'global') {
      library.loadMoreGlobal()
    }
  }
}

const scrollToTop = () => {
  if (contentRef.value) {
    contentRef.value.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const switchTab = (tab, callback = null) => {
  if (activeTab.value === tab) {
    // Уже на этом табе - скроллим вверх
    scrollToTop()
  } else {
    // Переключаем таб
    activeTab.value = tab
    if (callback) callback()
  }
}

// Handle sidebar navigation
const handleSidebarNavigate = (tab) => {
  currentView.value = 'library'
  currentPlaylist.value = null
  expandedSection.value = null
  
  // Map sidebar tabs to actual tabs with callbacks
  const tabCallbacks = {
    'home': () => library.fetchHistory(),
    'tracks': null,
    'liked': null,
    'history': null,
    'artists': () => library.fetchArtists(),
    'explore': () => library.fetchGlobalStats(),
    'global': () => library.fetchGlobalStats(),
    'playlists': null,
    'albums': null,
    'search': () => { showSearch.value = true; nextTick(() => searchInput.value?.focus()) }
  }
  
  if (tab === 'search') {
    showSearch.value = true
    activeTab.value = 'search'
    nextTick(() => searchInput.value?.focus())
  } else if (tab === 'global') {
    // Navigate to global library
    activeTab.value = 'global'
    library.fetchGlobalStats()
  } else if (tab === 'albums') {
    // Open albums section expanded
    activeTab.value = 'albums'
  } else if (tab === 'playlists') {
    // Open playlists tab
    activeTab.value = 'playlists'
  } else {
    switchTab(tab, tabCallbacks[tab])
  }
}

const goBack = () => {
  // If expanded section is open, close it first
  if (expandedSection.value) {
    expandedSection.value = null
    return
  }
  
  // Pop from navigation stack
  if (navigationStack.value.length > 0) {
    const prevState = navigationStack.value.pop()
    currentView.value = prevState.view
    currentPlaylist.value = prevState.playlist
    
    // Restore artist if we're going back to artist view
    if (prevState.view === 'artist' && prevState.artist) {
      library.setCurrentArtist(prevState.artist)
    } else if (prevState.view === 'library') {
      library.clearCurrentArtist()
    }
    
    // Restore scroll positions after DOM update
    nextTick(() => {
      restoreScrollPositions()
    })
  } else {
    // No history, go to library
    currentView.value = 'library'
    currentPlaylist.value = null
    library.clearCurrentArtist()
  }
}

// Save current scroll positions of horizontal scrollers
const saveScrollPositions = () => {
  const selectors = {
    artistsScroll: '.artists-scroll',
    albumsScroll: '.albums-scroll', 
    sourcesScroll: '.sources-scroll',
    playlistsScroll: '.playlists-scroll',
    genresScroll: '.genres-scroll',
  }
  
  for (const [key, selector] of Object.entries(selectors)) {
    const el = document.querySelector(selector)
    if (el) {
      scrollPositions.value[key] = el.scrollLeft
    }
  }
}

// Restore scroll positions of horizontal scrollers
const restoreScrollPositions = () => {
  const selectors = {
    artistsScroll: '.artists-scroll',
    albumsScroll: '.albums-scroll',
    sourcesScroll: '.sources-scroll', 
    playlistsScroll: '.playlists-scroll',
    genresScroll: '.genres-scroll',
  }
  
  for (const [key, selector] of Object.entries(selectors)) {
    const el = document.querySelector(selector)
    if (el && scrollPositions.value[key]) {
      el.scrollLeft = scrollPositions.value[key]
    }
  }
}

// Push current state to navigation stack before navigating
const pushNavigation = () => {
  saveScrollPositions()
  navigationStack.value.push({
    view: currentView.value,
    playlist: currentPlaylist.value,
    artist: library.currentArtist,  // Save artist state for back navigation
  })
}

const openSection = (section) => {
  expandedSection.value = section
}

const playTrack = async (track, queue = null) => {
  await player.play(track, queue || library.tracks)
}

const toggleLike = async (trackId) => {
  const isLiked = await library.toggleLike(trackId)
  telegram?.HapticFeedback?.impactOccurred?.('light')
}

const playPlaylist = async () => {
  if (currentPlaylist.value?.tracks?.length) {
    await player.play(currentPlaylist.value.tracks[0], currentPlaylist.value.tracks)
  }
}

const downloadPlaylist = async () => {
  if (!currentPlaylist.value?.tracks?.length) {
    toast.value?.show('Плейлист пуст', 'error')
    return
  }
  
  try {
    const trackIds = currentPlaylist.value.tracks.map(t => t.id)
    const result = await playerApi.downloadPlaylist(trackIds, currentPlaylist.value.name)
    
    telegram?.HapticFeedback?.notificationOccurred?.('success')
    toast.value?.show(`Отправлено ${result.data.sent} треков в чат`, 'success')
  } catch (error) {
    console.error('Failed to download playlist:', error)
    telegram?.HapticFeedback?.notificationOccurred?.('error')
    toast.value?.show('Не удалось отправить плейлист', 'error')
  }
}

const playLikedTracks = async () => {
  if (library.likedTracks.length) {
    await player.play(library.likedTracks[0], library.likedTracks)
  }
}

// Playlist menu
const showPlaylistMenu = (playlist) => {
  selectedPlaylist.value = playlist
  showPlaylistMenuModal.value = true
}

// Playlist menu handlers
const handlePlaylistMenuOpen = (playlist) => {
  openPlaylist(playlist)
}

const handlePlaylistPlayAll = async (playlist) => {
  try {
    const response = await playlistsApi.getOne(playlist.id)
    const tracks = response.data.tracks || []
    if (tracks.length) {
      await player.play(tracks[0], tracks)
    }
  } catch (error) {
    console.error('Failed to play playlist:', error)
    toast.value?.show('Не удалось воспроизвести плейлист', 'error')
  }
}

const handlePlaylistShuffle = async (playlist) => {
  try {
    const response = await playlistsApi.getOne(playlist.id)
    const tracks = response.data.tracks || []
    if (tracks.length) {
      const shuffled = [...tracks].sort(() => Math.random() - 0.5)
      await player.play(shuffled[0], shuffled)
    }
  } catch (error) {
    console.error('Failed to shuffle playlist:', error)
    toast.value?.show('Не удалось воспроизвести плейлист', 'error')
  }
}

const handlePlaylistAddToQueue = async (playlist) => {
  try {
    const response = await playlistsApi.getOne(playlist.id)
    const tracks = response.data.tracks || []
    tracks.forEach(track => player.addToQueue(track))
    toast.value?.show(`Добавлено ${tracks.length} треков в очередь`, 'success')
  } catch (error) {
    console.error('Failed to add playlist to queue:', error)
    toast.value?.show('Не удалось добавить в очередь', 'error')
  }
}

const handlePlaylistRename = async (playlist) => {
  const newName = prompt('Новое название плейлиста:', playlist.name)
  if (newName && newName.trim() && newName !== playlist.name) {
    try {
      await playlistsApi.update(playlist.id, { name: newName.trim() })
      await library.fetchPlaylists()
      toast.value?.show('Плейлист переименован', 'success')
    } catch (error) {
      console.error('Failed to rename playlist:', error)
      toast.value?.show('Не удалось переименовать плейлист', 'error')
    }
  }
}

const handlePlaylistDelete = async (playlist) => {
  if (confirm(`Удалить плейлист «${playlist.name}»?`)) {
    try {
      await playlistsApi.delete(playlist.id)
      await library.fetchPlaylists()
      if (currentPlaylist.value?.id === playlist.id) {
        currentPlaylist.value = null
        currentView.value = 'library'
      }
      toast.value?.show('Плейлист удалён', 'success')
    } catch (error) {
      console.error('Failed to delete playlist:', error)
      toast.value?.show('Не удалось удалить плейлист', 'error')
    }
  }
}

// Track menu handlers
const handleAddToPlaylist = (track) => {
  trackForPlaylist.value = track
  showPlaylistPicker.value = true
}

const handleEditTrack = (track) => {
  editingTrack.value = track
  showEditModal.value = true
}

const handleDeleteTrack = (track) => {
  deletingTrack.value = track
  showConfirmDelete.value = true
}

const handleRemoveFromLibrary = async (track) => {
  try {
    const success = await library.removeFromLibrary(track.id)
    if (success) {
      telegram?.HapticFeedback?.notificationOccurred?.('success')
      toast.value?.show('Трек убран из библиотеки', 'success')
    } else {
      telegram?.HapticFeedback?.notificationOccurred?.('error')
      toast.value?.show('Не удалось убрать трек', 'error')
    }
  } catch (error) {
    console.error('Failed to remove from library:', error)
    telegram?.HapticFeedback?.notificationOccurred?.('error')
    toast.value?.show('Не удалось убрать трек', 'error')
  }
}

const handleDownloadTrack = async (track) => {
  try {
    await playerApi.download(track.id)
    telegram?.HapticFeedback?.notificationOccurred?.('success')
    toast.value?.show('Трек отправлен в чат', 'success')
  } catch (error) {
    console.error('Failed to download track:', error)
    telegram?.HapticFeedback?.notificationOccurred?.('error')
    toast.value?.show('Не удалось отправить трек', 'error')
  }
}

// Navigate to artist card from track menu
const handleGoToArtist = async (artistName) => {
  if (!artistName) return
  showFullPlayer.value = false  // Close full player if open
  await filterByArtist(artistName)
}

// Navigate to user profile from NowPlayingSidebar
const handleGoToUser = async (user) => {
  if (!user?.id) return
  showFullPlayer.value = false  // Close full player if open
  
  // Switch to explore tab and show user's tracks
  activeTab.value = 'explore'
  currentView.value = 'library'
  
  // Fetch user's tracks
  await library.fetchUserTracks(user.id)
}

// Navigate to album from track menu
const handleGoToAlbum = async (albumName, artistName) => {
  if (!albumName) return
  showFullPlayer.value = false  // Close full player if open
  
  // Normalize album name for comparison (case-insensitive, trimmed)
  const normalizedAlbumName = albumName.toLowerCase().trim()
  
  // Find album playlist by name (case-insensitive) and optionally by artist
  const albumPlaylist = library.playlists.find(p => {
    if (!p.is_auto_album) return false
    
    // Case-insensitive name comparison
    const playlistName = (p.name || '').toLowerCase().trim()
    if (playlistName !== normalizedAlbumName) return false
    
    // If we have an artist, check if it matches (also case-insensitive)
    if (artistName && p.album_artist) {
      const normalizedArtist = artistName.toLowerCase()
      const playlistArtist = p.album_artist.toLowerCase()
      return playlistArtist.includes(normalizedArtist) || normalizedArtist.includes(playlistArtist)
    }
    
    return true
  })
  
  if (albumPlaylist) {
    await openPlaylist(albumPlaylist)
  } else {
    toast.value?.show('Альбом не найден в библиотеке', 'warning')
  }
}

const confirmDeleteTrack = async () => {
  if (deletingTrack.value) {
    await library.deleteTrack(deletingTrack.value.id)
    telegram?.HapticFeedback?.notificationOccurred?.('success')
  }
  showConfirmDelete.value = false
  deletingTrack.value = null
}

const openPlaylist = async (playlist) => {
  // Check if this is a "virtual" album (no playlist created yet, id=-1)
  if (playlist.id === -1) {
    // Filter by album name instead
    activeFilter.value = `Альбом: ${playlist.name}`
    activeTab.value = 'tracks'
    filterScope.value = 'library'
    library.fetchTracks({ album: playlist.name })
    currentView.value = 'main'
    return
  }
  pushNavigation()
  currentPlaylist.value = await library.fetchPlaylist(playlist.id)
  currentView.value = 'playlist'
}

const createPlaylist = () => {
  newPlaylistName.value = ''
  showCreatePlaylist.value = true
}

const submitCreatePlaylist = async () => {
  if (!newPlaylistName.value.trim()) return
  await library.createPlaylist(newPlaylistName.value)
  showCreatePlaylist.value = false
}

const filterByArtist = async (artist, scope = 'library') => {
  // Open artist card view instead of filtering
  pushNavigation()
  await library.fetchArtistDetail(artist, scope)
  currentView.value = 'artist'
}

const filterByGenre = (genre) => {
  activeFilter.value = `Жанр: ${genre}`
  activeTab.value = 'tracks'
  library.fetchTracks({ genre })
}

// Play genre with shuffle enabled
const playGenreShuffle = async (genre) => {
  // Fetch tracks by genre
  const tracks = await library.fetchTracksByGenre(genre)
  if (tracks && tracks.length > 0) {
    // Shuffle the tracks
    const shuffled = [...tracks].sort(() => Math.random() - 0.5)
    player.shuffle = true
    await player.play(shuffled[0], shuffled)
  }
}

// Get artist avatar style (uses shared utility)
const getArtistAvatarStyleLocal = (name) => {
  return getArtistAvatarStyle(name, library.artistImages[name])
}

// Get track cover style for feed cards
const getTrackCoverStyle = (track) => {
  if (track.cover_url) return {}
  
  const str = (track.title || '') + (track.artist || '')
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue1 = Math.abs(hash % 360)
  const hue2 = (hue1 + 45) % 360
  
  return {
    background: `linear-gradient(135deg, hsl(${hue1}, 55%, 40%) 0%, hsl(${hue2}, 45%, 30%) 100%)`
  }
}

// Get track initials
const getTrackInitials = (track) => {
  const title = track.title || 'M'
  const words = title.split(' ').filter(w => w.length > 0)
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }
  return title.substring(0, 2).toUpperCase()
}

const clearFilter = () => {
  activeFilter.value = null
  filterScope.value = 'library'
  searchQuery.value = ''
  library.fetchTracks()
}

// formatDuration imported from @/utils/formatters as formatDurationLong
const formatDuration = formatDurationLong

let searchTimeout = null
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    const fullQuery = [...searchTags.value, searchQuery.value].filter(Boolean).join(' ')
    
    if (fullQuery) {
      // Switch to search tab when searching
      activeTab.value = 'search'
      activeFilter.value = searchScope.value === 'global' ? `🌍 ${fullQuery}` : fullQuery
    } else {
      // If search cleared, go back to home
      if (activeTab.value === 'search') {
        activeTab.value = 'home'
      }
      activeFilter.value = null
    }
    
    if (searchScope.value === 'global') {
      // Global search
      filterScope.value = 'global'
      library.fetchGlobalTracks({ search: fullQuery })
      // Also fetch global artists if not loaded
      if (library.globalArtists.length === 0) {
        library.fetchArtists('global')
      }
    } else {
      // Library search
      filterScope.value = 'library'
      library.fetchTracks({ search: fullQuery })
      // Also fetch library artists if not loaded
      if (library.artists.length === 0) {
        library.fetchArtists('library')
      }
    }
  }, 300)
}

const toggleSearchScope = () => {
  searchScope.value = searchScope.value === 'library' ? 'global' : 'library'
  // Re-trigger search with new scope
  if (searchQuery.value || searchTags.value.length > 0) {
    debouncedSearch()
  }
}

// Search tag handling
const addTag = () => {
  const query = searchQuery.value.trim()
  if (query) {
    searchTags.value.push(query)
    searchQuery.value = ''
    debouncedSearch()
  }
}

const removeTag = (index) => {
  searchTags.value.splice(index, 1)
  debouncedSearch()
}

const handleBackspace = () => {
  if (!searchQuery.value && searchTags.value.length > 0) {
    removeTag(searchTags.value.length - 1)
  }
}

const focusInput = () => {
  searchInput.value?.focus()
}

// Search open/close with animation
const toggleSearch = async () => {
  if (showSearch.value) {
    closeSearch()
  } else {
    showSearch.value = true
    await nextTick()
    searchInput.value?.focus()
  }
}

const closeSearch = () => {
  showSearch.value = false
  if (searchQuery.value || searchTags.value.length > 0 || searchScope.value === 'global') {
    searchQuery.value = ''
    searchTags.value = []
    searchScope.value = 'library'
    activeFilter.value = null
    filterScope.value = 'library'
    library.fetchTracks()  // Reset to full list
  }
}

// Navigate to home tab
const goToHome = () => {
  activeTab.value = 'home'
  library.fetchHistory()
}

// Pull-to-refresh handlers (override composable's with App-specific logic)
const handleTouchStartLocal = (e) => {
  const scrollTop = document.querySelector('.content')?.scrollTop || 0
  if (scrollTop === 0 && currentView.value === 'library') {
    pullStartY.value = e.touches[0].clientY
    isPulling.value = true
  }
}

const handleTouchMoveLocal = (e) => {
  if (!isPulling.value || library.refreshing) return
  
  const currentY = e.touches[0].clientY
  const diff = currentY - pullStartY.value
  
  if (diff > 0) {
    pullDistance.value = Math.min(diff * 0.5, 100)
    if (pullDistance.value > 10) {
      e.preventDefault()
    }
  }
}

const handleTouchEndLocal = async () => {
  if (!isPulling.value) return
  
  if (pullDistance.value > 60 && !library.refreshing) {
    await library.refresh()
    telegram?.HapticFeedback?.impactOccurred?.('light')
  }
  
  pullDistance.value = 0
  isPulling.value = false
  pullStartY.value = 0
}

// Apply Spotify theme on mount
onMounted(async () => {
  document.body.classList.add('spotify-theme')
  
  // Desktop detection
  window.addEventListener('resize', updateDesktopState)
  
  // Check authentication first
  checkAuth()
  
  // Listen for logout events from API
  window.addEventListener('auth:logout', onAuthLogout)
  
  // Only initialize if authenticated
  if (isAuthenticated.value) {
    await library.init()
    
    // Restore player state if available
    if (player.hasSavedState()) {
      await player.restoreState()
    }
  }
  
  // Handle unavailable tracks - show toast with helpful message
  player.setOnTrackUnavailable((track, message, isLargeFile) => {
    if (isLargeFile) {
      const sizeMB = track.file_size ? (track.file_size / 1024 / 1024).toFixed(1) : '20+'
      toast.value?.show(`Файл слишком большой (${sizeMB} MB) для стриминга. Нажмите ⋮ → Скачать`, 'warning', 6000)
    } else {
      toast.value?.show(message || 'Файл недоступен в Telegram', 'error')
    }
  })
})

// Cleanup on unmount
onUnmounted(() => {
  window.removeEventListener('auth:logout', onAuthLogout)
  window.removeEventListener('resize', updateDesktopState)
})
</script>

<style scoped>
/* App styles imported from external files */
@import './styles/index.css';
</style>

