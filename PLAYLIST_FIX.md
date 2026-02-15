# Playlist Creation Fix

## Проблема
При создании плейлиста через веб-интерфейс плейлист не появляется в библиотеке, хотя его можно увидеть в боте.

## Причина
В функции `create_playlist` в `api/routers/playlists.py` (строка 372-399) было **отсутствует явный commit** транзакции.

### До исправления:
```python
@router.post("", response_model=PlaylistResponse)
async def create_playlist(...):
    playlist = Playlist(...)
    db.add(playlist)
    await db.flush()  # ❌ Только flush, без commit!
    return PlaylistResponse(...)  # Ответ возвращается до commit
```

**Проблема в цепочке:**
1. Функция создает объект плейлиста в памяти
2. `flush()` получает ID, но не коммитит транзакцию
3. API возвращает ответ клиенту с ID
4. Веб-интерфейс пытается загрузить плейлист из БД
5. Но данные еще не закоммичены → плейлист не видно в списке

## Решение
Добавлен явный `await db.commit()` после `flush()`:

```python
@router.post("", response_model=PlaylistResponse)
async def create_playlist(...):
    playlist = Playlist(...)
    db.add(playlist)
    await db.flush()
    await db.commit()  # ✅ Гарантирует, что данные в БД
    
    owner = await db.get(User, user.id)
    
    return PlaylistResponse(
        ...
        owner_id=owner.id,
        owner_name=owner.display_name,
        is_owner=True,
        is_subscribed=False,
        covers=[],  # ✅ Добавлены недостающие поля
    )
```

## Изменения

### Файл: `api/routers/playlists.py`
- ✅ Добавлен `await db.commit()` после создания плейлиста
- ✅ Добавлены недостающие поля в ответе:
  - `owner_id`, `owner_name`
  - `is_owner`, `is_subscribed` 
  - `covers` (пустой список вместо None)

## Результат
Теперь при создании плейлиста в веб-интерфейсе:
1. Плейлист гарантированно сохраняется в БД
2. Плейлист появляется в списке библиотеки
3. Поведение согласуется с ботом

## Тестирование
Создан файл `test_playlist_creation.py` для ручного тестирования создания плейлистов.

Чтобы тестировать:
```bash
# 1. Запустить API и базу данных
python -m uvicorn api.main:app --reload

# 2. В отдельном терминале запустить тест (заменить TOKEN на реальный)
python test_playlist_creation.py
```
