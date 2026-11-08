/**
 * ============================================================================
 * Vite 配置（vite.config.js）
 * ============================================================================
 *
 * Vite 是什么？
 *   新一代前端构建工具，替代 Vue CLI / webpack。开发时它不做打包，
 *   而是用浏览器原生的 ES Module 直接加载文件，所以启动只要几百毫秒。
 *
 * 这个文件配了两件事：
 *   1. 用哪个插件编译 .vue 文件（@vitejs/plugin-vue2）
 *   2. 开发服务器的端口和代理规则
 */

// defineConfig 只是一个「类型提示」用的包装函数：
// 它把配置对象原样返回，编辑器就能根据它给出属性自动补全。
// 运行时不产生任何影响，你也可以直接 export default {...}。
import { defineConfig } from 'vite'

// Vue 2 的官方 Vite 插件。
// ★ 注意包名：Vue 2 用 @vitejs/plugin-vue2，Vue 3 用 @vitejs/plugin-vue。
//   装错了会报「Vue 版本不匹配」或者 template 编译失败。
// 它的作用：把 .vue 单文件组件拆成三部分分别处理
//   <template> → 编译成 render 函数
//   <script>   → 当作普通 JS/TS
//   <style>    → 处理 scoped、预处理器（sass/less）
import vue from '@vitejs/plugin-vue2'

export default defineConfig({
  // 插件列表。没有它，import App from './App.vue' 会直接报错。
  plugins: [vue()],

  server: {
    // ---------------------------------------------------------------
    // 开发服务器端口
    // ---------------------------------------------------------------
    // 为什么是 5174 而不是 Vite 默认的 5173？
    //   本机还有另一个项目（project1）的前端跑在 5173。
    //   两个项目同时启动时，不改端口会提示「5173 已被占用」，
    //   Vite 会自动顺延到 5174 或 5175 —— 端口不固定很麻烦
    //   （比如 Django 的 CORS 白名单是写死的端口）。
    //   所以这里固定写 5174，两边互不干扰。
    port: 5174,

    // ---------------------------------------------------------------
    // 代理（proxy）：解决开发环境跨域
    // ---------------------------------------------------------------
    // 背景：浏览器同源策略要求「协议+域名+端口」三者一致。
    //   前端 http://localhost:5174  →  后端 http://127.0.0.1:8001
    //   端口不同、域名不同 → 跨域 → 浏览器拦截响应
    //
    // 解决办法：让浏览器「只请求 5174」，由 Vite 这个 Node 进程去请求 8001，
    // 再把结果原样返回给浏览器。对浏览器来说，从头到尾都是同一个源，
    // 根本不存在跨域问题（跨域限制只存在于浏览器，服务器之间没有）。
    //
    // 请求链路：
    //   浏览器  GET http://localhost:5174/api/books/
    //      ↓ 命中以 /api 开头的规则
    //   Vite   转发到 http://127.0.0.1:8001/api/books/
    //      ↓
    //   Django 返回 JSON
    //      ↓
    //   Vite   原样回给浏览器
    proxy: {
      // 键是「匹配的路径前缀」，值是转发配置。
      // 所有以 /api 开头的请求都会被转发。
      '/api': {
        // 目标服务器：practice 后端的地址。
        // ★ 必须是 127.0.0.1 而不是 localhost：
        //   某些环境下 localhost 会先解析到 IPv6 的 ::1，
        //   而 Django runserver 默认只监听 IPv4，导致 ECONNREFUSED。
        target: 'http://127.0.0.1:8001',

        // changeOrigin: true 表示转发时把请求头里的 Host
        // 改成目标服务器的（127.0.0.1:8001）。
        // 很多后端框架会校验 Host 头（Django 的 ALLOWED_HOSTS 就是），
        // 不改的话可能出现 400 Bad Request / Invalid HTTP_HOST header。
        // ★ 牢记这个坑：忘了写 changeOrigin，接口就莫名报 400。
        changeOrigin: true

        // ★ 这里故意「没有」rewrite。
        //
        // rewrite 的作用是改写路径，比如：
        //     rewrite: (path) => path.replace(/^\/api/, '')
        // 加了它，/api/books/ 会被改成 /books/ 再转发，
        // 而后端接口是 /api/books/，于是 404。
        //
        // 本项目的 Django 路由本身就带 /api 前缀（config/urls.py 里的
        // path("api/", include("library.urls"))），所以路径要原样转发。
        // 网上很多教程会加 rewrite，那是因为它们的后端没有 /api 前缀，
        // 直接抄过来就会出问题。
      }
    }
  }
})
