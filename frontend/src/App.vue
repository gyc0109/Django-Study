<template>
  <div class="app">
    <h1>Django 4.2 + Celery + Vue 2.7</h1>
    <p class="sub">MySQL 8.4（3307） · Redis（6380） · Vite 代理 /api</p>

    <section>
      <h2>1. 服务状态 <button @click="loadHealth">刷新</button></h2>
      <pre>{{ healthText }}</pre>
    </section>

    <section>
      <h2>2. Celery 异步任务（加法）</h2>
      <div class="row">
        <input v-model.number="a" type="number" />
        <span>+</span>
        <input v-model.number="b" type="number" />
        <button @click="runAddTask">提交任务</button>
      </div>
      <pre>{{ taskText }}</pre>
    </section>

    <section>
      <h2>3. MySQL 数据（Notes）</h2>
      <div class="row">
        <input v-model="form.title" placeholder="标题" />
        <input v-model="form.content" placeholder="内容" />
        <button @click="addNote">新增</button>
      </div>
      <ul>
        <li v-for="note in notes" :key="note.id">
          <span>#{{ note.id }} {{ note.title }} — {{ note.content }}</span>
          <button class="danger" @click="removeNote(note.id)">删除</button>
        </li>
      </ul>
      <p v-if="!notes.length" class="empty">暂无数据，先新增一条试试。</p>
    </section>
  </div>
</template>

<script>
import { http } from './api'

export default {
  name: 'App',
  data() {
    return {
      health: null,
      healthError: '',
      a: 1,
      b: 2,
      task: null,
      form: { title: '', content: '' },
      notes: []
    }
  },
  computed: {
    healthText() {
      if (this.healthError) return `请求失败：${this.healthError}`
      if (!this.health) return '加载中...'
      return JSON.stringify(this.health, null, 2)
    },
    taskText() {
      if (!this.task) return '尚未提交任务'
      return JSON.stringify(this.task, null, 2)
    }
  },
  mounted() {
    this.loadHealth()
    this.loadNotes()
  },
  methods: {
    async loadHealth() {
      this.healthError = ''
      try {
        const { data } = await http.get('/health/')
        this.health = data
      } catch (err) {
        this.healthError = err.message
      }
    },
    async loadNotes() {
      const { data } = await http.get('/notes/')
      this.notes = data
    },
    async addNote() {
      if (!this.form.title.trim()) return
      await http.post('/notes/', this.form)
      this.form = { title: '', content: '' }
      this.loadNotes()
    },
    async removeNote(id) {
      await http.delete(`/notes/${id}/`)
      this.loadNotes()
    },
    async runAddTask() {
      const { data } = await http.post('/tasks/add/', { a: this.a, b: this.b })
      this.task = { task_id: data.task_id, status: 'PENDING' }
      this.pollTask(data.task_id)
    },
    async pollTask(taskId) {
      for (let i = 0; i < 10; i += 1) {
        await new Promise((resolve) => setTimeout(resolve, 800))
        const { data } = await http.get(`/tasks/${taskId}/`)
        this.task = data
        if (data.status === 'SUCCESS' || data.status === 'FAILURE') return
      }
    }
  }
}
</script>

<style>
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
  background: #f5f6fa;
  color: #2f3542;
}
.app { max-width: 860px; margin: 0 auto; padding: 32px 20px 60px; }
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
button.danger { background: #ef4444; padding: 4px 10px; }
button.danger:hover { background: #dc2626; }
pre {
  background: #0f172a;
  color: #e2e8f0;
  padding: 12px 14px;
  border-radius: 8px;
  font-size: 12px;
  overflow: auto;
  margin-bottom: 0;
}
ul { list-style: none; padding: 0; margin: 12px 0 0; }
li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px dashed #eef1f6;
  font-size: 14px;
}
.empty { color: #a4b0be; font-size: 13px; }
</style>
