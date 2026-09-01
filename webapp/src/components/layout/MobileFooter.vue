<template>
  <MobilePlayerSheet
    v-bind="$attrs"
    :isExpanded="isExpanded"
    :currentTrack="currentTrack"
    :isPlaying="isPlaying"
    :loading="loading"
    :progress="progress"
    :duration="duration"
    :buffered="buffered"
    :isLiked="isLiked"
    :showNav="showNav"
    :navItems="navItems"
    @update:isExpanded="handleExpandedChange"
    @toggle-play="$emit('toggle-play')"
    @next-track="$emit('next-track')"
    @prev-track="$emit('prev-track')"
    @seek="$emit('seek', $event)"
    @set-volume="$emit('set-volume', $event)"
    @toggle-mute="$emit('toggle-mute')"
    @toggle-shuffle="$emit('toggle-shuffle')"
    @toggle-repeat="$emit('toggle-repeat')"
    @like="$emit('like')"
    @nav-click="$emit('nav-click', $event)"
    @reset-view="$emit('reset-view', $event)"
  />
</template>

<script setup>
import { ref, watch } from 'vue'
import MobilePlayerSheet from './MobilePlayerSheet.vue'

const props = defineProps({
  showPlayer: {
    type: Boolean,
    default: false
  },
  currentTrack: {
    type: Object,
    default: null
  },
  isPlaying: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  progress: {
    type: Number,
    default: 0
  },
  duration: {
    type: Number,
    default: 0
  },
  buffered: {
    type: Number,
    default: 0
  },
  isLiked: {
    type: Boolean,
    default: false
  },
  showNav: {
    type: Boolean,
    default: true
  },
  navItems: {
    type: Array,
    default: undefined
  }
})

const emit = defineEmits([
  'expand-player',
  'toggle-play',
  'next-track',
  'prev-track',
  'seek',
  'set-volume',
  'toggle-mute',
  'toggle-shuffle',
  'toggle-repeat',
  'like',
  'nav-click',
  'reset-view'
])

const isExpanded = ref(false)

const handleExpandedChange = (val) => {
  isExpanded.value = val
  if (val) {
    emit('expand-player')
  }
}
</script>

