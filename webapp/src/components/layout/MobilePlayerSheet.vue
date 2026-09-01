<template>
  <div 
    class="mobile-player-sheet" 
    :class="sheetClasses"
    :style="sheetStyle"
    ref="sheetRootRef"
  >
    <!-- Background Backdrop Overlay (Fades in on drag/expand) -->
    <div 
      class="player-backdrop"
      :style="{ opacity: expandProgress * 0.96 }"
      @click="handleBackdropClick"
    ></div>

    <!-- Ambient Dynamic Light Aura based on cover artwork -->
    <div 
      class="ambient-aura"
      :style="{ opacity: expandProgress * 0.85 }"
    >
      <div class="aura-glow primary" :style="ambientCoverStyle"></div>
      <div class="aura-glow secondary"></div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         1. MORPHING TOP HEADER (PHYSICALLY TRAVELS BOTTOM ➔ TOP)
         ═══════════════════════════════════════════════════════════ -->
    <div 
      v-if="hasTrack"
      class="morph-header-unit"
      :style="headerTransformStyle"
      @touchstart="onHeaderTouchStart"
      @touchmove="onHeaderTouchMove"
      @touchend="onHeaderTouchEnd"
      @touchcancel="onHeaderTouchEnd"
      @click="handleHeaderClick"
    >
      <!-- Top Drag Bar Pill Indicator -->
      <div class="drag-indicator-bar">
        <div class="drag-pill" :class="{ expanded: expandProgress > 0.5 }"></div>
      </div>

      <!-- [STATE A: Collapsed] Nokia / Cyber LCD Mini Player -->
      <div 
        class="mini-lcd-view"
        :style="{ 
          opacity: Math.max(0, 1 - expandProgress * 2.2),
          pointerEvents: expandProgress > 0.3 ? 'none' : 'auto',
          transform: `scale(${1 - expandProgress * 0.08})`
        }"
        @contextmenu.prevent="openTrackContextMenu($event)"
      >
        <div class="lcd-housing">
          <!-- Row 1: Title Marquee + Live Spectrum + Indicators -->
          <div class="lcd-row row-top">
            <div class="lcd-live-spectrum" v-if="isPlaying">
              <span class="bar bar-1"></span>
              <span class="bar bar-2"></span>
              <span class="bar bar-3"></span>
            </div>
            
            <div class="lcd-title-marquee-wrap">
              <div class="lcd-marquee-track" :class="{ 'marquee': shouldMarquee }">
                <span class="lcd-title-text">{{ displayText }}</span>
                <span v-if="shouldMarquee" class="lcd-title-text lcd-title-clone">{{ displayText }}</span>
              </div>
            </div>

            <div class="lcd-indicators-group">
              <!-- Network issue -->
              <span 
                v-if="networkMonitor.hasIssues.value" 
                class="lcd-icon net-icon active" 
                :class="{ pulse: networkMonitor.connectionState.value === 'reconnecting' }"
                :title="networkMonitor.connectionState.value === 'offline' ? 'Нет сети' : 'Восстановление...'"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="1" y1="1" x2="23" y2="23"/>
                  <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/>
                  <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/>
                  <line x1="12" y1="20" x2="12.01" y2="20"/>
                </svg>
              </span>

              <!-- HD Badge -->
              <span v-if="playerStore.hdTrackInfo" class="lcd-icon hd-icon active" title="HD версия">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-8 12H9.5v-2h-2v2H6V9h1.5v2.5h2V9H11v6zm2-6h4c.55 0 1 .45 1 1v4c0 .55-.45 1-1 1h-4V9zm1.5 4.5h2v-3h-2v3z"/>
                </svg>
              </span>

              <!-- Like Button -->
              <span 
                class="lcd-icon like-icon" 
                :class="{ active: isLiked }" 
                @click.stop="$emit('like')"
                title="Лайк"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" :fill="isLiked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                </svg>
              </span>

              <!-- Shuffle -->
              <span 
                class="lcd-icon" 
                :class="{ active: shuffle }" 
                @click.stop="$emit('toggle-shuffle')"
                title="Перемешать"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
                </svg>
              </span>

              <!-- Repeat -->
              <span 
                class="lcd-icon" 
                :class="{ active: repeat !== 'none' }" 
                @click.stop="$emit('toggle-repeat')"
                :title="repeatTitle"
              >
                <svg v-if="repeat === 'one'" width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4zm-4-2V9h-1l-2 1v1h1.5v4H13z"/>
                </svg>
                <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/>
                </svg>
              </span>
            </div>
          </div>

          <!-- Row 2: 20 LED Dots Progress + Time + Mini Play Controls -->
          <div class="lcd-row row-bottom">
            <div class="lcd-led-progress">
              <span 
                class="lcd-led-dot" 
                v-for="i in 20" 
                :key="i" 
                :class="getDotClass(i, 20)"
              ></span>
            </div>

            <span class="lcd-time-display">{{ formatTime(progress) }}/{{ formatTime(duration || currentTrack?.duration) }}</span>

            <div class="lcd-quick-btns">
              <button class="lcd-action-btn" @click.stop="$emit('toggle-play')" title="Play/Pause">
                <svg v-if="loading" class="spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <path d="M12 2a10 10 0 0 1 10 10"/>
                </svg>
                <svg v-else-if="isPlaying" width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
                </svg>
                <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </button>
              <button class="lcd-action-btn" @click.stop="$emit('next-track')" title="Next">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- [STATE B: Expanded] Top Cyber HUD Island Header -->
      <div 
        class="cyber-top-island"
        :style="{ 
          opacity: Math.max(0, (expandProgress - 0.3) * 1.45),
          pointerEvents: expandProgress < 0.5 ? 'none' : 'auto'
        }"
      >
        <button class="hud-circle-btn collapse-trigger" @click.stop="collapsePlayer" title="Свернуть">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>

        <!-- Center Cyber HUD Display -->
        <div class="hud-center-capsule">
          <div class="hud-now-playing-row">
            <span class="hud-equalizer-bars" v-if="isPlaying">
              <span class="hud-eq-bar b1"></span>
              <span class="hud-eq-bar b2"></span>
              <span class="hud-eq-bar b3"></span>
              <span class="hud-eq-bar b4"></span>
            </span>
            <span class="hud-tag-title">СЕЙЧАС ИГРАЕТ</span>
            <span v-if="playerStore.hdTrackInfo" class="hud-hd-chip">HD</span>
          </div>
          <span class="hud-track-marquee">{{ getDisplayTitle(currentTrack) }}</span>
        </div>

        <div class="hud-actions-right">
          <button 
            class="hud-circle-btn like-btn" 
            :class="{ active: isLiked }"
            @click.stop="$emit('like')"
            title="Лайк"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" :fill="isLiked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
          </button>
          <button 
            class="hud-circle-btn menu-btn"
            @click.stop="openTrackContextMenu($event)"
            title="Опции"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <circle cx="12" cy="5" r="2"/>
              <circle cx="12" cy="12" r="2"/>
              <circle cx="12" cy="19" r="2"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         2. FULLSCREEN PLAYER CANVAS (PULLED UP WITH THE SHEET)
         ═══════════════════════════════════════════════════════════ -->
    <div 
      class="fullscreen-canvas-body"
      :style="{ 
        opacity: Math.max(0, (expandProgress - 0.15) * 1.18),
        transform: `translateY(${(1 - expandProgress) * 50}px) scale(${0.9 + expandProgress * 0.1})`,
        pointerEvents: expandProgress < 0.6 ? 'none' : 'auto'
      }"
    >
      <!-- 3D Neumorphic Album Cover with Horizontal Gestures -->
      <div 
        class="cover-art-viewport"
        :class="{ swiping: isCoverSwiping }"
        @touchstart="onCoverTouchStart"
        @touchmove="onCoverTouchMove"
        @touchend="onCoverTouchEnd"
        @touchcancel="onCoverTouchEnd"
        @contextmenu.prevent="openTrackContextMenu($event)"
      >
        <div class="cover-neon-halo"></div>
        <div class="cover-vinyl-frame" :style="coverStyle">
          <span v-if="!currentTrack?.cover_url" class="cover-initials-txt">{{ coverInitials }}</span>
          <img 
            v-else 
            :src="getCoverUrl(currentTrack.cover_url, CoverSize.XL)" 
            alt="Cover" 
            class="cover-art-img" 
            draggable="false"
          />

          <!-- Loading Spinner Overlay -->
          <div v-if="loading" class="cover-spin-overlay">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" class="spin">
              <circle cx="12" cy="12" r="10" stroke-width="3" stroke-opacity="0.25"/>
              <path d="M12 2a10 10 0 0 1 10 10" stroke-width="3" stroke-linecap="round"/>
            </svg>
          </div>
        </div>

        <!-- Directional Swipe Feedback Badges -->
        <div v-if="isCoverSwiping" class="cover-swipe-hints">
          <div v-if="coverSwipeDirection === 'left'" class="swipe-badge next-badge">
            <span>Дальше</span>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
            </svg>
          </div>
          <div v-if="coverSwipeDirection === 'right'" class="swipe-badge prev-badge">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15.41 16.59L10.83 12l4.58-4.59L14 6l-6 6 6 6 1.41-1.41z"/>
            </svg>
            <span>Назад</span>
          </div>
        </div>
      </div>

      <!-- Track Information & Clickable Artists -->
      <div class="track-meta-section" @contextmenu.prevent="openTrackContextMenu($event)">
        <h2 class="track-main-title">{{ getDisplayTitle(currentTrack) }}</h2>
        
        <p class="track-artists-row">
          <template v-if="parsedArtists.length > 0">
            <template v-for="(artist, index) in parsedArtists" :key="artist">
              <span class="artist-badge-link" @click.stop="goToArtist(artist)">{{ artist }}</span>
              <span v-if="index < parsedArtists.length - 1" class="artist-dot-sep">, </span>
            </template>
          </template>
          <span v-else>{{ getDisplayArtist(currentTrack) }}</span>
        </p>

        <!-- Interactive Tag Pills -->
        <TrackTags
          v-if="currentTrack?.id"
          :trackId="currentTrack.id"
          :tags="currentTrack.tags || []"
          :interactive="true"
          :max="5"
          class="track-tags-container"
        />
      </div>

      <!-- Cyber Scrubber Progress Slider -->
      <div class="scrubber-section">
        <div class="scrubber-track-rail">
          <div class="scrubber-buffered-fill" :style="{ width: `${bufferedPercent}%` }"></div>
          <div class="scrubber-played-fill" :style="{ width: `${progressPercent}%` }"></div>
          <input 
            type="range"
            class="scrubber-range-input"
            :value="progress"
            min="0"
            :max="duration || currentTrack?.duration || 100"
            @input="$emit('seek', Number($event.target.value))"
          />
        </div>
        <div class="scrubber-timestamp-row">
          <span class="ts current">{{ formatTime(progress) }}</span>
          <span class="ts total">{{ formatTime(duration || currentTrack?.duration) }}</span>
        </div>
      </div>

      <!-- Auxiliary Bar: Volume + Lyrics + Queue -->
      <div class="aux-tools-row">
        <!-- Compact Volume Slider -->
        <div class="aux-volume-wrap">
          <button class="aux-tool-btn mute-btn" @click.stop="$emit('toggle-mute')">
            <svg v-if="isMuted || volume === 0" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
            </svg>
            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
            </svg>
          </button>
          <input 
            type="range"
            class="aux-volume-range"
            :value="isMuted ? 0 : volume * 100"
            min="0"
            max="100"
            @input="$emit('set-volume', Number($event.target.value) / 100)"
          />
        </div>

        <!-- Lyrics Pill Button -->
        <button 
          class="aux-tool-btn pill-btn lyrics-pill" 
          :class="{ active: showLyrics }"
          @click.stop="toggleLyrics"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            <line x1="8" y1="8" x2="16" y2="8"></line>
            <line x1="8" y1="12" x2="13" y2="12"></line>
          </svg>
          <span>Текст</span>
        </button>

        <!-- Queue Pill Button -->
        <button 
          class="aux-tool-btn pill-btn queue-pill" 
          :class="{ active: showQueue }"
          @click.stop="toggleQueue"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M4 10h12v2H4zm0-4h12v2H4zm0 8h8v2H4zm10 0v6l5-3z"/>
          </svg>
          <span>Очередь</span>
          <span v-if="upcomingQueue.length" class="queue-num-chip">{{ upcomingQueue.length }}</span>
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         3. BOTTOM DOCK (MORPHS NAVIGATION ➔ 5 PLAYBACK CONTROLS)
         ═══════════════════════════════════════════════════════════ -->
    <div class="bottom-morph-dock">
      <!-- Layer A: Navigation Tabs (Active in Collapsed State) -->
      <nav 
        v-if="showNav"
        class="dock-layer navigation-layer"
        :style="{ 
          opacity: Math.max(0, 1 - expandProgress * 2.2),
          pointerEvents: expandProgress > 0.3 ? 'none' : 'auto',
          transform: `translateY(${expandProgress * 16}px)`
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
          <span class="nav-tab-title">{{ item.label }}</span>
        </button>
      </nav>

      <!-- Layer B: Playback Controls Deck (Active in Expanded State) -->
      <div 
        class="dock-layer controls-layer"
        :style="{ 
          opacity: Math.max(0, (expandProgress - 0.35) * 1.55),
          pointerEvents: expandProgress < 0.6 ? 'none' : 'auto',
          transform: `translateY(${(1 - expandProgress) * 20}px)`
        }"
      >
        <!-- Slot 1: Shuffle (Morphs from 'Библиотека') -->
        <button 
          class="dock-ctl-btn secondary-btn"
          :class="{ active: shuffle }"
          @click.stop="$emit('toggle-shuffle')"
          title="Перемешать"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
            <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
          </svg>
        </button>

        <!-- Slot 2: Previous Track (Morphs from 'Любимое') -->
        <button 
          class="dock-ctl-btn"
          @click.stop="$emit('prev-track')"
          title="Предыдущий трек"
        >
          <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
          </svg>
        </button>

        <!-- Slot 3: Master Hero Play/Pause Button (Center: Morphs from 'Коллекции') -->
        <button 
          class="dock-hero-play-btn"
          @click.stop="$emit('toggle-play')"
          title="Play / Pause"
        >
          <div class="hero-neon-ring"></div>
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

        <!-- Slot 4: Next Track (Morphs from 'Кенты') -->
        <button 
          class="dock-ctl-btn"
          @click.stop="$emit('next-track')"
          title="Следующий трек"
        >
          <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
          </svg>
        </button>

        <!-- Slot 5: Repeat Mode (Morphs from 'Настройки') -->
        <button 
          class="dock-ctl-btn secondary-btn"
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
         4. SLIDE-UP MODAL SHEETS (LYRICS & QUEUE)
         ═══════════════════════════════════════════════════════════ -->
    <!-- Lyrics Modal -->
    <Transition name="sheet-slide-up">
      <div v-if="showLyrics" class="inner-modal-sheet lyrics-modal">
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
      <div v-if="showQueue" class="inner-modal-sheet queue-modal">
        <div class="queue-drawer-container">
          <div class="queue-drawer-header">
            <div class="queue-hdr-text">
              <span class="queue-main-title">Очередь воспроизведения</span>
              <span class="queue-swipe-hint">Свайп влево для удаления</span>
            </div>
            <button class="queue-close-circle" @click="showQueue = false">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <div class="queue-items-scroll">
            <div 
              v-for="(t, idx) in upcomingQueue" 
              :key="`q-${t.id}-${idx}`"
              class="queue-row-card"
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
              <span class="q-row-num">{{ idx + 1 }}</span>
              <div class="q-row-cover" :style="getQueueCoverStyle(t)"></div>
              <div class="q-row-details">
                <span class="q-row-title">{{ getDisplayTitle(t) }}</span>
                <span class="q-row-artist">{{ getDisplayArtist(t) }}</span>
              </div>
              <div class="q-del-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                </svg>
              </div>
            </div>

            <div v-if="lazyShuffleMode" class="queue-shuffle-banner">
              <div class="shuffle-badge-icon">🔀</div>
              <div class="shuffle-badge-info">
                <span class="banner-title">Режим бесконечного перемешивания</span>
                <span class="banner-meta">{{ lazyShuffleIndex + 1 }} из {{ lazyShuffleTotal }} треков</span>
              </div>
            </div>

            <div v-else-if="!upcomingQueue.length" class="queue-empty-msg">
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
// 🌟 60FPS GESTURE & MORPH ENGINE
// ═════════════════════════════════════════════════════════════
const sheetRootRef = ref(null)

const expandProgress = ref(props.isExpanded ? 1.0 : 0.0)
const isDragging = ref(false)
const dragStartY = ref(0)
const dragStartProgress = ref(0)
const dragLastY = ref(0)
const dragLastTime = ref(0)
const dragVelocityY = ref(0)

const showLyrics = ref(false)
const showQueue = ref(false)

// Cover swipe state
const isCoverSwiping = ref(false)
const coverSwipeDirection = ref(null)
const coverTouchStartX = ref(0)
const coverTouchStartY = ref(0)
const coverTouchMoved = ref(false)
let coverLongPressTimer = null

// Queue delete swipe
const swipingQueueIndex = ref(-1)
const queueSwipeStartX = ref(0)
const queueSwipeProgress = ref(0)
const QUEUE_SWIPE_THRESHOLD = 90

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

const sheetStyle = computed(() => {
  if (expandProgress.value > 0.01) {
    return {
      top: '0px',
      height: '100%'
    }
  }
  return {
    top: 'auto',
    height: 'auto'
  }
})

// Header travel calculation
const headerTransformStyle = computed(() => {
  // When collapsed (progress 0): sits at bottom right above bottom nav bar (translateY = calc(100vh - 66px - headerHeight))
  // When expanded (progress 1): sits at top (translateY = 0)
  const p = expandProgress.value
  return {
    transform: `translateY(calc( (1 - ${p}) * (100vh - 68px - 66px - env(safe-area-inset-top, 0px)) ))`,
    transition: isDragging.value ? 'none' : 'transform 0.35s cubic-bezier(0.2, 0.9, 0.2, 1)'
  }
})

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
const ambientCoverStyle = computed(() => coverStyle.value)

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
// 🖐️ TOUCH GESTURES (SWIPE UP / DOWN)
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

  const travelDistance = getScreenHeight() * 0.72
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
    if (v < -0.3 || expandProgress.value > 0.22) {
      target = 1
    } else {
      target = 0
    }
  } else {
    if (v > 0.3 || expandProgress.value < 0.78) {
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
// 💿 COVER TOUCH SWIPE (NEXT / PREV)
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

  // Horizontal swipe for tracks
  if (Math.abs(deltaX) > 20 && Math.abs(deltaX) > Math.abs(deltaY) * 1.3) {
    isCoverSwiping.value = true
    coverSwipeDirection.value = deltaX > 0 ? 'right' : 'left'
  }
  // Vertical swipe down to collapse
  else if (deltaY > 25 && Math.abs(deltaY) > Math.abs(deltaX) * 1.3) {
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
    if (deltaX < -50) {
      telegram?.HapticFeedback?.impactOccurred?.('medium')
      emit('next-track')
    } else if (deltaX > 50) {
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
  justify-content: space-between;
  pointer-events: auto;
  user-select: none;
  -webkit-user-select: none;
  font-family: var(--font-sans);
  overflow: hidden;
}

/* ─── Backdrop Blur Overlay ─── */
.player-backdrop {
  position: fixed;
  inset: 0;
  background: radial-gradient(circle at 50% 25%, rgba(20, 26, 36, 0.96) 0%, rgba(6, 8, 12, 0.99) 100%);
  backdrop-filter: blur(44px) saturate(200%);
  -webkit-backdrop-filter: blur(44px) saturate(200%);
  pointer-events: none;
  z-index: 0;
  transition: opacity 0.2s linear;
}

.mobile-player-sheet.is-expanded .player-backdrop {
  pointer-events: auto;
}

/* ─── Ambient Dynamic Glow Aura ─── */
.ambient-aura {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  overflow: hidden;
  transition: opacity 0.25s ease;
}

.aura-glow.primary {
  position: absolute;
  top: 12%;
  left: 50%;
  transform: translateX(-50%);
  width: 320px;
  height: 320px;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.35;
}

.aura-glow.secondary {
  position: absolute;
  bottom: 20%;
  right: 15%;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: var(--c-accent-glow, rgba(29, 185, 84, 0.4));
  filter: blur(90px);
  opacity: 0.25;
}

/* ═══════════════════════════════════════════════════════════
   1. MORPHING TOP HEADER UNIT
   ═══════════════════════════════════════════════════════════ */

.morph-header-unit {
  position: relative;
  z-index: 10;
  width: 100%;
  padding-top: max(4px, env(safe-area-inset-top, 4px));
  touch-action: pan-x pan-y;
  cursor: pointer;
  will-change: transform;
}

.drag-indicator-bar {
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 3px 0 2px;
  pointer-events: none;
}

.drag-pill {
  width: 38px;
  height: 4px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: var(--r-full);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
  transition: width 0.2s ease, background 0.2s ease;
}

.drag-pill.expanded {
  width: 44px;
  background: rgba(255, 255, 255, 0.45);
}

/* ─── State A: Mini LCD Player View ─── */
.mini-lcd-view {
  margin: 2px 8px 4px;
  padding: 3px;
  background: rgba(18, 24, 32, 0.85);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-radius: var(--r-lg);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 
    0 8px 24px rgba(0, 0, 0, 0.45),
    inset 0 1px 1px rgba(255, 255, 255, 0.18);
  transition: transform 0.15s ease;
}

.mini-lcd-view:active {
  transform: scale(0.985);
}

.lcd-housing {
  background: linear-gradient(180deg, rgba(8, 16, 24, 0.94) 0%, rgba(3, 8, 14, 0.98) 100%);
  border-radius: var(--r-md);
  padding: 7px 10px;
  border: 1px solid rgba(77, 195, 255, 0.18);
  box-shadow: 
    inset 0 2px 10px rgba(0, 0, 0, 0.85),
    0 1px 0 rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  gap: 5px;
  position: relative;
  overflow: hidden;
}

.lcd-housing::before {
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

.row-top {
  justify-content: space-between;
}

.lcd-live-spectrum {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 12px;
  flex-shrink: 0;
}

.lcd-live-spectrum .bar {
  width: 2px;
  background: var(--c-accent, #1db954);
  border-radius: 1px;
  box-shadow: 0 0 4px var(--c-accent-glow);
  animation: spectrum-jump 0.8s infinite ease-in-out alternate;
}

.lcd-live-spectrum .bar-1 { height: 60%; animation-delay: 0.1s; }
.lcd-live-spectrum .bar-2 { height: 100%; animation-delay: 0.3s; }
.lcd-live-spectrum .bar-3 { height: 40%; animation-delay: 0.2s; }

@keyframes spectrum-jump {
  0% { height: 25%; }
  100% { height: 100%; }
}

.lcd-title-marquee-wrap {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  mask-image: linear-gradient(90deg, black 90%, transparent 100%);
  -webkit-mask-image: linear-gradient(90deg, black 90%, transparent 100%);
}

.lcd-marquee-track {
  display: inline-flex;
  white-space: nowrap;
}

.lcd-marquee-track.marquee {
  animation: marquee-scroll 12s linear infinite;
}

.lcd-title-text {
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

.lcd-indicators-group {
  display: flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
}

.lcd-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.3);
  cursor: pointer;
  transition: all 0.15s ease;
}

.lcd-icon.active {
  color: var(--lcd-text, #4DC3FF);
  text-shadow: 0 0 6px var(--lcd-glow, rgba(77, 195, 255, 0.6));
}

.lcd-icon.like-icon.active {
  color: #ff4b7b;
  text-shadow: 0 0 8px rgba(255, 75, 123, 0.8);
}

.lcd-icon.hd-icon.active {
  color: #ffd700;
  text-shadow: 0 0 8px rgba(255, 215, 0, 0.8);
}

.lcd-icon.net-icon.active {
  color: #ff6b6b;
}

.row-bottom {
  gap: 8px;
}

.lcd-led-progress {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 2px;
  min-width: 0;
}

.lcd-led-dot {
  flex: 1;
  height: 4px;
  min-width: 2px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  transition: background 0.15s ease, box-shadow 0.15s ease;
}

.lcd-led-dot.active {
  background: var(--c-accent);
  box-shadow: 0 0 5px var(--c-accent-glow);
}

.lcd-led-dot.buffered {
  background: rgba(0, 188, 212, 0.35);
}

.lcd-led-dot.next {
  background: var(--c-accent);
  animation: dot-blink 0.6s infinite ease-in-out;
}

@keyframes dot-blink {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; box-shadow: 0 0 6px var(--c-accent-glow); }
}

.lcd-time-display {
  font-size: 10px;
  font-weight: 600;
  color: var(--lcd-text, #4DC3FF);
  font-variant-numeric: tabular-nums;
  min-width: 60px;
  text-align: right;
}

.lcd-quick-btns {
  display: flex;
  border-radius: 6px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.lcd-action-btn {
  width: 28px;
  height: 22px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--lcd-text, #4DC3FF);
  transition: all 0.15s ease;
}

.lcd-action-btn:first-child {
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.lcd-action-btn:active {
  background: rgba(255, 255, 255, 0.12);
}

/* ─── State B: Expanded Top Cyber HUD Island ─── */
.cyber-top-island {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 14px;
  background: transparent;
}

.hud-circle-btn {
  width: 38px;
  height: 38px;
  border-radius: var(--r-full);
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.09) 0%, rgba(255, 255, 255, 0.02) 100%);
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

.hud-circle-btn:active {
  transform: scale(0.92);
  background: rgba(0, 0, 0, 0.35);
}

.hud-center-capsule {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 10px;
  min-width: 0;
}

.hud-now-playing-row {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 2px;
}

.hud-equalizer-bars {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 10px;
}

.hud-eq-bar {
  width: 2px;
  background: var(--c-accent, #1db954);
  border-radius: 1px;
  animation: eq-bounce 0.6s infinite ease-in-out alternate;
}

.hud-eq-bar.b1 { height: 80%; animation-delay: 0.1s; }
.hud-eq-bar.b2 { height: 100%; animation-delay: 0.3s; }
.hud-eq-bar.b3 { height: 50%; animation-delay: 0.2s; }
.hud-eq-bar.b4 { height: 90%; animation-delay: 0.4s; }

@keyframes eq-bounce {
  0% { height: 20%; }
  100% { height: 100%; }
}

.hud-tag-title {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1.5px;
  color: var(--c-accent);
  text-shadow: 0 0 6px var(--c-accent-glow);
}

.hud-hd-chip {
  padding: 1px 5px;
  font-size: 9px;
  font-weight: 800;
  background: linear-gradient(135deg, #ffd700, #ff8c00);
  color: #111;
  border-radius: 3px;
  box-shadow: 0 0 6px rgba(255, 215, 0, 0.6);
}

.hud-track-marquee {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.hud-actions-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.hud-circle-btn.like-btn.active {
  color: #ff4b7b;
  border-color: rgba(255, 75, 123, 0.4);
  box-shadow: 0 0 12px rgba(255, 75, 123, 0.6);
}

/* ═══════════════════════════════════════════════════════════
   2. FULLSCREEN CANVAS BODY (EXPANDS IN MIDDLE)
   ═══════════════════════════════════════════════════════════ */

.fullscreen-canvas-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 6px 20px 10px;
  min-height: 0;
  overflow: hidden;
  z-index: 5;
  transition: transform 0.35s cubic-bezier(0.2, 0.9, 0.2, 1), opacity 0.25s ease;
}

/* ─── Cover Art Viewport ─── */
.cover-art-viewport {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  min-height: 180px;
  max-height: 38vh;
  margin: 4px 0 10px;
}

.cover-neon-halo {
  position: absolute;
  width: min(270px, 32vh);
  aspect-ratio: 1;
  border-radius: 28px;
  background: var(--c-accent-glow, rgba(29, 185, 84, 0.3));
  filter: blur(30px);
  opacity: 0.4;
  pointer-events: none;
}

.cover-vinyl-frame {
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
    0 20px 40px rgba(0, 0, 0, 0.75),
    0 0 40px rgba(29, 185, 84, 0.2),
    inset 0 1px 1px rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.16);
  transition: transform 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.cover-art-viewport.swiping .cover-vinyl-frame {
  transform: scale(0.94);
}

.cover-art-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-initials-txt {
  font-size: 64px;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.75);
}

.cover-spin-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-accent);
}

.cover-swipe-hints {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.swipe-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid var(--c-accent);
  border-radius: var(--r-full);
  color: var(--c-accent);
  font-size: 12px;
  font-weight: 700;
  box-shadow: 0 0 16px var(--c-accent-glow);
}

/* ─── Track Meta Section ─── */
.track-meta-section {
  text-align: center;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.track-main-title {
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

.track-artists-row {
  font-size: 14px;
  color: var(--c-text-2);
  font-weight: 500;
}

.artist-badge-link {
  cursor: pointer;
  transition: color 0.15s ease;
}

.artist-badge-link:hover {
  color: var(--c-accent);
  text-decoration: underline;
}

.track-tags-container {
  justify-content: center;
  margin-top: 8px;
}

/* ─── Scrubber Progress Section ─── */
.scrubber-section {
  margin-bottom: 6px;
  flex-shrink: 0;
}

.scrubber-track-rail {
  position: relative;
  width: 100%;
  height: 6px;
  background: rgba(0, 0, 0, 0.55);
  border-radius: var(--r-full);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.7);
}

.scrubber-buffered-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: rgba(255, 255, 255, 0.18);
  border-radius: var(--r-full);
  pointer-events: none;
}

.scrubber-played-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: linear-gradient(90deg, var(--c-accent-dark, #169c46), var(--c-accent, #1db954));
  border-radius: var(--r-full);
  box-shadow: 0 0 8px var(--c-accent-glow);
  pointer-events: none;
}

.scrubber-range-input {
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

.scrubber-range-input::-webkit-slider-thumb {
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

.scrubber-range-input:active::-webkit-slider-thumb {
  transform: scale(1.3);
}

.scrubber-timestamp-row {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--c-text-3);
  font-variant-numeric: tabular-nums;
}

/* ─── Auxiliary Tools Row (Volume, Lyrics, Queue) ─── */
.aux-tools-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 2px;
  flex-shrink: 0;
}

.aux-volume-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  max-width: 140px;
}

.aux-volume-range {
  width: 100%;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: rgba(255, 255, 255, 0.12);
  border-radius: var(--r-full);
  outline: none;
  cursor: pointer;
}

.aux-volume-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: var(--r-full);
  background: #ffffff;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.6);
}

.aux-tool-btn {
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
  color: var(--c-text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.aux-tool-btn.mute-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--r-full);
}

.aux-tool-btn.pill-btn {
  padding: 6px 12px;
  gap: 5px;
  border-radius: var(--r-full);
  font-size: 11px;
  font-weight: 600;
  box-shadow: 
    2px 2px 5px rgba(0, 0, 0, 0.35),
    inset 0 1px 1px rgba(255, 255, 255, 0.15);
}

.aux-tool-btn.pill-btn:active {
  transform: scale(0.94);
  background: rgba(0, 0, 0, 0.3);
}

.aux-tool-btn.pill-btn.active {
  color: var(--c-accent);
  border-color: rgba(29, 185, 84, 0.4);
  background: linear-gradient(145deg, rgba(29, 185, 84, 0.15) 0%, rgba(0, 0, 0, 0.25) 100%);
  box-shadow: 0 0 12px var(--c-accent-glow);
}

.queue-num-chip {
  background: var(--c-accent);
  color: #000;
  font-size: 9px;
  font-weight: 800;
  padding: 1px 5px;
  border-radius: var(--r-full);
}

/* ═══════════════════════════════════════════════════════════
   3. BOTTOM MORPH DOCK (NAV ➔ CONTROLS)
   ═══════════════════════════════════════════════════════════ */

.bottom-morph-dock {
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
.dock-layer.navigation-layer {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding-bottom: env(safe-area-inset-bottom);
  will-change: transform, opacity;
  transition: transform 0.25s ease, opacity 0.2s ease;
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

/* ─── Layer B: Playback Controls Deck ─── */
.dock-layer.controls-layer {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: space-evenly;
  padding: 0 16px;
  padding-bottom: env(safe-area-inset-bottom);
  will-change: transform, opacity;
  transition: transform 0.25s ease, opacity 0.2s ease;
}

.dock-ctl-btn {
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

.dock-ctl-btn:active {
  transform: scale(0.92);
  background: rgba(0, 0, 0, 0.4);
  box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.7);
}

.dock-ctl-btn.secondary-btn {
  width: 40px;
  height: 40px;
  color: var(--c-text-3);
}

.dock-ctl-btn.secondary-btn.active {
  color: var(--c-accent);
  border-color: rgba(29, 185, 84, 0.4);
  box-shadow: 0 0 14px var(--c-accent-glow);
}

/* Center Master Hero Play Button */
.dock-hero-play-btn {
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

.dock-hero-play-btn:active {
  transform: scale(0.92);
  background: linear-gradient(145deg, #18b850 0%, #128038 100%);
  box-shadow: 0 0 14px var(--c-accent-glow);
}

/* ═══════════════════════════════════════════════════════════
   4. MODAL SHEETS (LYRICS & QUEUE)
   ═══════════════════════════════════════════════════════════ */

.inner-modal-sheet {
  position: absolute;
  inset: 0;
  background: rgba(12, 16, 22, 0.97);
  backdrop-filter: blur(36px);
  -webkit-backdrop-filter: blur(36px);
  z-index: 50;
  display: flex;
  flex-direction: column;
}

.queue-modal {
  top: auto;
  bottom: 0;
  height: 65%;
  border-radius: var(--r-xl) var(--r-xl) 0 0;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 -12px 36px rgba(0, 0, 0, 0.8);
}

.queue-drawer-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px 16px max(16px, env(safe-area-inset-bottom));
}

.queue-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.queue-hdr-text {
  display: flex;
  flex-direction: column;
}

.queue-main-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--c-text-1);
}

.queue-swipe-hint {
  font-size: 10px;
  color: var(--c-text-3);
}

.queue-close-circle {
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

.queue-items-scroll {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.queue-row-card {
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

.queue-row-card:active {
  background: rgba(255, 255, 255, 0.08);
}

.q-row-num {
  font-size: 12px;
  font-weight: 700;
  color: var(--c-accent);
  width: 18px;
  text-align: center;
}

.q-row-cover {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background-size: cover;
  flex-shrink: 0;
}

.q-row-details {
  flex: 1;
  min-width: 0;
}

.q-row-title {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.q-row-artist {
  display: block;
  font-size: 11px;
  color: var(--c-text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.q-del-icon {
  position: absolute;
  right: -36px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--c-accent);
  opacity: 0;
  transition: all 0.2s ease;
}

.queue-row-card.swiping .q-del-icon {
  opacity: 1;
  right: 12px;
}

.queue-row-card.swipe-delete {
  background: rgba(229, 57, 53, 0.25);
  border-color: rgba(229, 57, 53, 0.4);
}

.queue-shuffle-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: rgba(26, 32, 44, 0.85);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  margin-top: 8px;
}

.shuffle-badge-icon {
  font-size: 20px;
}

.shuffle-badge-info {
  display: flex;
  flex-direction: column;
}

.banner-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1);
}

.banner-meta {
  font-size: 11px;
  color: var(--c-text-3);
}

.queue-empty-msg {
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
