# 🎨 Design System Guide

## Структура файлов CSS

```
webapp/src/
├── style.css                    # Корневые стили, legacy aliases
└── styles/
    ├── design-system.css        # ⭐ Унифицированная система (NEW)
    ├── index.css                # Главный импорт
    ├── app-layout.css           # Лейауты
    ├── app-header.css           # Хедер
    ├── app-components.css       # Компоненты
    ├── app-feed.css             # Лента/карточки
    ├── app-search.css           # Поиск
    ├── app-playlists.css        # Плейлисты
    ├── app-tabs-modal.css       # Табы и модалки
    └── app-animations.css       # Анимации
```

---

## 📦 Design Tokens

### Цвета

```css
/* Акцентные */
--c-accent          /* #E53935 - основной красный */
--c-accent-light    /* #FF6F60 */
--c-accent-dark     /* #AB000D */
--c-accent-glow     /* rgba для свечения */

--c-secondary       /* #00BCD4 - циан */
--c-secondary-glow

/* Поверхности (от тёмного к светлому) */
--c-bg-0            /* #0D0D0D - самый тёмный */
--c-bg-1            /* #141414 - базовый фон */
--c-bg-2            /* #1A1A1A - карточки */
--c-bg-3            /* #222222 - интерактивные */
--c-bg-4            /* #2A2A2A - hover */

/* Текст */
--c-text-1          /* #FFFFFF - основной */
--c-text-2          /* #B0B0B0 - вторичный */
--c-text-3          /* #666666 - muted */
--c-text-4          /* #444444 - disabled */
```

### Радиусы

```css
--r-xs              /* 4px */
--r-sm              /* 8px */
--r-md              /* 12px */
--r-lg              /* 16px */
--r-xl              /* 24px */
--r-full            /* 9999px (круг) */
```

### Тени

```css
--sh-dark           /* rgba(0, 0, 0, 0.5) */
--sh-light          /* rgba(255, 255, 255, 0.04) */
--sh-inset-dark     /* rgba(0, 0, 0, 0.6) */
--sh-inset-light    /* rgba(255, 255, 255, 0.03) */
```

### Отступы

```css
--sp-1 ... --sp-12  /* 4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px, 48px */
```

---

## 🧱 Готовые компоненты

### Поверхности

| Класс | Описание |
|-------|----------|
| `.neu-surface` | Выпуклая карточка |
| `.neu-well` | Вдавленная поверхность (инпуты) |
| `.neu-panel` | Плавающая панель (модалки) |
| `.neu-sheet` | Bottom sheet |
| `.neu-card` | Интерактивная карточка |
| `.neu-cover` | Обложка с тенью |
| `.neu-cover-lg` | Большая обложка |

### Кнопки

| Класс | Описание |
|-------|----------|
| `.neu-btn-icon` | Круглая иконка-кнопка |
| `.neu-btn-icon.sm/lg/xl` | Размеры |
| `.neu-btn-primary` | Основная кнопка (акцент) |
| `.neu-btn-secondary` | Вторичная кнопка |
| `.neu-btn-rubber` | Nokia-style резиновая |
| `.neu-touch` | Flat touchable |

### Формы

| Класс | Описание |
|-------|----------|
| `.neu-input` | Текстовое поле |
| `.neu-search` | Поисковая строка |
| `.neu-slider` | Range слайдер |
| `.neu-toggle` | Toggle switch |

### LCD/LED (Nokia style)

| Класс | Описание |
|-------|----------|
| `.neu-lcd` | LCD экран-контейнер |
| `.lcd-text` | Текст со свечением |
| `.neu-led-bar` | Прогресс из точек |
| `.neu-led-dot` | Отдельная LED точка |
| `.neu-led-dot.active` | Активная точка |

### Эквалайзер

```html
<div class="equalizer">
  <div class="equalizer-bar"></div>
  <div class="equalizer-bar"></div>
  <div class="equalizer-bar"></div>
</div>
```

---

## 🎭 Модификаторы состояния

| Класс | Описание |
|-------|----------|
| `.is-playing` | Активный трек |
| `.is-active` | Активный элемент |
| `.is-disabled` | Отключённый |
| `.is-loading` | Загрузка (спиннер) |
| `.glow-accent` | Свечение акцентом |

---

## ✨ Анимации

### Keyframes
- `spin` - вращение
- `pulse` - пульсация
- `equalizer` - эквалайзер
- `marquee` - бегущая строка

### Utility классы
- `.anim-spin` - крутилка
- `.anim-pulse` - пульсация
- `.anim-equalizer` - эквалайзер

### Transitions
- `.transition-fast` - 0.1s
- `.transition-base` - 0.15s
- `.transition-slow` - 0.25s

---

## 🔄 Миграция со старых классов

| Старый класс | Новый класс |
|--------------|-------------|
| `.neu-raised` | `.neu-surface` |
| `.neu-outset` | `.neu-surface` |
| `.neu-inset` | `.neu-well` |
| `.neu-btn-circle` | `.neu-btn-icon` |
| `.neu-icon-btn` | `.neu-btn-icon` |

### Legacy переменные

Все старые переменные (`--xm-*`, `--spotify-*`, `--neu-*`) теперь являются алиасами к новым токенам:

```css
--xm-accent → var(--c-accent)
--spotify-green → var(--c-accent)
--neu-radius-lg → var(--r-lg)
```

---

## 💡 Tailwind интеграция

В `tailwind.config.js` добавлены:

```js
// Цвета
bg-accent, bg-surface-2, text-text-1, ...

// Тени
shadow-neu-raised, shadow-neu-inset, shadow-neu-glow

// Радиусы
rounded-xs, rounded-md, rounded-lg, rounded-xl

// Отступы
p-sp-2, m-sp-4, gap-sp-3, ...
```

---

## 📝 Примеры использования

### Карточка трека
```html
<div class="neu-card">
  <div class="neu-cover">
    <img src="..." />
  </div>
  <div class="text-lg font-semibold truncate">Title</div>
  <div class="text-sm text-muted">Artist</div>
</div>
```

### Кнопка воспроизведения
```html
<button class="neu-btn-icon lg">
  <svg>...</svg>
</button>
```

### Поисковая строка
```html
<div class="neu-search">
  <svg class="search-icon">...</svg>
  <input type="text" placeholder="Search..." />
</div>
```

### Модальное окно
```html
<div class="neu-panel p-6">
  <h3 class="text-2xl font-bold">Title</h3>
  <input class="neu-input" />
  <div class="flex gap-3">
    <button class="neu-btn-secondary flex-1">Cancel</button>
    <button class="neu-btn-primary flex-1">Save</button>
  </div>
</div>
```
