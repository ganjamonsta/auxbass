<template>
  <div class="dj-view-container">
    <!-- ═════════════════════════════════════════════════════════════
         TOP HEADER BAR: Discord Server Info & Status
         ═════════════════════════════════════════════════════════════ -->
    <header class="dj-header neu-panel">
      <div class="dj-header-left">
        <button class="neu-btn-icon back-btn" @click="handleGoBack" title="Назад">
          <ArrowLeft :size="20" />
        </button>

        <div class="dj-title-box">
          <div class="dj-badge-row">
            <div class="discord-tag">
              <svg width="15" height="15" viewBox="0 0 127.14 96.36" fill="currentColor">
                <path d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,45.91,53.88,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,45.91,96.12,53,91.08,65.69,84.69,65.69Z"/>
              </svg>
              <span>DISCORD DJ DECK</span>
            </div>

            <div v-if="discordStore.hasParty" class="live-status-pill">
              <span class="live-dot-pulse"></span>
              <span class="live-text">В ЭФИРЕ</span>
            </div>
            <div v-else class="idle-status-pill">
              <span class="idle-dot"></span>
              <span>НЕ ПОДКЛЮЧЕН</span>
            </div>
          </div>

          <h1 class="dj-room-name">
            <span class="guild-title-text">{{ discordStore.guildName ? `${discordStore.guildName}` : 'Тусовка в Discord' }}</span>
            <span v-if="discordStore.channelName" class="channel-hash">#{{ discordStore.channelName }}</span>
          </h1>
        </div>
      </div>

      <!-- Header Center: DJ Status Badges -->
      <div v-if="discordStore.hasParty" class="dj-header-center">
        <!-- Current DJ Pill -->
        <div 
          v-if="discordStore.hostUser" 
          class="dj-host-badge neu-card-sm"
          :title="discordStore.isHost ? 'Вы — текущий DJ тусовки' : `DJ: ${discordStore.hostUser.display_name}`"
        >
          <Crown :size="15" class="crown-icon" />
          <span class="dj-host-label">DJ:</span>
          <span class="dj-host-name">{{ discordStore.hostUser.display_name }}</span>
          <span v-if="discordStore.isHost" class="you-chip">ВЫ</span>
        </div>

        <!-- DJ Lock Mode Toggle -->
        <button
          class="dj-lock-toggle neu-btn-toggle"
          :class="{ active: discordStore.djLock, disabled: !discordStore.isHost }"
          :disabled="!discordStore.isHost"
          @click="toggleDjLock"
          :title="discordStore.isHost 
            ? (discordStore.djLock ? 'DJ Lock ВКЛ: Только вы управляете треками' : 'DJ Lock ВЫКЛ: Все участники могут управлять') 
            : (discordStore.djLock ? 'Только DJ может управлять воспроизведением' : 'Все участники могут управлять')"
        >
          <Lock v-if="discordStore.djLock" :size="14" />
          <Unlock v-else :size="14" />
          <span>{{ discordStore.djLock ? 'DJ Lock' : 'Общий доступ' }}</span>
        </button>

        <!-- Listen Along in Browser Toggle -->
        <button
          class="listen-along-toggle neu-btn-toggle"
          :class="{ active: discordStore.listenAlong }"
          @click="discordStore.toggleListenAlong"
          title="Слушать синхронно прямо в веб-плеере этого браузера"
        >
          <Headphones :size="14" />
          <span>{{ discordStore.listenAlong ? 'В браузере ВКЛ' : 'В браузере ВЫКЛ' }}</span>
        </button>
      </div>

      <!-- Header Right: Disconnect / Voice Indicator -->
      <div class="dj-header-right">
        <div v-if="discordStore.isUserInVoice" class="in-voice-pill">
          <span class="voice-wave-dot"></span>
          <span>В голосовом канале</span>
        </div>

        <button 
          v-if="discordStore.hasParty" 
          class="neu-btn-danger disconnect-btn" 
          @click="handleDisconnect"
          title="Отключить бота от голосового канала"
        >
          <Power :size="16" />
          <span class="btn-text">Отключить</span>
        </button>

        <button 
          v-else-if="discordStore.detectedUserChannel" 
          class="neu-btn-primary connect-quick-btn"
          @click="handleSummonBot"
          title="Подключить бота к вашему каналу"
        >
          <Radio :size="16" />
          <span>Подключить бота</span>
        </button>
      </div>
    </header>

    <!-- Mobile Segmented Tabs Switcher (Only on screens < 768px when party active) -->
    <div v-if="isMobile && discordStore.hasParty" class="dj-mobile-tabs neu-card-sm">
      <button 
        class="mobile-tab-btn" 
        :class="{ active: activeMobileTab === 'deck' }" 
        @click="activeMobileTab = 'deck'"
      >
        <Disc :size="16" />
        <span>Пульт</span>
      </button>
      <button 
        class="mobile-tab-btn" 
        :class="{ active: activeMobileTab === 'queue' }" 
        @click="activeMobileTab = 'queue'"
      >
        <ListMusic :size="16" />
        <span>Очередь ({{ discordStore.queue.length }})</span>
      </button>
      <button 
        class="mobile-tab-btn" 
        :class="{ active: activeMobileTab === 'members' }" 
        @click="activeMobileTab = 'members'"
      >
        <Users :size="16" />
        <span>В канале ({{ discordStore.activePartyMembers.length }})</span>
      </button>
    </div>

    <!-- ═════════════════════════════════════════════════════════════
         MAIN BODY CONTENT
         ═════════════════════════════════════════════════════════════ -->
    <div v-if="discordStore.hasParty" class="dj-content-layout">
      <!-- ─── LEFT COLUMN: MASTER DJ DECK ─── -->
      <section v-show="!isMobile || activeMobileTab === 'deck'" class="dj-deck-column">
        <div class="master-deck-card neu-panel">
          <div class="deck-top-label">
            <span class="lcd-led-tag">DECK A • MASTER OUTPUT</span>
            <div class="format-badge">48kHz • STEREO OPUS</div>
          </div>

          <!-- Vinyl / Cover Display Deck -->
          <div class="vinyl-display-wrapper">
            <div class="vinyl-record" :class="{ spinning: discordStore.isPlaying }">
              <div class="vinyl-groove-ring ring-1"></div>
              <div class="vinyl-groove-ring ring-2"></div>
              <div class="vinyl-groove-ring ring-3"></div>
              <div class="vinyl-center-hole"></div>
            </div>

            <div class="cover-art-box neu-inset-well">
              <img 
                v-if="currentTrackCover" 
                :src="currentTrackCover" 
                alt="Track Cover" 
                class="cover-art-img"
              />
              <div v-else class="cover-fallback">
                <Disc :size="54" />
              </div>

              <!-- Animated Equalizer Overlay when playing -->
              <div v-if="discordStore.isPlaying" class="deck-eq-bars">
                <span v-for="n in 5" :key="n" class="deck-eq-bar" :style="{ animationDelay: `${n * 0.12}s` }"></span>
              </div>
            </div>
          </div>

          <!-- Track Metadata -->
          <div class="deck-track-info">
            <div class="track-title-text" :title="discordStore.currentTrack?.title">
              {{ discordStore.currentTrack?.title || 'Очередь воспроизведения пуста' }}
            </div>
            <div class="track-artist-text">
              {{ discordStore.currentTrack?.artist || 'Добавьте треки в очередь справа' }}
            </div>

            <div v-if="discordStore.currentTrack?.added_by" class="added-by-pill">
              <span class="user-icon">👤</span>
              <span>Добавил(а): <strong>{{ discordStore.currentTrack.added_by.display_name || discordStore.currentTrack.added_by.username }}</strong></span>
            </div>
          </div>

          <!-- VFD / LCD Segment Status Display -->
          <div class="deck-lcd-screen neu-inset-panel">
            <div class="lcd-top-row">
              <span class="lcd-status-flag" :class="{ 'mode-play': discordStore.isPlaying, 'mode-pause': discordStore.isPaused }">
                {{ discordStore.isPlaying ? '▶ PLAYING' : discordStore.isPaused ? '❚❚ PAUSED' : '■ STOPPED' }}
              </span>
              <span class="lcd-volume-flag">VOL {{ discordStore.volume }}%</span>
              <span class="lcd-track-num">TRACK {{ (discordStore.queueIndex + 1) || 1 }}/{{ discordStore.queue.length || 1 }}</span>
            </div>

            <!-- Time Display -->
            <div class="lcd-time-display">
              <span class="lcd-time-main">{{ formatTime(discordStore.position) }}</span>
              <span class="lcd-time-sep">/</span>
              <span class="lcd-time-total">{{ formatTime(discordStore.duration) }}</span>
            </div>

            <!-- Animated VU Meter -->
            <div class="lcd-vu-meter">
              <div 
                v-for="bar in 24" 
                :key="bar" 
                class="vu-bar" 
                :class="{ 
                  lit: discordStore.isPlaying && isVuBarLit(bar),
                  peak: bar > 19 
                }"
              ></div>
            </div>
          </div>

          <!-- Neumorphic Seek Slider -->
          <div class="deck-progress-container">
            <div class="progress-labels">
              <span>{{ formatTime(currentDisplayPosition) }}</span>
              <span class="remaining-text">-{{ formatTime(Math.max(0, (discordStore.duration || 0) - currentDisplayPosition)) }}</span>
            </div>
            <input 
              type="range"
              class="neu-slider deck-seek-slider"
              :value="currentDisplayPosition"
              :min="0"
              :max="discordStore.duration || 100"
              :disabled="!discordStore.canControl"
              :style="{ '--slider-pct': `${seekProgressPercent}%` }"
              @input="handleSeekInput"
              @change="handleSeekChange"
            />
          </div>

          <!-- Primary Tactile Controls (Rubber Neumorphic Buttons) -->
          <div class="deck-controls-row">
            <!-- Replay / Prev -->
            <button 
              class="neu-btn-rubber control-btn"
              :disabled="!discordStore.canControl"
              @click="handleRestartOrPrev"
              title="В начало / Предыдущий трек"
            >
              <SkipBack :size="20" />
            </button>

            <!-- Big Master Play/Pause Button -->
            <button 
              class="neu-btn-rubber master-play-btn"
              :class="{ playing: discordStore.isPlaying }"
              :disabled="!discordStore.canControl"
              @click="togglePlayPause"
              title="Воспроизведение / Пауза"
            >
              <Pause v-if="discordStore.isPlaying" :size="28" fill="currentColor" />
              <Play v-else :size="28" fill="currentColor" />
            </button>

            <!-- Skip to Next -->
            <button 
              class="neu-btn-rubber control-btn"
              :disabled="!discordStore.canControl"
              @click="handleSkip"
              title="Следующий трек"
            >
              <SkipForward :size="20" />
            </button>

            <!-- Stop Button -->
            <button 
              class="neu-btn-rubber control-btn stop-btn"
              :disabled="!discordStore.canControl"
              @click="handleStop"
              title="Остановить воспроизведение"
            >
              <Square :size="18" fill="currentColor" />
            </button>
          </div>

          <!-- Volume Fader Row -->
          <div class="deck-volume-box neu-inset-well">
            <button class="vol-btn" @click="toggleMute" title="Громкость">
              <VolumeX v-if="discordStore.volume === 0" :size="18" />
              <Volume1 v-else-if="discordStore.volume < 50" :size="18" />
              <Volume2 v-else :size="18" />
            </button>
            <input 
              type="range" 
              class="neu-slider volume-slider"
              :value="discordStore.volume"
              min="0"
              max="100"
              :style="{ '--slider-pct': `${discordStore.volume}%` }"
              @input="discordStore.setVolume(Number($event.target.value))"
            />
            <span class="vol-percent">{{ discordStore.volume }}%</span>
          </div>
        </div>

        <!-- Voice Channel Members Card (Desktop view in left column) -->
        <div v-if="!isMobile" class="voice-members-card neu-panel">
          <div class="section-header">
            <div class="header-left-title">
              <Users :size="16" />
              <span>В канале ({{ discordStore.activePartyMembers.length }})</span>
            </div>
            <span class="sub-hint">Участники голосового канала</span>
          </div>

          <div class="members-grid">
            <div 
              v-for="member in discordStore.activePartyMembers" 
              :key="member.id"
              class="member-badge-card neu-card-sm"
              :class="{ 'is-dj': isMemberDJ(member) }"
            >
              <div class="member-avatar-box">
                <img v-if="member.avatar_url" :src="member.avatar_url" alt="" class="member-avatar-img" />
                <div v-else class="member-avatar-fallback">{{ member.display_name?.charAt(0) || '?' }}</div>
                <span v-if="isMemberDJ(member)" class="dj-crown-badge-mini" title="DJ">
                  <Crown :size="10" />
                </span>
              </div>

              <div class="member-info-col">
                <span class="member-display-name">{{ member.display_name }}</span>
                <span class="member-voice-sub">
                  <span v-if="member.is_deaf" class="warn-text">Глухой</span>
                  <span v-else-if="member.is_muted" class="muted-text">Микрофон выкл.</span>
                  <span v-else class="live-text">Слушает</span>
                </span>
              </div>

              <button 
                v-if="discordStore.isHost && !isMemberDJ(member)"
                class="make-dj-btn"
                @click="handleTransferDj(member.id)"
                title="Сделать этого пользователя DJ"
              >
                <Crown :size="13" />
                <span>DJ</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- ─── RIGHT COLUMN: COLLABORATIVE QUEUE & SEARCH ─── -->
      <section v-show="!isMobile || activeMobileTab === 'queue'" class="dj-queue-column">
        <div class="queue-manager-card neu-panel">
          <!-- Queue Top Header & Actions -->
          <div class="queue-header-row">
            <div class="queue-title-area">
              <div class="title-with-icon">
                <ListMusic :size="18" />
                <h2>Очередь воспроизведения</h2>
              </div>
              <span class="queue-stat-pill">
                {{ discordStore.queue.length }} {{ getTrackWord(discordStore.queue.length) }} • {{ totalQueueDurationFormatted }}
              </span>
            </div>

            <!-- Queue Quick Action Buttons -->
            <div class="queue-actions-area">
              <button 
                class="neu-btn-action" 
                :class="{ active: showQuickSearch }"
                @click="showQuickSearch = !showQuickSearch"
                title="Быстрый поиск и добавление трека в очередь"
              >
                <Plus :size="15" />
                <span>{{ showQuickSearch ? 'Скрыть поиск' : 'Добавить трек' }}</span>
              </button>

              <button 
                class="neu-btn-action"
                :disabled="!discordStore.canControl || discordStore.queue.length < 2"
                @click="handleShuffleQueue"
                title="Перемешать предстоящие треки в очереди"
              >
                <Shuffle :size="15" />
                <span>Перемешать</span>
              </button>

              <button 
                class="neu-btn-action danger"
                :disabled="!discordStore.canControl || discordStore.queue.length === 0"
                @click="handleClearQueue"
                title="Очистить очередь"
              >
                <Trash2 :size="15" />
                <span>Очистить</span>
              </button>
            </div>
          </div>

          <!-- Embedded Quick Track Search Dock -->
          <Transition name="expand">
            <div v-if="showQuickSearch" class="quick-search-dock neu-inset-well">
              <div class="search-input-wrapper">
                <Search :size="16" class="search-icon-left" />
                <input 
                  type="text" 
                  v-model="searchQuery" 
                  placeholder="Найти трек в медиатеке или по названию..." 
                  class="search-text-input"
                  @input="handleSearchInput"
                />
                <button v-if="searchQuery" class="clear-search-btn" @click="searchQuery = ''; searchResults = []">
                  ✕
                </button>
              </div>

              <!-- Search Results List -->
              <div v-if="isSearching" class="search-loading-hint">
                <div class="mini-spinner"></div>
                <span>Поиск треков...</span>
              </div>
              <div v-else-if="searchResults.length > 0" class="search-results-list">
                <div 
                  v-for="track in searchResults" 
                  :key="track.id" 
                  class="search-result-item neu-card-sm"
                >
                  <img 
                    v-if="getCover(track)" 
                    :src="getCover(track)" 
                    class="search-cover" 
                    alt="" 
                  />
                  <div v-else class="search-cover-fallback">
                    <Disc :size="18" />
                  </div>

                  <div class="search-meta">
                    <div class="result-title">{{ track.title }}</div>
                    <div class="result-artist">{{ track.artist }}</div>
                  </div>

                  <span class="result-duration">{{ formatTime(track.duration) }}</span>

                  <button 
                    class="add-to-queue-btn neu-btn-primary" 
                    :class="{ added: addedTrackIds.has(track.id) }"
                    :disabled="addedTrackIds.has(track.id)"
                    @click="addTrackToParty(track)"
                  >
                    <Check v-if="addedTrackIds.has(track.id)" :size="14" />
                    <Plus v-else :size="14" />
                    <span>{{ addedTrackIds.has(track.id) ? 'В очереди' : '+ В очередь' }}</span>
                  </button>
                </div>
              </div>
              <div v-else-if="searchQuery.trim().length >= 2" class="empty-search-hint">
                Ничего не найдено по запросу «{{ searchQuery }}»
              </div>
              <div v-else class="search-prompt-hint">
                Введите название трека или имя исполнителя для добавления в тусовку
              </div>
            </div>
          </Transition>

          <!-- ─── QUEUE LIST ─── -->
          <div class="queue-list-container">
            <div v-if="discordStore.queue.length === 0" class="empty-queue-box">
              <div class="empty-icon-circle neu-inset-well">
                <ListMusic :size="32" />
              </div>
              <h3>Очередь воспроизведения пуста</h3>
              <p>Нажмите кнопку <strong>«+ Добавить трек»</strong> выше или добавьте треки через контекстное меню из любого плейлиста или поиска!</p>
              <button class="neu-btn-primary empty-action-btn" @click="showQuickSearch = true">
                <Plus :size="16" />
                <span>Добавить первый трек</span>
              </button>
            </div>

            <div v-else class="queue-tracks-scroll">
              <div 
                v-for="(item, idx) in discordStore.queue" 
                :key="item.id ? `${item.id}-${idx}` : idx"
                class="queue-track-card neu-card"
                :class="{ 
                  'is-playing': idx === discordStore.queueIndex,
                  'is-dragging': draggedIndex === idx
                }"
                draggable="true"
                @dragstart="onDragStart(idx, $event)"
                @dragover.prevent="onDragOver(idx, $event)"
                @drop="onDrop(idx, $event)"
                @dragend="onDragEnd"
              >
                <!-- Drag Handle -->
                <div class="drag-handle" title="Перетащите для изменения порядка">
                  <GripVertical :size="16" />
                </div>

                <!-- Position or Playing Indicator -->
                <div class="queue-pos-indicator">
                  <div v-if="idx === discordStore.queueIndex && discordStore.isPlaying" class="mini-playing-eq">
                    <span class="eq-b b1"></span>
                    <span class="eq-b b2"></span>
                    <span class="eq-b b3"></span>
                  </div>
                  <span v-else class="pos-num">{{ idx + 1 }}</span>
                </div>

                <!-- Track Cover -->
                <div class="queue-track-cover">
                  <img 
                    v-if="getCover(item)" 
                    :src="getCover(item)" 
                    alt="" 
                    class="q-cover-img" 
                  />
                  <div v-else class="q-cover-fallback">
                    <Disc :size="18" />
                  </div>
                </div>

                <!-- Title & Artist -->
                <div class="queue-track-meta">
                  <div class="q-title-row">
                    <span class="q-title">{{ item.title }}</span>
                    <span v-if="idx === discordStore.queueIndex" class="now-badge">ИГРАЕТ</span>
                  </div>
                  <div class="q-sub-row">
                    <span class="q-artist">{{ item.artist }}</span>
                    <span v-if="item.added_by" class="q-added-badge">
                      👤 {{ item.added_by.display_name || item.added_by.username }}
                    </span>
                  </div>
                </div>

                <!-- Duration -->
                <span class="q-duration">{{ formatTime(item.duration) }}</span>

                <!-- Action Controls -->
                <div class="queue-item-actions">
                  <!-- Play Now (Cueing) -->
                  <button 
                    v-if="idx !== discordStore.queueIndex"
                    class="q-btn play-cue-btn"
                    :disabled="!discordStore.canControl"
                    @click="handlePlayQueueIndex(idx)"
                    title="Включить этот трек прямо сейчас"
                  >
                    <Play :size="14" fill="currentColor" />
                  </button>

                  <!-- Reorder Up -->
                  <button 
                    class="q-btn move-up-btn"
                    :disabled="!discordStore.canControl || idx === 0"
                    @click="handleMoveQueue(idx, idx - 1)"
                    title="Переместить выше"
                  >
                    <ChevronUp :size="15" />
                  </button>

                  <!-- Reorder Down -->
                  <button 
                    class="q-btn move-down-btn"
                    :disabled="!discordStore.canControl || idx === discordStore.queue.length - 1"
                    @click="handleMoveQueue(idx, idx + 1)"
                    title="Переместить ниже"
                  >
                    <ChevronDown :size="15" />
                  </button>

                  <!-- Remove -->
                  <button 
                    v-if="canRemoveTrack(item)"
                    class="q-btn remove-btn"
                    @click="handleRemoveQueue(idx)"
                    title="Удалить из очереди"
                  >
                    <Trash2 :size="14" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ─── MOBILE: MEMBERS COLUMN (Active when isMobile && activeMobileTab === 'members') ─── -->
      <section v-if="isMobile && activeMobileTab === 'members'" class="dj-mobile-members-column">
        <div class="voice-members-card neu-panel">
          <div class="section-header">
            <div class="header-left-title">
              <Users :size="16" />
              <span>В канале ({{ discordStore.activePartyMembers.length }})</span>
            </div>
            <span class="sub-hint">Участники голосового канала</span>
          </div>

          <div class="members-grid">
            <div 
              v-for="member in discordStore.activePartyMembers" 
              :key="member.id"
              class="member-badge-card neu-card-sm"
              :class="{ 'is-dj': isMemberDJ(member) }"
            >
              <div class="member-avatar-box">
                <img v-if="member.avatar_url" :src="member.avatar_url" alt="" class="member-avatar-img" />
                <div v-else class="member-avatar-fallback">{{ member.display_name?.charAt(0) || '?' }}</div>
                <span v-if="isMemberDJ(member)" class="dj-crown-badge-mini" title="DJ">
                  <Crown :size="10" />
                </span>
              </div>

              <div class="member-info-col">
                <span class="member-display-name">{{ member.display_name }}</span>
                <span class="member-voice-sub">
                  <span v-if="member.is_deaf" class="warn-text">Глухой</span>
                  <span v-else-if="member.is_muted" class="muted-text">Микрофон выкл.</span>
                  <span v-else class="live-text">Слушает</span>
                </span>
              </div>

              <button 
                v-if="discordStore.isHost && !isMemberDJ(member)"
                class="make-dj-btn"
                @click="handleTransferDj(member.id)"
                title="Сделать этого пользователя DJ"
              >
                <Crown :size="13" />
                <span>DJ</span>
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- ═════════════════════════════════════════════════════════════
         NO PARTY / CONNECT FLOW STATE (If bot is not yet in voice)
         ═════════════════════════════════════════════════════════════ -->
    <div v-else class="no-party-landing-container">
      <div class="no-party-card neu-panel">
        <div class="no-party-icon-circle neu-inset-well">
          <Radio :size="48" class="neon-icon" />
        </div>

        <h2>Запуск музыки в Discord</h2>
        <p class="no-party-desc">
          Транслируйте музыку прямо в голосовой канал вашего Discord сервера в высоком качестве без задержек.
        </p>

        <!-- Detected User Voice Channel Magic Card -->
        <div v-if="discordStore.detectedUserChannel" class="detected-channel-card neu-card">
          <div class="detected-top">
            <span class="live-dot-pulse"></span>
            <span class="detected-badge">ОБНАРУЖЕН ГОЛОСОВОЙ КАНАЛ</span>
          </div>
          <div class="detected-body">
            <div class="channel-title">
              #{{ discordStore.detectedUserChannel.channel_name }}
              <span class="guild-sub">({{ discordStore.detectedUserChannel.guild_name }})</span>
            </div>
            <p class="detected-info">Вы прямо сейчас находитесь в этом канале! Нажмите кнопку, чтобы позвать бота.</p>
            <button class="neu-btn-primary magic-connect-btn" @click="handleSummonBot">
              <Radio :size="18" />
              <span>Запустить музыку в мой канал</span>
            </button>
          </div>
        </div>

        <!-- Available Channels Selector -->
        <div class="channels-section">
          <h3>Или выберите канал вручную:</h3>

          <div v-if="discordStore.availableChannels.length > 0" class="servers-channels-list">
            <div 
              v-for="guild in discordStore.availableChannels" 
              :key="guild.guild_id" 
              class="guild-channels-group neu-card-sm"
            >
              <div class="guild-group-header">
                <img v-if="guild.guild_icon" :src="guild.guild_icon" class="guild-icon-small" alt="" />
                <span class="guild-name-text">{{ guild.guild_name }}</span>
              </div>

              <div class="channels-chips-grid">
                <button 
                  v-for="ch in guild.channels" 
                  :key="ch.id"
                  class="channel-chip-btn neu-btn-rubber"
                  @click="handleConnect(ch.id)"
                >
                  <Volume2 :size="14" />
                  <span>{{ ch.name }}</span>
                  <span v-if="ch.user_count > 0" class="ch-count-badge">{{ ch.user_count }} 👤</span>
                </button>
              </div>
            </div>
          </div>

          <div v-else class="empty-channels-note">
            <p>Бот пока не подключен к серверам или у него нет прав на просмотр голосовых каналов.</p>
          </div>

          <!-- Bot Invite Link -->
          <div v-if="discordStore.inviteUrl" class="bot-invite-footer">
            <a :href="discordStore.inviteUrl" target="_blank" class="neu-invite-btn">
              <ExternalLink :size="15" />
              <span>Пригласить бота на свой Discord сервер</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  Disc, Crown, Play, Pause, SkipForward, SkipBack, Square,
  Volume2, Volume1, VolumeX, Lock, Unlock, Headphones, Users,
  ListMusic, Trash2, Power, ExternalLink, Shuffle, Plus, Search,
  GripVertical, ChevronUp, ChevronDown, Check, Radio, ArrowLeft
} from 'lucide-vue-next'
import { useDiscordStore } from '@/stores/discord'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import { tracksApi } from '@/api'

const router = useRouter()
const discordStore = useDiscordStore()
const authStore = useAuthStore()
const playerStore = usePlayerStore()

// Mobile adaptation
const isMobile = ref(typeof window !== 'undefined' ? window.innerWidth < 768 : false)
const activeMobileTab = ref('deck') // 'deck' | 'queue' | 'members'

function updateMobileState() {
  isMobile.value = window.innerWidth < 768
}

// Dragging seek state (prevents seek flood and smooths slider UI)
const isDraggingSeek = ref(false)
const seekDragValue = ref(0)

const currentDisplayPosition = computed(() => {
  if (isDraggingSeek.value) {
    return seekDragValue.value
  }
  return discordStore.position
})

const seekProgressPercent = computed(() => {
  const dur = discordStore.duration || 1
  const pos = currentDisplayPosition.value
  return Math.min(100, Math.max(0, (pos / dur) * 100))
})

function handleSeekInput(e) {
  isDraggingSeek.value = true
  seekDragValue.value = Number(e.target.value)
}

async function handleSeekChange(e) {
  const targetPos = Number(e.target.value)
  isDraggingSeek.value = false
  await discordStore.seek(targetPos)
}

// Search in queue dock
const showQuickSearch = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const isSearching = ref(false)
const addedTrackIds = ref(new Set())
let searchDebounce = null

// Drag & drop reordering
const draggedIndex = ref(null)

onMounted(async () => {
  updateMobileState()
  window.addEventListener('resize', updateMobileState)
  await discordStore.fetchParty()
  await discordStore.fetchUserState()
  if (discordStore.availableChannels.length === 0) {
    discordStore.fetchAvailableChannels()
  }
  if (!discordStore.inviteUrl) {
    discordStore.fetchInvite()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', updateMobileState)
  if (searchDebounce) clearTimeout(searchDebounce)
})

function handleGoBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}

// Track cover URL resolution
const currentTrackCover = computed(() => {
  const track = discordStore.currentTrack
  return getCover(track)
})

function getCover(track) {
  if (!track || !track.cover_url) return null
  if (track.cover_url.startsWith('http') || track.cover_url.startsWith('/api')) {
    return track.cover_url
  }
  return `/api/images/${track.cover_url}`
}

function formatTime(seconds) {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function getTrackWord(count) {
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod100 >= 11 && mod100 <= 19) return 'треков'
  if (mod10 === 1) return 'трек'
  if (mod10 >= 2 && mod10 <= 4) return 'трека'
  return 'треков'
}

const totalQueueDurationFormatted = computed(() => {
  const total = discordStore.queue.reduce((acc, t) => acc + (t.duration || 0), 0)
  return formatTime(total)
})

function isMemberDJ(member) {
  if (!discordStore.hostUser) return false
  return discordStore.hostUser.id === member.id || 
         discordStore.hostUser.discord_id === member.id ||
         discordStore.hostUser.id === String(member.id)
}

function canRemoveTrack(item) {
  if (discordStore.isHost) return true
  const currentUserId = authStore.user?.id
  return item.added_by && item.added_by.id === currentUserId
}

// VU Meter simulation
function isVuBarLit(barNumber) {
  const pos = Math.floor(discordStore.position * 4) + barNumber
  return (pos % 5 !== 0 && pos % 7 !== 0) || barNumber <= 6
}

// Playback actions
function togglePlayPause() {
  if (discordStore.isPlaying) {
    discordStore.pause()
  } else {
    discordStore.resume()
  }
}

function handleRestartOrPrev() {
  if (discordStore.position > 3) {
    discordStore.seek(0)
  } else if (discordStore.queueIndex > 0) {
    discordStore.playQueueIndex(discordStore.queueIndex - 1)
  } else {
    discordStore.seek(0)
  }
}

function handleSkip() {
  discordStore.skip()
}

function handleStop() {
  discordStore.stop()
}

function handleSeek(pos) {
  discordStore.seek(pos)
}

let lastVolume = 100
function toggleMute() {
  if (discordStore.volume > 0) {
    lastVolume = discordStore.volume
    discordStore.setVolume(0)
  } else {
    discordStore.setVolume(lastVolume || 100)
  }
}

function toggleDjLock() {
  discordStore.setDjLock(!discordStore.djLock)
}

function handleTransferDj(memberId) {
  if (confirm('Передать роль главного DJ этому участнику?')) {
    discordStore.transferDj(memberId)
  }
}

async function handleDisconnect() {
  if (confirm('Отключить бота от голосового канала? Музыка остановится для всех.')) {
    await discordStore.disconnect()
  }
}

async function handleConnect(channelId) {
  await discordStore.connectToChannel(channelId)
}

async function handleSummonBot() {
  const ch = discordStore.detectedUserChannel
  if (!ch) return
  await discordStore.connectToChannel(ch.channel_id)
}

// Queue operations
async function handlePlayQueueIndex(index) {
  await discordStore.playQueueIndex(index)
}

async function handleMoveQueue(fromIdx, toIdx) {
  if (toIdx < 0 || toIdx >= discordStore.queue.length) return
  await discordStore.moveQueueTrack(fromIdx, toIdx)
}

async function handleRemoveQueue(index) {
  await discordStore.removeFromQueue(index)
}

async function handleClearQueue() {
  if (confirm('Очистить предстоящую очередь треков?')) {
    await discordStore.clearQueue(true)
  }
}

async function handleShuffleQueue() {
  await discordStore.shuffleQueue()
}

// Drag and drop reordering
function onDragStart(index, e) {
  draggedIndex.value = index
  e.dataTransfer.effectAllowed = 'move'
}

function onDragOver(index, e) {
  e.dataTransfer.dropEffect = 'move'
}

async function onDrop(targetIndex, e) {
  const fromIndex = draggedIndex.value
  draggedIndex.value = null
  if (fromIndex !== null && fromIndex !== targetIndex) {
    await discordStore.moveQueueTrack(fromIndex, targetIndex)
  }
}

function onDragEnd() {
  draggedIndex.value = null
}

// Search and add to queue
function handleSearchInput() {
  if (searchDebounce) clearTimeout(searchDebounce)
  const q = searchQuery.value.trim()
  if (q.length < 2) {
    searchResults.value = []
    isSearching.value = false
    return
  }
  isSearching.value = true
  searchDebounce = setTimeout(async () => {
    try {
      const res = await tracksApi.getAll({ search: q, limit: 15 })
      searchResults.value = res.data?.items || res.data || []
    } catch (e) {
      console.error('Track search error:', e)
    } finally {
      isSearching.value = false
    }
  }, 300)
}

async function addTrackToParty(track) {
  try {
    await discordStore.addToQueue(track)
    addedTrackIds.value.add(track.id)
    setTimeout(() => {
      addedTrackIds.value.delete(track.id)
    }, 2500)
  } catch (e) {
    console.error('Failed to add track to Discord queue:', e)
  }
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════════════
   DARK NEUMORPHISM (Hi-Fi Soft UI / Nokia XpressMusic)
   ═══════════════════════════════════════════════════════════════════ */

.dj-view-container {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4, 16px);
  padding: var(--sp-4, 16px);
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100%;
  padding-bottom: calc(var(--player-height, 64px) + 80px + env(safe-area-inset-bottom, 16px));
  color: var(--c-text-1, #ffffff);
}

/* ─── Neumorphic Panels & Cards ─── */
.neu-panel {
  background: var(--c-bg-2, #1A1A1A);
  border-radius: var(--r-lg, 16px);
  border: 1px solid rgba(255, 255, 255, 0.035);
  box-shadow: 6px 6px 14px var(--sh-dark, rgba(0, 0, 0, 0.72)),
             -3px -3px 8px var(--sh-light, rgba(255, 255, 255, 0.055));
}

.neu-card {
  background: var(--c-bg-2, #1A1A1A);
  border-radius: var(--r-md, 12px);
  border: 1px solid rgba(255, 255, 255, 0.03);
  box-shadow: 4px 4px 10px var(--sh-dark, rgba(0, 0, 0, 0.6)),
             -2px -2px 6px var(--sh-light, rgba(255, 255, 255, 0.04));
  transition: all 0.15s ease;
}

.neu-card-sm {
  background: var(--c-bg-3, #222222);
  border-radius: var(--r-sm, 8px);
  border: 1px solid rgba(255, 255, 255, 0.025);
  box-shadow: 3px 3px 6px var(--sh-dark, rgba(0, 0, 0, 0.5)),
             -2px -2px 5px var(--sh-light, rgba(255, 255, 255, 0.03));
}

.neu-inset-well {
  background: var(--c-bg-1, #121212);
  border-radius: var(--r-md, 12px);
  border: 1px solid rgba(0, 0, 0, 0.45);
  box-shadow: inset 3px 3px 6px var(--sh-inset-dark, rgba(0, 0, 0, 0.78)),
              inset -2px -2px 4px var(--sh-inset-light, rgba(255, 255, 255, 0.045));
}

.neu-inset-panel {
  background: var(--c-bg-0, #0D0D0D);
  border-radius: var(--r-sm, 8px);
  border: 1px solid rgba(0, 0, 0, 0.6);
  box-shadow: inset 4px 4px 8px rgba(0, 0, 0, 0.85),
              inset -2px -2px 4px rgba(255, 255, 255, 0.03);
}

/* ─── Buttons ─── */
.neu-btn-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--r-full, 9999px);
  background: var(--c-bg-3, #222222);
  border: 1px solid rgba(255, 255, 255, 0.04);
  color: var(--c-text-1, #fff);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 3px 3px 7px var(--sh-dark), -2px -2px 5px var(--sh-light);
  cursor: pointer;
  transition: all 0.15s ease;
}

.neu-btn-icon:active {
  transform: scale(0.95);
  box-shadow: inset 2px 2px 5px var(--sh-inset-dark);
}

.neu-btn-rubber {
  background: var(--rubber-bg, linear-gradient(180deg, #3a3a3a 0%, #252525 50%, #1a1a1a 100%));
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: var(--r-md, 12px);
  color: var(--c-text-1, #fff);
  box-shadow: 4px 4px 8px var(--sh-dark), -2px -2px 5px var(--sh-light);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.neu-btn-rubber:hover:not(:disabled) {
  filter: brightness(1.1);
}

.neu-btn-rubber:active:not(:disabled) {
  transform: scale(0.96);
  background: var(--rubber-pressed, linear-gradient(180deg, #2a2a2a 0%, #1a1a1a 50%, #151515 100%));
  box-shadow: inset 3px 3px 6px rgba(0, 0, 0, 0.8);
}

.neu-btn-rubber:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.neu-btn-primary {
  background: linear-gradient(135deg, var(--c-accent, #1db954) 0%, var(--c-accent-dark, #169c46) 100%);
  color: #000;
  font-weight: 700;
  border: none;
  border-radius: var(--r-md, 12px);
  padding: 8px 16px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  box-shadow: 3px 3px 8px var(--sh-dark), 0 0 14px var(--c-accent-glow, rgba(29, 185, 84, 0.4));
  transition: all 0.15s ease;
}

.neu-btn-primary:active {
  transform: scale(0.96);
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.5);
}

.neu-btn-danger {
  background: linear-gradient(180deg, #381c1c 0%, #251212 100%);
  border: 1px solid rgba(244, 67, 54, 0.3);
  color: #ff8585;
  border-radius: var(--r-md, 12px);
  padding: 8px 14px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  box-shadow: 3px 3px 6px var(--sh-dark);
  transition: all 0.15s ease;
}

.neu-btn-danger:hover {
  background: #421c1c;
  color: #ffaaaa;
}

.neu-btn-danger:active {
  transform: scale(0.96);
  box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.7);
}

.neu-btn-toggle {
  background: var(--c-bg-3, #222222);
  border: 1px solid rgba(255, 255, 255, 0.04);
  color: var(--c-text-2, #b3b3b3);
  border-radius: var(--r-md, 12px);
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  box-shadow: 3px 3px 6px var(--sh-dark), -2px -2px 4px var(--sh-light);
  transition: all 0.15s ease;
}

.neu-btn-toggle.active {
  background: var(--c-bg-4, #2A2A2A);
  color: var(--c-accent, #1db954);
  border-color: rgba(29, 185, 84, 0.3);
  box-shadow: inset 2px 2px 5px var(--sh-inset-dark), 0 0 10px rgba(29, 185, 84, 0.2);
}

.neu-btn-toggle.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.neu-btn-action {
  background: var(--c-bg-3, #222222);
  border: 1px solid rgba(255, 255, 255, 0.04);
  color: var(--c-text-1, #fff);
  border-radius: var(--r-md, 12px);
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  box-shadow: 3px 3px 6px var(--sh-dark), -2px -2px 4px var(--sh-light);
  transition: all 0.15s ease;
}

.neu-btn-action:hover:not(:disabled) {
  color: var(--c-accent, #1db954);
}

.neu-btn-action:active:not(:disabled) {
  transform: scale(0.96);
  box-shadow: inset 2px 2px 4px var(--sh-inset-dark);
}

.neu-btn-action.active {
  background: var(--c-bg-4, #2A2A2A);
  color: var(--c-accent, #1db954);
  box-shadow: inset 2px 2px 4px var(--sh-inset-dark);
}

.neu-btn-action.danger:hover:not(:disabled) {
  color: #ff7878;
}

.neu-btn-action:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ─── Sliders ─── */
.neu-slider {
  -webkit-appearance: none;
  width: 100%;
  height: 8px;
  background: linear-gradient(
    to right, 
    var(--c-accent, #1db954) 0%, 
    var(--c-accent, #1db954) var(--slider-pct, 0%), 
    var(--c-bg-0, #0D0D0D) var(--slider-pct, 0%), 
    var(--c-bg-0, #0D0D0D) 100%
  );
  border-radius: var(--r-full, 9999px);
  border: 1px solid rgba(0, 0, 0, 0.5);
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.8), inset -1px -1px 2px rgba(255, 255, 255, 0.03);
  outline: none;
  cursor: pointer;
}

.neu-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, var(--c-accent-light, #1ed760), var(--c-accent-dark, #169c46));
  box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.6), 0 0 8px var(--c-accent-glow, rgba(29, 185, 84, 0.4));
  border: 1px solid rgba(255, 255, 255, 0.4);
  cursor: pointer;
  transition: transform 0.1s ease;
}

.neu-slider::-webkit-slider-thumb:hover {
  transform: scale(1.18);
}

.neu-slider:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ═══════════════════════════════════════════════════════════════════
   TOP HEADER BAR
   ═══════════════════════════════════════════════════════════════════ */
.dj-header {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.dj-header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.dj-title-box {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dj-badge-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.discord-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(88, 101, 242, 0.18);
  color: #7983f5;
  border: 1px solid rgba(88, 101, 242, 0.3);
  border-radius: var(--r-full, 9999px);
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.live-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(29, 185, 84, 0.15);
  color: var(--c-accent, #1db954);
  border: 1px solid rgba(29, 185, 84, 0.3);
  border-radius: var(--r-full, 9999px);
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.05em;
}

.live-dot-pulse {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--c-accent, #1db954);
  box-shadow: 0 0 8px var(--c-accent);
  animation: pulse-green 1.5s infinite;
}

@keyframes pulse-green {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

.idle-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--c-text-3, #808080);
  border-radius: var(--r-full, 9999px);
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 700;
}

.idle-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #666;
}

.dj-room-name {
  font-size: 20px;
  font-weight: 800;
  margin: 0;
  letter-spacing: -0.01em;
}

.channel-hash {
  color: var(--c-accent, #1db954);
  font-weight: 700;
  margin-left: 6px;
}

.dj-header-center {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.dj-host-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 13px;
}

.crown-icon {
  color: #ffd700;
  filter: drop-shadow(0 0 5px rgba(255, 215, 0, 0.5));
}

.dj-host-label {
  color: var(--c-text-3, #808080);
  font-weight: 600;
}

.dj-host-name {
  color: var(--c-text-1, #fff);
  font-weight: 700;
}

.you-chip {
  background: var(--c-accent, #1db954);
  color: #000;
  font-size: 9px;
  font-weight: 900;
  padding: 2px 6px;
  border-radius: var(--r-xs, 4px);
  margin-left: 4px;
}

.dj-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.in-voice-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0, 188, 212, 0.12);
  color: var(--c-secondary, #00BCD4);
  border: 1px solid rgba(0, 188, 212, 0.25);
  border-radius: var(--r-full, 9999px);
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
}

.voice-wave-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--c-secondary, #00BCD4);
  box-shadow: 0 0 6px var(--c-secondary);
}

/* ═══════════════════════════════════════════════════════════════════
   MAIN 2-COLUMN LAYOUT
   ═══════════════════════════════════════════════════════════════════ */
.dj-content-layout {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 20px;
  align-items: start;
}

@media (max-width: 1024px) {
  .dj-content-layout {
    grid-template-columns: 1fr;
  }
}

/* ═══════════════════════════════════════════════════════════════════
   MOBILE TABS & RESPONSIVE BREAKPOINTS (< 768px)
   ═══════════════════════════════════════════════════════════════════ */
.dj-mobile-tabs {
  display: flex;
  align-items: center;
  padding: 4px;
  background: var(--c-bg-1, #121212);
  border-radius: var(--r-md, 12px);
  gap: 4px;
  box-shadow: inset 2px 2px 5px var(--sh-inset-dark, rgba(0, 0, 0, 0.7)),
              inset -1px -1px 3px var(--sh-inset-light, rgba(255, 255, 255, 0.04));
  border: 1px solid rgba(255, 255, 255, 0.03);
}

.mobile-tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 8px;
  border-radius: var(--r-sm, 8px);
  border: none;
  background: transparent;
  color: var(--c-text-3, #808080);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}

.mobile-tab-btn.active {
  background: var(--c-bg-3, #222222);
  color: var(--c-accent, #1db954);
  box-shadow: 3px 3px 7px var(--sh-dark, rgba(0, 0, 0, 0.6)),
             -2px -2px 5px var(--sh-light, rgba(255, 255, 255, 0.04)),
             0 0 10px var(--c-accent-glow, rgba(29, 185, 84, 0.25));
}

.dj-mobile-members-column {
  display: flex;
  flex-direction: column;
}



/* ═══════════════════════════════════════════════════════════════════
   LEFT COLUMN: MASTER DJ DECK
   ═══════════════════════════════════════════════════════════════════ */
.dj-deck-column {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.master-deck-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  background: linear-gradient(175deg, #1c1c1c 0%, #151515 100%);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.deck-top-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.lcd-led-tag {
  font-family: var(--font-mono, monospace);
  font-size: 11px;
  font-weight: 700;
  color: var(--c-accent, #1db954);
  letter-spacing: 0.1em;
}

.format-badge {
  font-family: var(--font-mono, monospace);
  font-size: 10px;
  color: var(--c-text-3, #808080);
  background: rgba(0, 0, 0, 0.4);
  padding: 2px 6px;
  border-radius: var(--r-xs, 4px);
}

/* ─── Vinyl Record & Artwork Deck ─── */
.vinyl-display-wrapper {
  position: relative;
  width: 220px;
  height: 220px;
  margin: 0 auto 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.vinyl-record {
  position: absolute;
  top: -8px;
  right: -24px;
  width: 210px;
  height: 210px;
  border-radius: 50%;
  background: radial-gradient(circle, #2a2a2a 0%, #111111 60%, #050505 100%);
  box-shadow: 4px 4px 14px rgba(0, 0, 0, 0.9), inset 0 0 20px rgba(0, 0, 0, 0.8);
  border: 2px solid #222;
  z-index: 1;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.vinyl-record.spinning {
  animation: spin-vinyl 12s linear infinite;
}

@keyframes spin-vinyl {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.vinyl-groove-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.ring-1 { top: 25px; left: 25px; right: 25px; bottom: 25px; }
.ring-2 { top: 50px; left: 50px; right: 50px; bottom: 50px; }
.ring-3 { top: 75px; left: 75px; right: 75px; bottom: 75px; }

.vinyl-center-hole {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #000;
  border: 2px solid rgba(255, 255, 255, 0.1);
}

.cover-art-box {
  position: relative;
  width: 180px;
  height: 180px;
  border-radius: var(--r-md, 12px);
  overflow: hidden;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 6px 6px 16px rgba(0, 0, 0, 0.8), -2px -2px 6px rgba(255, 255, 255, 0.04);
}

.cover-art-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-fallback {
  color: var(--c-text-3, #808080);
}

.deck-eq-bars {
  position: absolute;
  bottom: 8px;
  left: 8px;
  right: 8px;
  height: 24px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 4px;
  background: rgba(0, 0, 0, 0.5);
  border-radius: var(--r-sm, 8px);
  padding: 3px 6px;
  backdrop-filter: blur(4px);
}

.deck-eq-bar {
  flex: 1;
  background: var(--c-accent, #1db954);
  border-radius: 2px;
  animation: eq-bounce 0.8s ease-in-out infinite alternate;
}

@keyframes eq-bounce {
  0% { height: 3px; }
  100% { height: 18px; }
}

/* ─── Deck Track Info ─── */
.deck-track-info {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.track-title-text {
  font-size: 18px;
  font-weight: 800;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 360px;
}

.track-artist-text {
  font-size: 14px;
  color: var(--c-text-2, #b3b3b3);
}

.added-by-pill {
  margin-top: 6px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--c-bg-3, #222222);
  border: 1px solid rgba(255, 255, 255, 0.03);
  border-radius: var(--r-full, 9999px);
  padding: 4px 12px;
  font-size: 11px;
  color: var(--c-text-2, #b3b3b3);
}

.added-by-pill strong {
  color: var(--c-accent, #1db954);
}

/* ─── VFD / LCD Segment Screen ─── */
.deck-lcd-screen {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: var(--lcd-bg, linear-gradient(180deg, #0a1520 0%, #051015 100%));
  border: 1px solid rgba(77, 195, 255, 0.15);
}

.lcd-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-family: var(--font-mono, monospace);
  font-size: 10px;
  color: rgba(77, 195, 255, 0.6);
  letter-spacing: 0.08em;
}

.lcd-status-flag.mode-play {
  color: #1db954;
  text-shadow: 0 0 8px rgba(29, 185, 84, 0.6);
}

.lcd-status-flag.mode-pause {
  color: #ffa500;
  text-shadow: 0 0 8px rgba(255, 165, 0, 0.6);
}

.lcd-time-display {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 8px;
  font-family: var(--font-mono, monospace);
}

.lcd-time-main {
  font-size: 32px;
  font-weight: 800;
  color: var(--lcd-text, #4DC3FF);
  text-shadow: 0 0 12px var(--lcd-glow, rgba(77, 195, 255, 0.6));
  letter-spacing: 0.05em;
}

.lcd-time-sep {
  font-size: 20px;
  color: rgba(77, 195, 255, 0.4);
}

.lcd-time-total {
  font-size: 18px;
  font-weight: 600;
  color: rgba(77, 195, 255, 0.7);
}

.lcd-vu-meter {
  display: flex;
  align-items: center;
  gap: 3px;
  height: 10px;
}

.vu-bar {
  flex: 1;
  height: 100%;
  border-radius: 1px;
  background: rgba(77, 195, 255, 0.1);
  transition: background 0.1s ease;
}

.vu-bar.lit {
  background: #00CCFF;
  box-shadow: 0 0 4px #00CCFF;
}

.vu-bar.lit.peak {
  background: #FF5252;
  box-shadow: 0 0 4px #FF5252;
}

/* ─── Deck Progress / Seek ─── */
.deck-progress-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.progress-labels {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-family: var(--font-mono, monospace);
  font-size: 11px;
  color: var(--c-text-3, #808080);
}

/* ─── Controls Row ─── */
.deck-controls-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 6px 0;
}

.control-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
}

.master-play-btn {
  width: 68px;
  height: 68px;
  border-radius: 50%;
  color: #000;
  background: radial-gradient(circle at 35% 35%, var(--c-accent-light, #1ed760), var(--c-accent-dark, #169c46));
  box-shadow: 5px 5px 12px rgba(0, 0, 0, 0.7), -2px -2px 6px rgba(255, 255, 255, 0.15), 0 0 16px var(--c-accent-glow);
  border: 2px solid rgba(255, 255, 255, 0.25);
}

.master-play-btn:active:not(:disabled) {
  transform: scale(0.94);
  box-shadow: inset 3px 3px 6px rgba(0, 0, 0, 0.8);
}

.master-play-btn.playing {
  box-shadow: 5px 5px 12px rgba(0, 0, 0, 0.7), 0 0 22px var(--c-accent-glow);
}

.stop-btn {
  color: var(--c-text-2, #b3b3b3);
}

/* ─── Volume Fader ─── */
.deck-volume-box {
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.vol-btn {
  background: none;
  border: none;
  color: var(--c-text-2, #b3b3b3);
  cursor: pointer;
  display: flex;
  align-items: center;
}

.vol-percent {
  font-family: var(--font-mono, monospace);
  font-size: 12px;
  font-weight: 700;
  color: var(--c-text-2, #b3b3b3);
  min-width: 38px;
  text-align: right;
}

/* ─── Voice Members Card ─── */
.voice-members-card {
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
}

.sub-hint {
  font-size: 11px;
  color: var(--c-text-3, #808080);
}

.members-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.member-badge-card {
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.15s ease;
}

.member-badge-card.is-dj {
  border-color: rgba(255, 215, 0, 0.3);
  background: linear-gradient(90deg, rgba(255, 215, 0, 0.08) 0%, var(--c-bg-3) 100%);
}

.member-avatar-box {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--c-bg-1);
}

.member-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.member-avatar-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  color: var(--c-text-2);
}

.dj-crown-badge-mini {
  position: absolute;
  bottom: 0;
  right: 0;
  background: #000;
  color: #ffd700;
  border-radius: 50%;
  padding: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.member-info-col {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.member-display-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--c-text-1);
}

.member-voice-sub {
  font-size: 11px;
}

.warn-text { color: #f44336; }
.muted-text { color: #ff9800; }
.live-text { color: var(--c-accent, #1db954); }

.make-dj-btn {
  background: var(--c-bg-2, #1a1a1a);
  border: 1px solid rgba(255, 215, 0, 0.3);
  color: #ffd700;
  font-size: 11px;
  font-weight: 700;
  border-radius: var(--r-sm, 8px);
  padding: 4px 10px;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);
}

.make-dj-btn:hover {
  background: #2a2512;
}

/* ═══════════════════════════════════════════════════════════════════
   RIGHT COLUMN: QUEUE HUB & SEARCH
   ═══════════════════════════════════════════════════════════════════ */
.dj-queue-column {
  display: flex;
  flex-direction: column;
}

.queue-manager-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: 600px;
}

.queue-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.queue-title-area {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-with-icon h2 {
  font-size: 18px;
  font-weight: 800;
  margin: 0;
}

.queue-stat-pill {
  font-size: 12px;
  color: var(--c-text-3, #808080);
}

.queue-actions-area {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

/* ─── Embedded Quick Track Search Dock ─── */
.quick-search-dock {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon-left {
  position: absolute;
  left: 12px;
  color: var(--c-text-3, #808080);
}

.search-text-input {
  width: 100%;
  background: var(--c-bg-2, #1A1A1A);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--r-md, 12px);
  padding: 10px 38px;
  color: var(--c-text-1, #fff);
  font-size: 14px;
  outline: none;
  box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.6);
}

.search-text-input:focus {
  border-color: rgba(29, 185, 84, 0.4);
  box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.6), 0 0 10px rgba(29, 185, 84, 0.2);
}

.clear-search-btn {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  color: var(--c-text-3);
  cursor: pointer;
}

.search-loading-hint,
.empty-search-hint,
.search-prompt-hint {
  padding: 12px;
  text-align: center;
  font-size: 13px;
  color: var(--c-text-3, #808080);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.mini-spinner {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-top-color: var(--c-accent);
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.search-results-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 280px;
  overflow-y: auto;
}

.search-result-item {
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-cover {
  width: 38px;
  height: 38px;
  border-radius: var(--r-xs, 4px);
  object-fit: cover;
}

.search-cover-fallback {
  width: 38px;
  height: 38px;
  border-radius: var(--r-xs, 4px);
  background: var(--c-bg-1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-3);
}

.search-meta {
  flex: 1;
  min-width: 0;
}

.result-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-artist {
  font-size: 11px;
  color: var(--c-text-2);
}

.result-duration {
  font-family: var(--font-mono, monospace);
  font-size: 11px;
  color: var(--c-text-3);
}

.add-to-queue-btn {
  padding: 6px 12px;
  font-size: 12px;
}

.add-to-queue-btn.added {
  background: #333;
  color: var(--c-accent, #1db954);
  box-shadow: none;
}

/* ─── Queue List Area ─── */
.queue-list-container {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.empty-queue-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  text-align: center;
  gap: 14px;
  color: var(--c-text-2, #b3b3b3);
}

.empty-icon-circle {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-3, #808080);
}

.empty-queue-box h3 {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  color: var(--c-text-1, #fff);
}

.empty-queue-box p {
  font-size: 13px;
  max-width: 360px;
  margin: 0;
  line-height: 1.5;
}

.empty-action-btn {
  margin-top: 8px;
}

.queue-tracks-scroll {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: calc(100vh - 360px);
  min-height: 300px;
  overflow-y: auto;
  padding-right: 4px;
}

.queue-track-card {
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  user-select: none;
}

.queue-track-card:hover {
  background: var(--c-bg-3, #222222);
  transform: translateY(-1px);
}

.queue-track-card.is-playing {
  background: var(--c-bg-3, #222222);
  border-color: rgba(29, 185, 84, 0.4);
  box-shadow: inset 2px 2px 6px rgba(0, 0, 0, 0.6), 0 0 14px rgba(29, 185, 84, 0.15);
}

.queue-track-card.is-dragging {
  opacity: 0.4;
  border: 1px dashed var(--c-accent);
}

.drag-handle {
  color: var(--c-text-4, #555);
  cursor: grab;
  display: flex;
  align-items: center;
}

.drag-handle:active {
  cursor: grabbing;
}

.queue-pos-indicator {
  width: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pos-num {
  font-family: var(--font-mono, monospace);
  font-size: 12px;
  font-weight: 700;
  color: var(--c-text-3, #808080);
}

.mini-playing-eq {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 14px;
}

.eq-b {
  width: 3px;
  background: var(--c-accent, #1db954);
  border-radius: 1px;
  animation: eq-b-anim 0.6s infinite alternate;
}

.b1 { animation-delay: 0.1s; }
.b2 { animation-delay: 0.3s; }
.b3 { animation-delay: 0.2s; }

@keyframes eq-b-anim {
  0% { height: 3px; }
  100% { height: 13px; }
}

.queue-track-cover {
  width: 44px;
  height: 44px;
  border-radius: var(--r-sm, 8px);
  overflow: hidden;
  background: var(--c-bg-1);
  flex-shrink: 0;
}

.q-cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.q-cover-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-3);
}

.queue-track-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.q-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.q-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.now-badge {
  background: rgba(29, 185, 84, 0.2);
  color: var(--c-accent, #1db954);
  font-size: 9px;
  font-weight: 900;
  padding: 2px 6px;
  border-radius: var(--r-xs, 4px);
  border: 1px solid rgba(29, 185, 84, 0.3);
}

.q-sub-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
}

.q-artist {
  color: var(--c-text-2, #b3b3b3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.q-added-badge {
  color: var(--c-text-3, #808080);
  font-size: 11px;
}

.q-duration {
  font-family: var(--font-mono, monospace);
  font-size: 12px;
  color: var(--c-text-3, #808080);
  margin-right: 6px;
}

.queue-item-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.q-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--r-sm, 8px);
  background: var(--c-bg-3, #222222);
  border: 1px solid rgba(255, 255, 255, 0.03);
  color: var(--c-text-2, #b3b3b3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 2px 2px 4px var(--sh-dark);
  transition: all 0.12s ease;
}

.q-btn:hover:not(:disabled) {
  color: var(--c-text-1, #fff);
  background: var(--c-bg-4, #2A2A2A);
}

.q-btn:active:not(:disabled) {
  transform: scale(0.92);
  box-shadow: inset 2px 2px 4px var(--sh-inset-dark);
}

.q-btn.play-cue-btn:hover:not(:disabled) {
  color: var(--c-accent, #1db954);
}

.q-btn.remove-btn:hover:not(:disabled) {
  color: #ff6b6b;
}

.q-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* ═══════════════════════════════════════════════════════════════════
   NO PARTY / CONNECT LANDING FLOW
   ═════════════════════════════════════════════════════════════ */
.no-party-landing-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 16px;
}

.no-party-card {
  max-width: 680px;
  width: 100%;
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 20px;
}

.no-party-icon-circle {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.neon-icon {
  color: var(--c-accent, #1db954);
  filter: drop-shadow(0 0 12px var(--c-accent-glow));
}

.no-party-card h2 {
  font-size: 24px;
  font-weight: 800;
  margin: 0;
}

.no-party-desc {
  font-size: 14px;
  color: var(--c-text-2, #b3b3b3);
  max-width: 480px;
  margin: 0;
  line-height: 1.6;
}

.detected-channel-card {
  width: 100%;
  padding: 20px;
  text-align: left;
  border-color: rgba(29, 185, 84, 0.3);
  background: linear-gradient(180deg, rgba(29, 185, 84, 0.08) 0%, var(--c-bg-2) 100%);
}

.detected-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.detected-badge {
  font-size: 11px;
  font-weight: 800;
  color: var(--c-accent, #1db954);
  letter-spacing: 0.05em;
}

.channel-title {
  font-size: 20px;
  font-weight: 800;
}

.guild-sub {
  color: var(--c-text-2);
  font-weight: 600;
  font-size: 14px;
  margin-left: 6px;
}

.detected-info {
  font-size: 13px;
  color: var(--c-text-2);
  margin: 6px 0 16px;
}

.magic-connect-btn {
  width: 100%;
  padding: 12px;
  font-size: 15px;
  justify-content: center;
}

.channels-section {
  width: 100%;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.channels-section h3 {
  font-size: 15px;
  font-weight: 700;
  margin: 0;
  color: var(--c-text-2);
}

.servers-channels-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.guild-channels-group {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.guild-group-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.guild-icon-small {
  width: 22px;
  height: 22px;
  border-radius: 50%;
}

.guild-name-text {
  font-size: 13px;
  font-weight: 700;
  color: var(--c-text-1);
}

.channels-chips-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.channel-chip-btn {
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 600;
  gap: 6px;
}

.ch-count-badge {
  font-size: 10px;
  color: var(--c-accent, #1db954);
}

.empty-channels-note {
  font-size: 13px;
  color: var(--c-text-3);
  text-align: center;
  padding: 16px;
}

.bot-invite-footer {
  margin-top: 10px;
  text-align: center;
}

.neu-invite-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #7983f5;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  padding: 8px 16px;
  background: rgba(88, 101, 242, 0.12);
  border: 1px solid rgba(88, 101, 242, 0.25);
  border-radius: var(--r-md, 12px);
  transition: all 0.15s ease;
}

.neu-invite-btn:hover {
  background: rgba(88, 101, 242, 0.22);
}

/* Transitions */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.25s ease;
  max-height: 400px;
  opacity: 1;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
  margin-top: 0;
  margin-bottom: 0;
}

/* ═══════════════════════════════════════════════════════════════════
   RESPONSIVE BREAKPOINTS: MOBILE ADAPTATION (< 768px)
   ═══════════════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
  .dj-view-container {
    padding: 10px;
    padding-bottom: calc(var(--player-height, 64px) + 84px + env(safe-area-inset-bottom, 16px));
    gap: 10px;
  }

  .dj-header {
    display: grid;
    grid-template-columns: 1fr auto;
    grid-template-areas: 
      "left right"
      "chips chips";
    padding: 10px 12px;
    gap: 8px;
  }

  .dj-header-left {
    grid-area: left;
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
  }

  .dj-title-box {
    min-width: 0;
    flex: 1;
  }

  .dj-room-name {
    font-size: 15px;
    line-height: 1.25;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 4px;
    word-break: break-word;
  }

  .guild-title-text {
    font-size: 15px;
  }

  .channel-hash {
    font-size: 13px;
    margin-left: 2px;
  }

  .dj-header-right {
    grid-area: right;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 6px;
    width: auto;
  }

  .dj-header-right .in-voice-pill {
    display: none;
  }

  .dj-header-right .disconnect-btn,
  .dj-header-right .connect-quick-btn {
    padding: 5px 10px;
    font-size: 11px;
    border-radius: var(--r-sm, 8px);
  }

  /* Horizontal scrolling chips row for DJ badges on mobile */
  .dj-header-center {
    grid-area: chips;
    width: 100%;
    display: flex;
    align-items: center;
    overflow-x: auto;
    flex-wrap: nowrap;
    gap: 6px;
    padding-bottom: 2px;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }
  .dj-header-center::-webkit-scrollbar {
    display: none;
  }

  .dj-header-center .neu-card-sm,
  .dj-header-center .neu-btn-toggle {
    flex-shrink: 0;
    font-size: 11px;
    padding: 5px 8px;
  }

  /* Master deck adjustments on mobile - zero-scroll compact layout */
  .master-deck-card {
    padding: 10px;
    gap: 8px;
  }

  .vinyl-display-wrapper {
    width: 100px;
    height: 100px;
    margin: 0 auto 0;
  }

  .vinyl-record {
    width: 95px;
    height: 95px;
    right: -6px;
    top: -2px;
  }

  .cover-art-box {
    width: 85px;
    height: 85px;
  }

  .cover-fallback svg {
    width: 28px;
    height: 28px;
  }

  .deck-track-info {
    margin-top: 0;
    gap: 2px;
    text-align: center;
  }

  .track-title-text {
    font-size: 14px;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .track-artist-text {
    font-size: 11px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .added-by-pill {
    font-size: 9px;
    padding: 2px 6px;
    margin: 0 auto;
  }

  .deck-lcd-screen {
    padding: 6px 10px;
    gap: 4px;
  }

  .lcd-top-row {
    font-size: 9px;
  }

  .lcd-time-display {
    font-size: 20px;
    margin: 0;
  }

  .lcd-time-main {
    font-size: 20px;
  }

  .lcd-time-total {
    font-size: 14px;
  }

  .lcd-vu-meter {
    height: 4px;
    gap: 2px;
  }

  .deck-progress-container {
    gap: 2px;
  }

  .progress-labels {
    font-size: 10px;
  }

  .deck-controls-row {
    gap: 10px;
    margin: 2px 0;
  }

  .master-play-btn {
    width: 48px;
    height: 48px;
  }

  .control-btn {
    width: 36px;
    height: 36px;
  }

  .deck-volume-box {
    padding: 4px 10px;
    gap: 8px;
  }

  /* Queue manager adjustments on mobile */
  .queue-manager-card {
    padding: 14px 12px;
  }

  .queue-header-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .queue-actions-area {
    width: 100%;
    display: flex;
    overflow-x: auto;
    flex-wrap: nowrap;
    gap: 6px;
    padding-bottom: 2px;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }
  .queue-actions-area::-webkit-scrollbar {
    display: none;
  }

  .queue-actions-area .neu-btn-action {
    flex-shrink: 0;
    padding: 6px 10px;
    font-size: 12px;
  }

  .queue-track-item {
    padding: 8px 10px;
    gap: 8px;
  }

  .track-cover-mini {
    width: 36px;
    height: 36px;
  }
}
</style>
