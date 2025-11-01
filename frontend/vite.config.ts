import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000, // ✅ Custom Vite dev server port
    proxy: {
      "/api/v1": {
        target: "https://artwork-api-529829749133.asia-south1.run.app",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
