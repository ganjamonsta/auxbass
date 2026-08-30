<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div 
        v-if="showModal" 
        class="pwa-modal-backdrop"
        @click.self="closeGuide"
      >
        <div class="pwa-modal-container">
          <!-- Header -->
          <div class="pwa-modal-header">
            <div class="pwa-modal-icon-wrapper">
              <img src="/icons/icon-96x96.png" alt="AuxBass" class="pwa-modal-logo" />
            </div>
            <div class="pwa-modal-title-group">
              <h3 class="pwa-modal-title">Установка AuxBass</h3>
              <p class="pwa-modal-subtitle">Используйте плеер как полноценное приложение</p>
            </div>
            <button class="pwa-modal-close" @click="closeGuide" aria-label="Закрыть">
              <X :size="20" />
            </button>
          </div>

          <!-- Benefits Chips -->
          <div class="pwa-benefits">
            <div class="pwa-benefit-item">
              <Zap :size="15" class="benefit-icon" />
              <span>Быстрый запуск</span>
            </div>
            <div class="pwa-benefit-item">
              <Headphones :size="15" class="benefit-icon" />
              <span>Фоновый звук</span>
            </div>
            <div class="pwa-benefit-item">
              <Maximize2 :size="15" class="benefit-icon" />
              <span>Полноэкранный режим</span>
            </div>
          </div>

          <!-- Platform specific instructions -->
          <div class="pwa-steps-container">
            <!-- iOS Safari -->
            <template v-if="platform === 'ios'">
              <div class="step-card">
                <div class="step-number">1</div>
                <div class="step-content">
                  <div class="step-text">
                    Нажмите кнопку <strong>«Поделиться»</strong> в нижней панели Safari
                  </div>
                  <div class="step-badge">
                    <Share2 :size="16" />
                    <span>Поделиться</span>
                  </div>
                </div>
              </div>

              <div class="step-card">
                <div class="step-number">2</div>
                <div class="step-content">
                  <div class="step-text">
                    Прокрутите меню вниз и выберите <strong>«На экран "Домой"»</strong>
                  </div>
                  <div class="step-badge">
                    <PlusSquare :size="16" />
                    <span>На экран «Домой»</span>
                  </div>
                </div>
              </div>

              <div class="step-card">
                <div class="step-number">3</div>
                <div class="step-content">
                  <div class="step-text">
                    В правом верхнем углу нажмите <strong>«Добавить»</strong>
                  </div>
                </div>
              </div>
            </template>

            <!-- Telegram WebApp -->
            <template v-else-if="platform === 'telegram'">
              <div class="step-card">
                <div class="step-number">1</div>
                <div class="step-content">
                  <div class="step-text">
                    Нажмите кнопку <strong>«Добавить ярлык»</strong> ниже для быстрого доступа
                  </div>
                </div>
              </div>

              <div class="step-card">
                <div class="step-number">2</div>
                <div class="step-content">
                  <div class="step-text">
                    Либо откройте меню (три точки <strong>⋮</strong>) в правом верхнем углу Telegram и выберите <strong>«Добавить на главный экран»</strong>
                  </div>
                </div>
              </div>
            </template>

            <!-- Android -->
            <template v-else-if="platform === 'android'">
              <template v-if="canPromptDirectly">
                <div class="step-card">
                  <div class="step-number">✓</div>
                  <div class="step-content">
                    <div class="step-text">
                      Нажмите кнопку <strong>«Установить сейчас»</strong> ниже для быстрой установки на ваше устройство
                    </div>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="step-card">
                  <div class="step-number">1</div>
                  <div class="step-content">
                    <div class="step-text">
                      Нажмите на меню браузера (три точки <strong>⋮</strong> в правом верхнем углу)
                    </div>
                  </div>
                </div>

                <div class="step-card">
                  <div class="step-number">2</div>
                  <div class="step-content">
                    <div class="step-text">
                      Выберите <strong>«Установить приложение»</strong> или <strong>«Добавить на главный экран»</strong>
                    </div>
                  </div>
                </div>
              </template>
            </template>

            <!-- Desktop (Chrome / Brave / Edge / Firefox / Opera) -->
            <template v-else>
              <template v-if="canPromptDirectly">
                <div class="step-card">
                  <div class="step-number">✓</div>
                  <div class="step-content">
                    <div class="step-text">
                      Нажмите кнопку <strong>«Установить сейчас»</strong> ниже для добавления AuxBass на ваш компьютер
                    </div>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="step-card">
                  <div class="step-number">1</div>
                  <div class="step-content">
                    <div class="step-text">
                      В адресной строке браузера нажмите иконку <strong>установки приложения</strong> (значок <strong>⊕</strong> или <strong>💻</strong> в правой части адресной строки)
                    </div>
                  </div>
                </div>

                <div class="step-card">
                  <div class="step-number">2</div>
                  <div class="step-content">
                    <div class="step-text">
                      Либо откройте меню браузера (<strong>⋮</strong>) → выберите <strong>«Установить AuxBass»</strong>
                    </div>
                  </div>
                </div>
              </template>
            </template>
          </div>

          <!-- Modal Actions -->
          <div class="pwa-modal-footer">
            <button 
              v-if="canPromptDirectly" 
              class="pwa-primary-action-btn"
              @click="handleDirectInstall"
            >
              <Download :size="18" />
              <span>Установить сейчас</span>
            </button>
            <button 
              class="pwa-secondary-action-btn" 
              :class="{ 'full-width': !canPromptDirectly }"
              @click="closeGuide"
            >
              Понятно
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { 
  X, 
  Download, 
  Share2, 
  PlusSquare, 
  Zap, 
  Headphones, 
  Maximize2 
} from 'lucide-vue-next'
import { usePwaInstall } from '@/composables/usePwaInstall'

const {
  showModal,
  platform,
  canPromptDirectly,
  promptInstall,
  closeGuide
} = usePwaInstall()

const handleDirectInstall = () => {
  promptInstall()
}
</script>

<style scoped>
.pwa-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  z-index: 10010;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.pwa-modal-container {
  background: #18181c;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  width: 100%;
  max-width: 440px;
  padding: 24px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7);
  animation: modal-pop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.pwa-modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

.pwa-modal-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.pwa-modal-logo {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.pwa-modal-title-group {
  flex: 1;
  min-width: 0;
}

.pwa-modal-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #ffffff;
  line-height: 1.25;
}

.pwa-modal-subtitle {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--c-text-2, #b0b0b0);
  line-height: 1.3;
}

.pwa-modal-close {
  background: rgba(255, 255, 255, 0.08);
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-2, #b0b0b0);
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.pwa-modal-close:hover {
  background: rgba(255, 255, 255, 0.16);
  color: #ffffff;
}

/* Benefits */
.pwa-benefits {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.pwa-benefit-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: rgba(29, 185, 84, 0.12);
  border: 1px solid rgba(29, 185, 84, 0.25);
  border-radius: 8px;
  padding: 4px 8px;
  font-size: 11px;
  font-weight: 500;
  color: var(--c-accent-light, #1ed760);
}

.benefit-icon {
  color: var(--c-accent, #1db954);
}

/* Steps */
.pwa-steps-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.step-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 10px 12px;
}

.step-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(29, 185, 84, 0.2);
  color: var(--c-accent-light, #1ed760);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 1px;
}

.step-content {
  flex: 1;
  min-width: 0;
}

.step-text {
  font-size: 13px;
  color: #e0e0e0;
  line-height: 1.4;
}

.step-text strong {
  color: #ffffff;
}

.step-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  padding: 3px 8px;
  font-size: 12px;
  color: #ffffff;
}

/* Footer */
.pwa-modal-footer {
  display: flex;
  gap: 10px;
  margin-top: 4px;
}

.pwa-primary-action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: var(--c-accent, #1db954);
  color: #000000;
  border: none;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 4px 14px rgba(29, 185, 84, 0.35);
}

.pwa-primary-action-btn:hover {
  background: var(--c-accent-light, #1ed760);
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(29, 185, 84, 0.45);
}

.pwa-secondary-action-btn {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 12px 18px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.pwa-secondary-action-btn.full-width {
  flex: 1;
  background: rgba(255, 255, 255, 0.12);
}

.pwa-secondary-action-btn:hover {
  background: rgba(255, 255, 255, 0.18);
}

/* Animations */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.25s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

@keyframes modal-pop {
  from {
    transform: scale(0.92);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
