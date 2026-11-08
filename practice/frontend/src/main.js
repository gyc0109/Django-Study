/**
 * Vue 应用的启动入口。
 *
 * 做了三件事：
 *   1. 引入 Vue 和根组件 App.vue
 *   2. 创建 Vue 实例
 *   3. 用 $mount('#app') 把组件渲染到 index.html 的 <div id="app"> 里
 */

import Vue from 'vue'
import App from './App.vue'

new Vue({
  // render 函数：告诉 Vue 根组件是 App
  render: (h) => h(App)
}).$mount('#app')
