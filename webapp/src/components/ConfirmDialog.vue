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
  background: var(--xm-bg-elevated, #1A1A1A);
  border-radius: var(--neu-radius-xl, 24px);
  padding: 28px;
  width: 100%;
  max-width: 320px;
  text-align: center;
  box-shadow: 
    12px 12px 24px var(--neu-shadow-dark, rgba(0, 0, 0, 0.6)),
    -6px -6px 12px var(--neu-shadow-light, rgba(255, 255, 255, 0.03)),
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
  border-radius: var(--neu-radius-full, 9999px);
  background: var(--xm-bg-surface, #222);
  box-shadow: 
    inset 4px 4px 8px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -2px -2px 4px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
}

.confirm-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 10px;
  color: var(--xm-text-primary, #fff);
}

.confirm-message {
  font-size: 14px;
  color: var(--xm-text-muted, #888);
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
  border-radius: var(--neu-radius-md, 12px);
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-cancel {
  background: var(--xm-bg-surface, #222);
  color: var(--xm-text-secondary, #ccc);
  box-shadow: 
    4px 4px 10px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -2px -2px 6px var(--neu-shadow-light, rgba(255, 255, 255, 0.03));
}

.btn-cancel:active {
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -1px -1px 2px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
}

.btn-confirm {
  background: linear-gradient(180deg, var(--xm-accent, #1db954) 0%, var(--xm-accent-dark, #169c46) 100%);
  color: white;
  box-shadow: 
    4px 4px 10px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -2px -2px 6px var(--neu-shadow-light, rgba(255, 255, 255, 0.03)),
    0 4px 15px var(--xm-accent-glow, rgba(229, 57, 53, 0.3));
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
    4px 4px 10px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -2px -2px 6px var(--neu-shadow-light, rgba(255, 255, 255, 0.03)),
    0 4px 15px rgba(244, 67, 54, 0.3);
}

.btn-confirm.warning {
  background: linear-gradient(180deg, #FF9800 0%, #F57C00 100%);
  box-shadow: 
    4px 4px 10px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -2px -2px 6px var(--neu-shadow-light, rgba(255, 255, 255, 0.03)),
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
