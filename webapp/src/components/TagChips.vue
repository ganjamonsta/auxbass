<template>
  <div v-if="visibleTags.length" class="tag-chips" :class="[size, { wrap: wrap }]">
    <button
      v-for="tag in visibleTags"
      :key="tag"
      class="tag-chip"
      :class="{ clickable: clickable }"
      @click.stop="clickable && $emit('tagClick', tag)"
    >
      <Hash v-if="showIcon && size !== 'xs'" :size="iconSize" />
      <span v-if="size === 'xs'" class="tag-hash">#</span>
      <span class="tag-text">{{ tag }}</span>
    </button>
    <span v-if="hiddenCount > 0" class="tag-overflow">+{{ hiddenCount }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Hash } from 'lucide-vue-next'

const props = defineProps({
  tags: {
    type: Array,
    default: () => []
  },
  /** Max tags to display. 0 = show all */
  max: {
    type: Number,
    default: 3
  },
  /** xs | sm | md */
  size: {
    type: String,
    default: 'sm'
  },
  /** Show # icon before tag */
  showIcon: {
    type: Boolean,
    default: true
  },
  /** Whether to wrap chips or stay in single line */
  wrap: {
    type: Boolean,
    default: false
  },
  /** Allow click events (for future tag-based playlists) */
  clickable: {
    type: Boolean,
    default: false
  }
})

defineEmits(['tagClick'])

const visibleTags = computed(() => {
  if (!props.tags?.length) return []
  if (props.max === 0) return props.tags
  return props.tags.slice(0, props.max)
})

const hiddenCount = computed(() => {
  if (!props.tags?.length || props.max === 0) return 0
  return Math.max(0, props.tags.length - props.max)
})

const iconSize = computed(() => {
  switch (props.size) {
    case 'xs': return 10
    case 'sm': return 12
    case 'md': return 14
    default: return 12
  }
})
</script>

<style scoped>
.tag-chips {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow: hidden;
}

.tag-chips.wrap {
  flex-wrap: wrap;
}

/* ─── Tag Chip Base ─── */
.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  border: none;
  cursor: default;
  font-family: inherit;
  white-space: nowrap;
  transition: all 0.15s ease;
  background: var(--c-bg-3, #222);
  color: var(--c-text-2, #b0b0b0);
  border-radius: var(--r-xl, 24px);
}

.tag-chip.clickable {
  cursor: pointer;
}

.tag-chip.clickable:hover {
  background: var(--c-bg-4, #2a2a2a);
  color: var(--c-text-1, #fff);
  box-shadow: 
    0 0 8px var(--c-accent-glow, rgba(229, 57, 53, 0.2));
}

.tag-chip.clickable:active {
  transform: scale(0.95);
}

/* ─── Size: xs (inline in track meta) ─── */
.tag-chips.xs .tag-chip {
  padding: 1px 6px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.2px;
  border-radius: var(--r-sm, 8px);
  background: var(--c-bg-4, #2a2a2a);
}

.tag-chips.xs {
  gap: 4px;
}

.tag-hash {
  opacity: 0.5;
  font-weight: 700;
}

/* ─── Size: sm (default, for full player / context menu) ─── */
.tag-chips.sm .tag-chip {
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

/* ─── Size: md (for album/detail views) ─── */
.tag-chips.md .tag-chip {
  padding: 5px 14px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

/* ─── Icon Color ─── */
.tag-chip :deep(svg) {
  color: var(--c-accent, #1db954);
  opacity: 0.7;
  flex-shrink: 0;
}

.tag-chip.clickable:hover :deep(svg) {
  opacity: 1;
}

/* ─── Overflow Counter ─── */
.tag-overflow {
  font-size: 10px;
  color: var(--c-text-3, #666);
  font-weight: 600;
  flex-shrink: 0;
}
</style>
