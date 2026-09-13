<template>
  <div class="user-profile-view">
    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
    </div>

    <!-- Private / Forbidden Profile -->
    <div v-else-if="isForbidden" class="empty-state private-profile">
      <div class="empty-icon"><Lock :size="56" /></div>
      <h2>Профиль скрыт</h2>
      <p>Пользователь ограничил доступ к своей медиатеке настройками приватности</p>
      <button class="btn-pill-secondary" @click="router.back()">
        Назад
      </button>
    </div>

    <!-- Error / Not Found -->
    <div v-else-if="error || !user" class="empty-state error-profile">
      <div class="empty-icon"><UserX :size="56" /></div>
      <h2>Пользователь не найден</h2>
      <p>{{ error || 'Не удалось загрузить данные пользователя' }}</p>
      <button class="btn-pill-secondary" @click="router.back()">
        Назад
      </button>
    </div>

    <!-- Normal Profile View -->
    <template v-else>
      <!-- Modern Spotify / Apple Music Profile Hero Card -->
      <div class="profile-hero-card">
        <div class="hero-ambient-glow" :style="ambientGlowStyle"></div>

        <!-- Left: Full-Height Avatar -->
        <div 
          class="hero-avatar" 
          :class="{ 'is-clickable': isSelf }"
          :style="avatarGradientStyle"
          @click="isSelf && openEditProfileModal()"
          :title="isSelf ? 'Нажмите, чтобы изменить аватарку' : ''"
        >
          <img 
            v-if="userAvatar" 
            :src="userAvatar" 
            alt="Avatar" 
            class="hero-avatar-img" 
          />
          <span v-else class="hero-avatar-initials">{{ getInitials(user) }}</span>
          <div v-if="isSelf" class="hero-avatar-edit-overlay">
            <Camera :size="26" />
            <span class="edit-avatar-text">Изменить</span>
          </div>
        </div>

        <!-- Right: Info, Nickname, Stats, Actions -->
        <div class="hero-body">
          <div class="hero-meta-top">
            <span class="hero-type-label">ПРОФИЛЬ</span>
            <span v-if="isSelf" class="self-badge">Вы</span>
            <span v-if="isSelf && user.hide_telegram_id" class="hidden-handle-badge" title="Скрыт от других пользователей">
              <EyeOff :size="11" /> скрыт
            </span>
          </div>

          <h1 class="hero-name" :title="user.display_name">{{ user.display_name }}</h1>

          <div class="hero-subline">
            <span v-if="user.username" class="hero-handle">@{{ user.username }}</span>
            <span v-if="user.username" class="stat-separator">•</span>
            <!-- Stats -->
            <button class="hero-stat-pill" @click="selectTab('tracks')" title="Смотреть треки">
              <span class="stat-num">{{ user.track_count }}</span>
              <span class="stat-label">{{ getTracksWord(user.track_count) }}</span>
            </button>
            <span class="stat-separator">•</span>
            <button class="hero-stat-pill" @click="selectTab('playlists')" title="Смотреть плейлисты">
              <span class="stat-num">{{ user.playlist_count }}</span>
              <span class="stat-label">{{ getPlaylistsWord(user.playlist_count) }}</span>
            </button>
            <span class="stat-separator">•</span>
            <div 
              class="hero-stat-pill"
              :class="{ 'clickable-stat': isSelf }"
              @click="isSelf && router.push('/friends')"
              :title="isSelf ? 'Перейти к кентам' : ''"
            >
              <span class="stat-num">{{ user.followers_count }}</span>
              <span class="stat-label">подписчиков</span>
            </div>

            <!-- External Connected Accounts Badges -->
            <template v-if="scAccount">
              <span class="stat-separator">•</span>
              <button class="hero-ext-badge sc-badge" @click="selectTab('soundcloud')" title="SoundCloud профиль">
                <span class="sc-badge-inline">SC</span>
                <span class="ext-badge-name">{{ scAccount.username }}</span>
              </button>
            </template>

            <template v-if="spAccount">
              <span class="stat-separator">•</span>
              <button class="hero-ext-badge sp-badge" @click="selectTab('spotify')" title="Spotify профиль">
                <Radio :size="12" class="sp-icon-inline" />
                <span class="ext-badge-name">{{ spAccount.display_name || spAccount.username }}</span>
              </button>
            </template>
          </div>

          <!-- Top-right absolute share button -->
          <button class="hero-share-corner-btn" @click="handleShare" title="Поделиться профилем">
            <Share2 :size="18" />
          </button>

          <!-- Action Buttons Bar -->
          <div class="hero-actions-bar">
            <!-- Unified Play & Shuffle Capsule -->
            <div class="action-buttons hero-play-capsule" v-if="user.track_count > 0">
              <button 
                class="action-btn play-btn" 
                @click="handlePlayUserLibrary"
                title="Слушать медиатеку"
              >
                <Play :size="19" fill="currentColor" />
              </button>
              <button 
                v-if="user.track_count > 1"
                class="action-btn shuffle-btn" 
                @click="handleShuffleUserLibrary"
                title="Перемешать медиатеку"
              >
                <Shuffle :size="17" />
              </button>
            </div>

            <!-- Follow button -->
            <button
              v-if="!isSelf"
              class="hero-pill-btn follow-btn"
              :class="{ 'is-following': isFollowing }"
              :disabled="followLoading"
              @click="toggleFollow"
              :title="isFollowing ? 'Отписаться' : 'Подписаться'"
            >
              <Check v-if="isFollowing" :size="18" />
              <UserPlus v-else :size="18" />
            </button>

            <!-- Edit Profile (if self) -->
            <button
              v-if="isSelf"
              class="hero-pill-btn edit-profile-btn"
              @click="openEditProfileModal"
              title="Редактировать профиль"
            >
              <Edit3 :size="18" />
            </button>

            <!-- Settings (if self) -->
            <button
              v-if="isSelf"
              class="hero-pill-btn"
              @click="router.push('/settings')"
              title="Настройки аккаунта"
            >
              <Settings :size="18" />
            </button>
          </div>
        </div>
      </div>

      <!-- Active Background Imports / Ingestion Panel for Profile (when viewing self) -->
      <div v-if="isSelf && tasksStore.hasActiveImports" class="profile-active-imports-panel">
        <div class="panel-section-header">
          <div class="panel-section-title">
            <CloudDownload :size="15" class="section-icon-pulse" />
            <span>Импорт медиатеки</span>
            <span class="panel-section-count">{{ tasksStore.activeMinimizedJobs.length }}</span>
          </div>
          <span class="panel-overall-progress">Общий прогресс: {{ tasksStore.overallProgress }}%</span>
        </div>

        <div class="panel-import-cards">
          <div
            v-for="item in tasksStore.activeMinimizedJobs"
            :key="item.job.id"
            class="profile-import-card"
            :class="[item.meta?.type || 'generic', item.job.status, { 'is-queue': item.meta?.isQueue }]"
            @click="handleRestoreJob(item.job.id)"
            :title="item.meta?.isQueue ? 'Очередь загрузки треков' : 'Нажмите, чтобы развернуть окно импорта'"
          >
            <!-- Top row: icon + title + progress + actions -->
            <div class="import-card-top">
              <div class="import-icon-badge">
                <div v-if="item.job.status === 'in_progress'" class="import-spinner"></div>
                <Check v-else-if="item.job.status === 'completed'" :size="14" class="import-status-glyph success" />
                <AlertCircle v-else :size="14" class="import-status-glyph error" />

                <Music2 v-if="item.meta?.type === 'exportify'" :size="13" class="import-type-glyph" />
                <CloudDownload v-else :size="13" class="import-type-glyph" />
              </div>

              <div class="import-main-info">
                <div class="import-name-row">
                  <span class="import-name" :title="item.job.title">{{ item.job.title }}</span>
                  <span class="import-pct-badge">
                    {{ item.job.progress_percent }}%
                  </span>
                </div>
                <div class="import-stats-row">
                  <span class="import-tracks-count">
                    {{ item.job.processed_tracks }} / {{ item.job.total_tracks }} треков
                  </span>
                </div>
              </div>

              <div class="import-actions" @click.stop>
                <button
                  v-if="!item.meta?.isQueue"
                  class="import-action-btn restore"
                  @click="handleRestoreJob(item.job.id)"
                  title="Развернуть"
                >
                  <Maximize2 :size="13" />
                </button>
                <button
                  v-if="item.job.status === 'in_progress'"
                  class="import-action-btn cancel"
                  @click="handleCancelJob(item.job.id)"
                  :title="item.meta?.isQueue ? 'Отменить очередь' : 'Отменить импорт'"
                >
                  <X :size="13" />
                </button>
              </div>
            </div>

            <!-- Subtext row -->
            <div class="import-subtext" :title="subtextFor(item.job)">
              {{ subtextFor(item.job) }}
            </div>

            <!-- Mini download bar if currently downloading audio file -->
            <div 
              v-if="item.job.download_percent !== null && item.job.download_percent !== undefined && item.job.status === 'in_progress'"
              class="import-download-bar"
            >
              <div class="import-download-fill" :style="{ width: `${item.job.download_percent}%` }"></div>
            </div>

            <!-- Overall progress line -->
            <div class="import-progress-bar">
              <div 
                class="import-progress-fill"
                :style="{ width: `${item.job.progress_percent}%` }"
                :class="{ completed: item.job.status === 'completed' }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Modern Single-Line Tab Bar -->
      <div class="user-tabs-bar">
        <button
          class="user-tab-btn"
          :class="{ active: activeTab === 'overview' }"
          @click="selectTab('overview')"
        >
          <Sparkles :size="16" />
          <span>Обзор</span>
        </button>

        <button
          class="user-tab-btn"
          :class="{ active: activeTab === 'tracks' }"
          @click="selectTab('tracks')"
        >
          <Music :size="16" />
          <span>Треки</span>
          <span v-if="user.track_count > 0" class="user-tab-badge">{{ user.track_count }}</span>
        </button>

        <button
          class="user-tab-btn"
          :class="{ active: activeTab === 'playlists' }"
          @click="selectTab('playlists')"
        >
          <Folder :size="16" />
          <span>Плейлисты</span>
          <span v-if="user.playlist_count > 0" class="user-tab-badge">{{ user.playlist_count }}</span>
        </button>

        <button
          v-if="overviewAlbums.length > 0 || activeTab === 'albums'"
          class="user-tab-btn"
          :class="{ active: activeTab === 'albums' }"
          @click="selectTab('albums')"
        >
          <Disc3 :size="16" />
          <span>Альбомы</span>
          <span v-if="overviewAlbums.length > 0" class="user-tab-badge">{{ overviewAlbums.length }}</span>
        </button>

        <!-- SoundCloud Tab -->
        <button
          v-if="scAccount && (scAccount.show_playlists || scAccount.show_tracks || isSelf)"
          class="user-tab-btn sc-tab-btn"
          :class="{ active: activeTab === 'soundcloud' }"
          @click="selectTab('soundcloud')"
        >
          <span class="sc-badge-inline">SC</span>
          <span>SoundCloud</span>
          <span v-if="scPlaylists.length + scTracks.length > 0" class="user-tab-badge sc-badge-num">
            {{ scPlaylists.length + scTracks.length }}
          </span>
        </button>

        <!-- Spotify Tab -->
        <button
          v-if="spAccount && (spAccount.show_playlists || isSelf)"
          class="user-tab-btn sp-tab-btn"
          :class="{ active: activeTab === 'spotify' }"
          @click="selectTab('spotify')"
        >
          <Radio :size="16" />
          <span>Spotify</span>
          <span v-if="spPlaylists.length > 0" class="user-tab-badge sp-badge-num">
            {{ spPlaylists.length }}
          </span>
        </button>
      </div>

      <!-- Overview Tab Content -->
      <div v-show="activeTab === 'overview'" class="tab-pane overview-pane">
        <!-- Loading overview skeletons -->
        <div v-if="loadingOverview" class="overview-loading">
          <section class="profile-section">
            <div class="section-header">
              <div class="skeleton-section-title"></div>
            </div>
            <div class="overview-grid">
              <div v-for="i in 6" :key="i" class="feed-card-skeleton">
                <div class="skeleton-feed-cover"></div>
                <div class="skeleton-feed-title"></div>
                <div class="skeleton-feed-sub"></div>
              </div>
            </div>
          </section>
        </div>

        <template v-else>
          <!-- Section 1: Playlists Grid -->
          <section v-if="overviewPlaylists.length > 0" class="profile-section">
            <div class="section-header">
              <h2 class="section-title clickable" @click="selectTab('playlists')" title="Перейти в плейлисты">Плейлисты</h2>
              <button class="section-link" @click="selectTab('playlists')">Все {{ user.playlist_count || overviewPlaylists.length }}</button>
            </div>
            <div class="overview-grid">
              <div 
                v-for="pl in overviewPlaylists.slice(0, 12)" 
                :key="pl.id" 
                class="feed-card"
                @click="goToPlaylist(pl)"
                @contextmenu.prevent="handlePlaylistContextMenu(pl, $event)"
                v-longpress="(e) => handlePlaylistContextMenu(pl, e)"
              >
                <div class="feed-card-cover" :style="getPlaylistCoverStyle(pl)">
                  <img 
                    v-if="pl.covers?.length" 
                    :src="getCoverUrl(pl.covers[0], CoverSize.MEDIUM)" 
                    alt=""
                    loading="lazy"
                  />
                  <Folder v-else :size="36" />
                  <button 
                    v-if="pl.track_count > 0" 
                    class="play-overlay" 
                    @click.stop="shufflePlaylist(pl)"
                    title="Слушать"
                  >
                    <Play :size="18" fill="currentColor" />
                  </button>
                </div>
                <div class="feed-card-info">
                  <div class="feed-card-title">{{ pl.name }}</div>
                  <div class="feed-card-subtitle">{{ pl.track_count }} {{ getTracksWord(pl.track_count) }}</div>
                </div>
              </div>
            </div>
          </section>

          <!-- Section 2: Albums Grid -->
          <section v-if="overviewAlbums.length > 0" class="profile-section">
            <div class="section-header">
              <h2 class="section-title clickable" @click="selectTab('albums')" title="Перейти в альбомы">Альбомы</h2>
              <button class="section-link" @click="selectTab('albums')">Все {{ overviewAlbums.length }}</button>
            </div>
            <div class="overview-grid">
              <div 
                v-for="album in overviewAlbums.slice(0, 12)" 
                :key="album.id" 
                class="feed-card"
                @click="goToAlbum(album)"
                @contextmenu.prevent="handleAlbumContextMenu(album, $event)"
                v-longpress="(e) => handleAlbumContextMenu(album, e)"
              >
                <div class="feed-card-cover">
                  <img 
                    v-if="album.cover_url" 
                    :src="getCoverUrl(album.cover_url, CoverSize.MEDIUM)" 
                    alt=""
                    loading="lazy"
                  />
                  <Disc3 v-else :size="36" />
                  <button 
                    class="play-overlay" 
                    @click.stop="shuffleAlbum(album)"
                    title="Слушать"
                  >
                    <Play :size="18" fill="currentColor" />
                  </button>
                </div>
                <div class="feed-card-info">
                  <div class="feed-card-title">{{ album.name || album.title }}</div>
                  <div class="feed-card-subtitle">{{ album.artist || 'Альбом' }}</div>
                </div>
              </div>
            </div>
          </section>

          <!-- Section 3: Popular / Top Tracks -->
          <section v-if="overviewTracks.length > 0" class="profile-section">
            <div class="section-header">
              <h2 class="section-title clickable" @click="selectTab('tracks')" title="Перейти в треки">Треки</h2>
              <button class="section-link" @click="selectTab('tracks')">Все {{ user.track_count || overviewTracks.length }}</button>
            </div>
            <div class="profile-tracks-list">
              <TrackItem
                v-for="(track, index) in overviewTracks.slice(0, 5)"
                :key="track.id"
                :track="track"
                :trackNumber="index + 1"
                :isPlaying="playerStore.currentTrack?.id === track.id"
                :isLiked="libraryStore.isTrackLiked(track.id)"
                @click="handleTrackClick(track, index)"
                @like="handleLikeTrack(track)"
                @menu="(e) => handleTrackMenu(track, index, e)"
                @download="handleDirectDownload(track)"
                @addToLibrary="handleAddToLibrary(track)"
              />
            </div>
            <button 
              v-if="(user.track_count || overviewTracks.length) > 5" 
              class="profile-view-more-btn"
              @click="selectTab('tracks')"
            >
              <span>Показать все {{ user.track_count }} треков</span>
              <ChevronRight :size="16" />
            </button>
          </section>

          <!-- Section 4: SoundCloud Playlists (Overview preview) -->
          <section v-if="scPlaylists.length > 0" class="profile-section sc-section">
            <div class="section-header">
              <div class="section-title-with-badge clickable" @click="selectTab('soundcloud')" title="Перейти в SoundCloud">
                <span class="sc-badge-inline">SC</span>
                <h2 class="section-title">Плейлисты SoundCloud</h2>
              </div>
              <button class="section-link" @click="selectTab('soundcloud')">Все {{ scPlaylists.length }}</button>
            </div>
            <div class="overview-grid">
              <div 
                v-for="pl in scPlaylists.slice(0, 6)" 
                :key="pl.id" 
                class="feed-card ext-card sc-card"
                @click="openScPlaylist(pl)"
              >
                <div class="feed-card-cover sc-cover-box">
                  <img 
                    v-if="pl.artwork_url" 
                    :src="pl.artwork_url" 
                    alt=""
                    loading="lazy"
                    referrerpolicy="no-referrer"
                  />
                  <Folder v-else :size="36" />
                  <div class="play-overlay" title="Открыть плейлист">
                    <Play :size="18" fill="currentColor" />
                  </div>
                </div>
                <div class="feed-card-info">
                  <div class="feed-card-title">{{ pl.title }}</div>
                  <div class="feed-card-subtitle">{{ pl.track_count }} {{ getTracksWord(pl.track_count) }}</div>
                </div>
              </div>
            </div>
          </section>

          <!-- Section 5: SoundCloud Releases (Overview preview) -->
          <section v-if="scTracks.length > 0" class="profile-section sc-section">
            <div class="section-header">
              <div class="section-title-with-badge clickable" @click="selectTab('soundcloud')" title="Перейти в SoundCloud">
                <span class="sc-badge-inline">SC</span>
                <h2 class="section-title">Релизы SoundCloud</h2>
              </div>
              <button class="section-link" @click="selectTab('soundcloud')">Все {{ scTracks.length }}</button>
            </div>
            <div class="ext-tracks-overview-list">
              <ExternalTrackItem
                v-for="item in scTracks.slice(0, 5)"
                :key="item.url"
                :item="item"
                variant="soundcloud"
                :showBadges="true"
                :isImporting="importingTrackUrl === item.url"
                :isDownloading="tasksStore.isTrackDownloading(item.url)"
                :isQueued="tasksStore.isTrackQueued(item.url)"
                :isInLibrary="isTrackInLibrary(item)"
                @play="handleQuickPlayExternalTrack"
                @add="handleQuickAddExternalTrack"
              />
            </div>
          </section>

          <!-- Section 6: Spotify Playlists (Overview preview) -->
          <section v-if="spPlaylists.length > 0" class="profile-section sp-section">
            <div class="section-header">
              <div class="section-title-with-badge clickable" @click="selectTab('spotify')" title="Перейти в Spotify">
                <Radio :size="16" class="sp-icon-title" />
                <h2 class="section-title">Плейлисты Spotify</h2>
              </div>
              <button class="section-link" @click="selectTab('spotify')">Все {{ spPlaylists.length }}</button>
            </div>
            <div class="overview-grid">
              <div 
                v-for="pl in spPlaylists.slice(0, 6)" 
                :key="pl.id" 
                class="feed-card ext-card sp-card"
                @click="selectTab('spotify')"
              >
                <div class="feed-card-cover sp-cover-box">
                  <FileSpreadsheet :size="36" class="sp-card-icon" />
                </div>
                <div class="feed-card-info">
                  <div class="feed-card-title">{{ pl.title }}</div>
                  <div class="feed-card-subtitle">{{ pl.track_count }} {{ getTracksWord(pl.track_count) }}</div>
                </div>
              </div>
            </div>
          </section>

          <!-- Empty State if user has no public content -->
          <div 
            v-if="overviewPlaylists.length === 0 && overviewTracks.length === 0 && overviewAlbums.length === 0 && scPlaylists.length === 0 && scTracks.length === 0 && spPlaylists.length === 0" 
            class="empty-state"
          >
            <div class="empty-icon"><Music :size="48" /></div>
            <h2>Медиатека пуста</h2>
            <p>У пользователя пока нет публичных треков или плейлистов</p>
          </div>
        </template>
      </div>

      <!-- Tracks Tab Content -->
      <div v-show="activeTab === 'tracks'" class="tab-pane tracks-pane">
        <VirtualTrackList
          v-if="hasOpenedTracks || activeTab === 'tracks'"
          :key="'user-tracks-' + userId"
          ref="virtualTrackListRef"
          :fetchFn="fetchUserTracks"
          :pageSize="50"
          :skeletonCount="12"
          :showAlbum="true"
          :showAddToLibrary="true"
          menuContext="social"
          @click="handleTrackClick"
          @like="handleLikeTrack"
          @menu="handleTrackMenu"
          @download="handleDirectDownload"
          @addToLibrary="handleAddToLibrary"
        >
          <template #empty>
            <span class="empty-icon"><Music :size="48" /></span>
            <p>У пользователя нет треков в библиотеке</p>
          </template>
        </VirtualTrackList>
      </div>

      <!-- Playlists Tab Content -->
      <div v-show="activeTab === 'playlists'" class="tab-pane playlists-pane">
        <VirtualGrid
          v-if="hasOpenedPlaylists || activeTab === 'playlists'"
          :key="'user-playlists-' + userId"
          ref="playlistsGridRef"
          type="playlist"
          :fetchFn="fetchUserPlaylists"
          :pageSize="30"
          :skeletonCount="8"
          @click="goToPlaylist"
          @play="shufflePlaylist"
          @contextmenu="handlePlaylistContextMenu"
        >
          <template #empty>
            <span class="empty-icon"><Folder :size="48" /></span>
            <p>Нет публичных плейлистов</p>
          </template>
        </VirtualGrid>
      </div>

      <!-- Albums Tab Content -->
      <div v-show="activeTab === 'albums'" class="tab-pane albums-pane">
        <VirtualGrid
          v-if="hasOpenedAlbums || activeTab === 'albums'"
          :key="'user-albums-' + userId"
          ref="albumsGridRef"
          type="album"
          :fetchFn="fetchUserAlbums"
          :pageSize="30"
          :skeletonCount="8"
          @click="goToAlbum"
          @play="shuffleAlbum"
          @contextmenu="handleAlbumContextMenu"
        >
          <template #empty>
            <span class="empty-icon"><Disc3 :size="48" /></span>
            <p>Нет альбомов в библиотеке</p>
          </template>
        </VirtualGrid>
      </div>

      <!-- SoundCloud Tab Content -->
      <div v-show="activeTab === 'soundcloud'" class="tab-pane sc-pane">
        <!-- SC Profile Strip -->
        <div v-if="scAccount" class="ext-profile-strip sc-profile-strip">
          <div class="ext-strip-avatar">
            <img v-if="scAccount.avatar_url" :src="scAccount.avatar_url" alt="" referrerpolicy="no-referrer" />
            <span v-else class="sc-badge-large">SC</span>
          </div>
          <div class="ext-strip-info">
            <div class="ext-strip-platform">
              <span class="sc-badge-inline">SoundCloud</span>
              <span class="ext-verified-badge" title="Подключенный аккаунт">Подключен</span>
            </div>
            <h2 class="ext-strip-name">{{ scAccount.display_name || scAccount.username }}</h2>
            <div class="ext-strip-sub">
              <span class="ext-strip-handle">@{{ scAccount.username }}</span>
              <span v-if="scAccount.permalink_url" class="stat-separator">•</span>
              <a 
                v-if="scAccount.permalink_url" 
                :href="scAccount.permalink_url" 
                target="_blank" 
                rel="noopener noreferrer" 
                class="ext-strip-link"
              >
                <span>Открыть на SoundCloud</span>
                <ExternalLink :size="13" />
              </a>
            </div>
          </div>
          <div class="ext-strip-stats">
            <div class="ext-stat-box">
              <span class="ext-stat-num">{{ scPlaylists.length }}</span>
              <span class="ext-stat-lbl">плейлистов</span>
            </div>
            <div class="ext-stat-box">
              <span class="ext-stat-num">{{ scTracks.length }}</span>
              <span class="ext-stat-lbl">релизов</span>
            </div>
          </div>
        </div>

        <!-- If viewing a selected SoundCloud Playlist drawer/detail -->
        <div v-if="selectedScPlaylist" class="sc-playlist-detail-view">
          <div class="sc-playlist-detail-header">
            <button class="btn-back-pill" @click="closeScPlaylist">
              <ArrowLeft :size="16" />
              <span>Назад ко всем плейлистам</span>
            </button>
            <div class="sc-playlist-detail-meta">
              <div class="sc-playlist-detail-cover">
                <img 
                  v-if="selectedScPlaylist.artwork_url" 
                  :src="selectedScPlaylist.artwork_url" 
                  alt="" 
                  referrerpolicy="no-referrer" 
                />
                <Folder v-else :size="48" />
              </div>
              <div class="sc-playlist-detail-text">
                <span class="sc-badge-inline">Плейлист SoundCloud</span>
                <h2 class="sc-detail-title">{{ selectedScPlaylist.title }}</h2>
                <div class="sc-detail-sub">
                  <span>{{ scPlaylistTracks.length || selectedScPlaylist.track_count }} {{ getTracksWord(scPlaylistTracks.length || selectedScPlaylist.track_count) }}</span>
                  <span v-if="selectedScPlaylist.permalink_url" class="stat-separator">•</span>
                  <a 
                    v-if="selectedScPlaylist.permalink_url" 
                    :href="selectedScPlaylist.permalink_url" 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    class="ext-strip-link"
                  >
                    <span>SoundCloud</span>
                    <ExternalLink :size="12" />
                  </a>
                </div>
                <div v-if="isSelf" class="sc-detail-actions-row">
                  <button 
                    class="sc-sync-btn"
                    :disabled="isSyncingScPlaylist || loadingScPlaylistTracks || scPlaylistTracks.length === 0"
                    @click="handleSyncScPlaylist(selectedScPlaylist)"
                    title="Создать плейлист в TG Player и загрузить треки в Telegram-канал"
                  >
                    <div v-if="isSyncingScPlaylist" class="spinner small"></div>
                    <CloudDownload v-else :size="15" />
                    <span>{{ isSyncingScPlaylist ? 'Синхронизация плейлиста...' : `Синхронизировать в TG Player (${scPlaylistTracks.length || selectedScPlaylist.track_count})` }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Loading playlist tracks -->
          <div v-if="loadingScPlaylistTracks" class="loading-container">
            <div class="spinner"></div>
          </div>

          <!-- Playlist tracklist -->
          <div v-else class="sc-playlist-tracks-list">
            <ExternalTrackItem
              v-for="item in scPlaylistTracks"
              :key="item.url"
              :item="item"
              variant="soundcloud"
              :showBadges="true"
              :isImporting="importingTrackUrl === item.url"
              :isDownloading="tasksStore.isTrackDownloading(item.url)"
              :isQueued="tasksStore.isTrackQueued(item.url)"
              :isInLibrary="isTrackInLibrary(item)"
              @play="handleQuickPlayExternalTrack"
              @add="handleQuickAddExternalTrack"
            />
            <div v-if="scPlaylistTracks.length === 0" class="empty-state">
              <div class="empty-icon"><Music :size="40" /></div>
              <p>В этом плейлисте нет треков</p>
            </div>
          </div>
        </div>

        <!-- Normal Subtabs: Playlists vs Releases -->
        <div v-else class="sc-main-content">
          <div class="sc-subtabs-bar">
            <button 
              class="sc-subtab-btn" 
              :class="{ active: scSubTab === 'playlists' }"
              @click="scSubTab = 'playlists'"
            >
              <Folder :size="15" />
              <span>Плейлисты</span>
              <span class="subtab-count">{{ scPlaylists.length }}</span>
            </button>
            <button 
              class="sc-subtab-btn" 
              :class="{ active: scSubTab === 'tracks' }"
              @click="scSubTab = 'tracks'"
            >
              <Music :size="15" />
              <span>Релизы и треки</span>
              <span class="subtab-count">{{ scTracks.length }}</span>
            </button>
          </div>

          <!-- Subtab 1: Playlists -->
          <div v-if="scSubTab === 'playlists'" class="sc-subtab-content">
            <div v-if="loadingScPlaylists" class="loading-container">
              <div class="spinner"></div>
            </div>
            <div v-else-if="scPlaylists.length > 0" class="overview-grid">
              <div 
                v-for="pl in scPlaylists" 
                :key="pl.id" 
                class="feed-card ext-card sc-card"
                @click="openScPlaylist(pl)"
              >
                <div class="feed-card-cover sc-cover-box">
                  <img 
                    v-if="pl.artwork_url" 
                    :src="pl.artwork_url" 
                    alt=""
                    loading="lazy"
                    referrerpolicy="no-referrer"
                  />
                  <Folder v-else :size="36" />
                  <div class="play-overlay" title="Смотреть треки">
                    <Play :size="18" fill="currentColor" />
                  </div>
                </div>
                <div class="feed-card-info">
                  <div class="feed-card-title">{{ pl.title }}</div>
                  <div class="feed-card-subtitle">{{ pl.track_count }} {{ getTracksWord(pl.track_count) }}</div>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <div class="empty-icon"><Folder :size="44" /></div>
              <h3>Нет плейлистов SoundCloud</h3>
              <p>Пользователь не создал или скрыл свои плейлисты на SoundCloud</p>
            </div>
          </div>

          <!-- Subtab 2: Releases / Tracks -->
          <div v-if="scSubTab === 'tracks'" class="sc-subtab-content">
            <div v-if="loadingScTracks" class="loading-container">
              <div class="spinner"></div>
            </div>
            <div v-else-if="scTracks.length > 0" class="sc-tracks-wrapper">
              <div class="ext-tracks-list">
                <ExternalTrackItem
                  v-for="item in scTracks"
                  :key="item.url"
                  :item="item"
                  variant="soundcloud"
                  :showBadges="true"
                  :isImporting="importingTrackUrl === item.url"
                  :isDownloading="tasksStore.isTrackDownloading(item.url)"
                  :isQueued="tasksStore.isTrackQueued(item.url)"
                  :isInLibrary="isTrackInLibrary(item)"
                  @play="handleQuickPlayExternalTrack"
                  @add="handleQuickAddExternalTrack"
                />
              </div>
              <div v-if="scTracksCursor" class="load-more-box">
                <button 
                  class="btn-pill-secondary" 
                  :disabled="loadingMoreScTracks" 
                  @click="loadMoreScTracks"
                >
                  <div v-if="loadingMoreScTracks" class="spinner small"></div>
                  <span v-else>Загрузить ещё релизы</span>
                </button>
              </div>
            </div>
            <div v-else class="empty-state">
              <div class="empty-icon"><Music :size="44" /></div>
              <h3>Нет релизов на SoundCloud</h3>
              <p>Пользователь ещё не загружал собственные авторские треки на SoundCloud</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Spotify Tab Content -->
      <div v-show="activeTab === 'spotify'" class="tab-pane sp-pane">
        <!-- Spotify Profile Strip -->
        <div v-if="spAccount" class="ext-profile-strip sp-profile-strip">
          <div class="ext-strip-avatar sp-avatar">
            <img v-if="spAccount.avatar_url" :src="spAccount.avatar_url" alt="" referrerpolicy="no-referrer" />
            <Radio v-else :size="32" class="sp-icon-large" />
          </div>
          <div class="ext-strip-info">
            <div class="ext-strip-platform">
              <span class="sp-badge-inline">Spotify</span>
              <span class="ext-verified-badge" title="Подключенный аккаунт">Подключен</span>
            </div>
            <h2 class="ext-strip-name">{{ spAccount.display_name || spAccount.username }}</h2>
            <div class="ext-strip-sub">
              <span class="ext-strip-handle">@{{ spAccount.username }}</span>
              <span v-if="spAccount.permalink_url" class="stat-separator">•</span>
              <a 
                v-if="spAccount.permalink_url" 
                :href="spAccount.permalink_url" 
                target="_blank" 
                rel="noopener noreferrer" 
                class="ext-strip-link"
              >
                <span>Открыть на Spotify</span>
                <ExternalLink :size="13" />
              </a>
            </div>
          </div>
          <div class="ext-strip-stats">
            <div class="ext-stat-box">
              <span class="ext-stat-num">{{ spPlaylists.length }}</span>
              <span class="ext-stat-lbl">плейлистов</span>
            </div>
          </div>
        </div>

        <div class="sp-main-content">
          <div class="section-header">
            <h3 class="section-title">Импортированные плейлисты Spotify</h3>
            <span class="section-badge-pill">{{ spPlaylists.length }}</span>
          </div>

          <div v-if="loadingSpPlaylists" class="loading-container">
            <div class="spinner"></div>
          </div>

          <div v-else-if="spPlaylists.length > 0" class="overview-grid">
            <div 
              v-for="pl in spPlaylists" 
              :key="pl.id" 
              class="feed-card ext-card sp-card"
            >
              <div class="feed-card-cover sp-cover-box">
                <FileSpreadsheet :size="36" class="sp-card-icon" />
              </div>
              <div class="feed-card-info">
                <div class="feed-card-title">{{ pl.title }}</div>
                <div class="feed-card-subtitle">
                  {{ pl.track_count }} {{ getTracksWord(pl.track_count) }}
                  <span v-if="pl.created_at" class="sp-date">• {{ new Date(pl.created_at).toLocaleDateString() }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="empty-state">
            <div class="empty-icon"><Radio :size="44" /></div>
            <h3>Нет плейлистов Spotify</h3>
            <p>У пользователя пока нет сохраненных плейлистов из Spotify</p>
          </div>
        </div>
      </div>
    </template>

    <!-- Edit Profile Modal -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showEditProfileModal" class="modal-backdrop" @click="closeEditProfileModal">
          <div class="edit-profile-modal" @click.stop>
            <div class="modal-header">
              <h3>Редактирование профиля</h3>
              <button class="modal-close-btn" @click="closeEditProfileModal">
                <X :size="20" />
              </button>
            </div>

            <div class="modal-body">
              <!-- Avatar Preview & Actions -->
              <div class="modal-avatar-section">
                <div class="modal-avatar-preview" :style="avatarGradientStyle">
                  <img v-if="editAvatarUrl" :src="editAvatarUrl" class="modal-avatar-img" />
                  <span v-else>{{ (editNickname || user?.first_name || 'U').charAt(0).toUpperCase() }}</span>
                </div>
                <div class="modal-avatar-actions">
                  <input 
                    ref="modalFileInputRef" 
                    type="file" 
                    accept="image/*" 
                    style="display: none" 
                    @change="handleModalAvatarChange" 
                  />
                  <button 
                    class="btn-pill-primary small" 
                    :disabled="modalSaving" 
                    @click="modalFileInputRef?.click()"
                  >
                    <Camera :size="14" />
                    <span>{{ editAvatarUrl ? 'Сменить фото' : 'Загрузить фото' }}</span>
                  </button>
                  <button 
                    v-if="editAvatarUrl" 
                    class="btn-pill-secondary small danger-text" 
                    :disabled="modalSaving" 
                    @click="handleModalAvatarRemove"
                  >
                    <Trash2 :size="14" />
                    <span>Удалить</span>
                  </button>
                </div>
              </div>

              <!-- Nickname field -->
              <div class="modal-form-group">
                <label class="modal-label">Кастомный никнейм</label>
                <div class="modal-input-wrap">
                  <input 
                    v-model="editNickname" 
                    type="text" 
                    maxlength="50"
                    placeholder="Введите никнейм (например, xFer Serum)" 
                    class="modal-text-input" 
                    @keydown.enter="saveProfileModal"
                  />
                  <button 
                    v-if="editNickname" 
                    class="modal-input-clear" 
                    @click="editNickname = ''"
                    title="Очистить"
                  >
                    <X :size="14" />
                  </button>
                </div>
                <span class="modal-hint">Отображается в профиле и медиатеке вместо Telegram-имени.</span>
              </div>

              <!-- Hide Telegram ID toggle -->
              <div class="modal-privacy-row">
                <div class="modal-privacy-info">
                  <span class="modal-privacy-title">Скрыть Telegram ID и ник</span>
                  <span class="modal-privacy-desc">Ваш @username и ID не будут видны другим пользователям</span>
                </div>
                <label class="toggle">
                  <input type="checkbox" v-model="editHideTelegramId" />
                  <span class="toggle-slider"></span>
                </label>
              </div>
            </div>

            <div class="modal-footer">
              <button class="btn-pill-secondary" @click="closeEditProfileModal" :disabled="modalSaving">
                Отмена
              </button>
              <button class="btn-pill-primary" @click="saveProfileModal" :disabled="modalSaving">
                <div v-if="modalSaving" class="spinner small"></div>
                <span v-else>Сохранить</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import { useTasksStore } from '@/stores/tasks'
import { useContextMenu } from '@/composables/useContextMenu'
import { useTrackActions, useShare } from '@/composables'
import { socialApi, playlistsApi, authApi, ingestionApi } from '@/api/client'
import apiCache from '@/utils/apiCache'
import { getCoverUrl, CoverSize } from '@/utils'
import TrackItem from '@/components/TrackItem.vue'
import ExternalTrackItem from '@/components/ExternalTrackItem.vue'
import VirtualTrackList from '@/components/VirtualTrackList.vue'
import VirtualGrid from '@/components/VirtualGrid.vue'
import {
  UserPlus,
  Check,
  Share2,
  Lock,
  UserX,
  Music,
  Folder,
  Disc3,
  Settings,
  Play,
  Shuffle,
  ChevronRight,
  Sparkles,
  Camera,
  EyeOff,
  X,
  Edit3,
  Trash2,
  Radio,
  ExternalLink,
  ArrowLeft,
  FileSpreadsheet,
  CloudDownload,
  AlertCircle,
  Maximize2,
  Music2,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const uiStore = useUIStore()
const tasksStore = useTasksStore()
const { openMenu } = useContextMenu()
const { share } = useShare()

// Unified actions
const { handleDirectDownload, handleLikeTrack, handleAddToLibrary } = useTrackActions()

const userId = computed(() => {
  const raw = route.params.id
  if (raw === 'me' || !raw) {
    return authStore.user?.id || 0
  }
  const parsed = Number(raw)
  return isNaN(parsed) ? (authStore.user?.id || 0) : parsed
})
const isSelf = computed(() => !!(authStore.user && authStore.user.id === userId.value))

// State
const user = ref(null)
const loading = ref(true)
const error = ref(null)
const isForbidden = ref(false)
const isFollowing = ref(false)
const followLoading = ref(false)
const activeTab = ref('overview')
const hasOpenedTracks = ref(false)
const hasOpenedPlaylists = ref(false)
const hasOpenedAlbums = ref(false)

const markTabOpened = (tabKey) => {
  if (tabKey === 'tracks') hasOpenedTracks.value = true
  if (tabKey === 'playlists') hasOpenedPlaylists.value = true
  if (tabKey === 'albums') hasOpenedAlbums.value = true
}

// Overview data
const overviewTracks = ref([])
const overviewPlaylists = ref([])
const overviewAlbums = ref([])
const loadingOverview = ref(false)

// External Accounts State
const externalAccounts = ref([])
const scAccount = computed(() => externalAccounts.value.find(a => a.provider === 'soundcloud'))
const spAccount = computed(() => externalAccounts.value.find(a => a.provider === 'spotify'))

const scPlaylists = ref([])
const loadingScPlaylists = ref(false)
const scTracks = ref([])
const loadingScTracks = ref(false)
const scTracksCursor = ref(null)
const loadingMoreScTracks = ref(false)
const scSubTab = ref('playlists') // 'playlists' | 'tracks'
const selectedScPlaylist = ref(null)
const scPlaylistTracks = ref([])
const loadingScPlaylistTracks = ref(false)

const spPlaylists = ref([])
const loadingSpPlaylists = ref(false)

const importingTrackUrl = ref(null)

const isTrackInLibrary = (item) => {
  if (!item) return false
  return item.in_library || tasksStore.isTrackCompleted(item.url)
}

const loadExternalAccounts = async (id) => {
  if (!id) return
  try {
    const res = await socialApi.getUserExternalAccounts(id)
    externalAccounts.value = res.data?.accounts || []

    const sc = externalAccounts.value.find(a => a.provider === 'soundcloud')
    if (sc) {
      if (sc.show_playlists || isSelf.value) {
        loadScPlaylists(id)
      }
      if (sc.show_tracks || isSelf.value) {
        loadScTracks(id, true)
      }
    }

    const sp = externalAccounts.value.find(a => a.provider === 'spotify')
    if (sp) {
      if (sp.show_playlists || isSelf.value) {
        loadSpPlaylists(id)
      }
    }
  } catch (err) {
    console.error('Failed to load user external accounts:', err)
  }
}

const loadScPlaylists = async (id) => {
  loadingScPlaylists.value = true
  try {
    const res = await socialApi.getUserExternalPlaylists(id, 'soundcloud')
    scPlaylists.value = res.data?.items || []
  } catch (err) {
    console.error('Failed to load SC playlists:', err)
    scPlaylists.value = []
  } finally {
    loadingScPlaylists.value = false
  }
}

const loadScTracks = async (id, reset = true) => {
  loadingScTracks.value = true
  if (reset) {
    scTracksCursor.value = null
  }
  try {
    const res = await socialApi.getUserExternalTracks(id, 'soundcloud', { limit: 40 })
    scTracks.value = res.data?.items || []
    scTracksCursor.value = res.data?.next_cursor || null
  } catch (err) {
    console.error('Failed to load SC tracks:', err)
    scTracks.value = []
  } finally {
    loadingScTracks.value = false
  }
}

const loadMoreScTracks = async () => {
  if (!scTracksCursor.value || loadingMoreScTracks.value) return
  loadingMoreScTracks.value = true
  try {
    const res = await socialApi.getUserExternalTracks(userId.value, 'soundcloud', {
      cursor: scTracksCursor.value,
      limit: 40,
    })
    const more = res.data?.items || []
    scTracks.value = [...scTracks.value, ...more]
    scTracksCursor.value = res.data?.next_cursor || null
  } catch (err) {
    console.error('Failed to load more SC tracks:', err)
  } finally {
    loadingMoreScTracks.value = false
  }
}

const loadSpPlaylists = async (id) => {
  loadingSpPlaylists.value = true
  try {
    const res = await socialApi.getUserExternalPlaylists(id, 'spotify')
    spPlaylists.value = res.data?.items || []
  } catch (err) {
    console.error('Failed to load Spotify playlists:', err)
    spPlaylists.value = []
  } finally {
    loadingSpPlaylists.value = false
  }
}

const openScPlaylist = async (pl) => {
  selectTab('soundcloud')
  selectedScPlaylist.value = pl
  scPlaylistTracks.value = []
  loadingScPlaylistTracks.value = true
  try {
    const res = await socialApi.getUserExternalPlaylistTracks(userId.value, pl.id)
    scPlaylistTracks.value = res.data?.tracks || []
  } catch (err) {
    console.error('Failed to load SC playlist tracks:', err)
    uiStore.toast?.error('Ошибка', 'Не удалось загрузить треки плейлиста')
  } finally {
    loadingScPlaylistTracks.value = false
  }
}

const closeScPlaylist = () => {
  selectedScPlaylist.value = null
  scPlaylistTracks.value = []
}

const handleQuickPlayExternalTrack = async (item) => {
  if (importingTrackUrl.value) return
  importingTrackUrl.value = item.url

  try {
    const res = await ingestionApi.quickImport({
      url: item.url,
      title: item.title,
      artist: item.artist,
      duration: item.duration,
      cover_url: item.cover_url,
      genre: item.genre,
      tags: item.tags,
      add_to_library: false,
    })

    const track = res.data?.track
    if (track) {
      if (track.in_library) {
        item.in_library = true
      }
      item.already_in_tg = true
      item.track_id = track.id
      playerStore.play(track, [track])
    }
  } catch (e) {
    console.error('Failed to quick play external track:', e)
    const errorMsg = e.response?.data?.detail || 'Не удалось загрузить трек'
    uiStore.toast?.error('Ошибка воспроизведения', errorMsg)
  } finally {
    importingTrackUrl.value = null
  }
}

const handleQuickAddExternalTrack = (item) => {
  tasksStore.enqueueTrack(item, 'soundcloud')
}

// ─── Import & Ingestion Task Handlers ───
const isSyncingScPlaylist = ref(false)

const subtextFor = (job) => {
  if (!job) return ''
  if (job.status === 'completed') return job.current_step || 'Импорт завершён'
  if (job.status === 'failed') return job.error_message || 'Ошибка'
  if (job.status === 'cancelled') return 'Отменено'

  if (job.current_step && job.current_track_title) {
    return `${job.current_track_title} • ${job.current_step}`
  }
  if (job.current_track_title) {
    return job.current_track_title
  }
  return job.current_step || 'Синхронизация...'
}

const handleRestoreJob = (jobId) => {
  tasksStore.restoreJob(jobId)
}

const handleCancelJob = (jobId) => {
  tasksStore.cancelJob(jobId)
}

const handleSyncScPlaylist = async (playlist) => {
  if (isSyncingScPlaylist.value) return

  let tracksToSync = scPlaylistTracks.value
  if (!tracksToSync || tracksToSync.length === 0) {
    try {
      loadingScPlaylistTracks.value = true
      const res = await socialApi.getUserExternalPlaylistTracks(userId.value, playlist.id)
      tracksToSync = res.data?.tracks || []
      scPlaylistTracks.value = tracksToSync
    } catch (e) {
      uiStore.toast?.error('Ошибка', 'Не удалось получить треки плейлиста')
      return
    } finally {
      loadingScPlaylistTracks.value = false
    }
  }

  if (tracksToSync.length === 0) {
    uiStore.toast?.info('Синхронизация', 'В этом плейлисте нет треков для синхронизации')
    return
  }

  isSyncingScPlaylist.value = true
  try {
    const urls = tracksToSync.map(t => t.url)
    const tracksPayload = tracksToSync.map(t => ({
      url: t.url,
      title: t.title,
      artist: t.artist,
      duration: t.duration,
      cover_url: t.cover_url || playlist.artwork_url,
      genre: t.genre,
      tags: t.tags,
      extra: {
        is_soundcloud: true,
        playlist_title: playlist.title,
      }
    }))

    const res = await ingestionApi.start(
      playlist.permalink_url || urls[0],
      urls,
      tracksPayload,
      playlist.title,
      true,
      playlist.title
    )

    if (res.data) {
      tasksStore.registerJob(res.data, {
        type: 'import',
        title: `Плейлист: ${playlist.title}`,
      })
    }
    uiStore.toast?.success('Синхронизация', `Запущен импорт плейлиста «${playlist.title}» (${urls.length} треков)`)

    const jobId = res.data?.id
    const pollInterval = setInterval(async () => {
      try {
        const jobRes = await ingestionApi.getJob(jobId)
        const job = jobRes.data
        if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
          clearInterval(pollInterval)
          isSyncingScPlaylist.value = false
          if (job.status === 'completed') {
            uiStore.toast?.success('Готово', `Плейлист «${playlist.title}» успешно синхронизирован!`)
            libraryStore.fetchTracks({ refresh: true })
            loadOverviewData(userId.value)
          }
        }
      } catch (err) {
        clearInterval(pollInterval)
        isSyncingScPlaylist.value = false
      }
    }, 2000)
  } catch (e) {
    console.error('Failed to sync SC playlist from profile:', e)
    uiStore.toast?.error('Ошибка', 'Не удалось запустить синхронизацию плейлиста')
    isSyncingScPlaylist.value = false
  }
}

// Refs
const virtualTrackListRef = ref(null)
const playlistsGridRef = ref(null)
const albumsGridRef = ref(null)

const resetScrollToTop = () => {
  const mainContent = document.querySelector('.main-content')
  if (mainContent) {
    mainContent.scrollTop = 0
  }
}

const selectTab = async (tabKey) => {
  if (activeTab.value !== tabKey) {
    resetScrollToTop()
  }
  markTabOpened(tabKey)
  activeTab.value = tabKey
  await nextTick()
  window.dispatchEvent(new Event('resize'))
  if (tabKey === 'tracks') {
    virtualTrackListRef.value?.updateScroll?.()
  } else if (tabKey === 'playlists') {
    playlistsGridRef.value?.updateScroll?.()
  } else if (tabKey === 'albums') {
    albumsGridRef.value?.updateScroll?.()
  }
}

watch(activeTab, async (newTab) => {
  markTabOpened(newTab)
  await nextTick()
  window.dispatchEvent(new Event('resize'))
  if (newTab === 'tracks') {
    virtualTrackListRef.value?.updateScroll?.()
  } else if (newTab === 'playlists') {
    playlistsGridRef.value?.updateScroll?.()
  } else if (newTab === 'albums') {
    albumsGridRef.value?.updateScroll?.()
  }
})

const userAvatar = computed(() => {
  if (isSelf.value && authStore.userAvatarUrl) {
    return authStore.userAvatarUrl
  }
  return user.value?.avatar_url || user.value?.custom_avatar_url || user.value?.photo_url || null
})

// ─── Edit Profile Modal State ───
const showEditProfileModal = ref(false)
const editNickname = ref('')
const editAvatarUrl = ref(null)
const editHideTelegramId = ref(false)
const modalSaving = ref(false)
const modalFileInputRef = ref(null)
const pendingAvatarFile = ref(null)

const openEditProfileModal = () => {
  editNickname.value = user.value?.custom_nickname || (isSelf.value ? authStore.user?.custom_nickname : '') || ''
  editAvatarUrl.value = userAvatar.value || null
  editHideTelegramId.value = user.value?.hide_telegram_id ?? (isSelf.value ? authStore.user?.hide_telegram_id : false) ?? false
  pendingAvatarFile.value = null
  showEditProfileModal.value = true
}

const closeEditProfileModal = () => {
  if (modalSaving.value) return
  showEditProfileModal.value = false
  pendingAvatarFile.value = null
}

const handleModalAvatarChange = (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  pendingAvatarFile.value = file
  editAvatarUrl.value = URL.createObjectURL(file)
}

const handleModalAvatarRemove = () => {
  pendingAvatarFile.value = 'remove'
  editAvatarUrl.value = null
}

const saveProfileModal = async () => {
  if (modalSaving.value) return
  modalSaving.value = true
  try {
    // 1. Avatar change
    if (pendingAvatarFile.value === 'remove') {
      await authStore.deleteAvatar()
    } else if (pendingAvatarFile.value instanceof File) {
      await authStore.uploadAvatar(pendingAvatarFile.value)
    }

    // 2. Custom nickname
    const nick = editNickname.value.trim()
    await authStore.updateProfile({ custom_nickname: nick })

    // 3. Hide telegram ID
    if (editHideTelegramId.value !== (user.value?.hide_telegram_id || false)) {
      await authApi.updatePrivacy({ hide_telegram_id: editHideTelegramId.value })
      if (authStore.user) {
        authStore.user.hide_telegram_id = editHideTelegramId.value
      }
    }

    // Invalidate caches & force reload user profile
    apiCache.invalidateRelated('user', userId.value)
    await loadUserProfile(true)
    closeEditProfileModal()
    uiStore.showToast('Профиль успешно обновлен', 'success')
  } catch (err) {
    console.error('Failed to save profile:', err)
    uiStore.showToast('Ошибка при сохранении профиля', 'error')
  } finally {
    modalSaving.value = false
  }
}

const getInitials = (u) => {
  if (isSelf.value && authStore.userDisplayName) {
    return authStore.userDisplayName.charAt(0).toUpperCase()
  }
  if (!u) return '?'
  if (u.custom_nickname) return u.custom_nickname.charAt(0).toUpperCase()
  if (u.first_name) return u.first_name.charAt(0).toUpperCase()
  if (u.display_name) return u.display_name.charAt(0).toUpperCase()
  if (u.username) return u.username.charAt(0).toUpperCase()
  return '?'
}

const getTracksWord = (count) => {
  const c = count || 0
  const mod10 = c % 10
  const mod100 = c % 100
  if (mod100 >= 11 && mod100 <= 14) return 'треков'
  if (mod10 === 1) return 'трек'
  if (mod10 >= 2 && mod10 <= 4) return 'трека'
  return 'треков'
}

const getPlaylistsWord = (count) => {
  const c = count || 0
  const mod10 = c % 10
  const mod100 = c % 100
  if (mod100 >= 11 && mod100 <= 14) return 'плейлистов'
  if (mod10 === 1) return 'плейлист'
  if (mod10 >= 2 && mod10 <= 4) return 'плейлиста'
  return 'плейлистов'
}

const avatarGradientStyle = computed(() => {
  const str = user.value?.display_name || user.value?.username || 'User'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const h1 = Math.abs(hash % 360)
  const h2 = (h1 + 60) % 360
  return {
    background: `linear-gradient(135deg, hsl(${h1}, 70%, 45%) 0%, hsl(${h2}, 75%, 55%) 100%)`
  }
})

const ambientGlowStyle = computed(() => {
  const str = user.value?.display_name || user.value?.username || 'User'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const h1 = Math.abs(hash % 360)
  return {
    background: `radial-gradient(ellipse at 30% 0%, hsla(${h1}, 75%, 50%, 0.18) 0%, rgba(14, 18, 24, 0) 75%)`
  }
})

const getPlaylistCoverStyle = (playlist) => {
  if (playlist?.covers?.length) return {}
  const str = playlist?.name || 'Playlist'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const h1 = Math.abs(hash % 360)
  const h2 = (h1 + 40) % 360
  return {
    background: `linear-gradient(135deg, hsl(${h1}, 65%, 28%) 0%, hsl(${h2}, 60%, 18%) 100%)`
  }
}

// Load Overview Strips
const loadOverviewData = async (id) => {
  if (!id) return
  loadingOverview.value = true
  try {
    const [tracksRes, playlistsRes, albumsRes] = await Promise.allSettled([
      socialApi.getUserLibrary(id, { page: 1, per_page: 8 }),
      playlistsApi.getUserPlaylists(id),
      socialApi.getUserAlbums(id, { page: 1, per_page: 10 })
    ])

    if (tracksRes.status === 'fulfilled') {
      overviewTracks.value = tracksRes.value.data?.items || (Array.isArray(tracksRes.value.data) ? tracksRes.value.data : [])
    }
    if (playlistsRes.status === 'fulfilled') {
      overviewPlaylists.value = playlistsRes.value.data?.items || (Array.isArray(playlistsRes.value.data) ? playlistsRes.value.data : [])
    }
    if (albumsRes.status === 'fulfilled') {
      overviewAlbums.value = albumsRes.value.data?.items || (Array.isArray(albumsRes.value.data) ? albumsRes.value.data : [])
    }
  } catch (err) {
    console.error('Failed to load overview data:', err)
  } finally {
    loadingOverview.value = false
  }
}

// Fetch user profile
const loadUserProfile = async (bypassCache = false) => {
  const id = userId.value
  if (!id) {
    if (authStore.loading || !authStore.initialized) return
    error.value = 'Пользователь не найден'
    loading.value = false
    return
  }
  if (!user.value) {
    loading.value = true
  }
  error.value = null
  isForbidden.value = false

  try {
    const shouldBypass = bypassCache || isSelf.value
    const res = await socialApi.getUser(id, {}, { bypassCache: shouldBypass })
    user.value = res.data
    isFollowing.value = !!res.data.is_following
    loadOverviewData(id)
    loadExternalAccounts(id)
  } catch (err) {
    if (err.response?.status === 403) {
      isForbidden.value = true
    } else if (err.response?.status === 404) {
      error.value = 'Пользователь не существует'
    } else {
      error.value = 'Ошибка загрузки профиля'
    }
  } finally {
    loading.value = false
  }
}

// Toggle follow / unfollow
const toggleFollow = async () => {
  if (!authStore.hasChannel) {
    authStore.promptChannelSetup()
    return
  }
  if (!user.value || followLoading.value) return

  followLoading.value = true
  try {
    if (isFollowing.value) {
      await socialApi.unfollow(user.value.id)
      isFollowing.value = false
      if (user.value.followers_count > 0) user.value.followers_count--
    } else {
      await socialApi.follow(user.value.id)
      isFollowing.value = true
      user.value.followers_count++
    }
  } catch (err) {
    if (err.response?.status === 403) {
      authStore.promptChannelSetup()
    } else {
      console.error('Failed to toggle follow:', err)
    }
  } finally {
    followLoading.value = false
  }
}

// Share profile
const handleShare = () => {
  if (!user.value) return
  share({
    type: 'user',
    id: user.value.id,
    title: user.value.display_name,
    text: `Посмотри медиатеку ${user.value.display_name} в TG Player!`,
  })
}

// Track actions
const handlePlayUserLibrary = async () => {
  if (overviewTracks.value?.length > 0) {
    playerStore.play(overviewTracks.value[0], overviewTracks.value)
    uiStore.toast.success('Воспроизведение', `Играет медиатека ${user.value.display_name}`)
  } else {
    try {
      const res = await socialApi.getUserLibrary(userId.value, { page: 1, per_page: 50 })
      const tracks = res.data?.items || []
      if (tracks.length > 0) {
        playerStore.play(tracks[0], tracks)
        uiStore.toast.success('Воспроизведение', `Играет медиатека ${user.value.display_name}`)
      } else {
        uiStore.toast.info('Пусто', 'У пользователя нет доступных треков')
      }
    } catch (e) {
      console.error('Failed to play user library:', e)
    }
  }
}

const handleShuffleUserLibrary = async () => {
  try {
    const res = await socialApi.getUserLibrary(userId.value, { page: 1, per_page: 100 })
    const tracks = res.data?.items || []
    if (tracks.length > 0) {
      const shuffled = [...tracks].sort(() => Math.random() - 0.5)
      playerStore.play(shuffled[0], shuffled)
      uiStore.toast.success('Перемешивание', `Играет медиатека ${user.value.display_name}`)
    } else {
      uiStore.toast.info('Пусто', 'У пользователя нет доступных треков')
    }
  } catch (e) {
    console.error('Failed to shuffle user library:', e)
  }
}

const fetchUserTracks = async ({ offset, limit }) => {
  const page = Math.floor(offset / limit) + 1
  try {
    const res = await socialApi.getUserLibrary(userId.value, { page, per_page: limit })
    return {
      items: res.data.items || [],
      total: res.data.total || 0,
    }
  } catch (err) {
    console.error('Failed to fetch user tracks:', err)
    return { items: [], total: 0 }
  }
}

const handleTrackClick = (payload, index) => {
  // If emitted from VirtualTrackList: payload = { track, index, allTracks }
  if (payload && payload.track) {
    const track = payload.track
    const queue = payload.allTracks?.length ? payload.allTracks : [track]
    playerStore.play(track, queue)
    return
  }
  // If emitted from overview TrackItem: payload = track, index = index
  const track = payload
  if (overviewTracks.value?.length) {
    playerStore.play(track, overviewTracks.value)
  } else {
    playerStore.play(track)
  }
}

const handleTrackMenu = (payload, index, event) => {
  // If emitted from VirtualTrackList: payload = { track, index, event, context }
  if (payload && payload.track) {
    openMenu('track', payload.track, payload.context || 'social', payload.event)
    return
  }
  // If emitted from overview TrackItem: payload = track, index = index, event = event
  openMenu('track', payload, 'social', event)
}

// Playlist actions
const fetchUserPlaylists = async ({ offset, limit }) => {
  try {
    const res = await playlistsApi.getUserPlaylists(userId.value)
    const all = res.data.items || []
    return {
      items: all.slice(offset, offset + limit),
      total: all.length,
    }
  } catch (err) {
    console.error('Failed to fetch user playlists:', err)
    return { items: [], total: 0 }
  }
}

const goToPlaylist = (playlist) => {
  router.push(`/playlist/${playlist.id}`)
}

const shufflePlaylist = async (playlist) => {
  await playerStore.playShuffleAll('playlist', playlist.id, playlist.name)
}

const handlePlaylistContextMenu = (payload, event) => {
  // If emitted from VirtualGrid: payload = { item, event }
  if (payload && payload.item) {
    openMenu('playlist', payload.item, 'social', payload.event)
    return
  }
  // If emitted from overview feed-card: payload = playlist, event = event
  openMenu('playlist', payload, 'social', event)
}

// Album actions
const fetchUserAlbums = async ({ offset, limit }) => {
  const page = Math.floor(offset / limit) + 1
  try {
    const res = await socialApi.getUserAlbums(userId.value, { page, per_page: limit })
    return {
      items: res.data.items || [],
      total: res.data.total || 0,
    }
  } catch (err) {
    console.error('Failed to fetch user albums:', err)
    return { items: [], total: 0 }
  }
}

const goToAlbum = (album) => {
  router.push(`/album/${album.id}`)
}

const shuffleAlbum = async (album) => {
  await playerStore.playShuffleAll('album', album.id, album.name)
}

const handleAlbumContextMenu = (payload, event) => {
  // If emitted from VirtualGrid: payload = { item, event }
  if (payload && payload.item) {
    openMenu('album', payload.item, 'social', payload.event)
    return
  }
  // If emitted from overview feed-card: payload = album, event = event
  openMenu('album', payload, 'social', event)
}

watch(
  () => route.params.id,
  (newId) => {
    if (newId && route.name === 'user-profile') {
      activeTab.value = 'overview'
      hasOpenedTracks.value = false
      hasOpenedPlaylists.value = false
      hasOpenedAlbums.value = false
      externalAccounts.value = []
      scPlaylists.value = []
      scTracks.value = []
      spPlaylists.value = []
      selectedScPlaylist.value = null
      resetScrollToTop()
      loadUserProfile(true)
    }
  }
)

watch(
  () => authStore.user,
  (newUser) => {
    if (newUser && isSelf.value) {
      if (user.value) {
        user.value.custom_nickname = newUser.custom_nickname
        user.value.custom_avatar_url = newUser.custom_avatar_url
        user.value.avatar_url = newUser.custom_avatar_url || newUser.photo_url || user.value.avatar_url
        user.value.display_name = authStore.userDisplayName
        user.value.hide_telegram_id = newUser.hide_telegram_id
      }
      loadUserProfile(true)
    }
  },
  { deep: true }
)

watch(isSelf, (self) => {
  if (self) {
    tasksStore.checkRecentJobs()
  }
})

onMounted(() => {
  loadUserProfile(true)
  if (isSelf.value) {
    tasksStore.checkRecentJobs()
  }
})
</script>

<style scoped>
.user-profile-view {
  padding: 24px 32px 48px;
  max-width: 1400px;
  margin: 0 auto;
  min-height: calc(100vh - 120px);
  width: 100%;
  box-sizing: border-box;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 80px 0;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon {
  color: var(--c-accent);
  opacity: 0.8;
  margin-bottom: 8px;
}

.empty-state h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--c-text-1);
}

.empty-state p {
  color: var(--c-text-2);
  font-size: 14px;
  max-width: 320px;
}

/* Modern Profile Hero Card */
.profile-hero-card {
  position: relative;
  overflow: hidden;
  border-radius: 24px;
  background: var(--c-bg-2, #181818);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 28px 32px;
  margin-bottom: 28px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  gap: 32px;
}

.hero-ambient-glow {
  position: absolute;
  top: -60px;
  left: -40px;
  right: -40px;
  height: 240px;
  pointer-events: none;
  opacity: 0.95;
  filter: blur(28px);
}

.hero-avatar {
  position: relative;
  width: 176px;
  height: 176px;
  min-width: 176px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 56px;
  font-weight: 800;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  border: 3px solid rgba(255, 255, 255, 0.14);
  overflow: hidden;
  transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
  z-index: 1;
}

.hero-avatar.is-clickable {
  cursor: pointer;
}

.hero-avatar.is-clickable:hover {
  transform: scale(1.02);
  border-color: var(--c-accent, #1db954);
  box-shadow: 0 12px 36px rgba(29, 185, 84, 0.3);
}

.hero-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.hero-avatar-initials {
  user-select: none;
}

.hero-avatar-edit-overlay {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(2px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #fff;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.edit-avatar-text {
  font-size: 12px;
  font-weight: 700;
}

.hero-avatar.is-clickable:hover .hero-avatar-edit-overlay {
  opacity: 1;
}

.hero-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
  z-index: 1;
}

.hero-meta-top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hero-type-label {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  text-transform: uppercase;
}

.self-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--r-full, 9999px);
  background: var(--c-accent, #1db954);
  color: #000;
}

.hidden-handle-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
}

.hero-name {
  font-size: 38px;
  font-weight: 800;
  color: var(--c-text-1, #fff);
  margin: 0;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.025em;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.4);
}

.hero-subline {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 13.5px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
}

.hero-handle {
  font-size: 13.5px;
  color: var(--c-accent, #1db954);
  font-weight: 600;
}

.hero-stat-pill {
  background: none;
  border: none;
  padding: 0;
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
  font-size: 13.5px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.75));
  cursor: pointer;
  transition: color 0.15s ease;
}

.hero-stat-pill:hover {
  color: var(--c-accent, #1db954);
}

.stat-num {
  font-weight: 700;
  color: var(--c-text-1, #fff);
  font-size: 14px;
}

.stat-separator {
  color: rgba(255, 255, 255, 0.25);
  font-size: 11px;
}

.hero-actions-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.hero-share-corner-btn {
  position: absolute;
  top: 24px;
  right: 24px;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--c-text-1, #fff);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 5;
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.hero-share-corner-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.25);
  transform: scale(1.06);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.35);
}

.hero-share-corner-btn:active {
  transform: scale(0.96);
}

.hero-play-capsule {
  flex-shrink: 0;
}

.hero-pill-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--c-text-1, #fff);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  flex-shrink: 0;
  padding: 0;
}

.hero-pill-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.22);
  transform: scale(1.06);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
}

.hero-pill-btn:active:not(:disabled) {
  transform: scale(0.96);
}

.hero-pill-btn.follow-btn.is-following {
  background: rgba(255, 255, 255, 0.06);
  color: var(--c-accent, #1db954);
  border-color: rgba(29, 185, 84, 0.3);
}

/* Modern Tab Bar */
.user-tabs-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 28px;
  padding-bottom: 4px;
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.user-tabs-bar::-webkit-scrollbar {
  display: none;
}

.user-tabs-bar::after {
  content: '';
  flex-shrink: 0;
  width: 8px;
}

.user-tab-btn {
  display: inline-flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  height: 42px;
  padding: 0 20px;
  border-radius: 9999px;
  background: var(--c-bg-2, #181818);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  user-select: none;
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  flex-shrink: 0;
}

.user-tab-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-1, #fff);
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateY(-1px);
}

.user-tab-btn.active {
  background: var(--c-accent, #1db954);
  color: #000;
  font-weight: 700;
  border-color: var(--c-accent, #1db954);
  box-shadow: 0 4px 16px rgba(29, 185, 84, 0.4);
}

.user-tab-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.1);
  color: inherit;
  transition: background 0.2s;
}

.user-tab-btn.active .user-tab-badge {
  background: rgba(0, 0, 0, 0.18);
  color: #000;
}

/* Profile Sections (Overview mode) */
.profile-section {
  margin-bottom: 36px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
}

.section-title {
  font-size: 20px;
  font-weight: 800;
  color: var(--c-text-1, #fff);
  letter-spacing: -0.015em;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.section-title.clickable {
  cursor: pointer;
  transition: color 0.15s ease;
  user-select: none;
}

.section-title.clickable:hover {
  color: var(--c-accent, #1db954);
}

.section-link {
  background: none;
  border: none;
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  cursor: pointer;
  transition: color 0.15s ease;
  flex-shrink: 0;
  white-space: nowrap;
}

.section-link:hover {
  color: var(--c-accent, #1db954);
}

/* Responsive Overview Grid */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 18px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

@media (min-width: 1200px) {
  .overview-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 20px;
  }
}

/* Feed Cards */
.feed-card {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 12px;
  padding: 12px;
  transition: all 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
  box-sizing: border-box;
}

.feed-card:hover {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.1);
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.4);
}

.feed-card-cover {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  aspect-ratio: 1;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
  position: relative;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
  box-sizing: border-box;
}

.feed-card-cover img {
  width: 100%;
  height: 100%;
  max-width: 100%;
  min-width: 0;
  object-fit: cover;
  display: block;
}

.feed-card-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  width: 100%;
}

.feed-card-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
  max-width: 100%;
}

.feed-card-subtitle {
  font-size: 12px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
  max-width: 100%;
}

.play-overlay {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--c-accent, #1db954);
  color: #000;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.5);
  opacity: 0;
  transform: translateY(8px) scale(0.9);
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
  z-index: 2;
}

.feed-card:hover .play-overlay {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.play-overlay:hover {
  transform: scale(1.08) !important;
  background: #1ed760;
}

/* Skeletons */
.feed-card-skeleton {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 12px;
  box-sizing: border-box;
}

.skeleton-feed-cover {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  aspect-ratio: 1;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  margin-bottom: 10px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-feed-title {
  height: 14px;
  width: 80%;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  margin-bottom: 6px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-feed-sub {
  height: 12px;
  width: 50%;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-section-title {
  height: 20px;
  width: 120px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 0.3; }
}

/* Profile Tracks List */
.profile-tracks-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.profile-view-more-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 12px;
}

.profile-view-more-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-1, #fff);
  border-color: rgba(255, 255, 255, 0.12);
}

.tab-pane {
  min-height: 200px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
}

/* Responsive Mobile / Tablet Breakpoints */
@media (max-width: 768px) {
  .user-profile-view {
    padding: 16px 16px calc(var(--player-height, 70px) + var(--nav-height, 64px) + 32px);
    max-width: 100%;
  }

  .profile-hero-card {
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 24px 20px;
    gap: 18px;
    max-width: 100%;
    box-sizing: border-box;
  }

  .hero-avatar {
    width: 130px;
    height: 130px;
    min-width: 130px;
    font-size: 42px;
  }

  .hero-body {
    align-items: center;
    width: 100%;
    max-width: 100%;
  }

  .hero-meta-top {
    justify-content: center;
  }

  .hero-name {
    font-size: 28px;
    max-width: 100%;
  }

  .hero-subline {
    justify-content: center;
    max-width: 100%;
  }

  .hero-actions-bar {
    justify-content: center;
  }

  .user-tabs-bar {
    gap: 8px;
    margin-bottom: 20px;
    padding-bottom: 6px;
    margin-left: -16px;
    margin-right: -16px;
    padding-left: 16px;
    padding-right: 16px;
    width: calc(100% + 32px);
    max-width: calc(100% + 32px);
  }

  .user-tab-btn {
    height: 38px;
    padding: 0 14px;
    font-size: 13px;
    flex-shrink: 0;
  }

  .user-tab-badge {
    font-size: 10px;
    padding: 1px 6px;
  }

  .profile-section {
    margin-bottom: 28px;
  }

  .overview-grid {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 12px;
    width: 100%;
    max-width: 100%;
  }

  .feed-card {
    padding: 10px;
  }

  .play-overlay {
    opacity: 0.9;
    transform: translateY(0);
    width: 32px;
    height: 32px;
    right: 6px;
    bottom: 6px;
  }
}

@media (max-width: 480px) {
  .user-profile-view {
    padding: 14px 14px calc(var(--player-height, 70px) + var(--nav-height, 64px) + 32px);
  }

  .user-tabs-bar {
    margin-left: -14px;
    margin-right: -14px;
    padding-left: 14px;
    padding-right: 14px;
    width: calc(100% + 28px);
    max-width: calc(100% + 28px);
    gap: 6px;
  }

  .user-tab-btn {
    height: 36px;
    padding: 0 12px;
    font-size: 12.5px;
    gap: 6px;
  }

  .hero-avatar {
    width: 108px;
    height: 108px;
    min-width: 108px;
    font-size: 36px;
  }

  .hero-name {
    font-size: 24px;
  }

  .section-title {
    font-size: 18px;
  }

  .profile-section {
    margin-bottom: 22px;
  }

  .overview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    width: 100%;
    max-width: 100%;
  }

  .feed-card {
    padding: 8px;
    border-radius: 10px;
  }

  .feed-card-cover {
    margin-bottom: 8px;
    border-radius: 7px;
  }

  .feed-card-title {
    font-size: 13px;
  }

  .feed-card-subtitle {
    font-size: 11px;
  }

  .feed-card-skeleton {
    padding: 8px;
    border-radius: 10px;
  }

  .skeleton-feed-cover {
    margin-bottom: 8px;
    border-radius: 7px;
  }
}

.btn-pill-secondary {
  padding: 10px 24px;
  border-radius: var(--r-full, 9999px);
  background: var(--c-bg-3, #222);
  color: var(--c-text-1, #fff);
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
}

/* Edit Profile Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.edit-profile-modal {
  width: 100%;
  max-width: 480px;
  background: var(--c-bg-2, #181818);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.6);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: modalPop 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modalPop {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.modal-header h3 {
  font-size: 17px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  margin: 0;
}

.modal-close-btn {
  background: none;
  border: none;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  border-radius: 8px;
  transition: color 0.15s, background 0.15s;
}

.modal-close-btn:hover {
  color: var(--c-text-1, #fff);
  background: rgba(255, 255, 255, 0.08);
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.modal-avatar-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.modal-avatar-preview {
  width: 72px;
  height: 72px;
  min-width: 72px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
  border: 2px solid rgba(255, 255, 255, 0.15);
}

.modal-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.modal-avatar-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.btn-pill-primary.small,
.btn-pill-secondary.small {
  padding: 6px 14px;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0;
}

.btn-pill-primary {
  padding: 10px 24px;
  border-radius: var(--r-full, 9999px);
  background: var(--c-accent, #1db954);
  color: #000;
  border: none;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-pill-primary:hover:not(:disabled) {
  background: #1ed760;
  transform: scale(1.02);
}

.danger-text {
  color: #ff5c5c !important;
}

.modal-form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.modal-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
}

.modal-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.modal-text-input {
  width: 100%;
  padding: 11px 36px 11px 14px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  color: var(--c-text-1, #fff);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.modal-text-input:focus {
  border-color: var(--c-accent, #1db954);
}

.modal-input-clear {
  position: absolute;
  right: 10px;
  background: none;
  border: none;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 4px;
  border-radius: 4px;
}

.modal-input-clear:hover {
  color: var(--c-text-1, #fff);
}

.modal-hint {
  font-size: 12px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  line-height: 1.4;
}

.modal-privacy-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
}

.modal-privacy-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.modal-privacy-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1, #fff);
}

.modal-privacy-desc {
  font-size: 11px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

/* Toggle */
.toggle {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  transition: 0.3s;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background: white;
  border-radius: 50%;
  transition: 0.3s;
}

.toggle input:checked + .toggle-slider {
  background: var(--c-accent, #1db954);
}

.toggle input:checked + .toggle-slider:before {
  transform: translateX(20px);
}

@media (max-width: 600px) {
  .profile-hero-card {
    padding: 14px 16px;
  }
  .hero-avatar {
    width: 56px;
    height: 56px;
    min-width: 56px;
    font-size: 22px;
  }
  .hero-name {
    font-size: 18px;
  }
  .hero-actions-bar {
    gap: 8px;
  }
  .hero-play-btn {
    padding: 7px 14px;
    font-size: 12px;
  }
  .hero-pill-btn {
    padding: 7px 12px;
    font-size: 12px;
  }
}

/* ─── External Account Badges & Hero Integrations ─── */
.hero-ext-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 9999px;
  padding: 3px 10px;
  cursor: pointer;
  color: var(--c-text-1, #fff);
  font-size: 12px;
  font-weight: 600;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.hero-ext-badge:hover {
  background: rgba(255, 255, 255, 0.14);
  transform: translateY(-1px);
}

.hero-ext-badge.sc-badge {
  border-color: rgba(255, 85, 0, 0.35);
}

.hero-ext-badge.sc-badge:hover {
  border-color: #ff5500;
  box-shadow: 0 4px 14px rgba(255, 85, 0, 0.25);
}

.hero-ext-badge.sp-badge {
  border-color: rgba(29, 185, 84, 0.35);
}

.hero-ext-badge.sp-badge:hover {
  border-color: #1db954;
  box-shadow: 0 4px 14px rgba(29, 185, 84, 0.25);
}

.sc-badge-inline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #ff5500;
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  border-radius: 4px;
  padding: 1px 5px;
  line-height: 1.2;
  letter-spacing: 0.5px;
}

.sp-badge-inline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #1db954;
  color: #000;
  font-size: 10px;
  font-weight: 800;
  border-radius: 4px;
  padding: 1px 6px;
  line-height: 1.2;
}

.sp-icon-inline {
  color: #1db954;
  flex-shrink: 0;
}

.ext-badge-name {
  max-width: 130px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ─── External Account Tabs in user-tabs-bar ─── */
.user-tab-btn.sc-tab-btn {
  border-color: rgba(255, 85, 0, 0.25);
}

.user-tab-btn.sc-tab-btn.active {
  background: #ff5500;
  color: #fff;
  border-color: #ff5500;
  box-shadow: 0 4px 16px rgba(255, 85, 0, 0.4);
}

.user-tab-btn.sp-tab-btn {
  border-color: rgba(29, 185, 84, 0.25);
}

.user-tab-btn.sp-tab-btn.active {
  background: #1db954;
  color: #000;
  border-color: #1db954;
  box-shadow: 0 4px 16px rgba(29, 185, 84, 0.4);
}

.sc-badge-num {
  background: rgba(255, 85, 0, 0.2) !important;
  color: #ff7733 !important;
}

.user-tab-btn.sc-tab-btn.active .sc-badge-num {
  background: rgba(0, 0, 0, 0.25) !important;
  color: #fff !important;
}

.sp-badge-num {
  background: rgba(29, 185, 84, 0.2) !important;
  color: #1db954 !important;
}

.user-tab-btn.sp-tab-btn.active .sp-badge-num {
  background: rgba(0, 0, 0, 0.25) !important;
  color: #000 !important;
}

/* ─── External Profile Strips (Header in SC / Spotify Tabs) ─── */
.ext-profile-strip {
  position: relative;
  overflow: hidden;
  border-radius: 20px;
  background: var(--c-bg-2, #181818);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 24px 28px;
  margin-bottom: 28px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
  display: flex;
  align-items: center;
  gap: 24px;
}

.sc-profile-strip {
  background: linear-gradient(135deg, rgba(255, 85, 0, 0.08) 0%, rgba(20, 20, 20, 0.8) 100%);
  border-color: rgba(255, 85, 0, 0.2);
}

.sp-profile-strip {
  background: linear-gradient(135deg, rgba(29, 185, 84, 0.08) 0%, rgba(20, 20, 20, 0.8) 100%);
  border-color: rgba(29, 185, 84, 0.2);
}

.ext-strip-avatar {
  width: 80px;
  height: 80px;
  min-width: 80px;
  border-radius: 50%;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ext-strip-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sc-badge-large {
  font-size: 24px;
  font-weight: 800;
  color: #ff5500;
}

.sp-avatar {
  background: rgba(29, 185, 84, 0.1);
  border-color: rgba(29, 185, 84, 0.3);
}

.sp-icon-large {
  color: #1db954;
}

.ext-strip-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ext-strip-platform {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ext-verified-badge {
  font-size: 11px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  font-weight: 500;
}

.ext-strip-name {
  font-size: 22px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ext-strip-sub {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
}

.ext-strip-handle {
  font-weight: 500;
}

.ext-strip-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  text-decoration: none;
  font-size: 12px;
  transition: color 0.2s ease;
}

.ext-strip-link:hover {
  color: var(--c-text-1, #fff);
  text-decoration: underline;
}

.ext-strip-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.ext-stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 8px 16px;
  min-width: 70px;
}

.ext-stat-num {
  font-size: 18px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
}

.ext-stat-lbl {
  font-size: 11px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
}

/* ─── SoundCloud Subtabs Bar (Playlists vs Releases) ─── */
.sc-subtabs-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.sc-subtab-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-subtab-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-1, #fff);
}

.sc-subtab-btn.active {
  background: rgba(255, 85, 0, 0.15);
  border-color: #ff5500;
  color: #fff;
}

.subtab-count {
  font-size: 11px;
  background: rgba(255, 255, 255, 0.1);
  padding: 1px 6px;
  border-radius: 9999px;
}

.sc-subtab-btn.active .subtab-count {
  background: #ff5500;
  color: #fff;
}

/* ─── External Playlist Detail View ─── */
.sc-playlist-detail-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sc-playlist-detail-header {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.btn-back-pill {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--c-text-1, #fff);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-back-pill:hover {
  background: rgba(255, 255, 255, 0.14);
  transform: translateX(-2px);
}

.sc-playlist-detail-meta {
  display: flex;
  align-items: center;
  gap: 20px;
}

.sc-playlist-detail-cover {
  width: 100px;
  height: 100px;
  min-width: 100px;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.sc-playlist-detail-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sc-playlist-detail-text {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sc-detail-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  margin: 0;
}

.sc-detail-sub {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
}

/* ─── Lists & Cards ─── */
.ext-tracks-list,
.sc-playlist-tracks-list,
.ext-tracks-overview-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-title-with-badge {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-title-with-badge.clickable {
  cursor: pointer;
}

.section-title-with-badge.clickable:hover .section-title {
  color: var(--c-accent, #1db954);
}

.sp-icon-title {
  color: #1db954;
}

.sc-cover-box {
  background: linear-gradient(135deg, rgba(255, 85, 0, 0.2) 0%, rgba(20, 20, 20, 0.8) 100%) !important;
}

.sp-cover-box {
  background: linear-gradient(135deg, rgba(29, 185, 84, 0.2) 0%, rgba(20, 20, 20, 0.8) 100%) !important;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sp-card-icon {
  color: #1db954;
  opacity: 0.8;
}

.section-badge-pill {
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.1);
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
}

.sp-date {
  color: var(--c-text-3, rgba(255, 255, 255, 0.4));
  font-size: 11px;
}

.load-more-box {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

/* ─── Profile Active Ingestion / Imports Panel ─── */
.profile-active-imports-panel {
  background: rgba(20, 24, 33, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(16px);
  border-radius: 16px;
  padding: 16px 20px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  animation: panelFadeIn 0.3s ease;
}

@keyframes panelFadeIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.panel-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.panel-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-text-1, #fff);
}

.section-icon-pulse {
  color: #ff6600;
  animation: iconPulse 2s infinite ease-in-out;
}

@keyframes iconPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.15); opacity: 0.75; }
}

.panel-section-count {
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
  padding: 1px 7px;
  border-radius: 12px;
}

.panel-overall-progress {
  font-size: 12px;
  font-weight: 600;
  color: var(--c-accent, #1db954);
}

.panel-import-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.profile-import-card {
  position: relative;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 12px 14px 14px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.profile-import-card:hover {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.16);
}

.profile-import-card.exportify {
  border-color: rgba(29, 185, 84, 0.3);
  background: rgba(29, 185, 84, 0.06);
}

.profile-import-card.import {
  border-color: rgba(255, 85, 0, 0.3);
  background: rgba(255, 85, 0, 0.06);
}

.profile-import-card.completed {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(16, 28, 22, 0.6);
}

.import-card-top {
  display: flex;
  align-items: center;
  gap: 12px;
}

.import-icon-badge {
  position: relative;
  width: 32px;
  height: 32px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.profile-import-card.exportify .import-icon-badge {
  background: linear-gradient(135deg, #1db954 0%, #15883e 100%);
}

.profile-import-card.import .import-icon-badge {
  background: linear-gradient(135deg, #ff6600 0%, #cc4400 100%);
}

.import-spinner {
  position: absolute;
  inset: -2px;
  border: 2px solid transparent;
  border-top-color: #fff;
  border-radius: 11px;
  animation: spin 0.9s linear infinite;
}

.import-status-glyph.success {
  color: #22c55e;
}

.import-status-glyph.error {
  color: #ef4444;
}

.import-main-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.import-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.import-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.import-pct-badge {
  font-size: 11px;
  font-weight: 700;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 6px;
  border-radius: 6px;
  flex-shrink: 0;
}

.import-stats-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.import-tracks-count {
  font-size: 11px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
}

.import-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.import-action-btn {
  background: transparent;
  border: none;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  padding: 5px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.import-action-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: var(--c-text-1, #fff);
}

.import-action-btn.cancel:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
}

.import-subtext {
  font-size: 11px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.55));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 8px;
  margin-bottom: 6px;
}

.import-download-bar {
  height: 2px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 4px;
}

.import-download-fill {
  height: 100%;
  background: #3b82f6;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.import-progress-bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  overflow: hidden;
}

.import-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6600, #ff8533);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.profile-import-card.exportify .import-progress-fill {
  background: linear-gradient(90deg, #1db954, #1ed760);
}

.import-progress-fill.completed {
  background: #22c55e;
}

/* ─── SC Playlist Detail Sync Action ─── */
.sc-detail-actions-row {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.sc-sync-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #ff5500 0%, #cc4400 100%);
  color: #fff;
  border: none;
  padding: 10px 18px;
  border-radius: 9999px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(255, 85, 0, 0.35);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.sc-sync-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #ff6600 0%, #dd4400 100%);
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(255, 85, 0, 0.45);
}

.sc-sync-btn:active:not(:disabled) {
  transform: translateY(0);
}

.sc-sync-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
