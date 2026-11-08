/**
 * ============================================================================
 * Vue 应用的启动入口（main.js）
 * ============================================================================
 *
 * 整个前端只有这一个「起点」。浏览器加载 index.html 后，
 * 里面那行 <script type="module" src="/src/main.js"></script> 就会执行本文件。
 *
 * 它做了三件事：
 *   1. 引入 Vue 构造器和根组件 App.vue
 *   2. 创建一个 Vue 实例，并告诉它「根组件是谁」
 *   3. 把这个实例挂载到 index.html 的 <div id="app"> 上
 *
 * 注意：Vue 2 和 Vue 3 的启动写法完全不同：
 *   Vue 2：new Vue({...}).$mount('#app')            ← 本项目用的
 *   Vue 3：createApp(App).mount('#app')
 * 网上搜到 createApp 的代码不要直接抄进来，会报错。
 */

// 引入 Vue 2 的默认导出对象。
// 这个 import 最终来自 node_modules/vue/dist/vue.runtime.esm.js（运行时版）。
// 「运行时版」不含模板编译器，所以 .vue 文件里的 template 要在构建时
// 由 @vitejs/plugin-vue2 预编译成 render 函数 —— 这也是为什么要装那个插件。
import Vue from 'vue'

// 引入根组件（单文件组件，SFC）。
// Vite 会把它编译成一个普通对象（包含 render/data/methods 等），
// 所以这里能直接 import 进来用。
import App from './App.vue'

// 创建 Vue 实例。
new Vue({
  // render 函数：Vue 调用它来得到「要渲染什么」。
  //
  // h 是 createElement 的简写（hyperscript 的意思），
  // h(App) 表示「用 App 组件创建一个虚拟节点」。
  //
  // ★ 为什么用 render 而不是写 template: '<App/>'？
  //   因为我们用的是「运行时版」Vue，它不带模板编译器，
  //   写 template 字符串浏览器会报
  //   "You are using the runtime-only build of Vue where the template compiler is not available"。
  //   而 render 函数不需要编译，运行时版完全支持。
  render: (h) => h(App)
})
  // $mount('#app')：把 Vue 实例挂载到页面上 id 为 app 的元素。
  //   - 挂载后，该元素内部原有内容会被替换成 App 组件的渲染结果
  //   - 之后所有数据的响应式更新，都会自动反映到这个 DOM 区域
  // 也可以写成 new Vue({ el: '#app', render: ... })，效果完全一样，
  // 但 $mount 写法更灵活（可以先创建、配置完再挂载）。
  .$mount('#app')
