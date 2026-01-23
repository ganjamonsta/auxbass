<template>
  <div class="app spotify-theme">
    <!-- Toast notifications -->
    <Toast ref="toast" />
    
    <!-- One UI Style Header -->
    <header class="oneui-header" v-if="currentView === 'library'">
      <div class="header-top">
        <EnrichmentStatus />
        <button @click="showSearch = !showSearch" class="icon-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
          </svg>
        </button>
      </div>
      <h1>{{ headerTitle }}</h1>
      
      <!-- Search bar -->
      <Transition name="slide-down">
        <div v-if="showSearch" class="search-container">
          <input 
            v-model="searchQuery"
            type="text"
            placeholder="Поиск треков, артистов..."
            class="search-input"
            @input="debouncedSearch"
          />
        </div>
      </Transition>
    </header>

    <!-- Compact Header for other views -->
    <header v-else class="compact-header">
      <button @click="goBack" class="icon-btn">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </button>
      <span class="header-title">{{ headerTitle }}</span>
      <div class="spacer"></div>
    </header>

    <!-- Main content -->
    <main 
      class="content"
      @touchstart="handleTouchStart"
      @touchmove="handleTouchMove"
      @touchend="handleTouchEnd"
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
          <span>{{ activeFilter }}</span>
          <button @click="clearFilter" class="clear-filter-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
            </svg>
          </button>
        </div>

        <!-- Home Feed (Spotify-style) -->
        <div v-if="activeTab === 'home'" class="home-feed">
          <!-- Quick Access Grid -->
          <div class="quick-grid">
            <div 
              class="quick-item" 
              v-if="library.history.length > 0"
              @click="activeTab = 'history'"
            >
              <div class="quick-icon history-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M13 3a9 9 0 00-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0013 21a9 9 0 000-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
                </svg>
              </div>
              <span class="quick-title">Недавнее</span>
            </div>
            <div 
              class="quick-item" 
              v-for="pl in library.playlists.slice(0, 5)" 
              :key="pl.id"
              @click="openPlaylist(pl)"
            >
              <div class="quick-icon playlist-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M4 10h12v2H4zm0-4h12v2H4zm0 8h8v2H4zm10 0v6l5-3z"/>
                </svg>
              </div>
              <span class="quick-title">{{ pl.name }}</span>
            </div>
          </div>

          <!-- Liked Tracks Section -->
          <div v-if="library.likedTracks.length > 0" class="feed-section">
            <h2 class="feed-section-title">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="#1db954" style="margin-right: 8px; vertical-align: -3px;">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
              </svg>
              Любимые
            </h2>
            <div class="horizontal-scroll">
              <div 
                v-for="track in library.likedTracks.slice(0, 10)" 
                :key="track.id"
                class="feed-card"
                @click="playTrack(track)"
              >
                <div class="feed-card-cover" :style="getTrackCoverStyle(track)">
                  <img v-if="track.cover_url" :src="track.cover_url" alt="" />
                  <div v-else class="feed-card-placeholder">{{ getTrackInitials(track) }}</div>
                  <button class="play-overlay" @click.stop="playTrack(track)">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M8 5v14l11-7z"/>
                    </svg>
                  </button>
                  <div class="liked-badge">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                    </svg>
                  </div>
                </div>
                <div class="feed-card-title">{{ track.title || 'Без названия' }}</div>
                <div class="feed-card-subtitle">{{ track.artist || 'Неизвестный' }}</div>
              </div>
            </div>
          </div>

          <!-- Recently Played Section -->
          <div v-if="library.history.length > 0" class="feed-section">
            <h2 class="feed-section-title">Недавно играло</h2>
            <div class="horizontal-scroll">
              <div 
                v-for="track in library.history.slice(0, 10)" 
                :key="track.id"
                class="feed-card"
                @click="playTrack(track)"
              >
                <div class="feed-card-cover" :style="getTrackCoverStyle(track)">
                  <img v-if="track.cover_url" :src="track.cover_url" alt="" />
                  <div v-else class="feed-card-placeholder">{{ getTrackInitials(track) }}</div>
                  <button class="play-overlay" @click.stop="playTrack(track)">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M8 5v14l11-7z"/>
                    </svg>
                  </button>
                </div>
                <div class="feed-card-title">{{ track.title || 'Без названия' }}</div>
                <div class="feed-card-subtitle">{{ track.artist || 'Неизвестный' }}</div>
              </div>
            </div>
          </div>

          <!-- Top Artists Section -->
          <div v-if="library.artists.length > 0" class="feed-section">
            <h2 class="feed-section-title">Твои артисты</h2>
            <div class="horizontal-scroll">
              <div 
                v-for="artist in library.artists.slice(0, 10)" 
                :key="artist.artist"
                class="feed-card artist-card"
                @click="filterByArtist(artist.artist)"
              >
                <div class="feed-card-cover artist-cover" :style="getArtistAvatarStyle(artist.artist)">
                  <img 
                    v-if="library.artistImages[artist.artist]" 
                    :src="library.artistImages[artist.artist]" 
                    alt=""
                  />
                  <span v-else class="artist-initials">{{ getArtistInitials(artist.artist) }}</span>
                </div>
                <div class="feed-card-title">{{ artist.artist }}</div>
                <div class="feed-card-subtitle">{{ artist.count }} треков</div>
              </div>
            </div>
          </div>

          <!-- Playlists Section -->
          <div v-if="library.playlists.length > 0" class="feed-section">
            <h2 class="feed-section-title">Плейлисты</h2>
            <div class="horizontal-scroll">
              <div 
                v-for="pl in library.playlists" 
                :key="pl.id"
                class="feed-card"
                @click="openPlaylist(pl)"
              >
                <div class="feed-card-cover playlist-cover">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M4 10h12v2H4zm0-4h12v2H4zm0 8h8v2H4zm10 0v6l5-3z"/>
                  </svg>
                </div>
                <div class="feed-card-title">{{ pl.name }}</div>
                <div class="feed-card-subtitle">{{ pl.track_count || 0 }} треков</div>
              </div>
              <!-- Add playlist button -->
              <div class="feed-card add-card" @click="createPlaylist">
                <div class="feed-card-cover add-cover">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                  </svg>
                </div>
                <div class="feed-card-title">Создать</div>
                <div class="feed-card-subtitle">плейлист</div>
              </div>
            </div>
          </div>

          <!-- All Tracks Section -->
          <div class="feed-section">
            <h2 class="feed-section-title">Вся музыка</h2>
            <div class="feed-tracks-preview">
              <TrackItem 
                v-for="track in library.tracks.slice(0, 5)" 
                :key="track.id"
                :track="track"
                :isPlaying="player.currentTrack?.id === track.id && player.isPlaying"
                :isLiked="library.isTrackLiked(track.id)"
                @click="playTrack(track)"
                @menu="showTrackMenu(track)"
                @like="toggleLike(track.id)"
              />
              <button v-if="library.tracks.length > 5" class="see-all-btn" @click="activeTab = 'tracks'">
                Смотреть все ({{ library.total }})
              </button>
            </div>
          </div>
        </div>
        
        <!-- Track list -->
        <div v-if="activeTab === 'tracks'" class="track-list">
          <div v-if="library.loading" class="skeleton-list">
            <TrackSkeleton v-for="i in 6" :key="i" />
          </div>
          <div v-else-if="library.tracks.length === 0" class="empty">
            <div class="empty-icon">🎵</div>
            <p class="empty-title">Библиотека пуста</p>
            <p class="empty-hint">Отправь аудиофайлы боту,<br/>чтобы добавить музыку</p>
          </div>
          <TransitionGroup v-else name="list" tag="div">
            <TrackItem 
              v-for="track in library.tracks" 
              :key="track.id"
              :track="track"
              :isPlaying="player.currentTrack?.id === track.id && player.isPlaying"
              :isLiked="library.isTrackLiked(track.id)"
              @click="playTrack(track)"
              @menu="showTrackMenu(track)"
              @like="toggleLike(track.id)"
            />
          </TransitionGroup>
        </div>

        <!-- Playlists -->
        <div v-if="activeTab === 'playlists'" class="playlist-section">
          <button @click="createPlaylist" class="create-btn">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
            </svg>
            <span>Создать плейлист</span>
          </button>
          <div v-if="library.playlists.length === 0" class="empty">
            <div class="empty-icon">📁</div>
            <p class="empty-title">Нет плейлистов</p>
          </div>
          <PlaylistItem
            v-for="playlist in library.playlists"
            :key="playlist.id"
            :playlist="playlist"
            @click="openPlaylist(playlist)"
          />
        </div>

        <!-- Artists -->
        <div v-if="activeTab === 'artists'" class="list-section">
          <div v-if="library.artists.length === 0" class="empty">
            <div class="empty-icon">👤</div>
            <p class="empty-title">Нет артистов</p>
          </div>
          <div
            v-for="artist in library.artists"
            :key="artist.artist"
            class="list-item"
            @click="filterByArtist(artist.artist)"
          >
            <div class="list-item-avatar artist-avatar" :style="getArtistAvatarStyle(artist.artist)">
              <img 
                v-if="library.artistImages[artist.artist]" 
                :src="library.artistImages[artist.artist]" 
                alt=""
                class="avatar-image"
                @error="$event.target.style.display = 'none'"
              />
              <span v-else class="avatar-initials">{{ getArtistInitials(artist.artist) }}</span>
            </div>
            <div class="list-item-content">
              <span class="list-item-title">{{ artist.artist || 'Неизвестный' }}</span>
              <span class="list-item-subtitle">{{ artist.count }} треков</span>
            </div>
            <svg class="list-item-arrow" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
            </svg>
          </div>
        </div>

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
      </div>

      <!-- Playlist view -->
      <div v-if="currentView === 'playlist'" class="playlist-view">
        <div class="playlist-header-section">
          <div class="playlist-cover">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
            </svg>
          </div>
          <div class="playlist-meta">
            <h2>{{ currentPlaylist?.name }}</h2>
            <p>{{ currentPlaylist?.track_count }} треков • {{ formatDuration(currentPlaylist?.total_duration) }}</p>
          </div>
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
        />
      </div>
    </main>

    <!-- Bottom Tab Bar (One UI style) -->
    <nav v-if="currentView === 'library'" class="tab-bar">
      <button 
        :class="['tab-item', { active: activeTab === 'home' }]"
        @click="activeTab = 'home'; library.fetchHistory()"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
        </svg>
        <span>Главная</span>
      </button>
      <button 
        :class="['tab-item', { active: activeTab === 'tracks' }]"
        @click="activeTab = 'tracks'"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
        </svg>
        <span>Треки</span>
      </button>
      <button 
        :class="['tab-item', { active: activeTab === 'playlists' }]"
        @click="activeTab = 'playlists'"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
        </svg>
        <span>Плейлисты</span>
      </button>
      <button 
        :class="['tab-item', { active: activeTab === 'artists' }]"
        @click="activeTab = 'artists'; library.fetchArtists()"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>
        <span>Артисты</span>
      </button>
      <button 
        :class="['tab-item', { active: activeTab === 'history' }]"
        @click="activeTab = 'history'; library.fetchHistory()"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
        </svg>
        <span>История</span>
      </button>
    </nav>

    <!-- Mini Player -->
    <MiniPlayer 
      v-if="player.currentTrack"
      :track="player.currentTrack"
      :isPlaying="player.isPlaying"
      :loading="player.loading"
      :progress="player.progress"
      :duration="player.duration"
      @toggle="player.toggle()"
      @next="player.next()"
      @expand="showFullPlayer = true"
    />

    <!-- Full Player Modal with swipe -->
    <Transition name="slide-up">
      <FullPlayer 
        v-if="showFullPlayer"
        :track="player.currentTrack"
        :isPlaying="player.isPlaying"
        :loading="player.loading"
        :progress="player.progress"
        :duration="player.duration"
        :volume="player.volume"
        :isMuted="player.isMuted"
        :shuffle="player.shuffle"
        :repeat="player.repeat"
        :queue="player.queue"
        :queueIndex="player.queueIndex"
        @close="showFullPlayer = false"
        @toggle="player.toggle()"
        @next="player.next()"
        @prev="player.prev()"
        @seek="player.seek($event)"
        @setVolume="player.setVolume($event)"
        @toggleMute="player.toggleMute()"
        @toggleShuffle="player.toggleShuffle()"
        @toggleRepeat="player.toggleRepeat()"
      />
    </Transition>

    <!-- Track Context Menu -->
    <TrackMenu
      :show="showTrackMenuModal"
      :track="selectedTrack"
      @close="showTrackMenuModal = false"
      @addToPlaylist="handleAddToPlaylist"
      @edit="handleEditTrack"
      @delete="handleDeleteTrack"
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { usePlayerStore } from './stores/player'
import { useLibraryStore } from './stores/library'
import TrackItem from './components/TrackItem.vue'
import TrackSkeleton from './components/TrackSkeleton.vue'
import PlaylistItem from './components/PlaylistItem.vue'
import MiniPlayer from './components/MiniPlayer.vue'
import FullPlayer from './components/FullPlayer.vue'
import TrackMenu from './components/TrackMenu.vue'
import EditTrackModal from './components/EditTrackModal.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'
import PlaylistPicker from './components/PlaylistPicker.vue'
import EnrichmentStatus from './components/EnrichmentStatus.vue'
import Toast from './components/Toast.vue'

const telegram = inject('telegram')

// Stores
const player = usePlayerStore()
const library = useLibraryStore()

// Toast ref
const toast = ref(null)

// State
const currentView = ref('library')
const activeTab = ref('home')
const showSearch = ref(false)
const searchQuery = ref('')
const showFullPlayer = ref(false)
const showCreatePlaylist = ref(false)
const newPlaylistName = ref('')
const currentPlaylist = ref(null)
const activeFilter = ref(null) // Active artist/genre filter

// Track menu state
const showTrackMenuModal = ref(false)
const selectedTrack = ref(null)

// Edit modal state
const showEditModal = ref(false)
const editingTrack = ref(null)

// Confirm dialog state
const showConfirmDelete = ref(false)
const deletingTrack = ref(null)

// Playlist picker state
const showPlaylistPicker = ref(false)
const trackForPlaylist = ref(null)

// Pull-to-refresh state
const pullStartY = ref(0)
const pullDistance = ref(0)
const isPulling = ref(false)

// Computed
const headerTitle = computed(() => {
  switch (currentView.value) {
    case 'library': return 'TG Player'
    case 'playlist': return currentPlaylist.value?.name || 'Плейлист'
    default: return 'TG Player'
  }
})

const upcomingTracks = computed(() => {
  if (!player.queue.length || player.queueIndex < 0) return []
  return player.queue.slice(player.queueIndex + 1, player.queueIndex + 11)
})

// Methods
const goBack = () => {
  currentView.value = 'library'
  currentPlaylist.value = null
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

const showTrackMenu = (track) => {
  selectedTrack.value = track
  showTrackMenuModal.value = true
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

const confirmDeleteTrack = async () => {
  if (deletingTrack.value) {
    await library.deleteTrack(deletingTrack.value.id)
    telegram?.HapticFeedback?.notificationOccurred?.('success')
  }
  showConfirmDelete.value = false
  deletingTrack.value = null
}

const openPlaylist = async (playlist) => {
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

const filterByArtist = (artist) => {
  activeFilter.value = `Артист: ${artist}`
  activeTab.value = 'tracks'
  library.fetchTracks({ artist })
}

const filterByGenre = (genre) => {
  activeFilter.value = `Жанр: ${genre}`
  activeTab.value = 'tracks'
  library.fetchTracks({ genre })
}

// Get initials for artist avatar
const getArtistInitials = (name) => {
  if (!name) return '?'
  const words = name.split(' ').filter(w => w.length > 0)
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

// Generate gradient for artist avatar
const getArtistAvatarStyle = (name) => {
  if (library.artistImages[name]) return {}
  
  // Generate gradient based on name
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue1 = Math.abs(hash % 360)
  const hue2 = (hue1 + 40) % 360
  
  return {
    background: `linear-gradient(135deg, hsl(${hue1}, 60%, 45%) 0%, hsl(${hue2}, 50%, 35%) 100%)`
  }
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
  searchQuery.value = ''
  library.fetchTracks()
}

const formatDuration = (seconds) => {
  if (!seconds) return '0 мин'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) return `${hours} ч ${minutes} мин`
  return `${minutes} мин`
}

let searchTimeout = null
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    library.fetchTracks({ search: searchQuery.value })
  }, 300)
}

// Pull-to-refresh handlers
const handleTouchStart = (e) => {
  const scrollTop = document.querySelector('.content')?.scrollTop || 0
  if (scrollTop === 0 && currentView.value === 'library') {
    pullStartY.value = e.touches[0].clientY
    isPulling.value = true
  }
}

const handleTouchMove = (e) => {
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

const handleTouchEnd = async () => {
  if (!isPulling.value) return
  
  if (pullDistance.value > 60 && !library.refreshing) {
    await library.refresh()
    telegram?.HapticFeedback?.impactOccurred?.('light')
  }
  
  pullDistance.value = 0
  isPulling.value = false
  pullStartY.value = 0
}

// Handle track unavailable error
const handleTrackUnavailable = (track, message) => {
  toast.value?.error(
    'Трек недоступен',
    `${track.title || 'Трек'} был удалён из Telegram`
  )
  telegram?.HapticFeedback?.notificationOccurred?.('error')
  
  // Refresh library to update track states
  library.fetchTracks()
}

// Apply Spotify theme on mount
onMounted(async () => {
  document.body.classList.add('spotify-theme')
  await library.init()
  
  // Set up error callback for player
  player.setOnTrackUnavailable(handleTrackUnavailable)
})
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--spotify-black);
  color: var(--spotify-text);
}

/* One UI Large Header */
.oneui-header {
  flex-shrink: 0;
  padding: 16px 20px 20px;
  background: linear-gradient(180deg, var(--spotify-gray-dark) 0%, var(--spotify-black) 100%);
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.oneui-header h1 {
  font-size: 34px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.icon-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: var(--spotify-gray);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--spotify-text);
  transition: background 0.2s;
}

.icon-btn:active {
  background: var(--spotify-gray-light);
}

/* Compact Header */
.compact-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: var(--spotify-gray-dark);
  gap: 12px;
}

.header-title {
  flex: 1;
  font-size: 18px;
  font-weight: 600;
}

.spacer {
  width: 40px;
}

/* Search */
.search-container {
  margin-top: 16px;
}

.search-input {
  width: 100%;
  padding: 14px 16px;
  border: none;
  border-radius: 8px;
  background: var(--spotify-gray);
  color: var(--spotify-text);
  font-size: 16px;
}

.search-input::placeholder {
  color: var(--spotify-text-muted);
}

/* Content */
.content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 160px; /* Space for mini player + tab bar */
  position: relative;
}

/* Pull to refresh */
.pull-indicator {
  position: absolute;
  top: -60px;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--spotify-text-muted);
  font-size: 13px;
  transition: transform 0.1s ease-out;
  z-index: 10;
}

.pull-spinner {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--spotify-green);
}

.pull-spinner.active svg {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* History section */
.history-section {
  padding: 8px 0;
}

.history-list {
  padding: 0 8px;
}

/* Active filter indicator */
.active-filter {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  margin: 8px 16px;
  background: var(--spotify-green);
  border-radius: 8px;
  color: black;
  font-size: 14px;
  font-weight: 500;
}

.clear-filter-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: black;
}

/* Empty state */
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 14px;
  color: var(--spotify-text-muted);
  line-height: 1.4;
}

/* List items */
.list-section {
  padding: 8px 0;
}

.list-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  gap: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.list-item:active {
  background: var(--spotify-gray);
}

.list-item-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--spotify-gray);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--spotify-text-secondary);
  flex-shrink: 0;
  overflow: hidden;
}

.list-item-avatar.artist-avatar {
  border-radius: 50%;
}

.list-item-avatar .avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.list-item-avatar .avatar-initials {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.list-item-avatar.genre {
  border-radius: 8px;
  background: linear-gradient(135deg, var(--spotify-green) 0%, #1e3a5f 100%);
  color: white;
}

.list-item-content {
  flex: 1;
  min-width: 0;
}

.list-item-title {
  display: block;
  font-size: 16px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-item-subtitle {
  display: block;
  font-size: 13px;
  color: var(--spotify-text-muted);
  margin-top: 2px;
}

.list-item-arrow {
  color: var(--spotify-text-muted);
}

/* ========== Home Feed Styles ========== */
.home-feed {
  padding: 0 0 16px 0;
}

/* Quick Access Grid */
.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  padding: 16px;
}

.quick-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--spotify-gray);
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.quick-item:active {
  background: var(--spotify-gray-light);
}

.quick-icon {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--spotify-green) 0%, #1e8e5e 100%);
  color: white;
  flex-shrink: 0;
}

.quick-icon.history-icon {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
}

.quick-icon.playlist-icon {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
}

.quick-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--spotify-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Feed Sections */
.feed-section {
  margin-bottom: 24px;
}

.feed-section-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--spotify-text);
  padding: 0 16px;
  margin-bottom: 12px;
}

.horizontal-scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding: 0 16px;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.horizontal-scroll::before {
  content: '';
  flex-shrink: 0;
  width: 4px;
}

.horizontal-scroll::after {
  content: '';
  flex-shrink: 0;
  width: 4px;
}

.horizontal-scroll::-webkit-scrollbar {
  display: none;
}

/* Feed Cards */
.feed-card {
  flex-shrink: 0;
  width: 140px;
  scroll-snap-align: start;
  cursor: pointer;
}

.feed-card-cover {
  width: 140px;
  height: 140px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  background: var(--spotify-gray);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.feed-card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.feed-card-cover .feed-card-placeholder {
  font-size: 32px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.7);
}

.feed-card-cover .play-overlay {
  position: absolute;
  bottom: 8px;
  right: 8px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--spotify-green);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: black;
  opacity: 0;
  transform: translateY(8px);
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.feed-card:hover .play-overlay,
.feed-card:active .play-overlay {
  opacity: 1;
  transform: translateY(0);
}

/* Liked badge on cards */
.liked-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1db954;
}

.feed-card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--spotify-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feed-card-subtitle {
  font-size: 12px;
  color: var(--spotify-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

/* Artist Card */
.artist-card {
  text-align: center;
}

.artist-card .feed-card-cover {
  border-radius: 50%;
}

.artist-cover {
  border-radius: 50%;
}

.artist-cover img {
  border-radius: 50%;
}

.artist-initials {
  font-size: 36px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.85);
}

/* Playlist Card */
.playlist-cover {
  background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
  color: rgba(255, 255, 255, 0.9);
}

/* Add Card */
.add-card .add-cover {
  background: var(--spotify-gray);
  border: 2px dashed var(--spotify-gray-light);
  color: var(--spotify-text-muted);
}

.add-card:active .add-cover {
  background: var(--spotify-gray-light);
}

/* Tracks Preview */
.feed-tracks-preview {
  padding: 0 16px;
}

.see-all-btn {
  width: 100%;
  padding: 12px;
  margin-top: 8px;
  background: transparent;
  border: 1px solid var(--spotify-gray-light);
  border-radius: 20px;
  color: var(--spotify-text);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.see-all-btn:active {
  background: var(--spotify-gray);
}

/* Playlist section */
.playlist-section {
  padding: 16px;
}

.create-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  padding: 16px;
  border: 2px dashed var(--spotify-gray-light);
  border-radius: 12px;
  background: transparent;
  color: var(--spotify-text-secondary);
  font-size: 15px;
  cursor: pointer;
  margin-bottom: 16px;
  transition: all 0.2s;
}

.create-btn:active {
  background: var(--spotify-gray);
  border-color: var(--spotify-green);
  color: var(--spotify-green);
}

/* Playlist view */
.playlist-view {
  padding: 20px;
}

.playlist-header-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.playlist-cover {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--spotify-gray) 0%, var(--spotify-gray-dark) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--spotify-text-secondary);
}

.playlist-meta {
  flex: 1;
}

.playlist-meta h2 {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 4px;
}

.playlist-meta p {
  font-size: 14px;
  color: var(--spotify-text-muted);
}

.play-all-btn {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--spotify-green);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: black;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
  transition: transform 0.2s, box-shadow 0.2s;
}

.play-all-btn:active {
  transform: scale(0.95);
}

/* Queue section */
.queue-section {
  padding: 16px;
}

.queue-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--spotify-text-muted);
  padding: 16px 0 8px;
}

.queue-now-playing {
  background: var(--spotify-gray);
  border-radius: 12px;
  padding: 4px;
  margin-bottom: 16px;
}

/* Bottom Tab Bar */
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  background: var(--spotify-gray-dark);
  border-top: 1px solid var(--spotify-gray);
  padding: 8px 0 max(8px, env(safe-area-inset-bottom));
  z-index: 50;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 0;
  border: none;
  background: none;
  color: var(--spotify-text-muted);
  font-size: 11px;
  cursor: pointer;
  transition: color 0.2s;
}

.tab-item.active {
  color: var(--spotify-green);
}

.tab-item svg {
  width: 24px;
  height: 24px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.modal {
  background: var(--spotify-gray);
  padding: 24px;
  border-radius: 16px;
  width: 90%;
  max-width: 320px;
}

.modal h3 {
  margin-bottom: 16px;
  font-size: 20px;
  font-weight: 700;
}

.modal-input {
  width: 100%;
  padding: 14px 16px;
  border: none;
  border-radius: 8px;
  background: var(--spotify-gray-dark);
  color: var(--spotify-text);
  font-size: 16px;
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  gap: 12px;
}

.btn-primary, .btn-secondary {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 24px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary {
  background: var(--spotify-green);
  color: black;
}

.btn-secondary {
  background: transparent;
  color: var(--spotify-text);
  border: 1px solid var(--spotify-text-muted);
}

/* Skeleton list */
.skeleton-list {
  padding: 0;
}

/* Animations */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
