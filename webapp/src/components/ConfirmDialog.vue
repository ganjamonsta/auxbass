<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="confirm-overlay" @click.self="$emit('cancel')">
        <div class="confirm-dialog">
          <div class="confirm-icon" :class="type">
            <component :is="icon" :size="32" />
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
import { Trash2, AlertTriangle, Info, HelpCircle } from 'lucide-vue-next'

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
    case 'danger': return Trash2
    case 'warning': return AlertTriangle
    case 'info': return Info
    default: return HelpCircle
  }
})
</script>

<style scoped>
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 300;
  padding: 20px;
}

.confirm-dialog {
  background: var(--c-bg-2);
  border-radius: var(--r-xl);
  padding: 28px;
  width: 100%;
  max-width: 320px;
  text-align: center;
  box-shadow: 
    12px 12px 24px var(--sh-dark)),
    -6px -6px 12px var(--sh-light)),
    0 0 40px rgba(0, 0, 0, 0.5);
}

.confirm-icon {
  font-size: 52px;
  margin-bottom: 18px;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: auto;
  margin-right: auto;
  border-radius: var(--r-full);
  background: var(--c-bg-3);
  box-shadow: 
    inset 4px 4px 8px var(--sh-inset-dark)),
    inset -2px -2px 4px var(--sh-inset-light));
}

.confirm-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 10px;
  color: var(--c-text-1);
}

.confirm-message {
  font-size: 14px;
  color: var(--c-text-3);
  margin-bottom: 26px;
  line-height: 1.5;
}

.confirm-actions {
  display: flex;
  gap: 14px;
}

.btn-cancel,
.btn-confirm {
  flex: 1;
  padding: 16px;
  border: none;
  border-radius: var(--r-md);
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-cancel {
  background: var(--c-bg-3);
  color: var(--c-text-2);
  box-shadow: 
    4px 4px 10px var(--sh-dark)),
    -2px -2px 6px var(--sh-light));
}

.btn-cancel:active {
  box-shadow: 
    inset 2px 2px 4px var(--sh-inset-dark)),
    inset -1px -1px 2px var(--sh-inset-light));
}

.btn-confirm {
  background: linear-gradient(180deg, var(--c-accent) 0%, var(--c-accent-dark) 100%);
  color: white;
  box-shadow: 
    4px 4px 10px var(--sh-dark)),
    -2px -2px 6px var(--sh-light)),
    0 4px 15px var(--c-accent-glow));
}

.btn-confirm:active {
  transform: scale(0.98);
  box-shadow: 
    inset 3px 3px 6px rgba(0, 0, 0, 0.3),
    inset -2px -2px 4px rgba(255, 255, 255, 0.1);
}

.btn-confirm.danger {
  background: linear-gradient(180deg, #F44336 0%, #D32F2F 100%);
  box-shadow: 
    4px 4px 10px var(--sh-dark)),
    -2px -2px 6px var(--sh-light)),
    0 4px 15px rgba(244, 67, 54, 0.3);
}

.btn-confirm.warning {
  background: linear-gradient(180deg, #FF9800 0%, #F57C00 100%);
  box-shadow: 
    4px 4px 10px var(--sh-dark)),
    -2px -2px 6px var(--sh-light)),
    0 4px 15px rgba(255, 152, 0, 0.3);
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
