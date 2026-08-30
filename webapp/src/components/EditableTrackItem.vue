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
      <button class="remove-btn" @click="$emit('remove')" title="Удалить">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>
      </button>
    </template>
  </BaseTrackItem>
</template>

<script setup>
import BaseTrackItem from './BaseTrackItem.vue'

defineProps({
  track: { type: Object, required: true },
  index: { type: Number, required: true },
  isDragging: Boolean,
  isDragOver: Boolean,
  allTracks: { type: Array, default: () => [] }
})

defineEmits(['dragstart', 'dragend', 'dragover', 'drop', 'remove'])
</script>

<style scoped>
.remove-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--accent);
  border: none;
  color: #000;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
}

.remove-btn:hover { 
  background: var(--danger, #1db954); 
  color: #fff;
  transform: scale(1.1);
}

.remove-btn:active {
  transform: scale(0.95);
}

.remove-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}
</style>
