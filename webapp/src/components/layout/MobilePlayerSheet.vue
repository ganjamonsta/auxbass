<template>
  <div 
    class="mobile-player-sheet" 
    :class="sheetClasses"
    :style="sheetCssVars"
    ref="sheetRootRef"
  >
    <!-- Background Backdrop Overlay when expanded or dragging -->
    <div 
      class="player-backdrop"
      :style="{ opacity: expandProgress * 0.96 }"
      @click="handleBackdropClick"
    ></div>

    <!-- Ambient Dynamic Glow in expanded state -->
    <div 
      class="ambient-glow"
      :style="{ opacity: expandProgress }"
    >
      <div class="glow-orb primary" :style="ambientGlowStyle"></div>
      <div class="glow-orb secondary"></div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         1. MORPHING TOP HEADER (TRAVELS FROM BOTTOM TO TOP)
         ═══════════════════════════════════════════════════════════ -->
    <div 
      class="morph-header-container"
      ref="headerContainerRef"
      @touchstart="onHeaderTouchStart"
      @touchmove="onHeaderTouchMove"
      @touchend="onHeaderTouchEnd"
      @touchcancel="onHeaderTouchEnd"
      @click="handleHeaderClick"
    >
      <!-- Top Drag Bar / Status Handle (visible mostly in expanded state) -->
      <div class="header-drag-handle-wrap" :style="{ opacity: expandProgress }">
        <div class="drag-pill"></div>
      </div>

      <!-- State A: Collapsed LCD Mini Player -->
      <div 
        v-if="hasTrack"
        class="mini-player-view"
        :style="{ 
          opacity: 1 - expandProgress * 2.2, 
          pointerEvents: expandProgress > 0.3 ? 'none' : 'auto',
          transform: `scale(${1 - expandProgress * 0.1})`
        }"
        @contextmenu.prevent="openTrackContextMenu($event)"
      >
        <div class="lcd-screen">
          <!-- Row 1: Title + Status Indicators -->
          <div class="lcd-row row-title">
            <div class="lcd-title-container">
              <div class="lcd-title-track" :class="{ 'marquee': shouldMarquee }">
                <span class="lcd-title">{{ displayText }}</span>
                <span v-if="shouldMarquee" class="lcd-title lcd-title-clone">{{ displayText }}</span>
              </div>
            </div>
            <div class="lcd-indicators">
              <!-- Network issue indicator -->
              <span 
                v-if="networkMonitor.hasIssues.value" 
                class="lcd-indicator net-indicator active" 
                :class="{ pulse: networkMonitor.connectionState.value === 'reconnecting' }"
                :title="networkMonitor.connectionState.value === 'offline' ? 'Нет сети' : networkMonitor.connectionState.value === 'reconnecting' ? 'Восстановление...' : 'Медленная сеть'"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="1" y1="1" x2="23" y2="23"/>
                  <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/>
                  <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/>
                  <path d="M10.71 5.05A16 16 0 0 1 22.56 9"/>
                  <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/>
                  <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
                  <line x1="12" y1="20" x2="12.01" y2="20"/>
                </svg>
              </span>
              <span v-if="playerStore.hdTrackInfo" class="lcd-indicator hd-indicator active" title="HD версия">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-8 12H9.5v-2h-2v2H6V9h1.5v2.5h2V9H11v6zm2-6h4c.55 0 1 .45 1 1v4c0 .55-.45 1-1 1h-4V9zm1.5 4.5h2v-3h-2v3z"/>
                </svg>
              </span>
              <span 
                class="lcd-indicator like-indicator" 
                :class="{ active: isLiked }" 
                :title="isLiked ? 'Удалить из любимых' : 'Добавить в любимое'"
                @click.stop="$emit('like')"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" :fill="isLiked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                </svg>
              </span>
              <span 
                class="lcd-indicator shuffle-indicator" 
                :class="{ active: shuffle }" 
                title="Перемешивание"
                @click.stop="$emit('toggle-shuffle')"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
                </svg>
              </span>
              <span 
                class="lcd-indicator repeat-indicator" 
                :class="{ active: repeat !== 'none' }" 
                :title="repeatTitle"
                @click.stop="$emit('toggle-repeat')"
              >
                <svg v-if="repeat === 'one'" width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4zm-4-2V9h-1l-2 1v1h1.5v4H13z"/>
                </svg>
                <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/>
                </svg>
              </span>
            </div>
          </div>
          
          <!-- Row 2: Progress Dots + Time + Controls -->
          <div class="lcd-row row-controls">
            <div class="lcd-progress">
              <span 
                class="lcd-dot" 
                v-for="i in 20" 
                :key="i" 
                :class="getDotClass(i, 20)"
              ></span>
            </div>
            
            <span class="lcd-time">{{ formatTime(progress) }}/{{ formatTime(duration || currentTrack?.duration) }}</span>
            
            <div class="lcd-buttons">
              <button class="lcd-btn" @click.stop="$emit('toggle-play')" title="Воспроизведение">
                <svg v-if="loading" class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <path d="M12 2a10 10 0 0 1 10 10"/>
                </svg>
                <svg v-else-if="isPlaying" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </button>
              <button class="lcd-btn" @click.stop="$emit('next-track')" title="Следующий трек">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- State B: Expanded Cyber Top Header Bar -->
      <div 
        class="expanded-header-view"
        :style="{ 
          opacity: Math.max(0, (expandProgress - 0.35) * 1.54),
          pointerEvents: expandProgress < 0.6 ? 'none' : 'auto'
        }"
      >
        <button class="header-icon-btn collapse-btn" @click.stop="collapsePlayer" title="Свернуть">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>

        <div class="header-center-info">
          <span class="header-label">СЕЙЧАС ИГРАЕТ</span>
          <span class="header-track-name">{{ getDisplayTitle(currentTrack) }}</span>
        </div>

        <div class="header-actions">
          <span v-if="playerStore.hdTrackInfo" class="cyber-hd-badge">HD</span>
          <button 
            class="header-icon-btn header-like-btn" 
            :class="{ active: isLiked }"
            @click.stop="$emit('like')"
            title="Лайк"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" :fill="isLiked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
          </button>
          <button 
            class="header-icon-btn menu-btn"
            @click.stop="openTrackContextMenu($event)"
            title="Меню"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <circle cx="12" cy="5" r="2"/>
              <circle cx="12" cy="12" r="2"/>
              <circle cx="12" cy="19" r="2"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         2. FULLSCREEN PLAYER BODY CANVAS (PULLED UP WITH SHEET)
         ═══════════════════════════════════════════════════════════ -->
    <div 
      class="fullscreen-player-body"
      :style="{ 
        opacity: Math.max(0, (expandProgress - 0.15) * 1.18),
        transform: `translateY(${(1 - expandProgress) * 40}px) scale(${0.92 + expandProgress * 0.08})`,
        pointerEvents: expandProgress < 0.5 ? 'none' : 'auto'
      }"
    >
      <!-- Cover Art with Neumorphic 3D Card & Horizontal Swipe -->
      <div 
        class="body-cover-section"
        :class="{ swiping: isCoverSwiping }"
        @touchstart="onCoverTouchStart"
        @touchmove="onCoverTouchMove"
        @touchend="onCoverTouchEnd"
        @touchcancel="onCoverTouchEnd"
        @contextmenu.prevent="openTrackContextMenu($event)"
      >
        <div class="cover-glow-ring"></div>
        <div class="cover-card" :style="coverStyle">
          <span v-if="!currentTrack?.cover_url" class="cover-initials">{{ coverInitials }}</span>
          <img 
            v-else 
            :src="getCoverUrl(currentTrack.cover_url, CoverSize.XL)" 
            alt="Cover" 
            class="cover-image" 
            draggable="false"
          />

          <!-- Loading Overlay -->
          <div v-if="loading" class="cover-loading-overlay">
            <div class="cover-spinner">
              <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <circle cx="12" cy="12" r="10" stroke-width="3" stroke-opacity="0.25"/>
                <path d="M12 2a10 10 0 0 1 10 10" stroke-width="3" stroke-linecap="round"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- Swipe feedback hint arrows -->
        <div v-if="isCoverSwiping" class="cover-swipe-arrows">
          <div v-if="coverSwipeDirection === 'left'" class="swipe-arrow-badge right">
            <span>Дальше</span>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
            </svg>
          </div>
          <div v-if="coverSwipeDirection === 'right'" class="swipe-arrow-badge left">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15.41 16.59L10.83 12l4.58-4.59L14 6l-6 6 6 6 1.41-1.41z"/>
            </svg>
            <span>Назад</span>
          </div>
        </div>
      </div>

      <!-- Track Information & Interactive Tags -->
      <div class="body-info-section" @contextmenu.prevent="openTrackContextMenu($event)">
        <div class="info-title-wrap">
          <h2 class="body-track-title">{{ getDisplayTitle(currentTrack) }}</h2>
        </div>
        <p class="body-track-artist">
          <template v-if="parsedArtists.length > 0">
            <template v-for="(artist, index) in parsedArtists" :key="artist">
              <span class="artist-clickable-link" @click.stop="goToArtist(artist)">{{ artist }}</span>
              <span v-if="index < parsedArtists.length - 1" class="artist-separator">, </span>
            </template>
          </template>
          <span v-else>{{ getDisplayArtist(currentTrack) }}</span>
        </p>

        <!-- Interactive Tag Badges with Voting -->
        <TrackTags
          v-if="currentTrack?.id"
          :trackId="currentTrack.id"
          :tags="currentTrack.tags || []"
          :interactive="true"
          :max="5"
          class="body-tags-bar"
        />
      </div>

      <!-- High-Tech Progress Scrubber -->
      <div class="body-progress-section">
        <div class="progress-bar-wrapper">
          <div 
            class="progress-buffered-track" 
            :style="{ width: `${bufferedPercent}%` }"
          ></div>
          <div 
            class="progress-played-track" 
            :style="{ width: `${progressPercent}%` }"
          ></div>
          <input 
            type="range"
            class="progress-touch-slider"
            :value="progress"
            min="0"
            :max="duration || currentTrack?.duration || 100"
            @input="$emit('seek', Number($event.target.value))"
          />
        </div>
        <div class="progress-time-row">
          <span class="time-readout current">{{ formatTime(progress) }}</span>
          <span class="time-readout total">{{ formatTime(duration || currentTrack?.duration) }}</span>
        </div>
      </div>

      <!-- Auxiliary Utility Row (Volume + Lyrics + Queue) -->
      <div class="body-aux-row">
        <!-- Compact Volume Control -->
        <div class="aux-volume-control">
          <button class="aux-btn mute-btn" @click.stop="$emit('toggle-mute')">
            <svg v-if="isMuted || volume === 0" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
            </svg>
            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
            </svg>
          </button>
          <input 
            type="range"
            class="aux-volume-slider"
            :value="isMuted ? 0 : volume * 100"
            min="0"
            max="100"
            @input="$emit('set-volume', Number($event.target.value) / 100)"
          />
        </div>

        <!-- Lyrics Button -->
        <button 
          class="aux-btn pill-btn lyrics-btn" 
          :class="{ active: showLyrics }"
          @click.stop="toggleLyrics"
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            <line x1="8" y1="8" x2="16" y2="8"></line>
            <line x1="8" y1="12" x2="13" y2="12"></line>
          </svg>
          <span>Текст</span>
        </button>

        <!-- Queue Button -->
        <button 
          class="aux-btn pill-btn queue-btn" 
          :class="{ active: showQueue }"
          @click.stop="toggleQueue"
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor">
            <path d="M4 10h12v2H4zm0-4h12v2H4zm0 8h8v2H4zm10 0v6l5-3z"/>
          </svg>
          <span>Очередь</span>
          <span v-if="upcomingQueue.length" class="queue-counter">{{ upcomingQueue.length }}</span>
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         3. BOTTOM DOCK (MORPHS FROM NAVIGATION TO PLAYER CONTROLS)
         ═══════════════════════════════════════════════════════════ -->
    <div class="morph-dock-container">
      <!-- Deck A: Bottom Navigation Bar (Active when collapsed) -->
      <nav 
        v-if="showNav"
        class="dock-navigation-layer"
        :style="{ 
          opacity: Math.max(0, 1 - expandProgress * 2.2),
          pointerEvents: expandProgress > 0.3 ? 'none' : 'auto',
          transform: `translateY(${expandProgress * 15}px)`
        }"
      >
        <button 
          v-for="item in navItems" 
          :key="item.path"
          class="nav-tab-btn" 
          :class="{ active: isActiveRoute(item.path, item.matchPaths) }"
          @click="handleNavClick(item.path)"
        >
          <component :is="item.icon" class="nav-tab-icon" :size="22" :stroke-width="2" />
          <span class="nav-tab-label">{{ item.label }}</span>
        </button>
      </nav>

      <!-- Deck B: Fullscreen Playback Control Deck (Active when expanded) -->
      <div 
        class="dock-controls-layer"
        :style="{ 
          opacity: Math.max(0, (expandProgress - 0.4) * 1.66),
          pointerEvents: expandProgress < 0.6 ? 'none' : 'auto',
          transform: `translateY(${(1 - expandProgress) * 20}px)`
        }"
      >
        <!-- 1. Shuffle -->
        <button 
          class="tactile-ctl-btn secondary-btn"
          :class="{ active: shuffle }"
          @click.stop="$emit('toggle-shuffle')"
          title="Перемешать"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
            <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
          </svg>
        </button>

        <!-- 2. Prev -->
        <button 
          class="tactile-ctl-btn prev-btn"
          @click.stop="$emit('prev-track')"
          title="Предыдущий трек"
        >
          <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
          </svg>
        </button>

        <!-- 3. Master Hero Play/Pause Button -->
        <button 
          class="tactile-hero-play-btn"
          @click.stop="$emit('toggle-play')"
          title="Воспроизведение"
        >
          <div class="hero-glow-border"></div>
          <svg v-if="loading" class="spin" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
            <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
          </svg>
          <svg v-else-if="isPlaying" width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
          </svg>
          <svg v-else width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </button>

        <!-- 4. Next -->
        <button 
          class="tactile-ctl-btn next-btn"
          @click.stop="$emit('next-track')"
          title="Следующий трек"
        >
          <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
          </svg>
        </button>

        <!-- 5. Repeat -->
        <button 
          class="tactile-ctl-btn secondary-btn"
          :class="{ active: repeat !== 'none' }"
          @click.stop="$emit('toggle-repeat')"
          :title="repeatTitle"
        >
          <svg v-if="repeat === 'one'" width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
            <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4zm-4-2V9h-1l-2 1v1h1.5v4H13z"/>
          </svg>
          <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
            <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         4. SLIDE-UP MODAL OVERLAYS (LYRICS & QUEUE)
         ═══════════════════════════════════════════════════════════ -->
    <!-- Lyrics Modal -->
    <Transition name="sheet-slide-up">
      <div v-if="showLyrics" class="inner-sheet-overlay lyrics-overlay">
        <LyricsViewer
          :track="currentTrack"
          :currentTime="progress"
          :isPlaying="isPlaying"
          @seek="$emit('seek', $event)"
          @close="showLyrics = false"
        />
      </div>
    </Transition>

    <!-- Queue Modal Drawer -->
    <Transition name="sheet-slide-up">
      <div v-if="showQueue" class="inner-sheet-overlay queue-overlay">
        <div class="queue-sheet-content">
          <div class="queue-top-header">
            <div class="queue-title-block">
              <span class="queue-heading">Очередь воспроизведения</span>
              <span class="queue-subhint">Свайп влево для удаления</span>
            </div>
            <button class="queue-close-btn" @click="showQueue = false">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <div class="queue-scroll-list">
            <div 
              v-for="(t, idx) in upcomingQueue" 
              :key="`q-${t.id}-${idx}`"
              class="queue-card-item"
              :class="{ 
                swiping: swipingQueueIndex === idx,
                'swipe-delete': queueSwipeProgress > 0.5 && swipingQueueIndex === idx,
              }"
              :style="getQueueItemStyle(idx)"
              @touchstart="onQueueTouchStart($event, idx)"
              @touchmove="onQueueTouchMove($event, idx)"
              @touchend="onQueueTouchEnd($event, idx)"
              @click="$emit('play-from-queue', idx)"
              @contextmenu.prevent="openTrackContextMenuForQueue(t, $event)"
            >
              <span class="queue-index">{{ idx + 1 }}</span>
              <div class="queue-thumb" :style="getQueueCoverStyle(t)"></div>
              <div class="queue-meta">
                <span class="q-title">{{ getDisplayTitle(t) }}</span>
                <span class="q-artist">{{ getDisplayArtist(t) }}</span>
              </div>
              <div class="queue-delete-badge">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                </svg>
              </div>
            </div>

            <div v-if="lazyShuffleMode" class="queue-lazy-card">
              <div class="lazy-icon">🔀</div>
              <div class="lazy-meta">
                <span class="lazy-heading">Режим бесконечного перемешивания</span>
                <span class="lazy-desc">{{ lazyShuffleIndex + 1 }} из {{ lazyShuffleTotal }} треков</span>
              </div>
            </div>

            <div v-else-if="!upcomingQueue.length" class="queue-empty-state">
              <span>Нет предстоящих треков в очереди</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useContextMenu } from '@/composables/useContextMenu'
import { useNetworkMonitor } from '@/composables/useNetworkMonitor'
import { 
  getDisplayTitle, 
  getDisplayArtist, 
  getAllTrackArtists, 
  getTrackCoverStyle, 
  getTrackInitials, 
  getCoverUrl, 
  CoverSize 
} from '@/utils'
import TrackTags from '@/components/TrackTags.vue'
import LyricsViewer from '@/components/LyricsViewer.vue'
import { ListMusic, Disc3, Users, Heart, Settings } from 'lucide-vue-next'

const props = defineProps({
  // Expanded binding
  isExpanded: {
    type: Boolean,
    default: false
  },
  currentTrack: {
    type: Object,
    default: null
  },
  isPlaying: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  progress: {
    type: Number,
    default: 0
  },
  duration: {
    type: Number,
    default: 0
  },
  buffered: {
    type: Number,
    default: 0
  },
  volume: {
    type: Number,
    default: 1
  },
  isMuted: {
    type: Boolean,
    default: false
  },
  shuffle: {
    type: Boolean,
    default: false
  },
  repeat: {
    type: String,
    default: 'none'
  },
  queue: {
    type: Array,
    default: () => []
  },
  queueIndex: {
    type: Number,
    default: -1
  },
  shuffleOrder: {
    type: Array,
    default: () => []
  },
  shuffleIndex: {
    type: Number,
    default: -1
  },
  isLiked: {
    type: Boolean,
    default: false
  },
  lazyShuffleMode: {
    type: Boolean,
    default: false
  },
  lazyShuffleTotal: {
    type: Number,
    default: 0
  },
  lazyShuffleIndex: {
    type: Number,
    default: -1
  },
  // Navigation
  showNav: {
    type: Boolean,
    default: true
  },
  navItems: {
    type: Array,
    default: () => [
      { path: '/', icon: ListMusic, label: 'Библиотека', matchPaths: ['/'] },
      { path: '/liked', icon: Heart, label: 'Любимое', matchPaths: ['/liked'] },
      { path: '/collections', icon: Disc3, label: 'Коллекции', matchPaths: ['/collections', '/albums', '/playlists'] },
      { path: '/friends', icon: Users, label: 'Кенты', matchPaths: ['/friends'] },
      { path: '/settings', icon: Settings, label: 'Настройки', matchPaths: ['/settings'] },
    ]
  }
})

const emit = defineEmits([
  'update:isExpanded',
  'toggle-play',
  'next-track',
  'prev-track',
  'seek',
  'set-volume',
  'toggle-mute',
  'toggle-shuffle',
  'toggle-repeat',
  'like',
  'remove-from-queue',
  'move-in-queue',
  'play-from-queue',
  'nav-click',
  'reset-view'
])

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const { openMenu } = useContextMenu()
const networkMonitor = useNetworkMonitor()
const telegram = inject('telegram', null)

// ═════════════════════════════════════════════════════════════
// 🌟 GESTURE & MORPH STATE ENGINE
// ═════════════════════════════════════════════════════════════
const sheetRootRef = ref(null)
const headerContainerRef = ref(null)

// expandProgress: 0.0 (collapsed mini) to 1.0 (fully expanded)
const expandProgress = ref(props.isExpanded ? 1.0 : 0.0)
const isDragging = ref(false)
const dragStartY = ref(0)
const dragStartProgress = ref(0)
const dragLastY = ref(0)
const dragLastTime = ref(0)
const dragVelocityY = ref(0)

// Sub modals
const showLyrics = ref(false)
const showQueue = ref(false)

// Cover swipe state for prev/next track
const isCoverSwiping = ref(false)
const coverSwipeDirection = ref(null)
const coverTouchStartX = ref(0)
const coverTouchStartY = ref(0)
const coverTouchMoved = ref(false)
let coverLongPressTimer = null

// Queue item swipe delete state
const swipingQueueIndex = ref(-1)
const queueSwipeStartX = ref(0)
const queueSwipeProgress = ref(0)
const QUEUE_SWIPE_THRESHOLD = 90

// Sync with prop
watch(() => props.isExpanded, (val) => {
  if (!isDragging.value) {
    expandProgress.value = val ? 1.0 : 0.0
  }
  if (!val) {
    showLyrics.value = false
    showQueue.value = false
  }
})

const hasTrack = computed(() => !!props.currentTrack)

const sheetClasses = computed(() => ({
  'is-expanded': expandProgress.value > 0.95,
  'is-collapsed': expandProgress.value < 0.05,
  'is-in-motion': isDragging.value,
  'has-track': hasTrack.value
}))

// Dynamic calculation of translateY for the header and sheet
const sheetCssVars = computed(() => {
  return {
    '--morph-progress': expandProgress.value.toString()
  }
})

// LCD & text helpers
const displayText = computed(() => {
  const artist = getDisplayArtist(props.currentTrack)
  const title = getDisplayTitle(props.currentTrack)
  return `${artist} — ${title}`
})

const shouldMarquee = computed(() => displayText.value.length > 28)

const parsedArtists = computed(() => {
  const t = props.currentTrack
  if (!t) return []
  return getAllTrackArtists(t.artist, t.title, t.file_name)
})

const coverStyle = computed(() => getTrackCoverStyle(props.currentTrack))
const coverInitials = computed(() => getTrackInitials(props.currentTrack))

const ambientGlowStyle = computed(() => {
  return coverStyle.value
})

const repeatTitle = computed(() => {
  switch (props.repeat) {
    case 'one': return 'Повтор трека'
    case 'all': return 'Повтор всего'
    default: return 'Повтор выключен'
  }
})

const progressPercent = computed(() => {
  const dur = props.duration || props.currentTrack?.duration
  if (!dur) return 0
  return Math.min(100, Math.max(0, (props.progress / dur) * 100))
})

const bufferedPercent = computed(() => {
  const dur = props.duration || props.currentTrack?.duration
  if (!dur) return 0
  return Math.min(100, Math.max(0, (props.buffered / dur) * 100))
})

const getDotClass = (index, total = 20) => {
  const dotPercent = (index / total) * 100
  const prevDotPercent = ((index - 1) / total) * 100
  
  if (dotPercent <= progressPercent.value) return 'active'
  if (prevDotPercent < progressPercent.value && dotPercent > progressPercent.value) return 'next'
  if (dotPercent <= bufferedPercent.value) return 'buffered'
  return ''
}

const upcomingQueue = computed(() => {
  if (!props.queue.length || props.queueIndex < 0) return []
  
  if (props.shuffle && props.shuffleOrder.length > 0 && props.shuffleIndex >= 0) {
    const upcoming = []
    for (let i = 1; i <= 8; i++) {
      const nextShuffleIdx = props.shuffleIndex + i
      if (nextShuffleIdx >= props.shuffleOrder.length) break
      const queueIdx = props.shuffleOrder[nextShuffleIdx]
      if (props.queue[queueIdx]) {
        upcoming.push(props.queue[queueIdx])
      }
    }
    return upcoming
  }
  
  return props.queue.slice(props.queueIndex + 1, props.queueIndex + 9)
})

// ═════════════════════════════════════════════════════════════
// 🖐️ TOUCH GESTURE HANDLING (UP/DOWN EXPAND & COLLAPSE)
// ═════════════════════════════════════════════════════════════
const getScreenHeight = () => window.innerHeight || 800

const onHeaderTouchStart = (e) => {
  const touch = e.touches[0]
  isDragging.value = true
  dragStartY.value = touch.clientY
  dragLastY.value = touch.clientY
  dragLastTime.value = performance.now()
  dragStartProgress.value = expandProgress.value
  dragVelocityY.value = 0
}

const onHeaderTouchMove = (e) => {
  if (!isDragging.value) return
  const touch = e.touches[0]
  const currentY = touch.clientY
  const now = performance.now()
  
  const deltaY = currentY - dragStartY.value
  const dt = now - dragLastTime.value
  if (dt > 10) {
    dragVelocityY.value = (currentY - dragLastY.value) / dt
    dragLastY.value = currentY
    dragLastTime.value = now
  }

  const travelDistance = getScreenHeight() * 0.75

  // When starting from collapsed (progress 0): dragging UP (deltaY < 0) increases progress
  // When starting from expanded (progress 1): dragging DOWN (deltaY > 0) decreases progress
  const progressChange = -deltaY / travelDistance
  const newProgress = Math.max(0, Math.min(1, dragStartProgress.value + progressChange))
  expandProgress.value = newProgress
}

const onHeaderTouchEnd = () => {
  if (!isDragging.value) return
  isDragging.value = false

  const v = dragVelocityY.value
  let target = 0

  if (dragStartProgress.value < 0.5) {
    // We were collapsed: dragging UP fast (v < -0.3) or progress > 0.25 -> expand
    if (v < -0.3 || expandProgress.value > 0.25) {
      target = 1
    } else {
      target = 0
    }
  } else {
    // We were expanded: dragging DOWN fast (v > 0.3) or progress < 0.75 -> collapse
    if (v > 0.3 || expandProgress.value < 0.75) {
      target = 0
    } else {
      target = 1
    }
  }

  setExpandState(target === 1)
}

const setExpandState = (expanded) => {
  expandProgress.value = expanded ? 1.0 : 0.0
  emit('update:isExpanded', expanded)
  if (expanded) {
    telegram?.HapticFeedback?.impactOccurred?.('medium')
  } else {
    telegram?.HapticFeedback?.impactOccurred?.('light')
  }
}

const handleHeaderClick = () => {
  if (expandProgress.value < 0.2) {
    setExpandState(true)
  }
}

const collapsePlayer = () => {
  setExpandState(false)
}

const handleBackdropClick = () => {
  if (expandProgress.value > 0.5) {
    collapsePlayer()
  }
}

// ═════════════════════════════════════════════════════════════
// 💿 COVER TOUCH SWIPE (NEXT / PREV TRACK)
// ═════════════════════════════════════════════════════════════
const onCoverTouchStart = (e) => {
  const touch = e.touches[0]
  coverTouchStartX.value = touch.clientX
  coverTouchStartY.value = touch.clientY
  isCoverSwiping.value = false
  coverSwipeDirection.value = null
  coverTouchMoved.value = false

  clearTimeout(coverLongPressTimer)
  coverLongPressTimer = setTimeout(() => {
    if (!coverTouchMoved.value) {
      telegram?.HapticFeedback?.impactOccurred?.('heavy')
      openTrackContextMenu(e)
    }
  }, 500)
}

const onCoverTouchMove = (e) => {
  const touch = e.touches[0]
  const deltaX = touch.clientX - coverTouchStartX.value
  const deltaY = touch.clientY - coverTouchStartY.value

  if (Math.abs(deltaX) > 12 || Math.abs(deltaY) > 12) {
    coverTouchMoved.value = true
    clearTimeout(coverLongPressTimer)
  }

  // Horizontal swipe for next/prev
  if (Math.abs(deltaX) > 24 && Math.abs(deltaX) > Math.abs(deltaY) * 1.4) {
    isCoverSwiping.value = true
    coverSwipeDirection.value = deltaX > 0 ? 'right' : 'left'
  }
  // Vertical swipe down to collapse
  else if (deltaY > 30 && Math.abs(deltaY) > Math.abs(deltaX) * 1.4) {
    // Initiate downward sheet drag
    isDragging.value = true
    dragStartY.value = touch.clientY
    dragStartProgress.value = 1.0
  }
}

const onCoverTouchEnd = (e) => {
  clearTimeout(coverLongPressTimer)
  const touch = e.changedTouches?.[0] || e.touches?.[0]
  if (touch && isCoverSwiping.value) {
    const deltaX = touch.clientX - coverTouchStartX.value
    if (deltaX < -60) {
      telegram?.HapticFeedback?.impactOccurred?.('medium')
      emit('next-track')
    } else if (deltaX > 60) {
      telegram?.HapticFeedback?.impactOccurred?.('medium')
      emit('prev-track')
    }
  }

  if (isDragging.value) {
    onHeaderTouchEnd()
  }

  isCoverSwiping.value = false
  coverSwipeDirection.value = null
}

// ═════════════════════════════════════════════════════════════
// 📑 SUB-MODALS & ACTIONS
// ═════════════════════════════════════════════════════════════
const toggleLyrics = () => {
  showLyrics.value = !showLyrics.value
  if (showLyrics.value) showQueue.value = false
  telegram?.HapticFeedback?.impactOccurred?.('light')
}

const toggleQueue = () => {
  showQueue.value = !showQueue.value
  if (showQueue.value) showLyrics.value = false
  telegram?.HapticFeedback?.impactOccurred?.('light')
}

const goToArtist = (artistName) => {
  if (artistName) {
    router.push(`/artist/${encodeURIComponent(artistName)}`)
    collapsePlayer()
  }
}

const openTrackContextMenu = (event) => {
  if (!props.currentTrack) return
  telegram?.HapticFeedback?.impactOccurred?.('light')
  openMenu('track', props.currentTrack, 'player', event)
}

const openTrackContextMenuForQueue = (track, event) => {
  if (!track) return
  telegram?.HapticFeedback?.impactOccurred?.('light')
  openMenu('track', track, 'queue', event)
}

// Queue swipe delete
const onQueueTouchStart = (e, idx) => {
  swipingQueueIndex.value = idx
  queueSwipeStartX.value = e.touches[0].clientX
  queueSwipeProgress.value = 0
}

const onQueueTouchMove = (e, idx) => {
  if (swipingQueueIndex.value !== idx) return
  const currentX = e.touches[0].clientX
  const deltaX = queueSwipeStartX.value - currentX
  if (deltaX > 0) {
    queueSwipeProgress.value = Math.min(1, deltaX / QUEUE_SWIPE_THRESHOLD)
  }
}

const onQueueTouchEnd = (e, idx) => {
  if (swipingQueueIndex.value !== idx) return
  const currentX = e.changedTouches[0].clientX
  const deltaX = queueSwipeStartX.value - currentX
  if (deltaX > QUEUE_SWIPE_THRESHOLD) {
    telegram?.HapticFeedback?.impactOccurred?.('medium')
    emit('remove-from-queue', idx)
  }
  swipingQueueIndex.value = -1
  queueSwipeProgress.value = 0
}

const getQueueItemStyle = (idx) => {
  if (swipingQueueIndex.value === idx && queueSwipeProgress.value > 0) {
    const tx = -(queueSwipeProgress.value * QUEUE_SWIPE_THRESHOLD)
    return { transform: `translateX(${tx}px)`, transition: 'none' }
  }
  return {}
}

const getQueueCoverStyle = (track) => getTrackCoverStyle(track)

// ═════════════════════════════════════════════════════════════
// 🧭 NAVIGATION TAB HANDLERS
// ═════════════════════════════════════════════════════════════
const isActiveRoute = (path, matchPaths = []) => {
  if (path === '/') return route.path === '/'
  return matchPaths.some(p => route.path.startsWith(p))
}

const scrollToTop = () => {
  const mainContent = document.querySelector('.main-content')
  if (mainContent) {
    mainContent.scrollTo({ top: 0, behavior: 'smooth' })
  }
  const scrollContainers = document.querySelectorAll(
    '.main-content, .main-content-wrapper, .library-view, .collections-view, .liked-tracks-view, .friends-view, .settings-view, .virtual-track-list, .virtual-grid, .page-scroll-container, .mobile-page-content'
  )
  scrollContainers.forEach((el) => {
    if (el && el.scrollTop > 0) {
      el.scrollTo({ top: 0, behavior: 'smooth' })
    }
  })
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const handleNavClick = (path) => {
  const currentNav = props.navItems.find(i => i.path === path)
  const isCurrentActive = isActiveRoute(path, currentNav?.matchPaths || [path])

  if (isCurrentActive) {
    const mainContent = document.querySelector('.main-content')
    const currentScroll = mainContent ? mainContent.scrollTop : (window.scrollY || 0)
    scrollToTop()
    if (currentScroll <= 30) {
      emit('reset-view', path)
      window.dispatchEvent(new CustomEvent('reset-view-state', { detail: { route: path } }))
    }
  } else {
    emit('nav-click', path)
    router.push(path)
  }
}

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
/* ═════════════════════════════════════════════════════════════
   🎵 MOBILE PLAYER SHEET - Unified Morphing Neumorphic Glass
   ═════════════════════════════════════════════════════════════ */

.mobile-player-sheet {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 120;
  display: flex;
  flex-direction: column;
  pointer-events: auto;
  user-select: none;
  -webkit-user-select: none;
  font-family: var(--font-sans);
}

.mobile-player-sheet.is-expanded {
  top: 0;
  height: 100%;
}

.mobile-player-sheet:not(.is-in-motion) {
  transition: top 0.35s cubic-bezier(0.2, 0.9, 0.2, 1);
}

/* ─── Backdrop Blur Overlay ─── */
.player-backdrop {
  position: fixed;
  inset: 0;
  background: radial-gradient(circle at 50% 20%, rgba(22, 28, 38, 0.95) 0%, rgba(8, 10, 14, 0.98) 100%);
  backdrop-filter: blur(44px) saturate(190%);
  -webkit-backdrop-filter: blur(44px) saturate(190%);
  pointer-events: none;
  z-index: -1;
  transition: opacity 0.2s linear;
}

.mobile-player-sheet.is-expanded .player-backdrop {
  pointer-events: auto;
}

/* ─── Ambient Glow Orbs ─── */
.ambient-glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: -1;
  overflow: hidden;
  transition: opacity 0.25s ease;
}

.glow-orb.primary {
  position: absolute;
  top: 15%;
  left: 50%;
  transform: translateX(-50%);
  width: 280px;
  height: 280px;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.25;
}

.glow-orb.secondary {
  position: absolute;
  bottom: 25%;
  right: 10%;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: var(--c-accent-glow);
  filter: blur(90px);
  opacity: 0.2;
}

/* ═════════════════════════════════════════════════════════════
   1. MORPHING TOP HEADER BAR
   ═════════════════════════════════════════════════════════════ */

.morph-header-container {
  position: relative;
  z-index: 10;
  width: 100%;
  touch-action: pan-x pan-y;
  cursor: pointer;
  /* Dynamic upward translation driven by --morph-progress */
  transform: translateY(calc( (1 - var(--morph-progress)) * 0px - var(--morph-progress) * (100vh - 100% - env(safe-area-inset-top, 0px) - 66px) ));
  will-change: transform;
}

.mobile-player-sheet:not(.is-in-motion) .morph-header-container {
  transition: transform 0.35s cubic-bezier(0.2, 0.9, 0.2, 1);
}

.mobile-player-sheet.is-expanded .morph-header-container {
  padding-top: max(8px, env(safe-area-inset-top));
}

.header-drag-handle-wrap {
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 4px 0 2px;
  pointer-events: none;
}

.drag-pill {
  width: 38px;
  height: 4px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: var(--r-full);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

/* ─── State A: Mini Player View ─── */
.mini-player-view {
  margin: 3px 8px 4px;
  padding: 4px;
  background: rgba(20, 25, 33, 0.82);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-radius: var(--r-lg);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 
    0 8px 24px rgba(0, 0, 0, 0.45),
    inset 0 1px 1px rgba(255, 255, 255, 0.18);
  transition: transform 0.15s ease;
}

.mini-player-view:active {
  transform: scale(0.985);
}

.lcd-screen {
  background: linear-gradient(180deg, rgba(8, 16, 24, 0.92) 0%, rgba(4, 10, 16, 0.98) 100%);
  border-radius: var(--r-md);
  padding: 8px 10px;
  border: 1px solid rgba(77, 195, 255, 0.18);
  box-shadow: 
    inset 0 2px 10px rgba(0, 0, 0, 0.85),
    0 1px 0 rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
  overflow: hidden;
}

.lcd-screen::before {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.04) 2px,
    rgba(0, 0, 0, 0.04) 4px
  );
  pointer-events: none;
}

.lcd-row {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
  z-index: 1;
}

.row-title {
  justify-content: space-between;
}

.lcd-title-container {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  mask-image: linear-gradient(90deg, black 90%, transparent 100%);
  -webkit-mask-image: linear-gradient(90deg, black 90%, transparent 100%);
}

.lcd-title-track {
  display: inline-flex;
  white-space: nowrap;
}

.lcd-title-track.marquee {
  animation: marquee-scroll 12s linear infinite;
}

.lcd-title {
  color: var(--lcd-text, #4DC3FF);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.3px;
  text-shadow: 0 0 8px var(--lcd-glow, rgba(77, 195, 255, 0.6));
}

.lcd-title-clone {
  margin-left: 50px;
}

@keyframes marquee-scroll {
  0%, 5% { transform: translateX(0); }
  95%, 100% { transform: translateX(calc(-50% - 25px)); }
}

.lcd-indicators {
  display: flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
}

.lcd-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.3);
  cursor: pointer;
  transition: all 0.15s ease;
}

.lcd-indicator.active {
  color: var(--lcd-text, #4DC3FF);
  text-shadow: 0 0 6px var(--lcd-glow, rgba(77, 195, 255, 0.6));
}

.lcd-indicator.like-indicator.active {
  color: #ff4b7b;
  text-shadow: 0 0 8px rgba(255, 75, 123, 0.8);
}

.lcd-indicator.hd-indicator.active {
  color: #ffd700;
  text-shadow: 0 0 8px rgba(255, 215, 0, 0.8);
}

.lcd-indicator.net-indicator.active {
  color: #ff6b6b;
}

.row-controls {
  gap: 8px;
}

.lcd-progress {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 2px;
  min-width: 0;
}

.lcd-dot {
  flex: 1;
  height: 4px;
  min-width: 2px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  transition: background 0.15s ease, box-shadow 0.15s ease;
}

.lcd-dot.active {
  background: var(--c-accent);
  box-shadow: 0 0 5px var(--c-accent-glow);
}

.lcd-dot.buffered {
  background: rgba(0, 188, 212, 0.35);
}

.lcd-dot.next {
  background: var(--c-accent);
  animation: dot-blink 0.6s infinite ease-in-out;
}

@keyframes dot-blink {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; box-shadow: 0 0 6px var(--c-accent-glow); }
}

.lcd-time {
  font-size: 10px;
  font-weight: 600;
  color: var(--lcd-text, #4DC3FF);
  font-variant-numeric: tabular-nums;
  min-width: 60px;
  text-align: right;
}

.lcd-buttons {
  display: flex;
  border-radius: 6px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.lcd-btn {
  width: 30px;
  height: 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--lcd-text, #4DC3FF);
  transition: all 0.15s ease;
}

.lcd-btn:first-child {
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.lcd-btn:active {
  background: rgba(255, 255, 255, 0.1);
}

/* ─── State B: Expanded Cyber Header View ─── */
.expanded-header-view {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 14px;
  background: transparent;
}

.header-icon-btn {
  width: 38px;
  height: 38px;
  border-radius: var(--r-full);
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
  color: var(--c-text-1);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 
    2px 3px 6px rgba(0, 0, 0, 0.4),
    inset 0 1px 1px rgba(255, 255, 255, 0.2);
  transition: all 0.15s ease;
}

.header-icon-btn:active {
  transform: scale(0.92);
  background: rgba(0, 0, 0, 0.3);
}

.header-center-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 8px;
  min-width: 0;
}

.header-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1.5px;
  color: var(--c-accent);
  text-shadow: 0 0 6px var(--c-accent-glow);
}

.header-track-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.cyber-hd-badge {
  padding: 2px 6px;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.5px;
  background: linear-gradient(135deg, #ffd700, #ff8c00);
  color: #111;
  border-radius: 4px;
  box-shadow: 0 0 8px rgba(255, 215, 0, 0.6);
}

.header-like-btn.active {
  color: #ff4b7b;
  border-color: rgba(255, 75, 123, 0.4);
  box-shadow: 0 0 12px rgba(255, 75, 123, 0.6);
}

/* ═══════════════════════════════════════════════════════════
   2. FULLSCREEN PLAYER BODY CANVAS
   ═══════════════════════════════════════════════════════════ */

.fullscreen-player-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 10px 20px;
  min-height: 0;
  overflow: hidden;
  justify-content: space-between;
  will-change: transform, opacity;
}

.mobile-player-sheet:not(.is-in-motion) .fullscreen-player-body {
  transition: transform 0.35s cubic-bezier(0.2, 0.9, 0.2, 1), opacity 0.25s ease;
}

/* ─── Cover Art Section ─── */
.body-cover-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  min-height: 180px;
  max-height: 38vh;
  margin: 4px 0 12px;
}

.cover-card {
  width: 100%;
  max-width: min(280px, 34vh);
  aspect-ratio: 1;
  border-radius: 24px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.7),
    0 0 45px rgba(29, 185, 84, 0.18),
    inset 0 1px 1px rgba(255, 255, 255, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.14);
  transition: transform 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.body-cover-section.swiping .cover-card {
  transform: scale(0.94);
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-initials {
  font-size: 64px;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.75);
}

.cover-loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-spinner {
  color: var(--c-accent);
  animation: spin 1s linear infinite;
}

.cover-swipe-arrows {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.swipe-arrow-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid var(--c-accent);
  border-radius: var(--r-full);
  color: var(--c-accent);
  font-size: 12px;
  font-weight: 700;
  box-shadow: 0 0 16px var(--c-accent-glow);
}

/* ─── Track Info Section ─── */
.body-info-section {
  text-align: center;
  margin-bottom: 10px;
  flex-shrink: 0;
}

.body-track-title {
  font-size: 20px;
  font-weight: 800;
  color: var(--c-text-1);
  letter-spacing: -0.2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
  margin-bottom: 4px;
}

.body-track-artist {
  font-size: 14px;
  color: var(--c-text-2);
  font-weight: 500;
}

.artist-clickable-link {
  cursor: pointer;
  transition: color 0.15s ease;
}

.artist-clickable-link:hover {
  color: var(--c-accent);
  text-decoration: underline;
}

.body-tags-bar {
  justify-content: center;
  margin-top: 8px;
}

/* ─── Progress Bar Section ─── */
.body-progress-section {
  margin-bottom: 8px;
  flex-shrink: 0;
}

.progress-bar-wrapper {
  position: relative;
  width: 100%;
  height: 6px;
  background: rgba(0, 0, 0, 0.5);
  border-radius: var(--r-full);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.7);
}

.progress-buffered-track {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: rgba(255, 255, 255, 0.18);
  border-radius: var(--r-full);
  pointer-events: none;
}

.progress-played-track {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: linear-gradient(90deg, var(--c-accent-dark), var(--c-accent));
  border-radius: var(--r-full);
  box-shadow: 0 0 8px var(--c-accent-glow);
  pointer-events: none;
}

.progress-touch-slider {
  position: absolute;
  left: 0;
  top: -8px;
  width: 100%;
  height: 22px;
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  outline: none;
  cursor: pointer;
  z-index: 2;
  margin: 0;
}

.progress-touch-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: var(--r-full);
  border: 2px solid #ffffff;
  background: var(--c-accent);
  box-shadow: 0 0 10px var(--c-accent-glow), 0 2px 6px rgba(0, 0, 0, 0.6);
  cursor: pointer;
  transition: transform 0.15s ease;
}

.progress-touch-slider:active::-webkit-slider-thumb {
  transform: scale(1.3);
}

.progress-time-row {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--c-text-3);
  font-variant-numeric: tabular-nums;
}

/* ─── Auxiliary Row (Volume, Lyrics, Queue) ─── */
.body-aux-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 4px;
  flex-shrink: 0;
}

.aux-volume-control {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  max-width: 140px;
}

.aux-volume-slider {
  width: 100%;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: rgba(255, 255, 255, 0.12);
  border-radius: var(--r-full);
  outline: none;
  cursor: pointer;
}

.aux-volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: var(--r-full);
  background: #ffffff;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.6);
}

.aux-btn {
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
  color: var(--c-text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.aux-btn.mute-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--r-full);
}

.aux-btn.pill-btn {
  padding: 6px 12px;
  gap: 5px;
  border-radius: var(--r-full);
  font-size: 11px;
  font-weight: 600;
  box-shadow: 
    2px 2px 5px rgba(0, 0, 0, 0.35),
    inset 0 1px 1px rgba(255, 255, 255, 0.15);
}

.aux-btn.pill-btn:active {
  transform: scale(0.94);
  background: rgba(0, 0, 0, 0.3);
}

.aux-btn.pill-btn.active {
  color: var(--c-accent);
  border-color: rgba(29, 185, 84, 0.4);
  background: linear-gradient(145deg, rgba(29, 185, 84, 0.15) 0%, rgba(0, 0, 0, 0.25) 100%);
  box-shadow: 0 0 12px var(--c-accent-glow);
}

.queue-counter {
  background: var(--c-accent);
  color: #000;
  font-size: 9px;
  font-weight: 800;
  padding: 1px 5px;
  border-radius: var(--r-full);
}

/* ═════════════════════════════════════════════════════════════
   3. BOTTOM DOCK (MORPHING NAV ➔ CONTROLS)
   ═════════════════════════════════════════════════════════════ */

.morph-dock-container {
  position: relative;
  width: 100%;
  height: 64px;
  background: rgba(14, 18, 24, 0.88);
  backdrop-filter: blur(32px) saturate(180%);
  -webkit-backdrop-filter: blur(32px) saturate(180%);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: env(safe-area-inset-bottom);
  box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.45);
  flex-shrink: 0;
  z-index: 10;
}

/* ─── Layer A: Navigation Tabs ─── */
.dock-navigation-layer {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding-bottom: env(safe-area-inset-bottom);
  will-change: transform, opacity;
}

.nav-tab-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--c-text-3);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 12px;
  position: relative;
  min-width: 60px;
  transition: color 0.15s ease, transform 0.15s ease;
  -webkit-tap-highlight-color: transparent;
}

.nav-tab-btn.active {
  color: var(--c-accent);
}

.nav-tab-btn.active::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 28px;
  height: 3px;
  background: var(--c-accent);
  border-radius: 0 0 3px 3px;
}

.nav-tab-btn:active {
  transform: scale(0.93);
}

/* ─── Layer B: Playback Controls ─── */
.dock-controls-layer {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: space-evenly;
  padding: 0 16px;
  padding-bottom: env(safe-area-inset-bottom);
  will-change: transform, opacity;
}

.tactile-ctl-btn {
  width: 44px;
  height: 44px;
  border-radius: var(--r-full);
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.09) 0%, rgba(255, 255, 255, 0.02) 100%);
  color: var(--c-text-1);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 
    3px 4px 10px rgba(0, 0, 0, 0.45),
    -1px -1px 3px rgba(255, 255, 255, 0.05),
    inset 0 1px 1px rgba(255, 255, 255, 0.2);
  transition: all 0.15s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.tactile-ctl-btn:active {
  transform: scale(0.92);
  background: rgba(0, 0, 0, 0.4);
  box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.7);
}

.tactile-ctl-btn.secondary-btn {
  width: 40px;
  height: 40px;
  color: var(--c-text-3);
}

.tactile-ctl-btn.secondary-btn.active {
  color: var(--c-accent);
  border-color: rgba(29, 185, 84, 0.4);
  box-shadow: 0 0 14px var(--c-accent-glow);
}

/* Center Hero Play Button */
.tactile-hero-play-btn {
  width: 58px;
  height: 58px;
  border-radius: var(--r-full);
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: linear-gradient(145deg, #22e066 0%, #159b43 100%);
  color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  box-shadow: 
    0 6px 20px rgba(0, 0, 0, 0.6),
    0 0 24px var(--c-accent-glow),
    inset 0 2px 2px rgba(255, 255, 255, 0.6);
  transition: all 0.18s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.tactile-hero-play-btn:active {
  transform: scale(0.92);
  background: linear-gradient(145deg, #18b850 0%, #128038 100%);
  box-shadow: 0 0 14px var(--c-accent-glow);
}

/* ═══════════════════════════════════════════════════════════
   4. SLIDE-UP MODAL OVERLAYS (LYRICS & QUEUE)
   ═══════════════════════════════════════════════════════════ */

.inner-sheet-overlay {
  position: absolute;
  inset: 0;
  background: rgba(12, 16, 22, 0.97);
  backdrop-filter: blur(36px);
  -webkit-backdrop-filter: blur(36px);
  z-index: 50;
  display: flex;
  flex-direction: column;
}

.queue-overlay {
  top: auto;
  bottom: 0;
  height: 65%;
  border-radius: var(--r-xl) var(--r-xl) 0 0;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 -12px 36px rgba(0, 0, 0, 0.8);
}

.queue-sheet-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px 16px max(16px, env(safe-area-inset-bottom));
}

.queue-top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.queue-title-block {
  display: flex;
  flex-direction: column;
}

.queue-heading {
  font-size: 15px;
  font-weight: 700;
  color: var(--c-text-1);
}

.queue-subhint {
  font-size: 10px;
  color: var(--c-text-3);
}

.queue-close-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--r-full);
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  color: var(--c-text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.queue-scroll-list {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.queue-card-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 12px;
  margin-bottom: 6px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: background 0.15s ease;
}

.queue-card-item:active {
  background: rgba(255, 255, 255, 0.08);
}

.queue-index {
  font-size: 12px;
  font-weight: 700;
  color: var(--c-accent);
  width: 18px;
  text-align: center;
}

.queue-thumb {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background-size: cover;
  flex-shrink: 0;
}

.queue-meta {
  flex: 1;
  min-width: 0;
}

.q-title {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.q-artist {
  display: block;
  font-size: 11px;
  color: var(--c-text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-delete-badge {
  position: absolute;
  right: -36px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--c-accent);
  opacity: 0;
  transition: all 0.2s ease;
}

.queue-card-item.swiping .queue-delete-badge {
  opacity: 1;
  right: 12px;
}

.queue-card-item.swipe-delete {
  background: rgba(229, 57, 53, 0.25);
  border-color: rgba(229, 57, 53, 0.4);
}

.queue-lazy-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: rgba(26, 32, 44, 0.85);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  margin-top: 8px;
}

.lazy-icon {
  font-size: 20px;
}

.lazy-meta {
  display: flex;
  flex-direction: column;
}

.lazy-heading {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1);
}

.lazy-desc {
  font-size: 11px;
  color: var(--c-text-3);
}

.queue-empty-state {
  text-align: center;
  padding: 32px 16px;
  color: var(--c-text-3);
  font-size: 13px;
}

/* ─── Slide Up Transitions ─── */
.sheet-slide-up-enter-active,
.sheet-slide-up-leave-active {
  transition: transform 0.3s cubic-bezier(0.2, 0.9, 0.2, 1), opacity 0.2s ease;
}

.sheet-slide-up-enter-from,
.sheet-slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

/* ─── Utilities ─── */
.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (min-width: 1024px) {
  .mobile-player-sheet {
    display: none;
  }
}
</style>
