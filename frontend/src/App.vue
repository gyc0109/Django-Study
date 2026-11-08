<template>
  <!-- ================= 模板部分 =================
       Vue 的模板就是 HTML + Vue 指令。
       常用指令先认识几个：
         v-model        双向绑定：输入框的值和 data 里的变量自动同步
         v-if / v-else  条件渲染：满足条件才显示
         v-for          循环渲染列表
         @click         点击事件（@ 是 v-on: 的简写）
         :disabled      动态属性（: 是 v-bind: 的简写）
  -->
  <div class="app">
    <h1>Django 4.2 + Celery + Vue 2.7</h1>
    <p class="sub">MySQL 8.4（3307） · Redis（6380） · Vite 代理 /api</p>

    <!-- ========== 区块 1：服务状态 ========== -->
    <section>
      <h2>1. 服务状态 <button @click="loadHealth">刷新</button></h2>
      <!-- {{ }} 是插值语法，把 JS 表达式的值显示到页面上。
           healthText 是 computed（计算属性），见下方 script。 -->
      <pre>{{ healthText }}</pre>
    </section>

    <!-- ========== 区块 2：Celery 异步任务 ========== -->
    <section>
      <h2>2. Celery 异步任务（加法）</h2>
      <div class="row">
        <!-- v-model.number：双向绑定，并自动把输入转成数字 -->
        <input v-model.number="a" type="number" />
        <span>+</span>
        <input v-model.number="b" type="number" />
        <button @click="runAddTask">提交任务</button>
      </div>
      <pre>{{ taskText }}</pre>
    </section>

    <!-- ========== 区块 3：笔记 CRUD + 搜索 + 分页 + 手动同步 ========== -->
    <section>
      <h2>3. Notes CRUD + 搜索 + 分页</h2>

      <!-- 新增（立即提交）：v-model 绑定 form 对象的属性 -->
      <div class="row">
        <input v-model="form.title" placeholder="标题" @keyup.enter="addNote" />
        <input v-model="form.content" placeholder="内容" @keyup.enter="addNote" />
        <button @click="addNote">新增</button>
      </div>

      <!-- 搜索：@keyup.enter 表示按回车触发 doSearch -->
      <div class="row search-row">
        <input
          v-model="search"
          placeholder="搜索标题或内容，回车确认"
          @keyup.enter="doSearch"
        />
        <button @click="doSearch">搜索</button>
        <button class="ghost" @click="resetSearch">重置</button>
        <span class="hint">共 {{ total }} 条</span>
      </div>

      <!-- 同步工具栏：
           编辑只改本地草稿（edits），点这里的按钮才真正请求后端。
           :disabled="!dirtyCount || syncing" 表示：
             没有改动 或 正在同步时，按钮不可点。 -->
      <div class="row toolbar">
        <button :disabled="!dirtyCount || syncing" @click="syncAll">
          <!-- 三目运算符：正在同步显示"同步中..."，否则显示待同步数量 -->
          {{ syncing ? '同步中...' : `同步到后端（${dirtyCount}）` }}
        </button>
        <button class="ghost" :disabled="!editCount" @click="cancelAll">
          取消全部修改
        </button>
        <span v-if="syncMsg" class="ok">{{ syncMsg }}</span>
        <span v-else class="hint">编辑后不会立即提交，点「同步」才写入数据库</span>
      </div>

      <!-- 表格：v-for 循环渲染 notes 数组 -->
      <table>
        <thead>
          <tr>
            <th style="width: 60px">ID</th>
            <th>标题</th>
            <th>内容</th>
            <th style="width: 150px">创建时间</th>
            <th style="width: 130px">操作</th>
          </tr>
        </thead>
        <tbody>
          <!-- :key 必须写且唯一，Vue 靠它判断哪一行被增删/移动 -->
          <tr
            v-for="note in notes"
            :key="note.id"
            :class="{ dirty: isDirty(note.id) }"
          >
            <!-- 如果这一行有草稿（edits[note.id] 存在），就显示输入框 -->
            <template v-if="edits[note.id]">
              <td>#{{ note.id }}</td>
              <!-- 这里绑定的是草稿，不是原始数据，所以不会立即提交 -->
              <td><input v-model="edits[note.id].draft.title" /></td>
              <td><input v-model="edits[note.id].draft.content" /></td>
              <td>{{ formatTime(note.created_at) }}</td>
              <td>
                <button class="ghost" @click="cancelEdit(note.id)">撤销</button>
              </td>
            </template>
            <!-- 否则显示普通文本 -->
            <template v-else>
              <td>#{{ note.id }}</td>
              <td>{{ note.title }}</td>
              <td>{{ note.content }}</td>
              <td>{{ formatTime(note.created_at) }}</td>
              <td>
                <button class="ghost" @click="startEdit(note)">编辑</button>
                <button class="danger" @click="removeNote(note.id)">删除</button>
              </td>
            </template>
          </tr>
        </tbody>
      </table>
      <p v-if="!notes.length" class="empty">没有匹配的数据。</p>

      <!-- 分页：第一页时"上一页"不可点，最后一页时"下一页"不可点 -->
      <div class="row pager">
        <button :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
        <span>第 {{ page }} / {{ totalPages }} 页</span>
        <button :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
        <span class="hint">每页 {{ pageSize }} 条</span>
      </div>
    </section>
  </div>
</template>

<script>
/**
 * 组件的「逻辑部分」。
 *
 * 一个 Vue 组件的核心概念：
 *   data       -> 数据（状态），变化会自动更新页面
 *   computed   -> 计算属性：由 data 推导出来的值，有缓存
 *   methods    -> 方法：处理点击、发请求等
 *   mounted    -> 生命周期钩子：页面挂载完成后执行一次
 *
 * 注意：Vue 2 中 data 必须是「函数」，返回一个对象。
 * 这样每个组件实例都有自己独立的数据，不会互相影响。
 */

// 引入封装好的 axios 实例，用它请求后端接口
import { http } from './api'

export default {
  // 组件名，调试时能看出是哪个组件
  name: 'App',

  // ================= 数据 =================
  data() {
    return {
      // ---- 服务状态 ----
      health: null, // 后端 /api/health/ 返回的对象
      healthError: '', // 请求失败时的错误信息

      // ---- Celery 任务 ----
      a: 1, // 第一个加数
      b: 2, // 第二个加数
      task: null, // 任务状态对象 { task_id, status, result }

      // ---- 新增表单 ----
      form: { title: '', content: '' },

      // ---- 列表 / 搜索 / 分页 ----
      notes: [], // 当前页的数据（来自后端 results）
      search: '', // 搜索关键词（对应 ?search=）
      page: 1, // 当前页码（对应 ?page=）
      pageSize: 5, // 每页条数，必须和后端 PAGE_SIZE 一致
      total: 0, // 总条数（来自后端 count）

      // ---- 编辑草稿 ----
      // 结构：{ [笔记id]: { original: {title, content}, draft: {title, content} } }
      // original 记录进入编辑时的原值，用来判断"是否真的改过"
      // draft 是用户正在改的草稿，只有点「同步」才提交给后端
      edits: {},

      syncing: false, // 是否正在同步（防止重复点击）
      syncMsg: '' // 同步结果提示
    }
  },

  // ================= 计算属性 =================
  computed: {
    // 把后端返回的健康状态转成好看的文本
    healthText() {
      if (this.healthError) return `请求失败：${this.healthError}`
      if (!this.health) return '加载中...'
      return JSON.stringify(this.health, null, 2)
    },

    // 任务状态文本
    taskText() {
      if (!this.task) return '尚未提交任务'
      return JSON.stringify(this.task, null, 2)
    },

    // 总页数：总条数 / 每页条数，向上取整，最少 1 页
    totalPages() {
      return Math.max(1, Math.ceil(this.total / this.pageSize))
    },

    // 当前处于编辑状态的行数
    editCount() {
      return Object.keys(this.edits).length
    },

    // 真正被改动过的行 id 列表
    dirtyIds() {
      return Object.keys(this.edits).filter((id) =>
        this.isEntryDirty(this.edits[id])
      )
    },

    // 待同步数量，显示在按钮上
    dirtyCount() {
      return this.dirtyIds.length
    }
  },

  // ================= 生命周期 =================
  // mounted：组件挂载到页面后自动执行一次，适合做初始化请求
  mounted() {
    this.loadHealth()
    this.loadNotes()
  },

  // ================= 方法 =================
  methods: {
    // 请求后端健康检查接口
    async loadHealth() {
      this.healthError = ''
      try {
        const { data } = await http.get('/health/') // 实际请求 /api/health/
        this.health = data
      } catch (err) {
        this.healthError = err.message
      }
    },

    // 把后端返回的 ISO 时间（2026-11-08T19:07:49.49+08:00）变短一点
    formatTime(value) {
      return value ? value.replace('T', ' ').slice(0, 19) : ''
    },

    /**
     * 加载笔记列表。
     * 请求：GET /api/notes/?search=xx&page=n
     * 后端分页后返回：{ count, next, previous, results }
     * 注意不是数组，数据在 results 里。
     */
    async loadNotes() {
      const { data } = await http.get('/notes/', {
        // params 会被 axios 拼到 URL 上；
        // search 为空时传 undefined，axios 会忽略这个参数
        params: { search: this.search || undefined, page: this.page }
      })
      this.notes = data.results
      this.total = data.count

      // 如果删除后当前页超出范围（比如最后一页被删空），自动回到最后一页
      if (this.page > this.totalPages) {
        this.page = this.totalPages
        this.loadNotes()
      }
    },

    // 点击搜索：回到第一页再查询
    doSearch() {
      this.page = 1
      this.loadNotes()
    },

    // 重置搜索：清空关键词后重新查询
    resetSearch() {
      this.search = ''
      this.doSearch()
    },

    // 翻页
    goPage(target) {
      this.page = target
      this.loadNotes()
    },

    // 新增：立即 POST，不等待"同步"
    async addNote() {
      if (!this.form.title.trim()) return // 标题为空就不提交
      await http.post('/notes/', this.form)
      this.form = { title: '', content: '' } // 清空表单
      this.page = 1 // 新数据排在最前面，回到第一页查看
      this.loadNotes()
    },

    /**
     * 进入编辑：复制一份草稿。
     * 为什么要 this.$set？
     *   Vue 2 无法监听「给对象新增属性」，直接 this.edits[id] = xxx
     *   数据虽然变了，但页面不会更新。$set 才能触发响应式更新。
     */
    startEdit(note) {
      this.$set(this.edits, note.id, {
        original: { title: note.title, content: note.content },
        draft: { title: note.title, content: note.content }
      })
      this.syncMsg = ''
    },

    // 撤销某一行的修改（$delete 同理，删除属性也要用它）
    cancelEdit(id) {
      this.$delete(this.edits, id)
    },

    // 取消所有草稿
    cancelAll() {
      this.edits = {}
      this.syncMsg = ''
    },

    // 判断某条草稿和原始值是否不同
    isEntryDirty(entry) {
      return (
        entry.draft.title !== entry.original.title ||
        entry.draft.content !== entry.original.content
      )
    },

    // 判断某一行是否"被改过"，用来加浅黄底色
    isDirty(id) {
      const entry = this.edits[id]
      return entry ? this.isEntryDirty(entry) : false
    },

    /**
     * 同步：把所有改动过的草稿一次性 PATCH 到后端。
     * Promise.all 表示并行发送所有请求，全部成功才继续。
     */
    async syncAll() {
      const ids = this.dirtyIds
      if (!ids.length || this.syncing) return // 没有改动或正在同步就不执行

      this.syncing = true
      this.syncMsg = ''
      try {
        await Promise.all(
          ids.map((id) => http.patch(`/notes/${id}/`, this.edits[id].draft))
        )
        this.syncMsg = `已同步 ${ids.length} 条到 MySQL`
        this.edits = {} // 同步成功后清空草稿
        this.loadNotes() // 重新拉取，显示数据库里的最新数据
      } catch (err) {
        this.syncMsg = `同步失败：${err.message}`
      } finally {
        this.syncing = false // 无论成功失败都要恢复按钮状态
      }
    },

    // 删除：立即请求后端
    async removeNote(id) {
      await http.delete(`/notes/${id}/`)
      this.$delete(this.edits, id) // 如果这条正在编辑，一起清掉草稿
      this.loadNotes()
    },

    // 提交 Celery 加法任务
    async runAddTask() {
      const { data } = await http.post('/tasks/add/', { a: this.a, b: this.b })
      this.task = { task_id: data.task_id, status: 'PENDING' }
      this.pollTask(data.task_id) // 拿到 id 后开始轮询结果
    },

    /**
     * 轮询任务结果：每 800 毫秒查一次，最多查 10 次。
     * 异步任务不会立刻完成，所以前端要"隔一会儿问一次"。
     */
    async pollTask(taskId) {
      for (let i = 0; i < 10; i += 1) {
        await new Promise((resolve) => setTimeout(resolve, 800))
        const { data } = await http.get(`/tasks/${taskId}/`)
        this.task = data
        // 成功或失败就停止轮询
        if (data.status === 'SUCCESS' || data.status === 'FAILURE') return
      }
    }
  }
}
</script>

<style>
/* ================= 样式部分 =================
   这里是普通 CSS，只作用于本组件。
   语法和平时写网页一样，不需要特殊记忆。 */

* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
  background: #f5f6fa;
  color: #2f3542;
}
.app { max-width: 960px; margin: 0 auto; padding: 32px 20px 60px; }
h1 { font-size: 24px; margin-bottom: 6px; }
h2 { font-size: 16px; margin: 0 0 12px; }
.sub { color: #747d8c; margin-top: 0; font-size: 13px; }
section {
  background: #fff;
  border-radius: 10px;
  padding: 18px 20px;
  margin-top: 18px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}
.row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.search-row { margin-top: 10px; }
.toolbar {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #eef1f6;
}
input {
  padding: 7px 10px;
  border: 1px solid #dfe4ea;
  border-radius: 6px;
  outline: none;
}
input:focus { border-color: #3b82f6; }
button {
  padding: 7px 14px;
  border: none;
  border-radius: 6px;
  background: #3b82f6;
  color: #fff;
  cursor: pointer;
}
button:hover { background: #2563eb; }
button:disabled { background: #c7d2fe; cursor: not-allowed; }
button.ghost { background: #eef2ff; color: #3b82f6; }
button.ghost:hover { background: #e0e7ff; }
button.danger { background: #ef4444; padding: 4px 10px; }
button.danger:hover { background: #dc2626; }
table { width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 14px; }
th, td { text-align: left; padding: 8px 6px; border-bottom: 1px dashed #eef1f6; }
th { color: #747d8c; font-weight: 600; font-size: 13px; }
td input { width: 100%; }
td button { padding: 4px 10px; margin-right: 6px; }
tr.dirty { background: #fffbeb; } /* 有未同步修改的行 */
.pager { margin-top: 14px; }
.hint { color: #a4b0be; font-size: 13px; }
.ok { color: #16a34a; font-size: 13px; }
.empty { color: #a4b0be; font-size: 13px; }
pre {
  background: #0f172a;
  color: #e2e8f0;
  padding: 12px 14px;
  border-radius: 8px;
  font-size: 12px;
  overflow: auto;
  margin-bottom: 0;
}
</style>
