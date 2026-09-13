<template>
  <section id="profile" class="settings-section">
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
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Camera, ChevronRight, EyeOff, Trash2, RotateCcw, X, Check, Lock, LogOut } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import api from '@/api/client'

const router = useRouter()
const authStore = useAuthStore()
const playerStore = usePlayerStore()

const privacySettings = ref({
  hide_from_search: false,
  hide_profile: false,
  hide_telegram_id: false,
  notify_subscription: true,
})

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

const avatarGradient = computed(() => {
  const id = authStore.user?.id || 0
  const hue = (id * 137) % 360
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 60%, 45%) 0%, hsl(${(hue + 40) % 360}, 50%, 35%) 100%)`
  }
})

const goToMyProfile = () => {
  if (authStore.user?.id) {
    router.push(`/user/${authStore.user.id}`)
  }
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
    privacySettings.value[field] = !value
  }
}

const logout = async () => {
  playerStore.stop()
  authStore.logout()
  window.location.href = '/login'
}

onMounted(() => {
  loadPrivacySettings()
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

.setting-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.05);
  margin: 12px 0;
  width: 100%;
}

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

/* Profile specific styles */
.profile-header-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
}

.profile-avatar-block {
  position: relative;
  width: 68px;
  height: 68px;
  cursor: pointer;
  flex-shrink: 0;
}

.profile-avatar-visual {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 28px;
  font-weight: 600;
  overflow: hidden;
  position: relative;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.avatar-image-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-avatar-hover-ring {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
  color: #fff;
}

.profile-avatar-block:hover .profile-avatar-hover-ring {
  opacity: 1;
}

.profile-avatar-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 22px;
  height: 22px;
  background: var(--c-bg-2);
  border: 2px solid var(--c-bg-1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-2);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  pointer-events: none;
}

.profile-meta-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.profile-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 2px;
}

.profile-user-name {
  font-size: 18px;
  font-weight: 700;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.view-profile-chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-2);
  border: none;
  padding: 2px 8px;
  border-radius: var(--r-full);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.view-profile-chip:hover {
  background: rgba(255, 255, 255, 0.15);
  color: var(--c-text-1);
}

.profile-handle-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.profile-handle {
  font-size: 13px;
  color: var(--c-text-3);
}

.hidden-privacy-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  color: var(--c-accent);
  background: rgba(29, 185, 84, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}

.avatar-quick-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--c-bg-3);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--c-text-2);
  padding: 4px 10px;
  border-radius: var(--r-md);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.avatar-action-btn:hover:not(:disabled) {
  background: var(--c-bg-4);
  color: var(--c-text-1);
}

.avatar-action-btn.danger:hover:not(:disabled) {
  background: rgba(255, 77, 79, 0.1);
  color: #ff4d4f;
  border-color: rgba(255, 77, 79, 0.2);
}

.profile-field-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.field-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.field-title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.field-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text-1);
}

.field-hint {
  font-size: 12px;
  color: var(--c-text-3);
}

.field-reset-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--c-text-3);
  background: none;
  border: none;
  cursor: pointer;
}

.field-reset-link:hover {
  color: var(--c-text-1);
}

.nickname-field-row {
  display: flex;
  gap: 10px;
  align-items: stretch;
}

.nickname-input-box {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  background: var(--c-bg-3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--r-md);
  transition: all 0.2s;
}

.nickname-input-box:focus-within {
  border-color: rgba(29, 185, 84, 0.5);
  background: var(--c-bg-4);
  box-shadow: 0 0 0 2px rgba(29, 185, 84, 0.1);
}

.nickname-input-box.is-dirty {
  border-color: rgba(255, 171, 0, 0.5);
  background: rgba(255, 171, 0, 0.02);
}

.nickname-clean-input {
  flex: 1;
  background: transparent;
  border: none;
  padding: 10px 32px 10px 14px;
  color: var(--c-text-1);
  font-size: 14px;
  font-weight: 500;
  width: 100%;
}

.nickname-clean-input:focus {
  outline: none;
}

.input-clear-btn {
  position: absolute;
  right: 8px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--c-text-3);
  cursor: pointer;
  border-radius: 50%;
}

.input-clear-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--c-text-1);
}

.nickname-actions-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.profile-save-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 16px;
  height: 100%;
  min-height: 40px;
  background: var(--c-bg-3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-3);
  border-radius: var(--r-md);
  font-size: 13px;
  font-weight: 600;
  cursor: not-allowed;
  transition: all 0.2s;
}

.profile-save-btn.is-active {
  background: var(--c-accent);
  color: #000;
  border-color: var(--c-accent);
  cursor: pointer;
}

.profile-save-btn.is-active:hover {
  filter: brightness(1.1);
}

.profile-cancel-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 100%;
  min-height: 40px;
  background: var(--c-bg-3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-2);
  border-radius: var(--r-md);
  cursor: pointer;
}

.profile-cancel-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--c-text-1);
}

.privacy-subgroup-header {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--c-text-2);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  background: rgba(255, 77, 79, 0.1);
  border: 1px solid rgba(255, 77, 79, 0.2);
  color: #ff4d4f;
  border-radius: var(--r-md);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 16px;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: rgba(255, 77, 79, 0.15);
}

@media (max-width: 480px) {
  .nickname-field-row {
    flex-direction: column;
  }
  
  .nickname-actions-group {
    height: 40px;
  }
  
  .profile-save-btn {
    flex: 1;
  }
}
</style>
