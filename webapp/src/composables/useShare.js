import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { playerApi } from '@/api/client'

// Global singleton state so ShareModal can be controlled from anywhere
const isShareOpen = ref(false)
const isDownloading = ref(false)
const sharePayload = ref({
  type: 'playlist', // 'track' | 'playlist' | 'album' | 'user'
  id: null,
  title: '',
  subtitle: '',
  coverUrl: '',
  text: '',
})

export function useShare() {
  const authStore = useAuthStore()
  const uiStore = useUIStore()

  const getBotUsername = () => {
    let botUser = authStore.botUsername || authStore.appName
    const lower = (botUser || '').toLowerCase()
    if (!botUser || botUser === 'TG Player' || lower.includes('your_bot') || lower.includes('enter_')) {
      botUser = 'tg_player_bot'
    }
    return botUser.replace(/^@/, '').trim()
  }

  const getDeepLink = (type, id) => {
    const botUser = getBotUsername()
    const deepParam = `${type}_${id}`
    return `https://t.me/${botUser}?startapp=${deepParam}`
  }

  const getInlineQuery = (type, id) => {
    return `${type}:${id}`
  }

  /**
   * Open the Share Modal for an item
   */
  const openShare = ({ type, id, title = '', subtitle = '', coverUrl = '', text = '' }) => {
    sharePayload.value = {
      type,
      id,
      title,
      subtitle,
      coverUrl,
      text,
    }
    isShareOpen.value = true
  }

  const closeShare = () => {
    isShareOpen.value = false
  }

  /**
   * Primary action: Share to Telegram chat using Inline Query mode
   * Inside Telegram WebApp: calls Telegram.WebApp.switchInlineQuery
   * Outside Telegram: opens t.me share url or telegram link
   */
  const shareToTelegramChat = async (customPayload = null) => {
    const payload = customPayload || sharePayload.value
    const { type, id, title } = payload
    const botUser = getBotUsername()
    const query = getInlineQuery(type, id)

    // Check if running inside Telegram WebApp with switchInlineQuery support
    if (window.Telegram?.WebApp?.switchInlineQuery) {
      try {
        window.Telegram.WebApp.HapticFeedback?.impactOccurred?.('medium')
        window.Telegram.WebApp.switchInlineQuery(query, ['users', 'groups', 'channels'])
        closeShare()
        return
      } catch (e) {
        console.warn('Failed to call switchInlineQuery:', e)
      }
    }

    // Fallback for browser outside Telegram
    const deepLink = getDeepLink(type, id)
    const shareMessage = payload.text || (title ? `Послушай «${title}» в TG Player!` : 'Слушай в TG Player!')
    const tgShareUrl = `https://t.me/share/url?url=${encodeURIComponent(deepLink)}&text=${encodeURIComponent(shareMessage)}`

    if (window.Telegram?.WebApp?.openTelegramLink) {
      window.Telegram.WebApp.openTelegramLink(tgShareUrl)
      closeShare()
      return
    }

    window.open(tgShareUrl, '_blank')
    closeShare()
  }

  /**
   * Copy direct deep link to clipboard
   */
  const copyLink = async (customPayload = null) => {
    const payload = customPayload || sharePayload.value
    const { type, id } = payload
    const deepLink = getDeepLink(type, id)

    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.notificationOccurred('success')
    }

    if (navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(deepLink)
        uiStore.toast.success('Ссылка скопирована', 'Поделитесь ей с друзьями')
        closeShare()
        return
      } catch (e) {
        console.warn('Clipboard write failed:', e)
      }
    }

    prompt('Скопируйте ссылку:', deepLink)
    closeShare()
  }

  /**
   * Copy inline command (@bot type:id) to clipboard
   */
  const copyInlineCommand = async (customPayload = null) => {
    const payload = customPayload || sharePayload.value
    const { type, id } = payload
    const botUser = getBotUsername()
    const query = getInlineQuery(type, id)
    const cmd = `@${botUser} ${query}`

    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.notificationOccurred('success')
    }

    if (navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(cmd)
        uiStore.toast.success('Команда скопирована', `Вставьте «${cmd}» в любой чат`)
        closeShare()
        return
      } catch (e) {
        console.warn('Clipboard write failed:', e)
      }
    }

    prompt('Команда для инлайн-запроса:', cmd)
    closeShare()
  }

  /**
   * Share via native OS Web Share API or Telegram share url
   */
  const shareWeb = async (customPayload = null) => {
    const payload = customPayload || sharePayload.value
    const { type, id, title } = payload
    const deepLink = getDeepLink(type, id)
    const shareText = payload.text || (title ? `Послушай «${title}» в TG Player!` : 'TG Player')

    if (navigator.share) {
      try {
        await navigator.share({
          title: title || 'TG Player',
          text: shareText,
          url: deepLink,
        })
        closeShare()
        return
      } catch (e) {
        if (e.name !== 'AbortError') {
          console.warn('Web share failed:', e)
        }
      }
    }

    // Fallback
    const tgShareUrl = `https://t.me/share/url?url=${encodeURIComponent(deepLink)}&text=${encodeURIComponent(shareText)}`
    if (window.Telegram?.WebApp?.openTelegramLink) {
      window.Telegram.WebApp.openTelegramLink(tgShareUrl)
    } else {
      window.open(tgShareUrl, '_blank')
    }
    closeShare()
  }

  /**
   * Download item directly to the user's private chat with the bot
   */
  const downloadToTelegram = async (customPayload = null) => {
    const payload = customPayload || sharePayload.value
    const { type, id } = payload
    if (!id) return

    isDownloading.value = true
    try {
      if (type === 'track') {
        try {
          await playerApi.download(id)
          uiStore.toast.success('Отправлено', 'Трек отправлен вам в Telegram')
          closeShare()
          return
        } catch (err) {
          console.warn('Direct download API failed, trying bot deep link:', err)
        }
      }

      // Deep link to bot /start files_<type>_<id>
      const botUser = getBotUsername()
      const startParam = `files_${type}_${id}`
      const botUrl = `https://t.me/${botUser}?start=${startParam}`

      if (window.Telegram?.WebApp?.openTelegramLink) {
        window.Telegram.WebApp.openTelegramLink(botUrl)
      } else {
        window.open(botUrl, '_blank')
      }
      uiStore.toast.info('Переход в бота', 'Бот отправит файлы в диалог')
      closeShare()
    } catch (err) {
      console.error('Failed to download to Telegram:', err)
      uiStore.toast.error('Ошибка', 'Не удалось отправить файлы в Telegram')
    } finally {
      isDownloading.value = false
    }
  }

  // Backward compatibility method
  const share = async (params) => {
    openShare(params)
  }

  return {
    isShareOpen,
    isDownloading,
    sharePayload,
    getBotUsername,
    getDeepLink,
    getInlineQuery,
    openShare,
    closeShare,
    shareToTelegramChat,
    downloadToTelegram,
    copyLink,
    copyInlineCommand,
    shareWeb,
    share,
  }
}
