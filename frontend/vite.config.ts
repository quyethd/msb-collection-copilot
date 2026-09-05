import {defineConfig} from 'vite'; import react from '@vitejs/plugin-react';
const target='http://127.0.0.1:18080';
export default defineConfig({plugins:[react()],server:{port:5173,proxy:{'/demo':{target,changeOrigin:true}}}});
