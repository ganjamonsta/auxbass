<template>
  <Teleport to="body">
    <TransitionGroup name="toast" tag="div" class="toast-container">
      <div 
        v-for="toast in toasts" 
        :key="toast.id" 
        class="toast"
        :class="toast.type"
      >
        <div class="toast-icon">
          <svg v-if="toast.type === 'error'" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
          </svg>
          <svg v-else-if="toast.type === 'success'" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
          <svg v-else-if="toast.type === 'warning'" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
          </svg>
          <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
          </svg>
        </div>
        <div class="toast-content">
          <div class="toast-title">{{ toast.title }}</div>
          <div v-if="toast.message" class="toast-message">{{ toast.message }}</div>
        </div>
        <button class="toast-close" @click="removeToast(toast.id)">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
          </svg>
        </button>
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'

const toasts = ref([])
let toastId = 0

const addToast = (options) => {
  const id = ++toastId
  const toast = {
    id,
    type: options.type || 'info',
    title: options.title,
    message: options.message,
    duration: options.duration || 4000,
  }
  
  toasts.value.push(toast)
  
  if (toast.duration > 0) {
    setTimeout(() => {
      removeToast(id)
    }, toast.duration)
  }
  
  return id
}

const removeToast = (id) => {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index !== -1) {
    toasts.value.splice(index, 1)
  }
}

// Expose methods
defineExpose({
  addToast,
  removeToast,
  // Shorthand methods (title, type or (title, type, duration))
  show: (title, type = 'info', duration) => addToast({ type, title, duration }),
  success: (title, message) => addToast({ type: 'success', title, message }),
  error: (title, message) => addToast({ type: 'error', title, message }),
  info: (title, message) => addToast({ type: 'info', title, message }),
  warning: (title, message) => addToast({ type: 'warning', title, message }),
})
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 60px;
  left: 16px;
  right: 16px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  background: var(--xm-bg-elevated, #1A1A1A);
  border-radius: var(--neu-radius-lg, 16px);
  box-shadow: 
    8px 8px 16px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -4px -4px 8px var(--neu-shadow-light, rgba(255, 255, 255, 0.03)),
    0 4px 20px rgba(0, 0, 0, 0.4);
  pointer-events: auto;
  border-left: 4px solid transparent;
}

.toast.error {
  border-left-color: var(--xm-accent, #E53935);
  box-shadow: 
    8px 8px 16px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -4px -4px 8px var(--neu-shadow-light, rgba(255, 255, 255, 0.03)),
    0 0 20px var(--xm-accent-glow, rgba(229, 57, 53, 0.2));
}

.toast.success {
  border-left-color: #00C853;
  box-shadow: 
    8px 8px 16px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -4px -4px 8px var(--neu-shadow-light, rgba(255, 255, 255, 0.03)),
    0 0 20px rgba(0, 200, 83, 0.2);
}

.toast.info {
  border-left-color: var(--xm-secondary, #00BCD4);
  box-shadow: 
    8px 8px 16px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -4px -4px 8px var(--neu-shadow-light, rgba(255, 255, 255, 0.03)),
    0 0 20px rgba(0, 188, 212, 0.2);
}

.toast.warning {
  border-left-color: #FFA000;
  box-shadow: 
    8px 8px 16px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -4px -4px 8px var(--neu-shadow-light, rgba(255, 255, 255, 0.03)),
    0 0 20px rgba(255, 160, 0, 0.2);
}

.toast-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--neu-radius-full, 9999px);
  background: var(--xm-bg-surface, #222);
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -1px -1px 2px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
}

.toast.error .toast-icon {
  color: var(--xm-accent, #E53935);
}

.toast.success .toast-icon {
  color: #00C853;
}

.toast.info .toast-icon {
  color: var(--xm-secondary, #00BCD4);
}

.toast.warning .toast-icon {
  color: #FFA000;
}

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--xm-text-primary, #fff);
}

.toast-message {
  font-size: 13px;
  color: var(--xm-text-muted, #888);
  margin-top: 3px;
}

.toast-close {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  background: var(--xm-bg-surface, #222);
  border: none;
  border-radius: var(--neu-radius-full, 9999px);
  color: var(--xm-text-muted, #888);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  box-shadow: 
    3px 3px 6px var(--neu-shadow-dark, rgba(0, 0, 0, 0.5)),
    -2px -2px 4px var(--neu-shadow-light, rgba(255, 255, 255, 0.03));
}

.toast-close:active {
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark, rgba(0, 0, 0, 0.4)),
    inset -1px -1px 2px var(--neu-shadow-inset-light, rgba(255, 255, 255, 0.02));
}

/* Animations */
.toast-enter-active {
  animation: toast-in 0.3s ease-out;
}

.toast-leave-active {
  animation: toast-out 0.2s ease-in forwards;
}

@keyframes toast-in {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes toast-out {
  from {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
  to {
    opacity: 0;
    transform: translateY(-10px) scale(0.95);
  }
}
</style>
