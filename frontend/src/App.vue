<!--
  ============================================================================
  App.vue —— 本项目的「唯一页面组件」（Vue 单文件组件 SFC）

  ============================================================================
  一、.vue 文件是什么？
  ============================================================================
  一个 .vue 文件叫「单文件组件」（Single File Component，SFC），
  它把「一个页面/一个组件」需要的东西全放在同一个文件里：

      <template>  ->  结构（HTML，决定页面长什么样）
      <script>    ->  逻辑（JS，决定数据和行为）
      <style>     ->  样式（CSS，决定好看不好看）

  对比传统写法：以前要拆成 index.html + index.js + index.css 三个文件，
  改一个小功能要来回切三次；SFC 把它们收拢到一个文件，心智负担小很多。

  ★ 浏览器不认识 .vue，是 @vitejs/plugin-vue2 在开发时把它拆成三部分，
    分别处理后再拼成 JS 给浏览器——这就是为什么必须跑 Vite 开发服务器。

  ============================================================================
  二、Vue 的核心思想：数据驱动视图
  ============================================================================
  你不需要手动操作 DOM（不用 document.getElementById、不用 innerHTML）。
  只要改 data 里的变量，页面自动跟着变。这叫「响应式」。

      改 this.notes              ->  表格自动重绘
      改 this.page               ->  页码文字自动更新
      改 this.edits[id]          ->  对应行变成输入框（★ 要用 $set，见下方）

  ★ 反过来说：如果你发现「数据改了页面却没变」，99% 是因为
    你改的方式 Vue 2 监听不到（新增对象属性、用下标改数组），
    这时要用 this.$set / this.$delete。

  ============================================================================
  三、这个页面包含三个功能区
  ============================================================================
      1. 服务状态：调 /api/health/ 看 MySQL 和 Redis 通不通
      2. Celery 异步任务：提交一个加法任务，然后轮询查结果
      3. Notes CRUD：增删改查 + 搜索 + 分页 + ★「先编辑后同步」草稿机制
  ============================================================================
-->

<template>
  <!--
    ==========================================================================
    模板部分（template）
    ==========================================================================
    Vue 的模板就是「HTML + 指令」。指令都以 v- 开头（少数用简写）。
    先把下面这几个用到的记住，整个文件就没有看不懂的地方了：

      {{ 表达式 }}        插值：把 JS 表达式的值显示到页面上（会自动转义，防 XSS）
      v-model="x"         双向绑定：输入框 <=> data 里的 x，改哪边都同步
      v-if / v-else       条件渲染：条件为假时这个元素「根本不存在于 DOM」
      v-for="item in list" 循环渲染：列表有几个元素就生成几份 DOM
      @click="fn"         事件绑定（@ 是 v-on: 的简写）
      :disabled="expr"    动态属性（: 是 v-bind: 的简写，值是变量/表达式）

    ★ v-if 和 v-show 的区别（面试高频）：
        v-if   -> 假的元素直接不创建，切换时销毁/重建，初始渲染成本低但切换成本高
        v-show -> 元素始终存在，只是加 display:none，切换成本低但初始渲染成本高
      频繁切换用 v-show，条件很少变用 v-if。本项目用 v-if。
    ==========================================================================
  -->
  <div class="app">
    <!-- 页面主标题 -->
    <h1>Django 4.2 + Celery + Vue 2.7</h1>

    <!-- 副标题：把用到的技术栈和端口写出来，方便一眼确认环境是否对 -->
    <p class="sub">MySQL 8.4（3307） · Redis（6380） · Vite 代理 /api</p>

    <!-- ======================================================================
         区块 1：服务状态（健康检查）
         ====================================================================== -->
    <section>
      <h2>
        1. 服务状态
        <!-- @click="loadHealth"：点击时调用 methods 里的 loadHealth 方法。
             ★ 注意不要写成 @click="loadHealth()" ——
               虽然这样也能跑，但 Vue 会把「函数调用结果」当成处理函数，
               某些场景（比如要传 $event）会出问题。绑定方法名即可，Vue 会自己调用。 -->
        <button @click="loadHealth">刷新</button>
      </h2>

      <!-- <pre> 保留空白和换行，适合展示 JSON。
           这里显示的是 computed 计算属性 healthText，
           它会根据 health / healthError 自动算出要显示的文本。 -->
      <pre>{{ healthText }}</pre>
    </section>

    <!-- ======================================================================
         区块 2：Celery 异步任务（演示「接口秒回、任务后台跑」）
         ====================================================================== -->
    <section>
      <h2>2. Celery 异步任务（加法）</h2>

      <div class="row">
        <!-- v-model.number：双向绑定 + 自动把输入转成数字。
             ★ 不加 .number 的话拿到的是字符串 "1"，后端虽然能 int() 转换，
               但前端自己算的时候就会出现 "1" + "2" = "12" 这种坑。
             type="number" 只是让浏览器显示数字键盘/上下箭头，
               它并不能保证 v-model 拿到的是 number 类型（要配合 .number）。 -->
        <input v-model.number="a" type="number" />

        <span>+</span>

        <input v-model.number="b" type="number" />

        <button @click="runAddTask">提交任务</button>
      </div>

      <!-- 显示任务状态：PENDING / STARTED / SUCCESS，以及最终结果 -->
      <pre>{{ taskText }}</pre>
    </section>

    <!-- ======================================================================
         区块 3：Notes 的 CRUD + 搜索 + 分页 + 手动同步
         ====================================================================== -->
    <section>
      <h2>3. Notes CRUD + 搜索 + 分页</h2>

      <!-- ---------------------------------------------------------------
           3.1 新增表单（这个是「立即提交」，和下面的编辑草稿不同）
           --------------------------------------------------------------- -->
      <div class="row">
        <!-- v-model="form.title"：绑定到 data.form.title。
             ★ 这里绑的是「对象的属性」而不是一个基本类型变量，
               Vue 能监听到，因为它一开始就存在于 form 对象里（不是后加的属性）。
             @keyup.enter：按下回车就触发新增，省得去点按钮。
               同一个元素可以同时有 v-model 和 @keyup，互不影响。 -->
        <input v-model="form.title" placeholder="标题" @keyup.enter="addNote" />
        <input v-model="form.content" placeholder="内容" @keyup.enter="addNote" />

        <button @click="addNote">新增</button>
      </div>

      <!-- ---------------------------------------------------------------
           3.2 搜索栏
           --------------------------------------------------------------- -->
      <div class="row search-row">
        <input
          v-model="search"
          placeholder="搜索标题或内容，回车确认"
          @keyup.enter="doSearch"
        />
        <button @click="doSearch">搜索</button>
        <!-- class="ghost"：只是「幽灵按钮」的样式（浅色底），不影响逻辑 -->
        <button class="ghost" @click="resetSearch">重置</button>

        <!-- {{ total }} 来自后端分页返回的 count，是「符合条件的总条数」，
             不是当前页条数（当前页条数是 notes.length）。 -->
        <span class="hint">共 {{ total }} 条</span>
      </div>

      <!-- ---------------------------------------------------------------
           3.3 同步工具栏（本项目的「特色功能」）

           设计意图：
             用户点「编辑」后，改动只存在浏览器内存里（edits 草稿），
             不会立刻发请求。等改完多条，再统一点「同步到后端」，
             一次性 PATCH 给后端写进 MySQL。
           好处：减少请求次数，避免「改一个字就存一次库」。
           --------------------------------------------------------------- -->
      <div class="row toolbar">
        <!-- :disabled 的值是一个表达式：
               !dirtyCount  -> 没有任何「真正改动过的」行时禁用
               ||           -> 或者
               syncing      -> 正在同步中也禁用（防止重复点击发两遍请求）
             ★ 这里用 dirtyCount 而不是 editCount：
               editCount 是「处于编辑状态的行数」（可能点了编辑但没改），
               dirtyCount 是「内容真的变了的行数」。
               没改动就没必要同步。 -->
        <button :disabled="!dirtyCount || syncing" @click="syncAll">
          <!-- 模板里可以写三目运算符和模板字符串（反引号）。
               syncing 为真 -> 显示"同步中..."；
               否则 -> 显示"同步到后端（3）"这样的待同步数量。 -->
          {{ syncing ? '同步中...' : `同步到后端（${dirtyCount}）` }}
        </button>

        <!-- 取消所有草稿：只要有任意一行在编辑就可用 -->
        <button class="ghost" :disabled="!editCount" @click="cancelAll">
          取消全部修改
        </button>

        <!-- v-if / v-else 二选一显示：
               有同步结果提示时显示绿色文字；
               否则显示灰色的使用说明。
             ★ v-else 必须「紧跟」在 v-if 元素后面（中间不能有其他元素），
               否则 Vue 编译报错，或者 v-else 被当成孤立元素忽略。 -->
        <span v-if="syncMsg" class="ok">{{ syncMsg }}</span>
        <span v-else class="hint">编辑后不会立即提交，点「同步」才写入数据库</span>
      </div>

      <!-- ---------------------------------------------------------------
           3.4 数据表格
           --------------------------------------------------------------- -->
      <table>
        <thead>
          <tr>
            <!-- style 写宽度：让各列比例稳定，否则内容长短会导致表格抖动 -->
            <th style="width: 60px">ID</th>
            <th>标题</th>
            <th>内容</th>
            <th style="width: 150px">创建时间</th>
            <th style="width: 130px">操作</th>
          </tr>
        </thead>

        <tbody>
          <!-- v-for 循环：notes 里有几条数据就渲染几个 <tr>。
               ★ :key="note.id" 是必须写的，而且必须唯一。
                 它的作用是告诉 Vue「这一行对应哪条数据」，
                 这样在列表增删/排序时，Vue 能精确地复用或移动 DOM，
                 而不是把整个表格重新渲染一遍。

                 ★ 千万别用 index 当 key（:key="index"）：
                   翻页/搜索后列表内容全变了但 index 还是 0,1,2...，
                   Vue 会误以为「数据没变只是内容改了」，从而复用错的 DOM，
                   导致输入框里的内容串行、状态错乱。用数据自己的 id 才安全。 -->
          <tr
            v-for="note in notes"
            :key="note.id"
            :class="{ dirty: isDirty(note.id) }"
          >
            <!-- :class 传对象：键是类名，值是布尔。
                 这一行有未同步的改动时，会额外加上 dirty 类（浅黄底色）。
                 ★ 这是 CSS 类绑定的标准写法，比字符串拼接可读性好得多。 -->

            <!-- -----------------------------------------------------------
                 【编辑态】这一行有草稿时（edits[note.id] 存在），显示输入框
                 -----------------------------------------------------------
                 ★ <template v-if="..."> 是什么？
                   <template> 是一个「不产生真实 DOM 的容器」，
                   只用来包裹多个元素、承载 v-if/v-for。
                   渲染后你在浏览器元素面板里看不到 <template> 标签，
                   只有它里面的 5 个 <td>。
                   如果直接把 v-if 写在 <tr> 上，那就变成「整行显示/隐藏」，
                   而这里需要的是「行内换一套单元格」。 -->
            <template v-if="edits[note.id]">
              <!-- # 加 id，让人一眼看出这是哪条数据 -->
              <td>#{{ note.id }}</td>

              <!-- ★★★ 这里绑的是「草稿」而不是 note 本身 ★★★
                   v-model="edits[note.id].draft.title"
                   用户在输入框里打字，改的是 draft.title，
                   note.title（来自后端的响应式数据）一点没动。
                   所以页面上的表格数据不会「假保存」，
                   只有点同步、后端返回成功后重新 loadNotes，才会看到新值。
                   这就是「先编辑后同步」的实现核心。 -->
              <td><input v-model="edits[note.id].draft.title" /></td>
              <td><input v-model="edits[note.id].draft.content" /></td>

              <!-- 创建时间不允许改，仍然显示原值 -->
              <td>{{ formatTime(note.created_at) }}</td>

              <td>
                <!-- 撤销这一行的编辑：把草稿删掉，行就变回普通文本态 -->
                <button class="ghost" @click="cancelEdit(note.id)">撤销</button>
              </td>
            </template>

            <!-- -----------------------------------------------------------
                 【阅读态】没有草稿时，显示普通文本 + 编辑/删除按钮
                 -----------------------------------------------------------
                 ★ v-else 和上面的 v-if 是一对，必须相邻。 -->
            <template v-else>
              <td>#{{ note.id }}</td>
              <td>{{ note.title }}</td>
              <!-- ★ content 允许为空，当它是空字符串时会显示成空白单元格，
                   这是正常的（后端模型里 content 是 blank=True）。 -->
              <td>{{ note.content }}</td>
              <td>{{ formatTime(note.created_at) }}</td>

              <td>
                <!-- 传入整个 note 对象，方法里要拿它的当前值做草稿初值 -->
                <button class="ghost" @click="startEdit(note)">编辑</button>
                <!-- 只传 id 就够了，删除只需要主键 -->
                <button class="danger" @click="removeNote(note.id)">删除</button>
              </td>
            </template>
          </tr>
        </tbody>
      </table>

      <!-- 空状态提示：notes.length 为 0（包括搜索无结果、一页都没数据）时显示。
           ★ 用 !notes.length 而不是 notes.length === 0，更简洁且效果一样。 -->
      <p v-if="!notes.length" class="empty">没有匹配的数据。</p>

      <!-- ---------------------------------------------------------------
           3.5 分页器
           --------------------------------------------------------------- -->
      <div class="row pager">
        <!-- 第一页时「上一页」不可点：
               page <= 1 -> disabled 为 true
             ★ 用 <= 而不是 ===，是为了防御异常值（万一 page 被置成 0）。 -->
        <button :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>

        <span>第 {{ page }} / {{ totalPages }} 页</span>

        <!-- 最后一页时「下一页」不可点 -->
        <button :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>

        <!-- pageSize 是前端常量 5，必须和后端 settings.REST_FRAMEWORK 的
             PAGE_SIZE 一致，否则会出现「后端给 5 条，前端按 10 条算页数」的错乱。 -->
        <span class="hint">每页 {{ pageSize }} 条</span>
      </div>
    </section>
  </div>
</template>

<script>
/**
 * ============================================================================
 * 逻辑部分（script）
 * ============================================================================
 *
 * 【一个 Vue 组件由哪几块组成？】
 *   data()      数据（状态）：所有会变的东西都放这里，变了页面自动更新
 *   computed    计算属性：由 data 推导出来的值，有缓存，依赖不变就不重算
 *   methods     方法：处理点击、发请求、改数据
 *   mounted     生命周期钩子：组件挂载到页面后执行一次（适合初始化请求）
 *
 * 【data 为什么必须是「函数」而不是「对象」？】
 *   因为组件可能被复用多份。如果写成对象，所有实例会共享同一个引用，
 *   改 A 的数据 B 也跟着变（这是 Vue 2 里非常经典的 bug）。
 *   写成函数，每次创建实例都 return 一个全新对象，彼此隔离。
 *   ★ 根实例（main.js 里的 new Vue）可以是对象，因为它只会有一个；
 *     但组件里必须写函数，没有例外。
 *
 * 【computed 和 methods 的区别（高频问题）】
 *   computed：有缓存。依赖的 data 没变，多次访问只算一次。
 *   methods ：没缓存。每次调用都重新执行。
 *   所以「由 data 推导出的值」优先用 computed（比如 dirtyCount、totalPages）。
 *   ★ 注意 computed 里不要写副作用（不要发请求、不要改 data），
 *     它应该是「纯函数」。
 * ============================================================================
 */

// 引入封装好的 axios 实例。注意是「具名导入」，必须带花括号。
// 这个 http 的 baseURL 是 '/api'，所以下面写 '/notes/' 实际请求 /api/notes/。
import { http } from './api'

export default {
  // 组件名。作用：调试工具（Vue Devtools）里能看出是哪个组件，
  // 报错信息里的组件栈也更清晰。没什么神秘的运行时功能。
  name: 'App',

  // ==========================================================================
  // 数据（data）
  // ==========================================================================
  data() {
    // ★ 必须 return 一个对象，不能直接写 data: {...}
    return {
      // ----------------------------------------------------------------------
      // 第 1 组：服务状态
      // ----------------------------------------------------------------------
      health: null, // 后端 /api/health/ 返回的对象 {status, db, redis}；null 表示还没加载
      healthError: '', // 请求失败时的错误信息（空字符串表示没有错误）

      // ----------------------------------------------------------------------
      // 第 2 组：Celery 任务
      // ----------------------------------------------------------------------
      a: 1, // 第一个加数（默认值让用户打开页面就能点一下试试）
      b: 2, // 第二个加数
      task: null, // 任务状态对象 {task_id, status, result?}，null 表示还没提交过

      // ----------------------------------------------------------------------
      // 第 3 组：新增表单
      // ----------------------------------------------------------------------
      // ★ 放在一个对象里而不是拆成两个变量（title/content），
      //   好处是提交时可以直接 http.post('/notes/', this.form)，
      //   重置时一句 this.form = {title:'', content:''} 就搞定。
      form: { title: '', content: '' },

      // ----------------------------------------------------------------------
      // 第 4 组：列表 / 搜索 / 分页
      // ----------------------------------------------------------------------
      notes: [], // 当前页的数据数组（来自后端分页返回的 results，不是整个响应）
      search: '', // 搜索关键词（对应 URL 的 ?search=）
      page: 1, // 当前页码（对应 URL 的 ?page=），从 1 开始不是 0
      pageSize: 5, // 每页条数。★ 必须和后端 PAGE_SIZE 保持一致，否则页数算错
      total: 0, // 符合条件的总条数（来自后端分页返回的 count）

      // ----------------------------------------------------------------------
      // 第 5 组：编辑草稿（本项目最有意思的部分）
      // ----------------------------------------------------------------------
      // 结构（用笔记 id 当键）：
      //   {
      //     1: {
      //       original: { title: '原标题', content: '原内容' },  // 进入编辑时的快照
      //       draft:    { title: '正在改', content: '正在改' }   // 用户正在编辑的草稿
      //     },
      //     5: { ... }
      //   }
      //
      // 为什么要存 original？
      //   为了判断「用户到底改了没有」。如果只存 draft，
      //   用户点开编辑又原样改回去，你也无法知道它其实没变，
      //   会把没变的行也 PATCH 一遍（浪费请求，还会刷新 created_at）。
      //
      // ★ 这个对象的所有键都是「运行时动态添加」的，
      //   所以必须用 this.$set 加键，否则 Vue 2 监听不到（见 startEdit 的注释）。
      edits: {},

      syncing: false, // 是否正在同步（用于禁用按钮 + 显示"同步中..."）
      syncMsg: '' // 同步结果提示（成功/失败的文案）
    }
  },

  // ==========================================================================
  // 计算属性（computed）
  // ==========================================================================
  computed: {
    /**
     * 服务状态的可读文本。
     *
     * 优先级：
     *   1. 有错误 -> 显示错误信息
     *   2. 还没加载 -> 显示"加载中..."
     *   3. 正常 -> 把健康检查的 JSON 格式化后显示
     *
     * ★ JSON.stringify(obj, null, 2) 的第二个参数 null 是「replacer」（不过滤字段），
     *   第三个参数 2 表示「缩进 2 空格」，这样 <pre> 里显示会换行且整齐。
     */
    healthText() {
      if (this.healthError) return `请求失败：${this.healthError}`
      if (!this.health) return '加载中...'
      return JSON.stringify(this.health, null, 2)
    },

    /**
     * 任务状态的可读文本。
     * 后端返回什么就原样格式化显示，方便观察 PENDING -> STARTED -> SUCCESS 的变化。
     */
    taskText() {
      if (!this.task) return '尚未提交任务'
      return JSON.stringify(this.task, null, 2)
    },

    /**
     * 总页数。
     *
     * Math.ceil(total / pageSize)：向上取整。
     *   12 条 / 每页 5 -> 2.4 -> 3 页（最后一页 2 条）
     *
     * Math.max(1, ...)：保底 1 页。
     *   ★ 为什么要保底？
     *     如果 total 是 0（比如搜索无结果），ceil(0/5) = 0，
     *     页面上就会显示「第 1 / 0 页」这种很怪的东西。
     *     保底 1 页后显示「第 1 / 1 页」，符合直觉。
     */
    totalPages() {
      return Math.max(1, Math.ceil(this.total / this.pageSize))
    },

    /**
     * 当前「处于编辑状态」的行数。
     *
     * Object.keys(对象) 返回所有键组成的数组，length 就是行数。
     * ★ 注意 keys 返回的是「字符串数组」，比如 ['1', '5']，
     *   所以后面 dirtyIds 里比较时也全是字符串，这一点要留意
     *   （见 isDirty 的注释）。
     *
     * 用途：「取消全部修改」按钮的禁用判断（一行都没编辑就没必要点）。
     */
    editCount() {
      return Object.keys(this.edits).length
    },

    /**
     * 「内容真的被改动过」的行 id 列表。
     *
     * 两步：
     *   1. Object.keys(this.edits) 拿到所有处于编辑态的 id（字符串）；
     *   2. filter 过滤出 draft 和 original 不一致的那些。
     *
     * ★ computed 有缓存：只要 edits 里的内容没变，多次访问 dirtyIds
     *   不会重复执行 filter。而 dirtyCount 依赖 dirtyIds，
     *   也是缓存的，所以「按钮上显示的数字」不会造成性能问题。
     */
    dirtyIds() {
      return Object.keys(this.edits).filter((id) =>
        this.isEntryDirty(this.edits[id])
      )
    },

    /**
     * 待同步数量，直接显示在按钮上。
     * 依赖 dirtyIds，所以能被缓存，不会每次渲染都重新计算。
     */
    dirtyCount() {
      return this.dirtyIds.length
    }
  },

  // ==========================================================================
  // 生命周期（mounted）
  // ==========================================================================
  /**
   * mounted：组件挂载到页面（DOM 已生成）之后自动执行一次。
   *
   * 为什么在这里发初始化请求？
   *   页面一打开就应该看到数据，不需要用户点按钮。
   *
   * ★ 为什么不用 created？
   *   created 时 DOM 还没生成，如果请求回来要操作 DOM 就会出问题。
   *   发纯数据请求两者都行，但用 mounted 更安全、更符合直觉。
   *
   * ★ 为什么这两个调用没有 await？
   *   它们互不依赖，让它们并行跑（近似并行），页面能更快出数据。
   *   如果 await 第一个再发第二个，总耗时就变成两者之和了。
   */
  mounted() {
    this.loadHealth()
    this.loadNotes()
  },

  // ==========================================================================
  // 方法（methods）
  // ==========================================================================
  methods: {
    // ----------------------------------------------------------------------
    // 1. 健康检查
    // ----------------------------------------------------------------------
    /**
     * 请求后端健康检查接口：GET /api/health/
     *
     * 后端会返回 {status: 'ok'|'degraded', db: true/false, redis: true/false}：
     *   - 全正常时 HTTP 200；
     *   - 依赖挂了时 HTTP 503（axios 会走 catch 分支）。
     *
     * ★ 这里有个设计取舍：
     *   503 在 axios 里属于「错误」，会进 catch，
     *   我们就拿不到响应体里的 db/redis 明细了。
     *   如果想在 503 时也显示明细，需要用 err.response.data 去取。
     *   本项目为了简洁，503 时统一显示错误消息。
     */
    async loadHealth() {
      this.healthError = '' // 每次请求前先清掉旧的错误，避免残留误导
      try {
        // 实际请求 /api/health/（baseURL '/api' + '/health/'）
        const { data } = await http.get('/health/')
        this.health = data // 交给 computed 的 healthText 去格式化显示
      } catch (err) {
        // err.message 通常是 "Request failed with status code 503" 这类文字
        this.healthError = err.message
      }
    },

    // ----------------------------------------------------------------------
    // 2. 工具方法
    // ----------------------------------------------------------------------
    /**
     * 把后端返回的 ISO 时间变短一点再显示。
     *
     * 后端给的是：2026-11-08T19:07:49.490123+08:00
     * 处理过程：
     *   replace('T', ' ')  -> 2026-11-08 19:07:49.490123+08:00
     *   slice(0, 19)       -> 2026-11-08 19:07:49   （只保留前 19 个字符）
     *
     * ★ 为什么不用 dayjs / moment 之类的库？
     *   只是为了裁字符串，用正则或库都属杀鸡用牛刀。
     *   真实项目里如果需要「几小时前」这种相对时间，再引入 dayjs 更合适。
     *
     * ★ 空值保护：value 为空时返回空字符串，避免 null.replace 报错。
     */
    formatTime(value) {
      return value ? value.replace('T', ' ').slice(0, 19) : ''
    },

    // ----------------------------------------------------------------------
    // 3. 列表加载 / 搜索 / 分页
    // ----------------------------------------------------------------------
    /**
     * 加载笔记列表。
     *
     * 请求：GET /api/notes/?search=xx&page=n
     *
     * ★ 后端（DRF 分页）返回的不是数组，而是：
     *     { count: 12, next: "http://...?page=2", previous: null, results: [...] }
     *   所以取数据要写 data.results，不是 data。
     *   这是一个非常常见的踩坑点（拿到 data 直接用，发现 length 是 undefined）。
     */
    async loadNotes() {
      const { data } = await http.get('/notes/', {
        // params 对象会被 axios 拼成查询字符串，并自动做 URL 编码。
        //
        // ★ search 为什么写 this.search || undefined？
        //   当搜索框为空时，我们希望 URL 里【不要出现】?search=，
        //   而不是 ?search= 空字符串（虽然效果一样，但地址更干净）。
        //   axios 会自动忽略值为 undefined 的参数，所以这个写法很实用。
        params: { search: this.search || undefined, page: this.page }
      })

      this.notes = data.results // 只取当前页的数据
      this.total = data.count // 总条数，用于算总页数

      // ---- 「删到最后一页变空」的自动回退 ----
      // 场景：你在第 3 页（只有 2 条），把这两条都删了，
      //       后端再查第 3 页会返回空数组，页面看起来像坏了。
      // 处理：发现当前页超出总页数，就退回最后一页重新加载。
      //
      // ★ 注意这里存在一次「递归调用」：loadNotes -> loadNotes。
      //   它只会发生一次（因为回退后 page 一定等于 totalPages，不会再触发），
      //   所以不用担心死循环。
      if (this.page > this.totalPages) {
        this.page = this.totalPages
        this.loadNotes()
      }
    },

    /**
     * 点击搜索：回到第 1 页再查。
     *
     * ★ 为什么必须重置 page？
     *   假设你现在在第 3 页，搜一个只有 2 条结果的关键词，
     *   请求 ?page=3 会返回空列表——用户会以为「搜不到」。
     *   重置到第 1 页才能看到结果。
     */
    doSearch() {
      this.page = 1
      this.loadNotes()
    },

    /**
     * 重置搜索：清空关键词后重新查询。
     * 复用 doSearch()，因为它已经把 page 重置到 1 了。
     */
    resetSearch() {
      this.search = ''
      this.doSearch()
    },

    /**
     * 翻页。
     * @param {number} target 目标页码（上一页传 page-1，下一页传 page+1）
     *
     * ★ 调用方（模板）已经用 :disabled 保证了不会越界，
     *   所以这里不需要再做范围校验。
     */
    goPage(target) {
      this.page = target
      this.loadNotes()
    },

    // ----------------------------------------------------------------------
    // 4. 新增 / 删除（立即请求后端）
    // ----------------------------------------------------------------------
    /**
     * 新增笔记：立即 POST，不走草稿机制。
     *
     * 为什么新增不做草稿？
     *   因为「新增」本来就要用户填完再提交，输入框就是草稿，
     *   没有「编辑后延迟同步」的必要。
     *
     * 流程：校验 -> POST -> 清空表单 -> 回到第 1 页 -> 重新加载
     */
    async addNote() {
      // 标题为空就不提交（后端也会校验必填，但前端先拦一下更友好）
      // ★ .trim() 去掉首尾空格：防止用户只输入空格就提交
      if (!this.form.title.trim()) return

      // 直接把整个 form 对象发过去：{title: '...', content: '...'}
      // 后端 NoteSerializer 会校验并创建，返回 201 + 新对象
      await http.post('/notes/', this.form)

      // 清空表单。★ 用「重新赋值」而不是修改属性，
      //   这样能确保是一个全新的对象，不会残留旧引用。
      this.form = { title: '', content: '' }

      // 新数据排在最前面（模型 Meta.ordering = ['-id']），所以回第 1 页看
      this.page = 1
      this.loadNotes()
    },

    /**
     * 删除笔记：立即请求后端（删除是很明确的动作，不适合做草稿）。
     *
     * @param {number} id 笔记主键
     */
    async removeNote(id) {
      await http.delete(`/notes/${id}/`)

      // ★ 如果这条正在编辑，要顺手把草稿也删掉，
      //   否则 edits 里会残留一个「幽灵草稿」：
      //   列表里已经没有这条了，但 editCount 还算它一份。
      //   （虽然页面不会渲染它，但按钮上的数字会莫名其妙多 1。）
      this.$delete(this.edits, id)

      this.loadNotes()
    },

    // ----------------------------------------------------------------------
    // 5. 草稿编辑（先编辑，后同步）
    // ----------------------------------------------------------------------
    /**
     * 进入编辑态：为这一行创建草稿。
     *
     * @param {object} note 这一行的原始数据（来自后端响应）
     *
     * ★★★ 为什么必须用 this.$set？★★★
     *   Vue 2 的响应式是在「初始化 data 时」递归遍历对象、用
     *   Object.defineProperty 给每个已有属性装上 getter/setter 实现的。
     *   之后【新增的】属性没有 getter/setter，改了也不会触发视图更新。
     *
     *   如果直接写 this.edits[note.id] = {...}：
     *     data 里确实多了这个键，但页面【不会有任何变化】，
     *     你会以为「代码没生效」，其实是响应式没追上。
     *
     *   this.$set(对象, 键, 值) 的额外步骤就是：
     *     设置值的同时，手动调用「通知依赖更新」，把界面刷新出来。
     *
     *   ★ 同理，删除属性要用 this.$delete。
     *     这是 Vue 2 官方的两大「响应式陷阱」，Vue 3 用 Proxy 重写后不再有这个问题。
     */
    startEdit(note) {
      this.$set(this.edits, note.id, {
        // original：进入编辑时的快照，用于之后判断「是否真的改过」
        original: { title: note.title, content: note.content },
        // draft：用户编辑的对象，初值和 original 完全一样
        // ★ 这里必须「复制」而不是直接引用 note：
        //   如果写成 draft: note，那么 v-model 改 draft 就等于改 note，
        //   表格里的文本会随输入实时变化，看起来像「已经保存了」，
        //   而且撤销时也没法还原。复制的意义在于「隔离」。
        draft: { title: note.title, content: note.content }
      })

      // 开始新编辑时清掉上一次的同步提示，避免文案误导
      this.syncMsg = ''
    },

    /**
     * 撤销某一行的修改：删掉草稿，该行自动回到普通文本态。
     * @param {number} id 笔记主键
     *
     * ★ 为什么用 this.$delete 而不是 delete this.edits[id]？
     *   同样的响应式原因：Vue 2 监听不到直接 delete，页面不会更新。
     */
    cancelEdit(id) {
      this.$delete(this.edits, id)
    },

    /**
     * 取消所有草稿：一次性清空。
     *
     * ★ 这里是「整个对象重新赋值」（this.edits = {}），
     *   不是逐个删键，所以不需要 $delete——
     *   给 data 里【已有的属性】赋新值，Vue 是能监听到的。
     *   （陷阱只发生在「新增/删除属性」上。）
     */
    cancelAll() {
      this.edits = {}
      this.syncMsg = ''
    },

    /**
     * 判断一条草稿「是否真的改过」。
     *
     * @param {object} entry {original, draft}
     * @returns {boolean}
     *
     * ★ 用 !== 逐字段比较，而不是 JSON.stringify 全量对比：
     *   字段少时这样更快、更直观，也更容易看出是哪一项不同。
     *   字段多了可以改成遍历 keys 比较。
     */
    isEntryDirty(entry) {
      return (
        entry.draft.title !== entry.original.title ||
        entry.draft.content !== entry.original.content
      )
    },

    /**
     * 判断某一行是否要加「未同步」的黄色底色（模板里 :class 用）。
     *
     * @param {number|string} id 笔记主键
     * @returns {boolean}
     *
     * ★ 注意一个细节：模板里是 isDirty(note.id)，传进来的是 number；
     *   而 this.edits 的键永远是 string（JS 对象的键都会被转成字符串）。
     *   好在 this.edits[id] 这种「用数字下标访问对象」时，
     *   JS 会自动把数字转成字符串 "1"，所以能正确取到值。
     *   但如果哪天要用 === 比较 id，就要记得先统一类型。
     */
    isDirty(id) {
      const entry = this.edits[id]
      return entry ? this.isEntryDirty(entry) : false
    },

    /**
     * 同步：把所有「改动过的」草稿一次性 PATCH 到后端。
     *
     * 完整流程：
     *   1. 取出 dirtyIds（只同步真正改过的，没改的不发请求）
     *   2. 守卫：没有改动 或 正在同步中 -> 直接 return
     *   3. 上锁：syncing = true（按钮变灰，防止连点）
     *   4. Promise.all 并行发送所有 PATCH
     *   5. 成功后清空草稿 + 重新拉列表（以数据库为准）
     *   6. finally 解锁
     *
     * ★ 为什么用 PATCH 而不是 PUT？
     *   PUT 是全量更新，要求把对象的所有字段都传一遍；
     *   PATCH 是局部更新，只传要改的字段即可。
     *   我们只改 title/content，用 PATCH 语义更准确、也更安全。
     *
     * ★ 为什么用 Promise.all 并行？
     *   同步 5 条，串行大约 5 × 单次耗时；并行大约等于 1 次耗时。
     *   ★ 代价：只要有一条失败，Promise.all 立刻 reject，
     *     但【其他请求已经发出去了，无法回滚】。
     *     真实项目里如果对一致性要求高，应该让后端提供「批量更新」接口，
     *     在一个事务里完成；或者用 Promise.allSettled 收集每条结果分别处理。
     */
    async syncAll() {
      const ids = this.dirtyIds

      // 守卫：
      //   !ids.length  -> 一条都没改，不发空请求
      //   this.syncing -> 正在同步，忽略重复点击
      if (!ids.length || this.syncing) return

      this.syncing = true
      this.syncMsg = ''

      try {
        // map 把每个 id 变成一个「PATCH 请求的 Promise」，
        // Promise.all 等它们全部成功。
        //
        // 请求体是 this.edits[id].draft，即 {title, content}。
        // ★ 这里只提交草稿里的字段，不提交 created_at（那是只读字段）。
        await Promise.all(
          ids.map((id) => http.patch(`/notes/${id}/`, this.edits[id].draft))
        )

        this.syncMsg = `已同步 ${ids.length} 条到 MySQL`

        // 同步成功后清空所有草稿
        this.edits = {}

        // 重新拉一次列表，用数据库里的最新数据（包括后端可能做的格式化）刷新页面。
        // ★ 为什么不直接把草稿写回 notes？
        //   因为「前端以为的结果」和「数据库的实际结果」可能不同
        //   （比如后端做了 trim、字段默认值、时间戳更新）。
        //   以服务端返回为准（server as source of truth）是最稳的做法。
        this.loadNotes()
      } catch (err) {
        // 任何一条失败都会走到这里
        this.syncMsg = `同步失败：${err.message}`
      } finally {
        // ★ finally 保证「无论成功失败都解锁」。
        //   如果忘了写，一旦出错 syncing 永远是 true，按钮就再也点不动了。
        this.syncing = false
      }
    },

    // ----------------------------------------------------------------------
    // 6. Celery 异步任务
    // ----------------------------------------------------------------------
    /**
     * 提交加法任务：POST /api/tasks/add/
     *
     * 后端立刻返回 202 + {task_id}（不等计算完成），
     * 前端拿到 id 后开始轮询查结果。
     *
     * 流程：
     *   提交 -> 先把状态设成 PENDING 显示给用户 -> 启动轮询
     */
    async runAddTask() {
      const { data } = await http.post('/tasks/add/', { a: this.a, b: this.b })

      // 先乐观地显示 PENDING：让用户马上看到「任务已提交」的反馈，
      // 而不是等第一次轮询回来才有内容。
      this.task = { task_id: data.task_id, status: 'PENDING' }

      // 注意这里【没有 await】：轮询是个后台过程，
      // 让它自己跑，不阻塞当前函数的返回。
      this.pollTask(data.task_id)
    },

    /**
     * 轮询任务结果。
     *
     * 为什么需要轮询？
     *   HTTP 是「请求-响应」模型，服务器没法主动推消息给浏览器
     *   （除非用 WebSocket / SSE）。
     *   所以前端只能「隔一会儿问一次」：任务好了没？
     *
     * 本实现的参数：
     *   最多查 10 次，每次间隔 800 毫秒 -> 最多等约 8 秒。
     *
     * @param {string} taskId Celery 返回的任务 id（UUID 字符串）
     *
     * ★ 更优雅的方案（了解即可）：
     *   1. 指数退避：间隔 0.5s、1s、2s、4s... 减少无效请求；
     *   2. 用 WebSocket / SSE 由服务器主动推送，完全不用轮询；
     *   3. 用 Celery 的 result_backend + 长轮询接口。
     *   本项目为了教学直观，用最简单的固定间隔轮询。
     */
    async pollTask(taskId) {
      for (let i = 0; i < 10; i += 1) {
        // 先等 800ms 再查。
        // 为什么要先等？因为刚提交的任务几乎不可能瞬间完成，
        // 立刻查大概率还是 PENDING，白费一次请求。
        //
        // ★ 这里的 Promise 只是用来「睡一会儿」：
        //   setTimeout 本身不支持 Promise，用 new Promise 包一层，
        //   把回调式的定时器变成可以 await 的形式。
        await new Promise((resolve) => setTimeout(resolve, 800))

        const { data } = await http.get(`/tasks/${taskId}/`)
        this.task = data // 每次拿到最新状态就刷新界面

        // 终态：成功或失败，都不用再问了，直接结束轮询
        if (data.status === 'SUCCESS' || data.status === 'FAILURE') return
      }

      // 走到这里说明查了 10 次还没结束（可能是 worker 没启动、任务卡住）
      // ★ 这是一个很好的排查提示：如果一直 PENDING，先检查
      //   celery -A config worker -l info 有没有跑起来。
    }
  }
}
</script>

<style>
/*
  ============================================================================
  样式部分（style）

  ★ 注意 <style> 没有加 scoped 属性，所以这些样式是「全局」的：
    会作用于整个页面（包括以后加的子组件）。
    如果加了 <style scoped>，Vue 会给每个元素加上 data-v-xxxx 属性，
    让样式只作用于当前组件。
    本项目只有一个组件，全局也无所谓；组件多了建议加 scoped 避免互相污染。

  ★ 另外，body 的样式写在 scoped 里是不会生效的
    （因为 body 不在这个组件的模板里），只能写全局样式。
  ============================================================================
*/

/* 让所有元素的 width 包含 padding 和 border（默认是 content-box，不含）。
   不加这一句，设了 width:100% 再加 padding 就会溢出容器。 */
* {
  box-sizing: border-box;
}

/* 页面整体背景和字体。
   font-family 列了一串，浏览器从左往右找第一个存在的字体：
   -apple-system / BlinkMacSystemFont -> macOS 系统字体
   'Segoe UI'                        -> Windows
   'PingFang SC'                     -> macOS 中文常用字体
   sans-serif                        -> 最后的兜底 */
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
  background: #f5f6fa;
  color: #2f3542;
}

/* 页面主容器：限制最大宽度并居中（margin: 0 auto 是水平居中的经典写法）。
   左右留 padding 防止小屏时内容贴边。 */
.app {
  max-width: 960px;
  margin: 0 auto;
  padding: 32px 20px 60px;
}

h1 {
  font-size: 24px;
  margin-bottom: 6px;
}

h2 {
  font-size: 16px;
  margin: 0 0 12px;
}

/* 副标题：字号小一点、颜色浅一点，视觉上弱化 */
.sub {
  color: #747d8c;
  margin-top: 0;
  font-size: 13px;
}

/* 每个功能区块做成一张「卡片」：
   白底 + 圆角 + 内边距 + 很淡的阴影 */
section {
  background: #fff;
  border-radius: 10px;
  padding: 18px 20px;
  margin-top: 18px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

/* 一行内的横向排布：
   display:flex 让子元素横排；gap 控制间距（不用再写 margin）；
   flex-wrap: wrap 让空间不够时自动换行（小屏友好）；
   align-items: center 让按钮和输入框垂直居中对齐。 */
.row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.search-row {
  margin-top: 10px;
}

/* 同步工具栏：上方加一条虚线分隔，视觉上和搜索栏区分开 */
.toolbar {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #eef1f6;
}

input {
  padding: 7px 10px;
  border: 1px solid #dfe4ea;
  border-radius: 6px;
  outline: none; /* 去掉浏览器默认的聚焦外框，下面用 border-color 代替 */
}

/* 聚焦时边框变蓝，给用户「当前在哪个输入框」的反馈 */
input:focus {
  border-color: #3b82f6;
}

/* 按钮基础样式 */
button {
  padding: 7px 14px;
  border: none;
  border-radius: 6px;
  background: #3b82f6;
  color: #fff;
  cursor: pointer; /* 鼠标移上去变成小手，暗示可点击 */
}

button:hover {
  background: #2563eb;
}

/* 禁用态：浅色 + 禁止光标，让用户知道「现在点不了」 */
button:disabled {
  background: #c7d2fe;
  cursor: not-allowed;
}

/* .ghost（幽灵按钮）：浅蓝底 + 蓝字，用于次要操作（撤销、重置等） */
button.ghost {
  background: #eef2ff;
  color: #3b82f6;
}

button.ghost:hover {
  background: #e0e7ff;
}

/* .danger（危险按钮）：红色，用于删除这种不可逆操作 */
button.danger {
  background: #ef4444;
  padding: 4px 10px;
}

button.danger:hover {
  background: #dc2626;
}

/* border-collapse: collapse 让相邻单元格的边框合并成一条线，
   不加的话会变成双线，很难看。 */
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 14px;
  font-size: 14px;
}

th,
td {
  text-align: left;
  padding: 8px 6px;
  border-bottom: 1px dashed #eef1f6;
}

/* 表头文字弱化一些，和数据行区分开 */
th {
  color: #747d8c;
  font-weight: 600;
  font-size: 13px;
}

/* 编辑态下，输入框占满整个单元格 */
td input {
  width: 100%;
}

td button {
  padding: 4px 10px;
  margin-right: 6px;
}

/* ★ 有未同步修改的行：浅黄色底色，一眼就能看出「哪几行还没保存」。
   这个 class 由模板里的 :class="{ dirty: isDirty(note.id) }" 动态添加。 */
tr.dirty {
  background: #fffbeb;
}

.pager {
  margin-top: 14px;
}

/* 各种提示文字：灰色、小号 */
.hint {
  color: #a4b0be;
  font-size: 13px;
}

/* 成功提示：绿色 */
.ok {
  color: #16a34a;
  font-size: 13px;
}

.empty {
  color: #a4b0be;
  font-size: 13px;
}

/* <pre> 用来展示 JSON：
   深色底 + 浅色字，字体最好用等宽字体（这里是默认继承），
   overflow:auto 防止长 JSON 撑破容器。 */
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
