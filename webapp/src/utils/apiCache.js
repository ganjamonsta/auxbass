/**
 * API Response Cache Service
 * 
 * Provides in-memory caching for API responses with automatic expiration.
 * Helps reduce redundant API calls when navigating between sections.
 */

class ApiCache {
  constructor() {
    // In-memory cache with TTL
    this.cache = new Map()
    
    // Default cache durations (in milliseconds)
    this.ttls = {
      default: 5 * 60 * 1000,       // 5 minutes - generic data
      tracks: 3 * 60 * 1000,         // 3 minutes - track listings
      playlists: 5 * 60 * 1000,      // 5 minutes - playlists
      artists: 10 * 60 * 1000,       // 10 minutes - artists (rarely change)
      albums: 10 * 60 * 1000,        // 10 minutes - albums (rarely change)
      artistDetail: 15 * 60 * 1000,  // 15 minutes - artist details
      genres: 30 * 60 * 1000,        // 30 minutes - genres (rarely change)
      stats: 2 * 60 * 1000,          // 2 minutes - statistics
      liked: 1 * 60 * 1000,          // 1 minute - liked tracks (changes frequently)
    }
    
    // Start cleanup interval (every minute)
    this.startCleanup()
  }

  /**
   * Generate cache key from URL and params
   */
  generateKey(url, params = {}) {
    // Sort params to ensure consistent keys
    const sortedParams = Object.keys(params)
      .sort()
      .map(key => `${key}=${JSON.stringify(params[key])}`)
      .join('&')
    
    return sortedParams ? `${url}?${sortedParams}` : url
  }

  /**
   * Get TTL for specific endpoint
   */
  getTTL(url) {
    if (url.includes('/tracks/liked')) return this.ttls.liked
    if (url.includes('/tracks/global/stats')) return this.ttls.stats
    if (url.includes('/library/stats')) return this.ttls.stats
    if (url.includes('/tracks/genres')) return this.ttls.genres
    if (url.includes('/tracks/artists')) return this.ttls.genres
    if (url.includes('/artists/') && url.includes('/info')) return this.ttls.artistDetail
    if (url.includes('/artists/') && url.includes('/tracks')) return this.ttls.artistDetail
    if (url.includes('/artists')) return this.ttls.artists
    if (url.includes('/albums')) return this.ttls.albums
    if (url.includes('/playlists')) return this.ttls.playlists
    if (url.includes('/tracks')) return this.ttls.tracks
    
    return this.ttls.default
  }

  /**
   * Store value in cache
   */
  set(key, value, customTTL = null) {
    const ttl = customTTL || this.getTTL(key)
    const expiresAt = Date.now() + ttl
    
    this.cache.set(key, {
      value,
      expiresAt,
      createdAt: Date.now()
    })
    
    console.log(`[Cache] SET ${key} (TTL: ${Math.round(ttl / 1000)}s)`)
  }

  /**
   * Get value from cache
   */
  get(key) {
    const entry = this.cache.get(key)
    
    if (!entry) {
      return null
    }
    
    // Check if expired
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key)
      console.log(`[Cache] EXPIRED ${key}`)
      return null
    }
    
    const age = Math.round((Date.now() - entry.createdAt) / 1000)
    console.log(`[Cache] HIT ${key} (age: ${age}s)`)
    return entry.value
  }

  /**
   * Check if key exists and is valid
   */
  has(key) {
    return this.get(key) !== null
  }

  /**
   * Delete specific key
   */
  delete(key) {
    console.log(`[Cache] DELETE ${key}`)
    return this.cache.delete(key)
  }

  /**
   * Clear all cache
   */
  clear() {
    console.log(`[Cache] CLEAR ALL (${this.cache.size} entries)`)
    this.cache.clear()
  }

  /**
   * Invalidate cache by pattern
   */
  invalidatePattern(pattern) {
    let count = 0
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key)
        count++
      }
    }
    if (count > 0) {
      console.log(`[Cache] INVALIDATED ${count} entries matching "${pattern}"`)
    }
  }

  /**
   * Invalidate related caches after data changes
   */
  invalidateRelated(type, id = null) {
    switch (type) {
      case 'track':
        this.invalidatePattern('/tracks')
        this.invalidatePattern('/tracks/liked')
        this.invalidatePattern('/tracks/global')
        this.invalidatePattern('/tracks/history')
        if (id) this.invalidatePattern(`/tracks/${id}`)
        break
        
      case 'playlist':
        this.invalidatePattern('/playlists')
        if (id) this.invalidatePattern(`/playlists/${id}`)
        break
        
      case 'artist':
        this.invalidatePattern('/artists')
        this.invalidatePattern('/tracks/artists')
        if (id) this.invalidatePattern(`/artists/${id}`)
        break
        
      case 'album':
        this.invalidatePattern('/albums')
        if (id) this.invalidatePattern(`/albums/${id}`)
        break
        
      case 'like':
        this.invalidatePattern('/tracks/liked')
        if (id) this.invalidatePattern(`/tracks/${id}`)
        break
        
      case 'stats':
        this.invalidatePattern('/stats')
        this.invalidatePattern('/library/stats')
        this.invalidatePattern('/tracks/global/stats')
        break
    }
  }

  /**
   * Cleanup expired entries
   */
  cleanup() {
    const now = Date.now()
    let count = 0
    
    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.cache.delete(key)
        count++
      }
    }
    
    if (count > 0) {
      console.log(`[Cache] CLEANUP removed ${count} expired entries`)
    }
  }

  /**
   * Start automatic cleanup
   */
  startCleanup() {
    // Run cleanup every minute
    this.cleanupInterval = setInterval(() => {
      this.cleanup()
    }, 60 * 1000)
  }

  /**
   * Stop automatic cleanup
   */
  stopCleanup() {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval)
      this.cleanupInterval = null
    }
  }

  /**
   * Get cache statistics
   */
  getStats() {
    const now = Date.now()
    let total = 0
    let expired = 0
    
    for (const [key, entry] of this.cache.entries()) {
      total++
      if (now > entry.expiresAt) {
        expired++
      }
    }
    
    return {
      total,
      active: total - expired,
      expired
    }
  }
}

// Create singleton instance
const apiCache = new ApiCache()

// Expose for debugging
if (typeof window !== 'undefined') {
  window.__apiCache = apiCache
}

export default apiCache
