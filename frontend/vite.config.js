import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/agentrun': 'http://localhost:7860', // 开发时代理到后端
      '/get_chat_history': 'http://localhost:8000'
    }
  }
});