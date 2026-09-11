import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'

// Global singleton state so ShareModal can be controlled from anywhere
const isShareOpen = ref(false)
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
    if (!botUser || botUser === 'TG Player') {
      botUser = 'tg_player_bot'
    }
    return botUser.replace(/^@/, '')
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
  const shareToTelegramChat = async () => {
    const { type, id, title } = sharePayload.value
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
    const shareMessage = sharePayload.value.text || (title ? `Послушай «${title}» в TG Player!` : 'Слушай в TG Player!')
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
  const copyLink = async () => {
    const { type, id } = sharePayload.value
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
   * Share via native OS Web Share API or Telegram share url
   */
  const shareWeb = async () => {
    const { type, id, title } = sharePayload.value
    const deepLink = getDeepLink(type, id)
    const shareText = sharePayload.value.text || (title ? `Послушай «${title}» в TG Player!` : 'TG Player')

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

  // Backward compatibility method
  const share = async (params) => {
    openShare(params)
  }

  return {
    isShareOpen,
    sharePayload,
    getBotUsername,
    getDeepLink,
    getInlineQuery,
    openShare,
    closeShare,
    shareToTelegramChat,
    copyLink,
    shareWeb,
    share,
  }
}
