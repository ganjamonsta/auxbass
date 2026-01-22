<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="confirm-overlay" @click.self="$emit('cancel')">
        <div class="confirm-dialog">
          <div class="confirm-icon" :class="type">
            {{ icon }}
          </div>
          
          <h3 class="confirm-title">{{ title }}</h3>
          <p class="confirm-message">{{ message }}</p>

          <div class="confirm-actions">
            <button class="btn-cancel" @click="$emit('cancel')">
              {{ cancelText }}
            </button>
            <button 
              class="btn-confirm" 
              :class="type"
              @click="$emit('confirm')"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  show: Boolean,
  type: {
    type: String,
    default: 'warning', // warning, danger, info
  },
  title: {
    type: String,
    default: 'Подтверждение'
  },
  message: {
    type: String,
    default: 'Вы уверены?'
  },
  confirmText: {
    type: String,
    default: 'Да'
  },
  cancelText: {
    type: String,
    default: 'Отмена'
  }
})

const emit = defineEmits(['confirm', 'cancel'])

const icon = computed(() => {
  switch (props.type) {
    case 'danger': return '🗑️'
    case 'warning': return '⚠️'
    case 'info': return 'ℹ️'
    default: return '❓'
  }
})
</script>

<style scoped>
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 300;
  padding: 20px;
}

.confirm-dialog {
  background: var(--tg-theme-bg-color);
  border-radius: 16px;
  padding: 24px;
  width: 100%;
  max-width: 320px;
  text-align: center;
}

.confirm-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.confirm-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.confirm-message {
  font-size: 14px;
  color: var(--tg-theme-hint-color);
  margin-bottom: 24px;
  line-height: 1.4;
}

.confirm-actions {
  display: flex;
  gap: 12px;
}

.btn-cancel,
.btn-confirm {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
}

.btn-cancel {
  background: var(--tg-theme-secondary-bg-color);
  color: var(--tg-theme-text-color);
}

.btn-confirm {
  background: var(--tg-theme-button-color);
  color: var(--tg-theme-button-text-color);
}

.btn-confirm.danger {
  background: #ff3b30;
  color: white;
}

.btn-confirm.warning {
  background: #ff9500;
  color: white;
}

/* Animation */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
