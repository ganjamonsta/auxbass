<template>
  <!-- 1. Collapsed Rail Sidebar (Shown in grid when isSidebarCollapsed is true) -->
  <aside v-if="uiStore.isSidebarCollapsed" class="sidebar rail-sidebar">
    <!-- Burger toggle button + App logo -->
    <div class="rail-header">
      <button 
        class="rail-burger-btn" 
        @click="uiStore.openSidebarOverlay" 
        title="Развернуть меню (Ctrl+B)"
      >
        <Menu :size="20" />
      </button>

      <div class="rail-logo-icon" :title="authStore.appName || 'auxbassbot'">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
        </svg>
      </div>
    </div>

    <!-- Main Navigation Icons -->
    <nav class="rail-nav">
      <router-link to="/" class="rail-nav-item" :class="{ active: isActiveExact('/') }" title="Главная">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
        </svg>
        <div class="rail-active-indicator"></div>
      </router-link>

      <router-link 
        to="/search" 
        class="rail-nav-item" 
        :class="{ active: isActive('/search') }"
        @click="onSearchClick"
        title="Поиск"
      >
        <Search :size="22" />
        <div class="rail-active-indicator"></div>
      </router-link>

      <div 
        class="rail-nav-item clickable" 
        :class="{ active: route.name === 'library' }"
        @click="goToLibraryTab('overview')"
        title="Медиатека"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="m16 6 4 14M12 6v14M8 8v12M4 4v16"></path>
        </svg>
        <div class="rail-active-indicator"></div>
      </div>

      <router-link 
        to="/liked" 
        class="rail-nav-item liked-rail-item" 
        :class="{ active: isActive('/liked') }"
        title="Любимые треки"
      >
        <Heart :size="20" :fill="isActive('/liked') ? 'currentColor' : 'none'" />
        <span v-if="likedCount > 0" class="rail-badge">{{ formatRailCount(likedCount) }}</span>
        <div class="rail-active-indicator"></div>
      </router-link>

      <router-link 
        to="/friends" 
        class="rail-nav-item" 
        :class="{ active: isActive('/friends') }"
        title="Подписки"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
          <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
        </svg>
        <div class="rail-active-indicator"></div>
      </router-link>

      <router-link 
        to="/downloaded" 
        class="rail-nav-item offline-rail-item" 
        :class="{ active: isActive('/downloaded') }"
        title="Кэшированные и скачанные треки"
      >
        <FolderDown :size="20" />
        <span v-if="cachedTracksCount > 0" class="rail-badge offline-badge">{{ formatRailCount(cachedTracksCount) }}</span>
        <div class="rail-active-indicator"></div>
      </router-link>

      <router-link 
        to="/settings" 
        class="rail-nav-item import-rail-item" 
        :class="{ active: route.path === '/settings' }"
        title="Импорт и настройки"
      >
        <Upload :size="20" />
        <div class="rail-active-indicator"></div>
      </router-link>
    </nav>

    <!-- Divider -->
    <div class="rail-divider"></div>

    <!-- Playlists Mini Section -->
    <div v-if="displayedPlaylists.length > 0" class="rail-playlists">
      <div 
        v-for="playlist in displayedPlaylists.slice(0, 4)" 
        :key="playlist.id"
        class="rail-playlist-thumb"
        :class="{ active: $route.params.id == playlist.id && $route.name === 'playlist-detail' }"
        @click="$router.push(`/playlist/${playlist.id}`)"
        @contextmenu.prevent="openMenu('playlist', playlist, 'sidebar', $event)"
        :title="playlist.name"
      >
        <img v-if="playlist.covers?.length" :key="playlist.covers[0]" :src="getCoverUrl(playlist.covers[0], CoverSize.SMALL)" alt="" />
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
        </svg>
      </div>
    </div>

    <!-- Rail Footer -->
    <div class="rail-footer">
      <div 
        v-if="authStore.user" 
        class="rail-avatar clickable" 
        :class="{ active: showProfileMenu, 'has-active-imports': tasksStore.hasActiveImports }"
        @click="showProfileMenu = !showProfileMenu"
        @contextmenu.prevent="showProfileMenu = true"
        v-longpress="() => { showProfileMenu = true }"
        title="Мой профиль"
      >
        <img v-if="authStore.userAvatarUrl" :src="authStore.userAvatarUrl" class="sidebar-avatar-img" />
        <template v-else>{{ userInitials }}</template>
        <div v-if="tasksStore.hasActiveImports" class="rail-import-ring"></div>
      </div>
      <router-link to="/settings" class="rail-footer-btn" title="Настройки">
        <Settings :size="18" />
      </router-link>
      <button class="rail-footer-btn logout-btn" @click="logout" title="Выйти">
        <LogOut :size="18" />
      </button>
    </div>
  </aside>

  <!-- 2. Full Sidebar (Shown in grid when isSidebarCollapsed is false) -->
  <aside v-else class="sidebar full-sidebar">
    <!-- Logo with Collapse Toggle Button -->
    <div class="sidebar-logo">
      <div class="logo-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
        </svg>
      </div>
      <span class="logo-text">{{ authStore.appName || 'auxbassbot' }}</span>

      <!-- Collapse to icons button -->
      <button 
        class="sidebar-toggle-btn collapse-toggle-btn" 
        @click="uiStore.setSidebarCollapsed(true, true)" 
        title="Свернуть до иконок"
      >
        <PanelLeftClose :size="18" />
      </button>

      <div 
        v-if="authStore.user" 
        class="header-avatar clickable" 
        @click="goToMyProfile"
        title="Мой профиль"
      >
        <span class="header-avatar-badge">
          <img v-if="authStore.userAvatarUrl" :src="authStore.userAvatarUrl" class="sidebar-avatar-img" />
          <template v-else>{{ userInitials }}</template>
        </span>
      </div>
    </div>

    <!-- Main Navigation -->
    <nav class="sidebar-nav">
      <router-link to="/" class="nav-item" :class="{ active: isActiveExact('/') }">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
        </svg>
        <span>Главная</span>
      </router-link>

      <router-link 
        to="/search" 
        class="nav-item" 
        :class="{ active: isActive('/search') }"
        @click="onSearchClick"
      >
        <Search :size="22" />
        <span>Поиск</span>
      </router-link>

      <!-- Library Root -->
      <div 
        class="nav-item clickable" 
        :class="{ active: route.name === 'library' && (!route.query.tab || route.query.tab === 'overview') }"
        @click="goToLibraryTab('overview')"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="m16 6 4 14M12 6v14M8 8v12M4 4v16"></path>
        </svg>
        <span>Библиотека</span>
      </div>

      <!-- Library Sub-links -->
      <div class="sidebar-subnav">
        <div 
          class="nav-subitem clickable" 
          :class="{ active: route.name === 'library' && route.query.tab === 'tracks' }"
          @click="goToLibraryTab('tracks')"
          title="Все треки медиатеки"
        >
          <Music :size="15" />
          <span>Все треки</span>
          <span v-if="libraryStore.tracks?.length" class="sub-count">{{ libraryStore.tracks.length }}</span>
        </div>

        <div 
          class="nav-subitem clickable" 
          :class="{ active: route.name === 'library' && route.query.tab === 'artists' }"
          @click="goToLibraryTab('artists')"
          title="Исполнители"
        >
          <Mic2 :size="15" />
          <span>Артисты</span>
        </div>

        <div 
          class="nav-subitem clickable" 
          :class="{ active: route.name === 'library' && route.query.tab === 'albums' }"
          @click="goToLibraryTab('albums')"
          title="Альбомы"
        >
          <Disc3 :size="15" />
          <span>Альбомы</span>
        </div>
      </div>

      <!-- Liked Tracks / Любимые треки -->
      <router-link 
        to="/liked" 
        class="nav-item liked-highlight-item" 
        :class="{ active: isActive('/liked') }"
        title="Любимые треки"
      >
        <Heart :size="20" :fill="isActive('/liked') ? 'currentColor' : 'none'" />
        <span>Любимые треки</span>
        <span v-if="likedCount > 0" class="nav-count">{{ likedCount }}</span>
      </router-link>

      <router-link to="/friends" class="nav-item" :class="{ active: isActive('/friends') }">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
          <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
        </svg>
        <span>Подписки</span>
      </router-link>

      <!-- Offline / Cached tracks standout card -->
      <router-link 
        to="/downloaded" 
        class="nav-item offline-highlight-item" 
        :class="{ active: isActive('/downloaded') }"
        title="Кэшированные и скачанные треки"
      >
        <FolderDown :size="20" class="offline-icon" />
        <span>Offline</span>
        <span v-if="cachedTracksCount > 0" class="nav-count offline-count">{{ cachedTracksCount }}</span>
      </router-link>

      <!-- Import Section link -->
      <router-link 
        to="/settings" 
        class="nav-item import-highlight-item" 
        :class="{ active: route.path === '/settings' }"
        title="Импорт и настройки"
      >
        <Upload :size="20" class="import-icon" />
        <span>Импорт</span>
      </router-link>
    </nav>

    <!-- Playlists Section -->
    <div v-if="displayedPlaylists.length > 0" class="sidebar-section playlists-section">
      <div class="section-header clickable" @click="goToPersonalPlaylists">
        <span>Плейлисты</span>
        <span class="section-count">{{ userPlaylists.length }}</span>
      </div>

      <div class="playlists-list">
        <div 
          v-for="playlist in displayedPlaylists" 
          :key="playlist.id"
          class="nav-item playlist-item"
          :class="{ active: $route.params.id == playlist.id && $route.name === 'playlist-detail' }"
          @click="$router.push(`/playlist/${playlist.id}`)"
          @contextmenu.prevent="openMenu('playlist', playlist, 'sidebar', $event)"
        >
          <div class="playlist-cover" :style="getPlaylistCoverStyle(playlist)">
            <img v-if="playlist.covers?.length" :key="playlist.covers[0]" :src="getCoverUrl(playlist.covers[0], CoverSize.SMALL)" alt="" />
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
            </svg>
          </div>
          <div class="playlist-info">
            <span class="playlist-name">{{ playlist.name }}</span>
          </div>
          <span class="nav-count">{{ playlist.track_count }}</span>
        </div>
        
        <div 
          v-if="hasMorePlaylists"
          class="nav-item show-more-btn"
          @click="goToPersonalPlaylists"
        >
          <span class="show-more-text">Показать все {{ userPlaylists.length }}</span>
        </div>
      </div>
    </div>

    <!-- User Section (bottom) -->
    <div class="sidebar-footer">
      <div 
        class="user-info clickable" 
        :class="{ active: showProfileMenu, 'has-active-imports': tasksStore.hasActiveImports }"
        @click="showProfileMenu = !showProfileMenu" 
        @contextmenu.prevent="showProfileMenu = true"
        v-longpress="() => { showProfileMenu = true }"
        :title="tasksStore.hasActiveImports ? `Импорт: ${tasksStore.overallProgress}% (открыть меню профиля)` : 'Меню профиля'"
      >
        <div class="user-avatar-wrap">
          <div class="user-avatar" :class="{ 'importing': tasksStore.hasActiveImports }">
            <img v-if="authStore.userAvatarUrl" :src="authStore.userAvatarUrl" class="sidebar-avatar-img" />
            <template v-else>{{ userInitials }}</template>
          </div>
          <div v-if="tasksStore.hasActiveImports" class="avatar-import-ring"></div>
        </div>
        <div class="user-info-text">
          <span class="user-name">{{ userName }}</span>
          <span v-if="tasksStore.hasActiveImports" class="user-import-indicator">
            <span class="import-pulsing-dot"></span>
            <span class="import-label">Импорт {{ tasksStore.overallProgress }}%</span>
          </span>
        </div>
      </div>
      <button 
        v-if="!pwaInstall.isInstalled" 
        class="footer-btn install-btn" 
        @click="pwaInstall.promptInstall()" 
        title="Установить приложение"
      >
        <Download :size="20" />
      </button>
      <router-link to="/settings" class="footer-btn settings-btn" title="Настройки">
        <Settings :size="18" />
      </router-link>
      <button class="footer-btn logout-btn" @click="logout" title="Выйти">
        <LogOut :size="18" />
      </button>
    </div>
  </aside>

  <!-- 3. Overlay Drawer & Backdrop (Teleported to body when in collapsed mode) -->
  <Teleport to="body">
    <div v-if="uiStore.isSidebarCollapsed" class="sidebar-overlay-portal">
      <!-- Backdrop over center area -->
      <Transition name="overlay-backdrop">
        <div 
          v-if="uiStore.isSidebarOverlayOpen" 
          class="sidebar-overlay-backdrop"
          :class="{ 'has-bottom-player': !!playerStore.currentTrack }"
          @click="uiStore.closeSidebarOverlay"
        />
      </Transition>

      <!-- Overlay Drawer (280px floating on top of center) -->
      <Transition name="overlay-drawer">
        <aside 
          v-if="uiStore.isSidebarOverlayOpen" 
          class="sidebar sidebar-overlay-drawer"
          :class="{ 'has-bottom-player': !!playerStore.currentTrack }"
          @click.stop
        >
          <!-- Logo and Close Button -->
          <div class="sidebar-logo">
            <div class="logo-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
              </svg>
            </div>
            <span class="logo-text">{{ authStore.appName || 'auxbassbot' }}</span>

            <!-- Close overlay button -->
            <button 
              class="sidebar-toggle-btn close-drawer-btn" 
              @click="uiStore.closeSidebarOverlay"
              title="Свернуть меню"
            >
              <PanelLeftClose :size="18" />
            </button>

            <div 
              v-if="authStore.user" 
              class="header-avatar clickable" 
              @click="goToMyProfileAndClose"
              title="Мой профиль"
            >
              <span class="header-avatar-badge">
                <img v-if="authStore.userAvatarUrl" :src="authStore.userAvatarUrl" class="sidebar-avatar-img" />
                <template v-else>{{ userInitials }}</template>
              </span>
            </div>
          </div>

          <!-- Main Navigation (closes drawer on click) -->
          <nav class="sidebar-nav">
            <router-link to="/" class="nav-item" :class="{ active: isActiveExact('/') }" @click="handleNavClick">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
              </svg>
              <span>Главная</span>
            </router-link>

            <router-link 
              to="/search" 
              class="nav-item" 
              :class="{ active: isActive('/search') }"
              @click="onSearchClick"
            >
              <Search :size="22" />
              <span>Поиск</span>
            </router-link>

            <div 
              class="nav-item clickable" 
              :class="{ active: route.name === 'library' && (!route.query.tab || route.query.tab === 'overview') }"
              @click="goToLibraryTabAndClose('overview')"
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="m16 6 4 14M12 6v14M8 8v12M4 4v16"></path>
              </svg>
              <span>Библиотека</span>
            </div>

            <!-- Library Sub-links -->
            <div class="sidebar-subnav">
              <div 
                class="nav-subitem clickable" 
                :class="{ active: route.name === 'library' && route.query.tab === 'tracks' }"
                @click="goToLibraryTabAndClose('tracks')"
                title="Все треки медиатеки"
              >
                <Music :size="15" />
                <span>Все треки</span>
                <span v-if="libraryStore.tracks?.length" class="sub-count">{{ libraryStore.tracks.length }}</span>
              </div>

              <div 
                class="nav-subitem clickable" 
                :class="{ active: route.name === 'library' && route.query.tab === 'artists' }"
                @click="goToLibraryTabAndClose('artists')"
                title="Исполнители"
              >
                <Mic2 :size="15" />
                <span>Артисты</span>
              </div>

              <div 
                class="nav-subitem clickable" 
                :class="{ active: route.name === 'library' && route.query.tab === 'albums' }"
                @click="goToLibraryTabAndClose('albums')"
                title="Альбомы"
              >
                <Disc3 :size="15" />
                <span>Альбомы</span>
              </div>
            </div>

            <!-- Liked Tracks -->
            <router-link 
              to="/liked" 
              class="nav-item liked-highlight-item" 
              :class="{ active: isActive('/liked') }"
              @click="handleNavClick"
              title="Любимые треки"
            >
              <Heart :size="20" :fill="isActive('/liked') ? 'currentColor' : 'none'" />
              <span>Любимые треки</span>
              <span v-if="likedCount > 0" class="nav-count">{{ likedCount }}</span>
            </router-link>

            <router-link to="/friends" class="nav-item" :class="{ active: isActive('/friends') }" @click="handleNavClick">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
              </svg>
              <span>Подписки</span>
            </router-link>

            <!-- Offline -->
            <router-link 
              to="/downloaded" 
              class="nav-item offline-highlight-item" 
              :class="{ active: isActive('/downloaded') }"
              @click="handleNavClick"
              title="Кэшированные и скачанные треки"
            >
              <FolderDown :size="20" class="offline-icon" />
              <span>Offline</span>
              <span v-if="cachedTracksCount > 0" class="nav-count offline-count">{{ cachedTracksCount }}</span>
            </router-link>

            <!-- Import -->
            <router-link 
              to="/settings" 
              class="nav-item import-highlight-item" 
              :class="{ active: route.path === '/settings' }"
              @click="handleNavClick"
              title="Импорт и настройки"
            >
              <Upload :size="20" class="import-icon" />
              <span>Импорт</span>
            </router-link>
          </nav>

          <!-- Playlists Section -->
          <div v-if="displayedPlaylists.length > 0" class="sidebar-section playlists-section">
            <div class="section-header clickable" @click="goToPersonalPlaylistsAndClose">
              <span>Плейлисты</span>
              <span class="section-count">{{ userPlaylists.length }}</span>
            </div>

            <div class="playlists-list">
              <div 
                v-for="playlist in displayedPlaylists" 
                :key="playlist.id"
                class="nav-item playlist-item"
                :class="{ active: $route.params.id == playlist.id && $route.name === 'playlist-detail' }"
                @click="goToPlaylistAndClose(playlist.id)"
                @contextmenu.prevent="openMenu('playlist', playlist, 'sidebar', $event)"
              >
                <div class="playlist-cover" :style="getPlaylistCoverStyle(playlist)">
                  <img v-if="playlist.covers?.length" :key="playlist.covers[0]" :src="getCoverUrl(playlist.covers[0], CoverSize.SMALL)" alt="" />
                  <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
                  </svg>
                </div>
                <div class="playlist-info">
                  <span class="playlist-name">{{ playlist.name }}</span>
                </div>
                <span class="nav-count">{{ playlist.track_count }}</span>
              </div>
              
              <div 
                v-if="hasMorePlaylists"
                class="nav-item show-more-btn"
                @click="goToPersonalPlaylistsAndClose"
              >
                <span class="show-more-text">Показать все {{ userPlaylists.length }}</span>
              </div>
            </div>
          </div>

          <!-- User Section (bottom) -->
          <div class="sidebar-footer">
            <div 
              class="user-info clickable" 
              :class="{ active: showProfileMenu, 'has-active-imports': tasksStore.hasActiveImports }"
              @click="showProfileMenu = !showProfileMenu" 
              @contextmenu.prevent="showProfileMenu = true"
              v-longpress="() => { showProfileMenu = true }"
              :title="tasksStore.hasActiveImports ? `Импорт: ${tasksStore.overallProgress}% (открыть меню профиля)` : 'Меню профиля'"
            >
              <div class="user-avatar-wrap">
                <div class="user-avatar" :class="{ 'importing': tasksStore.hasActiveImports }">
                  <img v-if="authStore.userAvatarUrl" :src="authStore.userAvatarUrl" class="sidebar-avatar-img" />
                  <template v-else>{{ userInitials }}</template>
                </div>
                <div v-if="tasksStore.hasActiveImports" class="avatar-import-ring"></div>
              </div>
              <div class="user-info-text">
                <span class="user-name">{{ userName }}</span>
                <span v-if="tasksStore.hasActiveImports" class="user-import-indicator">
                  <span class="import-pulsing-dot"></span>
                  <span class="import-label">Импорт {{ tasksStore.overallProgress }}%</span>
                </span>
              </div>
            </div>
            <button 
              v-if="!pwaInstall.isInstalled" 
              class="footer-btn install-btn" 
              @click="pwaInstall.promptInstall()" 
              title="Установить приложение"
            >
              <Download :size="20" />
            </button>
            <router-link to="/settings" class="footer-btn settings-btn" @click="handleNavClick" title="Настройки">
              <Settings :size="18" />
            </router-link>
            <button class="footer-btn logout-btn" @click="logout" title="Выйти">
              <LogOut :size="18" />
            </button>
          </div>
        </aside>
      </Transition>
    </div>
  </Teleport>

  <!-- Context Menu for Profile -->
  <ProfileMenu v-model="showProfileMenu" placement="sidebar" />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { usePlayerStore } from '@/stores/player'
import { useTasksStore } from '@/stores/tasks'
import { useContextMenu } from '@/composables/useContextMenu'
import { usePwaInstall } from '@/composables/usePwaInstall'
import { getCoverUrl, CoverSize, getPlaylistCoverStyle } from '@/utils'
import { 
  Download, 
  FolderDown, 
  Upload, 
  Music, 
  Mic2, 
  Disc3, 
  Search, 
  Heart, 
  Menu, 
  PanelLeftClose, 
  Settings, 
  LogOut 
} from 'lucide-vue-next'
import { getCacheStats } from '@/utils/audioCacheDb'
import ProfileMenu from '@/components/layout/ProfileMenu.vue'

const route = useRoute()
const router = useRouter()
const libraryStore = useLibraryStore()
const authStore = useAuthStore()
const uiStore = useUIStore()
const playerStore = usePlayerStore()
const tasksStore = useTasksStore()
const pwaInstall = usePwaInstall()
const showProfileMenu = ref(false)
const cachedTracksCount = ref(0)

const handleNavClick = () => {
  if (uiStore.isSidebarOverlayOpen) {
    uiStore.closeSidebarOverlay()
  }
}

const onSearchClick = () => {
  handleNavClick()
  if (route.path === '/search') {
    window.dispatchEvent(new CustomEvent('nav-tab-click', { detail: { route: '/search' } }))
  }
}

const goToLibraryTabAndClose = (tab) => {
  handleNavClick()
  goToLibraryTab(tab)
}

const goToPersonalPlaylistsAndClose = () => {
  handleNavClick()
  goToPersonalPlaylists()
}

const goToPlaylistAndClose = (id) => {
  handleNavClick()
  router.push(`/playlist/${id}`)
}

const goToMyProfileAndClose = () => {
  handleNavClick()
  goToMyProfile()
}

const formatRailCount = (count) => {
  if (!count) return ''
  if (count > 999) return `${(count / 1000).toFixed(0)}k`
  if (count > 99) return '99+'
  return count.toString()
}

const updateCachedStats = async () => {
  try {
    const stats = await getCacheStats()
    cachedTracksCount.value = stats?.trackCount || 0
  } catch (_) {}
}

// Universal context menu
const { openMenu } = useContextMenu()

// Stats
const likedCount = computed(() => libraryStore.likedTracks?.length || 0)

// Playlists
const playlists = computed(() => libraryStore.playlists || [])

const userPlaylists = computed(() => playlists.value)

const displayedPlaylists = computed(() => {
  return userPlaylists.value.slice(0, 5)
})

const hasMorePlaylists = computed(() => {
  return userPlaylists.value.length > 5
})

// Navigation
const goToLibraryTab = (tab) => {
  uiStore.setLibraryTab(tab)
  if (tab === 'overview') {
    router.push('/library')
  } else {
    router.push({ path: '/library', query: { tab } })
  }
}

const goToPersonalPlaylists = () => {
  goToLibraryTab('playlists')
}

// User info
const userName = computed(() => {
  return authStore.userDisplayName || 'User'
})

const userInitials = computed(() => {
  const name = userName.value || 'U'
  return name.substring(0, 2).toUpperCase()
})

// Route matching
const isActive = (path) => {
  return route.path.startsWith(path)
}

const isActiveExact = (path) => {
  return route.path === path
}

const logout = async () => {
  if (confirm('Вы уверены, что хотите выйти?')) {
    authStore.logout()
    // Force full page reload to clear all store states
    window.location.href = '/login'
  }
}

const goToMyProfile = () => {
  if (authStore.user?.id) {
    router.push(`/user/${authStore.user.id}`)
  }
}

const onPlaylistChanged = () => {
  libraryStore.fetchPlaylists(true)
}

onMounted(() => {
  window.addEventListener('playlist:changed', onPlaylistChanged)
  window.addEventListener('cache-updated', updateCachedStats)
  updateCachedStats()
  if (!libraryStore.likedTracks?.length) {
    libraryStore.fetchLikedTracks()
  }
})

onUnmounted(() => {
  window.removeEventListener('playlist:changed', onPlaylistChanged)
  window.removeEventListener('cache-updated', updateCachedStats)
})
</script>

<style scoped>
/* Base Sidebar */
.sidebar {
  width: 280px;
  height: 100%;
  background: #0a0a0a;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar::-webkit-scrollbar {
  width: 6px;
}

.sidebar::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

/* =========================================================
   1. Compact Rail Sidebar (72px)
   ========================================================= */
.sidebar.rail-sidebar {
  width: var(--sidebar-collapsed-width, 72px);
  height: 100%;
  background: #0a0a0a;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 0 16px;
  overflow-y: auto;
  overflow-x: hidden;
  user-select: none;
}

.rail-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  width: 100%;
}

.rail-burger-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.rail-burger-btn:hover {
  background: rgba(29, 185, 84, 0.16);
  border-color: rgba(29, 185, 84, 0.45);
  color: var(--c-accent, #1db954);
  transform: scale(1.06);
}

.rail-burger-btn:active {
  transform: scale(0.96);
}

.rail-logo-icon {
  width: 38px;
  height: 38px;
  background: linear-gradient(135deg, var(--c-accent, #1db954), var(--c-accent-light, #1ed760));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #000;
  box-shadow: 0 4px 12px rgba(29, 185, 84, 0.25);
}

.rail-nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  align-items: center;
  padding: 0 8px;
}

.rail-nav-item {
  position: relative;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.65);
  background: transparent;
  border: none;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.18s ease;
}

.rail-nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
  transform: translateY(-1px);
}

.rail-nav-item.active {
  background: rgba(29, 185, 84, 0.14);
  color: var(--c-accent, #1db954);
}

.rail-nav-item.active svg {
  color: var(--c-accent, #1db954);
}

.rail-active-indicator {
  position: absolute;
  left: -8px;
  top: 10px;
  bottom: 10px;
  width: 3px;
  border-radius: 0 4px 4px 0;
  background: var(--c-accent, #1db954);
  opacity: 0;
  transition: opacity 0.15s ease;
}

.rail-nav-item.active .rail-active-indicator {
  opacity: 1;
}

.rail-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  color: #000;
  background: var(--c-accent, #1db954);
  border: 2px solid #0a0a0a;
  border-radius: 10px;
  min-width: 16px;
  height: 16px;
  padding: 0 3px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.offline-badge {
  background: rgba(255, 255, 255, 0.85);
  color: #000;
}

.rail-divider {
  width: 34px;
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
  margin: 10px auto;
}

.rail-playlists {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  width: 100%;
  padding: 2px 0;
}

.rail-playlist-thumb {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.5);
  transition: all 0.18s ease;
}

.rail-playlist-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.rail-playlist-thumb:hover {
  transform: scale(1.08);
  border-color: rgba(255, 255, 255, 0.3);
}

.rail-playlist-thumb.active {
  border-color: var(--c-accent, #1db954);
  box-shadow: 0 0 10px rgba(29, 185, 84, 0.35);
}

.rail-footer {
  margin-top: auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.rail-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.rail-avatar:hover {
  transform: scale(1.08);
  box-shadow: 0 0 12px rgba(255, 255, 255, 0.2);
}

.rail-import-ring {
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 2px solid transparent;
  border-top-color: var(--c-accent, #1db954);
  border-right-color: #38bdf8;
  animation: avatar-spin 1.2s linear infinite;
  pointer-events: none;
}

.rail-footer-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  text-decoration: none;
}

.rail-footer-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.rail-footer-btn.logout-btn:hover {
  color: #ff6b6b;
  background: rgba(255, 107, 107, 0.12);
}

/* =========================================================
   2. Full Sidebar & Overlay Drawer
   ========================================================= */
.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 16px 16px;
}

.sidebar-toggle-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.65);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  margin-left: auto;
  margin-right: 4px;
  flex-shrink: 0;
}

.sidebar-toggle-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  transform: scale(1.05);
}

.sidebar-toggle-btn:active {
  transform: scale(0.95);
}

.header-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #333 0%, #222 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.15);
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.15s ease, border-color 0.15s ease;
  flex-shrink: 0;
}

.header-avatar:hover {
  transform: scale(1.06);
  border-color: rgba(255, 255, 255, 0.4);
}

.header-avatar-badge {
  font-size: 12px;
  font-weight: 700;
  color: #fff;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--c-accent, #1db954), var(--c-accent-light, #1ed760));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #000;
  flex-shrink: 0;
}

.logo-text {
  font-size: 18px;
  font-weight: 800;
  color: white;
  letter-spacing: -0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-nav {
  padding: 8px 8px;
}

.nav-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 10px 14px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
  text-decoration: none;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: white;
}

.nav-item.active {
  background: rgba(29, 185, 84, 0.12);
  color: var(--c-accent, #1db954);
  font-weight: 600;
}

.nav-item.active svg {
  color: var(--c-accent, #1db954);
  opacity: 1;
}

/* Sidebar Subnav (Under Library) */
.sidebar-subnav {
  margin: 3px 0 6px 16px;
  padding-left: 10px;
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-subitem {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 12px;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.65);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}

.nav-subitem:hover {
  background: rgba(255, 255, 255, 0.07);
  color: white;
}

.nav-subitem.active {
  background: rgba(29, 185, 84, 0.12);
  color: var(--c-accent, #1db954);
  font-weight: 600;
}

.nav-subitem.active svg {
  color: var(--c-accent, #1db954);
}

.sub-count {
  margin-left: auto;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 6px;
  border-radius: 8px;
}

.offline-highlight-item {
  margin-top: 8px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 11px 14px;
}

.offline-highlight-item:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.18);
  transform: translateY(-1px);
}

.offline-highlight-item.active {
  background: rgba(29, 185, 84, 0.15);
  border-color: rgba(29, 185, 84, 0.4);
  color: var(--c-accent, #1db954);
}

.offline-highlight-item .offline-count {
  background: rgba(255, 255, 255, 0.14);
  color: rgba(255, 255, 255, 0.85);
  font-weight: 600;
}

.import-highlight-item {
  margin-top: 4px;
}

.import-highlight-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: white;
}

.import-highlight-item.active {
  background: rgba(29, 185, 84, 0.12);
  color: var(--c-accent, #1db954);
  font-weight: 600;
}

.nav-item svg {
  flex-shrink: 0;
  opacity: 0.8;
}

.nav-item > span:not(.nav-count) {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-count {
  margin-left: auto;
  flex-shrink: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
}

.sidebar-section {
  padding: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-header.clickable {
  cursor: pointer;
  transition: color 0.15s;
}

.section-header.clickable:hover {
  color: white;
}

.playlists-section {
  display: flex;
  flex-direction: column;
}

.playlists-list {
  padding-bottom: 8px;
}

.playlist-item {
  padding: 8px 16px;
  flex-direction: row;
  align-items: center;
}

.playlist-cover {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.7);
  flex-shrink: 0;
  overflow: hidden;
}

.playlist-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.playlist-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}

.playlist-info .playlist-name {
  flex: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.section-count {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  font-weight: normal;
}

.show-more-btn {
  justify-content: center !important;
  padding: 10px 16px !important;
  margin-top: 4px;
}

.show-more-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  transition: color 0.15s;
}

.show-more-btn:hover .show-more-text {
  color: var(--c-accent);
}

/* Sidebar Footer */
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  gap: 12px;
  background: #0a0a0a;
  position: sticky;
  bottom: 0;
  margin-top: auto;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.user-avatar-wrap {
  position: relative;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: white;
  flex-shrink: 0;
  overflow: hidden;
  transition: transform 0.2s ease;
}

.sidebar-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.user-avatar.importing {
  box-shadow: 0 0 10px rgba(29, 185, 84, 0.35);
}

.avatar-import-ring {
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 2px solid transparent;
  border-top-color: var(--c-accent, #1db954);
  border-right-color: #38bdf8;
  animation: avatar-spin 1.2s linear infinite;
  pointer-events: none;
}

@keyframes avatar-spin {
  to { transform: rotate(360deg); }
}

.user-info-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.user-name {
  font-size: 13px;
  color: white;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-import-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 1px;
}

.import-pulsing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--c-accent, #1db954);
  box-shadow: 0 0 6px var(--c-accent, #1db954);
  animation: dot-pulse 1.5s ease-in-out infinite;
  flex-shrink: 0;
}

@keyframes dot-pulse {
  0%, 100% { transform: scale(0.9); opacity: 0.6; }
  50% { transform: scale(1.3); opacity: 1; }
}

.import-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--c-accent, #1db954);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-info.clickable {
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--r-md);
  transition: background 0.15s ease;
}

.user-info.clickable:hover,
.user-info.clickable.active {
  background: rgba(255, 255, 255, 0.12);
}

.footer-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
}

.install-btn:hover {
  color: var(--c-accent, #1db954);
  background: rgba(29, 185, 84, 0.15);
}

.settings-btn:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.logout-btn:hover {
  color: #ff6b6b;
  background: rgba(255, 107, 107, 0.1);
}

/* =========================================================
   3. Overlay Backdrop & Drawer ("бургер меню поверх среднего экрана")
   ========================================================= */
.sidebar-overlay-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 1040;
  cursor: pointer;
}

.sidebar-overlay-backdrop.has-bottom-player {
  bottom: var(--desktop-player-height, 100px);
}

.sidebar-overlay-drawer {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 280px;
  z-index: 1050;
  background: #0d0d0d;
  border-right: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 18px 0 45px rgba(0, 0, 0, 0.85), 6px 0 16px rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-overlay-drawer.has-bottom-player {
  bottom: var(--desktop-player-height, 100px);
}

/* Overlay Transitions */
.overlay-backdrop-enter-active,
.overlay-backdrop-leave-active {
  transition: opacity 0.25s ease;
}

.overlay-backdrop-enter-from,
.overlay-backdrop-leave-to {
  opacity: 0;
}

.overlay-drawer-enter-active,
.overlay-drawer-leave-active {
  transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s ease;
}

.overlay-drawer-enter-from,
.overlay-drawer-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}
</style>
