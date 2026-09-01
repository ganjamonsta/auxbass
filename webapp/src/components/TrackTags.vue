<template>
  <div class="track-tags" v-if="hasTags || interactive">
    <!-- Tag list -->
    <div class="tags-list" :class="{ wrap: true }">
      <button
        v-for="tag in displayTags"
        :key="tag.id || tag.tag"
        class="tag-chip"
        :class="{
          voted: tag.voted_by_me,
          enrichment: tag.source === 'enrichment',
          'user-tag': tag.source === 'user',
        }"
        @click.stop="handleTagAction(tag)"
      >
        <Hash :size="12" />
        <span class="tag-text">{{ tag.tag }}</span>
        <span v-if="tag.vote_count > 0" class="tag-votes">{{ tag.vote_count }}</span>
        <Check v-if="tag.voted_by_me" :size="10" class="voted-icon" />
      </button>

      <!-- Overflow indicator -->
      <span v-if="hiddenCount > 0 && !expanded" class="tag-overflow" @click="expanded = true">
        +{{ hiddenCount }}
      </span>

      <!-- Add tag button -->
      <button
        v-if="interactive && !showInput"
        class="tag-chip add-tag-btn"
        @click.stop="showInput = true"
      >
        <Plus :size="12" />
        <span class="tag-text">тег</span>
      </button>
    </div>

    <!-- Add tag input -->
    <div v-if="showInput" class="tag-input-wrapper">
      <input
        ref="tagInputRef"
        v-model="newTag"
        type="text"
        class="tag-input"
        placeholder="Новый тег..."
        maxlength="50"
        @keydown.enter="submitTag"
        @keydown.escape="cancelInput"
        @blur="handleBlur"
      />
      <button
        v-if="newTag.trim()"
        class="tag-submit-btn"
        @mousedown.prevent="submitTag"
      >
        <Check :size="14" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { Hash, Plus, Check } from 'lucide-vue-next'
import { tracksApi } from '@/api/client'
import { useLibraryStore } from '@/stores/library'
import apiCache from '@/utils/apiCache'

const libraryStore = useLibraryStore()

const props = defineProps({
  /** Track ID for API calls */
  trackId: {
    type: Number,
    required: true,
  },
  /** Simple tags array (backward compat, used as fallback) */
  tags: {
    type: Array,
    default: () => [],
  },
  /** Enable interactive mode (voting, adding) */
  interactive: {
    type: Boolean,
    default: false,
  },
  /** Max tags to show before "show more" */
  max: {
    type: Number,
    default: 6,
  },
})

const emit = defineEmits(['tagClick', 'tagsUpdated'])

// State
const richTags = ref([])       // Full tag data from API: { id, tag, source, vote_count, voted_by_me }
const loading = ref(false)
const showInput = ref(false)
const newTag = ref('')
const tagInputRef = ref(null)
const expanded = ref(false)

// Computed
const hasTags = computed(() => {
  return richTags.value.length > 0 || props.tags?.length > 0
})

const displayTags = computed(() => {
  // Use rich tags if loaded, otherwise fall back to simple tags
  const source = richTags.value.length > 0
    ? richTags.value
    : (props.tags || []).map(t => ({
        id: null,
        tag: t,
        source: 'enrichment',
        vote_count: 0,
        voted_by_me: false,
      }))

  if (expanded.value || props.max === 0) return source
  return source.slice(0, props.max)
})

const hiddenCount = computed(() => {
  const total = richTags.value.length || props.tags?.length || 0
  if (expanded.value || props.max === 0) return 0
  return Math.max(0, total - props.max)
})

// Load rich tags when interactive or trackId changes
watch(
  () => [props.trackId, props.interactive],
  async ([trackId, interactive]) => {
    if (trackId && interactive) {
      await loadTags()
    } else {
      richTags.value = []
    }
  },
  { immediate: true }
)

// Focus input when shown
watch(showInput, async (val) => {
  if (val) {
    await nextTick()
    tagInputRef.value?.focus()
  }
})

// Methods
async function loadTags() {
  if (!props.trackId) return
  loading.value = true
  try {
    const { data } = await tracksApi.getTrackTags(props.trackId)
    richTags.value = data.tags || []
  } catch (e) {
    console.warn('[TrackTags] Failed to load tags:', e)
    richTags.value = []
  } finally {
    loading.value = false
  }
}

function handleTagAction(tag) {
  emit('tagClick', tag.tag)
}

function updateTagInList(tagId, updates) {
  const idx = richTags.value.findIndex(t => t.id === tagId)
  if (idx >= 0) {
    richTags.value[idx] = { ...richTags.value[idx], ...updates }
  }
}

async function submitTag() {
  const text = newTag.value.trim()
  if (!text || text.length < 2) return

  try {
    const { data } = await tracksApi.addTag(props.trackId, text)
    // Update or add in list
    const idx = richTags.value.findIndex(t => t.id === data.id)
    if (idx >= 0) {
      richTags.value[idx] = data
    } else {
      richTags.value.push(data)
    }
    newTag.value = ''
    showInput.value = false
    emit('tagsUpdated', richTags.value)

    // Invalidate API cache so subsequent fetches get fresh tags
    apiCache.invalidateRelated('track', props.trackId)
    apiCache.invalidatePattern('/tracks')

    // Notify all app views (VirtualTrackList, TrackItem, etc.) to immediately show the new tag
    const tagList = richTags.value.map(t => t.tag)
    await libraryStore.notifyTrackChange(props.trackId, { tags: tagList })
  } catch (e) {
    console.warn('[TrackTags] Add tag failed:', e?.response?.data?.detail || e)
  }
}

function cancelInput() {
  newTag.value = ''
  showInput.value = false
}

function handleBlur() {
  // Small delay to allow submit button click
  setTimeout(() => {
    if (!newTag.value.trim()) {
      showInput.value = false
    }
  }, 150)
}
</script>

<style scoped>
.track-tags {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tags-list {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

/* ─── Tag Chip ─── */
.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 10px;
  border: 1px solid transparent;
  cursor: pointer;
  font-family: inherit;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.3px;
  white-space: nowrap;
  transition: all 0.15s ease;
  background: var(--c-bg-3, #222);
  color: var(--c-text-2, #b0b0b0);
  border-radius: var(--r-xl, 24px);
}

.tag-chip:hover {
  background: var(--c-bg-4, #2a2a2a);
  color: var(--c-text-1, #fff);
}

.tag-chip:active {
  transform: scale(0.95);
}

/* Voted state */
.tag-chip.voted {
  background: var(--c-accent-bg, rgba(229, 57, 53, 0.12));
  color: var(--c-accent, #1db954);
  border-color: var(--c-accent-dim, rgba(229, 57, 53, 0.3));
}

.tag-chip.voted:hover {
  background: var(--c-accent-bg, rgba(229, 57, 53, 0.18));
}

/* Enrichment source indicator */
.tag-chip.enrichment {
  border-color: var(--c-bg-4, rgba(255, 255, 255, 0.06));
}

/* Icon color */
.tag-chip :deep(svg) {
  color: var(--c-accent, #1db954);
  opacity: 0.7;
  flex-shrink: 0;
}

.tag-chip.voted :deep(svg) {
  opacity: 1;
}

/* Vote count badge */
.tag-votes {
  font-size: 9px;
  font-weight: 700;
  color: var(--c-text-3, #666);
  margin-left: 2px;
  opacity: 0.8;
}

.tag-chip.voted .tag-votes {
  color: var(--c-accent, #1db954);
  opacity: 1;
}

/* Voted checkmark */
.voted-icon {
  margin-left: 1px;
  color: var(--c-accent, #1db954) !important;
  opacity: 1 !important;
}

/* Add tag button */
.add-tag-btn {
  background: transparent;
  border: 1px dashed var(--c-bg-4, rgba(255, 255, 255, 0.12));
  color: var(--c-text-3, #666);
}

.add-tag-btn:hover {
  border-color: var(--c-accent-dim, rgba(229, 57, 53, 0.4));
  color: var(--c-accent, #1db954);
  background: var(--c-accent-bg, rgba(229, 57, 53, 0.06));
}

.add-tag-btn :deep(svg) {
  color: currentColor;
  opacity: 1;
}

/* Overflow */
.tag-overflow {
  font-size: 10px;
  color: var(--c-text-3, #666);
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
}

.tag-overflow:hover {
  color: var(--c-text-2, #b0b0b0);
}

/* ─── Tag Input ─── */
.tag-input-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tag-input {
  flex: 1;
  padding: 5px 12px;
  border: 1px solid var(--c-bg-4, rgba(255, 255, 255, 0.12));
  border-radius: var(--r-xl, 24px);
  background: var(--c-bg-2, #1a1a1a);
  color: var(--c-text-1, #fff);
  font-family: inherit;
  font-size: 12px;
  outline: none;
  transition: border-color 0.15s ease;
}

.tag-input::placeholder {
  color: var(--c-text-3, #666);
}

.tag-input:focus {
  border-color: var(--c-accent-dim, rgba(229, 57, 53, 0.5));
}

.tag-submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%;
  background: var(--c-accent, #1db954);
  color: #fff;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.tag-submit-btn:hover {
  background: var(--c-accent-hover, #d32f2f);
  transform: scale(1.05);
}

.tag-submit-btn:active {
  transform: scale(0.95);
}
</style>
