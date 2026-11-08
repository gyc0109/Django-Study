/**
 * ============================================================================
 * src/main.js —— 前端真正的入口文件（整个 Vue 应用的「第一行代码」）
 * ============================================================================
 *
 * 【执行链路】
 *   index.html 里的 <script type="module" src="/src/main.js"> 被浏览器加载
 *        ↓
 *   执行本文件
 *        ↓
 *   创建 Vue 根实例，把 App.vue 渲染到 <div id="app"> 里
 *        ↓
 *   App.vue 的 mounted() 触发，开始请求后端 /api/health/ 和 /api/notes/
 *
 * 【为什么这个文件这么短？】
 * 因为它只负责「启动」，不负责「业务」。真正的界面在 App.vue，
 * 真正的请求封装在 api.js。职责分离，出了问题好定位。
 *
 * ============================================================================
 */

// ---------------------------------------------------------------------------
// import Vue from 'vue'
// ---------------------------------------------------------------------------
// 这个 'vue' 不是相对路径，而是「包名」——Vite 会去 node_modules 里找。
// 打开 package.json 会看到 "vue": "^2.7.16"，所以引入的是 Vue 2。
//
// ★ Vue 2 和 Vue 3 的启动方式完全不同，抄代码时千万注意：
//     Vue 2:  import Vue from 'vue';        new Vue({...}).$mount('#app')
//     Vue 3:  import { createApp } from 'vue';  createApp(App).mount('#app')
//   本项目用 Vue 2.7（官方给 Vue 2 的最后一个版本，支持 Composition API）。
//
// ★ 为什么 Vue 2 只能写 import Vue from 'vue'（默认导入），
//   而不能写成 import { createApp }？
//   因为 Vue 2 的包导出的是一个「构造函数」本身，没有具名导出 createApp。
//   写错了控制台会报：`createApp` is not exported by vue。
import Vue from 'vue'

// ---------------------------------------------------------------------------
// import App from './App.vue'
// ---------------------------------------------------------------------------
// 相对路径必须以 ./ 或 ../ 开头，否则 Vite 会以为是 npm 包去 node_modules 找。
//
// ★ 浏览器原生是不认识 .vue 文件的！能这样写全靠两个东西配合：
//     1. vite.config.js 里注册了 @vitejs/plugin-vue2 插件；
//     2. 请求经过 Vite 开发服务器，它把 .vue 现场编译成 JS 再返回。
//   所以这段代码不能直接丢到浏览器里跑，必须经过 Vite（或打包后的 dist）。
//
// App 是「根组件」，其他所有组件都是从它开始一层层嵌套出去的。
import App from './App.vue'

// ---------------------------------------------------------------------------
// 创建根实例并挂载
// ---------------------------------------------------------------------------
new Vue({
  // ---- render 函数 ----
  // 告诉 Vue：「这个实例负责渲染 App 这个组件」。
  //
  // h 是 createElement 的惯用简写（来自 hyperscript，意思是
  // 「生成 HTML 结构的脚本」）。h(App) 会创建一个「App 组件的虚拟节点」。
  //
  // ★★★ 为什么用 render 而不是 template？★★★
  //   写成 template: '<App />' 在「完整版 Vue」里是可以的，
  //   但 Vite 默认引入的是「运行时版（runtime-only）」Vue——
  //   它不包含模板编译器（为了减小体积）。
  //   运行时版里写 template 会报：
  //     [Vue warn]: You are using the runtime-only build of Vue where
  //     the template compiler is not available.
  //   而 render 函数是纯 JS，运行时版完全支持。
  //
  //   ★ 那 App.vue 里写的 <template> 为什么没事？
  //     因为那个 template 在「编译阶段」就被 @vitejs/plugin-vue2 处理掉了，
  //     最终产出的仍是 render 函数——运行时版拿到的已经是编译结果。
  render: (h) => h(App)

  // ★ 这里没有写 el: '#app'，而是用下面的 .$mount('#app')，
  //   两种写法效果完全一样，只是链式调用更紧凑：
  //     new Vue({ el: '#app', render: h => h(App) })   // 等价写法
}).$mount('#app')

// ---------------------------------------------------------------------------
// 【常见报错速查】
// ---------------------------------------------------------------------------
// 1) 页面全白，控制台提示 "Failed to mount app: mount target selector '#app'
//    returned null"
//    -> index.html 里的 id 不是 app，或者 <div id="app"> 被删了。
//
// 2) 报 "You are using the runtime-only build of Vue..."
//    -> 用了 template 选项却引入了运行时版，改用 render 函数。
//
// 3) 报 "Failed to resolve module specifier 'vue'"
//    -> 没有执行 npm install，node_modules 不存在。
//
// 4) 页面能开但接口全部 404
//    -> 不是这个文件的问题，去看 vite.config.js 的 proxy 配置
//       （target 端口写错最常见，本项目后端是 8000）。
// ---------------------------------------------------------------------------
