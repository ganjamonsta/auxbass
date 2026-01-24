<template>
  <div class="app spotify-theme">
    <!-- One UI Style Header with Animated Search -->
    <header class="oneui-header" v-if="currentView === 'library'">
      <div class="header-row">
        <!-- Left slot: EnrichmentStatus OR Search field (mutually exclusive) -->
        <div class="header-left-slot" :class="{ expanded: showSearch }">
          <Transition name="fade-slide" mode="out-in">
            <!-- Enrichment status (when search is closed) -->
            <EnrichmentStatus v-if="!showSearch" key="enrichment" />
            
            <!-- Search field (when search is open) -->
            <div v-else key="search" class="search-wrapper" @click="focusInput">
              <!-- Scope toggle (Library / Global) -->
              <button 
                class="search-scope-btn" 
                :class="{ global: searchScope === 'global' }"
                @click.stop="toggleSearchScope"
                :title="searchScope === 'library' ? 'Искать в своей библиотеке' : 'Искать везде'"
              >
                <svg v-if="searchScope === 'library'" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                </svg>
                <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                </svg>
              </button>
              <div class="search-content">
                <span v-for="(tag, index) in searchTags" :key="index" class="search-tag" @click.stop="removeTag(index)">
                  {{ tag }}
                </span>
                <input 
                  ref="searchInput"
                  v-model="searchQuery"
                  type="text"
                  :placeholder="searchScope === 'library' ? 'Поиск в библиотеке...' : 'Глобальный поиск...'"
                  class="search-input-inline"
                  @input="debouncedSearch"
                  @keyup.escape="closeSearch"
                  @keydown.enter.prevent="addTag"
                  @keydown.backspace="handleBackspace"
                />
              </div>
            </div>
          </Transition>
        </div>
        
        <!-- Title (visible when search is closed) -->
        <h1 v-if="!showSearch" class="header-title-main" @click="goToHome">
          {{ currentTabName }}
        </h1>
        
        <!-- Search Toggle Button (always fixed right) -->
        <button @click="toggleSearch" class="icon-btn search-toggle">
          <Transition name="icon-flip" mode="out-in">
            <svg v-if="!showSearch" key="search" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
            </svg>
            <svg v-else key="close" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
            </svg>
          </Transition>
        </button>
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
      ref="contentRef"
      class="content"
      @scroll="handleContentScroll"
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
          <span v-if="filterScope === 'global'" class="global-badge">🌍</span>
          <span>{{ activeFilter }}</span>
          <button @click="clearFilter" class="clear-filter-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
            </svg>
          </button>
        </div>

        <!-- Home Feed (Spotify-style) -->
        <div v-if="activeTab === 'home'" class="home-feed">
          <!-- Quick Access Grid - only essential items -->
          <div class="quick-grid">
            <!-- Liked tracks -->
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
            <!-- History -->
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
            <!-- All playlists link -->
            <div 
              class="quick-item"
              v-if="library.playlists.length > 1"
              @click="activeTab = 'playlists'"
            >
              <div class="quick-icon allpl-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9h-4v4h-2v-4H9V9h4V5h2v4h4v2z"/>
                </svg>
              </div>
              <span class="quick-title">Плейлисты</span>
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

        <!-- Search Results (sectioned) -->
        <div v-if="activeTab === 'search'" class="search-results">
          <!-- Loading state -->
          <div v-if="(library.loading || library.globalLoading) && !hasSearchResults" class="skeleton-list">
            <TrackSkeleton v-for="i in 4" :key="i" />
          </div>

          <!-- No results -->
          <div v-else-if="!hasSearchResults && activeFilter" class="empty">
            <div class="empty-icon">🔍</div>
            <p class="empty-title">Ничего не найдено</p>
            <p class="empty-hint">Попробуйте другой запрос</p>
          </div>

          <template v-else>
            <!-- Artists Section -->
            <div v-if="searchResultArtists.length > 0" class="search-section">
              <h3 class="search-section-title">Артисты</h3>
              <div class="search-artists-list">
                <div
                  v-for="artist in searchResultArtists"
                  :key="artist.artist"
                  class="search-artist-item"
                  @click="filterByArtist(artist.artist, searchScope)"
                >
                  <div class="search-artist-avatar" :style="getArtistAvatarStyle(artist.artist)">
                    <img 
                      v-if="library.artistImages[artist.artist]" 
                      :src="library.artistImages[artist.artist]" 
                      alt=""
                      @error="$event.target.style.display = 'none'"
                    />
                    <span v-else class="avatar-initials">{{ getArtistInitials(artist.artist) }}</span>
                  </div>
                  <div class="search-artist-info">
                    <span class="search-artist-name">{{ artist.artist }}</span>
                    <span class="search-artist-count">{{ artist.count }} треков</span>
                  </div>
                  <svg class="search-item-arrow" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
                  </svg>
                </div>
              </div>
            </div>

            <!-- Albums Section -->
            <div v-if="searchResultAlbums.length > 0" class="search-section">
              <h3 class="search-section-title">Альбомы</h3>
              <div class="search-albums-list">
                <div
                  v-for="album in searchResultAlbums"
                  :key="album.id"
                  class="search-album-item"
                  @click="openPlaylist(album)"
                >
                  <div class="search-album-cover">
                    <img v-if="album.cover_url" :src="album.cover_url" alt="" />
                    <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5zm0-5.5c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/>
                    </svg>
                  </div>
                  <div class="search-album-info">
                    <span class="search-album-name">{{ album.name }}</span>
                    <span class="search-album-artist">{{ album.album_artist || 'Альбом' }} • {{ album.track_count }} треков</span>
                  </div>
                  <svg class="search-item-arrow" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
                  </svg>
                </div>
              </div>
            </div>

            <!-- Playlists Section -->
            <div v-if="searchResultPlaylists.length > 0" class="search-section">
              <h3 class="search-section-title">Плейлисты</h3>
              <div class="search-playlists-list">
                <div
                  v-for="playlist in searchResultPlaylists"
                  :key="playlist.id"
                  class="search-playlist-item"
                  @click="openPlaylist(playlist)"
                >
                  <div class="search-playlist-cover">
                    <img v-if="playlist.cover_url" :src="playlist.cover_url" alt="" />
                    <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
                    </svg>
                  </div>
                  <div class="search-playlist-info">
                    <span class="search-playlist-name">{{ playlist.name }}</span>
                    <span class="search-playlist-count">{{ playlist.track_count }} треков</span>
                  </div>
                  <svg class="search-item-arrow" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
                  </svg>
                </div>
              </div>
            </div>

            <!-- Tracks Section -->
            <div v-if="displayedTracks.length > 0" class="search-section">
              <h3 class="search-section-title">Треки</h3>
              <TrackItem 
                v-for="track in displayedTracks.slice(0, 20)" 
                :key="track.id"
                :track="track"
                :isPlaying="player.currentTrack?.id === track.id && player.isPlaying"
                :isLiked="library.isTrackLiked(track.id)"
                @click="playTrack(track, displayedTracks)"
                @menu="showTrackMenu(track)"
                @like="toggleLike(track.id)"
              />
              <button 
                v-if="displayedTracks.length > 20" 
                class="see-all-btn"
                @click="activeTab = 'tracks'"
              >
                Показать все треки ({{ filterScope === 'global' ? library.globalTotal : library.total }})
              </button>
            </div>
          </template>
        </div>
        
        <!-- Track list -->
        <div v-if="activeTab === 'tracks'" class="track-list">
          <!-- Skeleton only on initial load when no tracks -->
          <div v-if="(library.loading || library.globalLoading) && displayedTracks.length === 0" class="skeleton-list">
            <TrackSkeleton v-for="i in 6" :key="i" />
          </div>
          
          <div v-else-if="displayedTracks.length === 0" class="empty">
            <div class="empty-icon">🎵</div>
            <p class="empty-title">{{ filterScope === 'global' ? 'Треки не найдены' : 'Библиотека пуста' }}</p>
            <p class="empty-hint">{{ filterScope === 'global' ? 'Попробуйте другого артиста' : 'Отправь аудиофайлы боту, чтобы добавить музыку' }}</p>
          </div>
          
          <template v-else>
            <TrackItem 
              v-for="track in displayedTracks" 
              :key="track.id"
              :track="track"
              :isPlaying="player.currentTrack?.id === track.id && player.isPlaying"
              :isLiked="library.isTrackLiked(track.id)"
              @click="playTrack(track, displayedTracks)"
              @menu="showTrackMenu(track)"
              @like="toggleLike(track.id)"
            />
            
            <!-- Load more button -->
            <button 
              v-if="library.hasMore && !library.loading" 
              class="load-more-btn"
              :disabled="library.loading"
              @click="library.loadMore()"
            >
              Загрузить ещё
            </button>
            
            <!-- Loading indicator while fetching more -->
            <div v-if="library.loading" class="loading-more">
              <div class="loading-spinner"></div>
              <span>Загрузка...</span>
            </div>
          </template>
        </div>

        <!-- Playlists - Categorized -->
        <div v-if="activeTab === 'playlists'" class="playlist-section">
          <!-- System playlists -->
          <div class="playlist-category">
            <h3 class="category-title">Быстрый доступ</h3>
            <div class="system-playlists-grid">
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
            </div>
          </div>

          <!-- Source playlists (from bots/channels) -->
          <div v-if="sourcePlaylists.length > 0" class="playlist-category">
            <h3 class="category-title clickable" @click="openSection('sources')">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 6px; opacity: 0.7;">
                <path d="M21 3H3c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H3V5h18v14zM9.41 15.95L12 13.36l2.59 2.59L16 14.54l-4-4-4 4z"/>
              </svg>
              Источники
              <svg class="section-arrow" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
              </svg>
            </h3>
            <div class="playlists-compact-list">
              <PlaylistItem
                v-for="playlist in sourcePlaylists"
                :key="playlist.id"
                :playlist="playlist"
                @click="openPlaylist(playlist)"
              />
            </div>
          </div>

          <!-- Album playlists (auto-generated from Deezer) -->
          <div v-if="albumPlaylists.length > 0" class="playlist-category">
            <h3 class="category-title clickable" @click="openSection('albums')">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 6px; opacity: 0.7;">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5zm0-5.5c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/>
              </svg>
              Альбомы
              <svg class="section-arrow" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
              </svg>
            </h3>
            <div class="playlists-compact-list">
              <PlaylistItem
                v-for="playlist in albumPlaylists"
                :key="playlist.id"
                :playlist="playlist"
                @click="openPlaylist(playlist)"
              />
            </div>
          </div>

          <!-- User playlists -->
          <div class="playlist-category">
            <div class="category-header">
              <h3 class="category-title clickable" @click="openSection('playlists')">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 6px; opacity: 0.7;">
                  <path d="M4 10h12v2H4zm0-4h12v2H4zm0 8h8v2H4zm10 0v6l5-3z"/>
                </svg>
                Мои плейлисты
                <svg class="section-arrow" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
                </svg>
              </h3>
              <button @click.stop="createPlaylist" class="create-btn-small">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                </svg>
              </button>
            </div>
            <div v-if="userPlaylists.length === 0" class="empty-small">
              <p>Нет плейлистов</p>
              <button @click="createPlaylist" class="create-btn">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                </svg>
                <span>Создать плейлист</span>
              </button>
            </div>
            <div v-else class="playlists-compact-list">
              <PlaylistItem
                v-for="playlist in userPlaylists"
                :key="playlist.id"
                :playlist="playlist"
                @click="openPlaylist(playlist)"
              />
            </div>
          </div>
        </div>

        <!-- Artists -->
        <div v-if="activeTab === 'artists'" class="list-section">
          <!-- Scope toggle -->
          <div class="scope-toggle">
            <button 
              :class="['scope-btn', { active: library.artistScope === 'library' }]"
              @click="library.fetchArtists('library')"
            >
              Моя библиотека
            </button>
            <button 
              :class="['scope-btn', { active: library.artistScope === 'global' }]"
              @click="library.fetchArtists('global')"
            >
              Вся музыка
            </button>
          </div>
          
          <div v-if="displayedArtists.length === 0" class="empty">
            <div class="empty-icon">👤</div>
            <p class="empty-title">Нет артистов</p>
          </div>
          <div
            v-for="artist in displayedArtists"
            :key="artist.artist"
            class="list-item"
            @click="filterByArtist(artist.artist, library.artistScope)"
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

    <!-- Mini Player (above tab bar in flex layout) -->
    <MiniPlayer 
      v-if="player.currentTrack && currentView === 'library'"
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

    <!-- Bottom Tab Bar (One UI style) -->
    <nav v-if="currentView === 'library' && !expandedSection" class="tab-bar">
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
import { playerApi } from './api/client'
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
import GlobalLibrary from './components/GlobalLibrary.vue'
import ArtistCard from './components/ArtistCard.vue'
import Toast from './components/Toast.vue'

const telegram = inject('telegram')

// Get username from Telegram
const userDisplayName = computed(() => {
  const user = telegram?.initDataUnsafe?.user
  if (user?.username) {
    return `@${user.username}`
  }
  return user?.first_name || 'Musiq'
})

// Get current user ID from Telegram
const currentUserId = computed(() => {
  return telegram?.initDataUnsafe?.user?.id || null
})

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

// Stores
const player = usePlayerStore()
const library = useLibraryStore()

// Refs
const searchInput = ref(null)
const contentRef = ref(null)

// Toast ref
const toast = ref(null)

// State
const currentView = ref('library')
const activeTab = ref('home')
const showSearch = ref(false)
const searchQuery = ref('')
const searchTags = ref([])
const searchScope = ref('library')  // 'library' or 'global' - search scope
const showFullPlayer = ref(false)
const showCreatePlaylist = ref(false)
const newPlaylistName = ref('')
const currentPlaylist = ref(null)
const activeFilter = ref(null) // Active artist/genre filter
const filterScope = ref('library') // 'library' or 'global' - which library we're filtering

// Fullscreen section view
const expandedSection = ref(null) // 'albums', 'sources', 'playlists' or null

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

const goBack = () => {
  // If expanded section is open, close it first
  if (expandedSection.value) {
    expandedSection.value = null
    return
  }
  currentView.value = 'library'
  currentPlaylist.value = null
  library.clearCurrentArtist()
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
  filterScope.value = 'library'
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
  
  // Restore player state if available
  if (player.hasSavedState()) {
    await player.restoreState()
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
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: var(--tg-viewport-stable-height, 100dvh);
  max-height: var(--tg-viewport-stable-height, 100dvh);
  overflow: hidden;
  background-color: var(--spotify-black);
  color: var(--spotify-text);
}

/* One UI Large Header */
.oneui-header {
  flex-shrink: 0;
  padding: 8px 12px 10px;
  background: linear-gradient(180deg, var(--spotify-gray-dark) 0%, var(--spotify-black) 100%);
}

.header-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Left slot - EnrichmentStatus or Search field (mutually exclusive) */
.header-left-slot {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.header-left-slot.expanded {
  flex: 1;
  min-width: 0;
}

/* Header title */
.header-title-main {
  flex: 1;
  min-width: 0;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.5px;
  margin: 0;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-title-main:active {
  opacity: 0.7;
}

/* Search wrapper - fills center area */
.search-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
  height: 44px;
  background: var(--neu-bg);
  border-radius: 22px;
  padding: 4px 14px;
  gap: 10px;
  box-shadow: 
    inset 3px 3px 6px var(--neu-shadow-dark),
    inset -2px -2px 4px var(--neu-shadow-light);
  border: 1px solid rgba(255, 255, 255, 0.02);
}

.search-scope-btn {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: var(--xm-bg-surface);
  color: var(--spotify-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.search-scope-btn:active {
  transform: scale(0.9);
}

.search-scope-btn.global {
  background: var(--spotify-green);
  color: white;
  box-shadow: 0 2px 8px rgba(29, 185, 84, 0.4);
}

.search-content {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.search-tag {
  background: var(--spotify-green);
  color: white;
  padding: 5px 12px;
  border-radius: 14px;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  white-space: nowrap;
  box-shadow: 0 2px 6px rgba(29, 185, 84, 0.3);
}

.search-icon {
  flex-shrink: 0;
  color: var(--spotify-text-muted);
}

.search-input-inline {
  flex: 1;
  min-width: 60px;
  border: none;
  background: transparent;
  color: var(--spotify-text);
  font-size: 16px;
  outline: none;
  padding: 0;
  height: 36px;
}

.search-input-inline::placeholder {
  color: var(--spotify-text-muted);
}

.search-toggle {
  flex-shrink: 0;
}

/* Animations */

/* Fade slide animation for title/search swap */
.fade-slide-enter-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: absolute;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* Icon flip animation */
.icon-flip-enter-active,
.icon-flip-leave-active {
  transition: all 0.2s ease;
}

.icon-flip-enter-from {
  opacity: 0;
  transform: rotate(-90deg) scale(0.8);
}

.icon-flip-leave-to {
  opacity: 0;
  transform: rotate(90deg) scale(0.8);
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
  width: 44px;
  height: 44px;
  border: none;
  background: var(--neu-bg);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--spotify-text);
  transition: all 0.2s ease;
  box-shadow: 
    5px 5px 10px var(--neu-shadow-dark),
    -2px -2px 6px var(--neu-shadow-light);
}

.icon-btn:active {
  box-shadow: 
    inset 3px 3px 6px var(--neu-shadow-dark),
    inset -2px -2px 4px var(--neu-shadow-light);
  transform: scale(0.95);
}

/* Compact Header */
.compact-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: var(--spotify-gray-dark);
  gap: 10px;
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
  flex: 1 1 0;
  min-height: 0;  /* Allow flex shrinking for proper overflow */
  height: 0; /* Force flex to control height */
  overflow-y: overlay; /* Overlay scrollbar - doesn't take layout space */
  overflow-x: hidden;  /* Prevent horizontal scrollbar */
  position: relative;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.3) transparent;
  scrollbar-gutter: auto;
  -webkit-overflow-scrolling: touch; /* Smooth scrolling on iOS */
}

/* Content scrollbar - overlay thin style */
.content::-webkit-scrollbar {
  width: 6px !important;
  background: transparent !important;
}

.content::-webkit-scrollbar-track {
  background: transparent !important;
}

.content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.25) !important;
  border-radius: 3px !important;
}

.content::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.45) !important;
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
  gap: 10px;
  padding: 10px 12px;
  margin-bottom: 4px;
}

.liked-cover {
  width: 60px;
  height: 60px;
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
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
  color: white;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4) !important;
}

.liked-tab.active {
  color: #ef4444 !important;
}

.liked-tab svg {
  fill: currentColor;
}

/* Active filter indicator */
.active-filter {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  margin: 6px 10px;
  background: var(--spotify-green);
  border-radius: 6px;
  color: black;
  font-size: 14px;
  font-weight: 500;
}

.active-filter .global-badge {
  font-size: 16px;
}

.clear-filter-btn {
  width: 28px;
  height: 28px;
  margin-left: auto;
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

/* Search Results */
.search-results {
  padding: 0 4px;
}

.search-section {
  margin-bottom: 20px;
}

.search-section-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--spotify-text-muted);
  padding: 12px 12px 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.search-artists-list,
.search-albums-list,
.search-playlists-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.search-artist-item,
.search-album-item,
.search-playlist-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--xm-bg-card);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.search-artist-item:active,
.search-album-item:active,
.search-playlist-item:active {
  transform: scale(0.98);
  opacity: 0.8;
}

.search-artist-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--spotify-gray) 0%, var(--spotify-gray-dark) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.search-artist-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-initials {
  font-size: 16px;
  font-weight: 700;
  color: var(--spotify-text-muted);
}

.search-artist-info,
.search-album-info,
.search-playlist-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.search-artist-name,
.search-album-name,
.search-playlist-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--spotify-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-artist-count,
.search-album-artist,
.search-playlist-count {
  font-size: 13px;
  color: var(--spotify-text-muted);
}

.search-album-cover,
.search-playlist-cover {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  background: linear-gradient(135deg, var(--spotify-gray) 0%, var(--spotify-gray-dark) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.search-album-cover img,
.search-playlist-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.search-item-arrow {
  flex-shrink: 0;
  color: var(--spotify-text-muted);
  opacity: 0.5;
}

.see-all-btn {
  display: block;
  width: calc(100% - 24px);
  margin: 12px auto;
  padding: 12px;
  border: none;
  border-radius: 12px;
  background: var(--spotify-gray);
  color: var(--spotify-text);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.see-all-btn:active {
  transform: scale(0.98);
  background: var(--spotify-gray-light);
}

/* Scope toggle for library/global */
.scope-toggle {
  display: flex;
  gap: 6px;
  padding: 8px 10px;
  background: var(--spotify-black);
  position: sticky;
  top: 0;
  z-index: 10;
}

.scope-btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  border-radius: 20px;
  background: var(--spotify-gray);
  color: var(--spotify-text-secondary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.scope-btn.active {
  background: var(--spotify-green);
  color: black;
}

.scope-btn:active {
  transform: scale(0.97);
}

/* List items */
.list-section {
  padding: 8px 0;
}

.list-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  gap: 10px;
  cursor: pointer;
  transition: background 0.15s;
}

.list-item:active {
  background: var(--spotify-gray);
}

.list-item-avatar {
  width: 40px;
  height: 40px;
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
  padding: 0 0 8px 0;
}

/* Quick Access Grid - horizontal scroll */
.quick-grid {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}

.quick-grid::-webkit-scrollbar {
  display: none;
}

.quick-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--xm-bg-elevated);
  border-radius: var(--neu-radius-md);
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light);
  border: 1px solid rgba(255, 255, 255, 0.02);
  flex-shrink: 0;
}

.quick-item:active {
  box-shadow: 
    inset 3px 3px 6px var(--neu-shadow-inset-dark),
    inset -2px -2px 4px var(--neu-shadow-inset-light);
  transform: scale(0.96);
}

.quick-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--neu-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--xm-accent) 0%, var(--xm-accent-dark) 100%);
  color: white;
  flex-shrink: 0;
  box-shadow: 0 3px 8px var(--xm-accent-glow);
}

.quick-icon svg {
  width: 20px;
  height: 20px;
}

.quick-icon.liked-icon {
  background: linear-gradient(135deg, var(--xm-accent) 0%, var(--xm-accent-dark) 100%);
}

.quick-icon.history-icon {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  box-shadow: 0 3px 8px rgba(139, 92, 246, 0.3);
}

.quick-icon.playlist-icon {
  background: linear-gradient(135deg, var(--xm-secondary) 0%, #0891b2 100%);
  box-shadow: 0 3px 8px var(--xm-secondary-glow);
}

.quick-icon.allpl-icon {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  box-shadow: 0 3px 8px rgba(59, 130, 246, 0.3);
}

.quick-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--xm-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100px;
}

/* Feed Sections */
.feed-section {
  margin-bottom: 16px;
}

.feed-section-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--spotify-text);
  padding: 0 12px;
  margin-bottom: 8px;
}

.horizontal-scroll {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  scroll-snap-type: x proximity;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  padding: 4px 0;
  padding-left: 12px;
  padding-right: 12px;
}

.horizontal-scroll::-webkit-scrollbar {
  display: none;
}

.horizontal-scroll::after {
  content: '';
  flex-shrink: 0;
  width: 4px;
}

.scroll-spacer {
  display: none;
}

/* Feed Cards */
.feed-card {
  flex-shrink: 0;
  width: 110px;
  scroll-snap-align: none;
  cursor: pointer;
  text-align: center;
  transition: transform 0.15s ease;
}

.feed-card:active {
  transform: scale(0.94);
}

.feed-card-cover {
  width: 110px;
  height: 110px;
  background: var(--xm-bg-elevated);
  border-radius: var(--neu-radius-lg); 
  box-shadow: 
    5px 5px 10px var(--neu-shadow-dark),
    -3px -3px 6px var(--neu-shadow-light);
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 8px;
  padding: 3px;
  box-sizing: border-box;
  border: 1px solid rgba(255, 255, 255, 0.02);
}

/* Rounded image inside neomorphic frame */
.feed-card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: var(--neu-radius-md);
}

.feed-card-cover .feed-card-placeholder {
  font-size: 36px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.6);
}

.feed-card-cover .play-overlay {
  position: absolute;
  bottom: 8px;
  right: 8px;
  width: 42px;
  height: 42px;
  border-radius: var(--neu-radius-full);
  background: linear-gradient(145deg, var(--xm-accent), var(--xm-accent-dark));
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transform: translateY(8px);
  transition: all 0.2s ease;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.5),
    0 0 12px var(--xm-accent-glow);
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
  width: 24px;
  height: 24px;
  border-radius: var(--neu-radius-full);
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-accent);
}

.feed-card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--xm-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feed-card-subtitle {
  font-size: 11px;
  color: var(--xm-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

/* Artist Card */
.artist-card .feed-card-cover {
  border-radius: var(--neu-radius-full);
}

.artist-cover {
  border-radius: var(--neu-radius-full);
}

.artist-cover img {
  border-radius: var(--neu-radius-full);
}

.artist-initials {
  font-size: 32px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.8);
}

/* Playlist Card */
.playlist-cover {
  background: linear-gradient(135deg, var(--xm-secondary) 0%, #0891b2 100%);
  color: rgba(255, 255, 255, 0.9);
}

/* Genre Card */
.genre-card .feed-card-cover {
  position: relative;
}

.genre-cover {
  color: rgba(255, 255, 255, 0.9);
}

.genre-cover svg {
  width: 32px;
  height: 32px;
}

.genre-icon {
  opacity: 0.9;
}

.shuffle-badge {
  position: absolute;
  bottom: 6px;
  right: 6px;
  width: 22px;
  height: 22px;
  border-radius: var(--neu-radius-full);
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-accent);
}

.shuffle-badge svg {
  width: 13px;
  height: 13px;
}

/* Add Card */
.add-card {
  width: 100px;
}

.add-card .add-cover {
  width: 100px;
  height: 100px;
  background: var(--neu-bg);
  border: 2px dashed var(--spotify-gray-light);
  color: var(--spotify-text-muted);
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-dark),
    inset -1px -1px 3px var(--neu-shadow-light);
  box-sizing: border-box;
}

.add-card .add-cover svg {
  width: 32px;
  height: 32px;
  opacity: 0.6;
}

.add-card:active .add-cover {
  background: var(--spotify-gray);
  border-style: solid;
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
  padding: 8px 12px;
}

/* Playlist categories */
.playlist-category {
  margin-bottom: 14px;
}

.category-title {
  display: flex;
  align-items: center;
  font-size: 11px;
  font-weight: 600;
  color: var(--spotify-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
  padding: 0 2px;
}

.category-title.clickable {
  cursor: pointer;
  transition: color 0.15s;
}

.category-title.clickable:active {
  color: var(--spotify-green);
}

.section-arrow {
  margin-left: auto;
  opacity: 0.5;
}

.category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  padding: 0 2px;
}

.category-header .category-title {
  margin-bottom: 0;
  flex: 1;
}

/* Expanded section fullscreen view */
.expanded-section {
  position: fixed;
  inset: 0;
  background: var(--spotify-black);
  z-index: 60;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.expanded-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--spotify-gray-dark);
  flex-shrink: 0;
}

.expanded-title {
  flex: 1;
  font-size: 18px;
  font-weight: 600;
  color: var(--spotify-text);
}

.expanded-grid {
  flex: 1;
  overflow-y: overlay;
  scrollbar-gutter: auto;
  padding: 12px;
  padding-bottom: 120px; /* Space for MiniPlayer */
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  gap: 12px;
  align-content: start;
}

.empty-section {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  color: var(--spotify-text-secondary);
}

.empty-section .empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-section p {
  margin-bottom: 16px;
}

/* Slide up transition */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

.create-btn-small {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--spotify-gray);
  border: none;
  border-radius: 50%;
  color: var(--spotify-text);
  cursor: pointer;
  transition: all 0.15s;
}

.create-btn-small svg {
  width: 16px;
  height: 16px;
}

.create-btn-small:active {
  background: var(--spotify-green);
  color: black;
}

.system-playlists-grid {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scrollbar-width: none;
  padding-bottom: 4px;
}

.system-playlists-grid::-webkit-scrollbar {
  display: none;
}

.playlists-compact-list {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 4px 0 8px 12px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.playlists-compact-list::-webkit-scrollbar {
  display: none;
}

.empty-small {
  text-align: center;
  padding: 10px 10px;
  color: var(--spotify-text-secondary);
}

.empty-small p {
  margin-bottom: 6px;
  font-size: 12px;
}

/* System playlists (Liked, History) */
.system-playlist-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--xm-bg-elevated);
  border-radius: var(--neu-radius-md);
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light);
}

.system-playlist-item:active {
  background: var(--xm-bg-surface);
  transform: scale(0.97);
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark),
    inset -1px -1px 3px var(--neu-shadow-inset-light);
}

.system-playlist-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--neu-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.system-playlist-icon svg {
  width: 18px;
  height: 18px;
}

.system-playlist-icon.liked-gradient {
  background: linear-gradient(135deg, var(--xm-accent) 0%, var(--xm-accent-dark) 100%);
  box-shadow: 0 3px 10px var(--xm-accent-glow);
}

.system-playlist-icon.history-gradient {
  background: linear-gradient(135deg, #7c3aed 0%, #a78bfa 100%);
  box-shadow: 0 3px 10px rgba(124, 58, 237, 0.3);
}

.system-playlist-info {
  flex: 1;
  min-width: 0;
}

.system-playlist-title {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: var(--xm-text-primary);
  white-space: nowrap;
}

.system-playlist-count {
  display: block;
  font-size: 12px;
  color: var(--xm-text-muted);
}

.create-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px;
  border: 1px dashed var(--spotify-gray-light);
  border-radius: 8px;
  background: transparent;
  color: var(--spotify-text-secondary);
  font-size: 13px;
  cursor: pointer;
  margin-bottom: 12px;
  transition: all 0.15s;
}

.create-btn svg {
  width: 18px;
  height: 18px;
}

.create-btn:active {
  background: var(--spotify-gray);
  border-color: var(--spotify-green);
  color: var(--spotify-green);
}

/* Playlist view */
.playlist-view {
  padding: 16px;
}

.playlist-header-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
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
  overflow: hidden;
  flex-shrink: 0;
}

.playlist-cover.has-cover {
  background: transparent;
}

.playlist-cover .cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 4-image collage for playlists */
.cover-collage {
  width: 100%;
  height: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 1px;
}

.cover-collage .collage-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* If only 1-3 images, adjust layout */
.cover-collage .collage-img:only-child {
  grid-column: 1 / -1;
  grid-row: 1 / -1;
}

.playlist-meta {
  flex: 1;
  min-width: 0;
}

.playlist-artist {
  font-size: 12px;
  color: var(--spotify-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: block;
  margin-bottom: 2px;
}

.playlist-meta h2 {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.playlist-meta p {
  font-size: 13px;
  color: var(--spotify-text-muted);
}

.play-all-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--spotify-green);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: black;
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
  transition: transform 0.2s, box-shadow 0.2s;
  flex-shrink: 0;
}

.play-all-btn svg {
  width: 22px;
  height: 22px;
}

.play-all-btn:active {
  transform: scale(0.95);
}

.download-playlist-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--spotify-gray);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--spotify-text-secondary);
  transition: transform 0.15s, background 0.15s;
  flex-shrink: 0;
}

.download-playlist-btn svg {
  width: 18px;
  height: 18px;
}

.download-playlist-btn:active {
  transform: scale(0.95);
  background: var(--spotify-gray-light);
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
  border-radius: 10px;
  padding: 3px;
  margin-bottom: 12px;
}

/* Bottom Tab Bar - Nokia XpressMusic Style (Icon only) */
.tab-bar {
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  gap: 12px;
  background: linear-gradient(180deg, var(--xm-bg-elevated) 0%, var(--xm-bg-deep) 100%);
  padding: 10px 16px max(10px, env(safe-area-inset-bottom));
  z-index: 50;
  border-top: 1px solid rgba(255, 255, 255, 0.03);
  box-shadow: 0 -4px 16px var(--neu-shadow-dark);
}

.tab-item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border: none;
  border-radius: var(--neu-radius-full);
  color: var(--xm-text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
  
  /* Nokia rubber button style */
  background: var(--rubber-bg);
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.5),
    -2px -2px 4px rgba(255, 255, 255, 0.03),
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    inset 0 -1px 0 rgba(0, 0, 0, 0.3);
  border: 1px solid var(--rubber-border);
}

.tab-item svg {
  width: 26px;
  height: 26px;
}

/* Rubber texture dots */
.tab-item::before {
  content: '';
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 3px;
  background: 
    radial-gradient(circle at 20% 50%, rgba(255,255,255,0.1) 0%, transparent 60%),
    radial-gradient(circle at 50% 50%, rgba(255,255,255,0.1) 0%, transparent 60%),
    radial-gradient(circle at 80% 50%, rgba(255,255,255,0.1) 0%, transparent 60%);
  border-radius: 2px;
  pointer-events: none;
}

.tab-item:active {
  transform: scale(0.92);
  background: var(--rubber-bg-pressed);
  box-shadow: 
    0 1px 2px rgba(0, 0, 0, 0.5),
    inset 0 2px 4px rgba(0, 0, 0, 0.4);
}

.tab-item.active {
  color: var(--xm-accent);
  background: linear-gradient(180deg, 
    #454545 0%, 
    #353535 50%, 
    #2a2a2a 100%);
  box-shadow: 
    0 3px 6px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.15),
    inset 0 -1px 0 rgba(0, 0, 0, 0.3),
    0 0 12px var(--xm-accent-glow);
}

.tab-item.active:active {
  transform: scale(0.94) translateY(1px);
  box-shadow: 
    0 1px 2px rgba(0, 0, 0, 0.5),
    inset 0 2px 4px rgba(0, 0, 0, 0.3);
}

.tab-item.active svg {
  filter: drop-shadow(0 0 6px var(--xm-accent-glow));
}

.tab-item svg {
  width: 20px;
  height: 20px;
  transition: filter 0.2s;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.modal {
  background: var(--xm-bg-elevated);
  padding: 24px;
  border-radius: var(--neu-radius-xl);
  width: 90%;
  max-width: 340px;
  box-shadow: 
    16px 16px 32px var(--neu-shadow-dark),
    -8px -8px 16px var(--neu-shadow-light),
    0 0 40px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.modal h3 {
  margin-bottom: 20px;
  font-size: 22px;
  font-weight: 700;
  color: var(--xm-text-primary);
}

.modal-input {
  width: 100%;
  padding: 16px 20px;
  border: none;
  border-radius: var(--neu-radius-lg);
  background: var(--xm-bg-deep);
  color: var(--xm-text-primary);
  font-size: 16px;
  margin-bottom: 24px;
  box-shadow: 
    inset 4px 4px 8px var(--neu-shadow-inset-dark),
    inset -2px -2px 4px var(--neu-shadow-inset-light);
  outline: none;
  transition: box-shadow 0.2s ease;
}

.modal-input:focus {
  box-shadow: 
    inset 4px 4px 8px var(--neu-shadow-inset-dark),
    inset -2px -2px 4px var(--neu-shadow-inset-light),
    0 0 0 2px var(--xm-accent-glow);
}

.modal-input::placeholder {
  color: var(--xm-text-muted);
}

.modal-actions {
  display: flex;
  gap: 14px;
}

.btn-primary, .btn-secondary {
  flex: 1;
  padding: 16px;
  border: none;
  border-radius: var(--neu-radius-lg);
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary {
  background: linear-gradient(145deg, var(--xm-accent-light), var(--xm-accent-dark));
  color: white;
  box-shadow: 
    5px 5px 10px var(--neu-shadow-dark),
    -2px -2px 5px var(--neu-shadow-light),
    0 0 16px var(--xm-accent-glow);
}

.btn-primary:active {
  transform: scale(0.97);
  box-shadow: 
    inset 3px 3px 6px rgba(0, 0, 0, 0.4),
    0 0 12px var(--xm-accent-glow);
}

.btn-secondary {
  background: var(--xm-bg-surface);
  color: var(--xm-text-primary);
  box-shadow: 
    5px 5px 10px var(--neu-shadow-dark),
    -2px -2px 5px var(--neu-shadow-light);
}

.btn-secondary:active {
  transform: scale(0.97);
  box-shadow: 
    inset 3px 3px 6px var(--neu-shadow-inset-dark),
    inset -2px -2px 4px var(--neu-shadow-inset-light);
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

/* Load more button for infinite scroll */
.load-more-btn {
  display: block;
  width: calc(100% - 32px);
  margin: 16px auto;
  padding: 16px 24px;
  background: var(--xm-bg-elevated);
  color: var(--xm-text-primary);
  border: none;
  border-radius: var(--neu-radius-lg);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 
    5px 5px 10px var(--neu-shadow-dark),
    -3px -3px 6px var(--neu-shadow-light);
}

.load-more-btn:active {
  transform: scale(0.97);
  box-shadow: 
    inset 3px 3px 6px var(--neu-shadow-inset-dark),
    inset -2px -2px 4px var(--neu-shadow-inset-light);
}

/* Loading more indicator */
.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 24px;
  color: var(--xm-text-secondary);
  font-size: 14px;
}

/* Loading view (centered spinner) */
.loading-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 48px;
  color: var(--xm-text-secondary);
  font-size: 14px;
}

/* Artist view */
.artist-view {
  padding-bottom: 0;
}

.loading-spinner {
  width: 22px;
  height: 22px;
  border: 3px solid var(--xm-bg-hover);
  border-top-color: var(--xm-accent);
  border-radius: var(--neu-radius-full);
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
