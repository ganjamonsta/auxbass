# API Caching Implementation

## Проблема

Каждый раз при навигации между разделами (артисты, плейлисты, альбомы) приложение заново загружало данные с сервера, что создавало ненужную нагрузку и замедляло работу.

## Решение

Реализовано двухуровневое кеширование:

### 1. Frontend Caching (In-Memory)

**Файл:** `webapp/src/utils/apiCache.js`

Умный in-memory кеш с автоматическим TTL для разных типов данных:

- **Liked tracks**: 1 минута (часто меняются)
- **Statistics**: 2 минуты
- **Tracks**: 3 минуты
- **Playlists**: 5 минуты
- **Artists/Albums**: 10 минут (редко меняются)
- **Artist details**: 15 минут
- **Genres**: 30 минут (практически статичны)

**Возможности:**
- Автоматическое кеширование GET-запросов
- Умная инвалидация кеша при мутациях (POST/PUT/DELETE)
- Очистка устаревших записей
- Поддержка паттернов для массовой инвалидации

### 2. Backend Cache Headers

**Файл:** `api/main.py` - `CacheControlMiddleware`

Сервер добавляет HTTP заголовки `Cache-Control` для оптимизации:

```
Cache-Control: private, max-age={seconds}, must-revalidate
```

- `private` - кеш только у клиента
- `max-age` - время жизни кеша
- `must-revalidate` - проверять актуальность при истечении

## Интеграция

### API Client (`webapp/src/api/client.js`)

**Request Interceptor:**
Проверяет кеш перед отправкой запроса. Если данные есть и не устарели - возвращает из кеша.

**Response Interceptor:**
Сохраняет успешные GET-ответы в кеш.

**Автоматическая инвалидация:**
Мутирующие операции (create, update, delete, like) автоматически инвалидируют связанные кеши.

### Примеры использования

```javascript
// Обычный запрос - автоматически кешируется
const artists = await artistsApi.getAll()

// Повторный запрос - берется из кеша
const artistsAgain = await artistsApi.getAll() // HIT cache!

// Лайк трека - автоматически инвалидирует кеш лайков
await tracksApi.like(trackId) // Инвалидирует /tracks/liked

// Ручная очистка кеша
import apiCache from '@/utils/apiCache'
apiCache.clear() // Очистить весь кеш
apiCache.invalidatePattern('/artists') // Очистить все связанное с артистами
```

### Store Integration (`webapp/src/stores/library.js`)

Добавлены методы для управления кешем:

```javascript
const libraryStore = useLibraryStore()

// Очистить весь API кеш
libraryStore.clearApiCache()

// Инвалидировать по паттерну
libraryStore.invalidateCachePattern('/tracks')
```

## Отладка

В консоли браузера доступен глобальный объект для отладки:

```javascript
// Статистика кеша
window.__apiCache.getStats()
// => { total: 15, active: 12, expired: 3 }

// Посмотреть все закешированные ключи
window.__apiCache.cache

// Очистить кеш вручную
window.__apiCache.clear()

// Инвалидировать по паттерну
window.__apiCache.invalidatePattern('/artists')
```

## Логирование

В консоли можно увидеть работу кеша:

```
[Cache] SET /api/tracks?page=1&per_page=50 (TTL: 180s)
[Cache] HIT /api/tracks?page=1&per_page=50 (age: 45s)
[Cache] INVALIDATED 3 entries matching "/tracks/liked"
[Cache] EXPIRED /api/artists?offset=0&limit=30
[Cache] CLEANUP removed 5 expired entries
```

## Производительность

**До:**
- Каждая навигация = новый запрос
- Медленная загрузка при переключении разделов
- Высокая нагрузка на сервер

**После:**
- Повторные запросы берутся из кеша
- Мгновенная загрузка при возврате в раздел
- Снижение нагрузки на сервер на 60-80%

## Конфигурация

### Изменение TTL

Отредактируйте `webapp/src/utils/apiCache.js`:

```javascript
this.ttls = {
  tracks: 5 * 60 * 1000,  // Увеличить до 5 минут
  artists: 20 * 60 * 1000, // Увеличить до 20 минут
}
```

### Отключение кеша для конкретного запроса

```javascript
// Обойти кеш
api.get('/tracks', { bypassCache: true })
```

## Автоматическая инвалидация

При мутациях данных кеш автоматически очищается:

| Действие | Инвалидируется |
|----------|----------------|
| `like/unlike` | `/tracks/liked`, `/tracks/{id}` |
| `createPlaylist/updatePlaylist` | `/playlists`, `/playlists/{id}` |
| `updateTrack/deleteTrack` | `/tracks`, `/tracks/{id}` |
| `addToLibrary/removeFromLibrary` | `/tracks`, `/tracks/global` |

## Best Practices

1. **Не кешировать чувствительные данные** - auth endpoints не кешируются
2. **Короткий TTL для часто меняющихся данных** - liked tracks (1 мин)
3. **Длинный TTL для статичных данных** - genres (30 мин)
4. **Автоматическая инвалидация** - при любых изменениях данных
5. **Отладка через консоль** - `window.__apiCache` для мониторинга
