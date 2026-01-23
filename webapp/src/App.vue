<template>
  <div class="app spotify-theme">
    <!-- One UI Style Header with Animated Search -->
    <header class="oneui-header" v-if="currentView === 'library'">
      <div class="header-row">
        <EnrichmentStatus />
        
        <!-- Animated Search / Title Toggle -->
        <div class="search-title-container" :class="{ expanded: showSearch }">
          <!-- Title (visible when search closed) -->
          <Transition name="fade-title">
            <h1 v-if="!showSearch" class="header-title-main" @click="openSearch">
              TG Player
            </h1>
          </Transition>
          
          <!-- Search Input (visible when search open) -->
          <Transition name="expand-search">
            <div v-if="showSearch" class="search-wrapper">
              <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
              </svg>
              <input 
                ref="searchInput"
                v-model="searchQuery"
                type="text"
                placeholder="Поиск треков, артистов..."
                class="search-input-inline"
                @input="debouncedSearch"
                @blur="onSearchBlur"
                @keyup.escape="closeSearch"
              />
              <button class="search-close-btn" @click="closeSearch">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
                </svg>
              </button>
            </div>
          </Transition>
        </div>
        
        <!-- Search Toggle Button (visible when search closed) -->
        <Transition name="fade">
          <button v-if="!showSearch" @click="openSearch" class="icon-btn search-toggle">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
            </svg>
          </button>
        </Transition>
      </div>
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
              class="quick-item liked-quick" 
              v-if="library.likedTracks.length > 0"
              @click="activeTab = 'liked'"
            >
              <div class="quick-icon liked-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                </svg>
              </div>
              <span class="quick-title">Любимое</span>
            </div>
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

          <!-- Top Artists Section -->
          <div v-if="library.artists.length > 0" class="feed-section">
            <h2 class="feed-section-title">Твои артисты</h2>
            <div class="horizontal-scroll">
              <div class="scroll-spacer"></div>
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
              <div class="scroll-spacer"></div>
            </div>
          </div>

          <!-- Genres Section -->
          <div v-if="library.genres.length > 0" class="feed-section">
            <h2 class="feed-section-title">Жанры</h2>
            <div class="horizontal-scroll">
              <div class="scroll-spacer"></div>
              <div 
                v-for="genre in library.genres.slice(0, 10)" 
                :key="genre.genre"
                class="feed-card genre-card"
                @click="playGenreShuffle(genre.genre)"
              >
                <div class="feed-card-cover genre-cover" :style="getGenreStyle(genre.genre)">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor" class="genre-icon">
                    <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
                  </svg>
                  <div class="shuffle-badge">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
                    </svg>
                  </div>
                </div>
                <div class="feed-card-title">{{ genre.genre }}</div>
                <div class="feed-card-subtitle">{{ genre.count }} треков</div>
              </div>
              <div class="scroll-spacer"></div>
            </div>
          </div>

          <!-- Playlists Section -->
          <div v-if="library.playlists.length > 0" class="feed-section">
            <h2 class="feed-section-title">Плейлисты</h2>
            <div class="horizontal-scroll">
              <div class="scroll-spacer"></div>
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
              <div class="scroll-spacer"></div>
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
          <!-- Любимое -->
          <div 
            v-if="library.likedTracks.length > 0" 
            class="system-playlist-item"
            @click="activeTab = 'liked'"
          >
            <div class="system-playlist-icon liked-gradient">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
              </svg>
            </div>
            <div class="system-playlist-info">
              <span class="system-playlist-title">Любимое</span>
              <span class="system-playlist-count">{{ library.likedTracks.length }} треков</span>
            </div>
          </div>
          
          <!-- История -->
          <div 
            v-if="library.history.length > 0" 
            class="system-playlist-item"
            @click="activeTab = 'history'"
          >
            <div class="system-playlist-icon history-gradient">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
              </svg>
            </div>
            <div class="system-playlist-info">
              <span class="system-playlist-title">История</span>
              <span class="system-playlist-count">{{ library.history.length }} треков</span>
            </div>
          </div>

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
              @click="playTrack(track)"
              @menu="showTrackMenu(track)"
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

    <!-- Mini Player (above tab bar in flex layout) -->
    <MiniPlayer 
      v-if="player.currentTrack && currentView === 'library'"
      :track="player.currentTrack"
      :isPlaying="player.isPlaying"
      :loading="player.loading"
      :progress="player.progress"
      :duration="player.duration"
      @toggle="player.toggle()"
      @next="player.next()"
      @expand="showFullPlayer = true"
    />

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
import { ref, computed, onMounted, inject, nextTick } from 'vue'
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

// Refs
const searchInput = ref(null)

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

const playLikedTracks = async () => {
  if (library.likedTracks.length) {
    await player.play(library.likedTracks[0], library.likedTracks)
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

// Generate gradient for genre card
const getGenreStyle = (genre) => {
  const genreColors = {
    'Rock': { h1: 0, h2: 30 },
    'Pop': { h1: 300, h2: 330 },
    'Hip-Hop': { h1: 40, h2: 60 },
    'Rap': { h1: 35, h2: 55 },
    'Electronic': { h1: 180, h2: 220 },
    'Dance': { h1: 280, h2: 320 },
    'House': { h1: 200, h2: 240 },
    'Techno': { h1: 260, h2: 290 },
    'Dubstep': { h1: 270, h2: 300 },
    'Drum and Bass': { h1: 15, h2: 45 },
    'Jazz': { h1: 45, h2: 70 },
    'Classical': { h1: 220, h2: 250 },
    'Metal': { h1: 0, h2: 20 },
    'R&B': { h1: 320, h2: 350 },
    'Soul': { h1: 30, h2: 50 },
    'Country': { h1: 35, h2: 55 },
    'Reggae': { h1: 100, h2: 140 },
    'Blues': { h1: 210, h2: 240 },
    'Indie': { h1: 150, h2: 180 },
    'Alternative': { h1: 160, h2: 190 },
  }
  
  // Find matching genre or generate from name
  let hue1, hue2
  const found = Object.entries(genreColors).find(([key]) => 
    genre.toLowerCase().includes(key.toLowerCase())
  )
  
  if (found) {
    hue1 = found[1].h1
    hue2 = found[1].h2
  } else {
    // Generate from name hash
    let hash = 0
    for (let i = 0; i < genre.length; i++) {
      hash = genre.charCodeAt(i) + ((hash << 5) - hash)
    }
    hue1 = Math.abs(hash % 360)
    hue2 = (hue1 + 40) % 360
  }
  
  return {
    background: `linear-gradient(135deg, hsl(${hue1}, 70%, 40%) 0%, hsl(${hue2}, 60%, 30%) 100%)`
  }
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

// Search open/close with animation
const openSearch = async () => {
  showSearch.value = true
  await nextTick()
  searchInput.value?.focus()
}

const closeSearch = () => {
  showSearch.value = false
  if (searchQuery.value) {
    searchQuery.value = ''
    library.fetchTracks()  // Reset to full list
  }
}

const onSearchBlur = () => {
  // Close search if empty after small delay (allows clicking close button)
  setTimeout(() => {
    if (!searchQuery.value && showSearch.value) {
      showSearch.value = false
    }
  }, 150)
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

// Apply Spotify theme on mount
onMounted(async () => {
  document.body.classList.add('spotify-theme')
  await library.init()
})
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;  /* Contain scrollbar within app bounds */
  background-color: var(--spotify-black);
  color: var(--spotify-text);
}

/* One UI Large Header */
.oneui-header {
  flex-shrink: 0;
  padding: 12px 16px 16px;
  background: linear-gradient(180deg, var(--spotify-gray-dark) 0%, var(--spotify-black) 100%);
}

.header-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Search/Title Container - animated expansion */
.search-title-container {
  flex: 1;
  position: relative;
  height: 44px;
  display: flex;
  align-items: center;
}

.header-title-main {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.5px;
  margin: 0;
  cursor: pointer;
  white-space: nowrap;
}

/* Search wrapper with animation */
.search-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
  height: 44px;
  background: var(--spotify-gray);
  border-radius: 22px;
  padding: 0 12px;
  gap: 10px;
}

.search-icon {
  flex-shrink: 0;
  color: var(--spotify-text-muted);
}

.search-input-inline {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--spotify-text);
  font-size: 16px;
  outline: none;
  padding: 0;
}

.search-input-inline::placeholder {
  color: var(--spotify-text-muted);
}

.search-close-btn {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border: none;
  background: var(--spotify-gray-light);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--spotify-text);
}

.search-toggle {
  flex-shrink: 0;
}

/* Animations */
.expand-search-enter-active {
  animation: expandSearch 0.3s ease-out;
}

.expand-search-leave-active {
  animation: expandSearch 0.2s ease-in reverse;
}

@keyframes expandSearch {
  from {
    opacity: 0;
    transform: scaleX(0.3);
    transform-origin: right center;
  }
  to {
    opacity: 1;
    transform: scaleX(1);
    transform-origin: right center;
  }
}

.fade-title-enter-active,
.fade-title-leave-active {
  transition: opacity 0.2s ease;
}

.fade-title-enter-from,
.fade-title-leave-to {
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
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

/* Content */
.content {
  flex: 1;
  min-height: 0;  /* Allow flex shrinking for proper overflow */
  overflow-y: auto;
  overflow-x: hidden;  /* Prevent horizontal scrollbar */
  position: relative;
}

/* Content scrollbar - fully transparent track */
.content::-webkit-scrollbar {
  width: 4px;
  background: transparent;
}

.content::-webkit-scrollbar-track {
  background: transparent;
}

.content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
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

/* Liked section */
.liked-section {
  padding: 8px 0;
}

.liked-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  margin-bottom: 8px;
}

.liked-cover {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  background: linear-gradient(135deg, #1db954 0%, #1ed760 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.liked-meta {
  flex: 1;
  min-width: 0;
}

.liked-meta h2 {
  font-size: 22px;
  font-weight: 700;
  color: var(--spotify-text);
  margin: 0 0 4px;
}

.liked-meta p {
  font-size: 14px;
  color: var(--spotify-text-muted);
  margin: 0;
}

.liked-list {
  padding: 0 8px;
}

/* Liked quick item and tab */
.liked-quick .quick-icon,
.liked-icon {
  background: linear-gradient(135deg, #1db954 0%, #1ed760 100%) !important;
  color: white;
}

.liked-tab.active {
  color: #1db954 !important;
}

.liked-tab svg {
  fill: currentColor;
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
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.horizontal-scroll::-webkit-scrollbar {
  display: none;
}

.scroll-spacer {
  flex-shrink: 0;
  width: 16px;
}

/* Feed Cards */
.feed-card {
  flex-shrink: 0;
  width: 140px;
  scroll-snap-align: start;
  cursor: pointer;
  text-align: center;
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
  margin: 0 auto 8px;
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

/* Genre Card */
.genre-card .feed-card-cover {
  position: relative;
}

.genre-cover {
  color: rgba(255, 255, 255, 0.9);
}

.genre-icon {
  opacity: 0.9;
}

.shuffle-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--spotify-green);
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

/* System playlists (Liked, History) */
.system-playlist-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  background: var(--spotify-gray);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.system-playlist-item:active {
  background: var(--spotify-gray-light);
}

.system-playlist-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.system-playlist-icon.liked-gradient {
  background: linear-gradient(135deg, #1db954 0%, #1ed760 100%);
}

.system-playlist-icon.history-gradient {
  background: linear-gradient(135deg, #7c3aed 0%, #a78bfa 100%);
}

.system-playlist-info {
  flex: 1;
  min-width: 0;
}

.system-playlist-title {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: var(--spotify-text);
}

.system-playlist-count {
  display: block;
  font-size: 13px;
  color: var(--spotify-text-muted);
  margin-top: 2px;
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

/* Bottom Tab Bar - Neumorphic Style */
.tab-bar {
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  gap: 16px;
  background: var(--spotify-black);
  padding: 12px 16px max(12px, env(safe-area-inset-bottom));
  z-index: 50;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 64px;
  height: 56px;
  border: none;
  border-radius: 16px;
  background: var(--spotify-gray-dark);
  color: var(--spotify-text-muted);
  font-size: 10px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  /* Neumorphic shadow */
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.4),
    -2px -2px 6px rgba(255, 255, 255, 0.05);
}

.tab-item:active {
  /* Pressed state - inset shadow */
  box-shadow: 
    inset 3px 3px 6px rgba(0, 0, 0, 0.4),
    inset -2px -2px 4px rgba(255, 255, 255, 0.05);
  transform: scale(0.95);
}

.tab-item.active {
  color: var(--spotify-green);
  background: linear-gradient(145deg, var(--spotify-gray), var(--spotify-gray-dark));
  box-shadow: 
    4px 4px 10px rgba(0, 0, 0, 0.5),
    -2px -2px 6px rgba(255, 255, 255, 0.08),
    inset 0 0 0 1px rgba(29, 185, 84, 0.2);
}

.tab-item.active svg {
  filter: drop-shadow(0 0 4px rgba(29, 185, 84, 0.5));
}

.tab-item svg {
  width: 22px;
  height: 22px;
  transition: filter 0.2s;
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
