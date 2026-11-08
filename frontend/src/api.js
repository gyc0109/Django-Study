/**
 * ============================================================================
 * src/api.js —— 统一的 HTTP 请求工具（对 axios 的一层薄封装）
 * ============================================================================
 *
 * 【为什么要封装一层？不封装会怎样？】
 * 不封装的话，每个组件里都得这么写：
 *     axios.get('http://127.0.0.1:8000/api/notes/')
 * 问题：
 *   1. 后端地址写死在 20 个文件里，换端口要改 20 处，必漏；
 *   2. 超时时间、请求头、Token 各写各的，风格不统一；
 *   3. 401/500 的错误处理要重复写 20 遍。
 *
 * 封装之后，全项目只有这一个文件知道「后端在哪」，
 * 组件里只关心「我要请求哪个路径」，换地址只需改一行。
 *
 * 【本文件在整个链路里的位置】
 *     App.vue  ──调用──►  http.get('/notes/')
 *                              │ axios 拼接 baseURL
 *                              ▼
 *                          /api/notes/          （浏览器看到的地址，5173 端口）
 *                              │ Vite 开发服务器代理（见 vite.config.js）
 *                              ▼
 *                          http://127.0.0.1:8000/api/notes/   （真正的 Django）
 *
 * ============================================================================
 */

// axios 是目前最常用的 HTTP 客户端，基于 Promise，支持 async/await。
// 浏览器自带的 fetch 也能用，但 axios 有几个便利：
//   - 自动把响应体 JSON.parse（fetch 要自己 .json()）；
//   - 提供 params 选项，自动拼查询字符串并做 URL 编码；
//   - 提供拦截器（interceptors），适合统一加 Token / 统一报错。
import axios from 'axios'

// ---------------------------------------------------------------------------
// axios.create(...) 创建一个「定制版」的 axios 实例
// ---------------------------------------------------------------------------
// ★ 为什么不直接用 import axios from 'axios' 的全局默认实例？
//   因为全局实例是「共享」的——万一某个第三方组件改了它的默认配置
//   （比如 global defaults.headers），会影响你所有请求。
//   用 create 建一个独立实例，配置只作用于本项目，互不干扰。
//
// export 出去之后，别的文件这样用：
//     import { http } from './api'
//     const { data } = await http.get('/notes/')
//
// ★ 注意这里是「具名导出」（export const），
//   所以导入时必须写 { http }（带花括号）；
//   如果写成 import http from './api'（不带花括号）会得到 undefined。
export const http = axios.create({
  // ---- baseURL：所有请求的公共前缀 ----
  // 配了 '/api' 之后：
  //     http.get('/notes/')    -> 实际请求 /api/notes/
  //     http.post('/health/')  -> 实际请求 /api/health/
  //
  // ★★★ 为什么写 '/api' 而不是 'http://127.0.0.1:8000/api'？★★★
  //   写相对地址有两个关键好处：
  //   1. 不跨域：浏览器认为请求的是「自己的 5173 端口」，
  //      不会触发 CORS 预检（OPTIONS 请求）；
  //   2. 由 Vite 代理转发到后端（见 vite.config.js 的 proxy），
  //      后端端口改了只改 vite.config.js，这里一个字都不用动。
  //
  //   如果这里写死 http://127.0.0.1:8000/api，就变成真正的跨域请求，
  //   需要 Django 那边配 CORS_ALLOWED_ORIGINS，反而更麻烦。
  baseURL: '/api',

  // ---- timeout：超时时间（毫秒）----
  // 10 秒还没收到响应就抛错，进入 catch。
  //
  // ★ 为什么要设超时？
  //   axios 默认 timeout 是 0（永不超时）。如果后端卡死或网络断了，
  //   请求会一直挂着，用户看到按钮一直转圈，体验很差。
  //
  // ★ 注意：Celery 的异步任务接口不会受这个影响，
  //   因为 /api/tasks/add/ 是「立刻返回 202」的，
  //   真正慢的任务在后台跑，前端是靠轮询去查的。
  timeout: 10000
})

// ===========================================================================
// 【路径写法的一个大坑，务必记住】★
// ===========================================================================
// baseURL 是 '/api'，axios 拼地址的规则是「直接字符串相加」，它不会帮你补斜杠：
//
//     http.get('/notes/')   ->  '/api' + '/notes/'  =  '/api/notes/'   ✅
//     http.get('notes/')    ->  '/api' + 'notes/'   =  '/apinotes/'    ❌ 直接 404
//
// 所以路径【开头必须写斜杠】。
// （另一种做法是把 baseURL 写成 '/api/'，两边都带斜杠，
//  但那样如果路径也以 / 开头会得到 '//api//notes/'，
//  Django 一般能容忍，但有些服务器不能，所以不推荐。）
//
// ===========================================================================
// 【常用写法速查】
// ===========================================================================
//   // GET 带查询参数（推荐用 params，axios 会自动做 URL 编码）
//   const { data } = await http.get('/notes/', { params: { page: 2, search: 'django' } })
//   // 等价于请求 /api/notes/?page=2&search=django
//
//   // POST 提交 JSON（axios 自动设置 Content-Type: application/json）
//   await http.post('/notes/', { title: '标题', content: '内容' })
//
//   // PATCH 局部更新（只传要改的字段）
//   await http.patch('/notes/1/', { title: '新标题' })
//
//   // DELETE
//   await http.delete('/notes/1/')
//
//   // 返回值解构：axios 的响应对象是 { data, status, headers, config, request }
//   // 业务数据在 data 里，所以习惯写 const { data } = await ...
//
// ===========================================================================
// 【扩展：以后要加登录 Token，怎么做？】
// ===========================================================================
// 在这里加一个「请求拦截器」，所有请求发出前自动带上 Token：
//
//   http.interceptors.request.use((config) => {
//     const token = localStorage.getItem('token')
//     if (token) config.headers.Authorization = `Bearer ${token}`
//     return config        // ★ 必须 return，否则请求会被中断
//   })
//
// 再加一个「响应拦截器」统一处理错误：
//
//   http.interceptors.response.use(
//     (res) => res,
//     (err) => {
//       if (err.response?.status === 401) {
//         // Token 过期，跳登录页
//       }
//       return Promise.reject(err)
//     }
//   )
//
// ★ 拦截器写在 http 创建之后、使用之前，全项目的请求都会经过它，
//   这就是「封装一层」最大的价值——横切逻辑只写一遍。
// ===========================================================================
