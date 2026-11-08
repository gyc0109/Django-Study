/**
 * ============================================================================
 * axios 统一封装（api.js）
 * ============================================================================
 *
 * 为什么不直接在组件里 import axios 用？
 * 因为真实项目里请求配置会越来越复杂：
 *    - 统一前缀 /api
 *    - 统一超时时间
 *    - 统一请求头（Content-Type、Authorization）
 *    - 统一错误处理（401 跳登录、500 弹提示）
 *    - 统一 loading
 *
 * 这些「只写一次、全局生效」的东西，放在这里最合适。
 * 以后要加登录 token，只改这一个文件，不用动 20 个组件。
 *
 * ★ 注意 axios 的一个反直觉行为：
 *   我们用了 baseURL: '/api'，所以调用 http.get('/books/') 时，
 *   axios 会拼成 '/api' + '/books/' = '/api/books/'（浏览器实际请求这个相对地址）。
 *   而 http.get('books/')（没有前导斜杠）会拼成 '/api' + 'books/' 吗？
 *   不会，axios 会拼成 '/apibooks/'，直接 404。
 *   所以路径开头一定要有 "/"。
 */

// axios：最流行的 HTTP 请求库，基于 Promise，浏览器和 Node 都能用。
// 相比原生 fetch，它自动把 JSON 字符串转成对象、自动处理超时、拦截器更好用。
import axios from 'axios'

// 创建一个「带默认配置」的实例，并导出给所有组件复用。
//   export const http  命名导出，组件里 import { http } from './api'
//   如果写成 export default，导入时名字可以随便起（import xxx from './api'），
//   但命名导出更利于「一个文件导出多个东西」的场景。
export const http = axios.create({
  // ---------------------------------------------------------------
  // baseURL：每个请求路径前都会自动加上这个前缀
  // ---------------------------------------------------------------
  // 实际请求 = baseURL + 你传的路径，例如：
  //     http.get('/books/')   →  浏览器请求 /api/books/
  //
  // ★ 这个 /api 是相对地址（没有协议和域名），所以会请求「当前页面所在的服务器」，
  //   也就是 http://localhost:5174/api/books/。
  //   然后由 Vite 开发服务器的 proxy 转发到后端 8001（见 vite.config.js）。
  //
  // ★ 为什么不直接写 http://127.0.0.1:8001/api？
  //   那样就是跨域请求（端口不同），会触发浏览器的 CORS 检查和预检请求。
  //   虽然 Django 那边配了 CORS_ALLOWED_ORIGINS 也能通，但多一层风险；
  //   用代理则是「同源请求」，浏览器根本不检查跨域，最省心。
  //   生产环境上线时，通常也是 Nginx 把 /api 反向代理到后端，思路完全一致。
  baseURL: '/api',

  // ---------------------------------------------------------------
  // timeout：超时时间（毫秒）
  // ---------------------------------------------------------------
  // 10 秒内没有任何响应就主动中断，抛出一个 error。
  // ★ 为什么需要它？默认 axios 不超时，如果后端挂了或者网络卡住，
  //   请求会一直挂着，用户看到页面永远在转圈，体验极差。
  // ★ 注意这是「整个请求」的超时，不是「连接」的超时。
  //   如果后端接口本身就要跑 30 秒（比如同步导出大报表），
  //   那就不能用这个实例，要单独传更长的 timeout 或干脆用异步任务（本项目就是这么做的）。
  timeout: 10000
})

/**
 * 小提示：如果想给所有请求自动加请求头，可以这样写拦截器（本项目暂时不需要）：
 *
 *   http.interceptors.request.use((config) => {
 *     const token = localStorage.getItem('token')
 *     if (token) config.headers.Authorization = `Bearer ${token}`
 *     return config
 *   })
 *
 * 想统一处理错误，就加响应拦截器：
 *
 *   http.interceptors.response.use(
 *     (res) => res,
 *     (err) => {
 *       if (err.response?.status === 401) location.href = '/login'
 *       return Promise.reject(err)
 *     }
 *   )
 */
