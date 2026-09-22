import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import fs from 'node:fs'
import path from 'node:path'
import { execSync } from 'node:child_process'

// Определение коммита и версии сборки
let gitCommit = process.env.GIT_COMMIT || 'unknown'
if (gitCommit === 'unknown') {
  try {
    gitCommit = execSync('git rev-parse --short HEAD', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim()
  } catch (e) {}
}

const pkg = JSON.parse(fs.readFileSync(new URL('./package.json', import.meta.url), 'utf-8'))
const appVersion = pkg.version || '1.0.0'
const buildTime = Date.now()
const buildId = `${gitCommit}-${buildTime}`

/** Плагин генерации dist/version.json при сборке */
function generateVersionJsonPlugin() {
  return {
    name: 'generate-version-json',
    closeBundle() {
      try {
        const outDir = path.resolve(fileURLToPath(new URL('.', import.meta.url)), 'dist')
        if (!fs.existsSync(outDir)) {
          fs.mkdirSync(outDir, { recursive: true })
        }
        const versionData = {
          version: appVersion,
          buildId,
          gitCommit,
          buildTime,
          builtAt: new Date(buildTime).toISOString()
        }
        fs.writeFileSync(
          path.join(outDir, 'version.json'),
          JSON.stringify(versionData, null, 2),
          'utf-8'
        )
        console.log(`\n📦 [Vite] Generated dist/version.json (buildId: ${buildId})`)
      } catch (err) {
        console.warn('[Vite] Failed to write version.json:', err)
      }
    }
  }
}

export default defineConfig({
  plugins: [vue(), generateVersionJsonPlugin()],
  define: {
    __APP_VERSION__: JSON.stringify(appVersion),
    __APP_BUILD_ID__: JSON.stringify(buildId),
    __APP_BUILD_TIME__: JSON.stringify(buildTime),
    __APP_COMMIT__: JSON.stringify(gitCommit),
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('vue') || id.includes('pinia') || id.includes('@vueuse')) {
              return 'vendor-vue'
            }
            if (id.includes('lucide-vue-next')) {
              return 'vendor-icons'
            }
            if (id.includes('axios')) {
              return 'vendor-network'
            }
            return 'vendor-others'
          }
        }
      }
    }
  }
})
