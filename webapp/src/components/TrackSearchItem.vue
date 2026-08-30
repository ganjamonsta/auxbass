<template>
  <BaseTrackItem
    :track="track"
    :dimmed="isInPlaylist"
    :allTracks="[track]"
  >
    <template #action>
      <button 
        v-if="!isInPlaylist"
        class="action-btn add"
        @click="$emit('add', track)"
        :disabled="isAdding"
      >
        <span v-if="isAdding">...</span>
        <span v-else>+</span>
      </button>
      <button 
        v-else
        class="action-btn check"
        @click="$emit('remove', track)"
        :disabled="isRemoving"
      >
        <span v-if="isRemoving">...</span>
        <span v-else><Check :size="16" /></span>
      </button>
    </template>
  </BaseTrackItem>
</template>

<script setup>
import BaseTrackItem from './BaseTrackItem.vue'
import { Check } from 'lucide-vue-next'

defineProps({
  track: { type: Object, required: true },
  isInPlaylist: Boolean,
  isAdding: Boolean,
  isRemoving: Boolean
})

defineEmits(['add', 'remove'])
</script>

<style scoped>
.action-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--c-accent);
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

.action-btn:hover { transform: scale(1.1); }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.action-btn.check:hover { background: var(--c-error); color: #fff; }
</style>
