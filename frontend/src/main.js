/**
 * 前端入口文件。
 *
 * 浏览器加载 index.html 后，会执行这个文件（见 index.html 里的 script 标签）。
 * 这里做一件事：创建 Vue 根实例，把 App.vue 渲染到页面上的 #app 容器里。
 */

// 引入 Vue 2
import Vue from 'vue'
// 引入根组件（.vue 文件由 Vite 的 vue2 插件编译）
import App from './App.vue'

new Vue({
  // render 函数：告诉 Vue "这个实例要渲染哪个组件"。
  // h 是 createElement 的简写，h(App) 表示创建 App 组件的虚拟节点。
  // 这是 Vue 2 中不写模板、直接用渲染函数的写法。
  render: (h) => h(App)
  // $mount('#app')：把渲染结果挂载到 index.html 里 id="app" 的 div 上
}).$mount('#app')
