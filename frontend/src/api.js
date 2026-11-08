/**
 * 统一的 HTTP 请求工具。
 *
 * 为什么要封装一层？
 *   1. 不用在每个组件里重复写后端地址
 *   2. 超时、请求头等配置只写一次
 *   3. 以后要加 token、统一错误处理，只改这个文件
 */

import axios from 'axios'

// axios.create 创建一个"定制版"的 axios 实例
export const http = axios.create({
  // 所有请求都会自动加上这个前缀。
  // 例如 http.get('/notes/') 实际请求的是 /api/notes/。
  // 这个 /api 会被 Vite 代理转发到 http://127.0.0.1:8000。
  baseURL: '/api',

  // 超时时间：10 秒还没响应就报错，避免页面一直卡住。
  timeout: 10000
})

// 用法示例：
//   const { data } = await http.get('/notes/?page=1&search=abc')
//   await http.post('/notes/', { title: '标题', content: '内容' })
//   await http.patch('/notes/1/', { title: '新标题' })
//   await http.delete('/notes/1/')
