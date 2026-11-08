/**
 * Vite 配置文件（前端开发服务器 / 打包工具的配置）。
 *
 * Vite 是什么？
 *   一个前端构建工具：开发时启动本地服务器（热更新），
 *   上线前把 .vue / .js / .css 打包成浏览器能直接用的文件。
 */

// defineConfig 只是为了让编辑器有类型提示，写不写都能运行
import { defineConfig } from 'vite'
// 让 Vite 能编译 .vue 单文件组件（Vue 2 专用插件）
import vue from '@vitejs/plugin-vue2'

export default defineConfig({
  // 插件列表：有了它，import App from './App.vue' 才能工作
  plugins: [vue()],

  server: {
    // 开发服务器端口：http://localhost:5173
    port: 5173,

    // 代理：把前端发出的 /api 请求转发给 Django，解决跨域问题。
    // 浏览器只访问 5173（同源），由 Vite 在中间转发到 8000，
    // 这样开发时就不需要在浏览器里处理跨域。
    proxy: {
      '/api': {
        // 目标后端地址（Django 开发服务器）
        target: 'http://127.0.0.1:8000',
        // 把请求头里的 Host 改成目标地址，部分后端会校验
        changeOrigin: true
        // 注意：这里没有 rewrite，所以 /api/notes/ 会原样转发，
        // 正好对应 Django 的 /api/notes/ 路由。
      }
    }
  }
})
