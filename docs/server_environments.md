# 🌐 Работа с окружениями (Prod и Test)

Чтобы не ломать плеер пользователям во время разработки, мы используем два независимых контура на одном сервере.

---

## 🏗️ Схема работы

1. **Local (Твой комп)**: Пишешь код, тестируешь в [run_dev.bat](run_dev.bat).
2. **Staging (Сервер, Тест-бот)**: Код для проверки "в бою", но на отдельном боте.
3. **Production (Сервер, Основной бот)**: Стабильная версия для всех.

---

## 🌿 Работа с Git (Ветки)

Для разделения кода используем "ветки" (branches):

### 1. Как создать ветку для разработки
```bash
git checkout -b dev    # Создать ветку dev и перейти на неё
```

### 2. Типичный цикл разработки
1. Находясь в ветке `dev`, делаешь изменения.
2. Сохраняешь:
   ```bash
   git add .
   git commit -m "Добавил новую фичу"
   git push origin dev
   ```

### 3. Как перенести в Прод (Merge)
Когда потестил на тест-боте и всё работает:
```bash
git checkout main            # Переходим на главную ветку
git merge dev                # Вливаем изменения из dev в main
git push origin main         # Отправляем в облако
git checkout dev             # Возвращаемся в dev работать дальше
```

---

## 🖥️ Настройка Тест-сервера (один раз)

На сервере теперь будет две папки:
- `/opt/tg_player` (Прод)
- `/opt/tg_player_test` (Тест)

### Шаги на сервере:
1. Запусти скрипт настройки:
   ```bash
   bash deploy/setup_test_env.sh
   ```
2. Отредактируй `.env` в `/opt/tg_player_test/.env`:
   - Укажи `BOT_TOKEN` тестового бота.
   - Укажи `DATABASE_URL` (можно создать вторую БД `tg_player_test`).
3. Запусти сервисы:
   ```bash
   sudo systemctl start tg-player-api-test
   sudo systemctl start tg-player-bot-test
   ```

---

## 🚀 Деплой обновлений

### Обновить ТЕСТ (Staging):
```bash
cd /opt/tg_player_test
git pull origin dev
sudo systemctl restart tg-player-api-test tg-player-bot-test
```

### Обновить ПРОД (Production):
```bash
cd /opt/tg_player
git pull origin main
sudo systemctl restart tg-player-api tg-player-bot
```

---

## 🛠️ Шпаргалка по командам

| Действие | Команда |
| --- | --- |
| Где я сейчас? (ветка) | `git branch` |
| Уйти в дев | `git checkout dev` |
| Сохранить всё | `git add .` → `git commit -m "..."` |
| Отправить в облако | `git push origin dev` (или main) |
| Забрать из облака | `git pull origin dev` |
| Склеить ветки | `git merge dev` (находясь в main) |
