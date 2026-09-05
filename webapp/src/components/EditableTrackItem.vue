<template>
  <BaseTrackItem
    :track="track"
    :index="index"
    :allTracks="allTracks"
    :showDragHandle="true"
    :showIndex="true"
    :draggable="true"
    :isDragging="isDragging"
    :isDragOver="isDragOver"
    @dragstart="$emit('dragstart', $event)"
    @dragend="$emit('dragend')"
    @dragover="$emit('dragover', $event)"
    @drop="$emit('drop', $event)"
  >
    <template #action>
      <div class="edit-item-actions">
        <!-- Reorder buttons for reliable touch / mobile reordering -->
        <button
          type="button"
          class="reorder-btn"
          :disabled="index === 0"
          @click.stop="$emit('moveUp', index)"
          title="Переместить выше"
        >
          <ChevronUp :size="16" />
        </button>
        <button
          type="button"
          class="reorder-btn"
          :disabled="isLast"
          @click.stop="$emit('moveDown', index)"
          title="Переместить ниже"
        >
          <ChevronDown :size="16" />
        </button>
        <button
          type="button"
          class="remove-btn"
          @click.stop="$emit('remove')"
          title="Убрать из плейлиста"
        >
          <X :size="16" />
        </button>
      </div>
    </template>
  </BaseTrackItem>
</template>

<script setup>
import BaseTrackItem from './BaseTrackItem.vue'
import { ChevronUp, ChevronDown, X } from 'lucide-vue-next'

defineProps({
  track: { type: Object, required: true },
  index: { type: Number, required: true },
  isDragging: Boolean,
  isDragOver: Boolean,
  isLast: Boolean,
  allTracks: { type: Array, default: () => [] }
})

defineEmits(['dragstart', 'dragend', 'dragover', 'drop', 'remove', 'moveUp', 'moveDown'])
</script>

<style scoped>
.edit-item-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.reorder-btn,
.remove-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
  background: var(--c-bg-2, rgba(255, 255, 255, 0.08));
  color: var(--c-text-2, #aaa);
}

.reorder-btn:hover:not(:disabled) {
  background: var(--c-accent, #6366f1);
  color: #000;
  transform: scale(1.05);
}

.reorder-btn:disabled {
  opacity: 0.25;
  cursor: not-allowed;
}

.remove-btn:hover {
  background: var(--c-error, #ef4444);
  color: #fff;
  transform: scale(1.05);
}

.remove-btn:active,
.reorder-btn:active:not(:disabled) {
  transform: scale(0.95);
}
</style>
