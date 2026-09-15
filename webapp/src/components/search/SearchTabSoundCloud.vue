<template>
  <div class="soundcloud-results-mode">
    <!-- Back to full search breadcrumb bar -->
    <div class="sc-nav-breadcrumb-bar">
      <button class="sc-back-search-btn" @click="$emit('resetToAllSearch')">
        <ArrowLeft :size="15" />
        <span>Все разделы поиска</span>
      </button>
      <div class="sc-service-pill sc">
        <span class="sc-badge">SC</span>
        <span>SoundCloud</span>
      </div>
    </div>

    <!-- Sub-tab Switcher (4 tabs) -->
    <div class="sc-tab-switcher">
      <button 
        class="sc-subtab-btn" 
        :class="{ active: scSubTab === 'search' }"
        @click="$emit('setScSubTab', 'search')"
      >
        <Globe :size="15" />
        <span>Поиск</span>
        <span v-if="soundcloudResults.length > 0" class="sc-subtab-count">{{ soundcloudResults.length }}</span>
      </button>
      <button 
        class="sc-subtab-btn" 
        :class="{ active: scSubTab === 'likes' }"
        @click="$emit('setScSubTab', 'likes')"
      >
        <Heart :size="15" />
        <span>Лайки</span>
        <span v-if="scAccount?.likes_count || scLikes.length" class="sc-subtab-count">
          {{ scAccount?.likes_count || scLikes.length }}
        </span>
      </button>
      <button 
        class="sc-subtab-btn" 
        :class="{ active: scSubTab === 'tracks' }"
        @click="$emit('setScSubTab', 'tracks')"
      >
        <Music :size="15" />
        <span>Мои треки</span>
        <span v-if="scAccount?.tracks_count || scTracks.length" class="sc-subtab-count">
          {{ scAccount?.tracks_count || scTracks.length }}
        </span>
      </button>
      <button 
        class="sc-subtab-btn" 
        :class="{ active: scSubTab === 'playlists' }"
        @click="$emit('setScSubTab', 'playlists')"
      >
        <Folder :size="15" />
        <span>Плейлисты</span>
        <span v-if="scPlaylists.length > 0" class="sc-subtab-count">{{ scPlaylists.length }}</span>
      </button>
    </div>

    <!-- Account Connected Header Card (visible across likes, tracks, playlists) -->
    <div v-if="scAccount?.connected && scSubTab !== 'search'" class="sc-likes-header-card">
      <div class="sc-likes-user-bar">
        <img 
          v-if="scAccount.avatar_url" 
          :src="getCoverUrl(scAccount.avatar_url, CoverSize.SMALL)" 
          alt="" 
          class="sc-likes-avatar"
          referrerpolicy="no-referrer" 
        />
        <div v-else class="sc-likes-avatar-placeholder">
          <Radio :size="18" />
        </div>
        <div class="sc-likes-user-meta">
          <span class="sc-likes-username">{{ scAccount.display_name || scAccount.username }}</span>
          <div class="sc-user-badges-row">
            <button 
              class="sc-meta-stat-pill" 
              :class="{ active: scSubTab === 'likes' }" 
              @click="$emit('setScSubTab', 'likes')"
              title="Перейти к лайкам"
            >
              ❤️ {{ scAccount.likes_count || scLikes.length }} лайков
            </button>
            <button 
              class="sc-meta-stat-pill" 
              :class="{ active: scSubTab === 'tracks' }" 
              @click="$emit('setScSubTab', 'tracks')"
              title="Перейти к загруженным трекам"
            >
              🎵 {{ scAccount.tracks_count || scTracks.length }} треков
            </button>
            <button 
              class="sc-meta-stat-pill" 
              :class="{ active: scSubTab === 'playlists' }" 
              @click="$emit('setScSubTab', 'playlists')"
              title="Перейти к плейлистам"
            >
              📁 {{ scPlaylists.length ? `${scPlaylists.length} плейлистов` : 'Плейлисты' }}
            </button>
          </div>
        </div>
      </div>

      <div class="sc-likes-header-actions">
        <!-- Actions depending on active sub-tab -->
        <template v-if="scSubTab === 'likes'">
          <button 
            class="sc-sync-btn"
            :disabled="isSyncingAllLikes || isScLikesLoading || unimportedLikesCount === 0"
            @click="$emit('handleSyncAllLikes')"
            title="Импортировать все новые треки из лайков в медиатеку и Telegram-канал"
          >
            <div v-if="isSyncingAllLikes" class="spinner small"></div>
            <CloudDownload v-else :size="15" />
            <span>{{ isSyncingAllLikes ? 'Синхронизация...' : `Синхронизировать новые (${unimportedLikesCount})` }}</span>
          </button>
          <button 
            class="sc-refresh-icon-btn" 
            :disabled="isScLikesLoading"
            @click="$emit('fetchScLikes', true)"
            title="Обновить список лайков"
          >
            <RefreshCw :size="15" :class="{ 'spin-icon': isScLikesLoading }" />
          </button>
        </template>

        <template v-else-if="scSubTab === 'tracks'">
          <button 
            class="sc-sync-btn"
            :disabled="isSyncingAllTracks || isScTracksLoading || unimportedTracksCount === 0"
            @click="$emit('handleSyncAllTracks')"
            title="Импортировать все загруженные треки в медиатеку и Telegram-канал"
          >
            <div v-if="isSyncingAllTracks" class="spinner small"></div>
            <CloudDownload v-else :size="15" />
            <span>{{ isSyncingAllTracks ? 'Синхронизация...' : `Синхронизировать новые (${unimportedTracksCount})` }}</span>
          </button>
          <button 
            class="sc-refresh-icon-btn" 
            :disabled="isScTracksLoading"
            @click="$emit('fetchScTracks', true)"
            title="Обновить список треков"
          >
            <RefreshCw :size="15" :class="{ 'spin-icon': isScTracksLoading }" />
          </button>
        </template>

        <template v-else-if="scSubTab === 'playlists'">
          <button 
            class="sc-refresh-icon-btn" 
            :disabled="isScPlaylistsLoading"
            @click="$emit('fetchScPlaylists')"
            title="Обновить список плейлистов"
          >
            <RefreshCw :size="15" :class="{ 'spin-icon': isScPlaylistsLoading }" />
          </button>
        </template>
      </div>
    </div>

    <!-- Sync progress bar if active (visible globally across SC tabs) -->
    <div v-if="syncJobProgress" class="sc-sync-progress-banner">
      <div class="sc-sync-info-row">
        <span class="sc-sync-msg">
          <CloudDownload :size="14" class="sc-pulse-icon" />
          {{ syncJobProgress.title || 'Синхронизация SoundCloud' }}: 
          <b>{{ syncJobProgress.current_track_title || 'Загрузка...' }}</b>
        </span>
        <span class="sc-sync-count">{{ syncJobProgress.processed_tracks }} / {{ syncJobProgress.total_tracks }}</span>
      </div>
      <div class="sc-sync-bar-track">
        <div 
          class="sc-sync-bar-fill" 
          :style="{ width: `${Math.round((syncJobProgress.processed_tracks / (syncJobProgress.total_tracks || 1)) * 100)}%` }"
        ></div>
      </div>
    </div>

    <!-- ==================== 1. SEARCH MODE ==================== -->
    <template v-if="scSubTab === 'search'">
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
        <ExternalTrackItem
          v-for="item in soundcloudResults"
          :key="item.url"
          :item="item"
          variant="soundcloud"
          :show-badges="true"
          :is-importing="importingTrackUrl === item.url"
          :is-downloading="tasksStore.isTrackDownloading(item.url)"
          :is-queued="tasksStore.isTrackQueued(item.url)"
          :is-in-library="isTrackInLibrary(item)"
          @play="$emit('quickPlaySoundCloud', item)"
          @add="$emit('quickAddSoundCloud', item)"
        />

        <!-- Load More SoundCloud Button -->
        <div class="sc-load-more-wrap">
          <button 
            v-if="soundcloudResults.length < 60"
            class="sc-load-more-btn"
            :disabled="isLoadingMoreSoundCloud"
            @click="$emit('loadMoreSoundCloud')"
          >
            <div v-if="isLoadingMoreSoundCloud" class="spinner small"></div>
            <template v-else>Загрузить ещё (до 60)</template>
          </button>
          <span v-else class="sc-end-notice">Показаны 60 лучших результатов SoundCloud</span>
        </div>
      </div>

      <NoResultsBox 
        v-else-if="!isSoundCloudSearching" 
        :text="searchQuery.trim() ? 'На SoundCloud ничего не найдено' : 'Введите поисковый запрос выше для поиска треков на SoundCloud'" 
      />
    </template>

    <!-- ==================== 2. LIKES MODE ==================== -->
    <template v-else-if="scSubTab === 'likes'">
      <div v-if="scAccount?.connected">
        <!-- Status Filter Pills -->
        <div class="sc-filter-pills-bar">
          <button 
            class="sc-filter-pill" 
            :class="{ active: likesFilter === 'all' }"
            @click="likesFilter = 'all'"
          >
            Все ({{ scLikes.length }})
          </button>
          <button 
            class="sc-filter-pill" 
            :class="{ active: likesFilter === 'new' }"
            @click="likesFilter = 'new'"
          >
            Только новые ({{ unimportedLikesCount }})
          </button>
          <button 
            class="sc-filter-pill" 
            :class="{ active: likesFilter === 'imported' }"
            @click="likesFilter = 'imported'"
          >
            В медиатеке ({{ scLikes.length - unimportedLikesCount }})
          </button>
        </div>

        <!-- Active Search Filter Banner for Likes -->
        <div v-if="searchQuery.trim() && scLikes.length > 0" class="sc-likes-filter-notice">
          <span>Фильтр лайков: <b>«{{ searchQuery.trim() }}»</b> (найдено {{ displayedLikes.length }})</span>
          <button class="clear-filter-mini-btn" @click="$emit('clearSearchInput')" title="Сбросить фильтр поиска">
            ✕ Сбросить
          </button>
        </div>

        <!-- Loading indicator -->
        <div v-if="isScLikesLoading && scLikes.length === 0" class="section-loading-indicator">
          <div class="spinner small"></div>
          <span>Загрузка лайков с SoundCloud...</span>
        </div>

        <!-- Likes Track List -->
        <div v-if="displayedLikes.length > 0" class="sc-results-list full-list">
          <ExternalTrackItem
            v-for="item in displayedLikes"
            :key="item.url"
            :item="item"
            variant="soundcloud"
            :show-badges="true"
            :is-importing="importingTrackUrl === item.url"
            :is-downloading="tasksStore.isTrackDownloading(item.url)"
            :is-queued="tasksStore.isTrackQueued(item.url)"
            :is-in-library="isTrackInLibrary(item)"
            @play="$emit('quickPlaySoundCloud', item)"
            @add="$emit('quickAddSoundCloud', item)"
          />

          <!-- Load more likes button -->
          <div v-if="scLikesCursor" class="sc-load-more-wrap">
            <button 
              class="sc-load-more-btn"
              :disabled="isLoadingMoreScLikes || isSearchingDeeperLikes"
              @click="searchQuery.trim() ? $emit('loadAllLikesUntilMatch') : $emit('loadMoreScLikes')"
            >
              <div v-if="isLoadingMoreScLikes || isSearchingDeeperLikes" class="spinner small"></div>
              <template v-else>
                {{ searchQuery.trim() ? 'Искать глубже в остальных лайках' : `Загрузить ещё лайки (${scLikes.length} из ${scAccount?.likes_count || '...'})` }}
              </template>
            </button>
          </div>
        </div>

        <!-- No results in likes matching filter -->
        <NoResultsBox 
          v-else-if="!isScLikesLoading && scLikes.length > 0" 
          :text="searchQuery.trim() ? `В лайках нет треков по запросу «${searchQuery}»` : 'Нет треков, соответствующих выбранному фильтру'" 
        />

        <!-- Empty likes -->
        <NoResultsBox 
          v-else-if="!isScLikesLoading && scLikes.length === 0" 
          text="Лайков на SoundCloud пока нет" 
          hint="Поставьте лайки на SoundCloud и нажмите «Обновить»" 
        />
      </div>

      <!-- Not Connected Prompt -->
      <div v-else class="sc-not-connected-banner">
        <div class="sc-banner-icon">
          <Radio :size="32" />
        </div>
        <h4 class="sc-banner-title">Аккаунт SoundCloud не подключен</h4>
        <p class="sc-banner-desc">
          Привяжите ваш профиль SoundCloud в настройках, чтобы просматривать лайки, треки, сеты и автоматически сохранять аудиофайлы в личный Telegram-канал.
        </p>
        <button class="sc-btn primary" @click="$emit('goToSettings')">
          <Settings :size="15" />
          <span>Открыть настройки</span>
        </button>
      </div>
    </template>

    <!-- ==================== 3. USER TRACKS MODE (Мои треки) ==================== -->
    <template v-else-if="scSubTab === 'tracks'">
      <div v-if="scAccount?.connected">
        <!-- Status Filter Pills -->
        <div class="sc-filter-pills-bar">
          <button 
            class="sc-filter-pill" 
            :class="{ active: tracksFilter === 'all' }"
            @click="tracksFilter = 'all'"
          >
            Все ({{ scTracks.length }})
          </button>
          <button 
            class="sc-filter-pill" 
            :class="{ active: tracksFilter === 'new' }"
            @click="tracksFilter = 'new'"
          >
            Только новые ({{ unimportedTracksCount }})
          </button>
          <button 
            class="sc-filter-pill" 
            :class="{ active: tracksFilter === 'imported' }"
            @click="tracksFilter = 'imported'"
          >
            В медиатеке ({{ scTracks.length - unimportedTracksCount }})
          </button>
        </div>

        <!-- Search Notice for Tracks -->
        <div v-if="searchQuery.trim() && scTracks.length > 0" class="sc-likes-filter-notice">
          <span>Фильтр треков: <b>«{{ searchQuery.trim() }}»</b> (найдено {{ displayedTracks.length }})</span>
          <button class="clear-filter-mini-btn" @click="$emit('clearSearchInput')" title="Сбросить фильтр поиска">
            ✕ Сбросить
          </button>
        </div>

        <!-- Loading indicator -->
        <div v-if="isScTracksLoading && scTracks.length === 0" class="section-loading-indicator">
          <div class="spinner small"></div>
          <span>Загрузка авторских треков с SoundCloud...</span>
        </div>

        <!-- User Tracks List -->
        <div v-if="displayedTracks.length > 0" class="sc-results-list full-list">
          <ExternalTrackItem
            v-for="item in displayedTracks"
            :key="item.url"
            :item="item"
            variant="soundcloud"
            :show-badges="true"
            :is-importing="importingTrackUrl === item.url"
            :is-downloading="tasksStore.isTrackDownloading(item.url)"
            :is-queued="tasksStore.isTrackQueued(item.url)"
            :is-in-library="isTrackInLibrary(item)"
            @play="$emit('quickPlaySoundCloud', item)"
            @add="$emit('quickAddSoundCloud', item)"
          />

          <!-- Load more user tracks button -->
          <div v-if="scTracksCursor" class="sc-load-more-wrap">
            <button 
              class="sc-load-more-btn"
              :disabled="isLoadingMoreScTracks"
              @click="$emit('loadMoreScTracks')"
            >
              <div v-if="isLoadingMoreScTracks" class="spinner small"></div>
              <template v-else>
                Загрузить ещё треки ({{ scTracks.length }} из {{ scAccount?.tracks_count || '...' }})
              </template>
            </button>
          </div>
        </div>

        <!-- No results in tracks matching filter -->
        <NoResultsBox 
          v-else-if="!isScTracksLoading && scTracks.length > 0" 
          :text="searchQuery.trim() ? `В ваших треках нет совпадений по запросу «${searchQuery}»` : 'Нет треков, соответствующих выбранному фильтру'" 
        />

        <!-- Empty tracks -->
        <NoResultsBox 
          v-else-if="!isScTracksLoading && scTracks.length === 0" 
          text="Вы пока не загружали треки на SoundCloud" 
          hint="Треки, которые вы выкладываете на SoundCloud, появятся здесь автоматически" 
        />
      </div>

      <!-- Not Connected Prompt -->
      <div v-else class="sc-not-connected-banner">
        <div class="sc-banner-icon">
          <Radio :size="32" />
        </div>
        <h4 class="sc-banner-title">Аккаунт SoundCloud не подключен</h4>
        <p class="sc-banner-desc">
          Привяжите ваш профиль SoundCloud в настройках для синхронизации ваших треков и плейлистов.
        </p>
        <button class="sc-btn primary" @click="$emit('goToSettings')">
          <Settings :size="15" />
          <span>Открыть настройки</span>
        </button>
      </div>
    </template>

    <!-- ==================== 4. PLAYLISTS MODE ==================== -->
    <template v-else-if="scSubTab === 'playlists'">
      <div v-if="scAccount?.connected">
        <!-- A. PLAYLIST DETAILS VIEW (when a playlist is selected) -->
        <div v-if="selectedScPlaylist" class="sc-playlist-detail-container">
          <!-- Back to all playlists button -->
          <button class="sc-back-to-playlists-btn" @click="$emit('clearSelectedScPlaylist')">
            <ArrowLeft :size="15" />
            <span>Назад ко всем плейлистам SoundCloud</span>
          </button>

          <!-- Playlist Header Card -->
          <div class="sc-playlist-banner-card">
            <div class="sc-playlist-cover-wrap">
              <img 
                v-if="selectedScPlaylist.artwork_url" 
                :src="getCoverUrl(selectedScPlaylist.artwork_url, CoverSize.MEDIUM)" 
                alt="" 
                class="sc-playlist-cover"
                referrerpolicy="no-referrer" 
              />
              <div v-else class="sc-playlist-cover-placeholder">
                <Disc3 :size="40" />
              </div>
            </div>

            <div class="sc-playlist-info-meta">
              <div class="sc-playlist-type-tag">
                <span>{{ selectedScPlaylist.is_liked ? 'Понравившийся плейлист' : 'Мой плейлист SoundCloud' }}</span>
              </div>
              <h2 class="sc-playlist-title">{{ selectedScPlaylist.title }}</h2>
              <div class="sc-playlist-sub-row">
                <span class="sc-playlist-author">Автор: <b>{{ selectedScPlaylist.author }}</b></span>
                <span class="sc-dot-divider">•</span>
                <span>{{ selectedScPlaylist.track_count }} треков</span>
                <span v-if="selectedScPlaylist.duration" class="sc-dot-divider">•</span>
                <span v-if="selectedScPlaylist.duration">{{ formatDuration(selectedScPlaylist.duration) }}</span>
              </div>

              <div class="sc-playlist-actions-row">
                <button 
                  class="sc-sync-btn sc-playlist-main-sync-btn"
                  :disabled="isSyncingPlaylist || isScPlaylistTracksLoading || scPlaylistTracks.length === 0"
                  @click="$emit('handleSyncPlaylist', selectedScPlaylist)"
                  title="Создать плейлист в TG Player и загрузить треки в Telegram-канал"
                >
                  <div v-if="isSyncingPlaylist" class="spinner small"></div>
                  <CloudDownload v-else :size="16" />
                  <span>{{ isSyncingPlaylist ? 'Синхронизация плейлиста...' : `Синхронизировать в TG Player (${selectedScPlaylist.track_count})` }}</span>
                </button>

                <a 
                  v-if="selectedScPlaylist.permalink_url" 
                  :href="selectedScPlaylist.permalink_url" 
                  target="_blank" 
                  class="sc-link-external-btn"
                  title="Открыть плейлист на SoundCloud"
                >
                  <ExternalLink :size="15" />
                  <span>SoundCloud</span>
                </a>
              </div>
            </div>
          </div>

          <!-- Playlist Tracks List -->
          <div v-if="isScPlaylistTracksLoading" class="section-loading-indicator">
            <div class="spinner small"></div>
            <span>Загрузка треков плейлиста...</span>
          </div>

          <div v-else-if="scPlaylistTracks.length > 0" class="sc-results-list full-list">
            <ExternalTrackItem
              v-for="item in scPlaylistTracks"
              :key="item.url"
              :item="item"
              variant="soundcloud"
              :show-badges="true"
              :is-importing="importingTrackUrl === item.url"
              :is-downloading="tasksStore.isTrackDownloading(item.url)"
              :is-queued="tasksStore.isTrackQueued(item.url)"
              :is-in-library="isTrackInLibrary(item)"
              @play="$emit('quickPlaySoundCloud', item)"
              @add="$emit('quickAddSoundCloud', item)"
            />
          </div>

          <NoResultsBox 
            v-else-if="!isScPlaylistTracksLoading" 
            text="В этом плейлисте нет треков" 
          />
        </div>

        <!-- B. PLAYLISTS GRID VIEW -->
        <div v-else>
          <!-- Playlists Filter Bar -->
          <div class="sc-filter-pills-bar">
            <button 
              class="sc-filter-pill" 
              :class="{ active: playlistsFilter === 'all' }"
              @click="playlistsFilter = 'all'"
            >
              Все ({{ scPlaylists.length }})
            </button>
            <button 
              class="sc-filter-pill" 
              :class="{ active: playlistsFilter === 'created' }"
              @click="playlistsFilter = 'created'"
            >
              Мои плейлисты ({{ createdPlaylistsCount }})
            </button>
            <button 
              class="sc-filter-pill" 
              :class="{ active: playlistsFilter === 'liked' }"
              @click="playlistsFilter = 'liked'"
            >
              Сохранённые ({{ likedPlaylistsCount }})
            </button>
          </div>

          <!-- Loading Indicator -->
          <div v-if="isScPlaylistsLoading && scPlaylists.length === 0" class="section-loading-indicator">
            <div class="spinner small"></div>
            <span>Загрузка плейлистов с SoundCloud...</span>
          </div>

          <!-- Playlists Grid -->
          <div v-if="displayedPlaylists.length > 0" class="sc-playlists-grid">
            <div 
              v-for="pl in displayedPlaylists" 
              :key="pl.id" 
              class="sc-playlist-card"
              @click="$emit('selectScPlaylist', pl)"
            >
              <div class="sc-card-artwork-box">
                <img 
                  v-if="pl.artwork_url" 
                  :src="getCoverUrl(pl.artwork_url, CoverSize.MEDIUM)" 
                  alt="" 
                  class="sc-card-artwork"
                  referrerpolicy="no-referrer" 
                  loading="lazy" 
                />
                <div v-else class="sc-card-artwork-placeholder">
                  <Disc3 :size="32" />
                </div>
                <div class="sc-card-badge-layer">
                  <span v-if="pl.is_liked" class="sc-card-pill liked">❤️ Лайк</span>
                  <span v-else class="sc-card-pill created">📁 Сет</span>
                </div>
              </div>

              <div class="sc-card-body">
                <h4 class="sc-card-title" :title="pl.title">{{ pl.title }}</h4>
                <span class="sc-card-author">{{ pl.author }}</span>
                <div class="sc-card-footer-row">
                  <span class="sc-card-stat">{{ pl.track_count }} треков</span>
                  <span v-if="pl.duration" class="sc-card-stat">• {{ formatDuration(pl.duration) }}</span>
                </div>
              </div>

              <div class="sc-card-hover-action" @click.stop="$emit('handleSyncPlaylist', pl)">
                <CloudDownload :size="15" />
                <span>Синхронизировать</span>
              </div>
            </div>
          </div>

          <!-- Empty Playlists -->
          <NoResultsBox 
            v-else-if="!isScPlaylistsLoading && scPlaylists.length === 0" 
            text="Плейлисты на SoundCloud не найдены" 
            hint="Создайте сеты или поставьте лайки плейлистам на SoundCloud и нажмите «Обновить»" 
          />

          <NoResultsBox 
            v-else-if="!isScPlaylistsLoading && displayedPlaylists.length === 0" 
            text="Нет плейлистов в выбранной категории" 
          />
        </div>
      </div>

      <!-- Not Connected Prompt -->
      <div v-else class="sc-not-connected-banner">
        <div class="sc-banner-icon">
          <Radio :size="32" />
        </div>
        <h4 class="sc-banner-title">Аккаунт SoundCloud не подключен</h4>
        <p class="sc-banner-desc">
          Привяжите ваш профиль SoundCloud в настройках для синхронизации плейлистов.
        </p>
        <button class="sc-btn primary" @click="$emit('goToSettings')">
          <Settings :size="15" />
          <span>Открыть настройки</span>
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { 
  ArrowLeft, 
  Globe, 
  Heart, 
  CloudDownload, 
  RefreshCw, 
  Radio, 
  Settings, 
  Music, 
  Folder, 
  ExternalLink,
  Disc3 
} from 'lucide-vue-next'
import ExternalTrackItem from '@/components/ExternalTrackItem.vue'
import NoResultsBox from '@/components/NoResultsBox.vue'
import { useTasksStore } from '@/stores/tasks'
import { formatDuration, getCoverUrl, CoverSize } from '@/utils'

const props = defineProps({
  soundcloudResults: { type: Array, required: true },
  searchQuery: { type: String, required: true },
  scSubTab: { type: String, required: true },
  isSoundCloudSearching: { type: Boolean, required: true },
  isLoadingMoreSoundCloud: { type: Boolean, required: true },
  importingTrackUrl: { type: String, default: null },
  
  scAccount: { type: Object, default: null },
  
  // Likes
  scLikes: { type: Array, required: true },
  filteredScLikes: { type: Array, required: true },
  scLikesCursor: { type: String, default: null },
  isScLikesLoading: { type: Boolean, required: true },
  isLoadingMoreScLikes: { type: Boolean, required: true },
  isSearchingDeeperLikes: { type: Boolean, required: true },
  isSyncingAllLikes: { type: Boolean, required: true },
  syncJobProgress: { type: Object, default: null },
  unimportedLikesCount: { type: Number, required: true },

  // User Tracks (uploads)
  scTracks: { type: Array, default: () => [] },
  scTracksCursor: { type: String, default: null },
  isScTracksLoading: { type: Boolean, default: false },
  isLoadingMoreScTracks: { type: Boolean, default: false },
  isSyncingAllTracks: { type: Boolean, default: false },
  unimportedTracksCount: { type: Number, default: 0 },

  // Playlists
  scPlaylists: { type: Array, default: () => [] },
  isScPlaylistsLoading: { type: Boolean, default: false },
  selectedScPlaylist: { type: Object, default: null },
  scPlaylistTracks: { type: Array, default: () => [] },
  isScPlaylistTracksLoading: { type: Boolean, default: false },
  isSyncingPlaylist: { type: Boolean, default: false },
})

const emit = defineEmits([
  'resetToAllSearch',
  'setScSubTab',
  'loadMoreSoundCloud',
  'quickPlaySoundCloud',
  'quickAddSoundCloud',
  
  // Likes
  'handleSyncAllLikes',
  'fetchScLikes',
  'clearSearchInput',
  'loadAllLikesUntilMatch',
  'loadMoreScLikes',
  'goToSettings',

  // Tracks
  'fetchScTracks',
  'loadMoreScTracks',
  'handleSyncAllTracks',

  // Playlists
  'fetchScPlaylists',
  'selectScPlaylist',
  'clearSelectedScPlaylist',
  'handleSyncPlaylist',
])

const tasksStore = useTasksStore()

// Filter state inside tabs
const likesFilter = ref('all') // 'all' | 'new' | 'imported'
const tracksFilter = ref('all') // 'all' | 'new' | 'imported'
const playlistsFilter = ref('all') // 'all' | 'created' | 'liked'

const isTrackInLibrary = (item) => {
  if (!item) return false
  return item.in_library || tasksStore.isTrackCompleted(item.url)
}

// Displayed Likes with status filter & search
const displayedLikes = computed(() => {
  let list = props.searchQuery.trim() ? props.filteredScLikes : props.scLikes
  if (likesFilter.value === 'new') {
    return list.filter(t => !t.in_library)
  }
  if (likesFilter.value === 'imported') {
    return list.filter(t => t.in_library)
  }
  return list
})

// Displayed Tracks with status filter & search
const displayedTracks = computed(() => {
  let list = props.scTracks
  const q = props.searchQuery.trim().toLowerCase()
  if (q) {
    list = list.filter(t => 
      (t.title && t.title.toLowerCase().includes(q)) || 
      (t.artist && t.artist.toLowerCase().includes(q))
    )
  }
  if (tracksFilter.value === 'new') {
    return list.filter(t => !t.in_library)
  }
  if (tracksFilter.value === 'imported') {
    return list.filter(t => t.in_library)
  }
  return list
})

// Counts for Playlists
const createdPlaylistsCount = computed(() => {
  return props.scPlaylists.filter(p => !p.is_liked).length
})

const likedPlaylistsCount = computed(() => {
  return props.scPlaylists.filter(p => p.is_liked).length
})

// Displayed Playlists with category filter
const displayedPlaylists = computed(() => {
  if (playlistsFilter.value === 'created') {
    return props.scPlaylists.filter(p => !p.is_liked)
  }
  if (playlistsFilter.value === 'liked') {
    return props.scPlaylists.filter(p => p.is_liked)
  }
  return props.scPlaylists
})
</script>

<style scoped>
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  letter-spacing: -0.01em;
}

.section-count {
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-3, rgba(255, 255, 255, 0.45));
}

.section-loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  font-size: 13px;
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

/* SoundCloud Navigation & Sub-tabs */
.sc-nav-breadcrumb-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 2px 0;
}

.sc-back-search-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--c-text-1, #fff);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.sc-back-search-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.28);
  color: #ff5500;
  transform: translateX(-2px);
}

.sc-service-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
}

.sc-tab-switcher {
  display: flex;
  gap: 6px;
  margin-bottom: 16px;
  background: rgba(255, 255, 255, 0.03);
  padding: 4px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  overflow-x: auto;
}

.sc-subtab-btn {
  flex: 1;
  min-width: 110px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 8px;
  border: none;
  background: none;
  color: var(--c-text-3);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.sc-subtab-btn:hover {
  color: var(--c-text-1);
}

.sc-subtab-btn.active {
  background: #ff5500;
  color: #fff;
  box-shadow: 0 2px 10px rgba(255, 85, 0, 0.35);
}

.sc-subtab-count {
  font-size: 11px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
}

/* Filter Pills Bar */
.sc-filter-pills-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.sc-filter-pill {
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--c-text-2);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.sc-filter-pill:hover {
  background: rgba(255, 85, 0, 0.15);
  border-color: rgba(255, 85, 0, 0.3);
  color: #ffaa77;
}

.sc-filter-pill.active {
  background: rgba(255, 85, 0, 0.25);
  border-color: #ff5500;
  color: #fff;
}

.sc-likes-filter-notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: rgba(255, 85, 0, 0.1);
  border: 1px solid rgba(255, 85, 0, 0.25);
  border-radius: 10px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--c-text-1);
}

.clear-filter-mini-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 6px;
  color: #ffaa77;
  font-size: 11px;
  padding: 4px 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.clear-filter-mini-btn:hover {
  background: rgba(255, 85, 0, 0.25);
  color: #fff;
}

/* Header Card */
.sc-likes-header-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(255, 85, 0, 0.06);
  border: 1px solid rgba(255, 85, 0, 0.2);
  border-radius: 14px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.sc-likes-user-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sc-likes-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 2px solid #ff5500;
  object-fit: cover;
}

.sc-likes-avatar-placeholder {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 85, 0, 0.2);
  color: #ff5500;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sc-likes-user-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sc-likes-username {
  font-size: 15px;
  font-weight: 700;
  color: var(--c-text-1);
}

.sc-user-badges-row {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.sc-meta-stat-pill {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 2px 8px;
  font-size: 11px;
  color: var(--c-text-2);
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-meta-stat-pill:hover,
.sc-meta-stat-pill.active {
  background: rgba(255, 85, 0, 0.2);
  border-color: rgba(255, 85, 0, 0.4);
  color: #ffaa77;
}

.sc-likes-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sc-sync-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #ff5500;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(255, 85, 0, 0.3);
  transition: all 0.2s ease;
  font-family: inherit;
}

.sc-sync-btn:hover:not(:disabled) {
  background: #ff6611;
  transform: translateY(-1px);
}

.sc-sync-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sc-refresh-icon-btn {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-refresh-icon-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.sc-sync-progress-banner {
  padding: 10px 14px;
  background: rgba(255, 85, 0, 0.1);
  border: 1px solid rgba(255, 85, 0, 0.25);
  border-radius: 10px;
  margin-bottom: 14px;
}

.sc-pulse-icon {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.15); }
}

.sc-sync-info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-1);
  margin-bottom: 6px;
}

.sc-sync-msg {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80%;
}

.sc-sync-bar-track {
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.sc-sync-bar-fill {
  height: 100%;
  background: #ff5500;
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* Playlists Grid */
.sc-playlists-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 12px;
}

.sc-playlist-card {
  position: relative;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  flex-direction: column;
}

.sc-playlist-card:hover {
  background: rgba(255, 85, 0, 0.08);
  border-color: rgba(255, 85, 0, 0.3);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.sc-card-artwork-box {
  position: relative;
  width: 100%;
  padding-top: 100%;
  background: rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.sc-card-artwork {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.sc-playlist-card:hover .sc-card-artwork {
  transform: scale(1.05);
}

.sc-card-artwork-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 85, 0, 0.4);
  background: rgba(255, 85, 0, 0.05);
}

.sc-card-badge-layer {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
}

.sc-card-pill {
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 999px;
  backdrop-filter: blur(8px);
}

.sc-card-pill.liked {
  background: rgba(255, 30, 70, 0.85);
  color: #fff;
}

.sc-card-pill.created {
  background: rgba(255, 85, 0, 0.85);
  color: #fff;
}

.sc-card-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.sc-card-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sc-card-author {
  font-size: 12px;
  color: var(--c-text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sc-card-footer-row {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--c-text-3);
  margin-top: 4px;
}

.sc-card-hover-action {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px;
  background: rgba(255, 85, 0, 0.15);
  border-top: 1px solid rgba(255, 85, 0, 0.2);
  color: #ffaa77;
  font-size: 11px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.sc-playlist-card:hover .sc-card-hover-action {
  background: #ff5500;
  color: #fff;
}

/* Playlist Detail View */
.sc-playlist-detail-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sc-back-to-playlists-btn {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-2);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.sc-back-to-playlists-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  transform: translateX(-2px);
}

.sc-playlist-banner-card {
  display: flex;
  gap: 20px;
  padding: 18px;
  background: rgba(255, 85, 0, 0.06);
  border: 1px solid rgba(255, 85, 0, 0.2);
  border-radius: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.sc-playlist-cover-wrap {
  width: 120px;
  height: 120px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  flex-shrink: 0;
}

.sc-playlist-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sc-playlist-cover-placeholder {
  width: 100%;
  height: 100%;
  background: rgba(255, 85, 0, 0.2);
  color: #ff5500;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sc-playlist-info-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  min-width: 240px;
}

.sc-playlist-type-tag {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #ff7700;
}

.sc-playlist-title {
  font-size: 22px;
  font-weight: 800;
  color: var(--c-text-1);
  margin: 0;
  line-height: 1.2;
}

.sc-playlist-sub-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--c-text-2);
  flex-wrap: wrap;
}

.sc-dot-divider {
  color: rgba(255, 255, 255, 0.3);
}

.sc-playlist-actions-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.sc-playlist-main-sync-btn {
  padding: 9px 18px;
  font-size: 13px;
}

.sc-link-external-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--c-text-2);
  font-size: 12px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s ease;
}

.sc-link-external-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

/* Not connected banner */
.sc-not-connected-banner {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 36px 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px dashed rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  margin-top: 16px;
}

.sc-banner-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(255, 85, 0, 0.12);
  color: #ff5500;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.sc-banner-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0 0 6px 0;
}

.sc-banner-desc {
  font-size: 13px;
  color: var(--c-text-3);
  max-width: 440px;
  line-height: 1.5;
  margin: 0 0 16px 0;
}

.sc-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 9px 16px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  font-family: inherit;
}

.sc-btn.primary {
  background: #ff5500;
  color: #fff;
  box-shadow: 0 4px 12px rgba(255, 85, 0, 0.3);
}

.sc-btn.primary:hover {
  background: #ff6611;
  transform: translateY(-1px);
}
</style>
