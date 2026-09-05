import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'

export function useShare() {
  const authStore = useAuthStore()
  const uiStore = useUIStore()

  const share = async ({ type, id, title = '', text = '' }) => {
    let botUser = authStore.botUsername || authStore.appName
    if (!botUser || botUser === 'TG Player') {
      botUser = 'tg_player_bot'
    }
    botUser = botUser.replace(/^@/, '')

    const deepParam = `${type}_${id}`
    const deepLink = `https://t.me/${botUser}?startapp=${deepParam}`
    const shareMessage = text || (title ? `Послушай «${title}» в TG Player` : 'Слушай в TG Player')
    const tgShareUrl = `https://t.me/share/url?url=${encodeURIComponent(deepLink)}&text=${encodeURIComponent(shareMessage)}`

    if (window.Telegram?.WebApp?.openTelegramLink) {
      try {
        window.Telegram.WebApp.openTelegramLink(tgShareUrl)
        return
      } catch (e) {
        console.warn('Failed to open telegram share link:', e)
      }
    }

    if (navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(deepLink)
        uiStore.toast.success('Ссылка скопирована', 'Поделитесь ей с друзьями')
        return
      } catch (e) {
        console.warn('Failed to write to clipboard:', e)
      }
    }

    prompt('Скопируйте ссылку:', deepLink)
  }

  return { share }
}
