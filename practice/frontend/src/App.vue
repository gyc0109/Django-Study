<!--
  ============================================================================
  App.vue —— 整个练习项目的前端界面（一个单文件组件）
  ============================================================================

一、什么是「单文件组件」（SFC，Single File Component）？
  一个 .vue 文件里可以同时写三块内容：
      <template>  页面的结构（相当于 HTML）
      <script>    页面的逻辑（相当于 JS）
      <style>     页面的样式（相当于 CSS）

  好处：结构、逻辑、样式放在一起，一个功能一个文件，
  不用在 .html/.js/.css 三个文件之间来回跳。

二、这个组件做了什么？
  把后端的 6 类接口全部串起来，形成一个可视化操作台：
      1. 健康检查      GET  /api/health/
      2. 分类管理      GET/POST/DELETE /api/categories/
      3. 图书 CRUD     GET/POST/PATCH/DELETE /api/books/
      4. 搜索/筛选/分页 ?search=&category=&page=
      5. 行内编辑      点「编辑」整行变输入框，保存时发 PATCH
      6. 异步报表      POST /api/tasks/report/ 后轮询 /api/tasks/<id>/

三、Vue 2 的「响应式」一句话理解
  只要 data 里的变量变了，页面上用到它的地方会自动更新，
  你不需要手动操作 DOM（document.getElementById... 全都不需要）。
-->

<template>
  <!-- ============================================================
       模板（页面长什么样）
       常见指令速记：
         {{ }}            插值，把变量显示出来
         v-model          双向绑定（输入框 <-> 变量），改一边另一边自动变
         v-if / v-else    条件渲染（不满足条件的元素根本不存在于 DOM）
         v-for            循环渲染（列表、下拉选项）
         :key             循环项唯一标识，帮助 Vue 精准复用 DOM
         @click           事件绑定（@ 是 v-on: 的简写）
         :disabled        「:」是 v-bind: 的简写，绑定的是 JS 表达式而不是字符串
         :class           动态 class，根据数据切换样式
       ============================================================ -->
  <div class="app">
    <header>
      <h1>图书管理练习</h1>
      <p class="sub">
        Django 4.2 + DRF + MySQL + Redis 缓存 + Celery 异步任务 + Vue 2.7
      </p>
    </header>

    <!-- 全局提示：成功或失败都显示在这里。
         v-if 为 false 时，这个 <p> 完全不会渲染到页面上（不是隐藏，是不存在）。 -->
    <p v-if="notice" class="notice">{{ notice }}</p>

    <!-- ================= 区块 1：服务状态 ================= -->
    <section>
      <h2>1. 服务状态</h2>
      <div class="row">
        <!-- @click="loadHealth" 不带括号表示「把函数本身作为回调」，
             点击时 Vue 会自动调用它并传入原生事件对象。 -->
        <button @click="loadHealth">刷新状态</button>
        <span class="hint">检查 Django / MySQL / Redis 是否连通</span>
      </div>
      <!-- <pre> 保留空白和换行，适合原样显示 JSON。
           healthText 是 computed 计算属性，下面 script 里解释。 -->
      <pre>{{ healthText }}</pre>
    </section>

    <!-- ================= 区块 2：分类管理 ================= -->
    <section>
      <h2>2. 分类管理</h2>
      <div class="row">
        <!-- v-model="newCategory"：输入框的值和 data.newCategory 双向同步。
             @keyup.enter：只监听键盘「回车」，比监听所有 keyup 更精准。 -->
        <input
          v-model="newCategory"
          placeholder="新分类名称，例如：计算机"
          @keyup.enter="addCategory"
        />
        <button @click="addCategory">新增分类</button>
        <span class="hint">分类下有书时不允许删除（外键 PROTECT）</span>
      </div>

      <div class="chips">
        <!-- v-for 循环渲染分类标签。
             :key="c.id" 必须写：Vue 靠它判断「哪一项是新的、哪一项被删了」，
             不写会报警告，而且列表更新时可能出现输入框内容错位。
             后面的数字是 book_count，由后端反向统计得到（serializers.py 的
             SerializerMethodField + source="books.count"）。 -->
        <span v-for="c in categories" :key="c.id" class="chip">
          {{ c.name }}
          <b>{{ c.book_count }}</b>
          <!-- 这里把整个分类对象传给方法，而不是只传 id，
               因为删除后要弹窗提示名字，用对象更方便。
               .x 是自定义 class，样式里把按钮做成了小叉号。 -->
          <button class="x" title="删除分类" @click="removeCategory(c)">×</button>
        </span>
        <!-- v-if + length 判断：数组为空时显示提示，
             比「显示一个空盒子」友好。 -->
        <span v-if="!categories.length" class="hint">还没有分类</span>
      </div>
    </section>

    <!-- ================= 区块 3：图书 CRUD ================= -->
    <section>
      <h2>3. 图书管理</h2>

      <!-- 新增表单。
           注意 v-model 里是嵌套属性 form.title，Vue 2 也支持，能正常响应。 -->
      <div class="row form-row">
        <input v-model="form.title" placeholder="书名（必填）" @keyup.enter="addBook" />
        <input v-model="form.author" placeholder="作者" @keyup.enter="addBook" />
        <!-- v-model.number 是修饰符：把输入框里的字符串自动转成数字。
             不加的话，price 会是 "39" 而不是 39，虽然后端能转，
             但「没填」时是空字符串 ""，容易和 0 混淆。
             type="number" + min/step 只是浏览器层面的约束，后端仍会再校验。 -->
        <input v-model.number="form.price" type="number" min="0" step="0.01" placeholder="价格" />
        <input v-model.number="form.stock" type="number" min="0" placeholder="库存" />
        <!-- :value="null" 对应后端的「未分类」。
             ★ 这里必须用 :value（绑定 JS 的 null），
               如果写成 value="null"，那就是字符串 "null"，后端会报
               「“null” 不是合法的主键」。
             下拉框的 v-model 会拿选中项的 value 赋值给 form.category。 -->
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

        <!-- 下拉框变化立刻触发搜索（@change）。
             ★ 注意初始值是空字符串 '' 而不是 null：
               空字符串更容易判断「没有选分类」，而且不会被拼进 URL。 -->
        <select v-model="filterCategory" @change="doSearch">
          <option :value="''">全部分类</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>

        <!-- class="ghost" 是次要按钮样式（浅底深字），和主按钮区分开 -->
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
          <!-- 每一行对应一本书；:key 用 id -->
          <tr v-for="book in books" :key="book.id">
            <!-- ========== 编辑态 ==========
                 v-if 判断「当前正在编辑的是不是这一行」。
                 <template> 是一个不可见的包裹标签：
                   它本身不产生 DOM，只是为了让 v-if / v-else 能包住多个 <td>。
                   如果不使用 template，就得给每个 td 都写一遍 v-if。 -->
            <template v-if="editingId === book.id">
              <td>#{{ book.id }}</td>
              <!-- 编辑时输入框绑定的是 editDraft（草稿），不是 book 本身。
                   这一点非常关键：如果直接绑定 book.title，
                   用户打字时表格里的数据立刻就被改了（响应式），
                   点「取消」也回不去。用草稿就能做到「点保存才生效」。 -->
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
              <!-- 编辑态下创建时间不可改，直接显示 -->
              <td>{{ formatTime(book.created_at) }}</td>
              <td>
                <!-- 传 id 给 saveEdit：它需要知道要 PATCH 哪个地址 -->
                <button @click="saveEdit(book.id)">保存</button>
                <button class="ghost" @click="cancelEdit">取消</button>
              </td>
            </template>

            <!-- ========== 展示态 ==========
                 v-else 必须紧跟在 v-if 后面，中间不能插别的元素。 -->
            <template v-else>
              <td>#{{ book.id }}</td>
              <td>{{ book.title }}</td>
              <!-- author || '-' ：作者为空时显示短横线，避免空白单元格 -->
              <td>{{ book.author || '-' }}</td>
              <!-- 价格用 money() 格式化成 ¥39.00 -->
              <td>{{ money(book.price) }}</td>
              <td>{{ book.stock }}</td>
              <!-- category_name 来自后端的 SerializerMethodField，
                   没有分类时后端返回「未分类」 -->
              <td>{{ book.category_name }}</td>
              <td>{{ formatTime(book.created_at) }}</td>
              <td>
                <!-- 传整个 book 对象，方便 startEdit 复制出草稿 -->
                <button class="ghost" @click="startEdit(book)">编辑</button>
                <button class="danger" @click="removeBook(book)">删除</button>
              </td>
            </template>
          </tr>
        </tbody>
      </table>

      <!-- 列表为空时的空状态提示 -->
      <p v-if="!books.length" class="empty">没有匹配的图书。</p>

      <!-- 分页：第一页禁用上一页，最后一页禁用下一页。
           :disabled 绑定布尔值，true 时浏览器自带禁用效果（样式见 button:disabled）。 -->
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
        <!-- 任务执行期间禁用按钮，防止用户连点造成重复提交。
             按钮文字也随状态变化：生成中... / 生成库存报表 -->
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
 * ============================================================================
 * 逻辑部分
 * ============================================================================
 *
 * Vue 组件的核心概念（按重要性排序）：
 *   data       数据（状态）。必须是函数并 return 对象，
 *              这样每个组件实例都有自己独立的一份数据。
 *   computed   计算属性。由 data 推导而来，自动缓存：
 *              依赖的 data 没变，重复读取不会重新计算。
 *   methods    方法。放所有「做事」的函数（发请求、处理点击）。
 *   mounted    生命周期钩子。组件挂载到页面后执行一次，
 *              通常在这里发起初始数据的加载。
 *
 * 注意：在 methods / computed 里访问 data，必须加 this.：
 *       this.books 而不是 books。
 */

// 引入封装好的 axios 实例（baseURL = '/api'，超时 10 秒）
import { http } from './api'

export default {
  // 组件名。调试工具（Vue Devtools）里会显示它，
  // 也方便递归组件引用自己（本项目用不到）。
  name: 'App',

  /**
   * data：组件的「状态仓库」。
   *
   * ★ 为什么是函数而不是对象？
   *   Vue 2 要求 data 是一个返回新对象的函数。
   *   如果写成 data: { books: [] }，那么同一个组件的多个实例会共享
   *   同一个对象，一个实例改了数据，另一个实例也跟着变。
   *   写成函数，每次创建实例都会调用一次，得到全新的、互不干扰的对象。
   */
  data() {
    return {
      // ---- 服务状态 ----
      // health 存后端 /api/health/ 返回的原始 JSON
      health: null,
      // 请求失败时把错误信息存在这里（和 health 分开，便于模板判断）
      healthError: '',

      // ---- 提示信息 ----
      // 页面上那条橙色提示条的文字，空字符串表示不显示
      notice: '',

      // ---- 分类 ----
      categories: [],
      // 新增分类输入框的内容（v-model 双向绑定）
      newCategory: '',

      // ---- 图书列表 / 搜索 / 筛选 / 分页 ----
      // 当前页的图书数组（来自后端返回的 results 字段）
      books: [],
      // 总条数（来自后端返回的 count 字段），用来算总页数
      total: 0,
      // 当前页码，从 1 开始
      page: 1,
      // 每页条数。
      // ★ 必须和后端 settings.py 里的 PAGE_SIZE 一致，
      //   否则「总页数」会算错，翻页也会错位。
      pageSize: 5,
      // 搜索关键词（书名或作者）
      search: '',
      // 分类筛选值。'' 表示全部；数字表示某个分类 id。
      filterCategory: '',

      // ---- 新增表单 ----
      // 用一个对象管理 5 个字段，提交时直接取值，比 5 个独立变量清爽。
      // category 为 null 表示「未分类」。
      form: { title: '', author: '', price: 0, stock: 0, category: null },

      // ---- 行内编辑 ----
      // 正在编辑的那一行的 id；null 表示没有行在编辑状态。
      editingId: null,
      // 编辑草稿。点「保存」之前，所有修改都只在这个对象上，不影响表格。
      editDraft: { title: '', author: '', price: 0, stock: 0, category: null },

      // ---- 异步报表 ----
      // 保存最近一次查询到的任务状态 JSON（task_id / status / result）
      reportTask: null,
      // 是否正在执行报表任务，用来禁用按钮、切换按钮文字
      reportRunning: false
    }
  },

  /**
   * computed：计算属性。
   *
   * 和 methods 的区别：
   *   - computed 有缓存：依赖没变就直接返回上次的结果
   *   - methods 每次都重新执行
   * 所以「由 data 推导出来的值」优先用 computed。
   */
  computed: {
    // 把健康状态转换成一段可读文本。
    // 模板里直接 {{ healthText }} 即可，不用在模板里写 if/else 逻辑
    //（模板里塞太多逻辑会很难维护）。
    healthText() {
      // 有错误优先显示错误
      if (this.healthError) return `请求失败：${this.healthError}`
      // 还没请求回来
      if (!this.health) return '加载中...'
      // JSON.stringify 的第 3 个参数 2 表示「缩进 2 个空格」，
      // 这样 <pre> 里显示出来是格式化的、易读的 JSON。
      return JSON.stringify(this.health, null, 2)
    },

    // 总页数。
    // Math.ceil 向上取整：11 条 / 每页 5 条 = 2.2 → 3 页。
    // Math.max(1, ...) 保证至少 1 页：0 条时显示「第 1 / 1 页」而不是「第 1 / 0 页」。
    totalPages() {
      return Math.max(1, Math.ceil(this.total / this.pageSize))
    },

    // 异步任务结果格式化（和 healthText 同理）
    reportText() {
      if (!this.reportTask) return '尚未生成报表'
      return JSON.stringify(this.reportTask, null, 2)
    }
  },

  /**
   * mounted：生命周期钩子。
   *
   * 执行时机：组件的模板已经渲染成真实 DOM 之后。
   * 适合在这里发起「页面一打开就要有数据」的请求。
   *
   * ★ 这里三个请求是「同时发出」的（都返回 Promise 但没 await），
   *   目的是尽快加载页面，不必一个个排队等待。
   *   如果后面的请求依赖前面的结果，就必须用 await 串行。
   */
  mounted() {
    this.loadHealth() // 健康检查
    this.loadCategories() // 分类列表（下拉框要用）
    this.loadBooks() // 图书列表
  },

  /**
   * methods：组件的方法集合。
   *
   * 用 async/await 写异步请求，读起来像同步代码：
   *   const { data } = await http.get(...)
   * 等价于
   *   http.get(...).then(res => { const data = res.data })
   */
  methods: {
    // ================= 工具方法 =================

    /**
     * 时间格式化。
     *
     * 后端返回的时间长这样：
     *   "2026-11-08T19:36:30.807703+08:00"
     * 页面上想显示成：
     *   "2026-11-08 19:36:30"
     *
     * 做法：把 T 换成空格，再截取前 19 个字符。
     * ★ 这是最简单的「土办法」，不带时区转换。
     *   真实项目一般用 dayjs / date-fns 这类库处理时区。
     */
    formatTime(value) {
      return value ? value.replace('T', ' ').slice(0, 19) : ''
    },

    /**
     * 价格格式化。
     *
     * ★ 为什么用 Number(value || 0)？
     *   后端的 DecimalField 默认会被 DRF 序列化成「字符串」
     *   （COERCE_DECIMAL_TO_STRING 默认为 True），
     *   所以 book.price 实际是 "39.00" 这种字符串。
     *   字符串没有 toFixed 方法，必须先 Number() 转成数字。
     */
    money(value) {
      return `¥${Number(value || 0).toFixed(2)}`
    },

    /**
     * 统一错误提示。
     *
     * axios 抛出的错误对象结构：
     *   err.message           "Request failed with status code 400"
     *   err.response.data     后端返回的响应体（对象）
     *   err.response.status   HTTP 状态码
     *
     * DRF 的报错有两种常见形状：
     *   1. {"detail": "..."}              权限/404/自定义异常
     *   2. {"title": ["该字段不能为空。"]}  字段校验失败
     * 这里只处理了第 1 种；第 2 种会显示成 axios 的通用英文。
     * 想做完善可以遍历对象把所有字段错误拼起来。
     */
    showError(err) {
      const detail = err && err.response && err.response.data
      if (detail && detail.detail) {
        this.notice = `操作失败：${detail.detail}`
      } else {
        this.notice = `操作失败：${err.message}`
      }
    },

    // ================= 健康检查 =================

    /**
     * 请求 /api/health/，检查 Django / MySQL / Redis 是否正常。
     *
     * try/catch/finally 的用法：
     *   try      正常逻辑
     *   catch    出错时兜底（网络断了、后端 500）
     *   finally  不管成功失败都会执行（这里没用，但先请求完再说）
     */
    async loadHealth() {
      this.healthError = ''
      try {
        // 解构赋值：const { data } = response
        // 等价于 const data = response.data
        // axios 的响应对象是 { data, status, headers, config, ... }，
        // 我们通常只关心 data。
        const { data } = await http.get('/health/')
        this.health = data
      } catch (err) {
        // 这里不弹全局提示，只在区块里显示错误，避免干扰其它操作
        this.healthError = err.message
      }
    },

    // ================= 分类 =================

    /**
     * 加载分类列表。
     *
     * ★ 分类接口关闭了分页（视图里 pagination_class = None），
     *   所以返回的 data 直接就是数组 [{id, name, book_count}, ...]，
     *   而不是图书那种 {count, results} 结构。
     */
    async loadCategories() {
      const { data } = await http.get('/categories/')
      this.categories = data
    },

    /**
     * 新增分类。
     * 流程：校验非空 → POST → 清空输入框 → 重新拉列表 → 提示成功
     */
    async addCategory() {
      // .trim() 去掉首尾空格，防止用户输入 "  " 这种「看起来有内容」的空串
      const name = this.newCategory.trim()
      if (!name) return

      this.notice = ''
      try {
        // POST /api/categories/，请求体 { name: "计算机" }
        // axios 会自动设置 Content-Type: application/json 并序列化。
        await http.post('/categories/', { name })
        this.newCategory = ''

        // 重新拉列表，而不是手动 push 到数组里。
        // 好处：拿到的数据和后端完全一致（包括后端生成的 id），
        // 也顺便验证了「创建确实成功了」。
        await this.loadCategories()
        this.notice = `分类「${name}」已创建`
      } catch (err) {
        // 常见错误：分类名重复（后端 unique 约束）→ 400
        this.showError(err)
      }
    },

    /**
     * 删除分类。
     *
     * ★ 后端把外键设成了 on_delete=models.PROTECT：
     *   分类下面如果还有书，删除会抛 ProtectedError，
     *   视图里捕获后返回 400 + {"detail": "该分类下还有 N 本书，不能删除"}。
     *   前端不需要特别判断，走统一的 showError 即可。
     */
    async removeCategory(category) {
      // window.confirm 返回 true/false，用户点「取消」就直接返回
      if (!window.confirm(`确定删除分类「${category.name}」吗？`)) return

      this.notice = ''
      try {
        await http.delete(`/categories/${category.id}/`)

        // ★ 边界情况：如果用户当前正按这个分类筛选，
        //   删除后列表会一直是空的（筛选值指向了一个不存在的分类），
        //   所以要把筛选重置，并回到第一页。
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

    // ================= 图书列表 =================

    /**
     * 加载图书列表（带搜索、筛选、分页）。
     *
     * axios 的 params 选项会把对象拼成查询字符串：
     *   { search: 'python', page: 2 }
     *   → /api/books/?search=python&page=2
     *
     * ★ 值为 undefined 的参数会被 axios 自动忽略。
     *   所以这里用 `this.search || undefined`：
     *   搜索框为空时，URL 里就不会出现 "search="，
     *   后端也就不会用空字符串去匹配（虽然空搜索通常也无影响，但更干净）。
     */
    async loadBooks() {
      const { data } = await http.get('/books/', {
        params: {
          search: this.search || undefined,
          category: this.filterCategory || undefined,
          page: this.page
        }
      })

      // 分页接口返回 { count, next, previous, results }：
      //   count     总条数
      //   next      下一页的完整 URL（没有则为 null）
      //   previous  上一页的完整 URL
      //   results   当前页的数据数组
      this.books = data.results
      this.total = data.count

      // ★ 边界情况：删掉最后一页的最后一条数据后，
      //   当前页码可能超过总页数（比如共 2 页，你停在第 2 页，
      //   删完后只剩 1 页），此时后端会返回空数组。
      //   这里自动退回最后一页并重新加载。
      if (this.page > this.totalPages) {
        this.page = this.totalPages
        this.loadBooks()
      }
    },

    // 搜索：必须先把页码重置为 1，
    // 否则你在第 3 页搜索，结果只有 1 页，会直接看到「空列表」。
    doSearch() {
      this.page = 1
      this.loadBooks()
    },

    // 重置所有筛选条件，回到第一页
    resetFilters() {
      this.search = ''
      this.filterCategory = ''
      this.page = 1
      this.loadBooks()
    },

    // 跳转到指定页。
    // 上一页/下一页按钮传进来的是 page-1 / page+1，
    // 越界的情况已经被 :disabled 挡住了，所以这里不用再判断。
    goPage(target) {
      this.page = target
      this.loadBooks()
    },

    // ================= 图书增删改 =================

    /**
     * 新增图书。
     *
     * 提交的字段：
     *   title    必填（后端校验）
     *   author   可空
     *   price    数字，空时给 0
     *   stock    数字，空时给 0
     *   category 分类 id 或 null
     */
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
          // ★ this.form.price || 0：
          //   用户把输入框清空时，v-model.number 得到的是 ""（空字符串），
          //   空字符串会被后端当成非法数字，所以这里兜底成 0。
          price: this.form.price || 0,
          stock: this.form.stock || 0,
          category: this.form.category || null
        })

        // 清空表单。注意要「整体替换」成一个新对象，
        // 而不是逐个字段赋值 —— 两种写法 Vue 2 都能响应，
        // 但整体替换更不容易漏掉字段。
        this.form = { title: '', author: '', price: 0, stock: 0, category: null }

        // 新增后回到第一页：新书通常出现在最后（按 id 排序），
        // 留在当前页可能看不到它。
        this.page = 1
        await this.loadBooks()
        // 分类的 book_count 变了，也要刷新分类，
        // 否则标签上的数字还是旧的。
        await this.loadCategories()
        this.notice = '新增成功'
      } catch (err) {
        this.showError(err)
      }
    },

    /**
     * 进入编辑态。
     *
     * ★ 关键：把数据「复制」到 editDraft，而不是共用一个对象。
     *   price 用 Number() 转一下，因为后端返回的是字符串 "39.00"，
     *   而 <input type="number"> 需要数字，否则输入框可能是空的。
     */
    startEdit(book) {
      this.editingId = book.id
      this.editDraft = {
        title: book.title,
        author: book.author,
        price: Number(book.price),
        stock: book.stock,
        category: book.category
      }
    },

    // 取消编辑：只清掉 editingId，
    // 草稿对象留着也没关系（下次 startEdit 会被覆盖）。
    // 因为表格展示的是 books 里的原始数据，从没被改过，所以界面自然恢复。
    cancelEdit() {
      this.editingId = null
    },

    /**
     * 保存编辑。
     *
     * 用 PATCH 而不是 PUT：
     *   PUT    全量更新，没传的字段会被重置（需要传所有必填字段）
     *   PATCH  局部更新，只改传过去的字段
     * 对于「行内编辑」这种只改部分字段的场景，PATCH 更合适。
     *
     * ★ 另一个坑：本项目模型里很多字段有 default 值，
     *   导致即使发 PUT 只传 title 也会成功（DRF 认为有 default 就不是必填），
     *   表现为「PUT 看起来像 PATCH」。不要依赖这个行为，语义上该用 PATCH 就用 PATCH。
     */
    async saveEdit(id) {
      if (!this.editDraft.title.trim()) {
        this.notice = '书名不能为空'
        return
      }

      this.notice = ''
      try {
        await http.patch(`/books/${id}/`, {
          title: this.editDraft.title.trim(),
          author: this.editDraft.author.trim(),
          price: this.editDraft.price || 0,
          stock: this.editDraft.stock || 0,
          category: this.editDraft.category || null
        })

        this.editingId = null
        await this.loadBooks()
        // 改分类会让两个分类的 book_count 变化，所以刷新分类
        await this.loadCategories()
        this.notice = '保存成功'
      } catch (err) {
        this.showError(err)
      }
    },

    /**
     * 删除图书。
     * 删除后同样要处理「当前正在编辑这一行」的情况，
     * 否则 editingId 会指向一个已经不存在的 id。
     */
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

    // ================= Celery 异步报表 =================

    /**
     * 触发「生成库存报表」。
     *
     * 为什么不能像其它接口一样 await 结果？
     *   因为这个任务被设计成「可能很慢」，后端收到请求后立刻返回 202 +
     *   task_id，真正的计算在 Celery worker 里进行。
     *   所以这里要「提交任务 → 再轮询查询结果」两步走。
     */
    async runReport() {
      this.notice = ''
      this.reportRunning = true
      try {
        // 提交任务：接口立刻返回 { task_id: "xxx" }
        const { data } = await http.post('/tasks/report/')

        // 先把「排队中」的状态显示出来，用户就知道点到了
        this.reportTask = { task_id: data.task_id, status: 'PENDING' }

        // 开始轮询
        await this.pollReport(data.task_id)
      } catch (err) {
        this.showError(err)
      } finally {
        // ★ finally 保证：不管成功、失败、还是抛异常，
        //   按钮都会恢复可用。否则一旦出错，按钮就永远禁用了。
        this.reportRunning = false
      }
    },

    /**
     * 轮询任务状态。
     *
     * 简化版实现：最多查 12 次，每次间隔 700ms（总计约 8.4 秒）。
     * 真实项目通常会：
     *   - 用更长的超时或指数退避（1s、2s、4s...）
     *   - 页面切走时停止轮询
     *   - 用 WebSocket 代替轮询（更实时、更省资源）
     *
     * Celery 的四种状态：
     *   PENDING   排队中 / 还没被 worker 领取
     *   STARTED   正在执行（需要 CELERY_TASK_TRACK_STARTED = True 才看得到）
     *   SUCCESS   成功，结果在 result 字段
     *   FAILURE   失败，错误在 result 字段里
     *
     * ★ 最坑的一点：如果 worker 根本没启动，
     *   任务永远停在 PENDING，这里就会查满 12 次然后放弃。
     */
    async pollReport(taskId) {
      for (let i = 0; i < 12; i += 1) {
        // new Promise + setTimeout：把「等待 700 毫秒」变成可以 await 的 Promise。
        // 直接用 setTimeout 是回调风格，没法 await。
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
/* ============================================================================
   样式部分：纯 CSS，不涉及任何逻辑。
   由于没有写 scoped，这些样式是全局的（会影响到整个页面）。
   本项目只有一个组件，所以影响不大；
   多个组件时建议加 <style scoped>，让样式只作用于当前组件。
   ============================================================================ */

/* 让所有元素的宽高包含 padding 和 border，
   这样设置宽度时不用再手动减掉内边距，布局更好算。 */
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: #f5f6f8;
  color: #222;
  /* 字体栈：从系统默认字体开始，逐个回退，保证中英文都有好看的字体 */
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
}

/* 页面主体：最宽 1100px 并水平居中（margin: 0 auto 的经典居中写法） */
.app {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 16px 60px;
}

header h1 {
  margin: 0 0 6px;
  font-size: 26px;
}

/* 副标题 */
.sub {
  margin: 0 0 20px;
  color: #777;
  font-size: 13px;
}

/* 每个功能区块：白底卡片 */
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

/* 横向排列的一行：flex + gap 是现在最省事的布局方式，
   不用再算 margin，也不会出现「最后一个元素多出边距」的问题。
   flex-wrap: wrap 让它在窄屏时自动换行。 */
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
  outline: none; /* 去掉浏览器默认的蓝色外框，改用下面的 border-color 高亮 */
}

/* 聚焦时边框变蓝，给用户「当前在这个输入框」的反馈 */
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

/* 禁用态：变灰 + 禁止光标（对应 :disabled 属性） */
button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

/* 次要按钮：浅色底、深色字 */
button.ghost {
  background: #eef2ff;
  color: #3730a3;
}

/* 危险操作按钮（删除） */
button.danger {
  background: #dc2626;
}

/* 灰色小字说明 */
.hint {
  color: #888;
  font-size: 12px;
}

/* 提示条：橙色系 */
.notice {
  background: #fff7ed;
  border: 1px solid #fdba74;
  color: #9a3412;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
}

/* 深色的代码块，用来显示 JSON。
   overflow: auto 保证内容太长时出现滚动条，而不是撑破布局。 */
pre {
  background: #0f172a;
  color: #d1fae5;
  padding: 12px;
  border-radius: 8px;
  font-size: 12px;
  overflow: auto;
  margin: 0;
}

/* 分类标签容器 */
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 单个分类标签：圆角药丸形状（border-radius: 999px） */
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

/* 标签里的书籍数量，用蓝色突出 */
.chip b {
  color: #2563eb;
}

/* 删除分类的小叉号：透明背景 + 灰色 */
.chip .x {
  background: transparent;
  color: #94a3b8;
  padding: 0 2px;
  font-size: 15px;
  line-height: 1;
}

/* 鼠标悬停变红，暗示「这是删除」 */
.chip .x:hover {
  color: #dc2626;
}

/* 数据表格：border-collapse 让相邻单元格的边框合并成一条，
   不然会出现 2px 粗的双线。 */
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

/* 表格里的输入框占满单元格 */
td input,
td select {
  width: 100%;
  padding: 5px 6px;
}

/* 表格里的按钮小一号，避免撑高行 */
td button {
  padding: 4px 8px;
  margin-right: 4px;
}

/* 空列表提示 */
.empty {
  color: #999;
  font-size: 13px;
}

/* 分页条：去掉底部多余的外边距 */
.pager {
  margin-top: 12px;
  margin-bottom: 0;
}
</style>
