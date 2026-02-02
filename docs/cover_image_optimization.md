# Cover Image Size Optimization

## Problem

Cover images were loaded at full resolution (1000x1000 or 500x500) everywhere in the app, even for tiny thumbnails (40-50px). This caused:
- **Excessive network usage** - loading ~1MB images for 50px thumbnails
- **Slow page loads** - especially on lists with many tracks
- **Wasted bandwidth** - users downloading 100x more data than needed

## Solution

Created a `getCoverUrl(url, size)` utility that adapts Deezer cover URLs to appropriate sizes:

| Size Preset | Resolution | Use Case |
|-------------|------------|----------|
| `SMALL` | 120x120 | Track lists, queue items, sidebar |
| `MEDIUM` | 250x250 | Grid cards, playlist covers |
| `LARGE` | 500x500 | Detail page headers |
| `XL` | 1000x1000 | Full player, high-res displays |

### Deezer URL Format

Deezer provides covers at multiple sizes:
- `https://e-cdns-images.dzcdn.net/images/cover/{hash}/56x56-000000-80-0-0.jpg` (small)
- `https://e-cdns-images.dzcdn.net/images/cover/{hash}/120x120-000000-80-0-0.jpg`
- `https://e-cdns-images.dzcdn.net/images/cover/{hash}/250x250-000000-80-0-0.jpg` (medium)
- `https://e-cdns-images.dzcdn.net/images/cover/{hash}/500x500-000000-80-0-0.jpg` (big)
- `https://e-cdns-images.dzcdn.net/images/cover/{hash}/1000x1000-000000-80-0-0.jpg` (xl)

The utility replaces the size portion of the URL to get the appropriate resolution.

## Implementation

### Utility (`webapp/src/utils/formatters.js`)

```javascript
export const CoverSize = {
  SMALL: 'small',     // 120x120 - for tiny thumbnails, lists
  MEDIUM: 'medium',   // 250x250 - for grid cards
  LARGE: 'large',     // 500x500 - for detail headers
  XL: 'xl'            // 1000x1000 - for full player
}

export function getCoverUrl(url, size = CoverSize.MEDIUM) {
  if (!url) return null
  
  const sizeMap = {
    [CoverSize.SMALL]: '120x120',
    [CoverSize.MEDIUM]: '250x250',
    [CoverSize.LARGE]: '500x500',
    [CoverSize.XL]: '1000x1000'
  }
  
  const targetSize = sizeMap[size] || sizeMap[CoverSize.MEDIUM]
  
  if (url.includes('dzcdn.net/images/cover/')) {
    return url.replace(/\/\d+x\d+(-|$)/, `/${targetSize}$1`)
  }
  
  return url // Non-Deezer URLs returned as-is
}
```

### Usage

```vue
<template>
  <!-- Small thumbnail in track list -->
  <img :src="getCoverUrl(track.cover_url, CoverSize.SMALL)" />
  
  <!-- Medium size for grid cards -->
  <img :src="getCoverUrl(album.cover_url, CoverSize.MEDIUM)" />
  
  <!-- Large for detail page headers -->
  <img :src="getCoverUrl(album.cover_url, CoverSize.LARGE)" />
  
  <!-- XL for full player -->
  <img :src="getCoverUrl(track.cover_url, CoverSize.XL)" />
</template>

<script setup>
import { getCoverUrl, CoverSize } from '@/utils'
</script>
```

## Updated Components

### Mobile Components
- `TrackItem.vue` - SMALL (track list thumbnails)
- `FullPlayer.vue` - XL (full player cover)
- `PlaylistItem.vue` - MEDIUM (single), SMALL (collage)
- `PlaylistGridCard.vue` - SMALL (collage images)
- `AlbumGridCard.vue` - MEDIUM
- `ArtistGridCard.vue` - MEDIUM
- `ArtistCard.vue` - LARGE (header), SMALL (albums/playlists)
- `BaseTrackItem.vue` - SMALL

### Desktop Components
- `NowPlayingSidebar.vue` - XL (main cover), SMALL (queue)
- `DesktopPlayer.vue` - LARGE
- `CoverSection.vue` - XL
- `QueuePanel.vue` - SMALL
- `ArtistLibrary.vue` - SMALL
- `Sidebar.vue` - SMALL

### Views
- `AlbumDetailView.vue` - LARGE (header)
- `ArtistDetailView.vue` - LARGE (header), MEDIUM (album cards)
- `PlaylistDetailView.vue` - LARGE (single), SMALL (collage)
- `FriendsView.vue` - SMALL (tracks/albums)
- `CollectionsView.vue` - SMALL

## Estimated Savings

| Context | Before | After | Savings |
|---------|--------|-------|---------|
| Track list (50 items) | ~50 MB | ~1.5 MB | **97%** |
| Album grid (20 items) | ~20 MB | ~1.5 MB | **92%** |
| Playlist with collage | ~4 MB | ~120 KB | **97%** |

## Future Improvements

1. **srcset support** - `getCoverSrcSet()` function already prepared for responsive images
2. **WebP support** - Check if Deezer supports WebP format for further optimization
3. **Lazy loading** - Already using `loading="lazy"` on most images
4. **Cache headers** - Ensure proper browser caching of resized images
