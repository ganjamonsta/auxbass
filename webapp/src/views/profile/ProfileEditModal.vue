<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="modelValue" class="modal-backdrop" @click="handleClose">
        <div class="edit-profile-modal" @click.stop>
          <div class="modal-header">
            <h3>Редактирование профиля</h3>
            <button class="modal-close-btn" @click="handleClose">
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
            <button class="btn-pill-secondary" @click="handleClose" :disabled="modalSaving">
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
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { authApi } from '@/api/client'
import apiCache from '@/utils/apiCache'
import { computeAvatarGradient } from './profileUtils'
import { Camera, X, Trash2 } from 'lucide-vue-next'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  user: { type: Object, default: null },
  userAvatar: { type: String, default: null },
  userId: { type: Number, default: 0 },
})

const emit = defineEmits(['update:modelValue', 'saved'])

const authStore = useAuthStore()
const uiStore = useUIStore()

// Local state
const editNickname = ref('')
const editAvatarUrl = ref(null)
const editHideTelegramId = ref(false)
const modalSaving = ref(false)
const modalFileInputRef = ref(null)
const pendingAvatarFile = ref(null)

const avatarGradientStyle = ref({})

// Reset form when modal opens
watch(() => props.modelValue, (show) => {
  if (show && props.user) {
    editNickname.value = props.user.custom_nickname || (authStore.user?.custom_nickname) || ''
    editAvatarUrl.value = props.userAvatar || null
    editHideTelegramId.value = props.user.hide_telegram_id ?? (authStore.user?.hide_telegram_id) ?? false
    pendingAvatarFile.value = null
    avatarGradientStyle.value = computeAvatarGradient(props.user.display_name || props.user.username)
  }
})

const handleClose = () => {
  if (modalSaving.value) return
  emit('update:modelValue', false)
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
    if (editHideTelegramId.value !== (props.user?.hide_telegram_id || false)) {
      await authApi.updatePrivacy({ hide_telegram_id: editHideTelegramId.value })
      if (authStore.user) {
        authStore.user.hide_telegram_id = editHideTelegramId.value
      }
    }

    // Invalidate caches & signal parent to reload
    apiCache.invalidateRelated('user', props.userId)
    emit('saved')
    emit('update:modelValue', false)
    uiStore.showToast('Профиль успешно обновлен', 'success')
  } catch (err) {
    console.error('Failed to save profile:', err)
    uiStore.showToast('Ошибка при сохранении профиля', 'error')
  } finally {
    modalSaving.value = false
  }
}
</script>

<style scoped>
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
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
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

.btn-pill-secondary {
  padding: 10px 24px;
  border-radius: var(--r-full, 9999px);
  background: var(--c-bg-3, #222);
  color: var(--c-text-1, #fff);
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
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

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
