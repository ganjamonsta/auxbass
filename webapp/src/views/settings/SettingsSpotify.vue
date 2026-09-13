<template>
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

      <!-- Spotify Profile Connection Box -->
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

      <!-- Spotify Privacy Settings -->
      <div v-if="spAccount?.connected" class="service-privacy-box sp-privacy-box">
        <div class="service-privacy-header">
          <Lock :size="13" />
          <span>Приватность в профиле</span>
        </div>
        
        <div class="setting-row mini-setting-row">
          <div class="setting-info">
            <span class="setting-name">Показывать Spotify в профиле</span>
            <span class="setting-desc">Отображать бейдж профиля Spotify и вкладку</span>
          </div>
          <label class="toggle">
            <input 
              type="checkbox" 
              :checked="spAccount.show_on_profile !== false" 
              @change="handleUpdateSpPrivacy('show_on_profile', $event.target.checked)"
            />
            <span class="toggle-slider"></span>
          </label>
        </div>

        <div class="setting-row mini-setting-row" v-if="spAccount.show_on_profile !== false">
          <div class="setting-info">
            <span class="setting-name">Показывать сохранённые плейлисты</span>
            <span class="setting-desc">Другие пользователи смогут видеть импортированные плейлисты Spotify</span>
          </div>
          <label class="toggle">
            <input 
              type="checkbox" 
              :checked="spAccount.show_playlists !== false" 
              @change="handleUpdateSpPrivacy('show_playlists', $event.target.checked)"
            />
            <span class="toggle-slider"></span>
          </label>
        </div>
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
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Radio, Check, FileSpreadsheet, Upload, ExternalLink, Unlink, Lock, AlertCircle } from 'lucide-vue-next'
import { useExternalAccountsStore } from '@/stores/externalAccounts'
import { useTasksStore } from '@/stores/tasks'
import { useUIStore } from '@/stores/ui'

const externalAccountsStore = useExternalAccountsStore()
const tasksStore = useTasksStore()
const uiStore = useUIStore()

const spAccount = computed(() => externalAccountsStore.spAccount)
const loadingSpAccount = computed(() => externalAccountsStore.loadingSp)
const isConnectingSp = ref(false)
const isDisconnectingSp = ref(false)
const spUsernameInput = ref('')
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
    })
    spUsernameInput.value = ''
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

const handleUpdateSpPrivacy = async (field, value) => {
  try {
    await externalAccountsStore.updatePrivacy('spotify', { [field]: value })
    uiStore.toast?.success('Настройки сохранены', 'Приватность Spotify обновлена')
  } catch (err) {
    console.error('Failed to update Spotify privacy:', err)
    uiStore.toast?.error('Ошибка', 'Не удалось обновить настройки приватности')
  }
}

onMounted(() => {
  fetchSpAccount()
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

.sp-icon {
  color: #1db954;
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

.status-pill.sp-status.connected {
  background: rgba(29, 185, 84, 0.12);
  color: #1db954;
  border-color: rgba(29, 185, 84, 0.25);
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

.service-desc {
  font-size: 14px;
  color: var(--c-text-2);
  margin: 0 0 16px 0;
  line-height: 1.5;
}

.sp-exportify-box {
  background: var(--c-bg-3);
  border-radius: var(--r-md);
  padding: 16px;
  margin-bottom: 20px;
  border: 1px solid rgba(29, 185, 84, 0.15);
}

.sp-exportify-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.sp-exportify-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(29, 185, 84, 0.1);
  color: #1db954;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sp-exportify-texts {
  display: flex;
  flex-direction: column;
}

.sp-exportify-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text-1);
}

.sp-exportify-sub {
  font-size: 13px;
  color: var(--c-text-2);
  margin-top: 2px;
}

.sp-exportify-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.sp-profile-connected-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--c-bg-3);
  padding: 12px 14px;
  border-radius: var(--r-md);
  margin-bottom: 16px;
}

.sp-profile-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sp-profile-avatar-wrap {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(29, 185, 84, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
}

.sp-profile-texts {
  display: flex;
  flex-direction: column;
}

.sp-profile-label {
  font-size: 11px;
  color: var(--c-text-3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sp-profile-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
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
  text-decoration: none;
}

.action-btn.primary {
  background: var(--c-accent);
  color: #000;
}

.action-btn.secondary {
  background: var(--c-bg-3);
  color: var(--c-text-1);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.action-btn.danger-ghost {
  background: transparent;
  color: #ff4d4f;
  border: 1px solid rgba(255, 77, 79, 0.3);
}

.action-btn.danger-ghost:hover {
  background: rgba(255, 77, 79, 0.1);
}

.action-btn.sp-primary-btn {
  background: #1db954;
  color: #000;
}

.action-btn.sp-primary-btn:hover {
  background: #1ed760;
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

.service-error-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: rgba(255, 77, 79, 0.1);
  border-radius: var(--r-md);
  color: #ff4d4f;
  font-size: 13px;
  margin-top: 10px;
}

@media (max-width: 540px) {
  .sp-exportify-actions {
    grid-template-columns: 1fr;
  }
  .sp-profile-connected-row {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
}

@media (max-width: 400px) {
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
