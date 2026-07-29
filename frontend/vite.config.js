import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 개발 서버 실행: npm run dev  (기본 http://localhost:5173)
export default defineConfig({
  plugins: [react()],
});
