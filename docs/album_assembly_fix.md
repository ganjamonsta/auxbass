# Диагностика и исправление сборки альбомов

## Выявленная проблема

На примере альбома **Cold Visions** (Bladee):
- В Last.fm: **30 треков**
- В сервисе: **16-19 треков**
- Все треки есть в библиотеке, но часть не обогащена правильно

### Причины проблемы

1. **Треки с (feat. X) не находятся в Deezer/Last.fm напрямую**
   - Пример: "YUNG SHERMAN (feat. Yung Sherman)" - Deezer не находит
   - Пример: "ONE SECOND (feat. Yung Lean)" - Last.fm возвращает `album: None`

2. **Некоторые треки сопоставляются с неправильными альбомами**
   - "RED CROSS" → "Crest" (вместо Cold Visions)
   - "PM2" → "Eversince" (вместо Cold Visions)
   - "NORMAL" → "I Miss Mixtapes" (вместо Cold Visions)

3. **Нет механизма "обратного поиска"**
   - Текущая логика: трек → Deezer/Last.fm → альбом
   - Отсутствует: проверка, входит ли трек в известные альбомы артиста

## Внесённые изменения

### 1. Новый компонент: `tracklist_matcher.py`
**Файл:** `bot/services/enrichment/tracklist_matcher.py`

Функционал:
- Получает список альбомов артиста из Last.fm
- Загружает треклист каждого альбома
- Ищет трек по fuzzy matching в треклистах
- Возвращает найденный альбом с обложкой и номером трека

```python
match = await album_tracklist_matcher.find_album_for_track(
    track_title="YUNG SHERMAN",
    artist="Bladee"
)
# Returns: {"album_name": "Cold Visions", "cover_url": "...", "track_number": 3}
```

### 2. Интеграция в процессор обогащения
**Файл:** `bot/services/enrichment/processor.py`

Добавлен fallback через tracklist_matcher:
```python
# FALLBACK: If still no album found, try tracklist matching
if not result.album_name and artist and lastfm_client.is_configured:
    tracklist_match = await self._enrich_from_tracklist(title, artist)
    if tracklist_match:
        result.album_name = tracklist_match.get("album_name")
        result.track_number = tracklist_match.get("track_number")
        ...
```

### 3. Диагностические скрипты
- `scripts/diagnose_cold_visions.py` - детальная диагностика альбома
- `scripts/fix_cold_visions.py` - исправление конкретного альбома
- `scripts/re_enrich_without_album.py` - переобогащение треков без альбома

## Использование

### Диагностика альбома
```bash
python scripts/diagnose_cold_visions.py
```

### Исправление Cold Visions
```bash
python scripts/fix_cold_visions.py
```

### Переобогащение треков без альбома
```bash
# Dry-run (симуляция)
python scripts/re_enrich_without_album.py --artist Bladee --dry-run

# Применить изменения
python scripts/re_enrich_without_album.py --artist Bladee --limit 50
```

## Логика работы (после исправлений)

```
Трек загружен
    ↓
1. Deezer search → album?
    ↓ нет
2. Last.fm track.getInfo → album?
    ↓ нет
3. [NEW] Tracklist matcher:
   - Получить альбомы артиста из Last.fm
   - Для каждого альбома загрузить треклист
   - Fuzzy match трека в треклистах
    ↓
Альбом найден → обогащение завершено
```

## Рекомендации

1. **Переобогатить существующие треки** без альбома
2. **Периодически запускать** `re_enrich_without_album.py` для новых треков
3. **Рассмотреть** кэширование треклистов альбомов в базе данных
