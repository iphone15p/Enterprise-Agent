import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // 代理 API 请求到 FastAPI 后端
    proxy: {
      '/run_agent': 'http://127.0.0.1:7860',
      '/get_chat_history': 'http://127.0.0.1:7860',
    },
  },
});
