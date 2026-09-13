<template>
  <div class="tracks-results-mode">
    <!-- Initial loading skeleton when searching tracks -->
    <div v-if="isTracksSearching && allTracksList.length === 0" class="search-skeleton-list">
      <TrackSkeleton v-for="n in 8" :key="n" />
    </div>

    <!-- Empty state when all track sources are exhausted -->
    <NoResultsBox 
      v-else-if="!isTracksSearching && !isFriendsLoading && !isGlobalLoading && allTracksList.length === 0" 
      text="Треки не найдены" 
      hint="Попробуйте изменить поисковый запрос или выбрать другой тег" 
    />

    <template v-else>
      <!-- 1. My Library Tracks -->
      <section v-if="libraryResults.length > 0" class="result-section">
        <div class="section-header">
          <span class="section-title">
            <Music :size="16" /> Моя библиотека
          </span>
          <span class="section-count">
            {{ libraryResults.length }}<template v-if="libraryTotal > libraryResults.length"> из {{ libraryTotal }}</template>
          </span>
        </div>
        <div class="track-results-list">
          <TrackItem
            v-for="(track, index) in libraryResults"
            :key="track.id"
            :track="track"
            :isPlaying="playerStore.currentTrack?.id === track.id"
            :isLiked="libraryStore.isTrackLiked(track.id)"
            :showAddToLibrary="false"
            :inLibrary="true"
            @click="$emit('playTrack', track, libraryResults, index)"
            @like="$emit('likeTrack', track)"
            @menu="(e) => $emit('menu', e, 'track', track)"
            @download="$emit('downloadTrack', track)"
            @hdNotice="$emit('hdNotice')"
          />
        </div>
        <button 
          v-if="hasMoreLibrary" 
          class="load-more-btn" 
          :disabled="isLibraryLoadingMore" 
          @click="$emit('loadMoreLibrary')"
        >
          <div v-if="isLibraryLoadingMore" class="spinner small"></div>
          <span>{{ isLibraryLoadingMore ? 'Загрузка...' : `Показать ещё (${libraryResults.length} из ${libraryTotal})` }}</span>
        </button>
      </section>

      <!-- 2. Friends' Tracks -->
      <section v-if="friendsResults.length > 0" class="result-section">
        <div class="section-header friends-section">
          <span class="section-title">
            <Users :size="16" /> У друзей
          </span>
          <span class="section-count">
            {{ friendsResults.length }}<template v-if="friendsTotal > friendsResults.length"> из {{ friendsTotal }}</template>
          </span>
        </div>
        <div class="track-results-list">
          <TrackItem
            v-for="(track, index) in friendsResults"
            :key="'friends-' + track.id"
            :track="track"
            :isPlaying="playerStore.currentTrack?.id === track.id"
            :isLiked="libraryStore.isTrackLiked(track.id)"
            :showAddToLibrary="true"
            :inLibrary="Boolean(track.in_library || libraryStore.isInLibrary(track.id))"
            @click="$emit('playTrack', track, allTracksList, index)"
            @like="$emit('likeTrack', track)"
            @menu="(e) => $emit('menu', e, 'track', track)"
            @download="$emit('downloadTrack', track)"
            @hdNotice="$emit('hdNotice')"
            @addToLibrary="$emit('addToLibrary', track)"
          />
        </div>
        <button 
          v-if="hasMoreFriends" 
          class="load-more-btn" 
          :disabled="isFriendsLoadingMore" 
          @click="$emit('loadMoreFriends')"
        >
          <div v-if="isFriendsLoadingMore" class="spinner small"></div>
          <span>{{ isFriendsLoadingMore ? 'Загрузка...' : 'Показать ещё у друзей' }}</span>
        </button>
      </section>

      <!-- Loading friends -->
      <div v-if="isFriendsLoading" class="section-loading-indicator">
        <div class="spinner small"></div>
        <span>Поиск у друзей...</span>
      </div>

      <!-- 3. Global Network Tracks -->
      <section v-if="globalResults.length > 0" class="result-section">
        <div class="section-header global-section">
          <span class="section-title">
            <Globe :size="16" /> Общая сеть
          </span>
          <span class="section-count">
            {{ globalResults.length }}<template v-if="globalTotal > globalResults.length"> из {{ globalTotal }}</template>
          </span>
        </div>
        <div class="track-results-list">
          <TrackItem
            v-for="(track, index) in globalResults"
            :key="'global-' + track.id"
            :track="track"
            :isPlaying="playerStore.currentTrack?.id === track.id"
            :isLiked="libraryStore.isTrackLiked(track.id)"
            :showAddToLibrary="true"
            :inLibrary="Boolean(track.in_library || libraryStore.isInLibrary(track.id))"
            @click="$emit('playTrack', track, allTracksList, index)"
            @like="$emit('likeTrack', track)"
            @menu="(e) => $emit('menu', e, 'track', track)"
            @download="$emit('downloadTrack', track)"
            @hdNotice="$emit('hdNotice')"
            @addToLibrary="$emit('addToLibrary', track)"
          />
        </div>
        <button 
          v-if="hasMoreGlobal" 
          class="load-more-btn" 
          :disabled="isGlobalLoadingMore" 
          @click="$emit('loadMoreGlobal')"
        >
          <div v-if="isGlobalLoadingMore" class="spinner small"></div>
          <span>{{ isGlobalLoadingMore ? 'Загрузка...' : 'Показать ещё в общей сети' }}</span>
        </button>
      </section>

      <!-- Loading global -->
      <div v-if="isGlobalLoading" class="section-loading-indicator">
        <div class="spinner small"></div>
        <span>Поиск в общей сети...</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { Music, Users, Globe } from 'lucide-vue-next'
import TrackItem from '@/components/TrackItem.vue'
import TrackSkeleton from '@/components/TrackSkeleton.vue'
import NoResultsBox from '@/components/NoResultsBox.vue'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'

const props = defineProps({
  isTracksSearching: { type: Boolean, required: true },
  allTracksList: { type: Array, required: true },
  
  libraryResults: { type: Array, required: true },
  libraryTotal: { type: Number, required: true },
  hasMoreLibrary: { type: Boolean, required: true },
  isLibraryLoadingMore: { type: Boolean, required: true },
  
  friendsResults: { type: Array, required: true },
  friendsTotal: { type: Number, required: true },
  hasMoreFriends: { type: Boolean, required: true },
  isFriendsLoadingMore: { type: Boolean, required: true },
  isFriendsLoading: { type: Boolean, required: true },
  
  globalResults: { type: Array, required: true },
  globalTotal: { type: Number, required: true },
  hasMoreGlobal: { type: Boolean, required: true },
  isGlobalLoadingMore: { type: Boolean, required: true },
  isGlobalLoading: { type: Boolean, required: true }
})

const emit = defineEmits([
  'playTrack',
  'likeTrack',
  'menu',
  'downloadTrack',
  'hdNotice',
  'addToLibrary',
  'loadMoreLibrary',
  'loadMoreFriends',
  'loadMoreGlobal'
])

const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
</script>
