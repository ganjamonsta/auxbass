<template>
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
            :src="getCoverUrl(scAccount.avatar_url, CoverSize.SMALL)" 
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
          <div class="sc-stats-badges-box">
            <div class="sc-likes-badge" title="Количество лайков на SoundCloud">
              <span class="sc-likes-num">{{ scAccount.likes_count || 0 }}</span>
              <span class="sc-likes-label">лайков</span>
            </div>
            <div class="sc-likes-badge" title="Количество авторских треков на SoundCloud">
              <span class="sc-likes-num">{{ scAccount.tracks_count || 0 }}</span>
              <span class="sc-likes-label">треков</span>
            </div>
          </div>
        </div>

        <div class="service-actions-grid sc-actions-grid">
          <button class="action-btn primary sc-primary-btn" @click="goToSoundCloudLikes">
            <Heart :size="15" />
            <span>Лайки</span>
          </button>
          <button class="action-btn sc-secondary-btn" @click="goToSoundCloudTracks">
            <Music :size="15" />
            <span>Мои треки</span>
          </button>
          <button class="action-btn sc-secondary-btn" @click="goToSoundCloudPlaylists">
            <Folder :size="15" />
            <span>Плейлисты</span>
          </button>
          <button class="action-btn danger-ghost" :disabled="isDisconnectingSc" @click="handleDisconnectSc">
            <Unlink :size="15" />
            <span>Отвязать</span>
          </button>
        </div>

        <!-- SoundCloud Privacy Settings -->
        <div class="service-privacy-box">
          <div class="service-privacy-header">
            <Lock :size="13" />
            <span>Приватность в профиле</span>
          </div>
          
          <div class="setting-row mini-setting-row">
            <div class="setting-info">
              <span class="setting-name">Показывать SoundCloud в профиле</span>
              <span class="setting-desc">Отображать бейдж аккаунта и вкладку SoundCloud</span>
            </div>
            <label class="toggle">
              <input 
                type="checkbox" 
                :checked="scAccount.show_on_profile !== false" 
                @change="handleUpdateScPrivacy('show_on_profile', $event.target.checked)"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>

          <div class="setting-row mini-setting-row" v-if="scAccount.show_on_profile !== false">
            <div class="setting-info">
              <span class="setting-name">Показывать плейлисты</span>
              <span class="setting-desc">Другие пользователи смогут видеть и слушать ваши плейлисты</span>
            </div>
            <label class="toggle">
              <input 
                type="checkbox" 
                :checked="scAccount.show_playlists !== false" 
                @change="handleUpdateScPrivacy('show_playlists', $event.target.checked)"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>

          <div class="setting-row mini-setting-row" v-if="scAccount.show_on_profile !== false">
            <div class="setting-info">
              <span class="setting-name">Показывать авторские треки и релизы</span>
              <span class="setting-desc">Ваши загруженные треки будут видны во вкладке профиля</span>
            </div>
            <label class="toggle">
              <input 
                type="checkbox" 
                :checked="scAccount.show_tracks !== false" 
                @change="handleUpdateScPrivacy('show_tracks', $event.target.checked)"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
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
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Check, Heart, Music, Folder, Unlink, Lock, Radio, ExternalLink, Key, ChevronDown, AlertCircle } from 'lucide-vue-next'
import { useExternalAccountsStore } from '@/stores/externalAccounts'
import { useUIStore } from '@/stores/ui'
import { getCoverUrl, CoverSize } from '@/utils'

const router = useRouter()
const externalAccountsStore = useExternalAccountsStore()
const uiStore = useUIStore()

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

const handleUpdateScPrivacy = async (field, value) => {
  try {
    await externalAccountsStore.updatePrivacy('soundcloud', { [field]: value })
    uiStore.toast?.success('Настройки сохранены', 'Приватность SoundCloud обновлена')
  } catch (err) {
    console.error('Failed to update SoundCloud privacy:', err)
    uiStore.toast?.error('Ошибка', 'Не удалось обновить настройки приватности')
  }
}

const goToSoundCloudLikes = () => {
  router.push({ path: '/search', query: { tab: 'soundcloud', mode: 'likes' } })
}

const goToSoundCloudTracks = () => {
  router.push({ path: '/search', query: { tab: 'soundcloud', mode: 'tracks' } })
}

const goToSoundCloudPlaylists = () => {
  router.push({ path: '/search', query: { tab: 'soundcloud', mode: 'playlists' } })
}

onMounted(() => {
  fetchScAccount()
})
</script>

<style scoped>
.settings-section {
  margin-bottom: var(--sp-5);
  width: 100%;
  transition: all 0.3s ease;
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

.status-pill.sc-status.connected {
  background: rgba(255, 85, 0, 0.12);
  color: #ff6600;
  border-color: rgba(255, 85, 0, 0.25);
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
  padding: 1px 5px;
  line-height: 1.2;
}

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

.service-loading-box {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--c-text-2);
  font-size: 14px;
  padding: 10px 0;
}

.service-profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.service-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.1);
}

.service-avatar-placeholder {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-3);
  border: 2px solid rgba(255, 255, 255, 0.1);
}

.service-avatar.sc-avatar {
  border-color: rgba(255, 85, 0, 0.3);
}

.service-avatar-placeholder.sc-placeholder {
  background: rgba(255, 85, 0, 0.1);
  color: #ff5500;
  border-color: rgba(255, 85, 0, 0.2);
}

.service-user-details {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.service-user-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--c-text-1);
}

.service-user-link {
  font-size: 13px;
  color: var(--c-text-2);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
}

.service-user-link:hover {
  text-decoration: underline;
}

.service-user-link.sc-link:hover {
  color: #ff5500;
}

.sc-stats-badges-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-end;
}

.sc-likes-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--c-bg-3);
  padding: 4px 10px;
  border-radius: var(--r-md);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.sc-likes-num {
  font-size: 14px;
  font-weight: 700;
  color: var(--c-text-1);
}

.sc-likes-label {
  font-size: 11px;
  color: var(--c-text-3);
  text-transform: uppercase;
}

.service-actions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 24px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: var(--r-full, 9999px);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.action-btn.primary {
  background: var(--c-accent);
  color: #000;
}

.action-btn.danger-ghost {
  background: transparent;
  color: #ff4d4f;
  border: 1px solid rgba(255, 77, 79, 0.3);
}

.action-btn.danger-ghost:hover {
  background: rgba(255, 77, 79, 0.1);
}

.action-btn.sc-primary-btn {
  background: #ff5500;
  color: #fff;
}

.action-btn.sc-primary-btn:hover {
  background: #e04a00;
}

.action-btn.sc-secondary-btn {
  background: rgba(255, 85, 0, 0.1);
  color: #ff5500;
  border: 1px solid rgba(255, 85, 0, 0.2);
}

.action-btn.sc-secondary-btn:hover {
  background: rgba(255, 85, 0, 0.2);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.service-privacy-box {
  background: var(--c-bg-3);
  border-radius: var(--r-md);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.service-privacy-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-2);
  margin-bottom: 4px;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  padding: 2px 0;
}

.setting-row.mini-setting-row {
  padding: 0;
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
}

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
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--c-bg-4);
  transition: .3s cubic-bezier(0.4, 0.0, 0.2, 1);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 2px;
  bottom: 2px;
  background-color: var(--c-text-2);
  transition: .3s cubic-bezier(0.4, 0.0, 0.2, 1);
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

input:checked + .toggle-slider {
  background-color: var(--c-accent);
  border-color: var(--c-accent);
}

input:checked + .toggle-slider:before {
  transform: translateX(20px);
  background-color: #fff;
}

.service-desc {
  font-size: 14px;
  color: var(--c-text-2);
  margin: 0 0 16px 0;
  line-height: 1.5;
}

.service-input-block {
  margin-bottom: 16px;
}

.service-input-label {
  display: block;
  font-size: 13px;
  color: var(--c-text-1);
  margin-bottom: 8px;
  font-weight: 500;
}

.service-input-row {
  display: flex;
  gap: 8px;
}

.service-text-input {
  flex: 1;
  background: var(--c-bg-3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--r-md);
  padding: 10px 14px;
  color: var(--c-text-1);
  font-size: 14px;
  transition: all 0.2s;
  min-width: 0;
}

.service-text-input:focus {
  outline: none;
  border-color: var(--c-accent);
  background: var(--c-bg-4);
}

.connect-submit-btn {
  min-width: 120px;
}

.token-foldout {
  background: var(--c-bg-3);
  border-radius: var(--r-md);
  overflow: hidden;
  margin-bottom: 16px;
}

.token-foldout-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: transparent;
  border: none;
  color: var(--c-text-2);
  font-size: 13px;
  cursor: pointer;
  text-align: left;
}

.token-foldout-toggle:hover {
  background: rgba(255, 255, 255, 0.02);
  color: var(--c-text-1);
}

.token-foldout-toggle svg.rotated {
  transform: rotate(180deg);
}

.token-foldout-toggle svg:last-child {
  margin-left: auto;
  transition: transform 0.2s;
}

.token-foldout-body {
  padding: 0 14px 14px;
}

.token-hint {
  display: block;
  font-size: 11px;
  color: var(--c-text-3);
  margin-top: 6px;
}

.service-error-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: rgba(255, 77, 79, 0.1);
  border-radius: var(--r-md);
  color: #ff4d4f;
  font-size: 13px;
}

@media (max-width: 540px) {
  .service-actions-grid {
    grid-template-columns: 1fr 1fr;
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
}
</style>
