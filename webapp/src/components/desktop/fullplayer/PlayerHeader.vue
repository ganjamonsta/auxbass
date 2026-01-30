<template>
  <div class="cockpit-header">
    <div class="header-left">
      <button class="hud-btn minimize" @click="$emit('close')" title="Свернуть">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 13H5v-2h14v2z"/>
        </svg>
      </button>
      <div class="mode-indicator">
        <span class="status-dot"></span>
        <span class="mode-text">PLAYER ACTIVE</span>
      </div>
    </div>
    
    <div class="header-center">
      <h1 class="cockpit-title">PLAYBACK CONTROL SYSTEM</h1>
    </div>
    
    <div class="header-right">
      <button class="hud-btn" @click="$emit('openTrackMenu')" title="Меню трека">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
defineEmits(['close', 'openTrackMenu'])
</script>

<style scoped>
.cockpit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 25px 35px;
  background: #12121e;
  position: relative;
  z-index: 10;
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 15px;
  flex: 1;
}

.header-center {
  flex: 2;
  display: flex;
  justify-content: center;
}

.cockpit-title {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #db2220 0%, #e85c7c 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-family: 'Segoe UI', -apple-system, sans-serif;
}

.mode-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: #12121e;
  border-radius: 20px;
  box-shadow: 
    inset 4px 4px 8px #08080f,
    inset -4px -4px 8px #1a1a28;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, #db2220 0%, #e85c7c 100%);
  box-shadow: 0 2px 8px rgba(232, 92, 124, 0.6);
  animation: statusPulse 2s ease-in-out infinite;
}

@keyframes statusPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(0.9); }
}

.mode-text {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1.5px;
  color: #db2220;
  font-family: 'Segoe UI', sans-serif;
}

.hud-btn {
  width: 44px;
  height: 44px;
  background: #12121e;
  border: none;
  border-radius: 12px;
  color: #db2220;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 
    6px 6px 12px #08080f,
    -6px -6px 12px #1a1a28;
}

.hud-btn:hover {
  box-shadow: 
    4px 4px 8px #08080f,
    -4px -4px 8px #1a1a28;
  transform: translateY(1px);
}

.hud-btn:active {
  box-shadow: 
    inset 4px 4px 8px #08080f,
    inset -4px -4px 8px #1a1a28;
  transform: translateY(2px);
}

.hud-btn.minimize {
  color: #e87c7c;
}

.hud-btn.minimize:hover {
  color: #ff6464;
}
</style>
