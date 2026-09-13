/**
 * useAppUpdate — управление обнаружением обновлений сервера и принудительной перезагрузкой интерфейса.
 * 
 * Обязанности:
 * 1. Сопоставление версии/хэша текущего бандла клиента и версии на сервере.
 * 2. Определение реального обновления (смена build_id после рестарта/деплоя).
 * 3. Реактивное состояние для плавающего баннера (updateAvailable, isUpdating).
 * 4. Функция forceAppRefresh: безопасная очистка Cache Storage, Service Worker
 *    и перезагрузка с bypass browser cache (без потери авторизации).
 */
import { ref, computed, readonly } from 'vue'

// Константа сборки клиента (инжектится Vite через define)
const CLIENT_BUILD_ID = typeof __APP_BUILD_ID__ !== 'undefined' ? __APP_BUILD_ID__ : null
const CLIENT_VERSION = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '1.0.0'
const CLIENT_BUILD_TIME = typeof __APP_BUILD_TIME__ !== 'undefined' ? __APP_BUILD_TIME__ : null
const CLIENT_COMMIT = typeof __APP_COMMIT__ !== 'undefined' ? __APP_COMMIT__ : null

// Singleton реактивное состояние
const clientBuildId = ref(CLIENT_BUILD_ID)
const serverBuildId = ref(null)
const serverVersion = ref(null)
const serverStartTime = ref(null)
const initialServerStartTime = ref(null)
const updateAvailable = ref(false)
const isUpdating = ref(false)
const lastCheckTime = ref(null)
const dismissedBuildId = ref(
  typeof sessionStorage !== 'undefined' 
    ? sessionStorage.getItem('tg_player_update_dismissed') 
    : null
)

let isInitialized = false
let lastFocusCheck = 0

/**
 * Обработать ответ от /api/health или /api/version
 * @param {Object} data - { build_id, version, server_start_time, git_commit, dist_hash }
 */
export function handleHealthResponse(data) {
  if (!data || typeof data !== 'object') return

  lastCheckTime.value = Date.now()

  if (data.version) {
    serverVersion.value = data.version
  }

  if (data.server_start_time) {
    serverStartTime.value = data.server_start_time
    if (!initialServerStartTime.value) {
      initialServerStartTime.value = data.server_start_time
    }
  }

  const sBuildId = data.build_id
  if (!sBuildId) return
  serverBuildId.value = sBuildId

  // Если clientBuildId не был задан (например, в dev), берем первый полученный
  if (!clientBuildId.value) {
    clientBuildId.value = sBuildId
    return
  }

  // В режиме разработки Vite HMR сам обновляет модули.
  // Разрешаем проверку только если запущен тест обновления
  if (import.meta.env.DEV && !window.__FORCE_UPDATE_CHECK__) {
    return
  }

  // Реальное обновление: build_id на сервере отличается от загруженного клиентом
  if (sBuildId !== clientBuildId.value) {
    if (dismissedBuildId.value !== sBuildId) {
      console.log(`[AppUpdate] New version detected! Client: ${clientBuildId.value} -> Server: ${sBuildId}`)
      updateAvailable.value = true
    }
  } else {
    // Если по какой-то причине они снова совпали
    updateAvailable.value = false
  }
}

/**
 * Выполнить ручной опрос версии с сервера
 */
export async function checkForUpdate() {
  try {
    const resp = await fetch(`/api/health?_t=${Date.now()}`, {
      method: 'GET',
      cache: 'no-store',
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    })
    if (resp.ok) {
      const data = await resp.json()
      handleHealthResponse(data)
      return data
    }
  } catch (e) {
    console.warn('[AppUpdate] Update check failed:', e)
  }
  return null
}

/**
 * Принудительное форс-обновление интерфейса:
 * 1. Очищает Cache Storage браузера
 * 2. Дерегистрирует устаревшие Service Workers
 * 3. Отправляет команду SKIP_WAITING/CLEAR_CACHE
 * 4. Перезагружает страницу с query-параметром ?_v=TIMESTAMP
 * (Авторизация и пользовательские данные в localStorage сохраняются!)
 */
export async function forceAppRefresh() {
  if (isUpdating.value) return
  isUpdating.value = true

  console.log('[AppUpdate] Initiating force refresh and cache flush...')

  try {
    // 1. Уведомление и снятие Service Worker
    if ('serviceWorker' in navigator) {
      try {
        const registrations = await navigator.serviceWorker.getRegistrations()
        for (const reg of registrations) {
          if (reg.active) {
            reg.active.postMessage({ type: 'CLEAR_CACHE' })
            reg.active.postMessage({ type: 'SKIP_WAITING' })
          }
          await reg.unregister()
          console.log('[AppUpdate] ServiceWorker unregistered:', reg.scope)
        }
      } catch (err) {
        console.warn('[AppUpdate] SW unregister error:', err)
      }
    }

    // 2. Очистка Cache Storage (кэш HTML, JS, CSS)
    if ('caches' in window) {
      try {
        const cacheNames = await caches.keys()
        await Promise.all(cacheNames.map(name => caches.delete(name)))
        console.log('[AppUpdate] All browser caches cleared successfully')
      } catch (err) {
        console.warn('[AppUpdate] Cache API clear error:', err)
      }
    }

    // Даем микро-паузу для завершения асинхронных операций хранилища
    await new Promise(resolve => setTimeout(resolve, 200))
  } catch (globalErr) {
    console.warn('[AppUpdate] Pre-reload cleanup error:', globalErr)
  }

  // 3. Форсированная перезагрузка с параметром обхода кэша
  try {
    const url = new URL(window.location.href)
    url.searchParams.set('_v', Date.now().toString())
    window.location.replace(url.toString())
  } catch (_) {
    window.location.reload(true)
  }

  // Fallback таймер на случай задержки replace
  setTimeout(() => {
    window.location.reload(true)
  }, 1000)
}

/**
 * Скрыть подсказку для текущей версии
 */
export function dismissUpdate() {
  updateAvailable.value = false
  if (serverBuildId.value) {
    dismissedBuildId.value = serverBuildId.value
    try {
      sessionStorage.setItem('tg_player_update_dismissed', serverBuildId.value)
    } catch (_) {}
  }
}

/**
 * Инициализация слушателей фокуса и видимости окна
 */
export function initAppUpdateListeners() {
  if (isInitialized || typeof window === 'undefined') return
  isInitialized = true

  const handleVisibilityOrFocus = () => {
    const now = Date.now()
    // Троттлинг проверок: не чаще чем раз в 15 секунд при фокусе
    if (now - lastFocusCheck < 15_000) return
    lastFocusCheck = now

    if (document.visibilityState === 'visible') {
      checkForUpdate()
    }
  }

  document.addEventListener('visibilitychange', handleVisibilityOrFocus)
  window.addEventListener('focus', handleVisibilityOrFocus)

  // Первоначальная проверка через 2 секунды после старта
  setTimeout(() => {
    checkForUpdate()
  }, 2000)

  // Dev-хелперы для ручного тестирования из консоли браузера
  if (typeof window !== 'undefined') {
    window.__SIMULATE_UPDATE__ = (fakeId = 'test-build-v999') => {
      window.__FORCE_UPDATE_CHECK__ = true
      handleHealthResponse({
        build_id: fakeId,
        version: '9.9.9-test',
        server_start_time: Math.floor(Date.now() / 1000)
      })
      console.log('[AppUpdate] Simulated update with build_id:', fakeId)
    }
    window.__FORCE_REFRESH__ = forceAppRefresh
  }
}

/**
 * Composable хук
 */
export function useAppUpdate() {
  return {
    clientBuildId: readonly(clientBuildId),
    serverBuildId: readonly(serverBuildId),
    serverVersion: readonly(serverVersion),
    serverStartTime: readonly(serverStartTime),
    clientVersion: CLIENT_VERSION,
    clientCommit: CLIENT_COMMIT,
    clientBuildTime: CLIENT_BUILD_TIME,
    updateAvailable: readonly(updateAvailable),
    isUpdating: readonly(isUpdating),
    lastCheckTime: readonly(lastCheckTime),
    checkForUpdate,
    forceAppRefresh,
    dismissUpdate,
    initAppUpdateListeners,
  }
}
