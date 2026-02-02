# Дизайн-система компонентов

## Neu-tab кнопки

Унифицированные neumorphic кнопки для табов и переключателей.

### Базовое использование

```vue
<div class="neu-tab-bar">
  <button class="neu-tab" :class="{ active: tab === 'first' }">
    <span class="neu-tab-content" data-text="Первый">Первый</span>
  </button>
  <button class="neu-tab" :class="{ active: tab === 'second' }">
    <span class="neu-tab-content" data-text="Второй">Второй</span>
  </button>
</div>
```

### С иконками

```vue
<div class="neu-tab-bar">
  <button class="neu-tab" :class="{ active: tab === 'albums' }">
    <Disc3 :size="16" />
    <span class="neu-tab-content" data-text="Альбомы">Альбомы</span>
  </button>
  <button class="neu-tab" :class="{ active: tab === 'playlists' }">
    <Folder :size="16" />
    <span class="neu-tab-content" data-text="Плейлисты">Плейлисты</span>
  </button>
</div>
```

### Почему `neu-tab-content`?

Обёртка `<span class="neu-tab-content" data-text="...">` предотвращает "прыгание" кнопки при смене `font-weight` между обычным (500) и жирным (600) состояниями. Атрибут `data-text` должен содержать тот же текст, что и содержимое span.

**Принцип работы:**
- `::after` псевдоэлемент резервирует место для жирного текста
- Он скрыт (`visibility: hidden`, `height: 0`), но занимает ширину
- Таким образом, кнопка всегда имеет ширину как для жирного текста

### Примеры использования в проекте

- **LibraryView** — переключатель типов контента (Треки/Альбомы/Артисты/Плейлисты)
- **CollectionsView** — переключатель табов (Альбомы/Плейлисты) и scope-switcher (Моя библиотека/Общая)
- **ArtistsView** — scope-switcher (Моя библиотека/Общая)

### Стили

Базовые стили находятся в `src/styles/design-system.css`:
- `.neu-tab-bar` — контейнер для кнопок
- `.neu-tab` — сама кнопка
- `.neu-tab-content` — обёртка для текста с anti-shift механизмом
- `.neu-tab.active` — активное состояние

### Кастомизация

Можно переопределить локально для конкретного использования:

```css
.my-custom-tabs .neu-tab {
  padding: 8px 16px; /* меньше padding */
}
```
