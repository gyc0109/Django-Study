<template>
  <!-- ============================================================
       模板（页面长什么样）
       常见指令速记：
         {{ }}            插值，把变量显示出来
         v-model          双向绑定（输入框 <-> 变量）
         v-if / v-else    条件渲染
         v-for            循环渲染
         :key             循环项唯一标识
         @click           点击事件
         :disabled        动态禁用
         :class          动态 class
       ============================================================ -->
  <div class="app">
    <header>
      <h1>图书管理练习</h1>
      <p class="sub">
        Django 4.2 + DRF + MySQL + Redis 缓存 + Celery 异步任务 + Vue 2.7
      </p>
    </header>

    <!-- 全局提示：成功或失败都显示在这里 -->
    <p v-if="notice" class="notice">{{ notice }}</p>

    <!-- ================= 区块 1：服务状态 ================= -->
    <section>
      <h2>1. 服务状态</h2>
      <div class="row">
        <button @click="loadHealth">刷新状态</button>
        <span class="hint">检查 Django / MySQL / Redis 是否连通</span>
      </div>
      <pre>{{ healthText }}</pre>
    </section>

    <!-- ================= 区块 2：分类管理 ================= -->
    <section>
      <h2>2. 分类管理</h2>
      <div class="row">
        <!-- @keyup.enter：输入框里按回车也能提交 -->
        <input
          v-model="newCategory"
          placeholder="新分类名称，例如：计算机"
          @keyup.enter="addCategory"
        />
        <button @click="addCategory">新增分类</button>
        <span class="hint">分类下有书时不允许删除（外键 PROTECT）</span>
      </div>

      <div class="chips">
        <!-- 后面的数字是 book_count，由后端反向统计得到 -->
        <span v-for="c in categories" :key="c.id" class="chip">
          {{ c.name }}
          <b>{{ c.book_count }}</b>
          <button class="x" title="删除分类" @click="removeCategory(c)">×</button>
        </span>
        <span v-if="!categories.length" class="hint">还没有分类</span>
      </div>
    </section>

    <!-- ================= 区块 3：图书 CRUD ================= -->
    <section>
      <h2>3. 图书管理</h2>

      <!-- 新增表单 -->
      <div class="row form-row">
        <input v-model="form.title" placeholder="书名（必填）" @keyup.enter="addBook" />
        <input v-model="form.author" placeholder="作者" @keyup.enter="addBook" />
        <input v-model.number="form.price" type="number" min="0" step="0.01" placeholder="价格" />
        <input v-model.number="form.stock" type="number" min="0" placeholder="库存" />
        <!-- :value="null" 对应后端的「未分类」 -->
        <select v-model="form.category">
          <option :value="null">未分类</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <button @click="addBook">新增图书</button>
      </div>

      <!-- 搜索 + 分类筛选 + 分页信息 -->
      <div class="row filter-row">
        <input
          v-model="search"
          placeholder="搜索书名或作者，回车确认"
          @keyup.enter="doSearch"
        />
        <button @click="doSearch">搜索</button>

        <select v-model="filterCategory" @change="doSearch">
          <option :value="''">全部分类</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>

        <button class="ghost" @click="resetFilters">重置</button>
        <span class="hint">共 {{ total }} 本</span>
      </div>

      <!-- 数据表格 -->
      <table>
        <thead>
          <tr>
            <th style="width: 60px">ID</th>
            <th>书名</th>
            <th>作者</th>
            <th style="width: 90px">价格</th>
            <th style="width: 80px">库存</th>
            <th style="width: 100px">分类</th>
            <th style="width: 150px">创建时间</th>
            <th style="width: 150px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="book in books" :key="book.id">
            <!-- 编辑态：这一行变成输入框 -->
            <template v-if="editingId === book.id">
              <td>#{{ book.id }}</td>
              <td><input v-model="editDraft.title" /></td>
              <td><input v-model="editDraft.author" /></td>
              <td><input v-model.number="editDraft.price" type="number" min="0" step="0.01" /></td>
              <td><input v-model.number="editDraft.stock" type="number" min="0" /></td>
              <td>
                <select v-model="editDraft.category">
                  <option :value="null">未分类</option>
                  <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </td>
              <td>{{ formatTime(book.created_at) }}</td>
              <td>
                <button @click="saveEdit(book.id)">保存</button>
                <button class="ghost" @click="cancelEdit">取消</button>
              </td>
            </template>

            <!-- 展示态：普通文本 -->
            <template v-else>
              <td>#{{ book.id }}</td>
              <td>{{ book.title }}</td>
              <td>{{ book.author || '-' }}</td>
              <td>{{ money(book.price) }}</td>
              <td>{{ book.stock }}</td>
              <td>{{ book.category_name }}</td>
              <td>{{ formatTime(book.created_at) }}</td>
              <td>
                <button class="ghost" @click="startEdit(book)">编辑</button>
                <button class="danger" @click="removeBook(book)">删除</button>
              </td>
            </template>
          </tr>
        </tbody>
      </table>

      <p v-if="!books.length" class="empty">没有匹配的图书。</p>

      <!-- 分页：第一页禁用上一页，最后一页禁用下一页 -->
      <div class="row pager">
        <button :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
        <span>第 {{ page }} / {{ totalPages }} 页</span>
        <button :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
      </div>
    </section>

    <!-- ================= 区块 4：Celery 异步报表 ================= -->
    <section>
      <h2>4. 异步任务：生成库存报表</h2>
      <div class="row">
        <button :disabled="reportRunning" @click="runReport">
          {{ reportRunning ? '生成中...' : '生成库存报表' }}
        </button>
        <span class="hint">
          任务丢给 Celery worker 执行，前端每 700ms 轮询一次结果
        </span>
      </div>
      <pre>{{ reportText }}</pre>
    </section>
  </div>
</template>

<script>
/**
 * 逻辑部分。
 *
 * Vue 组件的核心概念：
 *   data      数据（状态）
 *   computed  计算属性（由 data 推导，带缓存）
 *   methods   方法（发请求、处理点击）
 *   mounted   生命周期：组件挂载完成后执行一次
 */

// 封装好的 axios 实例
import { http } from './api'

export default {
  name: 'App',

  data() {
    return {
      // ---- 服务状态 ----
      health: null,
      healthError: '',

      // ---- 提示信息 ----
      notice: '',

      // ---- 分类 ----
      categories: [],
      newCategory: '',

      // ---- 图书列表 / 搜索 / 筛选 / 分页 ----
      books: [],
      total: 0,
      page: 1,
      pageSize: 5, // 必须和后端 PAGE_SIZE 一致
      search: '',
      filterCategory: '',

      // ---- 新增表单 ----
      form: { title: '', author: '', price: 0, stock: 0, category: null },

      // ---- 行内编辑 ----
      editingId: null,
      editDraft: { title: '', author: '', price: 0, stock: 0, category: null },

      // ---- 异步报表 ----
      reportTask: null,
      reportRunning: false
    }
  },

  computed: {
    // 健康状态格式化
    healthText() {
      if (this.healthError) return `请求失败：${this.healthError}`
      if (!this.health) return '加载中...'
      return JSON.stringify(this.health, null, 2)
    },

    // 总页数：总条数 / 每页条数，向上取整，至少 1 页
    totalPages() {
      return Math.max(1, Math.ceil(this.total / this.pageSize))
    },

    // 异步任务结果格式化
    reportText() {
      if (!this.reportTask) return '尚未生成报表'
      return JSON.stringify(this.reportTask, null, 2)
    }
  },

  // 页面加载完成后自动执行
  mounted() {
    this.loadHealth()
    this.loadCategories()
    this.loadBooks()
  },

  methods: {
    // ---------------- 工具方法 ----------------

    // "2026-11-08T19:36:30.807703+08:00" -> "2026-11-08 19:36:30"
    formatTime(value) {
      return value ? value.replace('T', ' ').slice(0, 19) : ''
    },

    // 价格显示成 ¥39.00
    money(value) {
      return `¥${Number(value || 0).toFixed(2)}`
    },

    // 统一显示错误信息
    showError(err) {
      const detail = err && err.response && err.response.data
      if (detail && detail.detail) {
        this.notice = `操作失败：${detail.detail}`
      } else {
        this.notice = `操作失败：${err.message}`
      }
    },

    // ---------------- 健康检查 ----------------

    async loadHealth() {
      this.healthError = ''
      try {
        const { data } = await http.get('/health/')
        this.health = data
      } catch (err) {
        this.healthError = err.message
      }
    },

    // ---------------- 分类 ----------------

    async loadCategories() {
      // 分类接口关闭了分页，所以 data 直接就是数组
      const { data } = await http.get('/categories/')
      this.categories = data
    },

    async addCategory() {
      const name = this.newCategory.trim()
      if (!name) return
      this.notice = ''
      try {
        await http.post('/categories/', { name })
        this.newCategory = ''
        await this.loadCategories()
        this.notice = `分类「${name}」已创建`
      } catch (err) {
        this.showError(err)
      }
    },

    async removeCategory(category) {
      if (!window.confirm(`确定删除分类「${category.name}」吗？`)) return
      this.notice = ''
      try {
        await http.delete(`/categories/${category.id}/`)
        // 如果当前正在按这个分类筛选，删除后要重置筛选
        if (this.filterCategory === category.id) {
          this.filterCategory = ''
          this.page = 1
        }
        await this.loadCategories()
        await this.loadBooks()
        this.notice = `分类「${category.name}」已删除`
      } catch (err) {
        // 分类下有书时，后端返回 400 和中文提示
        this.showError(err)
      }
    },

    // ---------------- 图书列表 ----------------

    async loadBooks() {
      const { data } = await http.get('/books/', {
        params: {
          // search 为空时传 undefined，axios 会自动忽略该参数
          search: this.search || undefined,
          category: this.filterCategory || undefined,
          page: this.page
        }
      })
      // 分页接口返回 { count, next, previous, results }
      this.books = data.results
      this.total = data.count

      // 删掉最后一页的数据后，页码可能越界，自动回到最后一页
      if (this.page > this.totalPages) {
        this.page = this.totalPages
        this.loadBooks()
      }
    },

    doSearch() {
      this.page = 1
      this.loadBooks()
    },

    resetFilters() {
      this.search = ''
      this.filterCategory = ''
      this.page = 1
      this.loadBooks()
    },

    goPage(target) {
      this.page = target
      this.loadBooks()
    },

    // ---------------- 图书增删改 ----------------

    async addBook() {
      if (!this.form.title.trim()) {
        this.notice = '书名不能为空'
        return
      }
      this.notice = ''
      try {
        await http.post('/books/', {
          title: this.form.title.trim(),
          author: this.form.author.trim(),
          price: this.form.price || 0,
          stock: this.form.stock || 0,
          category: this.form.category || null
        })
        // 清空表单
        this.form = { title: '', author: '', price: 0, stock: 0, category: null }
        this.page = 1
        await this.loadBooks()
        await this.loadCategories() // 分类的 book_count 变了
        this.notice = '新增成功'
      } catch (err) {
        this.showError(err)
      }
    },

    startEdit(book) {
      this.editingId = book.id
      // 复制一份数据到草稿，避免直接改到表格里显示的对象
      this.editDraft = {
        title: book.title,
        author: book.author,
        price: Number(book.price),
        stock: book.stock,
        category: book.category
      }
    },

    cancelEdit() {
      this.editingId = null
    },

    async saveEdit(id) {
      if (!this.editDraft.title.trim()) {
        this.notice = '书名不能为空'
        return
      }
      this.notice = ''
      try {
        // PATCH 是局部更新，只传需要改的字段
        await http.patch(`/books/${id}/`, {
          title: this.editDraft.title.trim(),
          author: this.editDraft.author.trim(),
          price: this.editDraft.price || 0,
          stock: this.editDraft.stock || 0,
          category: this.editDraft.category || null
        })
        this.editingId = null
        await this.loadBooks()
        await this.loadCategories()
        this.notice = '保存成功'
      } catch (err) {
        this.showError(err)
      }
    },

    async removeBook(book) {
      if (!window.confirm(`确定删除《${book.title}》吗？`)) return
      this.notice = ''
      try {
        await http.delete(`/books/${book.id}/`)
        if (this.editingId === book.id) this.editingId = null
        await this.loadBooks()
        await this.loadCategories()
        this.notice = '删除成功'
      } catch (err) {
        this.showError(err)
      }
    },

    // ---------------- Celery 异步报表 ----------------

    async runReport() {
      this.notice = ''
      this.reportRunning = true
      try {
        // 提交任务：接口立刻返回 task_id，不等待计算结果
        const { data } = await http.post('/tasks/report/')
        this.reportTask = { task_id: data.task_id, status: 'PENDING' }
        await this.pollReport(data.task_id)
      } catch (err) {
        this.showError(err)
      } finally {
        this.reportRunning = false
      }
    },

    async pollReport(taskId) {
      // 异步任务不会立刻完成，所以隔一段时间问一次
      for (let i = 0; i < 12; i += 1) {
        await new Promise((resolve) => setTimeout(resolve, 700))
        const { data } = await http.get(`/tasks/${taskId}/`)
        this.reportTask = data
        // 成功或失败就停止轮询
        if (data.status === 'SUCCESS' || data.status === 'FAILURE') return
      }
    }
  }
}
</script>

<style>
/* 样式部分：不涉及逻辑，保持简单清晰 */
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: #f5f6f8;
  color: #222;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
}

.app {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 16px 60px;
}

header h1 {
  margin: 0 0 6px;
  font-size: 26px;
}

.sub {
  margin: 0 0 20px;
  color: #777;
  font-size: 13px;
}

section {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px 18px;
  margin-bottom: 18px;
}

h2 {
  margin: 0 0 12px;
  font-size: 17px;
}

.row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

input,
select {
  padding: 7px 9px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
}

input:focus,
select:focus {
  border-color: #2563eb;
}

button {
  padding: 7px 12px;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
}

button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

button.ghost {
  background: #eef2ff;
  color: #3730a3;
}

button.danger {
  background: #dc2626;
}

.hint {
  color: #888;
  font-size: 12px;
}

.notice {
  background: #fff7ed;
  border: 1px solid #fdba74;
  color: #9a3412;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
}

pre {
  background: #0f172a;
  color: #d1fae5;
  padding: 12px;
  border-radius: 8px;
  font-size: 12px;
  overflow: auto;
  margin: 0;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 13px;
}

.chip b {
  color: #2563eb;
}

.chip .x {
  background: transparent;
  color: #94a3b8;
  padding: 0 2px;
  font-size: 15px;
  line-height: 1;
}

.chip .x:hover {
  color: #dc2626;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

th,
td {
  border-bottom: 1px solid #eef0f3;
  padding: 9px 6px;
  text-align: left;
}

th {
  background: #f8fafc;
  color: #555;
  font-weight: 600;
}

td input,
td select {
  width: 100%;
  padding: 5px 6px;
}

td button {
  padding: 4px 8px;
  margin-right: 4px;
}

.empty {
  color: #999;
  font-size: 13px;
}

.pager {
  margin-top: 12px;
  margin-bottom: 0;
}
</style>
