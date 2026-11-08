/**
 * axios 统一封装。
 *
 * 好处：
 *   1. 所有请求自动带上 /api 前缀，不用每个地方写全
 *   2. 超时、请求头只配置一次
 *   3. 以后要加登录 token，只改这一个文件
 */

import axios from 'axios'

export const http = axios.create({
  // 实际请求 = baseURL + 路径
  // 例如 http.get('/books/') -> 浏览器请求 /api/books/
  // 再由 Vite 代理转发到 http://127.0.0.1:8001/api/books/
  baseURL: '/api',

  // 10 秒没响应就中断，避免页面一直转圈
  timeout: 10000
})
