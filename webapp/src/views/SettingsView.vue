<template>
  <div class="settings-view">
    <div class="settings-header">
      <h1>Настройки</h1>
    </div>

    <!-- 1. Telegram Backup Channel Section -->
    <section id="channel" class="settings-section">
      <div class="section-header">
        <h2>
          <Megaphone :size="18" />
          <span>Канал для бэкапа</span>
        </h2>
        <span class="status-pill" :class="{ connected: authStore.hasChannel }">
          <Check v-if="authStore.hasChannel" :size="12" />
          {{ authStore.hasChannel ? 'Подключён' : 'Не привязан' }}
        </span>
      </div>

      <div class="settings-card channel-card" :class="{ 'not-connected': !authStore.hasChannel }">
        <template v-if="authStore.hasChannel">
          <div class="channel-connected">
            <div class="channel-info">
              <div class="channel-icon"><Check :size="20" /></div>
              <div class="channel-details">
                <span class="channel-title">{{ authStore.channelInfo?.channel_title || 'Канал подключён' }}</span>
                <span class="channel-username" v-if="authStore.channelInfo?.channel_username">
                  @{{ authStore.channelInfo.channel_username }}
                </span>
              </div>
            </div>
            <div class="channel-features">
              <div class="feature-item"><Check :size="13" /> Сохранение треков</div>
              <div class="feature-item"><Check :size="13" /> Создание плейлистов</div>
              <div class="feature-item"><Check :size="13" /> Автобэкап в канал</div>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="channel-not-connected">
            <p class="channel-desc">
              Подключите Telegram-канал, чтобы разблокировать все функции:
            </p>
            <ul class="feature-list">
              <li><Folder :size="15" /> Загрузка и сохранение треков</li>
              <li><Heart :size="15" /> Лайки и избранное</li>
              <li><ListMusic :size="15" /> Создание плейлистов</li>
              <li><Cloud :size="15" /> Автоматический бэкап музыки</li>
            </ul>
            <div class="setup-steps">
              <h3>Как подключить:</h3>
              <ol>
                <li>Создайте приватный канал в Telegram</li>
                <li>Добавьте бота <strong>@{{ botUsername }}</strong> админом канала</li>
                <li>Напишите боту команду <code>/channel</code></li>
                <li>Перешлите любое сообщение из канала боту</li>
              </ol>
            </div>
            <button class="action-btn primary channel-refresh-btn" @click="refreshStatus">
              <RefreshCw :size="15" />
              <span>Обновить статус</span>
            </button>
          </div>
        </template>
      </div>
    </section>

    <!-- 2. SoundCloud Integration Section -->
    <section id="soundcloud" class="settings-section">
      <div class="section-header">
        <h2>
          <span class="sc-logo-badge">SC</span>
          <span>SoundCloud</span>
        </h2>
        <span class="status-pill sc-status" :class="{ connected: scAccount?.connected }">
          <Check v-if="scAccount?.connected" :size="12" />
          {{ loadingScAccount && !scAccount ? 'Проверка...' : (scAccount?.connected ? 'Подключён' : 'Не привязан') }}
        </span>
      </div>

      <div class="settings-card sc-card">
        <div v-if="loadingScAccount && !scAccount" class="service-loading-box">
          <div class="spinner small"></div>
          <span>Проверка аккаунта...</span>
        </div>

        <!-- Connected State -->
        <template v-else-if="scAccount?.connected">
          <div class="service-profile-header">
            <img 
              v-if="scAccount.avatar_url" 
              :src="scAccount.avatar_url" 
              alt="SoundCloud avatar" 
              class="service-avatar sc-avatar" 
              referrerpolicy="no-referrer"
            />
            <div v-else class="service-avatar-placeholder sc-placeholder">
              <Radio :size="22" />
            </div>
            <div class="service-user-details">
              <span class="service-user-title">{{ scAccount.display_name || scAccount.username }}</span>
              <a :href="scAccount.profile_url" target="_blank" rel="noopener" class="service-user-link sc-link">
                @{{ scAccount.username }} <ExternalLink :size="12" />
              </a>
            </div>
            <div class="sc-likes-badge" title="Количество лайков на SoundCloud">
              <span class="sc-likes-num">{{ scAccount.likes_count || 0 }}</span>
              <span class="sc-likes-label">лайков</span>
            </div>
          </div>

          <div class="service-actions-grid">
            <button class="action-btn primary sc-primary-btn" @click="goToSoundCloudLikes">
              <Heart :size="15" />
              <span>Мои лайки SoundCloud</span>
            </button>
            <button class="action-btn danger-ghost" :disabled="isDisconnectingSc" @click="handleDisconnectSc">
              <Unlink :size="15" />
              <span>Отвязать</span>
            </button>
          </div>
        </template>

        <!-- Not Connected State -->
        <template v-else>
          <p class="service-desc">
            Привяжите профиль SoundCloud, чтобы переносить любимые треки в медиатеку и сохранять аудио в Telegram-канал.
          </p>

          <div class="service-input-block">
            <label class="service-input-label">Ссылка на профиль или никнейм:</label>
            <div class="service-input-row">
              <input 
                v-model="scUsernameInput" 
                type="text" 
                placeholder="soundcloud.com/ваш-ник или ваш-ник"
                class="service-text-input"
                :disabled="isConnectingSc"
                @keydown.enter="handleConnectSc"
              />
              <button 
                class="action-btn primary sc-primary-btn connect-submit-btn" 
                :disabled="!scUsernameInput.trim() || isConnectingSc"
                @click="handleConnectSc"
              >
                <div v-if="isConnectingSc" class="spinner small"></div>
                <template v-else>Подключить</template>
              </button>
            </div>
          </div>

          <div class="token-foldout">
            <button class="token-foldout-toggle" @click="showTokenField = !showTokenField">
              <Key :size="13" />
              <span>{{ showTokenField ? 'Скрыть токен' : 'Приватные треки / OAuth Token (опционально)' }}</span>
              <ChevronDown :size="13" :class="{ rotated: showTokenField }" />
            </button>
            <div v-if="showTokenField" class="token-foldout-body">
              <input 
                v-model="scTokenInput" 
                type="password" 
                placeholder="OAuth Token из cookie oauth_token (необязательно)"
                class="service-text-input token-input"
                :disabled="isConnectingSc"
              />
              <span class="token-hint">Требуется только если ваши лайки закрыты настройками приватности на SoundCloud.</span>
            </div>
          </div>

          <div v-if="scConnectError" class="service-error-box">
            <AlertCircle :size="16" />
            <span>{{ scConnectError }}</span>
          </div>
        </template>
      </div>
    </section>

    <!-- 3. Spotify Integration & Import Section -->
    <section id="import" class="settings-section">
      <div class="section-header">
        <h2>
          <Radio :size="18" class="sp-icon" />
          <span>Spotify</span>
        </h2>
        <span class="status-pill sp-status" :class="{ connected: spAccount?.connected }">
          <Check v-if="spAccount?.connected" :size="12" />
          {{ loadingSpAccount && !spAccount ? 'Проверка...' : (spAccount?.connected ? 'Подключен' : 'Не подключен') }}
        </span>
      </div>

      <div class="settings-card sp-card">
        <p class="service-desc">
          Переносите треки и плейлисты из Spotify в высоком качестве 320 kbps через экспорт CSV (Exportify). 
          Все треки распознаются, проверяются на дубликаты и сохраняются в канал.
        </p>

        <!-- Quick Exportify Action Box -->
        <div class="sp-exportify-box">
          <div class="sp-exportify-info">
            <div class="sp-exportify-icon">
              <FileSpreadsheet :size="22" />
            </div>
            <div class="sp-exportify-texts">
              <span class="sp-exportify-title">Импорт через Exportify CSV</span>
              <span class="sp-exportify-sub">Бесплатно в 1 клик, без Premium и ввода паролей/токенов</span>
            </div>
          </div>
          <div class="sp-exportify-actions">
            <button class="action-btn primary sp-primary-btn" @click="tasksStore.openExportifyModal()">
              <Upload :size="15" />
              <span>Загрузить CSV файл</span>
            </button>
            <a 
              href="https://exportify.app" 
              target="_blank" 
              rel="noopener noreferrer" 
              class="action-btn secondary"
              title="Открыть exportify.app в новой вкладке"
            >
              <span>exportify.app</span>
              <ExternalLink :size="13" />
            </a>
          </div>
        </div>

        <!-- Spotify Profile Connection Box (Beautiful & Fixed!) -->
        <div v-if="spAccount?.connected" class="sp-profile-connected-row">
          <div class="sp-profile-info">
            <div class="sp-profile-avatar-wrap">
              <Radio :size="16" class="sp-icon" />
            </div>
            <div class="sp-profile-texts">
              <span class="sp-profile-label">Привязан профиль:</span>
              <span class="sp-profile-name" :title="spAccount.display_name || spAccount.username">
                {{ spAccount.display_name || spAccount.username }}
              </span>
            </div>
          </div>
          <button 
            class="action-btn danger-ghost sp-unlink-btn" 
            :disabled="isDisconnectingSp" 
            @click="handleDisconnectSp"
            title="Отвязать профиль Spotify"
          >
            <Unlink :size="14" />
            <span>Отвязать профиль</span>
          </button>
        </div>

        <div v-else class="service-input-block sp-input-block">
          <label class="service-input-label">Привязать профиль Spotify (опционально):</label>
          <div class="service-input-row">
            <input 
              v-model="spUsernameInput" 
              type="text" 
              placeholder="spotify.com/user/ваш-ник или ваш-ник"
              class="service-text-input"
              :disabled="isConnectingSp"
              @keydown.enter="handleConnectSp"
            />
            <button 
              class="action-btn secondary connect-submit-btn" 
              :disabled="!spUsernameInput.trim() || isConnectingSp"
              @click="handleConnectSp"
            >
              <div v-if="isConnectingSp" class="spinner small"></div>
              <template v-else>Сохранить</template>
            </button>
          </div>
        </div>

        <div v-if="spConnectError" class="service-error-box">
          <AlertCircle :size="16" />
          <span>{{ spConnectError }}</span>
        </div>
      </div>
    </section>

    <!-- 4. Profile & Privacy Section -->
    <section id="profile" ref="profileSectionRef" class="settings-section">
      <div class="section-header">
        <h2>
          <User :size="18" />
          <span>Профиль и приватность</span>
        </h2>
      </div>

      <div class="settings-card profile-privacy-card">
        <!-- Top Profile Card -->
        <div class="profile-header-card" v-if="authStore.user">
          <div class="profile-avatar-block" @click="avatarFileInputRef?.click()" title="Нажмите, чтобы загрузить или сменить фото">
            <div class="profile-avatar-visual" :style="avatarGradient">
              <img 
                v-if="authStore.user?.custom_avatar_url" 
                :src="authStore.user.custom_avatar_url" 
                alt="Avatar" 
                class="avatar-image-cover" 
              />
              <User v-else-if="!authStore.user.first_name && !authStore.user.custom_nickname" :size="26" />
              <span v-else class="avatar-letter">{{ (authStore.user.custom_nickname || authStore.user.first_name || 'U').charAt(0).toUpperCase() }}</span>
              <div class="profile-avatar-hover-ring">
                <Camera :size="18" />
              </div>
            </div>
            <div class="profile-avatar-badge" title="Сменить фото">
              <Camera :size="11" />
            </div>
            <input 
              ref="avatarFileInputRef" 
              type="file" 
              accept="image/*" 
              style="display: none" 
              @change="handleAvatarFileChange" 
            />
          </div>

          <div class="profile-meta-info">
            <div class="profile-name-row">
              <span class="profile-user-name" :title="authStore.userDisplayName">{{ authStore.userDisplayName }}</span>
              <button class="view-profile-chip" @click="goToMyProfile" title="Открыть свой профиль">
                <span>Профиль</span>
                <ChevronRight :size="12" />
              </button>
            </div>
            <div class="profile-handle-row">
              <span class="profile-handle">@{{ authStore.user.username || ('ID: ' + authStore.user.id) }}</span>
              <span v-if="privacySettings.hide_telegram_id" class="hidden-privacy-pill" title="Скрыт от других пользователей">
                <EyeOff :size="10" /> скрыт
              </span>
            </div>
            <!-- Quick photo actions -->
            <div class="avatar-quick-actions">
              <button 
                class="avatar-action-btn" 
                :disabled="isUploadingAvatar" 
                @click="avatarFileInputRef?.click()"
              >
                <Camera :size="12" />
                <span>{{ isUploadingAvatar ? 'Загрузка...' : (authStore.user?.custom_avatar_url ? 'Сменить' : 'Загрузить фото') }}</span>
              </button>
              <button 
                v-if="authStore.user?.custom_avatar_url" 
                class="avatar-action-btn danger" 
                :disabled="isUploadingAvatar" 
                @click="handleRemoveAvatar"
                title="Удалить аватарку"
              >
                <Trash2 :size="12" />
                <span>Удалить</span>
              </button>
            </div>
          </div>
        </div>

        <div class="setting-divider"></div>

        <!-- Custom Nickname Section -->
        <div class="profile-field-block">
          <div class="field-header">
            <div class="field-title-group">
              <span class="field-title">Кастомный никнейм</span>
              <span class="field-hint">Отображается вместо Telegram-имени</span>
            </div>
            <button 
              v-if="authStore.user?.custom_nickname && !isNicknameDirty" 
              class="field-reset-link" 
              :disabled="isSavingProfile" 
              @click="handleResetNickname" 
              title="Сбросить на имя из Telegram"
            >
              <RotateCcw :size="11" />
              <span>Сбросить ник</span>
            </button>
          </div>

          <div class="nickname-field-row">
            <div class="nickname-input-box" :class="{ 'is-dirty': isNicknameDirty }">
              <input 
                v-model="customNicknameInput" 
                type="text" 
                maxlength="50"
                placeholder="Введите никнейм" 
                class="nickname-clean-input" 
                :disabled="isSavingProfile"
                @keydown.enter="handleSaveNickname"
                @keydown.esc="handleCancelNickname"
              />
              <button 
                v-if="customNicknameInput" 
                class="input-clear-btn" 
                @click="customNicknameInput = ''" 
                title="Очистить"
                type="button"
                tabindex="-1"
              >
                <X :size="12" />
              </button>
            </div>

            <div class="nickname-actions-group">
              <button 
                class="profile-save-btn" 
                :class="{ 'is-active': isNicknameDirty }"
                :disabled="isSavingProfile || !isNicknameDirty" 
                @click="handleSaveNickname"
                title="Сохранить никнейм"
              >
                <div v-if="isSavingProfile" class="spinner small"></div>
                <Check v-else :size="13" />
                <span>Сохранить</span>
              </button>
              <button 
                v-if="isNicknameDirty" 
                class="profile-cancel-btn" 
                :disabled="isSavingProfile" 
                @click="handleCancelNickname"
                title="Отменить изменения"
              >
                <X :size="13" />
              </button>
            </div>
          </div>
        </div>

        <div class="setting-divider"></div>

        <!-- Privacy Subgroup Header -->
        <div class="privacy-subgroup-header">
          <Lock :size="13" />
          <span>Приватность</span>
        </div>

        <!-- Privacy Toggle 1: Hide Telegram ID & Username -->
        <div class="setting-row">
          <div class="setting-info">
            <span class="setting-name">Скрыть Telegram ID и ник</span>
            <span class="setting-desc">Ваш @username и ID не будут видны другим в профиле и поиске</span>
          </div>
          <label class="toggle">
            <input 
              type="checkbox" 
              v-model="privacySettings.hide_telegram_id" 
              @change="updatePrivacy('hide_telegram_id', $event.target.checked)"
            />
            <span class="toggle-slider"></span>
          </label>
        </div>

        <div class="setting-divider"></div>

        <!-- Privacy Toggle 2: Hide Profile Completely -->
        <div class="setting-row">
          <div class="setting-info">
            <span class="setting-name">Скрыть профиль полностью</span>
            <span class="setting-desc">Медиатека и альбомы будут скрыты от других</span>
          </div>
          <label class="toggle">
            <input 
              type="checkbox" 
              v-model="privacySettings.hide_profile" 
              @change="updatePrivacy('hide_profile', $event.target.checked)"
            />
            <span class="toggle-slider"></span>
          </label>
        </div>

        <div class="setting-divider"></div>

        <!-- Privacy Toggle 3: Hide from Search -->
        <div class="setting-row">
          <div class="setting-info">
            <span class="setting-name">Скрыть из поиска</span>
            <span class="setting-desc">Вас не найдут в поиске, доступ только по прямой ссылке</span>
          </div>
          <label class="toggle">
            <input 
              type="checkbox" 
              v-model="privacySettings.hide_from_search" 
              @change="updatePrivacy('hide_from_search', $event.target.checked)"
            />
            <span class="toggle-slider"></span>
          </label>
        </div>

        <div class="setting-divider"></div>

        <!-- Logout Action -->
        <button class="logout-btn" @click="logout">
          <LogOut :size="16" />
          <span>Выйти из аккаунта</span>
        </button>
      </div>
    </section>

    <!-- 5. Library Stats -->
    <section id="stats" class="settings-section">
      <div class="section-header">
        <h2>
          <Library :size="18" />
          <span>Библиотека</span>
        </h2>
      </div>

      <div class="settings-card stats-card">
        <div class="stats-grid" v-if="stats">
          <div class="stat-item">
            <span class="stat-value">{{ stats.total_tracks }}</span>
            <span class="stat-label">треков</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.album_count }}</span>
            <span class="stat-label">альбомов</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.artist_count }}</span>
            <span class="stat-label">исполнителей</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ formatDuration(stats.total_duration_seconds) }}</span>
            <span class="stat-label">общее время</span>
          </div>
        </div>
        <div class="stats-grid" v-else>
          <div class="stat-item stat-skeleton" v-for="i in 4" :key="i">
            <div class="skeleton-stat-value"></div>
            <div class="skeleton-stat-label"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- 7. Notification settings -->
    <section id="notifications" class="settings-section">
      <div class="section-header">
        <h2>
          <Bell :size="18" />
          <span>Уведомления</span>
        </h2>
      </div>

      <div class="settings-card">
        <div class="setting-row">
          <div class="setting-info">
            <span class="setting-name">Уведомления о подписках</span>
            <span class="setting-desc">Получать уведомления, когда кто-то подписывается на вас или ваши плейлисты</span>
          </div>
          <label class="toggle">
            <input 
              type="checkbox" 
              v-model="privacySettings.notify_subscription" 
              @change="updatePrivacy('notify_subscription', $event.target.checked)"
            />
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>
    </section>

    <!-- 8. Interface Section -->
    <section id="interface" class="settings-section">
      <div class="section-header">
        <h2>
          <Sliders :size="18" />
          <span>Интерфейс</span>
        </h2>
      </div>

      <div class="settings-card">
        <div class="setting-row slider-setting-block">
          <div class="slider-row-top">
            <div class="slider-label-group">
              <span class="setting-name">Масштаб интерфейса</span>
              <button 
                v-if="Math.round(playerStore.uiScale * 100) !== 100"
                class="scale-reset-btn"
                @click="playerStore.uiScale = 1.0"
                title="Сбросить на 100%"
              >
                Сброс
              </button>
            </div>
            <span class="setting-value">{{ Math.round(playerStore.uiScale * 100) }}%</span>
          </div>

          <input 
            type="range" 
            min="0.7" 
            max="1.3" 
            step="0.05"
            v-model.number="playerStore.uiScale"
            class="range-slider"
          />

          <div class="scale-presets-wrap">
            <div class="scale-presets">
              <button 
                v-for="preset in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]" 
                :key="preset"
                class="scale-preset-chip"
                :class="{ active: Math.round(playerStore.uiScale * 100) === Math.round(preset * 100) }"
                @click="playerStore.uiScale = preset"
              >
                {{ Math.round(preset * 100) }}%
              </button>
            </div>
          </div>
          <span class="setting-desc scale-desc">Измените размер интерфейса плеера под экран устройства</span>
        </div>
      </div>
    </section>

    <!-- 9. Audio (Enhancer) Section -->
    <section id="playback" class="settings-section">
      <div class="section-header">
        <h2>
          <Headphones :size="18" />
          <span>Аудио (Enhancer)</span>
        </h2>
        <span class="status-pill" :class="{ connected: playerStore.enhancerEnabled }">
          {{ playerStore.enhancerEnabled ? 'Включён' : 'Выключен' }}
        </span>
      </div>

      <div class="settings-card">
        <div class="setting-row">
          <div class="setting-info">
            <span class="setting-name">Включить обработку</span>
            <span class="setting-desc">Улучшение звука в реальном времени (Bass, Treble, Auto Gain)</span>
          </div>
          <label class="toggle">
            <input 
              type="checkbox" 
              v-model="playerStore.enhancerEnabled" 
            />
            <span class="toggle-slider"></span>
          </label>
        </div>

        <template v-if="playerStore.enhancerEnabled">
          <div class="setting-divider"></div>

          <div class="setting-row slider-setting-block">
            <div class="slider-row-top">
              <span class="setting-name">Bass (Низкие)</span>
              <span class="setting-value">{{ playerStore.bassGain }} dB</span>
            </div>
            <input 
              type="range" 
              min="-10" 
              max="10" 
              step="1"
              v-model.number="playerStore.bassGain"
              class="range-slider"
            />
          </div>

          <div class="setting-divider"></div>

          <div class="setting-row slider-setting-block">
            <div class="slider-row-top">
              <span class="setting-name">Treble (Высокие)</span>
              <span class="setting-value">{{ playerStore.trebleGain }} dB</span>
            </div>
            <input 
              type="range" 
              min="-10" 
              max="10" 
              step="1"
              v-model.number="playerStore.trebleGain"
              class="range-slider"
            />
          </div>

          <div class="setting-divider"></div>

          <div class="setting-row">
            <div class="setting-info">
              <span class="setting-name">Auto Gain (Компрессор)</span>
              <span class="setting-desc">Автоматическое выравнивание громкости между треками</span>
            </div>
            <label class="toggle">
              <input 
                type="checkbox" 
                v-model="playerStore.autoGain" 
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </template>
      </div>
    </section>

    <!-- 10. App (PWA) Section -->
    <section id="storage" class="settings-section">
      <div class="section-header">
        <h2>
          <Smartphone :size="18" />
          <span>Приложение</span>
        </h2>
      </div>

      <div class="settings-card">
        <div v-if="pwaInstall.isInstalled" class="pwa-status-installed">
          <div class="pwa-status-icon"><Check :size="20" /></div>
          <div class="pwa-status-text">
            <span class="pwa-status-title">Приложение установлено</span>
            <span class="pwa-status-desc">AuxBass работает в полноэкранном режиме Web App</span>
          </div>
        </div>

        <div v-else class="pwa-install-card">
          <div class="setting-info">
            <span class="setting-name">Установить как Web App</span>
            <span class="setting-desc">Быстрый запуск с домашнего экрана, фоновое воспроизведение и медиаклавиши</span>
          </div>
          <button class="action-btn primary pwa-install-btn" @click="handleInstallClick">
            <Download :size="16" />
            <span>{{ pwaInstall.isIOS ? 'Как установить' : 'Установить' }}</span>
          </button>
        </div>
      </div>
    </section>

    <!-- 11. Cache & Storage Section -->
    <section id="cache" class="settings-section">
      <div class="section-header">
        <h2>
          <HardDrive :size="18" />
          <span>Кэш и память</span>
        </h2>
      </div>

      <div class="settings-card cache-card">
        <!-- Auto-cache toggle -->
        <div class="setting-row">
          <div class="setting-info">
            <span class="setting-name">Автокэширование треков</span>
            <span class="setting-desc">Автоматически сохранять треки на устройство для мгновенного старта и офлайн-прослушивания</span>
          </div>
          <label class="toggle">
            <input 
              type="checkbox" 
              v-model="playerStore.autoCacheEnabled" 
            />
            <span class="toggle-slider"></span>
          </label>
        </div>

        <!-- Max Cache Size -->
        <template v-if="playerStore.autoCacheEnabled">
          <div class="setting-divider"></div>

          <div class="setting-row slider-setting-block">
            <div class="slider-row-top">
              <span class="setting-name">Лимит размера кэша</span>
              <span class="setting-value">{{ formatCacheLimit(playerStore.cacheMaxBytes) }}</span>
            </div>
            <div class="scale-presets-wrap">
              <div class="scale-presets cache-limits-presets">
                <button 
                  v-for="limit in cacheLimits" 
                  :key="limit.value"
                  class="scale-preset-chip"
                  :class="{ active: playerStore.cacheMaxBytes === limit.value }"
                  @click="playerStore.cacheMaxBytes = limit.value"
                >
                  {{ limit.label }}
                </button>
              </div>
            </div>
            <span class="setting-desc">При заполнении кэша старые треки удаляются автоматически (LRU)</span>
          </div>
        </template>

        <div class="setting-divider"></div>

        <!-- Cache stats bar -->
        <div class="cache-storage-bar-box">
          <div class="cache-stats-header">
            <div class="cache-stat-item">
              <span class="cache-stat-label">Занято кэшем</span>
              <span class="cache-stat-val">{{ formatBytes(cacheStats.totalBytes) }} <span class="cache-stat-count">({{ cacheStats.trackCount }} треков)</span></span>
            </div>
            <div v-if="cacheStats.quotaBytes > 0" class="cache-stat-item align-right">
              <span class="cache-stat-label">Доступно</span>
              <span class="cache-stat-val">{{ formatBytes(cacheStats.quotaBytes - cacheStats.usageBytes) }}</span>
            </div>
          </div>

          <div class="cache-progress-bar">
            <div 
              class="cache-progress-fill" 
              :style="{ width: `${cacheFillPercent}%` }"
            ></div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="cache-actions-grid">
          <button 
            v-if="cacheStats.trackCount > 0"
            class="action-btn success-soft view-downloaded-btn"
            @click="router.push('/downloaded')"
          >
            <HardDrive :size="15" />
            <span>Открыть скачанные ({{ cacheStats.trackCount }})</span>
          </button>

          <button 
            class="action-btn danger-soft clear-cache-btn" 
            :disabled="clearingCache || cacheStats.trackCount === 0"
            @click="handleClearCache"
          >
            <Trash2 :size="15" />
            <span>{{ clearingCache ? 'Очистка...' : 'Очистить кэш треков' }}</span>
          </button>
        </div>
      </div>
    </section>

    <!-- 12. About Section -->
    <section id="about" class="settings-section about-section">
      <div class="settings-card about-card">
        <h3 class="about-title">{{ authStore.appName }} <span class="about-ver">v2.0</span></h3>
        <p class="about-desc">Музыкальный плеер с хранением и стримингом в Telegram</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import { useTasksStore } from '@/stores/tasks'
import { useExternalAccountsStore } from '@/stores/externalAccounts'
import api, { authApi, ingestionApi } from '@/api/client'
import { 
  Megaphone, Check, Folder, Heart, ListMusic, Cloud, RefreshCw, Lock, 
  User, Bell, Sliders, Headphones, Smartphone, Download, HardDrive, 
  Trash2, ChevronRight, ExternalLink, Unlink, Key, ChevronDown, 
  AlertCircle, Radio, FileSpreadsheet, Upload, LogOut, Library,
  Camera, EyeOff, X, RotateCcw
} from 'lucide-vue-next'
import { usePwaInstall } from '@/composables/usePwaInstall'
import { getCacheStats, getCachedAudioStats } from '@/utils/audioCacheDb'
import { clearAudioCache } from '@/stores/playerCache'
import { formatDurationLong as formatDuration } from '@/utils'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const playerStore = usePlayerStore()
const tasksStore = useTasksStore()
const externalAccountsStore = useExternalAccountsStore()
const pwaInstall = usePwaInstall()

const goToMyProfile = () => {
  if (authStore.user?.id) {
    router.push(`/user/${authStore.user.id}`)
  }
}

const handleInstallClick = () => {
  pwaInstall.promptInstall()
}

// ─── Profile Customization State ───
const customNicknameInput = ref(authStore.user?.custom_nickname || '')
const isSavingProfile = ref(false)
const isUploadingAvatar = ref(false)
const avatarFileInputRef = ref(null)

const isNicknameDirty = computed(() => {
  const current = (authStore.user?.custom_nickname || '').trim()
  const input = customNicknameInput.value.trim()
  return input !== current
})

const handleCancelNickname = () => {
  customNicknameInput.value = authStore.user?.custom_nickname || ''
}

watch(() => authStore.user, (newU) => {
  if (newU) {
    customNicknameInput.value = newU.custom_nickname || ''
  }
}, { immediate: true })

const handleSaveNickname = async () => {
  if (isSavingProfile.value || !isNicknameDirty.value) return
  isSavingProfile.value = true
  try {
    await authStore.updateProfile({ custom_nickname: customNicknameInput.value.trim() })
  } catch (err) {
    console.error('Failed to update nickname:', err)
  } finally {
    isSavingProfile.value = false
  }
}

const handleResetNickname = async () => {
  if (isSavingProfile.value) return
  isSavingProfile.value = true
  try {
    await authStore.updateProfile({ custom_nickname: '' })
    customNicknameInput.value = ''
  } catch (err) {
    console.error('Failed to reset nickname:', err)
  } finally {
    isSavingProfile.value = false
  }
}

const handleAvatarFileChange = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  isUploadingAvatar.value = true
  try {
    await authStore.uploadAvatar(file)
  } catch (err) {
    console.error('Failed to upload avatar:', err)
  } finally {
    isUploadingAvatar.value = false
    if (e.target) e.target.value = ''
  }
}

const handleRemoveAvatar = async () => {
  if (!confirm('Удалить аватарку профиля?')) return
  isUploadingAvatar.value = true
  try {
    await authStore.deleteAvatar()
  } catch (err) {
    console.error('Failed to delete avatar:', err)
  } finally {
    isUploadingAvatar.value = false
  }
}

const STATS_STORAGE_KEY = 'tg_player_library_stats'

const getCachedStats = () => {
  try {
    const raw = localStorage.getItem(STATS_STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch (_) {}
  return null
}

const stats = ref(getCachedStats())
const statsLoading = ref(!stats.value)
const darkMode = ref(true)
const botUsername = ref('tg_player_bot')  // Default, will be updated from config
const privacySettings = ref({
  hide_from_search: false,
  hide_profile: false,
  hide_telegram_id: false,
  notify_subscription: true,
})

// ─── SoundCloud Integration State ───
const scAccount = computed(() => externalAccountsStore.scAccount)
const loadingScAccount = computed(() => externalAccountsStore.loadingSc)
const isConnectingSc = ref(false)
const isDisconnectingSc = ref(false)
const scUsernameInput = ref('')
const scTokenInput = ref('')
const showTokenField = ref(false)
const scConnectError = ref('')

const fetchScAccount = async (force = false) => {
  try {
    await externalAccountsStore.fetchSoundCloud(force)
  } catch (e) {
    console.error('Failed to fetch SoundCloud account:', e)
  }
}

const handleConnectSc = async () => {
  const cleanUser = scUsernameInput.value.trim()
  if (!cleanUser) return
  isConnectingSc.value = true
  scConnectError.value = ''
  try {
    await externalAccountsStore.connectSoundCloud({
      username_or_url: cleanUser,
      auth_token: scTokenInput.value.trim() || undefined,
    })
    scUsernameInput.value = ''
    scTokenInput.value = ''
    showTokenField.value = false
  } catch (e) {
    console.error('Failed to connect SoundCloud:', e)
    scConnectError.value = e.response?.data?.detail || 'Не удалось привязать профиль SoundCloud'
  } finally {
    isConnectingSc.value = false
  }
}

const handleDisconnectSc = async () => {
  if (!confirm('Отвязать аккаунт SoundCloud?')) return
  isDisconnectingSc.value = true
  try {
    await externalAccountsStore.disconnectSoundCloud()
  } catch (e) {
    console.error('Failed to disconnect SoundCloud:', e)
  } finally {
    isDisconnectingSc.value = false
  }
}

const goToSoundCloudLikes = () => {
  router.push({ path: '/search', query: { tab: 'soundcloud', mode: 'likes' } })
}

// ─── Spotify Integration State ───
const spAccount = computed(() => externalAccountsStore.spAccount)
const loadingSpAccount = computed(() => externalAccountsStore.loadingSp)
const isConnectingSp = ref(false)
const isDisconnectingSp = ref(false)
const spUsernameInput = ref('')
const spTokenInput = ref('')
const showSpTokenField = ref(false)
const spConnectError = ref('')

const fetchSpAccount = async (force = false) => {
  try {
    await externalAccountsStore.fetchSpotify(force)
  } catch (e) {
    console.error('Failed to fetch Spotify account:', e)
  }
}

const handleConnectSp = async () => {
  const cleanUser = spUsernameInput.value.trim()
  if (!cleanUser) return
  isConnectingSp.value = true
  spConnectError.value = ''
  try {
    await externalAccountsStore.connectSpotify({
      username_or_url: cleanUser,
      auth_token: spTokenInput.value.trim() || undefined,
    })
    spUsernameInput.value = ''
    spTokenInput.value = ''
    showSpTokenField.value = false
  } catch (e) {
    console.error('Failed to connect Spotify:', e)
    spConnectError.value = e.response?.data?.detail || 'Не удалось привязать профиль Spotify'
  } finally {
    isConnectingSp.value = false
  }
}

const handleDisconnectSp = async () => {
  if (!confirm('Отвязать аккаунт Spotify?')) return
  isDisconnectingSp.value = true
  try {
    await externalAccountsStore.disconnectSpotify()
  } catch (e) {
    console.error('Failed to disconnect Spotify:', e)
  } finally {
    isDisconnectingSp.value = false
  }
}

const goToSpotifyLikes = () => {
  router.push({ path: '/search', query: { tab: 'spotify', mode: 'likes' } })
}

// Avatar gradient based on user ID for unique colors
const avatarGradient = computed(() => {
  const id = authStore.user?.id || 0
  const hue = (id * 137) % 360
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 60%, 45%) 0%, hsl(${(hue + 40) % 360}, 50%, 35%) 100%)`
  }
})

const repeatModeText = computed(() => {
  const modes = {
    none: 'Выключен',
    all: 'Повтор всего',
    one: 'Повтор трека'
  }
  return modes[playerStore.repeatMode] || 'Выключен'
})

const repeatModeIcon = computed(() => {
  const icons = {
    none: '🔁',
    all: '🔁',
    one: '🔂'
  }
  return icons[playerStore.repeatMode] || '🔁'
})

const loadStats = async () => {
  statsLoading.value = true
  try {
    const response = await api.get('/library/stats')
    stats.value = response.data
    try {
      localStorage.setItem(STATS_STORAGE_KEY, JSON.stringify(response.data))
    } catch (_) {}
  } catch (error) {
    console.error('Failed to load stats:', error)
  } finally {
    statsLoading.value = false
  }
}

const loadBotConfig = async () => {
  try {
    const response = await authApi.getConfig()
    if (response.data?.bot_username) {
      botUsername.value = response.data.bot_username
    }
  } catch (error) {
    console.error('Failed to load bot config:', error)
  }
}

const refreshStatus = async () => {
  await authStore.fetchStatus()
}

const loadPrivacySettings = async () => {
  try {
    const response = await api.get('/auth/privacy')
    privacySettings.value = response.data
  } catch (error) {
    console.error('Failed to load privacy settings:', error)
  }
}

const updatePrivacy = async (field, value) => {
  try {
    await api.put('/auth/privacy', { [field]: value })
    if (field === 'hide_telegram_id' && authStore.user) {
      authStore.user.hide_telegram_id = value
    }
  } catch (error) {
    console.error('Failed to update privacy:', error)
    // Revert on error
    privacySettings.value[field] = !value
  }
}


const toggleRepeat = () => {
  const modes = ['none', 'all', 'one']
  const currentIndex = modes.indexOf(playerStore.repeatMode)
  playerStore.repeatMode = modes[(currentIndex + 1) % modes.length]
}

const logout = async () => {
  // Stop playback before logout
  playerStore.stop()
  authStore.logout()
  // Force full page reload to clear all store states
  window.location.href = '/login'
}

const cachedAudioStats = getCachedAudioStats()
const cacheStats = ref({
  totalBytes: cachedAudioStats?.totalBytes || 0,
  trackCount: cachedAudioStats?.trackCount || 0,
  quotaBytes: 0,
  usageBytes: 0
})
const clearingCache = ref(false)

const cacheLimits = [
  { label: '500 МБ', value: 500 * 1024 * 1024 },
  { label: '1 ГБ', value: 1024 * 1024 * 1024 },
  { label: '2 ГБ', value: 2048 * 1024 * 1024 },
  { label: '5 ГБ', value: 5120 * 1024 * 1024 },
  { label: 'Без лимита', value: 0 },
]

const formatCacheLimit = (bytes) => {
  if (!bytes || bytes === 0) return 'Без ограничений'
  const gb = bytes / (1024 * 1024 * 1024)
  if (gb >= 1) return `${gb.toFixed(0)} ГБ`
  return `${(bytes / (1024 * 1024)).toFixed(0)} МБ`
}

const formatBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0 МБ'
  const mb = bytes / (1024 * 1024)
  if (mb < 1024) return `${mb.toFixed(1)} МБ`
  return `${(mb / 1024).toFixed(1)} ГБ`
}

const cacheFillPercent = computed(() => {
  if (!playerStore.cacheMaxBytes || playerStore.cacheMaxBytes === 0) {
    if (!cacheStats.value.quotaBytes) return 0
    return Math.min(100, Math.max(2, (cacheStats.value.totalBytes / cacheStats.value.quotaBytes) * 100))
  }
  if (cacheStats.value.totalBytes === 0) return 0
  return Math.min(100, Math.max(2, (cacheStats.value.totalBytes / playerStore.cacheMaxBytes) * 100))
})

const refreshCacheStats = async () => {
  try {
    cacheStats.value = await getCacheStats()
  } catch (e) {
    console.warn('Failed to get cache stats:', e)
  }
}

const handleClearCache = async () => {
  if (!confirm('Очистить весь локальный кэш треков?')) return
  clearingCache.value = true
  try {
    await clearAudioCache()
    localStorage.removeItem('tracks_cache')
    localStorage.removeItem('albums_cache')
    await refreshCacheStats()
  } catch (e) {
    console.error('Error clearing cache:', e)
  } finally {
    clearingCache.value = false
  }
}

// Watch dark mode toggle
watch(darkMode, (isDark) => {
  document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light')
  localStorage.setItem('theme', isDark ? 'dark' : 'light')
})

onMounted(() => {
  // Load data in parallel without blocking page rendering
  loadStats()
  loadBotConfig()
  loadPrivacySettings()
  refreshCacheStats()
  fetchScAccount()
  fetchSpAccount()
  
  // Load saved theme preference
  const savedTheme = localStorage.getItem('theme')
  darkMode.value = savedTheme !== 'light'
  
  const scrollToTargetSection = () => {
    const target = route.query.section || (route.hash ? route.hash.replace('#', '') : null)
    if (target) {
      setTimeout(() => {
        const el = document.getElementById(target)
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' })
          if (target !== 'profile') {
            el.classList.add('section-highlight')
            setTimeout(() => el.classList.remove('section-highlight'), 2200)
          }
        }
      }, 150)
    } else {
      const container = detectedScrollContainer || findScrollContainer(document.querySelector('.settings-view'))
      if (container && container !== window) {
        container.scrollTo({ top: 0, behavior: 'instant' })
      } else {
        window.scrollTo({ top: 0, behavior: 'instant' })
      }
    }
  }

  scrollToTargetSection()
  
  window.addEventListener('cache-updated', refreshCacheStats)
  window.addEventListener('reset-view-state', handleResetState)

  nextTick(() => {
    checkSectionFromHash()
    const targetEl = profileSectionRef.value || document.getElementById('profile') || document.querySelector('.settings-view')
    detectedScrollContainer = findScrollContainer(targetEl)
    if (detectedScrollContainer && detectedScrollContainer !== window) {
      detectedScrollContainer.addEventListener('scroll', onScroll, { passive: true })
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll, { passive: true })

    setTimeout(() => {
      updateActiveSectionOnScroll()
    }, 200)
  })
})

const profileSectionRef = ref(null)
let detectedScrollContainer = null
let scrollTicking = false

const findScrollContainer = (el) => {
  let parent = el?.parentElement
  while (parent) {
    const style = window.getComputedStyle(parent)
    if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
      return parent
    }
    parent = parent.parentElement
  }
  return window
}

const checkSectionFromHash = () => {
  const hash = route.hash ? route.hash.replace('#', '') : (route.query.section || '')
  if (['profile', 'stats', 'notifications', 'interface', 'playback', 'storage', 'cache', 'about'].includes(hash)) {
    uiStore.setSettingsSection('settings')
  } else if (['channel', 'soundcloud', 'import'].includes(hash)) {
    uiStore.setSettingsSection('import')
  }
}

const updateActiveSectionOnScroll = () => {
  const profileEl = profileSectionRef.value || document.getElementById('profile')
  if (!profileEl) return

  if (!detectedScrollContainer) {
    detectedScrollContainer = findScrollContainer(profileEl)
  }

  const isWindow = detectedScrollContainer === window || !detectedScrollContainer
  const containerTop = isWindow ? 0 : detectedScrollContainer.getBoundingClientRect().top
  const containerHeight = isWindow ? window.innerHeight : detectedScrollContainer.clientHeight
  const currentScrollTop = isWindow 
    ? (window.scrollY || document.documentElement.scrollTop) 
    : detectedScrollContainer.scrollTop

  // If near the very top of the page, import/integrations section is always active
  if (currentScrollTop < 60) {
    uiStore.setSettingsSection('import')
    return
  }

  const profileRect = profileEl.getBoundingClientRect()
  const profileTopRelativeToContainer = profileRect.top - containerTop

  // Threshold: when profile section reaches the upper portion of the viewport (<= 220px from container top or 35% of container height)
  const threshold = Math.min(220, containerHeight * 0.35)

  if (profileTopRelativeToContainer <= threshold) {
    uiStore.setSettingsSection('settings')
  } else {
    uiStore.setSettingsSection('import')
  }
}

const onScroll = () => {
  if (!scrollTicking) {
    requestAnimationFrame(() => {
      updateActiveSectionOnScroll()
      scrollTicking = false
    })
    scrollTicking = true
  }
}

watch([() => route.hash, () => route.query.section], () => {
  checkSectionFromHash()
  const target = route.query.section || (route.hash ? route.hash.replace('#', '') : null)
  if (target) {
    const el = document.getElementById(target)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      if (target !== 'profile') {
        el.classList.add('section-highlight')
        setTimeout(() => el.classList.remove('section-highlight'), 2200)
      }
    }
  } else {
    const container = detectedScrollContainer || findScrollContainer(document.querySelector('.settings-view'))
    if (container && container !== window) {
      container.scrollTo({ top: 0, behavior: 'smooth' })
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }
  setTimeout(updateActiveSectionOnScroll, 300)
})

onUnmounted(() => {
  if (detectedScrollContainer && detectedScrollContainer !== window) {
    detectedScrollContainer.removeEventListener('scroll', onScroll)
  }
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', onScroll)
  window.removeEventListener('cache-updated', refreshCacheStats)
  window.removeEventListener('reset-view-state', handleResetState)
})

// Обработчик сброса состояния
const handleResetState = (event) => {
  if (event.detail.route === '/settings') {
    const container = detectedScrollContainer || findScrollContainer(document.querySelector('.settings-view'))
    if (container && container !== window) {
      container.scrollTo({ top: 0, behavior: 'smooth' })
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
    uiStore.setSettingsSection('import')
  }
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════
   Settings View — Unified Card Architecture
   Uses design-system tokens: --sp-*, --r-*, --c-*
   ═══════════════════════════════════════════════ */

.settings-view {
  padding: var(--sp-6) var(--sp-4) var(--sp-12);
  max-width: 680px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.settings-header {
  margin-bottom: var(--sp-5);
}

.settings-header h1 {
  font-size: 26px;
  font-weight: 700;
  color: var(--c-text-1);
  letter-spacing: -0.5px;
  margin: 0;
  line-height: 1.2;
}

/* ─── Section Container & Headers ─── */
.settings-section {
  margin-bottom: var(--sp-5);
  width: 100%;
  transition: all 0.3s ease;
}

.settings-section.section-highlight {
  outline: 2px solid var(--c-accent, #1db954);
  border-radius: 12px;
  animation: section-pulse 2.2s ease-out;
}

@keyframes section-pulse {
  0% { box-shadow: 0 0 25px rgba(29, 185, 84, 0.7); }
  100% { box-shadow: none; }
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  margin-bottom: 8px;
  padding: 0 2px;
}

.section-header h2 {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
  line-height: 1.4;
}

/* ─── Status Pills ─── */
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: var(--r-full);
  background: rgba(255, 255, 255, 0.05);
  color: var(--c-text-3);
  border: 1px solid rgba(255, 255, 255, 0.04);
  line-height: 1.2;
  flex-shrink: 0;
}

.status-pill.connected {
  background: rgba(29, 185, 84, 0.12);
  color: #1db954;
  border-color: rgba(29, 185, 84, 0.25);
}

.status-pill.sc-status.connected {
  background: rgba(255, 85, 0, 0.12);
  color: #ff6600;
  border-color: rgba(255, 85, 0, 0.25);
}

.status-pill.sp-status.connected {
  background: rgba(29, 185, 84, 0.12);
  color: #1db954;
  border-color: rgba(29, 185, 84, 0.25);
}

/* ─── Unified Card Architecture ─── */
.settings-card {
  background: var(--c-bg-2);
  border-radius: var(--r-lg);
  border: 1px solid rgba(255, 255, 255, 0.04);
  box-shadow: 
    3px 3px 10px var(--sh-dark),
    -1px -1px 2px var(--sh-light);
  padding: 16px;
  width: 100%;
  box-sizing: border-box;
}

/* ─── Dividers ─── */
.setting-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.05);
  margin: 12px 0;
  width: 100%;
}

.card-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.05);
  margin: 14px 0;
  width: 100%;
}

/* ─── Setting Row (Toggle / Action Item) ─── */
.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  padding: 2px 0;
}

.setting-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  gap: 2px;
}

.setting-name {
  color: var(--c-text-1);
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
}

.setting-desc {
  color: var(--c-text-3);
  font-size: 12px;
  line-height: 1.4;
  margin: 0;
}

/* ─── Action Buttons ─── */
.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 9px 16px;
  border-radius: var(--r-md);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
  text-decoration: none;
  line-height: 1;
  white-space: nowrap;
}

.action-btn.primary {
  background: var(--c-accent);
  color: #000;
  box-shadow: 0 2px 8px rgba(29, 185, 84, 0.25);
}

.action-btn.primary:hover:not(:disabled) {
  background: var(--c-accent-light);
  transform: translateY(-1px);
}

.action-btn.primary:disabled {
  background: rgba(255, 255, 255, 0.06) !important;
  color: rgba(255, 255, 255, 0.35) !important;
  box-shadow: none;
  cursor: not-allowed;
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.06);
  color: var(--c-text-2);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.action-btn.secondary:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: var(--c-text-1);
}

.action-btn.danger-ghost {
  background: rgba(244, 67, 54, 0.08);
  color: #ff5555;
  border: 1px solid rgba(244, 67, 54, 0.2);
}

.action-btn.danger-ghost:hover:not(:disabled) {
  background: rgba(244, 67, 54, 0.16);
  border-color: rgba(244, 67, 54, 0.4);
}

.action-btn.danger-ghost:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.danger-soft {
  background: rgba(244, 67, 54, 0.08);
  color: #ff5555;
  border: 1px solid rgba(244, 67, 54, 0.25);
}

.action-btn.danger-soft:hover:not(:disabled) {
  background: rgba(244, 67, 54, 0.15);
  border-color: rgba(244, 67, 54, 0.4);
}

.action-btn.success-soft {
  background: rgba(29, 185, 84, 0.1);
  color: #1db954;
  border: 1px solid rgba(29, 185, 84, 0.25);
}

.action-btn.success-soft:hover {
  background: rgba(29, 185, 84, 0.18);
  border-color: rgba(29, 185, 84, 0.4);
}

/* ─── Toggle Switch ─── */
.toggle {
  position: relative;
  display: inline-flex;
  align-items: center;
  width: 44px;
  height: 26px;
  flex-shrink: 0;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
  position: absolute;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: var(--c-bg-4);
  border-radius: 13px;
  transition: background 0.2s ease;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.toggle-slider::before {
  position: absolute;
  content: '';
  height: 20px;
  width: 20px;
  left: 2px;
  bottom: 2px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

.toggle input:checked + .toggle-slider {
  background: var(--c-accent);
  border-color: var(--c-accent);
}

.toggle input:checked + .toggle-slider::before {
  transform: translateX(18px);
}

/* ═══════════════════════════════════════════════
   1. Backup Channel Section
   ═══════════════════════════════════════════════ */
.channel-card.not-connected {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
  border: 1px solid rgba(102, 126, 234, 0.25);
}

.channel-connected {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.channel-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.channel-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--c-accent);
  color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.channel-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 1px;
}

.channel-title {
  color: var(--c-text-1);
  font-weight: 600;
  font-size: 15px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.channel-username {
  color: var(--c-text-2);
  font-size: 13px;
}

.channel-features {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.feature-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(29, 185, 84, 0.12);
  color: var(--c-accent);
  padding: 5px 10px;
  border-radius: var(--r-full);
  font-size: 12px;
  font-weight: 500;
  line-height: 1;
  white-space: nowrap;
}

.channel-not-connected {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.channel-desc {
  color: var(--c-text-2);
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--c-text-1);
  font-size: 13px;
  line-height: 1.4;
}

.setup-steps {
  background: var(--c-bg-3);
  border-radius: var(--r-md);
  padding: 12px 14px;
}

.setup-steps h3 {
  color: var(--c-text-1);
  font-size: 13px;
  font-weight: 600;
  margin: 0 0 6px 0;
}

.setup-steps ol {
  padding-left: 18px;
  margin: 0;
  color: var(--c-text-2);
  font-size: 12px;
  line-height: 1.6;
}

.setup-steps strong {
  color: var(--c-accent);
}

.setup-steps code {
  background: var(--c-bg-4);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  color: var(--c-text-1);
  font-size: 11px;
}

.channel-refresh-btn {
  width: 100%;
  margin-top: 4px;
}

/* ═══════════════════════════════════════════════
   2. Service Shared Styles (SC & Spotify)
   ═══════════════════════════════════════════════ */
.service-desc {
  font-size: 13px;
  color: var(--c-text-2);
  line-height: 1.5;
  margin: 0 0 12px 0;
}

.service-loading-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px;
  background: var(--c-bg-3);
  border-radius: var(--r-md);
  color: var(--c-text-3);
  font-size: 13px;
}

.service-profile-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.service-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.service-avatar-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.service-user-details {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.service-user-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.service-user-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  text-decoration: none;
}

.service-user-link:hover {
  text-decoration: underline;
}

.service-actions-grid {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
}

.service-input-block {
  margin-top: 10px;
}

.service-input-label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: var(--c-text-3);
  margin-bottom: 6px;
}

.service-input-row {
  display: flex;
  gap: 8px;
  align-items: stretch;
}

.service-text-input {
  flex: 1;
  min-width: 0;
  background: var(--c-bg-1);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--r-md);
  padding: 9px 12px;
  color: var(--c-text-1);
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.service-text-input:focus {
  border-color: var(--c-accent);
}

.service-text-input:disabled {
  opacity: 0.6;
}

.connect-submit-btn {
  flex-shrink: 0;
}

.token-foldout {
  margin-top: 8px;
}

.token-foldout-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  color: var(--c-text-3);
  font-size: 12px;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}

.token-foldout-toggle:hover {
  color: var(--c-text-2);
}

.token-foldout-toggle .rotated {
  transform: rotate(180deg);
}

.token-foldout-body {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.token-input {
  font-family: monospace;
  font-size: 11px;
}

.token-hint {
  font-size: 11px;
  color: var(--c-text-3);
  line-height: 1.3;
}

.service-error-box {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: var(--r-sm);
  background: rgba(255, 68, 68, 0.1);
  border: 1px solid rgba(255, 68, 68, 0.25);
  color: #ff5555;
  font-size: 12px;
}

/* ─── SoundCloud Specific ─── */
.sc-card {
  border: 1px solid rgba(255, 85, 0, 0.18);
  background: linear-gradient(180deg, rgba(255, 85, 0, 0.04) 0%, var(--c-bg-2) 100%);
}

.sc-logo-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #ff5500;
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  border-radius: 4px;
  padding: 1px 4px;
  letter-spacing: 0.5px;
}

.sc-avatar {
  border: 2px solid #ff5500;
  box-shadow: 0 2px 8px rgba(255, 85, 0, 0.3);
}

.sc-placeholder {
  background: rgba(255, 85, 0, 0.15);
  color: #ff5500;
}

.sc-link {
  color: #ff6600;
}

.sc-likes-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.04);
  padding: 4px 10px;
  border-radius: var(--r-sm);
  border: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.sc-likes-num {
  font-size: 15px;
  font-weight: 700;
  color: #ff5500;
  line-height: 1.1;
}

.sc-likes-label {
  font-size: 10px;
  color: var(--c-text-3);
  text-transform: uppercase;
}

.sc-primary-btn {
  background: #ff5500 !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(255, 85, 0, 0.3) !important;
}

.sc-primary-btn:hover:not(:disabled) {
  background: #ff6611 !important;
}

/* ─── Spotify Specific ─── */
.sp-card {
  border: 1px solid rgba(29, 185, 84, 0.18);
  background: linear-gradient(180deg, rgba(29, 185, 84, 0.04) 0%, var(--c-bg-2) 100%);
}

.sp-icon {
  color: #1db954;
}

.sp-primary-btn {
  background: #1db954 !important;
  color: #000000 !important;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(29, 185, 84, 0.3) !important;
}

.sp-primary-btn:hover:not(:disabled) {
  background: #1ed760 !important;
}

.sp-exportify-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: rgba(29, 185, 84, 0.07);
  border: 1px solid rgba(29, 185, 84, 0.2);
  border-radius: var(--r-md);
  padding: 14px;
  margin-top: 10px;
  margin-bottom: 8px;
}

.sp-exportify-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sp-exportify-icon {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  background: rgba(29, 185, 84, 0.18);
  color: #1db954;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sp-exportify-texts {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.sp-exportify-title {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
  line-height: 1.3;
}

.sp-exportify-sub {
  font-size: 12px;
  color: var(--c-text-2);
  line-height: 1.3;
  margin-top: 2px;
}

.sp-exportify-actions {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
}

/* Spotify Connected Profile Row (Clean & Fixed!) */
.sp-profile-connected-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--r-md);
  margin-top: 12px;
}

.sp-profile-info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.sp-profile-avatar-wrap {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(29, 185, 84, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sp-profile-texts {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  flex-wrap: wrap;
}

.sp-profile-label {
  font-size: 13px;
  color: var(--c-text-3);
  white-space: nowrap;
}

.sp-profile-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.sp-unlink-btn {
  flex-shrink: 0;
  padding: 7px 12px;
  font-size: 12px;
}

.sp-input-block {
  margin-top: 12px;
}

/* ═══════════════════════════════════════════════
   4. Profile & Privacy Section
   ═══════════════════════════════════════════════ */
.profile-privacy-card {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.profile-header-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 4px 0;
}

.profile-avatar-block {
  position: relative;
  cursor: pointer;
  border-radius: 50%;
  width: 58px;
  height: 58px;
  flex-shrink: 0;
  transition: transform 0.15s ease;
}

.profile-avatar-block:hover {
  transform: scale(1.03);
}

.profile-avatar-visual {
  width: 58px;
  height: 58px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  color: #fff;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
  border: 2px solid rgba(255, 255, 255, 0.14);
}

.avatar-image-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.avatar-letter {
  font-size: 24px;
  font-weight: 800;
  line-height: 1;
  text-transform: uppercase;
}

.profile-avatar-hover-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
  color: #fff;
}

.profile-avatar-block:hover .profile-avatar-hover-ring {
  opacity: 1;
}

.profile-avatar-badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--c-bg-2, #242424);
  border: 2px solid var(--c-bg-1, #181818);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-2, #a7a7a7);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
  transition: all 0.15s ease;
}

.profile-avatar-block:hover .profile-avatar-badge {
  background: var(--c-accent, #1db954);
  color: #000;
}

.profile-meta-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  flex: 1;
}

.profile-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.profile-user-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.01em;
}

.view-profile-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  height: 24px;
  padding: 0 8px;
  border-radius: 12px;
  background: rgba(29, 185, 84, 0.1);
  color: var(--c-accent);
  border: 1px solid rgba(29, 185, 84, 0.25);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.view-profile-chip:hover {
  background: rgba(29, 185, 84, 0.2);
  border-color: rgba(29, 185, 84, 0.4);
  transform: translateY(-1px);
}

.profile-handle-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.profile-handle {
  font-size: 12px;
  color: var(--c-text-3);
  font-weight: 500;
}

.hidden-privacy-pill {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 1px 6px;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  font-size: 10px;
  color: var(--c-text-2);
  font-weight: 500;
}

.avatar-quick-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}

.avatar-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 26px;
  padding: 0 9px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-2);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.avatar-action-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: var(--c-text-1);
}

.avatar-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.avatar-action-btn.danger {
  color: #ff6b6b;
  background: rgba(244, 92, 92, 0.08);
  border-color: rgba(244, 92, 92, 0.18);
}

.avatar-action-btn.danger:hover:not(:disabled) {
  background: rgba(244, 92, 92, 0.16);
  border-color: rgba(244, 92, 92, 0.3);
  color: #ff5252;
}

/* ─── Custom Nickname Block ─── */
.profile-field-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 2px 0;
}

.field-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.field-title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.field-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1);
}

.field-hint {
  font-size: 11px;
  color: var(--c-text-3);
  margin: 0;
  line-height: 1.3;
}

.field-reset-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 6px;
  background: transparent;
  border: 1px solid rgba(255, 92, 92, 0.2);
  color: #ff6b6b;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.field-reset-link:hover:not(:disabled) {
  background: rgba(255, 92, 92, 0.1);
  border-color: rgba(255, 92, 92, 0.35);
  color: #ff5252;
}

.field-reset-link:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.nickname-field-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.nickname-input-box {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  min-width: 0;
}

.nickname-clean-input {
  width: 100%;
  height: 36px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--r-md, 8px);
  padding: 0 32px 0 12px;
  color: var(--c-text-1, #fff);
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: all 0.2s ease;
}

.nickname-clean-input:focus {
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--c-accent, #1db954);
  box-shadow: 0 0 0 1px rgba(29, 185, 84, 0.3);
}

.input-clear-btn {
  position: absolute;
  right: 8px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  border: none;
  color: var(--c-text-3);
  cursor: pointer;
  transition: all 0.15s ease;
}

.input-clear-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  color: var(--c-text-1);
}

.nickname-actions-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.profile-save-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 36px;
  padding: 0 14px;
  border-radius: var(--r-md, 8px);
  font-size: 12px;
  font-weight: 600;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

/* When disabled (not dirty or saving) */
.profile-save-btn:disabled {
  background: rgba(255, 255, 255, 0.04) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
  color: rgba(255, 255, 255, 0.3) !important;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.profile-save-btn:disabled svg {
  color: rgba(255, 255, 255, 0.3) !important;
}

/* When active/dirty */
.profile-save-btn.is-active:not(:disabled) {
  background: var(--c-accent, #1db954);
  border-color: var(--c-accent, #1db954);
  color: #000;
  box-shadow: 0 2px 10px rgba(29, 185, 84, 0.35);
}

.profile-save-btn.is-active:not(:disabled) svg {
  color: #000;
}

.profile-save-btn.is-active:not(:disabled):hover {
  background: var(--c-accent-light, #1ed760);
  border-color: var(--c-accent-light, #1ed760);
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(29, 185, 84, 0.45);
}

.profile-save-btn.is-active:not(:disabled):active {
  transform: translateY(0);
}

.profile-cancel-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--r-md, 8px);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--c-text-2);
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.profile-cancel-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: var(--c-text-1);
}

/* Privacy Subgroup */
.privacy-subgroup-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--c-text-3);
  padding: 2px 0 6px;
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px;
  background: transparent;
  border: 1px solid rgba(244, 67, 54, 0.25);
  border-radius: var(--r-md);
  color: var(--c-error);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 2px;
}

.logout-btn:hover {
  background: rgba(244, 67, 54, 0.08);
  border-color: rgba(244, 67, 54, 0.4);
}

/* ═══════════════════════════════════════════════
   5. Library Stats Grid
   ═══════════════════════════════════════════════ */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.stat-item {
  background: var(--c-bg-3);
  border-radius: var(--r-md);
  padding: 12px 8px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 76px;
  border: 1px solid rgba(255, 255, 255, 0.02);
}

.stat-value {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: var(--c-text-1);
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.stat-label {
  display: block;
  color: var(--c-text-3);
  font-size: 12px;
  margin-top: 3px;
  line-height: 1.2;
}

.stat-item.stat-skeleton {
  min-height: 76px;
}

.skeleton-stat-value {
  height: 24px;
  width: 50px;
  background: var(--c-bg-4);
  border-radius: var(--r-sm);
  animation: pulse-skeleton 1.5s ease-in-out infinite;
}

.skeleton-stat-label {
  height: 10px;
  width: 40px;
  background: var(--c-bg-4);
  border-radius: var(--r-xs);
  margin-top: 6px;
  animation: pulse-skeleton 1.5s ease-in-out infinite;
  animation-delay: 0.1s;
}

@keyframes pulse-skeleton {
  0%, 100% { opacity: 0.35; }
  50% { opacity: 0.75; }
}

/* ═══════════════════════════════════════════════
   6. Range Slider & Presets
   ═══════════════════════════════════════════════ */
.slider-setting-block {
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  width: 100%;
}

.slider-row-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  width: 100%;
}

.slider-label-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.scale-reset-btn {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: var(--r-xs, 4px);
  background: var(--c-bg-3);
  color: var(--c-text-2);
  border: 1px solid rgba(255, 255, 255, 0.08);
  cursor: pointer;
  transition: all 0.15s ease;
}

.scale-reset-btn:hover {
  color: var(--c-accent);
  background: var(--c-bg-4);
  border-color: var(--c-accent-glow);
}

.setting-value {
  color: var(--c-accent);
  font-weight: 600;
  font-size: 14px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.range-slider {
  width: 100%;
  height: 6px;
  background: var(--c-bg-4);
  border-radius: 3px;
  outline: none;
  -webkit-appearance: none;
  margin: 4px 0;
}

.range-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--c-accent);
  cursor: pointer;
  transition: transform 0.15s ease;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
}

.range-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

.range-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--c-accent);
  cursor: pointer;
  border: none;
}

.scale-presets-wrap {
  overflow-x: auto;
  width: 100%;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  padding: 2px 0;
}

.scale-presets-wrap::-webkit-scrollbar {
  display: none;
}

.scale-presets {
  display: flex;
  gap: 6px;
  width: 100%;
  min-width: 320px;
}

.scale-preset-chip {
  flex: 1;
  min-width: 36px;
  padding: 6px 0;
  text-align: center;
  border-radius: var(--r-sm);
  background: var(--c-bg-3);
  color: var(--c-text-2);
  border: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.scale-preset-chip:hover {
  background: var(--c-bg-4);
  color: var(--c-text-1);
}

.scale-preset-chip.active {
  background: var(--c-accent);
  color: #000000;
  font-weight: 600;
  border-color: var(--c-accent);
  box-shadow: 0 0 8px var(--c-accent-glow);
}

.scale-desc {
  margin-top: 2px;
}

/* ═══════════════════════════════════════════════
   7. PWA Section
   ═══════════════════════════════════════════════ */
.pwa-status-installed {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(29, 185, 84, 0.1);
  border: 1px solid rgba(29, 185, 84, 0.25);
  border-radius: var(--r-md);
}

.pwa-status-icon {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--c-accent);
  color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.pwa-status-title {
  display: block;
  font-weight: 600;
  color: var(--c-text-1);
  font-size: 14px;
}

.pwa-status-desc {
  display: block;
  font-size: 12px;
  color: var(--c-text-2);
  margin-top: 1px;
}

.pwa-install-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.pwa-install-btn {
  flex-shrink: 0;
}

/* ═══════════════════════════════════════════════
   8. Cache & Storage Section
   ═══════════════════════════════════════════════ */
.cache-storage-bar-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 4px 0 12px;
}

.cache-stats-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.cache-stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.cache-stat-item.align-right {
  align-items: flex-end;
  text-align: right;
}

.cache-stat-label {
  font-size: 11px;
  color: var(--c-text-3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.cache-stat-val {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text-1);
}

.cache-stat-count {
  font-size: 12px;
  font-weight: 400;
  color: var(--c-text-2);
}

.cache-progress-bar {
  width: 100%;
  height: 6px;
  background: var(--c-bg-4);
  border-radius: 3px;
  overflow: hidden;
}

.cache-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--c-accent) 0%, #00e676 100%);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.cache-actions-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  margin-top: 8px;
}

.view-downloaded-btn,
.clear-cache-btn {
  width: 100%;
  padding: 10px;
}

/* ═══════════════════════════════════════════════
   9. About Section
   ═══════════════════════════════════════════════ */
.about-card {
  text-align: center;
  padding: 18px;
}

.about-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0;
}

.about-ver {
  font-size: 12px;
  color: var(--c-accent);
  font-weight: 600;
  margin-left: 4px;
}

.about-desc {
  font-size: 12px;
  color: var(--c-text-3);
  margin: 4px 0 0 0;
}

/* ═══════════════════════════════════════════════
   10. Responsive Breakpoints
   ═══════════════════════════════════════════════ */
@media (max-width: 540px) {
  .settings-view {
    padding: var(--sp-4) 12px 100px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }

  .service-actions-grid {
    grid-template-columns: 1fr 1fr;
  }

  .sp-exportify-actions {
    grid-template-columns: 1fr;
  }

  .sp-profile-connected-row {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .sp-unlink-btn {
    width: 100%;
  }

  .pwa-install-card {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .pwa-install-btn {
    width: 100%;
  }
}

@media (max-width: 400px) {
  .service-actions-grid {
    grid-template-columns: 1fr;
  }

  .service-input-row {
    flex-direction: column;
  }

  .connect-submit-btn {
    width: 100%;
  }

  .sp-profile-name {
    max-width: 140px;
  }
}
</style>

