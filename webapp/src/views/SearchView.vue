<template>
  <div class="search-view">
    <!-- Search Bar -->
    <div class="search-bar-wrapper">
      <SearchBar
        v-model="searchQuery"
        placeholder="Поиск по трекам, тегам #, артистам, плейлистам..."
        :loading="isLoading"
        @input="debouncedSearch"
        @clear="handleClear"
      />
    </div>

    <!-- Filter chips (when query is active) -->
    <div v-if="searchQuery.trim()" class="search-type-chips">
      <button 
        v-for="chip in filterChips" 
        :key="chip.id"
        class="type-chip"
        :class="{ active: activeFilter === chip.id }"
        @click="activeFilter = chip.id"
      >
        <span>{{ chip.label }}</span>
        <span v-if="getChipBadge(chip.id)" class="chip-badge">{{ getChipBadge(chip.id) }}</span>
      </button>
    </div>

    <!-- Search Results Mode -->
    <div v-if="searchQuery.trim()" class="search-results-container">
      <!-- Loading initial search results skeleton -->
      <div v-if="isInitialLoading" class="search-skeleton-list">
        <TrackSkeleton v-for="n in 8" :key="n" />
      </div>

      <template v-else>
        <!-- ==================== TAB: ALL ==================== -->
        <div v-if="activeFilter === 'all'" class="all-results-mode">
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
                @click="activeFilter = 'tracks'"
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
                @click="handlePlayTrack(track, topTracks, index)"
                @like="handleLikeTrack(track)"
                @menu="(e) => openMenu('track', track, 'search', e)"
                @download="handleDirectDownload(track)"
                @hdNotice="handleHdNotice"
                @addToLibrary="handleAddToLibrary(track)"
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
                @click="activeFilter = 'soundcloud'"
              >
                <span>Все {{ soundcloudResults.length }}</span>
                <ArrowRight :size="14" />
              </button>
            </div>
            
            <div class="sc-results-list">
              <div
                v-for="item in soundcloudResults.slice(0, 5)"
                :key="item.url"
                class="sc-track-item"
                @click="handleQuickPlaySoundCloud(item)"
              >
                <div class="sc-track-cover">
                  <img v-if="item.cover_url" :src="item.cover_url" alt="" loading="lazy" referrerpolicy="no-referrer" />
                  <Music v-else :size="20" />
                  <div v-if="importingTrackUrl === item.url" class="sc-track-loading">
                    <div class="spinner small"></div>
                  </div>
                  <div v-else class="sc-track-play">
                    <Play :size="14" fill="currentColor" />
                  </div>
                </div>
                <div class="sc-track-info">
                  <div class="sc-track-title" :title="item.title">{{ item.title }}</div>
                  <div class="sc-track-artist">{{ item.artist }}</div>
                </div>
                <div class="sc-track-actions">
                  <span v-if="item.duration" class="sc-track-duration">{{ formatDuration(item.duration) }}</span>
                  <button 
                    class="sc-add-btn" 
                    :disabled="importingTrackUrl === item.url"
                    @click.stop="handleQuickAddSoundCloud(item)"
                    title="Добавить в медиатеку"
                  >
                    <Plus :size="16" />
                  </button>
                </div>
              </div>
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
                @click="activeFilter = 'artists'"
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
                @click="goToArtist(artist.name || artist.artist)"
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
                @click="activeFilter = 'albums'"
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
                @click="goToAlbum(album.id)"
                @contextmenu.prevent="openMenu('album', album, 'search', $event)"
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
                @click="activeFilter = 'playlists'"
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
                @click="goToPlaylist(pl.id)"
                @contextmenu.prevent="openMenu('playlist', pl, 'search', $event)"
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

        <!-- ==================== TAB: TRACKS ==================== -->
        <div v-else-if="activeFilter === 'tracks'" class="tracks-results-mode">
          <!-- Initial loading skeleton when searching tracks -->
          <div v-if="isTracksSearching && allTracksList.length === 0" class="search-skeleton-list">
            <TrackSkeleton v-for="n in 8" :key="n" />
          </div>

          <!-- Empty state when all track sources are exhausted -->
          <div v-else-if="!isTracksSearching && !isFriendsLoading && !isGlobalLoading && allTracksList.length === 0" class="no-results-box">
            <p class="no-results-text">Треки не найдены</p>
            <p class="no-results-hint">Попробуйте изменить поисковый запрос или выбрать другой тег</p>
          </div>

          <template v-else>
            <!-- 1. My Library Tracks -->
            <section v-if="libraryResults.length > 0" class="result-section">
              <div class="section-header">
                <span class="section-title">
                  <Music :size="16" /> Моя библиотека
                </span>
                <span class="section-count">
                  {{ libraryResults.length }}<template v-if="libraryTotal > libraryResults.length"> из {{ libraryTotal }}</template>
                </span>
              </div>
              <div class="track-results-list">
                <TrackItem
                  v-for="(track, index) in libraryResults"
                  :key="track.id"
                  :track="track"
                  :isPlaying="playerStore.currentTrack?.id === track.id"
                  :isLiked="libraryStore.isTrackLiked(track.id)"
                  :showAddToLibrary="false"
                  :inLibrary="true"
                  @click="handlePlayTrack(track, libraryResults, index)"
                  @like="handleLikeTrack(track)"
                  @menu="(e) => openMenu('track', track, 'search', e)"
                  @download="handleDirectDownload(track)"
                  @hdNotice="handleHdNotice"
                />
              </div>
              <button 
                v-if="hasMoreLibrary" 
                class="load-more-btn" 
                :disabled="isLibraryLoadingMore" 
                @click="loadMoreLibrary"
              >
                <div v-if="isLibraryLoadingMore" class="spinner small"></div>
                <span>{{ isLibraryLoadingMore ? 'Загрузка...' : `Показать ещё (${libraryResults.length} из ${libraryTotal})` }}</span>
              </button>
            </section>

            <!-- 2. Friends' Tracks -->
            <section v-if="friendsResults.length > 0" class="result-section">
              <div class="section-header friends-section">
                <span class="section-title">
                  <Users :size="16" /> У друзей
                </span>
                <span class="section-count">
                  {{ friendsResults.length }}<template v-if="friendsTotal > friendsResults.length"> из {{ friendsTotal }}</template>
                </span>
              </div>
              <div class="track-results-list">
                <TrackItem
                  v-for="(track, index) in friendsResults"
                  :key="'friends-' + track.id"
                  :track="track"
                  :isPlaying="playerStore.currentTrack?.id === track.id"
                  :isLiked="libraryStore.isTrackLiked(track.id)"
                  :showAddToLibrary="true"
                  :inLibrary="Boolean(track.in_library || libraryStore.isInLibrary(track.id))"
                  @click="handlePlayTrack(track, allTracksList, index)"
                  @like="handleLikeTrack(track)"
                  @menu="(e) => openMenu('track', track, 'search', e)"
                  @download="handleDirectDownload(track)"
                  @hdNotice="handleHdNotice"
                  @addToLibrary="handleAddToLibrary(track)"
                />
              </div>
              <button 
                v-if="hasMoreFriends" 
                class="load-more-btn" 
                :disabled="isFriendsLoadingMore" 
                @click="loadMoreFriends"
              >
                <div v-if="isFriendsLoadingMore" class="spinner small"></div>
                <span>{{ isFriendsLoadingMore ? 'Загрузка...' : 'Показать ещё у друзей' }}</span>
              </button>
            </section>

            <!-- Loading friends -->
            <div v-if="isFriendsLoading" class="section-loading-indicator">
              <div class="spinner small"></div>
              <span>Поиск у друзей...</span>
            </div>

            <!-- 3. Global Network Tracks -->
            <section v-if="globalResults.length > 0" class="result-section">
              <div class="section-header global-section">
                <span class="section-title">
                  <Globe :size="16" /> Общая сеть
                </span>
                <span class="section-count">
                  {{ globalResults.length }}<template v-if="globalTotal > globalResults.length"> из {{ globalTotal }}</template>
                </span>
              </div>
              <div class="track-results-list">
                <TrackItem
                  v-for="(track, index) in globalResults"
                  :key="'global-' + track.id"
                  :track="track"
                  :isPlaying="playerStore.currentTrack?.id === track.id"
                  :isLiked="libraryStore.isTrackLiked(track.id)"
                  :showAddToLibrary="true"
                  :inLibrary="Boolean(track.in_library || libraryStore.isInLibrary(track.id))"
                  @click="handlePlayTrack(track, allTracksList, index)"
                  @like="handleLikeTrack(track)"
                  @menu="(e) => openMenu('track', track, 'search', e)"
                  @download="handleDirectDownload(track)"
                  @hdNotice="handleHdNotice"
                  @addToLibrary="handleAddToLibrary(track)"
                />
              </div>
              <button 
                v-if="hasMoreGlobal" 
                class="load-more-btn" 
                :disabled="isGlobalLoadingMore" 
                @click="loadMoreGlobal"
              >
                <div v-if="isGlobalLoadingMore" class="spinner small"></div>
                <span>{{ isGlobalLoadingMore ? 'Загрузка...' : 'Показать ещё в общей сети' }}</span>
              </button>
            </section>

            <!-- Loading global -->
            <div v-if="isGlobalLoading" class="section-loading-indicator">
              <div class="spinner small"></div>
              <span>Поиск в общей сети...</span>
            </div>
          </template>
        </div>

        <!-- ==================== TAB: ARTISTS ==================== -->
        <div v-else-if="activeFilter === 'artists'" class="artists-results-mode">
          <div class="section-header">
            <span class="section-title">
              <Users :size="18" /> Артисты
            </span>
            <span class="section-count">{{ artistsResults.length }}</span>
          </div>
          <div v-if="artistsResults.length > 0" class="artists-grid">
            <div 
              v-for="artist in artistsResults" 
              :key="artist.name || artist.artist"
              class="feed-card artist-card"
              @click="goToArtist(artist.name || artist.artist)"
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
          <div v-else-if="!isArtistsSearching" class="no-results-box">
            <p class="no-results-text">Артисты не найдены</p>
            <p class="no-results-hint">Попробуйте изменить поисковый запрос</p>
          </div>
        </div>

        <!-- ==================== TAB: SOUNDCLOUD ==================== -->
        <div v-else-if="activeFilter === 'soundcloud'" class="soundcloud-results-mode">
          <div class="section-header">
            <span class="section-title">
              <span class="sc-badge">SC</span> SoundCloud (Глобальный поиск)
            </span>
            <span class="section-count">{{ soundcloudResults.length }}</span>
          </div>

          <div v-if="isSoundCloudSearching" class="section-loading-indicator">
            <div class="spinner small"></div>
            <span>Поиск на SoundCloud...</span>
          </div>

          <div v-else-if="soundcloudResults.length > 0" class="sc-results-list full-list">
            <div
              v-for="item in soundcloudResults"
              :key="item.url"
              class="sc-track-item"
              @click="handleQuickPlaySoundCloud(item)"
            >
              <div class="sc-track-cover">
                <img v-if="item.cover_url" :src="item.cover_url" alt="" loading="lazy" referrerpolicy="no-referrer" />
                <Music v-else :size="20" />
                <div v-if="importingTrackUrl === item.url" class="sc-track-loading">
                  <div class="spinner small"></div>
                </div>
                <div v-else class="sc-track-play">
                  <Play :size="14" fill="currentColor" />
                </div>
              </div>
              <div class="sc-track-info">
                <div class="sc-track-title" :title="item.title">{{ item.title }}</div>
                <div class="sc-track-artist">{{ item.artist }}</div>
              </div>
              <div class="sc-track-actions">
                <span v-if="item.duration" class="sc-track-duration">{{ formatDuration(item.duration) }}</span>
                <button 
                  class="sc-add-btn" 
                  :disabled="importingTrackUrl === item.url"
                  @click.stop="handleQuickAddSoundCloud(item)"
                  title="Добавить в медиатеку"
                >
                  <Plus :size="16" />
                </button>
              </div>
            </div>

            <!-- Load More SoundCloud Button -->
            <div class="sc-load-more-wrap">
              <button 
                v-if="soundcloudResults.length < 60"
                class="sc-load-more-btn"
                :disabled="isLoadingMoreSoundCloud"
                @click="loadMoreSoundCloud"
              >
                <div v-if="isLoadingMoreSoundCloud" class="spinner small"></div>
                <template v-else>Загрузить ещё (до 60)</template>
              </button>
              <span v-else class="sc-end-notice">Показаны 60 лучших результатов SoundCloud</span>
            </div>
          </div>

          <div v-else-if="!isSoundCloudSearching" class="no-results-box">
            <p class="no-results-text">На SoundCloud ничего не найдено</p>
          </div>
        </div>

        <!-- ==================== TAB: ALBUMS ==================== -->
        <div v-else-if="activeFilter === 'albums'" class="albums-results-mode">
          <div class="section-header">
            <span class="section-title">
              <Disc3 :size="18" /> Альбомы
            </span>
            <span class="section-count">{{ albumsResults.length }}</span>
          </div>
          <div v-if="albumsResults.length > 0" class="albums-grid">
            <div 
              v-for="album in albumsResults" 
              :key="album.id"
              class="feed-card"
              @click="goToAlbum(album.id)"
              @contextmenu.prevent="openMenu('album', album, 'search', $event)"
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
          <div v-else-if="!isAlbumsSearching" class="no-results-box">
            <p class="no-results-text">Альбомы не найдены</p>
            <p class="no-results-hint">Попробуйте изменить поисковый запрос</p>
          </div>
        </div>

        <!-- ==================== TAB: PLAYLISTS ==================== -->
        <div v-else-if="activeFilter === 'playlists'" class="playlists-results-mode">
          <div class="section-header">
            <span class="section-title">
              <Folder :size="18" /> Плейлисты
            </span>
            <span class="section-count">{{ playlistsResults.length }}</span>
          </div>
          <div v-if="playlistsResults.length > 0" class="playlists-grid">
            <div 
              v-for="pl in playlistsResults" 
              :key="pl.id"
              class="feed-card"
              @click="goToPlaylist(pl.id)"
              @contextmenu.prevent="openMenu('playlist', pl, 'search', $event)"
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
          <div v-else-if="!isPlaylistsSearching" class="no-results-box">
            <p class="no-results-text">Плейлисты не найдены</p>
            <p class="no-results-hint">Попробуйте изменить поисковый запрос</p>
          </div>
        </div>

        <!-- Global Empty Results (All categories empty) -->
        <div v-if="noResults" class="no-results-box">
          <p class="no-results-text">Ничего не найдено по запросу «{{ searchQuery }}»</p>
          <p class="no-results-hint">Попробуйте ввести другой тег, название трека, исполнителя или плейлиста</p>
        </div>
      </template>
    </div>

    <!-- ==================== EXPLORE MODE: DYNAMIC TAGS GRID ==================== -->
    <div v-else class="search-explore-container">
      <div class="explore-header">
        <div class="explore-title-row">
          <div class="title-with-icon">
            <Hash :size="20" class="explore-icon" />
            <h2 class="explore-heading">Обзор по тегам</h2>
          </div>
          <!-- Scope switcher -->
          <div class="tag-scope-tabs">
            <button 
              class="scope-tab" 
              :class="{ active: tagScope === 'library' }"
              @click="switchScope('library')"
            >
              Мои теги
            </button>
            <button 
              class="scope-tab" 
              :class="{ active: tagScope === 'global' }"
              @click="switchScope('global')"
            >
              Все теги
            </button>
          </div>
        </div>
        <p class="explore-subheading">Нажмите на любой тег, чтобы открыть подборку музыки</p>
      </div>

      <!-- Loading tags skeleton -->
      <div v-if="loadingTags && tags.length === 0" class="tags-loading-grid">
        <div v-for="n in 8" :key="n" class="tag-tile-skeleton">
          <div class="skeleton-tag-title"></div>
          <div class="skeleton-tag-count"></div>
        </div>
      </div>

      <!-- Tags Grid -->
      <div v-else class="tags-grid">
        <div 
          v-for="tag in displayTags" 
          :key="tag.name"
          class="tag-tile"
          :style="{ background: getTagGradient(tag.name) }"
          @click="handleTagClick(tag.name)"
        >
          <div class="tag-info">
            <span class="tag-name">#{{ tag.name }}</span>
            <span v-if="tag.track_count > 0" class="tag-count">
              {{ tag.track_count }} {{ formatTrackCount(tag.track_count) }}
            </span>
          </div>

          <!-- Decorative Hash watermark -->
          <div class="tag-watermark">
            <Hash :size="48" stroke-width="2.5" />
          </div>

          <!-- Quick play mix button -->
          <button 
            v-if="tag.track_count > 0"
            class="tag-play-btn"
            @click.stop="handlePlayTagMix(tag.name)"
            title="Слушать микс по тегу"
          >
            <Play :size="16" fill="currentColor" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, onActivated } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { usePlayerStore } from '@/stores/player'
import { useUIStore } from '@/stores/ui'
import { 
  useContextMenu, 
  useDebouncedSearch, 
  useTrackSearch, 
  useTrackActions, 
  useTrackSync 
} from '@/composables'
import api, { tracksApi, artistsApi, albumsApi, playlistsApi, ingestionApi } from '@/api/client'
import SearchBar from '@/components/ui/SearchBar.vue'
import TrackItem from '@/components/TrackItem.vue'
import TrackSkeleton from '@/components/TrackSkeleton.vue'
import { getCoverUrl, CoverSize, formatDuration } from '@/utils'
import { 
  Music, 
  Hash, 
  Play, 
  Users, 
  Disc3,
  Globe, 
  Folder, 
  ArrowRight,
  Plus 
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const libraryStore = useLibraryStore()
const playerStore = usePlayerStore()
const uiStore = useUIStore()
const { openMenu } = useContextMenu()
const { handleDirectDownload, handleHdNotice } = useTrackActions()

// Input & Debounce
const { 
  query: searchQuery, 
  debouncedQuery, 
  search: debouncedSearch, 
  clear: clearSearchInput, 
  setQuery 
} = useDebouncedSearch()

const activeFilter = ref('all')

// ─── 3-Tier Track Search Composable ───
const {
  searchQuery: trackSearchQuery,
  libraryResults,
  friendsResults,
  globalResults,
  isSearching: isTracksSearching,
  isFriendsLoading,
  isGlobalLoading,
  isFriendsLoadingMore,
  isGlobalLoadingMore,
  libraryPage,
  libraryTotal,
  friendsTotal,
  globalTotal,
  hasMoreLibrary,
  hasMoreFriends,
  hasMoreGlobal,
  isLibraryLoadingMore,
  allResults: allTracksList,
  loadMoreLibrary,
  loadMoreFriends,
  loadMoreGlobal,
  clearSearch: clearTrackSearch,
  search: executeTrackSearch
} = useTrackSearch({ perPage: 40 })

// Auto-sync reactive track models
useTrackSync(libraryResults, { isLibraryList: true })
useTrackSync(friendsResults)
useTrackSync(globalResults)

// ─── Artists, Albums & Playlists Search State ───
const artistsResults = ref([])
const albumsResults = ref([])
const playlistsResults = ref([])
const isArtistsSearching = ref(false)
const isAlbumsSearching = ref(false)
const isPlaylistsSearching = ref(false)

// ─── SoundCloud External Search State ───
const soundcloudResults = ref([])
const isSoundCloudSearching = ref(false)
const isLoadingMoreSoundCloud = ref(false)
const importingTrackUrl = ref(null)

const searchSoundCloud = async (query, limit = 30) => {
  const cleanQ = query.replace(/^#/, '').trim()
  if (!cleanQ || cleanQ.length < 2) {
    soundcloudResults.value = []
    return
  }

  isSoundCloudSearching.value = true
  try {
    const res = await ingestionApi.search(cleanQ, 'soundcloud', limit)
    soundcloudResults.value = res.data || []
  } catch (e) {
    console.error('Failed to search SoundCloud:', e)
    soundcloudResults.value = []
  } finally {
    isSoundCloudSearching.value = false
  }
}

const loadMoreSoundCloud = async () => {
  const cleanQ = searchQuery.value.replace(/^#/, '').trim()
  if (!cleanQ || isLoadingMoreSoundCloud.value) return
  isLoadingMoreSoundCloud.value = true
  try {
    const targetLimit = Math.min(60, soundcloudResults.value.length + 30)
    const res = await ingestionApi.search(cleanQ, 'soundcloud', targetLimit)
    soundcloudResults.value = res.data || []
  } catch (e) {
    console.error('Failed to load more from SoundCloud:', e)
  } finally {
    isLoadingMoreSoundCloud.value = false
  }
}

const handleQuickPlaySoundCloud = async (scTrack) => {
  if (importingTrackUrl.value) return
  importingTrackUrl.value = scTrack.url

  try {
    const res = await ingestionApi.quickImport({
      url: scTrack.url,
      title: scTrack.title,
      artist: scTrack.artist,
      duration: scTrack.duration,
      cover_url: scTrack.cover_url,
    })

    const track = res.data?.track
    if (track) {
      playerStore.playTrack(track, [track], 0)
      libraryStore.fetchTracks({ refresh: true })
      uiStore.toast?.success('В эфире!', `${track.artist} — ${track.title}`)
    }
  } catch (e) {
    console.error('Failed to quick import track:', e)
    uiStore.toast?.error('Ошибка импорта', e.response?.data?.detail || 'Не удалось загрузить трек')
  } finally {
    importingTrackUrl.value = null
  }
}

const handleQuickAddSoundCloud = async (scTrack) => {
  if (importingTrackUrl.value) return
  importingTrackUrl.value = scTrack.url

  try {
    const res = await ingestionApi.quickImport({
      url: scTrack.url,
      title: scTrack.title,
      artist: scTrack.artist,
      duration: scTrack.duration,
      cover_url: scTrack.cover_url,
    })

    const track = res.data?.track
    if (track) {
      libraryStore.fetchTracks({ refresh: true })
      uiStore.toast?.success('В медиатеке', `${track.artist} — ${track.title}`)
    }
  } catch (e) {
    console.error('Failed to quick import track:', e)
    uiStore.toast?.error('Ошибка импорта', e.response?.data?.detail || 'Не удалось загрузить трек')
  } finally {
    importingTrackUrl.value = null
  }
}

// Combined search loading state
const isLoading = computed(() => {
  return isTracksSearching.value || isArtistsSearching.value || isAlbumsSearching.value || isPlaylistsSearching.value || isSoundCloudSearching.value
})

const isInitialLoading = computed(() => {
  return isLoading.value && 
         allTracksList.value.length === 0 && 
         artistsResults.value.length === 0 && 
         albumsResults.value.length === 0 && 
         playlistsResults.value.length === 0 &&
         soundcloudResults.value.length === 0
})

// Dynamic Tags state
const tags = ref([])
const loadingTags = ref(false)
const tagScope = ref('library')

const filterChips = [
  { id: 'all', label: 'Все' },
  { id: 'tracks', label: 'Треки' },
  { id: 'soundcloud', label: 'SoundCloud' },
  { id: 'artists', label: 'Артисты' },
  { id: 'albums', label: 'Альбомы' },
  { id: 'playlists', label: 'Плейлисты' },
]

const totalTracksCount = computed(() => {
  const sum = (libraryTotal.value || 0) + (friendsTotal.value || 0) + (globalTotal.value || 0)
  return sum || allTracksList.value.length
})

const getChipBadge = (chipId) => {
  if (chipId === 'tracks') {
    return totalTracksCount.value > 0 ? totalTracksCount.value : null
  }
  if (chipId === 'soundcloud') {
    return soundcloudResults.value.length > 0 ? soundcloudResults.value.length : null
  }
  if (chipId === 'artists') {
    return artistsResults.value.length > 0 ? artistsResults.value.length : null
  }
  if (chipId === 'albums') {
    return albumsResults.value.length > 0 ? albumsResults.value.length : null
  }
  if (chipId === 'playlists') {
    return playlistsResults.value.length > 0 ? playlistsResults.value.length : null
  }
  return null
}

// Top tracks preview for the "All" tab (max 8 items across library, friends, global)
const topTracks = computed(() => {
  const list = []
  const seen = new Set()
  for (const group of [libraryResults.value, friendsResults.value, globalResults.value]) {
    for (const t of group) {
      if (!seen.has(t.id)) {
        seen.add(t.id)
        list.push(t)
        if (list.length >= 8) return list
      }
    }
  }
  return list
})

const noResults = computed(() => {
  if (isLoading.value || isFriendsLoading.value || isGlobalLoading.value) return false
  if (activeFilter.value === 'all') {
    return topTracks.value.length === 0 && artistsResults.value.length === 0 && albumsResults.value.length === 0 && playlistsResults.value.length === 0 && soundcloudResults.value.length === 0
  }
  if (activeFilter.value === 'tracks') {
    return allTracksList.value.length === 0
  }
  if (activeFilter.value === 'soundcloud') {
    return soundcloudResults.value.length === 0
  }
  if (activeFilter.value === 'artists') {
    return artistsResults.value.length === 0
  }
  if (activeFilter.value === 'albums') {
    return albumsResults.value.length === 0
  }
  if (activeFilter.value === 'playlists') {
    return playlistsResults.value.length === 0
  }
  return false
})

// Fallback presets if tags API returns empty
const fallbackPresets = [
  { name: 'phonk', track_count: 0 },
  { name: 'dnb', track_count: 0 },
  { name: 'lo-fi', track_count: 0 },
  { name: 'rock', track_count: 0 },
  { name: 'ambient', track_count: 0 },
  { name: 'hiphop', track_count: 0 },
  { name: 'synthwave', track_count: 0 },
  { name: 'chill', track_count: 0 },
  { name: 'nightdrive', track_count: 0 },
  { name: 'indie', track_count: 0 },
  { name: 'electronic', track_count: 0 },
  { name: 'workout', track_count: 0 },
]

const displayTags = computed(() => {
  if (tags.value.length > 0) return tags.value
  return fallbackPresets
})

// Deterministic vibrant HSL gradient generator for tags
const getTagGradient = (name) => {
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const h1 = Math.abs(hash % 360)
  const h2 = (h1 + 38) % 360
  return `linear-gradient(135deg, hsl(${h1}, 75%, 40%) 0%, hsl(${h2}, 80%, 25%) 100%)`
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

const loadTags = async () => {
  loadingTags.value = true
  try {
    const resp = await tracksApi.getTags(tagScope.value, 40)
    const list = resp.data || []
    if (list.length > 0) {
      tags.value = list
    } else if (tagScope.value === 'library') {
      const globalResp = await tracksApi.getTags('global', 40)
      tags.value = globalResp.data || []
    }
  } catch (e) {
    console.error('Failed to load tags:', e)
  } finally {
    loadingTags.value = false
  }
}

const switchScope = async (scope) => {
  if (tagScope.value === scope) return
  tagScope.value = scope
  tags.value = []
  await loadTags()
}

// ─── Search Execution ───
const goToAlbum = (albumId) => {
  router.push(`/album/${albumId}`)
}

const searchArtistsAndPlaylists = async (query) => {
  const cleanQ = query.replace(/^#/, '').trim()
  if (!cleanQ) {
    artistsResults.value = []
    albumsResults.value = []
    playlistsResults.value = []
    return
  }

  isArtistsSearching.value = true
  isAlbumsSearching.value = true
  isPlaylistsSearching.value = true

  // 1. Search Artists (Global network + fallback)
  try {
    const res = await artistsApi.getGlobal({ search: cleanQ, limit: 30 })
    artistsResults.value = res.data?.items || []
  } catch (e) {
    console.error('Failed to search artists:', e)
    const all = libraryStore.artists || []
    artistsResults.value = all.filter(a => (a.name || a.artist || '').toLowerCase().includes(cleanQ.toLowerCase()))
  } finally {
    isArtistsSearching.value = false
  }

  // 2. Search Albums (Global network + fallback)
  try {
    const res = await albumsApi.getGlobal({ search: cleanQ, limit: 30 })
    albumsResults.value = res.data?.items || []
  } catch (e) {
    console.error('Failed to search albums:', e)
    albumsResults.value = []
  } finally {
    isAlbumsSearching.value = false
  }

  // 3. Search Playlists (Personal + Global)
  try {
    const [myRes, globalRes] = await Promise.allSettled([
      playlistsApi.getAll({ search: cleanQ, limit: 20 }),
      playlistsApi.getGlobal({ search: cleanQ, limit: 20 })
    ])
    const myItems = myRes.status === 'fulfilled' ? (myRes.value.data?.items || myRes.value.data || []) : []
    const globalItems = globalRes.status === 'fulfilled' ? (globalRes.value.data?.items || globalRes.value.data || []) : []
    
    const seen = new Set()
    const combined = []
    for (const pl of [...myItems, ...globalItems]) {
      if (pl?.id && !seen.has(pl.id)) {
        seen.add(pl.id)
        combined.push(pl)
      }
    }
    playlistsResults.value = combined
  } catch (e) {
    console.error('Failed to search playlists:', e)
    const all = libraryStore.playlists || []
    playlistsResults.value = all.filter(p => (p.name || '').toLowerCase().includes(cleanQ.toLowerCase()))
  } finally {
    isPlaylistsSearching.value = false
  }
}

const performSearch = (q) => {
  const query = (q || '').trim()
  if (query) {
    trackSearchQuery.value = query
    executeTrackSearch()
    searchArtistsAndPlaylists(query)
    searchSoundCloud(query)
  } else {
    clearTrackSearch()
    artistsResults.value = []
    albumsResults.value = []
    playlistsResults.value = []
    soundcloudResults.value = []
  }
}

// Watch debounced query from user typing
watch(debouncedQuery, (newVal) => {
  performSearch(newVal)
})

const handleClear = () => {
  clearSearchInput()
  clearTrackSearch()
  artistsResults.value = []
  albumsResults.value = []
  playlistsResults.value = []
  soundcloudResults.value = []
  if (route.query.q || route.query.search || route.query.tag) {
    router.replace({ path: '/search', query: {} })
  }
}

// ─── Playback & Track Actions ───
const handlePlayTrack = (track, list, index) => {
  playerStore.playTrack(track, list || allTracksList.value, index >= 0 ? index : 0)
}

const handleLikeTrack = async (track) => {
  await libraryStore.toggleLike(track.id)
  track.is_liked = !track.is_liked
}

const handleAddToLibrary = async (track) => {
  try {
    const success = await libraryStore.addToLibrary(track.id)
    if (success) {
      track.in_library = true
      uiStore.toast.success('Добавлено', 'Трек добавлен в вашу библиотеку')
    }
  } catch (e) {
    uiStore.toast.error('Ошибка', 'Не удалось добавить трек')
  }
}

const goToArtist = (name) => {
  if (name) router.push(`/artist/${encodeURIComponent(name)}`)
}

const goToPlaylist = (id) => {
  if (id) router.push(`/playlist/${id}`)
}

const handleTagClick = (tagName) => {
  setQuery(`#${tagName}`, true)
}

const handlePlayTagMix = async (tagName) => {
  setQuery(`#${tagName}`, true)
  try {
    // 1. Try playing from library mix first
    const libRes = await api.get('/library', { params: { search: `#${tagName}`, per_page: 5 } }).catch(() => null)
    if (libRes?.data?.items?.length) {
      await playerStore.playShuffleAll('library', null, null, { search: `#${tagName}` })
      return
    }

    // 2. Otherwise play from global results for this tag
    const globalRes = await tracksApi.getGlobal({ search: `#${tagName}`, per_page: 30 })
    const items = globalRes.data?.items || []
    if (items.length > 0) {
      playerStore.playTrack(items[0], items, 0)
    } else {
      uiStore.toast.info('Тег', `По тегу #${tagName} треков пока нет`)
    }
  } catch (e) {
    console.error('Failed to play tag mix:', e)
  }
}

// ─── Route Synchronization ───
const applyRouteQuery = () => {
  const tagParam = route.query.tag
  const queryParam = route.query.q || route.query.search
  if (tagParam && typeof tagParam === 'string') {
    const formatted = tagParam.startsWith('#') ? tagParam : `#${tagParam}`
    setQuery(formatted, true)
  } else if (queryParam && typeof queryParam === 'string') {
    setQuery(queryParam, true)
  }
}

const handleResetState = (event) => {
  if (event.detail?.route === '/search') {
    handleClear()
    activeFilter.value = 'all'
  }
}

onMounted(() => {
  loadTags()
  applyRouteQuery()
  window.addEventListener('reset-view-state', handleResetState)
})

// Watch route query params for reactive updates (e.g. from tag clicks, browser navigation)
watch(
  () => [route.query.tag, route.query.q, route.query.search],
  () => {
    applyRouteQuery()
  }
)

onActivated(() => {
  applyRouteQuery()
})

onUnmounted(() => {
  window.removeEventListener('reset-view-state', handleResetState)
})
</script>

<style scoped>
.search-view {
  padding: 12px 16px 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.search-bar-wrapper {
  margin-bottom: 12px;
}

/* Type filter chips */
.search-type-chips {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scrollbar-width: none;
  padding-bottom: 8px;
  margin-bottom: 16px;
}

.search-type-chips::-webkit-scrollbar {
  display: none;
}

.type-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.05);
  color: var(--c-text-2, rgba(255, 255, 255, 0.8));
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.18s ease;
  font-family: inherit;
}

.type-chip.active {
  background: var(--c-accent, #1db954);
  color: #000;
  border-color: transparent;
}

.chip-badge {
  font-size: 11px;
  background: rgba(0, 0, 0, 0.2);
  padding: 1px 6px;
  border-radius: 10px;
  font-weight: 700;
}

.type-chip.active .chip-badge {
  background: rgba(0, 0, 0, 0.25);
  color: #000;
}

/* Results */
.result-section {
  margin-bottom: 28px;
}

.result-header, .section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.header-left, .section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  letter-spacing: -0.01em;
}

.header-icon {
  color: var(--c-accent, #1db954);
}

.result-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  margin: 0;
}

.result-count, .section-count {
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-3, rgba(255, 255, 255, 0.45));
}

.section-view-all {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--c-text-3, rgba(255, 255, 255, 0.6));
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 6px;
  transition: all 0.2s;
  font-family: inherit;
}

.section-view-all:hover {
  color: var(--c-accent, #1db954);
  transform: translateX(2px);
}

.track-results-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.section-header.friends-section,
.section-header.global-section {
  margin-top: 24px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.section-loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  font-size: 13px;
}

.load-more-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  margin-top: 12px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--c-accent, #1db954);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.load-more-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

.load-more-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Grids for Artists, Albums & Playlists tabs */
.artists-grid, .albums-grid, .playlists-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(136px, 1fr));
  gap: 14px;
  margin-top: 8px;
}

@media (min-width: 768px) {
  .artists-grid, .albums-grid, .playlists-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 16px;
  }
}

.artists-grid .feed-card,
.albums-grid .feed-card,
.playlists-grid .feed-card {
  width: 100%;
  flex: initial;
}

/* Horizontal scroll cards */
.horizontal-scroll {
  display: flex;
  gap: 14px;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 8px;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.horizontal-scroll::-webkit-scrollbar {
  display: none;
}

.feed-card {
  flex: 0 0 136px;
  width: 136px;
  cursor: pointer;
  scroll-snap-align: start;
  user-select: none;
  transition: transform 0.2s ease;
}

@media (min-width: 768px) {
  .feed-card {
    flex: 0 0 156px;
    width: 156px;
  }
}

.feed-card:hover {
  transform: translateY(-2px);
}

.feed-card:active {
  transform: scale(0.97);
}

.feed-card-cover {
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  background: var(--c-bg-2, #181818);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.4);
}

.feed-card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.feed-card:hover .feed-card-cover img {
  transform: scale(1.04);
}

.artist-card .artist-cover {
  border-radius: 50%;
}

.artist-initials {
  font-size: 24px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.8);
}

.artist-card .feed-card-title,
.artist-card .feed-card-subtitle {
  text-align: center;
}

.feed-card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.feed-card-subtitle {
  font-size: 12px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Card Tags */
.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.card-tags.center {
  justify-content: center;
}

.card-tag {
  font-size: 10px;
  font-weight: 500;
  color: var(--c-accent, #1db954);
  background: rgba(29, 185, 84, 0.12);
  padding: 1px 6px;
  border-radius: 4px;
  white-space: nowrap;
  letter-spacing: 0.2px;
  line-height: 14px;
}

/* Empty Results */
.no-results-box {
  text-align: center;
  padding: 48px 16px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
}

.no-results-text {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--c-text-1, #fff);
}

.no-results-hint {
  font-size: 13px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.45));
}

/* Explore: Tags Header */
.explore-header {
  margin-bottom: 16px;
}

.explore-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.explore-icon {
  color: var(--c-accent, #1db954);
}

.explore-heading {
  font-size: 20px;
  font-weight: 800;
  color: var(--c-text-1, #fff);
  margin: 0;
  letter-spacing: -0.01em;
}

.explore-subheading {
  font-size: 13px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  margin-top: 4px;
}

/* Scope tabs */
.tag-scope-tabs {
  display: flex;
  background: rgba(255, 255, 255, 0.08);
  padding: 3px;
  border-radius: 12px;
  gap: 2px;
}

.scope-tab {
  background: transparent;
  border: none;
  color: var(--c-text-3, rgba(255, 255, 255, 0.6));
  font-size: 12px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 9px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.scope-tab.active {
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
}

/* Tags Grid */
.tags-grid, .tags-loading-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

@media (min-width: 640px) {
  .tags-grid, .tags-loading-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }
}

@media (min-width: 1024px) {
  .tags-grid, .tags-loading-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
  }
}

.tag-tile {
  height: 96px;
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  user-select: none;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.tag-tile:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
}

.tag-tile:active {
  transform: scale(0.97);
}

.tag-info {
  display: flex;
  flex-direction: column;
  z-index: 1;
}

.tag-name {
  font-size: 16px;
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
}

.tag-count {
  font-size: 11px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.75);
  margin-top: 3px;
}

.tag-watermark {
  position: absolute;
  right: -8px;
  bottom: -8px;
  opacity: 0.18;
  transform: rotate(-15deg);
  color: #fff;
  pointer-events: none;
}

.tag-play-btn {
  position: absolute;
  right: 10px;
  bottom: 10px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transform: scale(0.85);
  transition: all 0.2s ease;
  z-index: 2;
  backdrop-filter: blur(4px);
}

.tag-tile:hover .tag-play-btn {
  opacity: 1;
  transform: scale(1);
}

.tag-play-btn:hover {
  background: var(--c-accent, #1db954);
  color: #000;
  border-color: transparent;
  transform: scale(1.1) !important;
}

/* Loading skeletons */
.search-skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tag-tile-skeleton {
  height: 96px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  padding: 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-sizing: border-box;
}

.skeleton-tag-title {
  height: 16px;
  width: 60%;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-tag-count {
  height: 10px;
  width: 35%;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.05);
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.15s;
}

@keyframes pulse {
  0%, 100% { opacity: 0.35; }
  50% { opacity: 0.75; }
}

/* SoundCloud Search Styles */
.sc-badge {
  background: #ff5500;
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.sc-results-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sc-results-list.full-list {
  margin-top: 12px;
}

.sc-track-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.sc-track-item:hover {
  background: rgba(255, 85, 0, 0.08);
  border-color: rgba(255, 85, 0, 0.25);
  transform: translateX(2px);
}

.sc-track-cover {
  position: relative;
  width: 44px;
  height: 44px;
  border-radius: 8px;
  overflow: hidden;
  background: #18181c;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.4);
}

.sc-track-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sc-track-play {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
  color: #ff5500;
}

.sc-track-item:hover .sc-track-play {
  opacity: 1;
}

.sc-track-loading {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
}

.sc-track-info {
  flex: 1;
  min-width: 0;
}

.sc-track-title {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sc-track-artist {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sc-track-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.sc-track-duration {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.sc-add-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-add-btn:hover:not(:disabled) {
  background: #ff5500;
  border-color: #ff5500;
  transform: scale(1.05);
}

.sc-add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sc-load-more-wrap {
  display: flex;
  justify-content: center;
  margin-top: 16px;
  margin-bottom: 24px;
}

.sc-load-more-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: rgba(255, 85, 0, 0.12);
  border: 1px solid rgba(255, 85, 0, 0.3);
  border-radius: 12px;
  color: #ff7700;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-load-more-btn:hover:not(:disabled) {
  background: #ff5500;
  color: #fff;
  border-color: #ff5500;
  box-shadow: 0 4px 16px rgba(255, 85, 0, 0.3);
}

.sc-load-more-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sc-end-notice {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.4);
}
</style>
