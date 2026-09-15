<template>
  <Teleport to="body">
    <Transition name="fade">
      <div 
        v-if="isShareOpen" 
        class="share-overlay" 
        @click.self="closeShare"
        @contextmenu.prevent="closeShare"
      >
        <Transition name="scale">
          <div v-if="isShareOpen" class="share-dialog" @click.stop>
            <!-- Header -->
            <div class="share-header">
              <div class="header-title">
                <Share2 :size="18" class="header-icon" />
                <span>Поделиться</span>
              </div>
              <button class="close-btn" @click="closeShare" title="Закрыть">
                <X :size="20" />
              </button>
            </div>

            <!-- Preview Card -->
            <div class="preview-card">
              <div class="preview-cover" :style="coverStyle">
                <component :is="typeIcon" v-if="!sharePayload.coverUrl" :size="28" />
                <img 
                  v-else 
                  :src="sharePayload.coverUrl" 
                  alt="Cover" 
                  class="cover-img"
                  @error="onCoverError"
                />
              </div>
              <div class="preview-info">
                <span class="type-badge">{{ typeLabel }}</span>
                <div class="preview-title" :title="sharePayload.title">
                  {{ sharePayload.title || 'Без названия' }}
                </div>
                <div class="preview-subtitle" v-if="sharePayload.subtitle">
                  {{ sharePayload.subtitle }}
                </div>
              </div>
            </div>

            <!-- Actions List -->
            <div class="share-actions">
              <!-- Action 1: Send directly to TG Chat via bot -->
              <button class="share-btn primary-share-btn" @click="shareToTelegramChat">
                <div class="btn-icon-wrapper telegram-glow">
                  <Send :size="20" />
                </div>
                <div class="btn-content">
                  <span class="btn-title">Отправить в чат Telegram</span>
                  <span class="btn-desc">Сообщением от бота с плеером и кнопками</span>
                </div>
              </button>

              <!-- Action 2: Download directly to own Telegram -->
              <button v-if="sharePayload.type !== 'user'" class="share-btn download-share-btn" @click="downloadToTelegram" :disabled="isDownloading">
                <div class="btn-icon-wrapper download-glow">
                  <div v-if="isDownloading" class="btn-spinner"></div>
                  <CloudDownload v-else :size="20" />
                </div>
                <div class="btn-content">
                  <span class="btn-title">{{ downloadButtonTitle }}</span>
                  <span class="btn-desc">{{ downloadButtonDesc }}</span>
                </div>
              </button>

              <!-- Action 3: Copy link -->
              <button class="share-btn" @click="handleCopy">
                <div class="btn-icon-wrapper">
                  <Check v-if="copied" :size="20" class="copied-icon" />
                  <Copy v-else :size="20" />
                </div>
                <div class="btn-content">
                  <span class="btn-title">{{ copied ? 'Ссылка скопирована!' : 'Скопировать ссылку' }}</span>
                  <span class="btn-desc">{{ deepLinkPreview }}</span>
                </div>
              </button>

              <!-- Action 3: Native Web Share / Telegram Share -->
              <button class="share-btn" @click="shareWeb">
                <div class="btn-icon-wrapper">
                  <ExternalLink :size="20" />
                </div>
                <div class="btn-content">
                  <span class="btn-title">Поделиться ссылкой</span>
                  <span class="btn-desc">Через системное меню или Telegram</span>
                </div>
              </button>
            </div>

            <!-- Inline Command Hint Footer -->
            <div class="inline-hint" @click="copyInlineCommand" title="Нажмите, чтобы скопировать команду">
              <span class="hint-prefix">💡 Инлайн-запрос:</span>
              <code class="hint-code">@{{ botUsername }} {{ inlineCommand }}</code>
              <Copy :size="13" class="hint-copy-icon" />
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { 
  Share2, 
  X, 
  Send, 
  Copy, 
  Check, 
  ExternalLink, 
  Music, 
  Disc3, 
  Folder, 
  User,
  CloudDownload
} from 'lucide-vue-next'
import { useShare } from '@/composables/useShare'
import { useUIStore } from '@/stores/ui'

const { 
  isShareOpen, 
  isDownloading,
  sharePayload, 
  closeShare, 
  shareToTelegramChat, 
  downloadToTelegram,
  copyLink, 
  shareWeb, 
  getBotUsername, 
  getDeepLink 
} = useShare()

const uiStore = useUIStore()
const copied = ref(false)
const imgFailed = ref(false)

const botUsername = computed(() => getBotUsername())

const inlineCommand = computed(() => {
  const { type, id } = sharePayload.value
  return `${type}:${id}`
})

const deepLinkPreview = computed(() => {
  const { type, id } = sharePayload.value
  return `t.me/${botUsername.value}?startapp=${type}_${id}`
})

const typeLabel = computed(() => {
  switch (sharePayload.value.type) {
    case 'track': return 'ТРЕК'
    case 'playlist': return 'ПЛЕЙЛИСТ'
    case 'album': return 'АЛЬБОМ'
    case 'user': return 'ПРОФИЛЬ'
    default: return 'МЕДИА'
  }
})

const downloadButtonTitle = computed(() => {
  switch (sharePayload.value.type) {
    case 'track': return 'Скачать трек в Telegram'
    case 'playlist': return 'Скачать плейлист в Telegram'
    case 'album': return 'Скачать альбом в Telegram'
    default: return 'Скачать файлы в Telegram'
  }
})

const downloadButtonDesc = computed(() => {
  if (sharePayload.value.type === 'track') {
    return 'Прислать аудиофайл в личные сообщения с ботом'
  }
  return 'Прислать все треки в личные сообщения с ботом'
})

const typeIcon = computed(() => {
  switch (sharePayload.value.type) {
    case 'track': return Music
    case 'playlist': return Folder
    case 'album': return Disc3
    case 'user': return User
    default: return Music
  }
})

const coverStyle = computed(() => {
  return {
    background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9))',
  }
})

const onCoverError = () => {
  imgFailed.value = true
}

const handleCopy = async () => {
  await copyLink()
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}

const copyInlineCommand = async () => {
  const cmd = `@${botUsername.value} ${inlineCommand.value}`
  if (navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(cmd)
      uiStore.toast.success('Команда скопирована', `Вставьте «${cmd}» в любой чат`)
      return
    } catch (_) {}
  }
  prompt('Команда для инлайн-запроса:', cmd)
}
</script>

<style scoped>
.share-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.72);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 16px;
}

.share-dialog {
  background: var(--c-bg-2, #18191f);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--r-xl, 20px);
  width: 100%;
  max-width: 380px;
  overflow: hidden;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.6),
    0 0 0 1px rgba(255, 255, 255, 0.05);
  animation: modal-enter 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.share-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--c-text-1, #fff);
}

.header-icon {
  color: var(--c-accent-1, #3b82f6);
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--c-text-3, #94a3b8);
  cursor: pointer;
  padding: 4px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.close-btn:hover {
  color: var(--c-text-1, #fff);
  background: rgba(255, 255, 255, 0.08);
}

/* Preview Card */
.preview-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.preview-cover {
  width: 58px;
  height: 58px;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-3, #94a3b8);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-info {
  flex: 1;
  min-width: 0;
}

.type-badge {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  padding: 2px 7px;
  border-radius: 6px;
  background: rgba(59, 130, 246, 0.18);
  color: var(--c-accent-1, #60a5fa);
  margin-bottom: 4px;
}

.preview-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.preview-subtitle {
  font-size: 13px;
  color: var(--c-text-3, #94a3b8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

/* Actions List */
.share-actions {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.share-btn {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 14px;
  color: var(--c-text-1, #fff);
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
  width: 100%;
}

.share-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.12);
  transform: translateY(-1px);
}

.share-btn:active {
  transform: translateY(0);
}

/* Primary Telegram action */
.primary-share-btn {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.2), rgba(30, 64, 175, 0.1));
  border-color: rgba(59, 130, 246, 0.35);
}

.primary-share-btn:hover {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.3), rgba(30, 64, 175, 0.2));
  border-color: rgba(59, 130, 246, 0.5);
}

/* Download action button */
.download-share-btn {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(6, 182, 212, 0.08));
  border-color: rgba(16, 185, 129, 0.3);
}

.download-share-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.25), rgba(6, 182, 212, 0.15));
  border-color: rgba(16, 185, 129, 0.5);
}

.download-share-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.download-glow {
  background: linear-gradient(135deg, #10b981, #06b6d4);
  color: #fff;
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4);
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* @keyframes spin — defined in design-system.css */

.btn-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-1, #fff);
  flex-shrink: 0;
}

.telegram-glow {
  background: linear-gradient(135deg, #2563eb, #0284c7);
  color: #fff;
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
}

.copied-icon {
  color: #22c55e;
}

.btn-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.btn-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text-1, #fff);
}

.btn-desc {
  font-size: 11px;
  color: var(--c-text-3, #94a3b8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Inline Hint Footer */
.inline-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  margin: 0 16px 14px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px dashed rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  cursor: pointer;
  font-size: 11px;
  color: var(--c-text-3, #94a3b8);
  transition: all 0.15s;
}

.inline-hint:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(59, 130, 246, 0.4);
}

.hint-prefix {
  flex-shrink: 0;
}

.hint-code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: var(--c-accent-1, #60a5fa);
  background: rgba(59, 130, 246, 0.12);
  padding: 2px 6px;
  border-radius: 4px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hint-copy-icon {
  color: var(--c-text-3, #64748b);
  flex-shrink: 0;
}

@keyframes modal-enter {
  from {
    opacity: 0;
    transform: scale(0.94);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
