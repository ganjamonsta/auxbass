// vite.config.js
import { defineConfig } from "file:///S:/git/tg_player/webapp/node_modules/vite/dist/node/index.js";
import vue from "file:///S:/git/tg_player/webapp/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import { fileURLToPath, URL } from "node:url";
import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";
var __vite_injected_original_import_meta_url = "file:///S:/git/tg_player/webapp/vite.config.js";
var gitCommit = process.env.GIT_COMMIT || "unknown";
if (gitCommit === "unknown") {
  try {
    gitCommit = execSync("git rev-parse --short HEAD", { stdio: ["ignore", "pipe", "ignore"] }).toString().trim();
  } catch (e) {
  }
}
var pkg = JSON.parse(fs.readFileSync(new URL("./package.json", __vite_injected_original_import_meta_url), "utf-8"));
var appVersion = pkg.version || "1.0.0";
var buildTime = Date.now();
var buildId = `${gitCommit}-${buildTime}`;
function generateVersionJsonPlugin() {
  return {
    name: "generate-version-json",
    closeBundle() {
      try {
        const outDir = path.resolve(fileURLToPath(new URL(".", __vite_injected_original_import_meta_url)), "dist");
        if (!fs.existsSync(outDir)) {
          fs.mkdirSync(outDir, { recursive: true });
        }
        const versionData = {
          version: appVersion,
          buildId,
          gitCommit,
          buildTime,
          builtAt: new Date(buildTime).toISOString()
        };
        fs.writeFileSync(
          path.join(outDir, "version.json"),
          JSON.stringify(versionData, null, 2),
          "utf-8"
        );
        console.log(`
\u{1F4E6} [Vite] Generated dist/version.json (buildId: ${buildId})`);
      } catch (err) {
        console.warn("[Vite] Failed to write version.json:", err);
      }
    }
  };
}
var vite_config_default = defineConfig({
  plugins: [vue(), generateVersionJsonPlugin()],
  define: {
    __APP_VERSION__: JSON.stringify(appVersion),
    __APP_BUILD_ID__: JSON.stringify(buildId),
    __APP_BUILD_TIME__: JSON.stringify(buildTime),
    __APP_COMMIT__: JSON.stringify(gitCommit)
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", __vite_injected_original_import_meta_url))
    }
  },
  server: {
    port: 5173,
    host: true
  },
  build: {
    outDir: "dist",
    sourcemap: false,
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            if (id.includes("vue") || id.includes("pinia") || id.includes("@vueuse")) {
              return "vendor-vue";
            }
            if (id.includes("lucide-vue-next")) {
              return "vendor-icons";
            }
            if (id.includes("axios")) {
              return "vendor-network";
            }
            return "vendor-others";
          }
        }
      }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJTOlxcXFxnaXRcXFxcdGdfcGxheWVyXFxcXHdlYmFwcFwiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiUzpcXFxcZ2l0XFxcXHRnX3BsYXllclxcXFx3ZWJhcHBcXFxcdml0ZS5jb25maWcuanNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL1M6L2dpdC90Z19wbGF5ZXIvd2ViYXBwL3ZpdGUuY29uZmlnLmpzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSdcbmltcG9ydCB2dWUgZnJvbSAnQHZpdGVqcy9wbHVnaW4tdnVlJ1xuaW1wb3J0IHsgZmlsZVVSTFRvUGF0aCwgVVJMIH0gZnJvbSAnbm9kZTp1cmwnXG5pbXBvcnQgZnMgZnJvbSAnbm9kZTpmcydcbmltcG9ydCBwYXRoIGZyb20gJ25vZGU6cGF0aCdcbmltcG9ydCB7IGV4ZWNTeW5jIH0gZnJvbSAnbm9kZTpjaGlsZF9wcm9jZXNzJ1xuXG4vLyBcdTA0MUVcdTA0M0ZcdTA0NDBcdTA0MzVcdTA0MzRcdTA0MzVcdTA0M0JcdTA0MzVcdTA0M0RcdTA0MzhcdTA0MzUgXHUwNDNBXHUwNDNFXHUwNDNDXHUwNDNDXHUwNDM4XHUwNDQyXHUwNDMwIFx1MDQzOCBcdTA0MzJcdTA0MzVcdTA0NDBcdTA0NDFcdTA0MzhcdTA0MzggXHUwNDQxXHUwNDMxXHUwNDNFXHUwNDQwXHUwNDNBXHUwNDM4XG5sZXQgZ2l0Q29tbWl0ID0gcHJvY2Vzcy5lbnYuR0lUX0NPTU1JVCB8fCAndW5rbm93bidcbmlmIChnaXRDb21taXQgPT09ICd1bmtub3duJykge1xuICB0cnkge1xuICAgIGdpdENvbW1pdCA9IGV4ZWNTeW5jKCdnaXQgcmV2LXBhcnNlIC0tc2hvcnQgSEVBRCcsIHsgc3RkaW86IFsnaWdub3JlJywgJ3BpcGUnLCAnaWdub3JlJ10gfSkudG9TdHJpbmcoKS50cmltKClcbiAgfSBjYXRjaCAoZSkge31cbn1cblxuY29uc3QgcGtnID0gSlNPTi5wYXJzZShmcy5yZWFkRmlsZVN5bmMobmV3IFVSTCgnLi9wYWNrYWdlLmpzb24nLCBpbXBvcnQubWV0YS51cmwpLCAndXRmLTgnKSlcbmNvbnN0IGFwcFZlcnNpb24gPSBwa2cudmVyc2lvbiB8fCAnMS4wLjAnXG5jb25zdCBidWlsZFRpbWUgPSBEYXRlLm5vdygpXG5jb25zdCBidWlsZElkID0gYCR7Z2l0Q29tbWl0fS0ke2J1aWxkVGltZX1gXG5cbi8qKiBcdTA0MUZcdTA0M0JcdTA0MzBcdTA0MzNcdTA0MzhcdTA0M0QgXHUwNDMzXHUwNDM1XHUwNDNEXHUwNDM1XHUwNDQwXHUwNDMwXHUwNDQ2XHUwNDM4XHUwNDM4IGRpc3QvdmVyc2lvbi5qc29uIFx1MDQzRlx1MDQ0MFx1MDQzOCBcdTA0NDFcdTA0MzFcdTA0M0VcdTA0NDBcdTA0M0FcdTA0MzUgKi9cbmZ1bmN0aW9uIGdlbmVyYXRlVmVyc2lvbkpzb25QbHVnaW4oKSB7XG4gIHJldHVybiB7XG4gICAgbmFtZTogJ2dlbmVyYXRlLXZlcnNpb24tanNvbicsXG4gICAgY2xvc2VCdW5kbGUoKSB7XG4gICAgICB0cnkge1xuICAgICAgICBjb25zdCBvdXREaXIgPSBwYXRoLnJlc29sdmUoZmlsZVVSTFRvUGF0aChuZXcgVVJMKCcuJywgaW1wb3J0Lm1ldGEudXJsKSksICdkaXN0JylcbiAgICAgICAgaWYgKCFmcy5leGlzdHNTeW5jKG91dERpcikpIHtcbiAgICAgICAgICBmcy5ta2RpclN5bmMob3V0RGlyLCB7IHJlY3Vyc2l2ZTogdHJ1ZSB9KVxuICAgICAgICB9XG4gICAgICAgIGNvbnN0IHZlcnNpb25EYXRhID0ge1xuICAgICAgICAgIHZlcnNpb246IGFwcFZlcnNpb24sXG4gICAgICAgICAgYnVpbGRJZCxcbiAgICAgICAgICBnaXRDb21taXQsXG4gICAgICAgICAgYnVpbGRUaW1lLFxuICAgICAgICAgIGJ1aWx0QXQ6IG5ldyBEYXRlKGJ1aWxkVGltZSkudG9JU09TdHJpbmcoKVxuICAgICAgICB9XG4gICAgICAgIGZzLndyaXRlRmlsZVN5bmMoXG4gICAgICAgICAgcGF0aC5qb2luKG91dERpciwgJ3ZlcnNpb24uanNvbicpLFxuICAgICAgICAgIEpTT04uc3RyaW5naWZ5KHZlcnNpb25EYXRhLCBudWxsLCAyKSxcbiAgICAgICAgICAndXRmLTgnXG4gICAgICAgIClcbiAgICAgICAgY29uc29sZS5sb2coYFxcblx1RDgzRFx1RENFNiBbVml0ZV0gR2VuZXJhdGVkIGRpc3QvdmVyc2lvbi5qc29uIChidWlsZElkOiAke2J1aWxkSWR9KWApXG4gICAgICB9IGNhdGNoIChlcnIpIHtcbiAgICAgICAgY29uc29sZS53YXJuKCdbVml0ZV0gRmFpbGVkIHRvIHdyaXRlIHZlcnNpb24uanNvbjonLCBlcnIpXG4gICAgICB9XG4gICAgfVxuICB9XG59XG5cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XG4gIHBsdWdpbnM6IFt2dWUoKSwgZ2VuZXJhdGVWZXJzaW9uSnNvblBsdWdpbigpXSxcbiAgZGVmaW5lOiB7XG4gICAgX19BUFBfVkVSU0lPTl9fOiBKU09OLnN0cmluZ2lmeShhcHBWZXJzaW9uKSxcbiAgICBfX0FQUF9CVUlMRF9JRF9fOiBKU09OLnN0cmluZ2lmeShidWlsZElkKSxcbiAgICBfX0FQUF9CVUlMRF9USU1FX186IEpTT04uc3RyaW5naWZ5KGJ1aWxkVGltZSksXG4gICAgX19BUFBfQ09NTUlUX186IEpTT04uc3RyaW5naWZ5KGdpdENvbW1pdCksXG4gIH0sXG4gIHJlc29sdmU6IHtcbiAgICBhbGlhczoge1xuICAgICAgJ0AnOiBmaWxlVVJMVG9QYXRoKG5ldyBVUkwoJy4vc3JjJywgaW1wb3J0Lm1ldGEudXJsKSlcbiAgICB9XG4gIH0sXG4gIHNlcnZlcjoge1xuICAgIHBvcnQ6IDUxNzMsXG4gICAgaG9zdDogdHJ1ZVxuICB9LFxuICBidWlsZDoge1xuICAgIG91dERpcjogJ2Rpc3QnLFxuICAgIHNvdXJjZW1hcDogZmFsc2UsXG4gICAgY2h1bmtTaXplV2FybmluZ0xpbWl0OiA2MDAsXG4gICAgcm9sbHVwT3B0aW9uczoge1xuICAgICAgb3V0cHV0OiB7XG4gICAgICAgIG1hbnVhbENodW5rcyhpZCkge1xuICAgICAgICAgIGlmIChpZC5pbmNsdWRlcygnbm9kZV9tb2R1bGVzJykpIHtcbiAgICAgICAgICAgIGlmIChpZC5pbmNsdWRlcygndnVlJykgfHwgaWQuaW5jbHVkZXMoJ3BpbmlhJykgfHwgaWQuaW5jbHVkZXMoJ0B2dWV1c2UnKSkge1xuICAgICAgICAgICAgICByZXR1cm4gJ3ZlbmRvci12dWUnXG4gICAgICAgICAgICB9XG4gICAgICAgICAgICBpZiAoaWQuaW5jbHVkZXMoJ2x1Y2lkZS12dWUtbmV4dCcpKSB7XG4gICAgICAgICAgICAgIHJldHVybiAndmVuZG9yLWljb25zJ1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgaWYgKGlkLmluY2x1ZGVzKCdheGlvcycpKSB7XG4gICAgICAgICAgICAgIHJldHVybiAndmVuZG9yLW5ldHdvcmsnXG4gICAgICAgICAgICB9XG4gICAgICAgICAgICByZXR1cm4gJ3ZlbmRvci1vdGhlcnMnXG4gICAgICAgICAgfVxuICAgICAgICB9XG4gICAgICB9XG4gICAgfVxuICB9XG59KVxuIl0sCiAgIm1hcHBpbmdzIjogIjtBQUErUCxTQUFTLG9CQUFvQjtBQUM1UixPQUFPLFNBQVM7QUFDaEIsU0FBUyxlQUFlLFdBQVc7QUFDbkMsT0FBTyxRQUFRO0FBQ2YsT0FBTyxVQUFVO0FBQ2pCLFNBQVMsZ0JBQWdCO0FBTG9JLElBQU0sMkNBQTJDO0FBUTlNLElBQUksWUFBWSxRQUFRLElBQUksY0FBYztBQUMxQyxJQUFJLGNBQWMsV0FBVztBQUMzQixNQUFJO0FBQ0YsZ0JBQVksU0FBUyw4QkFBOEIsRUFBRSxPQUFPLENBQUMsVUFBVSxRQUFRLFFBQVEsRUFBRSxDQUFDLEVBQUUsU0FBUyxFQUFFLEtBQUs7QUFBQSxFQUM5RyxTQUFTLEdBQUc7QUFBQSxFQUFDO0FBQ2Y7QUFFQSxJQUFNLE1BQU0sS0FBSyxNQUFNLEdBQUcsYUFBYSxJQUFJLElBQUksa0JBQWtCLHdDQUFlLEdBQUcsT0FBTyxDQUFDO0FBQzNGLElBQU0sYUFBYSxJQUFJLFdBQVc7QUFDbEMsSUFBTSxZQUFZLEtBQUssSUFBSTtBQUMzQixJQUFNLFVBQVUsR0FBRyxTQUFTLElBQUksU0FBUztBQUd6QyxTQUFTLDRCQUE0QjtBQUNuQyxTQUFPO0FBQUEsSUFDTCxNQUFNO0FBQUEsSUFDTixjQUFjO0FBQ1osVUFBSTtBQUNGLGNBQU0sU0FBUyxLQUFLLFFBQVEsY0FBYyxJQUFJLElBQUksS0FBSyx3Q0FBZSxDQUFDLEdBQUcsTUFBTTtBQUNoRixZQUFJLENBQUMsR0FBRyxXQUFXLE1BQU0sR0FBRztBQUMxQixhQUFHLFVBQVUsUUFBUSxFQUFFLFdBQVcsS0FBSyxDQUFDO0FBQUEsUUFDMUM7QUFDQSxjQUFNLGNBQWM7QUFBQSxVQUNsQixTQUFTO0FBQUEsVUFDVDtBQUFBLFVBQ0E7QUFBQSxVQUNBO0FBQUEsVUFDQSxTQUFTLElBQUksS0FBSyxTQUFTLEVBQUUsWUFBWTtBQUFBLFFBQzNDO0FBQ0EsV0FBRztBQUFBLFVBQ0QsS0FBSyxLQUFLLFFBQVEsY0FBYztBQUFBLFVBQ2hDLEtBQUssVUFBVSxhQUFhLE1BQU0sQ0FBQztBQUFBLFVBQ25DO0FBQUEsUUFDRjtBQUNBLGdCQUFRLElBQUk7QUFBQSx5REFBcUQsT0FBTyxHQUFHO0FBQUEsTUFDN0UsU0FBUyxLQUFLO0FBQ1osZ0JBQVEsS0FBSyx3Q0FBd0MsR0FBRztBQUFBLE1BQzFEO0FBQUEsSUFDRjtBQUFBLEVBQ0Y7QUFDRjtBQUVBLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzFCLFNBQVMsQ0FBQyxJQUFJLEdBQUcsMEJBQTBCLENBQUM7QUFBQSxFQUM1QyxRQUFRO0FBQUEsSUFDTixpQkFBaUIsS0FBSyxVQUFVLFVBQVU7QUFBQSxJQUMxQyxrQkFBa0IsS0FBSyxVQUFVLE9BQU87QUFBQSxJQUN4QyxvQkFBb0IsS0FBSyxVQUFVLFNBQVM7QUFBQSxJQUM1QyxnQkFBZ0IsS0FBSyxVQUFVLFNBQVM7QUFBQSxFQUMxQztBQUFBLEVBQ0EsU0FBUztBQUFBLElBQ1AsT0FBTztBQUFBLE1BQ0wsS0FBSyxjQUFjLElBQUksSUFBSSxTQUFTLHdDQUFlLENBQUM7QUFBQSxJQUN0RDtBQUFBLEVBQ0Y7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLE1BQU07QUFBQSxFQUNSO0FBQUEsRUFDQSxPQUFPO0FBQUEsSUFDTCxRQUFRO0FBQUEsSUFDUixXQUFXO0FBQUEsSUFDWCx1QkFBdUI7QUFBQSxJQUN2QixlQUFlO0FBQUEsTUFDYixRQUFRO0FBQUEsUUFDTixhQUFhLElBQUk7QUFDZixjQUFJLEdBQUcsU0FBUyxjQUFjLEdBQUc7QUFDL0IsZ0JBQUksR0FBRyxTQUFTLEtBQUssS0FBSyxHQUFHLFNBQVMsT0FBTyxLQUFLLEdBQUcsU0FBUyxTQUFTLEdBQUc7QUFDeEUscUJBQU87QUFBQSxZQUNUO0FBQ0EsZ0JBQUksR0FBRyxTQUFTLGlCQUFpQixHQUFHO0FBQ2xDLHFCQUFPO0FBQUEsWUFDVDtBQUNBLGdCQUFJLEdBQUcsU0FBUyxPQUFPLEdBQUc7QUFDeEIscUJBQU87QUFBQSxZQUNUO0FBQ0EsbUJBQU87QUFBQSxVQUNUO0FBQUEsUUFDRjtBQUFBLE1BQ0Y7QUFBQSxJQUNGO0FBQUEsRUFDRjtBQUNGLENBQUM7IiwKICAibmFtZXMiOiBbXQp9Cg==
